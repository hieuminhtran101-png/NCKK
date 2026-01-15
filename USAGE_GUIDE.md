# 📖 HƯỚNG DẪN SỬ DỤNG HỆ THỐNG - COMPREHENSIVE GUIDE

**Version:** 2.0 (MongoDB + JWT + RBAC)  
**Updated:** January 15, 2026  
**Status:** Production Ready

---

## 🎯 MỤC LỤC

1. [Cài Đặt & Setup](#cài-đặt--setup)
2. [Khái Niệm Cơ Bản](#khái-niệm-cơ-bản)
3. [API Documentation](#api-documentation)
4. [Common Errors & Fixes](#common-errors--fixes)
5. [Security Best Practices](#security-best-practices)
6. [Troubleshooting](#troubleshooting)

---

## 🔧 CÀI ĐẶT & SETUP

### Yêu Cầu Hệ Thống

```
Python 3.10+
MongoDB 4.0+ (local hoặc Atlas cloud)
FastAPI 0.128+
Motor (async MongoDB driver)
```

### 1. Cài Đặt Dependencies

```bash
# Tạo virtual environment
python -m venv venv
venv\Scripts\activate

# Cài dependencies
pip install -r requirements.txt
pip install motor pymongo  # MongoDB drivers
```

### 2. Cấu Hình MongoDB

**Option A: Local MongoDB**

```bash
# Windows: Download từ https://www.mongodb.com/try/download/community
# hoặc dùng Docker:
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

**Option B: MongoDB Atlas (Cloud)**

1. Truy cập: https://www.mongodb.com/cloud/atlas
2. Tạo free account
3. Create cluster
4. Copy connection string: `mongodb+srv://username:password@...`

### 3. Cấu Hình .env File

```env
# MongoDB
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=fastapi_books

# JWT Security (THAY ĐỔI GIÁ TRỊ!)
JWT_SECRET_KEY=your-super-secret-key-min-32-chars-long-change-me

# Hugging Face LLM
HF_API_KEY=hf_your_api_key

# Telegram (optional)
TELEGRAM_BOT_TOKEN=your_bot_token
```

⚠️ **CẢNH BÁO:**

- `JWT_SECRET_KEY` phải >= 32 ký tự trong production
- KHÔNG commit .env vào Git
- KHÔNG dùng default keys

### 4. Khởi Động Server

```bash
# Development (auto-reload)
python -m uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Kiểm tra: http://localhost:8000/docs (Swagger UI)

---

## 💡 KHÁI NIỆM CƠ BẢN

### User Roles (Phân Quyền)

```
┌─────────────────────────────────────────┐
│           ROLE HIERARCHY                │
├─────────────────────────────────────────┤
│                                         │
│ 1. ADMIN (Admin)                        │
│    └─ Full access to all features       │
│    └─ Can manage users                  │
│    └─ Can create/edit announcements     │
│                                         │
│ 2. INSTRUCTOR (Giáo viên)               │
│    └─ Can create public events          │
│    └─ Can view student schedules        │
│    └─ Can create announcements          │
│                                         │
│ 3. USER (Sinh viên)                     │
│    └─ Personal schedule management      │
│    └─ Personal reminders                │
│    └─ View public events                │
│                                         │
└─────────────────────────────────────────┘
```

### Authentication Flow

```
User Login
    ↓
POST /auth/login {email, password}
    ↓
Server verify password (PBKDF2)
    ↓
Generate JWT token with role
    ↓
Return {access_token, user_id, role}
    ↓
Client stores token in header
    ↓
Authorization: Bearer {access_token}
    ↓
Server verify token (HMAC-SHA256)
    ↓
Extract user_id + role → check permissions
    ↓
Execute action if authorized
```

### MongoDB Collections

```
┌─ users
│  ├─ _id (ObjectId)
│  ├─ email (string, unique)
│  ├─ hashed_password (string)
│  ├─ role (admin | instructor | user)
│  ├─ full_name
│  ├─ telegram_chat_id
│  ├─ is_active (boolean)
│  └─ created_at, updated_at
│
├─ events
│  ├─ _id (ObjectId)
│  ├─ user_id (reference to users)
│  ├─ title
│  ├─ start, end (DateTime)
│  ├─ remind_before_minutes
│  └─ is_sent (whether reminder sent)
│
├─ schedules
│  ├─ _id (ObjectId)
│  ├─ user_id (reference to users)
│  ├─ day_of_week (0-6)
│  ├─ course, instructor, room, time
│  └─ notes
│
└─ public_events
   ├─ _id (ObjectId)
   ├─ title, description
   ├─ event_type (exam, announcement, holiday, registration)
   ├─ start, end (DateTime)
   ├─ is_active (boolean)
   └─ created_by (admin_id)
```

---

## 📡 API DOCUMENTATION

### Authentication Endpoints

#### 1. Register User (Đăng Ký)

```http
POST /auth/register
Content-Type: application/json

{
  "email": "student@example.com",
  "password": "SecurePassword123!",
  "full_name": "Nguyễn Văn A"
}

Response 200:
{
  "ok": true,
  "user_id": "507f1f77bcf86cd799439011",
  "role": "user",
  "message": "User registered successfully"
}

Response 400:
{
  "ok": false,
  "detail": "Email already registered"
}
```

**Lưu Ý:**

- Email phải unique
- Password >= 8 ký tự, recommended >= 12
- Default role: "user" (student)
- Email không thể đổi sau khi tạo

#### 2. Login (Đăng Nhập)

```http
POST /auth/login
Content-Type: application/json

{
  "email": "student@example.com",
  "password": "SecurePassword123!"
}

Response 200:
{
  "ok": true,
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "user_id": "507f1f77bcf86cd799439011",
  "role": "user",
  "expires_in": 86400
}

Response 401:
{
  "detail": "Invalid email or password"
}
```

**Lưu Ý:**

- Token expires in 24 hours (default)
- Lưu token ở localStorage (web) hoặc Keychain (mobile)
- Gửi token qua header: `Authorization: Bearer {token}`

#### 3. Refresh Token (TODO)

```http
POST /auth/refresh
Authorization: Bearer {old_token}

Response 200:
{
  "access_token": "new_jwt_token...",
  "expires_in": 86400
}
```

---

### Schedule Endpoints (Quản Lý Lịch)

#### 1. Create Schedule Entry (Thêm Lịch)

```http
POST /schedules
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "day_of_week": 1,          // 0=Sunday, 1=Monday, ...
  "course": "Mathematics",
  "instructor": "Prof. Smith",
  "room": "A101",
  "start_time": "08:00",
  "end_time": "09:30",
  "notes": "Chapter 5-6"
}

Response 201:
{
  "ok": true,
  "schedule_id": "507f1f77bcf86cd799439012",
  "message": "Schedule created"
}
```

**Permission:** Only own schedules (USER) or all (ADMIN)

#### 2. Get Schedule (Xem Lịch)

```http
GET /schedules/{user_id}
Authorization: Bearer {access_token}

Response 200:
{
  "ok": true,
  "schedules": [
    {
      "schedule_id": "...",
      "day_of_week": 1,
      "course": "Mathematics",
      "instructor": "Prof. Smith",
      "room": "A101",
      "start_time": "08:00",
      "end_time": "09:30"
    }
  ]
}
```

**Permission:**

- INSTRUCTOR can view any user's schedule
- ADMIN can view any user's schedule
- USER can only view own schedule

#### 3. Update Schedule (Sửa)

```http
PUT /schedules/{schedule_id}
Authorization: Bearer {access_token}

{
  "course": "Advanced Math",
  "room": "A201"
}

Response 200:
{
  "ok": true,
  "message": "Schedule updated"
}
```

**Permission:** Must be owner or ADMIN

#### 4. Delete Schedule (Xóa)

```http
DELETE /schedules/{schedule_id}
Authorization: Bearer {access_token}

Response 200:
{
  "ok": true,
  "message": "Schedule deleted"
}
```

---

### Events Endpoints (Nhắc Nhở)

#### 1. Create Event (Tạo Nhắc Nhở)

```http
POST /events
Authorization: Bearer {access_token}

{
  "title": "Project Submission",
  "start": "2026-01-20T14:00:00",
  "end": "2026-01-20T15:00:00",
  "remind_before_minutes": 60
}

Response 201:
{
  "ok": true,
  "event_id": "507f1f77bcf86cd799439013",
  "message": "Event created"
}
```

**Permission:** Own events only (USER), or manage any (ADMIN)

#### 2. List Events (Xem Danh Sách)

```http
GET /events
Authorization: Bearer {access_token}

Response 200:
{
  "ok": true,
  "events": [
    {
      "event_id": "...",
      "title": "Project Submission",
      "start": "2026-01-20T14:00:00",
      "remind_before_minutes": 60,
      "is_sent": false
    }
  ]
}
```

#### 3. Update Event (Sửa)

```http
PUT /events/{event_id}
Authorization: Bearer {access_token}

{
  "remind_before_minutes": 120
}

Response 200:
{
  "ok": true
}
```

#### 4. Delete Event (Xóa)

```http
DELETE /events/{event_id}
Authorization: Bearer {access_token}

Response 200:
{
  "ok": true
}
```

---

### Public Events (Công Khai)

#### 1. Create Public Event (Admin Only)

```http
POST /public-events
Authorization: Bearer {admin_token}

{
  "title": "Midterm Exam",
  "description": "Mathematics exam",
  "event_type": "exam",      // exam | announcement | holiday | registration
  "start": "2026-02-15T08:00:00",
  "end": "2026-02-15T10:00:00"
}

Response 201:
{
  "ok": true,
  "event_id": "..."
}
```

**Permission:** ADMIN only

#### 2. Get Public Events (All Users)

```http
GET /public-events
Authorization: Bearer {access_token}

Response 200:
{
  "ok": true,
  "events": [
    {
      "event_id": "...",
      "title": "Midterm Exam",
      "event_type": "exam",
      "start": "2026-02-15T08:00:00"
    }
  ]
}
```

**Permission:** All authenticated users

#### 3. Update Public Event (Admin Only)

```http
PUT /public-events/{event_id}
Authorization: Bearer {admin_token}

{
  "title": "Midterm Exam (Updated)"
}

Response 200:
{
  "ok": true
}
```

#### 4. Delete Public Event (Admin Only)

```http
DELETE /public-events/{event_id}
Authorization: Bearer {admin_token}

Response 200:
{
  "ok": true
}
```

---

### LLM Chat Endpoint

#### POST /chat (LLM-Powered Q&A)

```http
POST /chat
Authorization: Bearer {access_token}

{
  "text": "Hôm nay tôi có bao nhiêu buổi học?"
}

Response 200:
{
  "ok": true,
  "action": "get_schedule",
  "result": {
    "events": [
      {
        "title": "Mathematics",
        "start": "2026-01-15T08:00:00",
        "end": "2026-01-15T09:30:00"
      }
    ]
  },
  "messages": ["Bạn có 2 buổi học hôm nay"]
}
```

---

## ⚠️ COMMON ERRORS & FIXES

### Error 1: "Invalid Authorization header"

```
Status: 401
Detail: "Invalid Authorization header"
```

**Nguyên nhân:**

- Quên "Bearer " prefix
- Token hết hạn
- Token không hợp lệ

**Cách Fix:**

```
❌ WRONG: Authorization: {token}
✅ RIGHT: Authorization: Bearer {token}

❌ WRONG: Authorization: bearer {token}
✅ RIGHT: Authorization: Bearer {token}
```

---

### Error 2: "Forbidden - Insufficient permissions"

```
Status: 403
Detail: "Insufficient permissions"
```

**Nguyên nhân:**

- Người dùng không có role cần thiết
- Cố gắng xem/sửa dữ liệu của người khác
- Role = "user" nhưng endpoint yêu cầu "instructor"

**Cách Fix:**

```
// Check role trước khi call API
GET /auth/me → {role: "user"}

// USER cannot create public events
❌ POST /public-events (403)
✅ Hỏi ADMIN để tạo

// USER cannot view other's schedule
❌ GET /schedules/other_user_id (403)
✅ GET /schedules/own_user_id (200)
```

---

### Error 3: "Email already registered"

```
Status: 400
Detail: "Email already registered"
```

**Nguyên nhân:**

- Email đã được đăng ký trước đó

**Cách Fix:**

```
// Use different email
POST /auth/register
{
  "email": "different@example.com",  // Thay email khác
  "password": "..."
}

// OR reset password nếu quên (TODO)
POST /auth/forgot-password
{
  "email": "existing@example.com"
}
```

---

### Error 4: "MongoDB connection failed"

```
Status: 500
Detail: "Internal server error"
Console: "MongoDB connection failed: [Errno 111] Connection refused"
```

**Nguyên nhân:**

- MongoDB server không chạy
- Connection string sai
- MongoDB Atlas quota exceeded

**Cách Fix:**

```bash
# Check MongoDB running
docker ps | grep mongodb
# or
mongosh  # Local connection

# Check connection string
echo $MONGODB_URL
# Should be: mongodb://localhost:27017
# or: mongodb+srv://user:pass@cluster.mongodb.net/

# Restart MongoDB
docker stop mongodb && docker start mongodb

# Or use in-memory fallback (development only)
# Comment out await connect_db() in main.py
```

---

### Error 5: "Invalid or expired token"

```
Status: 401
Detail: "Invalid or expired token"
```

**Nguyên nhân:**

- Token hết hạn (24 giờ)
- JWT_SECRET_KEY đổi
- Token bị tamper

**Cách Fix:**

```
// Đăng nhập lại để lấy token mới
POST /auth/login
{
  "email": "...",
  "password": "..."
}

// Hoặc dùng refresh endpoint (TODO)
POST /auth/refresh
Authorization: Bearer {old_token}
```

---

### Error 6: "CORS error - No 'Access-Control-Allow-Origin' header"

```
Status: 0
Error: "Access to XMLHttpRequest at 'http://localhost:8000/...'
from origin 'http://localhost:3000' has been blocked by CORS policy"
```

**Nguyên nhân:**

- Frontend và backend trên khác port
- CORS không được config

**Cách Fix:**

```python
# app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### Error 7: "PyMongo or Motor not installed"

```
ModuleNotFoundError: No module named 'motor'
```

**Cách Fix:**

```bash
pip install motor pymongo
```

---

## 🔐 SECURITY BEST PRACTICES

### 1. Password Security

```python
# ✅ GOOD - 12+ characters, mixed case
password = "MySecure@Password123"

# ❌ BAD - Too simple
password = "123456"
password = "password"
password = "qwerty"
```

**Hashing:** PBKDF2-SHA256 (100,000 iterations)

### 2. JWT Token Security

```python
# ✅ GOOD - Long, random secret key
JWT_SECRET_KEY = "your-super-secret-key-min-32-chars-long-change-me-in-production"

# ❌ BAD - Short, predictable
JWT_SECRET_KEY = "secret"
JWT_SECRET_KEY = "default-key"
JWT_SECRET_KEY = "123456"
```

**Token lifespan:** 24 hours (configurable)

### 3. Authorization Header

```javascript
// ✅ GOOD
const headers = {
  Authorization: `Bearer ${token}`,
  "Content-Type": "application/json",
};

// ❌ BAD - Don't send token in URL
fetch(`/api/data?token=${token}`);

// ❌ BAD - Don't log tokens
console.log(token);
```

### 4. MongoDB Security

```
Production (MongoDB Atlas):
├─ Use strong password
├─ Enable IP whitelisting
├─ Use connection string encryption
└─ Enable audit logging

Development (Local MongoDB):
├─ Disable authentication (OK for dev)
├─ Use bind_ip: 127.0.0.1 (local only)
└─ Don't expose to public network
```

### 5. Environment Variables

```env
# ✅ GOOD - .env file (gitignore)
JWT_SECRET_KEY=super-secret-key
MONGODB_URL=mongodb://user:pass@...

# ❌ BAD - Hardcoded
SECRET_KEY = "secret" // in code

# ❌ BAD - Committed to Git
// .env file in git repo
```

### 6. Role-Based Access Control (RBAC)

```
┌─ Admin
│  ├─ Can delete any user
│  ├─ Can modify any schedule/event
│  └─ Can view all data
│
├─ Instructor
│  ├─ Can create public events
│  ├─ Can view student schedules
│  └─ Cannot delete users
│
└─ User (Student)
   ├─ Can only view own data
   ├─ Cannot create public events
   └─ Cannot view other students' data
```

**Enforcement:**

```python
# Check in every endpoint
if user_role != "admin" and resource_owner_id != user_id:
    raise HTTPException(403, "Forbidden")
```

---

## 🐛 TROUBLESHOOTING

### Problem: "Slow API response"

**Diagnosis:**

```bash
# Check MongoDB performance
db.collection.find({}).explain("executionStats")

# Check API logs
tail -f logs/app.log
```

**Solutions:**

- Add indexes: `await create_indexes()` in mongodb.py
- Optimize queries (use projection, filtering)
- Use caching (Redis)

---

### Problem: "High memory usage"

**Causes:**

- Too many connections to MongoDB
- Large result sets in memory

**Solutions:**

```python
# Use cursor.limit() để paginate
async for doc in collection.find({}).limit(10):
    print(doc)

# Use cursor.skip() cho pagination
collection.find({}).skip(20).limit(10)
```

---

### Problem: "Data not persisting"

**Check:**

1. MongoDB running? `docker ps | grep mongodb`
2. Connection string correct? `echo $MONGODB_URL`
3. Insert actually executed?

**Debug:**

```bash
# Login to MongoDB
mongosh

# Check database
use fastapi_books
db.users.find()
db.events.find()
```

---

### Problem: "Tests failing after MongoDB migration"

**Solution:**

```python
# Use test database
# tests/conftest.py
@pytest.fixture(autouse=True)
async def clean_db():
    """Clean test database before each test"""
    db = get_db()
    await db.users.delete_many({})
    await db.events.delete_many({})
    yield
    await db.users.delete_many({})
```

---

## 📞 GETTING HELP

| Issue   | Resource                      |
| ------- | ----------------------------- |
| MongoDB | https://www.mongodb.com/docs/ |
| FastAPI | https://fastapi.tiangolo.com  |
| JWT     | https://jwt.io                |
| Motor   | https://motor.readthedocs.io/ |

---

**Last Updated:** January 15, 2026  
**Status:** Production Ready
