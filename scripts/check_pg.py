import asyncio
import os
import sys

from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, func, text

from core.models import (
    Base, User, AuditLog, Tenant, AcademicGroup, Student,
    AssessmentBatch, StudentResult, BatchTask, Invitation
)

PG_URL = os.getenv("DATABASE_URL")
if not PG_URL:
    print("ERROR: DATABASE_URL is not set.")
    sys.exit(1)

if PG_URL.startswith("postgres://"):
    PG_URL = PG_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif PG_URL.startswith("postgresql://"):
    PG_URL = PG_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

pg_engine = create_async_engine(PG_URL)
pg_session = async_sessionmaker(pg_engine, expire_on_commit=False)

async def check():
    print("=" * 55)
    print("Railway PostgreSQL - Record Count Diagnostic")
    print("=" * 55)
    async with pg_session() as s:
        for model, name in [
            (User, "Users"),
            (Tenant, "Tenants"),
            (AcademicGroup, "Academic Groups"),
            (Student, "Students"),
            (AssessmentBatch, "Assessment Batches"),
            (StudentResult, "Student Results"),
            (Invitation, "Invitations"),
            (AuditLog, "Audit Logs"),
        ]:
            res = await s.execute(select(func.count()).select_from(model))
            count = res.scalar()
            status = "OK" if count > 0 else "EMPTY"
            print(f"  {name:<25} {count:>5}  [{status}]")
    print("=" * 55)

if __name__ == "__main__":
    asyncio.run(check())
