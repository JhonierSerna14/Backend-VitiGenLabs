"""
MongoDB Database Connection Module

This module handles MongoDB connections for the VitiGenLabs backend application.
It provides both synchronous and asynchronous database clients with proper
connection management and error handling.
"""

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from app.config import settings

logger = logging.getLogger(__name__)


class AsyncMongoDB:
    """
    Asynchronous MongoDB client manager.
    
    Handles the async MongoDB connection and database instance
    for non-blocking database operations.
    """
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None


class SyncMongoDB:
    """
    Synchronous MongoDB client manager.
    
    Handles the sync MongoDB connection for operations that
    require synchronous database access.
    """
    client: Optional[MongoClient] = None
    database: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo() -> None:
    """
    Establish connection to MongoDB.
    
    Creates async MongoDB client with optimized connection settings
    and tests the connection to ensure it's working properly.
    
    Raises:
        ConnectionFailure: If unable to connect to MongoDB
        ServerSelectionTimeoutError: If MongoDB server selection times out
    """
    try:
        logger.info(f"Connecting to MongoDB at {settings.MONGODB_URL}")
        
        # Create async client with optimized settings
        AsyncMongoDB.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=settings.MAX_DB_CONNECTIONS,
            minPoolSize=10,
            maxIdleTimeMS=30000,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            retryWrites=True,
            retryReads=True
        )
        
        # Get database instance
        AsyncMongoDB.database = AsyncMongoDB.client[settings.MONGODB_DATABASE]
        
        # Test the connection
        await AsyncMongoDB.client.admin.command('ismaster')
        logger.info(f"Successfully connected to MongoDB database: {settings.MONGODB_DATABASE}")
        
    except (ConnectionFailure, ServerSelectionTimeoutError) as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error connecting to MongoDB: {e}")
        raise


async def close_mongo_connection() -> None:
    """
    Close MongoDB connections gracefully.
    
    Properly closes both async and sync MongoDB clients to prevent
    connection leaks and ensure clean shutdown.
    """
    try:
        if AsyncMongoDB.client:
            AsyncMongoDB.client.close()
            logger.info("Async MongoDB connection closed")
            
        if SyncMongoDB.client:
            SyncMongoDB.client.close()
            logger.info("Sync MongoDB connection closed")
            
    except Exception as e:
        logger.error(f"Error closing MongoDB connections: {e}")


def get_async_database() -> AsyncIOMotorDatabase:
    """
    Get the async MongoDB database instance.
    
    Returns:
        AsyncIOMotorDatabase: The async database instance
        
    Raises:
        RuntimeError: If database connection is not established
    """
    if AsyncMongoDB.database is None:
        raise RuntimeError("Database connection not established. Call connect_to_mongo() first.")
    return AsyncMongoDB.database


def get_sync_database():
    """
    Get the sync MongoDB database instance.
    
    Returns:
        Database: The sync database instance
        
    Note:
        This is mainly used for operations that require synchronous access.
        Prefer the async version when possible.
    """
    if SyncMongoDB.database is None:
        # Create sync client if not exists
        SyncMongoDB.client = MongoClient(settings.MONGODB_URL)
        SyncMongoDB.database = SyncMongoDB.client[settings.MONGODB_DATABASE]
    
    return SyncMongoDB.database


async def ping_database() -> bool:
    """
    Ping the database to check connectivity.
    
    Returns:
        bool: True if database is accessible, False otherwise
    """
    try:
        if AsyncMongoDB.client:
            await AsyncMongoDB.client.admin.command('ping')
            return True
    except Exception as e:
        logger.error(f"Database ping failed: {e}")
    return False

