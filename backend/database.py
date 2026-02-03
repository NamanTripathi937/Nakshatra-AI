import os
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger("nakshatra-backend")

# MongoDB Configuration
MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "nakshatra_db"

# Async MongoDB client for FastAPI
motor_client: AsyncIOMotorClient = None
database = None

def get_database():
    """Get the async database instance"""
    return database

async def connect_to_mongo():
    """Connect to MongoDB on startup"""
    global motor_client, database
    try:
        motor_client = AsyncIOMotorClient(MONGODB_URI)
        database = motor_client[DATABASE_NAME]
        # Test connection
        await motor_client.admin.command('ping')
        logger.info(f"Successfully connected to MongoDB: {DATABASE_NAME}")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise e

async def close_mongo_connection():
    """Close MongoDB connection on shutdown"""
    global motor_client
    if motor_client:
        motor_client.close()
        logger.info("MongoDB connection closed")

# Collection - single unified collection for all session data
def get_sessions_collection():
    """Get the unified sessions collection"""
    return database["sessions"]
