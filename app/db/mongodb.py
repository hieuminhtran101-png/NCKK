"""
MongoDB Connection & Models
Sử dụng PyMongo (sync client - tương thích tốt hơn)
"""

import os
from pymongo import MongoClient, ASCENDING
from typing import Optional, Any
import asyncio

# MongoDB Connection
MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "fastapi_books")

# Global DB connection
db: Optional[Any] = None
client: Optional[MongoClient] = None


async def connect_db():
    """Kết nối MongoDB"""
    global db, client
    try:
        client = MongoClient(MONGODB_URL, connectTimeoutMS=10000, serverSelectionTimeoutMS=10000)
        db = client[DATABASE_NAME]
        # Ping để kiểm tra connection
        client.admin.command("ping")
        print("✅ Connected to MongoDB successfully")
        print(f"✅ Database: {DATABASE_NAME}")
        
        # Bỏ tạo indexes để tránh lỗi (có thể tạo manual sau)
        # await create_indexes()
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise


async def disconnect_db():
    """Ngắt kết nối MongoDB"""
    global db, client
    if client:
        client.close()
        print("✅ MongoDB disconnected")


async def create_indexes():
    """Tạo indexes cho performance"""
    global db
    if db is None:
        return
    
    try:
        # Users collection
        users_col = db["users"]
        users_col.create_index("email", unique=True)
        users_col.create_index("username", unique=True, sparse=True)
        
        # Events collection
        events_col = db["events"]
        events_col.create_index([("user_id", ASCENDING), ("start", ASCENDING)])
        
        # Schedules collection
        schedules_col = db["schedules"]
        schedules_col.create_index([("user_id", ASCENDING), ("day_of_week", ASCENDING)])
        
        # Public events collection
        public_events_col = db["public_events"]
        public_events_col.create_index([("event_type", ASCENDING), ("is_active", ASCENDING)])
        
        print("✅ MongoDB indexes created")
    except Exception as e:
        print(f"⚠️  Index creation warning: {e}")


def get_db():
    """Get current MongoDB connection"""
    global db
    if db is None:
        raise RuntimeError("Database not connected")
    return db
