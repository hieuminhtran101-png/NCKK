# 📋 UPGRADE PLAN: Smart Scheduler với AI Agent

**Mục tiêu:** Nâng cấp từ FastAPI Books → Hệ thống quản lý lịch học thông minh

---

## 📊 TỔNG QUAN KỸ THUẬT

### Stack Hiện Tại

- ✅ **API:** FastAPI + Uvicorn
- ✅ **Database:** MongoDB (async PyMongo)
- ✅ **Auth:** JWT + RBAC (admin/instructor/user)
- ✅ **LLM:** Hugging Face Inference API
- ✅ **Scheduler:** APScheduler (background jobs)

### Stack Nâng Cấp

- ✅ **Cache:** Redis (session + schedule cache)
- ✅ **Notification:** Firebase Cloud Messaging (FCM) + Push
- ✅ **AI Agent:** Custom service (Parser + Priority Engine + Scheduler Assistant)
- ✅ **Frontend:** Flutter/React Native (mobile app)
- 🟡 **File Processing:** Python-docx, openpyxl, pdf2image

---

## 🎯 PHASE 1: Infrastructure & Database (1-2 ngày)

### 1.1 Docker Setup - MongoDB + Redis

**Status:** ⏳ In Progress

**Files:**

- `docker-compose.yml` - MongoDB + Redis (✅ Updated)

**Tasks:**

```bash
# Chạy containers
docker-compose up -d

# Kiểm tra MongoDB
docker exec fastapi_mongodb mongosh --eval "db.adminCommand('ping')"

# Kiểm tra Redis
docker exec fastapi_redis redis-cli ping
```

**Expected Output:**

```
MongoDB: { ok: 1 }
Redis: PONG
```

### 1.2 MongoDB Schema Design

**Collections:**

- `users` - User accounts + roles
- `schedules` - Lịch học (imported)
- `events` - Sự kiện/deadline
- `public_events` - Thông báo công khai
- `notifications` - Notification history
- `ai_logs` - AI processing logs
- `cache:*` - Cache keys (via Redis)

**Indexes:**

```javascript
db.users.createIndex({ email: 1 }, { unique: true });
db.schedules.createIndex({ user_id: 1, day_of_week: 1 });
db.events.createIndex({ user_id: 1, deadline: 1 });
db.notifications.createIndex({ user_id: 1, created_at: -1 });
```

### 1.3 Redis Setup

**Connection String:** `redis://localhost:6379/0`

**Key Patterns:**

```
schedule:user:{user_id}:today        # Hôm nay's schedule
cache:ai:parse:{request_id}          # Parse result cache
session:user:{user_id}               # Session data
notification:pending:{user_id}       # Pending notifications
```

**TTL:**

- Session: 24h
- Schedule cache: 1h
- AI result: 7 days
- Notifications: 30 days

---

## 🎯 PHASE 2: AI Agent Service (2-3 ngày)

### 2.1 Input Parser - Trích xuất thông tin

**File:** `app/core/ai_agent.py`

**Chức năng:**

```python
class InputParser:
    def parse_excel(file_path: str) -> List[Schedule]
        # Trích: Môn học, Giờ, Phòng, Ghi chú

    def parse_image(image_path: str) -> str
        # OCR → Text → parse_text()

    def parse_text(text: str) -> List[Event]
        # "Ngày 15/1 phòng 123 lịch Toán"
        # → {date: 15/1, room: 123, subject: Toán}
```

**Dependencies:**

```bash
pip install python-docx openpyxl pdf2image pytesseract pillow
```

### 2.2 Priority Engine - Phân loại quan trọng

**File:** `app/core/ai_priority.py`

**Logic:**

```python
class PriorityEngine:
    def classify(event: Event) -> Priority
        # Quan trọng (Đỏ) - Thay đổi phòng, thi cử
        # Bình thường (Vàng) - Lịch bình thường
        # Spam (Xám) - Ghi chú nhỏ

        score = 0
        score += has_keyword("phòng") * 10  # Room change
        score += has_keyword("thi") * 15    # Exam
        score += has_keyword("nộp") * 8     # Submission
        score += is_deadline() * 5

        if score >= 15:
            return Priority.CRITICAL
        elif score >= 8:
            return Priority.HIGH
        else:
            return Priority.LOW
```

### 2.3 Scheduler Assistant - Gợi ý thời gian

**File:** `app/core/ai_scheduler.py`

**Logic:**

```python
class SchedulerAssistant:
    def find_free_slots(user_id: str, date: str) -> List[TimeSlot]
        # Quét schedules + events của user
        # Return danh sách giờ trống 30-60 phút

        # 8am-9am ❌ Toán
        # 9am-10am ✅ FREE
        # 10am-11am ❌ Tiếng Anh
        # 11am-12pm ✅ FREE
```

---

## 🎯 PHASE 3: Notification System (2-3 ngày)

### 3.1 Firebase Cloud Messaging (FCM) Integration

**File:** `app/core/notification.py`

**Setup:**

```bash
pip install firebase-admin
```

**Configuration:**

```python
import firebase_admin
from firebase_admin import credentials, messaging

cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)

def send_push(user_id: str, title: str, body: str):
    token = db.users.findOne({"_id": user_id})["fcm_token"]
    message = messaging.Message(
        notification=messaging.Notification(title, body),
        data={"type": "schedule", "user_id": user_id},
        token=token
    )
    response = messaging.send(message)
    return response
```

### 3.2 Notification Service

**Notifications:**

| Event          | Trigger   | Message                    |
| -------------- | --------- | -------------------------- |
| Room Change    | AI detect | "⚠️ Toán chuyển sang P201" |
| Deadline Soon  | 1h trước  | "📌 Nộp bài Văn trong 1h"  |
| New Exam       | Import    | "📝 Thi Anh ngày 20/1"     |
| Event Reminder | 30 phút   | "🔔 Lịch bắt đầu lúc..."   |

**Implementation:**

```python
async def notify_schedule_change(user_id: str, old_room: str, new_room: str):
    notification = {
        "user_id": user_id,
        "type": "room_change",
        "old_room": old_room,
        "new_room": new_room,
        "created_at": datetime.utcnow(),
        "is_read": False
    }
    db.notifications.insert_one(notification)

    await send_push(user_id,
        title="Thay đổi phòng học",
        body=f"Chuyển từ {old_room} → {new_room}")
```

### 3.3 Notification History API

**Endpoints:**

```
GET /notifications                  # Danh sách notifications
GET /notifications/{id}             # Chi tiết
PUT /notifications/{id}/read        # Mark as read
DELETE /notifications/{id}          # Delete
```

---

## 🎯 PHASE 4: Mobile Frontend - Flutter/React Native (3-5 ngày)

### 4.1 Features

- **Dashboard:** Lịch hôm nay + upcoming deadlines
- **Calendar View:** Month/Week view
- **Schedule Import:** Upload Excel/Image
- **Notifications:** Push + In-app
- **Profile:** User settings + preferences
- **AI Chat:** Ask AI assistant

### 4.2 API Integration

```dart
// Flutter example
class ApiClient {
  static const BASE_URL = "http://localhost:8000";

  Future<void> registerSchedules(List<Schedule> schedules) async {
    final response = await http.post(
      Uri.parse("$BASE_URL/schedules/batch"),
      headers: {"Authorization": "Bearer $token"},
      body: json.encode(schedules)
    );
  }

  Future<void> updateFCMToken(String token) async {
    await http.post(
      Uri.parse("$BASE_URL/users/fcm-token"),
      body: json.encode({"fcm_token": token})
    );
  }
}
```

---

## 🎯 PHASE 5: Advanced Features (3-5 ngày)

### 5.1 AI Learning

- Track user preferences (preferred notification times)
- Learn important keywords (from user marking as important)
- Personalize priority classification

### 5.2 Analytics

- Dashboard: Most common subjects, deadlines, etc.
- Usage stats: API calls, notifications sent
- Performance metrics: Parse accuracy, cache hit rate

### 5.3 Integration

- **Email Reminders:** SMTP integration
- **Google Calendar Sync:** OAuth2 + Calendar API
- **Telegram Bot:** Telegram notifications too
- **Slack:** For class groups/study groups

---

## 📁 FILE STRUCTURE AFTER UPGRADE

```
app/
├── api/
│   ├── endpoints/
│   │   ├── auth.py          ✅ Existing
│   │   ├── schedules.py     ✅ Existing
│   │   ├── events.py        ✅ Existing
│   │   ├── notifications.py  🆕 New
│   │   ├── upload.py        🆕 New (file upload)
│   │   └── ai_agent.py      🆕 New (AI endpoints)
│   └── deps.py              ✅ Existing
│
├── core/
│   ├── auth.py              ✅ Existing
│   ├── auth_mongo.py        ✅ Existing
│   ├── permissions.py       ✅ Existing
│   ├── ai_agent.py          🆕 New (Parser)
│   ├── ai_priority.py       🆕 New (Priority)
│   ├── ai_scheduler.py      🆕 New (Assistant)
│   ├── notification.py      🆕 New (FCM)
│   ├── redis.py             🆕 New (Redis cache)
│   └── scheduler.py         ✅ Existing (APScheduler)
│
├── db/
│   └── mongodb.py           ✅ Existing
│
├── models/
│   ├── user.py              ✅ Existing
│   ├── schedule.py          ✅ Existing
│   ├── event.py             ✅ Existing
│   ├── notification.py      🆕 New
│   └── ai_request.py        🆕 New
│
├── schemas/
│   ├── user.py              ✅ Existing
│   ├── schedule.py          ✅ Existing
│   ├── event.py             ✅ Existing
│   ├── notification.py      🆕 New
│   └── ai_agent.py          🆕 New
│
└── main.py                  ✅ Update (add Redis)

tests/
├── test_auth.py             ✅ Existing
├── test_schedules.py        ✅ Existing
├── test_ai_agent.py         🆕 New
├── test_notifications.py    🆕 New
└── test_integration.py      🆕 New

docker-compose.yml           ✅ Updated (MongoDB + Redis)
```

---

## 🚀 QUICK START

### Step 1: Start Services

```bash
docker-compose up -d

# Verify
docker-compose ps
```

### Step 2: Install Dependencies

```bash
pip install firebase-admin redis python-docx openpyxl pytesseract pillow
```

### Step 3: Update .env

```env
# Existing
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=fastapi_books
JWT_SECRET_KEY=...
HF_API_KEY=...

# New
REDIS_URL=redis://localhost:6379/0
FIREBASE_CREDENTIALS=firebase-key.json
FCM_SERVER_KEY=...
```

### Step 4: Run Server

```bash
python -m uvicorn app.main:app --reload
```

### Step 5: Test

```bash
# Register user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@test.com", "password": "pass123", "full_name": "Test"}'

# Upload schedule
curl -X POST http://localhost:8000/upload/schedule \
  -H "Authorization: Bearer {token}" \
  -F "file=@schedule.xlsx"

# AI Parse
curl -X POST http://localhost:8000/ai/parse \
  -H "Content-Type: application/json" \
  -d '{"text": "Toán ngày 15/1 phòng 201"}'
```

---

## ✅ COMPLETION CHECKLIST

- [ ] Phase 1: Docker + MongoDB + Redis
- [ ] Phase 2: AI Agent Parser + Priority + Scheduler
- [ ] Phase 3: FCM + Notification System
- [ ] Phase 4: Mobile App (Flutter/React Native)
- [ ] Phase 5: Advanced Features + Analytics
- [ ] Tests: Unit + Integration
- [ ] Documentation: API Docs + User Guide
- [ ] Deployment: Docker image + CI/CD

---

**Estimated Timeline:** 2-3 tuần (2-3 tuần dev + 1 tuần testing)  
**Team:** 1-2 developers (Backend) + 1 mobile dev

---

_Last Updated: January 15, 2026_
