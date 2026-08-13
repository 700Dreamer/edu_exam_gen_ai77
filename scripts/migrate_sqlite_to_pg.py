import asyncio
import os
import sys
from datetime import datetime

# Adjust Python path to load core modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, text

from core.models import (
    Base, User, AuditLog, Tenant, AcademicGroup, Student,
    AssessmentBatch, StudentResult, BatchTask, Invitation
)

# SQLite Source Engine
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_PATH = os.path.join(BASE_DIR, "edulytics_history.db")
SQLITE_URL = f"sqlite+aiosqlite:///{SQLITE_PATH}"

sqlite_engine = create_async_engine(SQLITE_URL)
sqlite_session_maker = async_sessionmaker(sqlite_engine, expire_on_commit=False)

# PostgreSQL Target Engine
PG_URL = os.getenv("DATABASE_URL")
if not PG_URL:
    print("ERROR: DATABASE_URL environment variable is missing in .env")
    sys.exit(1)

if PG_URL.startswith("postgres://"):
    PG_URL = PG_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif PG_URL.startswith("postgresql://"):
    PG_URL = PG_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

pg_engine = create_async_engine(PG_URL)
pg_session_maker = async_sessionmaker(pg_engine, expire_on_commit=False)

async def migrate():
    print("=" * 60)
    print("EDULYTICS MANUAL DATA MIGRATION: SQLite -> PostgreSQL")
    print("=" * 60)
    print(f"Source SQLite: {SQLITE_PATH}")
    print(f"Target PostgreSQL: {PG_URL.split('@')[-1]}")
    print("-" * 60)

    # 1. Initialize PostgreSQL tables
    print("[1/9] Initializing schema on PostgreSQL...")
    async with pg_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("      PostgreSQL tables initialized successfully.")

    async with sqlite_session_maker() as sqlite_session, pg_session_maker() as pg_session:

        # Helper function to migrate a table model
        async def copy_records(model_class, model_name):
            print(f"      Migrating {model_name}...")
            res = await sqlite_session.execute(select(model_class))
            items = res.scalars().all()
            if not items:
                print(f"      No records found for {model_name}.")
                return 0

            count = 0
            for item in items:
                # Merge instance into target PostgreSQL session
                await pg_session.merge(item)
                count += 1

            await pg_session.commit()
            print(f"      Successfully transferred {count} records for {model_name}.")
            return count

        # 2. Migrate Users
        print("[2/9] Migrating Users...")
        await copy_records(User, "User")

        # 3. Migrate Tenants
        print("[3/9] Migrating Tenants...")
        await copy_records(Tenant, "Tenant")

        # 4. Migrate Academic Groups
        print("[4/9] Migrating Academic Groups...")
        await copy_records(AcademicGroup, "AcademicGroup")

        # 5. Migrate Students
        print("[5/9] Migrating Students...")
        await copy_records(Student, "Student")

        # 6. Migrate Invitations
        print("[6/9] Migrating Invitations...")
        await copy_records(Invitation, "Invitation")

        # 7. Migrate Assessment Batches
        print("[7/9] Migrating Assessment Batches...")
        await copy_records(AssessmentBatch, "AssessmentBatch")

        # 8. Migrate Student Results
        print("[8/9] Migrating Student Results...")
        await copy_records(StudentResult, "StudentResult")

        # 9. Migrate Audit Logs
        print("[9/9] Migrating Audit Logs...")
        await copy_records(AuditLog, "AuditLog")

    print("=" * 60)
    print("MIGRATION COMPLETE! All SQLite data successfully copied to PostgreSQL.")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(migrate())
    except Exception as e:
        print(f"\nFATAL ERROR DURING MIGRATION: {e}")
        import traceback
        traceback.print_exc()
