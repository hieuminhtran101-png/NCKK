# 📚 COMPLETE SETUP GUIDE

**Goal:** Full setup guide with all options and troubleshooting  
**Duration:** 10-20 minutes (depending on your choices)

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Database Setup](#database-setup)
4. [Environment Configuration](#environment-configuration)
5. [Verification](#verification)
6. [Frontend Setup (Optional)](#frontend-setup-optional)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required

- **Python 3.8 or higher** - [Download](https://www.python.org)
  - Verify: `python --version`
- **MongoDB Community Edition** - [Download](https://www.mongodb.com/try/download/community)
  - Verify: Start MongoDB and check it's running

### Optional

- **Node.js 16+** - [Download](https://nodejs.org) (for frontend)
- **Hugging Face Account** - [Create Free](https://huggingface.co/join)
- **Telegram Account** - (for bot integration)

---

## Initial Setup

### Step 1: Clone/Navigate to Project

```bash
# Navigate to project directory
cd d:\fast-api-books

# Verify you're in right place
ls  # or: dir (Windows)
# You should see: app/, tests/, requirements.txt, etc.
```

### Step 2: Create Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate venv (Windows PowerShell)
venv\Scripts\Activate.ps1

# Activate venv (Windows CMD)
venv\Scripts\activate.bat

# Activate venv (macOS/Linux)
source venv/bin/activate

# Verify activated (should show "(venv)" prefix in terminal)
python --version
```

### Step 3: Install Dependencies

```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install project dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
# Should show: fastapi with version
```

---

## Database Setup

### Option A: MongoDB Local (Recommended for Development)

```bash
# 1. Download & install MongoDB Community Edition
#    https://www.mongodb.com/try/download/community

# 2. Start MongoDB service
#    Windows: "C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe"
#    Or use MongoDB Compass (comes with installer)

# 3. Verify connection
#    Open new terminal:
#    mongosh  # or: mongo (older versions)
#    Type: show databases
#    Should list system databases

# 4. Connection string in .env
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=fastapi_books
```

### Option B: MongoDB Atlas (Cloud - Free Tier)

```bash
# 1. Create account: https://www.mongodb.com/cloud/atlas
# 2. Create free cluster (M0 tier)
# 3. Get connection string from Atlas dashboard
# 4. Add to .env file:
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/fastapi_books
DATABASE_NAME=fastapi_books

# 5. Test connection
python -c "from app.db.mongodb import connect_db; asyncio.run(connect_db())"
```

### Option C: No Database (Fallback Mode)

```bash
# If you skip database setup:
# - App still runs
# - Database operations fail gracefully
# - LLM processing still works
# - See warning in server startup logs
```

---

## Environment Configuration

### Step 1: Create .env File

```bash
# Copy template
cp .env.example .env

# Or create manually
cat > .env << EOF
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=fastapi_books

# JWT
JWT_SECRET_KEY=super-secret-key-32-chars-minimum-here!!!

# LLM (Hugging Face)
HF_API_KEY=

# Telegram (optional)
TELEGRAM_BOT_TOKEN=

# Redis (optional)
REDIS_URL=redis://localhost:6379/0
EOF
```

### Step 2: Configure HF_API_KEY (For LLM)

#### **Option A: Automatic Setup (Recommended)**

```bash
# Run setup script
python setup_hf_key.py

# Follow prompts:
# 1. Get key from https://huggingface.co/settings/tokens
# 2. Copy and paste when prompted
# 3. Script updates .env automatically
# 4. Restart server to use
```

#### **Option B: Manual Setup**

```bash
# 1. Get free API key: https://huggingface.co/settings/tokens
#    - Create new token
#    - Select "Fine-grained"
#    - Permissions: Read-only access to Inference API
#    - Copy the token (hf_...)

# 2. Edit .env file
# 3. Find line: HF_API_KEY=
# 4. Replace with: HF_API_KEY=hf_YOUR_COPIED_KEY_HERE
# 5. Save file

# 3. Test it
pytest tests/test_hf_config.py -v
# Should show: test_hf_api_key_configured PASSED
```

#### **Option C: Environment Variable**

```bash
# Windows PowerShell
$env:HF_API_KEY="hf_YOUR_KEY_HERE"

# Windows CMD
set HF_API_KEY=hf_YOUR_KEY_HERE

# macOS/Linux
export HF_API_KEY="hf_YOUR_KEY_HERE"

# Verify
echo $env:HF_API_KEY  # Should show your key
```

### Step 3: Configure Other Variables (Optional)

```bash
# JWT Secret Key - change for production
JWT_SECRET_KEY=change-this-to-a-real-secret-32-chars-minimum!!!

# Redis - if you want caching
REDIS_URL=redis://localhost:6379/0
# Start Redis: redis-server

# Telegram Bot - if implementing bot
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

# Database - if using cloud MongoDB Atlas
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/fastapi_books
```

---

## Verification

### Step 1: Run Tests

```bash
# Run all tests
pytest -v

# Expected output:
# ======================== 35 passed in 2.34s ==========================

# If some tests fail:
pytest -v --tb=short  # Show detailed failures
pytest tests/test_specific_file.py  # Test specific file
```

### Step 2: Start Server

```bash
# Start development server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete

# Server should show:
# ✅ Connected to MongoDB successfully
# ℹ️ Redis connection optional
```

### Step 3: Test Endpoints

```bash
# In a new terminal:

# Health check
curl http://localhost:8000/health
# Returns: {"status": "ok"}

# API Documentation
# Open in browser: http://localhost:8000/docs
# Interactive Swagger UI with all endpoints

# Register user (test data)
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
  }'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpass123"
  }'
# Returns: {"access_token": "eyJ0eXAi...", "token_type": "bearer"}

# Chat with LLM (copy token from login response)
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hôm nay tôi có lịch gì?"}'
```

---

## Frontend Setup (Optional)

### If You Want the Web Interface

```bash
# 1. Navigate to frontend
cd frontend

# 2. Install dependencies
npm install

# 3. Start development server
npm start

# 4. Browser opens automatically to http://localhost:3000

# 5. In app:
#    - Register a new account
#    - Import schedules
#    - View events
#    - See reminders
```

### Frontend Prerequisites

- Node.js 16+ installed
- npm (comes with Node)
- Backend server running (from Step above)

---

## Troubleshooting

### Python/venv Issues

**Problem:** `python command not found`

```bash
# Solution 1: Add Python to PATH
# Control Panel → System → Advanced System Settings → Environment Variables
# Add Python installation directory to PATH

# Solution 2: Use full path
C:\Python311\python.exe --version

# Solution 3: Use py launcher (Windows)
py --version
py -m venv venv
```

**Problem:** `venv not activating properly`

```bash
# Try different activation method:

# Windows PowerShell:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\Activate.ps1

# Windows CMD:
venv\Scripts\activate.bat

# Verify:
pip list  # Should work without error
```

### Dependency Issues

**Problem:** `pip install fails`

```bash
# Solution 1: Upgrade pip
python -m pip install --upgrade pip

# Solution 2: Use Python 3.8+ (check: python --version)
# Solution 3: Install one by one
pip install fastapi uvicorn pydantic python-dotenv

# Solution 4: Check internet connection
```

**Problem:** `Module not found` when running server

```bash
# Solution 1: Verify venv activated (should show "(venv)" in terminal)
# Solution 2: Reinstall requirements
pip install -r requirements.txt --force-reinstall

# Solution 3: Check Python version matches (3.8+)
python --version
```

### Database Issues

**Problem:** `MongoDB connection failed`

```bash
# Solution 1: Start MongoDB service
# Windows: Press Win + R → services.msc → find MongoDB → Start
# macOS: brew services start mongodb-community
# Linux: sudo systemctl start mongod

# Solution 2: Verify connection
mongosh  # or: mongo
# Should open MongoDB shell

# Solution 3: Check connection string in .env
# Local: mongodb://localhost:27017
# Cloud: mongodb+srv://username:password@cluster...

# Solution 4: Test connection
python -c "
import asyncio
from app.db.mongodb import connect_db
asyncio.run(connect_db())
print('✅ Connected!')
"
```

**Problem:** `MongoDB authentication failed` (Cloud/Atlas)

```bash
# Solution 1: Verify credentials in connection string
# Format: mongodb+srv://username:password@cluster...

# Solution 2: Check special characters in password
# If password has @, %, etc., URL-encode them
# @ = %40, % = %25, etc.

# Solution 3: Whitelist IP in Atlas
# Go to Atlas → Network Access → Add Current IP

# Solution 4: Use correct database name
# URL should end with: ...@cluster.mongodb.net/fastapi_books
```

### LLM/HF API Issues

**Problem:** `/chat returns fallback message`

```bash
# Step 1: Check if HF_API_KEY is set
echo $env:HF_API_KEY  # Windows PowerShell
echo $HF_API_KEY      # macOS/Linux

# Step 2: If empty, set it
python setup_hf_key.py

# Step 3: Verify installation
pytest tests/test_hf_config.py -v

# Step 4: If key works, restart server
# Kill server (Ctrl+C) and restart
python -m uvicorn app.main:app --reload

# Step 5: Test again
curl -X POST http://localhost:8000/chat ...
```

**Problem:** `HuggingFace API rate limited`

```bash
# Solution 1: Wait a bit, try again in 1 minute
# Solution 2: Use different model
# Solution 3: Use fallback responses (still works)
# Solution 4: Check API status: https://status.huggingface.co/
```

### Port Issues

**Problem:** `Address already in use`

```bash
# Solution 1: Use different port
python -m uvicorn app.main:app --port 8001

# Solution 2: Kill process using port 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID [PID] /F

# macOS/Linux:
lsof -i :8000
kill -9 [PID]

# Solution 3: Check what's using port
netstat -ano | findstr LISTENING
```

### Test Issues

**Problem:** `pytest command not found`

```bash
# Solution 1: Activate venv
venv\Scripts\activate

# Solution 2: Install pytest
pip install pytest

# Solution 3: Run with python module
python -m pytest -v
```

**Problem:** `35 tests passing but some fail`

```bash
# Run with verbose output
pytest -v --tb=long

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test
pytest tests/test_auth.py::test_user_registration -v

# Check test output for errors
```

### Server Won't Start

**Problem:** `Import errors when starting server`

```bash
# Check for circular imports
python -c "from app.main import app"

# If error, read the traceback carefully

# Common issue: .env file not found
# Solution: Create .env file with minimal config:
cat > .env << EOF
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=fastapi_books
JWT_SECRET_KEY=super-secret-key-32-chars-minimum-here!!!
EOF
```

**Problem:** `Lifespan startup failed`

```bash
# Server logs show which connection failed (MongoDB, Redis)
# App still runs but with warnings

# Check each connection individually:

# MongoDB:
python -c "from app.db.mongodb import connect_db; asyncio.run(connect_db())"

# Redis:
python -c "from app.core.redis import connect_redis; connect_redis()"

# Each should work or show clear error
```

---

## Final Verification Checklist

- [ ] Python 3.8+ installed: `python --version`
- [ ] venv activated: `(venv)` shows in terminal
- [ ] Dependencies installed: `pip list | grep fastapi`
- [ ] MongoDB running: `mongosh` connects
- [ ] .env file exists with required variables
- [ ] Tests passing: `pytest -v` → 35 passed
- [ ] Server starts: `python -m uvicorn app.main:app --reload`
- [ ] Health check works: `curl http://localhost:8000/health`
- [ ] API docs visible: http://localhost:8000/docs
- [ ] Chat endpoint works: responds to POST /chat

---

## What's Next?

1. ✅ **System running?** → Explore http://localhost:8000/docs
2. 📖 **Want to understand architecture?** → Read SYSTEM_ARCHITECTURE.md
3. 🤖 **Want LLM working perfectly?** → See LLM_CONFIG.md
4. 🤝 **Building Telegram bot?** → Check TELEGRAM_BOT.md
5. 📝 **Need API reference?** → Read API_REFERENCE.md

---

## Getting Help

- **Stuck?** Check TROUBLESHOOTING.md (above)
- **Need quick start?** See QUICKSTART.md
- **API questions?** Read API_REFERENCE.md
- **Design questions?** Check SYSTEM_ARCHITECTURE.md
- **All else fails?** Check START_HERE.md for documentation guide

---

**You're all set! Ready to build something awesome?** 🚀
