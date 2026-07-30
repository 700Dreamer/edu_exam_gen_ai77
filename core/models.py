import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, DateTime, ForeignKey, JSON
from fastapi_users.db import SQLAlchemyBaseUserTableUUID
import uuid
from datetime import datetime
from typing import Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Dynamic Database URL Configuration (PostgreSQL / SQLite) ──
raw_db_url = os.getenv("DATABASE_URL")
if raw_db_url:
    if raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif raw_db_url.startswith("postgresql://"):
        raw_db_url = raw_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    elif raw_db_url.startswith("sqlite://") and not raw_db_url.startswith("sqlite+aiosqlite://"):
        raw_db_url = raw_db_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    DATABASE_URL = raw_db_url
else:
    DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'edulytics_history.db')}"

connect_args = {"timeout": 30.0} if "sqlite" in DATABASE_URL else {}
engine = create_async_engine(DATABASE_URL, connect_args=connect_args)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

class User(SQLAlchemyBaseUserTableUUID, Base):
    role: Mapped[str] = mapped_column(String(50), default="staff", nullable=False)

class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

class Tenant(Base):
    """Represents a School or Institution."""
    __tablename__ = "tenant"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

class AcademicGroup(Base):
    """Represents a specific Class and Stream within a School (e.g., P.7 Blue)."""
    __tablename__ = "academic_group"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tenant.id", ondelete="CASCADE"), nullable=False)
    level: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., P.1, P.2
    stream: Mapped[str] = mapped_column(String(50), nullable=False) # e.g., Blue, North

class Student(Base):
    """Represents an individual student belonging to an Academic Group."""
    __tablename__ = "student"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    academic_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_group.id", ondelete="CASCADE"), nullable=False)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    index_number: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True)

class AssessmentBatch(Base):
    """Represents an asynchronous exam upload and grading session."""
    __tablename__ = "assessment_batch"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    academic_group_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("academic_group.id", ondelete="CASCADE"), nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    exam_type: Mapped[str] = mapped_column(String(100), nullable=False)
    mode: Mapped[Optional[str]] = mapped_column(String(50), default="worksheet", nullable=True) # worksheet (primary) vs answer_sheet (secondary)
    status: Mapped[str] = mapped_column(String(50), default="Processing", nullable=False) # Processing, Completed, Needs Review
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    batch_insights: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    master_question_urls: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    master_exam_structure: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

class StudentResult(Base):
    """Represents the graded exam results for a single student from a batch."""
    __tablename__ = "student_result"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessment_batch.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("student.id", ondelete="SET NULL"), nullable=True)
    total_score: Mapped[Optional[int]] = mapped_column(nullable=True)
    ai_remarks: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    needs_manual_review: Mapped[bool] = mapped_column(default=False, nullable=False)
    paper_images_urls: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    raw_extracted_html: Mapped[Optional[str]] = mapped_column(String, nullable=True)

class BatchTask(Base):
    """Represents an individual granular task for background batch processing."""
    __tablename__ = "batch_task"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    batch_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("assessment_batch.id", ondelete="CASCADE"), nullable=False)
    student_result_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("student_result.id", ondelete="CASCADE"), nullable=False)
    task_type: Mapped[str] = mapped_column(String(50), default="grade_paper", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="QUEUED", nullable=False) # QUEUED, PROCESSING, COMPLETED, FAILED
    attempts: Mapped[int] = mapped_column(default=0, nullable=False)
    max_retries: Mapped[int] = mapped_column(default=3, nullable=False)
    last_error: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        from sqlalchemy import text
        try:
            await conn.execute(text("ALTER TABLE assessment_batch ADD COLUMN batch_insights TEXT"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE assessment_batch ADD COLUMN mode TEXT DEFAULT 'worksheet'"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE assessment_batch ADD COLUMN master_question_urls JSON"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE assessment_batch ADD COLUMN master_exam_structure JSON"))
        except Exception:
            pass

async def get_async_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
