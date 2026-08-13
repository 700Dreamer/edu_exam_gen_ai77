import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()

# Adjust Python path to load core modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, text
from core.models import (
    Base, User, AuditLog, Tenant, AcademicGroup, Student,
    AssessmentBatch, StudentResult, BatchTask, Invitation
)

# --- Railway Volume SQLite Source (ALWAYS reads from the Railway volume, not local) ---
SQLITE_PATH = "/app/data_volume/edulytics_history.db"
if not os.path.exists(SQLITE_PATH):
    print(f"ERROR: SQLite database not found at {SQLITE_PATH}")
    print("This script must run inside the Railway container where the volume is mounted.")
    sys.exit(1)

SQLITE_URL = f"sqlite+aiosqlite:///{SQLITE_PATH}"
sqlite_engine = create_async_engine(SQLITE_URL)
sqlite_session_maker = async_sessionmaker(sqlite_engine, expire_on_commit=False)

# --- PostgreSQL Target Engine ---
PG_URL = os.getenv("DATABASE_URL")
if not PG_URL:
    print("ERROR: DATABASE_URL environment variable is not set.")
    sys.exit(1)

if PG_URL.startswith("postgres://"):
    PG_URL = PG_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif PG_URL.startswith("postgresql://"):
    PG_URL = PG_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

pg_engine = create_async_engine(PG_URL)
pg_session_maker = async_sessionmaker(pg_engine, expire_on_commit=False)


async def wipe_and_migrate():
    print("=" * 60)
    print("WIPE & MIGRATE: Railway Volume SQLite -> PostgreSQL")
    print("=" * 60)
    print(f"Source SQLite:   {SQLITE_PATH}")
    print(f"Target PG host:  {PG_URL.split('@')[-1]}")
    print("-" * 60)

    # STEP 1: Wipe PostgreSQL — drop all tables and recreate them clean
    print("[STEP 1/2] Wiping all PostgreSQL tables...")
    async with pg_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("           PostgreSQL wiped and schema recreated.")

    # STEP 2: Migrate all data from Railway volume SQLite to PostgreSQL
    print("[STEP 2/2] Migrating all data from Railway SQLite volume...")

    async with sqlite_session_maker() as src, pg_session_maker() as dst:

        async def copy(model_class, label):
            res = await src.execute(select(model_class))
            items = res.scalars().all()
            count = len(items)
            if count == 0:
                print(f"  {label}: 0 records (skipping)")
                return
            for item in items:
                await dst.merge(item)
            await dst.commit()
            print(f"  {label}: {count} records migrated")

        # Migration order respects foreign key dependencies
        await copy(User,            "Users")
        await copy(Tenant,          "Tenants")
        await copy(AcademicGroup,   "Academic Groups")

        # Students: deduplicate index_number values before inserting.
        # SQLite may have allowed the same index_number across different groups;
        # PostgreSQL enforces a strict global UNIQUE constraint on the column.
        # Strategy: first student to claim an index_number keeps it; all others get NULL.
        print("  Students: deduplicating index_number values...")
        res = await src.execute(select(Student))
        students = res.scalars().all()
        seen_index_numbers: set = set()
        count = 0
        dupes = 0
        for stu in students:
            # Normalize empty strings to None
            if stu.index_number is not None and stu.index_number.strip() == "":
                stu.index_number = None
            # Deduplicate — null out any index_number already claimed
            if stu.index_number is not None:
                if stu.index_number in seen_index_numbers:
                    print(f"    Duplicate index_number='{stu.index_number}' for '{stu.full_name}' -> setting to NULL")
                    stu.index_number = None
                    dupes += 1
                else:
                    seen_index_numbers.add(stu.index_number)
            await dst.merge(stu)
            count += 1
        await dst.commit()
        print(f"  Students: {count} records migrated ({dupes} duplicate index numbers nulled)")

        await copy(Invitation,      "Invitations")
        await copy(AssessmentBatch, "Assessment Batches")
        await copy(StudentResult,   "Student Results")
        await copy(BatchTask,       "Batch Tasks")
        await copy(AuditLog,        "Audit Logs")

    print("-" * 60)
    print("MIGRATION COMPLETE. Railway PostgreSQL now reflects the volume SQLite data.")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(wipe_and_migrate())
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
