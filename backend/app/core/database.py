"""
InvoiceFlow Pro - Database Configuration
"""
try:
    from databases import Database
    database = Database(settings.DATABASE_URL)
except ImportError:
    Database = None
    database = None
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


# SQLAlchemy engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Metadata for Alembic
metadata = MetaData()


async def get_database() -> Database:
    """Get database connection"""
    return database