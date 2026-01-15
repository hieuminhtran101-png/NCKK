# 📈 UPGRADE PLAN: Smart Schedule Management System with AI

**Current Status:** Basic FastAPI + MongoDB + JWT  
**Target Status:** Full-stack Smart Schedule App with AI Agent  
**Estimated Duration:** 4-6 weeks (3-5 days per phase)

---

## 🎯 Phase Overview

```
PHASE 1 (1-2 days): Database Upgrade
├─ PostgreSQL setup (primary DB)
├─ Redis setup (cache)
└─ Data migration from MongoDB

PHASE 2 (2-3 days): Backend API Expansion
├─ Schedule Service (CRUD + advanced filters)
├─ Task/Deadline Service
├─ Calendar Service
└─ Advanced API endpoints

PHASE 3 (3-4 days): AI Agent Service (Core)
├─ Input Processor (file/text parsing)
├─ Data Parser (extract info from unstructured data)
├─ Priority Engine (classify importance)
└─ Scheduler Assistant (suggest time slots)

PHASE 4 (2-3 days): Notification Service
├─ Firebase Cloud Messaging (FCM) integration
├─ Push notification templates
├─ Notification history & preferences
└─ Real-time notification delivery

PHASE 5 (3-5 days): Frontend Setup
├─ Flutter/React Native project scaffold
├─ UI components (Calendar, Dashboard, Forms)
├─ Authentication flow
└─ File upload & camera integration

PHASE 6 (2-3 days): Testing & Integration
├─ Unit tests for AI service
├─ Integration tests (API + AI + Notifications)
├─ End-to-end testing
└─ Performance testing

PHASE 7 (2-3 days): Deployment & Documentation
├─ Docker setup for all services
├─ Kubernetes manifests (optional)
├─ Production deployment guide
└─ API documentation (OpenAPI/Postman)
```

---

## 📋 PHASE 1: Database Upgrade (1-2 days)

### Current State

- ✅ MongoDB connected
- ✅ Basic user collection
- ❌ No relational structure
- ❌ No cache layer

### Target State

- ✅ PostgreSQL (primary relational DB)
- ✅ Redis (caching layer)
- ✅ Connection pooling
- ✅ Optimized queries with indexes

### Task 1.1: PostgreSQL Setup

```sql
-- Tables needed:
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR UNIQUE NOT NULL,
  password_hash VARCHAR NOT NULL,
  full_name VARCHAR,
  role ENUM('admin', 'instructor', 'user'),
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE schedules (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  title VARCHAR NOT NULL,
  description TEXT,
  start_time TIMESTAMP NOT NULL,
  end_time TIMESTAMP NOT NULL,
  location VARCHAR,
  day_of_week INT,
  recurring BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP
);

CREATE TABLE tasks (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  title VARCHAR NOT NULL,
  description TEXT,
  deadline TIMESTAMP NOT NULL,
  priority ENUM('high', 'medium', 'low'),
  status ENUM('pending', 'in_progress', 'completed'),
  created_at TIMESTAMP
);

CREATE TABLE notifications (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  title VARCHAR NOT NULL,
  message TEXT,
  type VARCHAR,
  read BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP
);

CREATE TABLE ai_logs (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  input_type VARCHAR,
  input_data TEXT,
  ai_output TEXT,
  confidence_score FLOAT,
  created_at TIMESTAMP
);
```

### Task 1.2: Redis Setup

- Install Redis (local or cloud)
- Configure connection pool
- Setup cache strategies for:
  - Daily schedule (TTL: 1 hour)
  - User preferences (TTL: 24 hours)
  - AI model responses (TTL: 30 minutes)

### Task 1.3: ORM Configuration

- Use **SQLAlchemy** + **Alembic** for schema management
- Create models for each table
- Setup connection pooling

### Task 1.4: Data Migration

- MongoDB → PostgreSQL migration script
- Validate data integrity
- Parallel testing (both DBs) for safety

---

## 📋 PHASE 2: Backend API Expansion (2-3 days)

### Current Endpoints

```
POST   /auth/register
POST   /auth/login
GET    /users/me
POST   /schedules
GET    /schedules
PUT    /schedules/{id}
DELETE /schedules/{id}
POST   /chat
```

### New Endpoints to Add

#### Schedule Service (Advanced)

```
GET    /schedules/day/{date}              # Get schedules for specific day
GET    /schedules/week/{start_date}       # Weekly view
GET    /schedules/month/{year}/{month}    # Monthly view
GET    /schedules/search?keyword=...      # Search schedules
POST   /schedules/{id}/duplicate          # Duplicate schedule (recurring)
GET    /schedules/{id}/conflicts          # Find time conflicts
POST   /schedules/{id}/share              # Share with other users
```

#### Task/Deadline Service (New)

```
POST   /tasks                              # Create task
GET    /tasks                              # Get all tasks
GET    /tasks/urgent                       # Get high-priority tasks
GET    /tasks/due-today                    # Get today's deadlines
PUT    /tasks/{id}                         # Update task
DELETE /tasks/{id}                         # Delete task
POST   /tasks/{id}/complete                # Mark as completed
```

#### Calendar Service (New)

```
GET    /calendar/events/{date}            # Get all events for date
GET    /calendar/free-slots?duration=30   # Find free time slots
POST   /calendar/suggest                  # Get AI-suggested schedule
```

#### Notifications Service (New)

```
GET    /notifications                      # Get user notifications
PUT    /notifications/{id}/read            # Mark as read
DELETE /notifications/{id}                # Delete notification
POST   /notifications/preferences          # Save FCM token & preferences
```

### Implementation Details

- Add pagination to all GET endpoints
- Add filtering (status, priority, date range)
- Add sorting options
- Implement caching with Redis
- Add rate limiting (slowdown spam)

---

## 📋 PHASE 3: AI Agent Service (3-4 days) ⭐ CORE

### Architecture

```
┌──────────────────────────────────────────┐
│         AI Agent Service                 │
├──────────────────────────────────────────┤
│                                          │
│  ┌─────────────────────────────────────┐ │
│  │ 1. Input Processor                  │ │
│  │    ├─ File parser (Excel, PDF)      │ │
│  │    ├─ Image OCR (classroom photos)  │ │
│  │    ├─ Text parser (raw messages)    │ │
│  │    └─ Validate input format         │ │
│  └─────────────────────────────────────┘ │
│                   ↓                      │
│  ┌─────────────────────────────────────┐ │
│  │ 2. Data Parser/Extractor            │ │
│  │    ├─ Extract: Time, Date, Subject  │ │
│  │    ├─ Extract: Location, Room #     │ │
│  │    ├─ NLP for ambiguous dates       │ │
│  │    └─ Handle variations (10:30 vs   │ │
│  │        10h30, 14:00 vs 2:00 PM)     │ │
│  └─────────────────────────────────────┘ │
│                   ↓                      │
│  ┌─────────────────────────────────────┐ │
│  │ 3. Priority Engine                  │ │
│  │    ├─ Keyword matching (exam, final)│ │
│  │    ├─ Time sensitivity (urgent?)    │ │
│  │    ├─ Persona-based filtering       │ │
│  │    └─ Output: {score, category}     │ │
│  └─────────────────────────────────────┘ │
│                   ↓                      │
│  ┌─────────────────────────────────────┐ │
│  │ 4. Scheduler Assistant              │ │
│  │    ├─ Find free time slots          │ │
│  │    ├─ Suggest meeting times         │ │
│  │    ├─ Check availability conflicts  │ │
│  │    └─ Recommend schedule changes    │ │
│  └─────────────────────────────────────┘ │
│                   ↓                      │
│            API Response                 │
│     {success, data, confidence}         │
└──────────────────────────────────────────┘
```

### Task 3.1: Input Processor

```python
# app/ai_service/input_processor.py

class InputProcessor:
    async def process_file(file: UploadFile) -> dict:
        """Process Excel/PDF/Image files"""
        - Read file
        - Validate format
        - Extract raw text
        - Return structured input

    async def process_text(text: str) -> dict:
        """Process raw text messages"""
        - Clean text
        - Identify sentence boundaries
        - Return structured input

    async def process_image(image: bytes) -> dict:
        """Process classroom photos"""
        - Use Tesseract/EasyOCR for OCR
        - Extract text from image
        - Return structured input
```

### Task 3.2: Data Parser/Extractor

```python
# app/ai_service/data_parser.py

class DataParser:
    async def extract_schedule_info(raw_text: str) -> dict:
        """Extract: time, date, subject, location"""
        Using:
        - Regex patterns for date/time
        - NLP for entity extraction
        - Fuzzy matching for subject names

        Output:
        {
            "subject": "Toán học",
            "start_time": "2026-01-20T10:30:00",
            "end_time": "2026-01-20T12:30:00",
            "location": "Phòng A201",
            "confidence": 0.95
        }

    async def parse_multiple_formats(text: str) -> List[dict]:
        """Handle multiple schedule formats"""
        - "10:30 - 12:30" → datetime objects
        - "10h30" → datetime objects
        - "2:00 PM" → 14:00
        - "thứ 2" (Mon) → next Monday date
        - Relative dates: "hôm nay" (today)
```

### Task 3.3: Priority Engine

```python
# app/ai_service/priority_engine.py

class PriorityEngine:
    async def classify_importance(info: dict) -> dict:
        """Classify notification importance"""

        Scoring factors:
        - Keywords (exam=HIGH, homework=MEDIUM, announcement=LOW)
        - Time sensitivity (deadline today=HIGH)
        - Subject type (core vs elective)
        - User persona (Bình ignores random stuff)

        Output:
        {
            "priority": "high|medium|low",
            "category": "exam|deadline|meeting|announcement",
            "confidence": 0.92,
            "reason": "Keywords: 'exam' detected"
        }
```

### Task 3.4: Scheduler Assistant

```python
# app/ai_service/scheduler_assistant.py

class SchedulerAssistant:
    async def find_free_slots(
        user_id: str,
        duration: int = 60,  # minutes
        date: str = None
    ) -> List[dict]:
        """Find available time slots"""
        - Query user's current schedule
        - Find gaps >= duration
        - Return: [{start: "10:00", end: "11:30"}, ...]

    async def suggest_meeting_time(
        user_id: str,
        participants: List[str],
        duration: int = 60
    ) -> List[dict]:
        """Suggest meeting time for multiple people"""
        - Get free slots for all participants
        - Find intersections
        - Return top 3 suggestions

    async def check_conflicts(new_schedule: dict) -> dict:
        """Check if new schedule conflicts with existing"""
        - Check time overlaps
        - Return: {has_conflict: bool, conflicts: [...]}
```

### Task 3.5: API Endpoints for AI Service

```
POST   /ai/parse-schedule             # Parse file/text → structured schedule
POST   /ai/parse-multiple             # Parse 10+ schedules at once
POST   /ai/classify-importance        # Classify notification priority
GET    /ai/free-slots?duration=30     # Find free time (next 7 days)
POST   /ai/suggest-meeting            # Suggest meeting time
GET    /ai/logs                       # View AI processing history
```

### Task 3.6: Testing AI Service

```python
# tests/test_ai_service.py

Test cases:
- Parse schedule from Excel
- Parse schedule from image
- Extract time in multiple formats
- Classify notifications (high/medium/low priority)
- Find free slots (with and without conflicts)
- Multi-person meeting suggestions
- Error handling (invalid input, OCR failure)
```

---

## 📋 PHASE 4: Notification Service (2-3 days)

### Architecture

```
Backend API
    ↓
Notification Queue (Redis)
    ↓
Firebase Cloud Messaging (FCM)
    ↓
Mobile App (Firebase plugin)
    ↓
Device Push Notification
```

### Task 4.1: Firebase Setup

- Create Firebase project
- Get FCM credentials
- Setup Firebase Admin SDK

### Task 4.2: Notification Service Code

```python
# app/services/notification_service.py

class NotificationService:
    async def send_notification(
        user_id: str,
        title: str,
        message: str,
        data: dict = None,
        priority: str = "normal"
    ) -> bool:
        """Send push notification to user's device"""

    async def schedule_notification(
        user_id: str,
        notification: dict,
        scheduled_time: datetime
    ) -> str:
        """Schedule notification for later"""

    async def send_batch(
        user_ids: List[str],
        notification: dict
    ) -> dict:
        """Send to multiple users"""
```

### Task 4.3: Notification Templates

```
Schedule Change Alert:
  "Title": "Phòng học thay đổi"
  "Body": "Môn Toán chuyển từ A201 → A205"

Deadline Reminder:
  "Title": "Deadline sắp đến"
  "Body": "Bài tập Vật lý còn 2 giờ"

New Schedule:
  "Title": "Lịch học mới"
  "Body": "Môn Anh ngữ: Thứ 3, 14:00-16:00"
```

### Task 4.4: Notification Preferences

```
User can set:
- FCM token (device ID)
- Notification types (all/important/none)
- Quiet hours (21:00-08:00)
- Disable notifications for certain subjects
```

---

## 📋 PHASE 5: Frontend Setup (3-5 days)

### Option A: Flutter (Recommended)

- Better performance
- Native look & feel
- Better offline support

### Option B: React Native

- JS ecosystem
- Faster development
- Web code sharing possible

### Core Screens to Build

```
1. Login/Register
   ├─ Email field
   ├─ Password field
   └─ Login button

2. Dashboard
   ├─ Today's schedule
   ├─ Urgent tasks
   ├─ Calendar widget
   └─ Floating action button (add schedule)

3. Calendar View
   ├─ Month view
   ├─ Week view
   ├─ Day view
   └─ Tap to see details

4. Schedule Details
   ├─ Title, time, location
   ├─ Edit button
   ├─ Share button
   ├─ Notifications toggle

5. Add/Edit Schedule
   ├─ Manual entry form
   ├─ File upload (Excel/Image)
   ├─ AI parse button
   └─ Confirm button

6. Tasks List
   ├─ All tasks
   ├─ Filter by status/priority
   ├─ Mark complete
   └─ Edit/Delete buttons

7. Notifications
   ├─ List of notifications
   ├─ Mark as read
   ├─ Settings button

8. Settings
   ├─ Profile edit
   ├─ Notification preferences
   ├─ Logout
```

### Task 5.1: Create Flutter Project

```bash
flutter create smart_schedule_app
cd smart_schedule_app

# Add dependencies:
# - dio (HTTP client)
# - provider (state management)
# - firebase_messaging (notifications)
# - table_calendar (calendar widget)
# - image_picker (file upload)
# - path_provider (local storage)
```

### Task 5.2: API Integration

```dart
// lib/services/api_service.dart
class ApiService {
  Future<AuthResponse> register(String email, String password) {}
  Future<AuthResponse> login(String email, String password) {}
  Future<List<Schedule>> getSchedules(String date) {}
  Future<Schedule> addSchedule(Schedule schedule) {}
  Future<void> uploadFile(File file) {}
}
```

---

## 📋 PHASE 6: Testing & Integration (2-3 days)

### Unit Tests

```python
tests/
├─ test_ai_service.py (20+ tests)
├─ test_parser.py (15+ tests)
├─ test_priority_engine.py (10+ tests)
├─ test_scheduler_assistant.py (10+ tests)
├─ test_notification_service.py (10+ tests)
└─ test_api_endpoints.py (30+ tests)
```

### Integration Tests

```python
# Test full user flows:
1. User registers → Login → Upload schedule → See in calendar → Get notification
2. User creates task → Set deadline → Get reminder 1 hour before
3. User shares schedule → Other user receives notification
4. AI parses file → Creates schedule → Triggers notification
```

### Performance Tests

```
- Load test: 1000 concurrent users
- Response time: <500ms for API
- AI parsing: <3s per file
- Notification delivery: <5s after trigger
```

---

## 📋 PHASE 7: Deployment & Documentation (2-3 days)

### Docker Setup

```dockerfile
# Backend API
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]

# Docker Compose: PostgreSQL + Redis + API + AI Service
```

### Deployment Options

- **Option 1:** Heroku (simple, 1-click deploy)
- **Option 2:** AWS (EC2 + RDS + ElastiCache)
- **Option 3:** DigitalOcean (simple, cheap)
- **Option 4:** Kubernetes (scalable, complex)

### Documentation to Create

- API Reference (OpenAPI/Swagger)
- AI Service Documentation
- Frontend Setup Guide
- Deployment Guide
- User Manual
- Architecture Diagram

---

## 🎯 Implementation Sequence

Start with **PHASE 1 → 3 → 2 → 4 → 5 → 6 → 7**

Why this order:

1. **DB first** (everything depends on it)
2. **AI core** (unique feature, most complex)
3. **Backend API** (expand existing code)
4. **Notifications** (depends on API)
5. **Frontend** (can work in parallel)
6. **Testing** (validate everything)
7. **Deployment** (production ready)

---

## 📊 Effort Estimation

| Phase            | Days           | Difficulty | Priority     |
| ---------------- | -------------- | ---------- | ------------ |
| 1: DB Upgrade    | 1-2            | Medium     | HIGH         |
| 2: Backend API   | 2-3            | Medium     | HIGH         |
| 3: AI Service    | 3-4            | **Hard**   | **CRITICAL** |
| 4: Notifications | 2-3            | Medium     | HIGH         |
| 5: Frontend      | 3-5            | Medium     | HIGH         |
| 6: Testing       | 2-3            | Medium     | HIGH         |
| 7: Deployment    | 2-3            | Medium     | MEDIUM       |
| **TOTAL**        | **15-23 days** | -          | -            |

---

## 🛠️ Tech Stack Summary

**Backend:**

- FastAPI (API framework)
- PostgreSQL (relational DB)
- Redis (caching)
- SQLAlchemy (ORM)
- Firebase (notifications)

**AI/ML:**

- Python NLP libraries (spaCy, NLTK)
- Tesseract/EasyOCR (image OCR)
- Regex + fuzzy matching (text extraction)
- scikit-learn (priority classification)

**Frontend:**

- Flutter or React Native (mobile)
- Provider/GetX (state management)
- Firebase (push notifications)

**DevOps:**

- Docker (containerization)
- Docker Compose (local development)
- GitHub Actions (CI/CD)

---

## 🚀 Getting Started

### Step 1: Review This Plan

- Read all sections above
- Ask questions about unclear parts
- Prioritize based on your needs

### Step 2: Start PHASE 1

- Setup PostgreSQL locally
- Setup Redis locally
- Create migration script from MongoDB
- Create SQLAlchemy models

### Step 3: Iterate

- Complete one phase fully
- Test thoroughly
- Document as you go
- Move to next phase

---

## ✅ Success Criteria

- ✅ All API endpoints work (>95% uptime)
- ✅ AI service parses files with >90% accuracy
- ✅ Notifications delivered <5s
- ✅ Frontend loads in <2s
- ✅ All tests pass (coverage >80%)
- ✅ Documentation complete
- ✅ Ready for production

---

**Ready to start? Let's go! 🚀**
