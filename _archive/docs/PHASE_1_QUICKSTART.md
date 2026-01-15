# 🚀 UPGRADE QUICK START GUIDE

## 📊 Overview

You have:

- ✅ Basic FastAPI app with MongoDB + JWT
- ✅ Test files
- 🟡 Ready to upgrade to production-grade system with AI

---

## ⚡ PHASE 1: Database Setup (Today - 1-2 hours)

### Option A: Docker (Easiest) ⭐ RECOMMENDED

```bash
# 1. Navigate to project
cd D:\fast-api-books

# 2. Start all services (PostgreSQL + Redis + MongoDB)
docker-compose up -d

# 3. Verify all running
docker ps

# Output should show:
# - fastapi_postgres (port 5432)
# - fastapi_redis (port 6379)
# - fastapi_mongodb (port 27017)

# 4. Check logs
docker-compose logs postgres
docker-compose logs redis
```

### Option B: Manual Installation (Windows)

```bash
# PostgreSQL
# Download from: https://www.postgresql.org/download/windows/
# Run installer, remember password, keep default settings

# Redis
# Download from: https://github.com/microsoftarchive/redis/releases/
# Or: choco install redis (if Chocolatey installed)

# Verify
psql --version
redis-cli ping
```

---

## 📝 Update `.env` File

Add these variables:

```env
# Existing
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=fastapi_books
JWT_SECRET_KEY=super-secret-key-32-chars-minimum-here!!!
HF_API_KEY=your-key

# NEW - PostgreSQL
DATABASE_URL=postgresql://postgres:password@localhost:5432/fastapi_books

# NEW - Redis
REDIS_URL=redis://localhost:6379/0

# NEW - AI Service
AI_CONFIDENCE_THRESHOLD=0.7
AI_MODEL=openai  # or huggingface
```

---

## 🔧 Install New Dependencies

```bash
# Activate venv
venv\Scripts\activate

# Install PostgreSQL driver + cache tools
pip install sqlalchemy psycopg2-binary redis alembic python-multipart

# Or from requirements
pip install -r requirements-phase1.txt
```

**Create `requirements-phase1.txt`:**

```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
redis==5.0.1
pydantic==2.5.0
python-dotenv==1.0.0
pymongo==4.6.0
motor==3.3.2
apscheduler==3.10.4
requests==2.31.0
alembic==1.12.1
python-multipart==0.0.6
```

---

## 📂 Create Phase 1 Code Files

I'll provide the exact code to create. Files needed:

### 1. Database Connection

```bash
# Create file: app/db/connection.py
# (Copy content from PHASE_1_DATABASE_SETUP.md)
```

### 2. SQLAlchemy Models

```bash
# Create file: app/db/models.py
# (Copy content from PHASE_1_DATABASE_SETUP.md)
```

### 3. Redis Cache Service

```bash
# Create file: app/core/cache.py
# (Copy content from PHASE_1_DATABASE_SETUP.md)
```

### 4. Migration Service

```bash
# Create file: app/services/migration_service.py
# (Copy content from PHASE_1_DATABASE_SETUP.md)
```

---

## ✅ Verify Everything Works

### Step 1: Test Database Connection

```bash
# Open Python terminal
python

# Run:
from app.db.connection import engine, init_db
init_db()  # Create all tables
print("✅ PostgreSQL connected and tables created")
exit()
```

### Step 2: Test Redis Connection

```bash
# Open Python terminal
python

# Run:
from app.core.cache import CacheService
CacheService.set("test", "hello")
print(CacheService.get("test"))  # Should print: hello
exit()
```

### Step 3: Run Server

```bash
# Terminal 1
python -m uvicorn app.main:app --reload --port 8000

# Expected output:
# ✅ Connected to MongoDB successfully (fallback)
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 4: Test API

```bash
# Terminal 2
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"pass123","full_name":"Test"}'

# Should return 201 with user_id
```

---

## 🚨 Common Issues & Solutions

### Issue 1: `psycopg2: command not found`

**Solution:** `pip install psycopg2-binary`

### Issue 2: `Cannot connect to PostgreSQL`

**Solution:**

- Check if PostgreSQL is running: `psql -U postgres`
- Check `.env` DATABASE_URL is correct
- Default password is `password`

### Issue 3: Redis connection refused

**Solution:**

- Windows: Start Redis server manually or via docker
- Check port 6379 is not in use: `netstat -ano | findstr :6379`

### Issue 4: `Module not found`

**Solution:**

```bash
# Make sure in venv
venv\Scripts\activate

# Install all deps again
pip install -r requirements-phase1.txt
```

---

## 📈 What's Next After Phase 1?

Once Phase 1 is working:

### Phase 2: Backend API Expansion (2-3 days)

- Add Task Service endpoints
- Add Calendar Service endpoints
- Add advanced filtering
- Add Redis caching to endpoints

### Phase 3: AI Agent Service (3-4 days) ⭐ CORE FEATURE

- File parser (Excel/PDF)
- Text extractor (NLP)
- Priority classifier
- Scheduler assistant

### Phase 4: Notifications (2-3 days)

- Firebase setup
- Push notifications
- Notification preferences

### Phase 5: Frontend (3-5 days)

- Flutter/React Native app
- Calendar UI
- File upload
- Real-time notifications

---

## 🎯 Success Checklist for Phase 1

- [ ] Docker running (or PostgreSQL + Redis installed)
- [ ] `.env` updated with new variables
- [ ] `app/db/connection.py` created
- [ ] `app/db/models.py` created
- [ ] `app/core/cache.py` created
- [ ] `requirements-phase1.txt` created
- [ ] All packages installed (`pip install -r requirements-phase1.txt`)
- [ ] Server starts without errors
- [ ] Can register new user (creates in PostgreSQL)
- [ ] Can login user
- [ ] Cache service works (test with `CacheService`)
- [ ] All tables created in PostgreSQL

---

## 💡 Pro Tips

1. **Keep MongoDB running** for now - acts as backup
2. **Test extensively** before moving to Phase 2
3. **Document issues** you encounter
4. **Don't skip requirements** - they're needed for later phases
5. **Use Docker** if possible - simpler setup, no conflicts

---

## 🆘 Need Help?

Check these files:

- `UPGRADE_PLAN_2026.md` - Full roadmap
- `PHASE_1_DATABASE_SETUP.md` - Detailed Phase 1 guide
- `AI_HANDOFF.md` - Architecture explanation

---

**Ready to start? Let's do PHASE 1! 🚀**

Next command:

```bash
docker-compose up -d
```

Then run server and test!
