#!/usr/bin/env python3
"""
CLI script to permanently delete a school (tenant) and all its associated data:
- Academic groups (classes / streams)
- Students
- Assessment batches
- Student results
- Batch background tasks
- S3 / Object storage exam assets (batches/{batch_id}/*)
- Tenant record
"""

import sys
import os
import argparse
import asyncio
import uuid
from typing import Optional

# Set up paths and environment
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, SRC_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(SRC_DIR, ".env"))

from sqlalchemy import select, func, delete as sql_delete
from core.models import (
    async_session_maker,
    Tenant,
    AcademicGroup,
    Student,
    AssessmentBatch,
    StudentResult,
    BatchTask
)
from core.storage import delete_s3_batch_files


async def list_schools():
    """Lists all registered schools with counts of related records."""
    async with async_session_maker() as session:
        tenants_res = await session.execute(select(Tenant).order_by(Tenant.name))
        tenants = tenants_res.scalars().all()

        if not tenants:
            print("No schools found in database.")
            return

        print("\n" + "=" * 90)
        print(f"{'ID':<36} | {'School Name':<28} | {'Classes':<8} | {'Students':<8} | {'Batches':<8}")
        print("=" * 90)

        for t in tenants:
            # Count groups
            g_res = await session.execute(
                select(AcademicGroup.id).where(AcademicGroup.tenant_id == t.id)
            )
            g_ids = g_res.scalars().all()
            classes_count = len(g_ids)

            students_count = 0
            batches_count = 0
            if g_ids:
                stu_res = await session.execute(
                    select(func.count(Student.id)).where(Student.academic_group_id.in_(g_ids))
                )
                students_count = stu_res.scalar() or 0

                batch_res = await session.execute(
                    select(func.count(AssessmentBatch.id)).where(AssessmentBatch.academic_group_id.in_(g_ids))
                )
                batches_count = batch_res.scalar() or 0

            print(f"{str(t.id):<36} | {t.name[:28]:<28} | {classes_count:<8} | {students_count:<8} | {batches_count:<8}")

        print("=" * 90 + "\n")


async def get_school(identifier: str) -> Optional[Tenant]:
    """Finds a school by UUID or exact/case-insensitive name."""
    async with async_session_maker() as session:
        # Try parsing as UUID
        try:
            t_uuid = uuid.UUID(identifier)
            tenant = await session.get(Tenant, t_uuid)
            if tenant:
                return tenant
        except ValueError:
            pass

        # Try by name (case-insensitive)
        res = await session.execute(
            select(Tenant).where(func.lower(Tenant.name) == identifier.strip().lower())
        )
        tenants = res.scalars().all()
        if len(tenants) == 1:
            return tenants[0]
        elif len(tenants) > 1:
            print(f"Multiple schools found with name '{identifier}'. Please specify the exact UUID.")
            for t in tenants:
                print(f"  - ID: {t.id} | Name: {t.name}")
            return None

        # Partial match if not found
        res_partial = await session.execute(
            select(Tenant).where(Tenant.name.ilike(f"%{identifier.strip()}%"))
        )
        partial_matches = res_partial.scalars().all()
        if len(partial_matches) == 1:
            return partial_matches[0]
        elif len(partial_matches) > 1:
            print(f"Multiple schools match '{identifier}'. Please specify the exact UUID:")
            for t in partial_matches:
                print(f"  - ID: {t.id} | Name: {t.name}")
            return None

        return None


async def inspect_school_data(tenant: Tenant):
    """Gathers counts of all data that will be deleted for the school."""
    async with async_session_maker() as session:
        groups_res = await session.execute(
            select(AcademicGroup).where(AcademicGroup.tenant_id == tenant.id)
        )
        groups = groups_res.scalars().all()
        group_ids = [g.id for g in groups]

        students_count = 0
        batches = []
        results_count = 0
        tasks_count = 0

        if group_ids:
            stu_res = await session.execute(
                select(func.count(Student.id)).where(Student.academic_group_id.in_(group_ids))
            )
            students_count = stu_res.scalar() or 0

            batches_res = await session.execute(
                select(AssessmentBatch).where(AssessmentBatch.academic_group_id.in_(group_ids))
            )
            batches = batches_res.scalars().all()
            batch_ids = [b.id for b in batches]

            if batch_ids:
                res_count_q = await session.execute(
                    select(func.count(StudentResult.id)).where(StudentResult.batch_id.in_(batch_ids))
                )
                results_count = res_count_q.scalar() or 0

                tasks_count_q = await session.execute(
                    select(func.count(BatchTask.id)).where(BatchTask.batch_id.in_(batch_ids))
                )
                tasks_count = tasks_count_q.scalar() or 0

        return {
            "tenant": tenant,
            "groups": groups,
            "students_count": students_count,
            "batches": batches,
            "results_count": results_count,
            "tasks_count": tasks_count
        }


async def delete_school(data: dict, clean_s3: bool = True):
    """Permanently deletes the school and all cascading records."""
    tenant = data["tenant"]
    group_ids = [g.id for g in data["groups"]]
    batch_ids = [b.id for b in data["batches"]]

    # 1. Clean S3 objects first if requested
    s3_deleted_count = 0
    if clean_s3 and batch_ids:
        print("\nCleaning up associated S3 assets...")
        for b_id in batch_ids:
            count = delete_s3_batch_files(str(b_id))
            s3_deleted_count += count
            if count > 0:
                print(f"  - Batch {b_id}: removed {count} S3 objects")

    # 2. Delete database records in reverse dependency order
    async with async_session_maker() as session:
        if batch_ids:
            await session.execute(
                sql_delete(BatchTask).where(BatchTask.batch_id.in_(batch_ids))
            )
            await session.execute(
                sql_delete(StudentResult).where(StudentResult.batch_id.in_(batch_ids))
            )
            await session.execute(
                sql_delete(AssessmentBatch).where(AssessmentBatch.id.in_(batch_ids))
            )

        if group_ids:
            await session.execute(
                sql_delete(Student).where(Student.academic_group_id.in_(group_ids))
            )
            await session.execute(
                sql_delete(AcademicGroup).where(AcademicGroup.id.in_(group_ids))
            )

        # Delete the tenant record itself
        await session.execute(
            sql_delete(Tenant).where(Tenant.id == tenant.id)
        )
        await session.commit()

    return s3_deleted_count


async def main():
    parser = argparse.ArgumentParser(description="Permanently delete a school and all associated data.")
    parser.add_argument("school", nargs="?", help="School UUID or name to delete")
    parser.add_argument("--list", action="store_true", help="List all schools in the database")
    parser.add_argument("-y", "--yes", action="store_true", help="Skip confirmation prompt")
    parser.add_argument("--no-s3", action="store_true", help="Skip deleting S3 bucket files")

    args = parser.parse_args()

    if args.list or not args.school:
        await list_schools()
        if not args.school:
            print("To delete a school, run:")
            print("  python3 scripts/delete_school.py <school_name_or_uuid>")
            return

    tenant = await get_school(args.school)
    if not tenant:
        print(f"Error: School '{args.school}' not found.")
        sys.exit(1)

    data = await inspect_school_data(tenant)

    print("\n" + "=" * 65)
    print("SCHOOL DELETION TARGET")
    print("=" * 65)
    print(f"  Name:               {tenant.name}")
    print(f"  ID:                 {tenant.id}")
    print(f"  Academic Groups:    {len(data['groups'])}")
    print(f"  Students:           {data['students_count']}")
    print(f"  Assessment Batches: {len(data['batches'])}")
    print(f"  Student Results:    {data['results_count']}")
    print(f"  Background Tasks:   {data['tasks_count']}")
    print(f"  Clean S3 Assets:    {'No' if args.no_s3 else 'Yes'}")
    print("=" * 65)
    print("WARNING: This action is permanent and cannot be undone.")

    if not args.yes:
        confirm = input("\nType 'DELETE' to confirm deletion: ")
        if confirm.strip() != "DELETE":
            print("Deletion cancelled.")
            sys.exit(0)

    s3_deleted = await delete_school(data, clean_s3=not args.no_s3)

    print("\n" + "=" * 65)
    print("DELETION COMPLETED SUCCESSFULLY")
    print("=" * 65)
    print(f"  School '{tenant.name}' and all associated records have been wiped.")
    if not args.no_s3:
        print(f"  Total S3 objects purged: {s3_deleted}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
