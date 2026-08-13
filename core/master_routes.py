from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta
import uuid

from core.models import User, Invitation, AuditLog, get_async_session, async_session_maker
from core.auth import current_active_user, require_role, fastapi_users, auth_backend
from pydantic import BaseModel
from fastapi_users.password import PasswordHelper

router = APIRouter()
ph = PasswordHelper()

# --- Master Protected Routes ---

class InviteRequest(BaseModel):
    email: str

@router.post("/master/invite")
async def generate_invite(
    req: InviteRequest, 
    master: User = Depends(require_role(["master"])),
    session: AsyncSession = Depends(get_async_session)
):
    token = str(uuid.uuid4())
    expires = datetime.utcnow() + timedelta(hours=1)
    
    invite = Invitation(
        token=token,
        email=req.email,
        role="staff",
        invited_by=master.id,
        expires_at=expires
    )
    session.add(invite)
    
    # Audit log
    log = AuditLog(user_id=master.id, action="invite_created", details={"invited_email": req.email})
    session.add(log)
    
    await session.commit()
    
    # In a real app, send an email here. For now, we return the token to construct the link.
    return {"status": "success", "token": token, "email": req.email, "expires_at": expires.isoformat()}

@router.get("/master/users")
async def list_users(
    master: User = Depends(require_role(["master"])),
    session: AsyncSession = Depends(get_async_session)
):
    res = await session.execute(select(User).where(User.role == "staff"))
    users = res.scalars().all()
    return [{"id": str(u.id), "email": u.email, "is_active": u.is_active} for u in users]

@router.delete("/master/users/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    master: User = Depends(require_role(["master"])),
    session: AsyncSession = Depends(get_async_session)
):
    res = await session.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Hard delete for simplicity, or could soft delete
    await session.delete(user)
    
    # Audit log
    log = AuditLog(user_id=master.id, action="user_deleted", details={"deleted_user_email": user.email})
    session.add(log)
    
    await session.commit()
    return {"status": "success", "message": f"User {user.email} deleted."}

@router.get("/master/audit-logs")
async def get_audit_logs(
    master: User = Depends(require_role(["master"])),
    session: AsyncSession = Depends(get_async_session)
):
    # Fetch logs with user emails if possible, joining User table
    # For simplicity, just fetch logs
    query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100)
    res = await session.execute(query)
    logs = res.scalars().all()
    
    return [
        {
            "id": str(l.id),
            "user_id": str(l.user_id) if l.user_id else None,
            "action": l.action,
            "details": l.details,
            "timestamp": l.timestamp.isoformat()
        } for l in logs
    ]

# --- Public Routes (Staff Registration via Invite) ---

class RegisterInviteRequest(BaseModel):
    token: str
    password: str

@router.post("/auth/register-via-invite")
async def register_via_invite(
    req: RegisterInviteRequest,
    session: AsyncSession = Depends(get_async_session)
):
    # 1. Validate Token
    res = await session.execute(select(Invitation).where(Invitation.token == req.token))
    invite = res.scalar_one_or_none()
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invitation token.")
        
    if invite.used_at is not None:
        raise HTTPException(status_code=400, detail="Invitation already used.")
        
    if invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invitation expired.")
        
    # 2. Check if user email already exists
    user_res = await session.execute(select(User).where(User.email == invite.email))
    if user_res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User with this email already exists.")
        
    # 3. Create User
    new_user = User(
        id=uuid.uuid4(),
        email=invite.email,
        hashed_password=ph.hash(req.password),
        is_active=True,
        is_superuser=False,
        is_verified=True,
        role=invite.role
    )
    session.add(new_user)
    
    # 4. Mark token used
    invite.used_at = datetime.utcnow()
    
    # 5. Audit log (User themselves)
    log = AuditLog(user_id=new_user.id, action="registered_via_invite", details={"email": new_user.email})
    session.add(log)
    
    await session.commit()
    
    return {"status": "success", "message": "Account created successfully!"}

@router.get("/auth/verify-invite/{token}")
async def verify_invite(
    token: str,
    session: AsyncSession = Depends(get_async_session)
):
    res = await session.execute(select(Invitation).where(Invitation.token == token))
    invite = res.scalar_one_or_none()
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid invitation token.")
        
    if invite.used_at is not None:
        raise HTTPException(status_code=400, detail="This invitation link has already been used.")
        
    if invite.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="This invitation link has expired (links are valid for 1 hour).")
        
    return {"status": "valid", "email": invite.email}

@router.get("/auth/me")
async def get_me(user: User = Depends(current_active_user)):
    return {
        "id": str(user.id),
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active
    }
