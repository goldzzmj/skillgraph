"""
API Dependencies

Dependency injection for FastAPI application.
"""

from typing import Generator, Optional, AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import Depends
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Database configuration
DATABASE_URL = "sqlite:///./skillgraph.db"
ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./skillgraph.db"

# Create engines
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
try:
    async_engine = create_async_engine(ASYNC_DATABASE_URL)
except Exception:
    async_engine = None

# Create session factories
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
if async_engine is not None:
    AsyncSessionLocal = sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
else:
    AsyncSessionLocal = None


def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    if AsyncSessionLocal is None:
        raise RuntimeError("Async database dependencies are not installed")
    async with AsyncSessionLocal() as session:
        yield session


# Singleton instances for parsers and extractors
parser_instance = None
entity_extractor_instance = None
community_detector_instance = None


def get_parser():
    """Get singleton parser instance."""
    from skillgraph.parser import SkillParser

    global parser_instance
    if parser_instance is None:
        parser_instance = SkillParser()
    return parser_instance


def get_entity_extractor():
    """Get singleton entity extractor instance."""
    from skillgraph.graphrag import EntityExtractor

    global entity_extractor_instance
    if entity_extractor_instance is None:
        entity_extractor_instance = EntityExtractor()
    return entity_extractor_instance


def get_community_detector():
    """Get singleton community detector instance."""
    from skillgraph.graphrag import CommunityDetector

    global community_detector_instance
    if community_detector_instance is None:
        community_detector_instance = CommunityDetector()
    return community_detector_instance
