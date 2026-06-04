from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Boolean, Text, Enum
import os
from dotenv import load_dotenv

load_dotenv()

# Convert postgresql:// to postgresql+asyncpg:// for async support
DATABASE_URL = os.getenv("DATABASE_URL").replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

from database.models import User,Field, Planting, Harvest, Sale, Reminder, CropInput

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session