import sys
import os
import uuid
import asyncio

# Add project root to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from fastapi_users.password import PasswordHelper
from core.models import User, async_session_maker
from sqlalchemy import select

async def seed_master():
    print("--- Seed Master Account ---")
    email = input("Master Email: ")
    password = input("Master Password: ")
    
    ph = PasswordHelper()
    hashed_password = ph.hash(password)
    
    async with async_session_maker() as session:
        # Check if a master already exists
        res = await session.execute(select(User).where(User.role == "master"))
        existing_master = res.scalar_one_or_none()
        if existing_master:
            print(f"A master account already exists ({existing_master.email}). Please delete it first or use that one.")
            return

        res = await session.execute(select(User).where(User.email == email))
        user = res.scalar_one_or_none()
        if user:
            print(f"User {email} already exists!")
            return
            
        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=hashed_password,
            is_active=True,
            is_superuser=True,
            is_verified=True,
            role="master"
        )
        session.add(user)
        await session.commit()
        print(f"Master account '{email}' created successfully! You can now log in.")

if __name__ == "__main__":
    asyncio.run(seed_master())
