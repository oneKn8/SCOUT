"""
Database connection and utilities for SCOUT Backend
"""

import asyncpg
from typing import Optional, Dict, Any, List
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class Database:
    """Simple database connection wrapper"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Initialize database connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                settings.DATABASE_URL,
                min_size=1,
                max_size=10,
                server_settings={
                    'jit': 'off'  # Disable JIT for better performance on small queries
                }
            )
            logger.info("Database connection pool created")
        except Exception as e:
            logger.error("Failed to create database pool", error=str(e))
            raise

    async def disconnect(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")

    async def fetch_one(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Execute query and fetch one result"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            result = await conn.fetchrow(query, *args)
            return dict(result) if result else None

    async def fetch_all(self, query: str, *args) -> List[Dict[str, Any]]:
        """Execute query and fetch all results"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            results = await conn.fetch(query, *args)
            return [dict(row) for row in results]

    async def execute(self, query: str, *args) -> str:
        """Execute query and return status"""
        if not self.pool:
            await self.connect()

        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def get_resume_file_path(self, resume_id: str) -> Optional[str]:
        """
        Get the file path for a resume by its ID
        Looks up the most recent artifact for the resume
        """
        query = """
        SELECT file_path, file_name
        FROM artifacts
        WHERE resume_id = $1
        ORDER BY created_at DESC
        LIMIT 1
        """

        result = await self.fetch_one(query, resume_id)
        if result and result.get('file_path'):
            # Return the full path to the stored file
            return result['file_path']

        # Fallback: try to find by resume_id in artifacts table
        # Some uploads might not create resume records yet
        query_artifact = """
        SELECT file_path, file_name
        FROM artifacts
        WHERE id = $1
        ORDER BY created_at DESC
        LIMIT 1
        """

        result = await self.fetch_one(query_artifact, resume_id)
        return result['file_path'] if result else None


# Global database instance
db = Database()