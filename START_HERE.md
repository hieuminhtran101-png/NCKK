# 🚀 START HERE - Fast API Books Project

**Status:** ✅ Ready to Use  
**Date:** January 15, 2026  
**Test Status:** 35/35 passing  
**Setup Time:** 5-10 minutes

---

## 📖 What is This?

AI-powered learning schedule management system with:

- ✅ **Personal Schedule Management** - Track classes, assignments, exams
- ✅ **Smart Event Reminders** - Automatic notifications via Telegram
- ✅ **LLM Integration** - Natural language questions about your schedule
- ✅ **Public Announcements** - School-wide events and announcements
- ✅ **Background Scheduler** - Runs every minute for reminders

---

## ⚡ Quick Start (5 minutes)

### 1️⃣ **Set Up Environment**

```bash
# Clone & navigate
cd d:\fast-api-books

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ **Configure Environment Variables**

**Option A: Automatic (Recommended)**

```bash
python setup_hf_key.py
```

**Option B: Manual**

```bash
# Edit .env file
# Add: HF_API_KEY=hf_YOUR_KEY_HERE
# Get key from: https://huggingface.co/settings/tokens
```

### 3️⃣ **Run Tests** (Verify Setup)

```bash
pytest -v
# Expected: 35 passed ✅
```

### 4️⃣ **Start Server**

```bash
python -m uvicorn app.main:app --reload
# Server running: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### 5️⃣ **Test It!**

```bash
# Health check
curl http://localhost:8000/health

# Chat with LLM
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hôm nay tôi có lịch gì?"}'
```

✅ **Done!** Your system is running.

---

## 📋 Documentation Guide

**Choose what you need:**

| Document                   | Purpose                       | Read If                        |
| -------------------------- | ----------------------------- | ------------------------------ |
| **START_HERE.md**          | This file - Quick orientation | You're new here                |
| **QUICKSTART.md**          | 5-min setup checklist         | You want fast setup            |
| **COMPLETE_SETUP.md**      | Full guide with all options   | You need detailed instructions |
| **LLM_CONFIG.md**          | Hugging Face configuration    | LLM not responding             |
| **API_REFERENCE.md**       | All endpoints & examples      | Building frontend/integration  |
| **SYSTEM_ARCHITECTURE.md** | Technical design              | Understanding system design    |
| **TELEGRAM_BOT.md**        | Bot implementation            | Want to build Telegram bot     |
| **TESTING.md**             | Test suite & debugging        | Tests failing or debugging     |
| **TROUBLESHOOTING.md**     | Common problems & fixes       | Something's broken             |
| **PROJECT_ROADMAP.md**     | Future plans & priorities     | What's coming next             |

---

## 🎯 Common Tasks

### "I want to use the chat endpoint"

1. Run server: `python -m uvicorn app.main:app --reload`
2. See QUICKSTART.md for curl examples
3. Visit: http://localhost:8000/docs (Swagger UI)

### "LLM responses not working"

1. Check: `echo %HF_API_KEY%` (Windows) or `echo $HF_API_KEY` (Mac/Linux)
2. If empty, run: `python setup_hf_key.py`
3. Restart server
4. See TROUBLESHOOTING.md § LLM Not Responding

### "Want to implement Telegram bot"

1. Read TELEGRAM_BOT.md (architecture & design)
2. Get bot token from @BotFather on Telegram
3. Follow implementation steps in TELEGRAM_BOT.md

### "Tests failing"

1. Check venv activated: `python -m pytest --version` (should work)
2. Run: `pytest -v` to see details
3. See TESTING.md § Common Test Failures

### "Database not connecting"

1. MongoDB running? Check: `netstat -ano | findstr :27017`
2. Start MongoDB if needed
3. Check .env: `MONGODB_URL=mongodb://localhost:27017`
4. See TROUBLESHOOTING.md § Database Connection

---

## 🏗️ Project Structure

```
fast-api-books/
├── START_HERE.md              ← You are here
├── QUICKSTART.md              ← Fast setup
├── COMPLETE_SETUP.md          ← Full guide
├── API_REFERENCE.md           ← Endpoint docs
├── SYSTEM_ARCHITECTURE.md     ← System design
├── LLM_CONFIG.md              ← Hugging Face setup
├── TELEGRAM_BOT.md            ← Bot guide
├── TESTING.md                 ← Test guide
├── TROUBLESHOOTING.md         ← Problem solving
├── PROJECT_ROADMAP.md         ← Future plans
│
├── .env                       ← Configuration (keep secret!)
├── requirements.txt           ← Python dependencies
├── setup_hf_key.py           ← Easy setup script
├── docker-compose.yml         ← Docker setup
├── pytest.ini                 ← Test configuration
│
├── app/
│   ├── main.py               ← FastAPI app
│   ├── core/
│   │   ├── config.py         ← Settings & validation
│   │   ├── auth.py           ← JWT authentication
│   │   ├── llm.py            ← Hugging Face wrapper
│   │   ├── scheduler.py      ← Background tasks
│   │   ├── redis.py          ← Redis cache
│   │   └── telegram.py       ← Telegram integration
│   ├── db/
│   │   └── mongodb.py        ← Database connection
│   ├── schemas/              ← Pydantic models
│   │   ├── user.py
│   │   ├── agent.py
│   │   ├── event.py
│   │   ├── schedule.py
│   │   └── ...
│   └── api/endpoints/        ← API routes
│       ├── agent.py          ← /agent endpoints
│       ├── chat.py           ← /chat endpoint (LLM)
│       ├── auth.py           ← /auth endpoints
│       ├── events.py         ← /events endpoints
│       ├── schedules.py      ← /schedules endpoints
│       ├── telegram.py       ← /telegram endpoints
│       └── ...
│
├── tests/                    ← Test suite
│   ├── test_auth.py
│   ├── test_chat_endpoint.py
│   ├── test_hf_config.py
│   ├── test_llm.py
│   └── ...
│
├── frontend/                 ← React frontend (optional)
│   ├── src/
│   ├── package.json
│   └── ...
│
└── _archive/                 ← Old/deprecated files
    └── docs/                 ← Archived documentation
```

---

## 🔧 Prerequisites

- ✅ **Python 3.8+** - [Download](https://www.python.org)
- ✅ **MongoDB** - [Download MongoDB Community](https://www.mongodb.com/try/download/community)
- ✅ **Node.js 16+** (optional, for frontend) - [Download](https://nodejs.org)
- ✅ **Hugging Face API Key** - [Get Free Key](https://huggingface.co/settings/tokens)

---

## 🚀 Next Steps

### Immediate

- [ ] Follow QUICKSTART.md (5 minutes)
- [ ] Run tests: `pytest -v`
- [ ] Start server and test /chat endpoint
- [ ] Configure HF_API_KEY: `python setup_hf_key.py`

### This Week

- [ ] Read API_REFERENCE.md for endpoint details
- [ ] Explore http://localhost:8000/docs (interactive API docs)
- [ ] Create sample schedules and events
- [ ] Test different question types with LLM

### This Month

- [ ] Implement Telegram bot (see TELEGRAM_BOT.md)
- [ ] Set up database migration if needed
- [ ] Configure production deployment
- [ ] Add frontend integration

---

## 📊 System Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                  USER QUESTION                          │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│           FastAPI Backend (main.py)                     │
│  POST /chat endpoint receives: {"text": "..."}          │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│        LLM Pipeline (core/llm.py)                       │
│  - Validates HF_API_KEY                                │
│  - Sends to Hugging Face Inference API                 │
│  - Parses response: {intent, confidence, entities}     │
└──────────────────────┬──────────────────────────────────┘
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
    ┌──────────────┐      ┌─────────────┐
    │ Valid LLM    │      │ Fallback    │
    │ Response     │      │ Heuristics  │
    │ (HF API key) │      │ (No API key)│
    └──────────────┘      └─────────────┘
            │                     │
            └──────────┬──────────┘
                       ▼
┌─────────────────────────────────────────────────────────┐
│        Agent Dispatcher (api/endpoints/agent.py)        │
│  Routes to handler based on intent:                     │
│  - get_schedule → fetch events from MongoDB             │
│  - get_free_time → find available slots                 │
│  - check_availability → verify schedule                 │
│  - create_event → add new reminder                      │
│  - chat → return natural response                       │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│           Database & Cache Layers                       │
│  - MongoDB: persistent storage (users, schedules)       │
│  - Redis: caching & sessions                           │
│  - APScheduler: background tasks (reminders)            │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### 1. **Authentication**

- User registration & login with JWT tokens
- Password hashing with salt
- Role-based access (user, instructor, admin)

### 2. **Schedule Management**

- Create, read, update, delete personal schedules
- Support for recurring classes
- Search and filter capabilities
- Import from Excel or text

### 3. **Event Reminders**

- Personal event management
- Automatic Telegram notifications
- Customizable reminder times
- Priority classification (AI-powered)

### 4. **LLM Integration**

- Parse natural language questions
- Understand schedule-related intents
- Respond conversationally
- Fallback to heuristics if API unavailable

### 5. **Public Announcements**

- Admin creates school-wide events
- Students can view announcements
- Filter by event type (exam, registration, holiday, etc.)

---

## 📞 Getting Help

1. **Quick Issue?** → Check TROUBLESHOOTING.md
2. **Setup Problem?** → See COMPLETE_SETUP.md
3. **API Question?** → Read API_REFERENCE.md
4. **Tests Failing?** → Check TESTING.md
5. **Code Question?** → See SYSTEM_ARCHITECTURE.md

---

## 🎓 Learning Resources

- **FastAPI** - https://fastapi.tiangolo.com
- **Hugging Face Inference API** - https://huggingface.co/docs/api-inference/
- **Telegram Bot API** - https://core.telegram.org/bots/api
- **MongoDB Python** - https://pymongo.readthedocs.io
- **APScheduler** - https://apscheduler.readthedocs.io

---

## 📝 License

This project is part of learning materials. Feel free to use, modify, and distribute.

---

## 🎉 Ready to Get Started?

1. **Follow QUICKSTART.md** for fast setup (5 min)
2. **Run tests** to verify everything works
3. **Start the server** and explore /docs
4. **Read other guides** as needed

**Questions?** Check the relevant documentation file above.

**Let's build something awesome!** 🚀
