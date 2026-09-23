from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
import uuid

from models import User 

# ------------------ User Utilities ------------------

async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID):
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()

async def get_user_by_email(session: AsyncSession, email: str):
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def get_user_by_api_key(session: AsyncSession, api_key: str):
    result = await session.execute(select(User).where(User.api_key == api_key))
    return result.scalar_one_or_none()

# ------------------ User Creation ------------------

async def create_user(session: AsyncSession, email: str, password_hash: str, domain_name: str, superuser: bool = False): 
    existing_user = await get_user_by_email(session, email)
    if existing_user:
        raise ValueError("Email already exists")

    new_user = User(
        email=email,
        password_hash=password_hash, # Ensure these exist in your models.py
        domain_name=domain_name,
        superuser=superuser
    )
    session.add(new_user)
    
    try:
        await session.commit()
        await session.refresh(new_user)
        return new_user
    except IntegrityError:
        await session.rollback()
        raise ValueError("Failed to create user due to integrity error")

# ------------------ API Key Utilities ------------------

async def generate_api_key(session: AsyncSession, user_id: uuid.UUID):
    user = await get_user_by_id(session, user_id)
    if not user:
        raise ValueError("User not found")
        
    new_api_key = str(uuid.uuid4())
    user.api_key = new_api_key
    
    await session.commit()
    await session.refresh(user)
    
    return new_api_key
