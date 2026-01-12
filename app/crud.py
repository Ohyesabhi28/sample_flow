from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from app import models

async def get_user_by_phone(db: AsyncSession, phone_number: str):
    result = await db.execute(select(models.User).options(selectinload(models.User.profile)).filter(models.User.phone_number == phone_number))
    return result.scalars().first()

async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(models.User).options(selectinload(models.User.profile)).filter(models.User.email == email))
    return result.scalars().first()

async def create_news(db: AsyncSession, news: models.News):
    db.add(news)
    await db.commit()
    await db.refresh(news)
    return news

async def get_news(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(models.News).offset(skip).limit(limit).order_by(models.News.created_at.desc()))
    return result.scalars().all()

async def create_product(db: AsyncSession, product: models.Product):
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product

async def get_active_products(db: AsyncSession, now: datetime, skip: int = 0, limit: int = 10):
    result = await db.execute(
        select(models.Product)
        .filter(models.Product.publish_at <= now)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()

async def create_question(db: AsyncSession, question: models.Question):
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return question

async def get_questions(db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(models.Question).offset(skip).limit(limit).order_by(models.Question.created_at.desc()))
    return result.scalars().all()
