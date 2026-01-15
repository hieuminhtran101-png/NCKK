# PostgreSQL + Redis Setup for Smart Schedule System

## 🚀 Quick Start

### Windows Users

```bash
# 1. Download PostgreSQL
# https://www.postgresql.org/download/windows/
# Install with default settings

# 2. Download Redis
# https://github.com/microsoftarchive/redis/releases
# Or use: choco install redis (if Chocolatey installed)

# 3. Verify installation
psql --version
redis-cli --version
```

### Docker Users (Recommended)

```bash
# Create docker-compose.yml in project root
docker-compose up -d

# Check if running
docker ps
```

---

## 📁 Project Structure for Phase 1

```
app/
├─ db/
│  ├─ __init__.py
│  ├─ connection.py         # Database connection & pooling
│  ├─ models.py             # SQLAlchemy models
│  └─ migrations/           # Alembic migrations
│     ├─ env.py
│     ├─ script.py.mako
│     └─ versions/
│        ├─ 001_initial.py
│        └─ 002_add_tables.py
│
├─ core/
│  ├─ cache.py              # Redis cache utilities
│  └─ config.py             # Database config
│
└─ services/
   └─ migration_service.py   # MongoDB → PostgreSQL migration
```

---

## 🗄️ 1. PostgreSQL Models

Here's the SQLAlchemy models for all tables:

```python
# app/db/models.py

from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Float, Enum, ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    password_salt = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="user")  # admin, instructor, user
    telegram_chat_id = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    schedules = relationship("Schedule", back_populates="user")
    tasks = relationship("Task", back_populates="user")
    notifications = relationship("Notification", back_populates="user")


class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    location = Column(String(255))
    day_of_week = Column(Integer)  # 0=Monday, 6=Sunday
    recurring = Column(Boolean, default=False)
    recurring_pattern = Column(String(50))  # weekly, monthly, etc
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="schedules")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    deadline = Column(DateTime, nullable=False)
    priority = Column(String(20), default="medium")  # high, medium, low
    status = Column(String(20), default="pending")   # pending, in_progress, completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="tasks")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(String(50))  # schedule, deadline, reminder, etc
    is_read = Column(Boolean, default=False)
    data = Column(Text)  # JSON extra data
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="notifications")


class AILog(Base):
    __tablename__ = "ai_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    input_type = Column(String(50))  # file, text, image
    input_data = Column(Text)
    ai_output = Column(Text)
    confidence_score = Column(Float)
    processing_time = Column(Float)  # milliseconds
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 2. Database Connection

```python
# app/db/connection.py

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
import os
from app.db.models import Base

# Database URL
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost/fastapi_books"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=None,  # Use default pool
    pool_size=20,
    max_overflow=0,
    echo=False
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def drop_db():
    """Drop all tables (for testing)"""
    Base.metadata.drop_all(bind=engine)
```

---

## 3. Redis Cache

```python
# app/core/cache.py

import redis
import json
import os
from typing import Any, Optional
from datetime import timedelta

# Redis connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

class CacheService:

    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get value from cache"""
        value = redis_client.get(key)
        if value:
            try:
                return json.loads(value)
            except:
                return value
        return None

    @staticmethod
    def set(key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache (ttl in seconds)"""
        try:
            redis_client.setex(
                key,
                ttl,
                json.dumps(value) if not isinstance(value, str) else value
            )
            return True
        except:
            return False

    @staticmethod
    def delete(key: str) -> bool:
        """Delete key from cache"""
        try:
            redis_client.delete(key)
            return True
        except:
            return False

    @staticmethod
    def clear_pattern(pattern: str) -> int:
        """Clear all keys matching pattern"""
        keys = redis_client.keys(pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0

    @staticmethod
    def get_schedule_cache_key(user_id: str, date: str) -> str:
        """Generate cache key for user schedule"""
        return f"schedule:{user_id}:{date}"

    @staticmethod
    def get_user_cache_key(user_id: str) -> str:
        """Generate cache key for user preferences"""
        return f"user:{user_id}:preferences"

# Predefined cache TTLs
CACHE_TTL = {
    "schedule_daily": 3600,        # 1 hour
    "user_preferences": 86400,     # 24 hours
    "ai_response": 1800,           # 30 minutes
    "free_slots": 300,             # 5 minutes
}
```

---

## 4. Environment Variables

Add to `.env`:

```env
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/fastapi_books

# Redis
REDIS_URL=redis://localhost:6379/0

# MongoDB (for migration)
MONGODB_URL=mongodb://localhost:27017
MONGO_DATABASE_NAME=fastapi_books
```

---

## 5. Docker Compose (Optional but Recommended)

```yaml
# docker-compose.yml

version: "3.8"

services:
  postgres:
    image: postgres:15-alpine
    container_name: fastapi_postgres
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
      POSTGRES_DB: fastapi_books
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: fastapi_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  mongodb:
    image: mongo:latest
    container_name: fastapi_mongodb
    environment:
      MONGO_INITDB_DATABASE: fastapi_books
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
    healthcheck:
      test: echo 'db.runCommand("ping").ok' | mongosh localhost:27017/fastapi_books --quiet
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
  mongo_data:
```

Run with: `docker-compose up -d`

---

## 6. Migration Script (MongoDB → PostgreSQL)

```python
# app/services/migration_service.py

from pymongo import MongoClient
from sqlalchemy.orm import Session
from app.db.models import User, Schedule, Task, Notification
from app.core.auth_mongo import hash_password
from datetime import datetime
import uuid

class MigrationService:

    @staticmethod
    def migrate_users(mongo_db, pg_session: Session) -> int:
        """Migrate users from MongoDB to PostgreSQL"""
        mongo_users = mongo_db["users"].find()
        count = 0

        for mongo_user in mongo_users:
            try:
                # Check if already exists
                existing = pg_session.query(User).filter_by(
                    email=mongo_user["email"]
                ).first()

                if existing:
                    continue

                # Create new user
                user = User(
                    id=uuid.uuid4(),
                    email=mongo_user["email"],
                    password_hash=mongo_user.get("password_hash", ""),
                    password_salt=mongo_user.get("password_salt", ""),
                    full_name=mongo_user.get("full_name"),
                    role=mongo_user.get("role", "user"),
                    telegram_chat_id=mongo_user.get("telegram_chat_id"),
                    is_active=mongo_user.get("is_active", True),
                    created_at=mongo_user.get("created_at", datetime.utcnow()),
                )

                pg_session.add(user)
                count += 1

            except Exception as e:
                print(f"Error migrating user {mongo_user.get('email')}: {e}")
                continue

        pg_session.commit()
        print(f"✅ Migrated {count} users")
        return count

    @staticmethod
    def migrate_schedules(mongo_db, pg_session: Session) -> int:
        """Migrate schedules from MongoDB to PostgreSQL"""
        mongo_schedules = mongo_db["schedules"].find()
        count = 0

        for mongo_schedule in mongo_schedules:
            try:
                # Find user in PostgreSQL
                user = pg_session.query(User).filter_by(
                    email=mongo_schedule.get("email")
                ).first()

                if not user:
                    continue

                # Create schedule
                schedule = Schedule(
                    id=uuid.uuid4(),
                    user_id=user.id,
                    title=mongo_schedule.get("title", ""),
                    description=mongo_schedule.get("description"),
                    start_time=mongo_schedule.get("start_time"),
                    end_time=mongo_schedule.get("end_time"),
                    location=mongo_schedule.get("location"),
                    day_of_week=mongo_schedule.get("day_of_week"),
                    recurring=mongo_schedule.get("recurring", False),
                    created_at=mongo_schedule.get("created_at", datetime.utcnow()),
                )

                pg_session.add(schedule)
                count += 1

            except Exception as e:
                print(f"Error migrating schedule: {e}")
                continue

        pg_session.commit()
        print(f"✅ Migrated {count} schedules")
        return count

    @staticmethod
    def run_full_migration(mongo_url: str, pg_session: Session):
        """Run complete migration"""
        print("🚀 Starting migration from MongoDB to PostgreSQL...")

        # Connect to MongoDB
        mongo_client = MongoClient(mongo_url)
        mongo_db = mongo_client["fastapi_books"]

        # Run migrations
        user_count = MigrationService.migrate_users(mongo_db, pg_session)
        schedule_count = MigrationService.migrate_schedules(mongo_db, pg_session)

        print(f"\n✅ Migration complete!")
        print(f"   Users: {user_count}")
        print(f"   Schedules: {schedule_count}")

        mongo_client.close()
```

---

## 🎯 Next Steps

1. **Install PostgreSQL & Redis** (locally or Docker)
2. **Update `.env`** with database URLs
3. **Run migration script** to move data from MongoDB
4. **Update `app/main.py`** to use PostgreSQL instead of MongoDB
5. **Test all endpoints** with new database
6. **Keep MongoDB** running temporarily for safety

---

**Once PHASE 1 is done, we move to PHASE 2: Backend API Expansion!**
