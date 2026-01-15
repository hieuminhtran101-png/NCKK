# 🤖 AI HANDOFF DOCUMENTATION

**For:** The next AI agent that will maintain/upgrade this project  
**Version:** 2.0 (MongoDB + JWT + RBAC)  
**Created:** January 15, 2026

---

## 📋 PROJECT OVERVIEW

This is a **FastAPI-based AI Student Schedule Management System** with:

- User authentication (JWT + password hashing)
- MongoDB for persistent storage
- Role-based access control (RBAC)
- LLM integration (Hugging Face)
- Telegram bot scaffold
- Background job scheduler

**Core Goal:** Manage student schedules, send reminders, and answer questions using LLM.

---

## 🗂️ PROJECT STRUCTURE

```
fastapi-books/
├── app/
│   ├── main.py                      # FastAPI app setup
│   ├── api/
│   │   └── endpoints/
│   │       ├── agent.py             # /chat, /agent/interpret
│   │       ├── auth.py              # /auth/register, /login
│   │       ├── events.py            # /events CRUD
│   │       ├── schedules.py         # /schedules CRUD
│   │       ├── public_events.py     # /public-events CRUD
│   │       └── telegram.py          # /telegram endpoints
│   │
│   ├── core/
│   │   ├── auth.py                  # OLD: In-memory auth (DEPRECATED)
│   │   ├── auth_mongo.py            # NEW: MongoDB auth with roles
│   │   ├── llm.py                   # Hugging Face LLM wrapper
│   │   ├── agent.py                 # Intent dispatcher
│   │   ├── permissions.py           # NEW: RBAC decorators
│   │   ├── events.py                # Event management logic
│   │   ├── schedules.py             # Schedule management
│   │   ├── public_events.py         # Public event logic
│   │   ├── telegram.py              # Telegram bot logic
│   │   └── scheduler.py             # Background jobs (APScheduler)
│   │
│   └── db/
│       └── mongodb.py               # NEW: MongoDB connection & setup
│
├── tests/
│   ├── test_auth.py                 # Auth tests
│   ├── test_events.py               # Event CRUD tests
│   ├── test_chat_endpoint.py        # /chat tests
│   ├── test_llm.py                  # LLM tests
│   └── ... (other tests)
│
├── .env                              # Environment variables (GITIGNORE!)
├── requirements.txt                 # Python dependencies
├── USAGE_GUIDE.md                   # User documentation (UPDATED)
├── AI_HANDOFF.md                    # This file
└── ... (other documentation)
```

---

## 🔑 KEY COMPONENTS & THEIR PURPOSE

### 1. **app/db/mongodb.py** (NEW)

**Purpose:** MongoDB connection management

**Key Functions:**

- `connect_db()` - Connect to MongoDB on startup
- `disconnect_db()` - Cleanup on shutdown
- `create_indexes()` - Create database indexes
- `get_db()` - Get current database connection

**How it works:**

```python
# In main.py lifespan
await connect_db()  # Connect on startup
# ... app runs ...
await disconnect_db()  # Cleanup on shutdown
```

**To upgrade:**

- Add connection pooling for high-load
- Implement replica set support
- Add database migration system (Alembic)

---

### 2. **app/core/auth_mongo.py** (NEW)

**Purpose:** Authentication with MongoDB + JWT + Roles

**Key Functions:**

```python
async def register_user(db, email, password, full_name, role="user")
async def login_user(db, email, password) -> {user_id, role, token}
async def get_user_by_id(db, user_id) -> User
async def verify_token(token) -> {user_id, role, exp}
async def has_role(db, user_id, required_role) -> bool
```

**User Roles:**

- `admin` - Full access
- `instructor` - Can create public events, view schedules
- `user` - Student (default)

**To upgrade:**

- Add `refresh_token` endpoint
- Add `change_password` endpoint
- Add `forgot_password` email flow
- Add OAuth2 integration (Google, GitHub)
- Add 2FA (Two-Factor Authentication)

---

### 3. **app/core/permissions.py** (NEW)

**Purpose:** RBAC decorators and utilities

**Key Components:**

```python
class UserRole(Enum): # admin, instructor, user
class PermissionChecker: # Generic permission checker

@require_role("admin")  # Decorator to check role
def some_admin_endpoint():
    ...

async def check_admin(db, user_id) -> bool
async def check_role(db, user_id, role) -> bool
```

**To upgrade:**

- Add fine-grained permissions (not just roles)
- Add permission inheritance
- Add audit logging (who did what, when)

---

### 4. **app/core/auth.py** (OLD - DEPRECATED)

**Status:** Keep for backward compatibility with in-memory tests

**Don't modify this.** Use `auth_mongo.py` instead.

**Migration done:**

- In-memory dicts → MongoDB
- User roles added
- JWT signature verification added

---

### 5. **app/core/llm.py**

**Purpose:** Hugging Face LLM integration

**Key Functions:**

```python
parse_question_to_json(question) -> {intent, confidence, entities}
get_chat_response(message, context) -> str
_parse_question_heuristic(question) -> {intent, confidence}  # Fallback
```

**Supported Intents:**

- `get_schedule` - View class schedule
- `get_free_time` - Find free time slots
- `check_availability` - Check if available
- `create_event` - Create reminder
- `chat` - Natural conversation

**To upgrade:**

- Add local model support (no API key needed)
- Add caching (Redis) for repeated questions
- Add multi-language support
- Add sentiment analysis

---

### 6. **app/core/scheduler.py**

**Purpose:** Background jobs (APScheduler)

**Current Job:**

- Every 1 minute: Check events → send Telegram reminders

**To upgrade:**

- Add email reminders
- Add SMS reminders
- Add notification history logging
- Handle timezone properly

---

## ⚙️ COMMON MODIFICATION POINTS

### Adding a New Endpoint

**Step 1:** Define in Pydantic model

```python
# app/api/endpoints/new_feature.py
from fastapi import APIRouter, Header, HTTPException
from app.db.mongodb import get_db
from app.core.permissions import check_admin

router = APIRouter()

@router.post("/new-feature")
async def create_feature(
    data: dict,
    authorization: str = Header(None),
    x_user_id: str = Header(None)
):
    db = get_db()

    # Option 1: Use header-based auth (simple)
    if not x_user_id:
        raise HTTPException(401, "Missing X-User-Id")

    # Option 2: Use JWT token (recommended)
    from app.core.auth_mongo import verify_token
    payload = verify_token(authorization.split(" ")[1])
    if not payload:
        raise HTTPException(401, "Invalid token")
    user_id = payload["user_id"]

    # Check permission
    if not await check_admin(db, user_id):
        raise HTTPException(403, "Admin only")

    # Do something
    result = await db.features.insert_one(data)
    return {"ok": True, "feature_id": str(result.inserted_id)}
```

**Step 2:** Add to main.py

```python
from app.api.endpoints import new_feature
app.include_router(new_feature.router)
```

**Step 3:** Test

```bash
pytest tests/test_new_feature.py -v
```

---

### Adding a New MongoDB Collection

**Step 1:** Add to mongodb.py indexes

```python
async def create_indexes():
    # ... existing code ...

    # New collection
    new_col = db["new_collection"]
    await new_col.create_index("field_name")
    await new_col.create_index([("field1", ASCENDING), ("field2", DESCENDING)])
```

**Step 2:** Create CRUD functions

```python
# app/core/new_feature.py
async def create_new(db, data: dict) -> str:
    col = db["new_collection"]
    result = await col.insert_one(data)
    return str(result.inserted_id)

async def get_new(db, id: str):
    from bson import ObjectId
    col = db["new_collection"]
    return await col.find_one({"_id": ObjectId(id)})

async def update_new(db, id: str, data: dict):
    from bson import ObjectId
    col = db["new_collection"]
    await col.update_one({"_id": ObjectId(id)}, {"$set": data})

async def delete_new(db, id: str):
    from bson import ObjectId
    col = db["new_collection"]
    await col.delete_one({"_id": ObjectId(id)})
```

---

### Changing User Role

**Important:** User roles are baked into JWT token. Token won't update until user logs in again.

```python
# To change user role:
async def upgrade_user_to_instructor(db, user_id: str):
    from bson import ObjectId
    users_col = db["users"]
    await users_col.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"role": "instructor", "updated_at": datetime.utcnow()}}
    )
    # User must login again to get new token with new role
```

---

## 🧪 TESTING STRATEGY

### Running Tests

```bash
# All tests
pytest -v

# Specific test file
pytest tests/test_auth.py -v

# Specific test
pytest tests/test_auth.py::test_register_user -v

# With output
pytest -v -s

# Coverage report
pytest --cov=app tests/
```

### Test Database Setup

```python
# tests/conftest.py (create if not exists)
import pytest
from motor.motor_asyncio import AsyncClient

@pytest.fixture(autouse=True)
async def clean_test_db():
    """Clean test database before/after each test"""
    # Connect to test database
    client = AsyncClient("mongodb://localhost:27017")
    db = client["fastapi_books_test"]

    # Clean all collections
    for col_name in await db.list_collection_names():
        await db[col_name].delete_many({})

    yield db

    # Cleanup
    client.close()
```

### Common Test Patterns

```python
# Test creating resource
async def test_create_event(clean_test_db):
    db = clean_test_db
    from app.core.events import create_event

    event = await create_event(db, user_id="123", data={...})
    assert event["title"] == "Test Event"

# Test permission denied
async def test_user_cannot_create_public_event(clean_test_db):
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.post(
        "/public-events",
        headers={"X-User-Id": "regular_user"},
        json={...}
    )
    assert response.status_code == 403

# Test endpoint with JWT
async def test_endpoint_with_token():
    token = create_access_token("user123", "user")
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

---

## 📊 MIGRATION PATH (In-Memory → MongoDB)

**Step 1: Data Migration**

```python
# Export in-memory data
users_data = _USERS.copy()
events_data = _EVENTS.copy()

# Insert into MongoDB
for user in users_data.values():
    await db.users.insert_one(user)

for event in events_data.values():
    await db.events.insert_one(event)
```

**Step 2: Update Core Functions**

- ✅ auth.py → auth_mongo.py (done)
- TODO: events.py → use MongoDB
- TODO: schedules.py → use MongoDB
- TODO: public_events.py → use MongoDB

**Step 3: Update Tests**

- TODO: Use test MongoDB database
- TODO: Clean database before/after tests

**Step 4: Rollback Plan**

- Keep in-memory functions as fallback
- Use `try/except` to catch MongoDB errors
- Log failures for debugging

---

## 🚀 RECOMMENDED UPGRADES (Priority Order)

### Phase 3.1: Complete MongoDB Migration (High Priority)

- [x] MongoDB connection ✅
- [x] User auth with roles ✅
- [x] JWT + permissions ✅
- [ ] Migrate events.py to MongoDB
- [ ] Migrate schedules.py to MongoDB
- [ ] Migrate public_events.py to MongoDB
- [ ] Update all tests for MongoDB
- **Effort:** 2-3 days

### Phase 3.2: Authentication Improvements (Medium Priority)

- [ ] `POST /auth/refresh` - Refresh expired tokens
- [ ] `POST /auth/change-password` - Change password
- [ ] `POST /auth/forgot-password` - Password reset flow
- [ ] `POST /auth/me` - Get current user info
- [ ] Email verification for new accounts
- **Effort:** 2-3 days

### Phase 3.3: Telegram Bot Integration (Medium Priority)

- [ ] Real Telegram Bot token setup
- [ ] JWT token for `/start` command
- [ ] Webhook verification (Telegram signature)
- [ ] Real Telegram API (not outbox)
- [ ] Chat natural language forwarding
- **Effort:** 2-3 days

### Phase 4: Security & Hardening (High Priority)

- [ ] HTTPS/SSL for production
- [ ] CORS configuration
- [ ] Rate limiting (throttle per user)
- [ ] Input validation & sanitization
- [ ] SQL injection prevention (N/A, using MongoDB)
- [ ] CSRF tokens (if needed)
- [ ] Audit logging (who did what, when)
- **Effort:** 3-5 days

### Phase 5: Performance & Scaling (Medium Priority)

- [ ] Redis caching (frequently accessed data)
- [ ] Database connection pooling
- [ ] Query optimization (indexes, projections)
- [ ] Pagination for large result sets
- [ ] Async operations for heavy tasks
- **Effort:** 3-5 days

### Phase 6: Production Deployment (High Priority)

- [ ] Docker containerization
- [ ] Docker Compose (for MongoDB + app)
- [ ] CI/CD pipeline (GitHub Actions)
- [ ] Environment-specific config (.env.prod)
- [ ] Monitoring & alerting
- [ ] Logging to external service (ELK, Datadog)
- [ ] Error tracking (Sentry)
- **Effort:** 5-7 days

---

## 🔍 DEBUGGING TIPS

### "MongoDB connection failed"

```python
# Check connection in main.py
try:
    await connect_db()
except Exception as e:
    print(f"⚠️  MongoDB not available: {e}")
    # Run in fallback mode (in-memory)
```

### "Permission denied"

```python
# Check user role
user = await get_user_by_id(db, user_id)
print(f"User role: {user['role']}")

# Verify token
payload = verify_token(token)
print(f"Token payload: {payload}")
```

### "Test failing after changes"

```bash
# Clean test database
mongosh
use fastapi_books_test
db.users.deleteMany({})
db.events.deleteMany({})

# Run tests again
pytest -v -s
```

---

## 📖 IMPORTANT FILES TO READ

1. **USAGE_GUIDE.md** - Full API documentation + error handling
2. **STATUS.md** - Project roadmap and status
3. **TELEGRAM_BOT_DESIGN.md** - Telegram integration design
4. **requirements.txt** - All dependencies
5. **.env.example** - Environment variables template

---

## 🎓 KNOWLEDGE BASE

### When adding a new feature:

1. Check if similar feature exists
2. Follow existing code patterns
3. Add appropriate role checks
4. Write tests first (TDD)
5. Update USAGE_GUIDE.md

### When debugging:

1. Check logs: `tail -f logs/app.log`
2. Use MongoDB shell: `mongosh`
3. Use Swagger UI: http://localhost:8000/docs
4. Run pytest with `-v -s` flags

### When deploying:

1. Set strong JWT_SECRET_KEY
2. Enable HTTPS
3. Configure CORS properly
4. Use MongoDB Atlas (not local)
5. Enable monitoring & logging

---

## 🎯 NEXT AI AGENT CHECKLIST

When you take over this project:

- [ ] Read this file completely
- [ ] Read USAGE_GUIDE.md
- [ ] Run `pytest -v` (all tests should pass)
- [ ] Start server and test manually
- [ ] Check .env configuration
- [ ] Understand MongoDB schema
- [ ] Understand JWT token flow
- [ ] Understand role-based access control
- [ ] Find and fix any TODOs in code
- [ ] Update documentation as you make changes

---

**Good luck! This is a solid foundation. Build on it!** 🚀
