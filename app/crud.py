from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from app import models

async def get_user_by_phone(db: AsyncSession, phone_number: str):
    result = await db.execute(select(models.User).filter(models.User.phone_number == phone_number))
    return result.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(models.User).filter(models.User.email == email))
    return result.scalars().first()
