# 📚 AI Quản lý Lịch Học và Nhắc Nhở Sự kiện

Hệ thống AI agent quản lý lịch học và tự động gửi lời nhắc cho sinh viên qua Telegram.

> **⚡ Quick Start:** Muốn cấu hình LLM ngay? Xem [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)

## 🎯 Tính Năng Chính

### 1. **Lịch Học Cá Nhân** (`/schedules`)

- Sinh viên tự nhập lịch học từng tuần
- Thông tin: môn học, giờ, phòng, giáo viên, ghi chú
- CRUD đầy đủ cho các bài học

### 2. **Sự Kiện Công Khai** (`/public-events`)

- Admin tạo sự kiện toàn trường (thi, khai giảng, đăng ký lớp, etc.)
- Các sinh viên có thể xem
- Phân loại theo loại sự kiện (exam, announcement, holiday, registration)

### 3. **Sự Kiện Cá Nhân** (`/events`)

- Sinh viên tạo các sự kiện riêng (deadline, dự án, etc.)
- Tự động gửi lời nhắc trước sự kiện qua Telegram

### 4. **AI Agent + LLM Thực** (`/chat`)

- Tích hợp Hugging Face Inference API
- Tự động phân tích câu hỏi thành intent + entities
- Chat tự nhiên cho các câu hỏi không liên quan lịch học
- Intent: `get_schedule`, `get_free_time`, `check_availability`, `create_event`, `chat`

### 5. **Bộ Lập Lịch (Scheduler)** (Background)

- Chạy mỗi 1 phút để kiểm tra sự kiện sắp tới
- Tự động gửi lời nhắc Telegram khi đến giờ

### 6. **Telegram Bot Integration**

- `/connect` - Kết nối tài khoản với Telegram
- `/webhook` - Nhận cập nhật từ Telegram
- Gửi nhắc sự kiện tự động

---

## 📁 Cấu Trúc Dự Án

```
fast-api-books/
├── app/
│   ├── core/                 # Logic chính
│   │   ├── agent.py          # Dispatcher cho các intent
│   │   ├── auth.py           # Xác thực, hash mật khẩu, JWT
│   │   ├── events.py         # Sự kiện cá nhân (CRUD)
│   │   ├── public_events.py  # Sự kiện công khai (admin)
│   │   ├── schedules.py      # Lịch học cá nhân
│   │   ├── scheduler.py      # Bộ lập lịch gửi nhắc
│   │   ├── llm.py            # LLM Hugging Face integration
│   │   └── telegram.py       # Kết nối Telegram
│   │
│   ├── api/
│   │   └── endpoints/        # API routes
│   │       ├── agent.py      # POST /agent/interpret
│   │       ├── auth.py       # POST /auth/register, /auth/login
│   │       ├── events.py     # CRUD /events
│   │       ├── public_events.py
│   │       ├── schedules.py
│   │       └── telegram.py
│   │
│   ├── schemas/              # Pydantic models
│   │   ├── agent.py
│   │   ├── auth.py           # User, UserCreate, UserOut
│   │   ├── event.py
│   │   └── schedule.py
│   │
│   └── main.py               # FastAPI app, routes, lifespan
│
├── tests/
│   ├── test_agent_interpret.py
│   ├── test_auth.py
│   ├── test_events.py
│   ├── test_scheduler.py
│   ├── test_telegram.py
│   ├── test_schedules_and_public_events.py
│   └── conftest.py           # Pytest config
│
├── docs/
│   ├── agent-spec.md         # Chi tiết schema AI agent
│   └── mongodb-schema.md     # Kế hoạch MongoDB
│
└── requirements.txt          # Dependencies
```

---

## 🔑 Thực Thể Chính

### **User (Người dùng)**

```json
{
  "id": "1",
  "email": "sinh_vien@example.com",
  "hashed_password": "...",
  "salt": "...",
  "full_name": "Nguyễn Văn A",
  "telegram_chat_id": "987654321",
  "timezone": "Asia/Ho_Chi_Minh",
  "created_at": "2026-01-14T...",
  "access_token": "eyJhbGc..."
}
```

### **Schedule Entry (Bài học)**

```json
{
  "id": "1",
  "subject": "Toán cao cấp",
  "day_of_week": "monday",
  "start_time": "08:00",
  "end_time": "09:30",
  "room": "A101",
  "teacher": "Th.S Nguyễn Văn A",
  "notes": "Mang máy tính",
  "created_at": "2026-01-14T..."
}
```

### **Event (Sự kiện cá nhân)**

```json
{
  "id": "1",
  "title": "Nộp đồ án",
  "description": "Đồ án môn học Mạng máy tính",
  "start": "2026-01-20T14:00:00",
  "end": "2026-01-20T15:00:00",
  "remind_before_minutes": 30,
  "notify_via": ["telegram"],
  "user_id": 1
}
```

### **Public Event (Sự kiện công khai)**

```json
{
  "id": "1",
  "title": "Lịch thi cuối kỳ",
  "description": "Thi tất cả môn học",
  "start_date": "2026-01-20T08:00:00",
  "end_date": "2026-02-05T17:00:00",
  "event_type": "exam",
  "target_groups": ["all"],
  "created_by": 0,
  "created_at": "2026-01-14T..."
}
```

---

## 🚀 Cách Sử Dụng API

### **1. Đăng Ký & Đăng Nhập**

```bash
# Đăng ký
POST /auth/register
{
  "email": "test@example.com",
  "password": "mypassword",
  "full_name": "Sinh Viên Test"
}

# Đăng nhập
POST /auth/login
{
  "email": "test@example.com",
  "password": "mypassword"
}

# Response
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

### **2. Nhập Lịch Học**

```bash
# Tạo bài học
POST /schedules
Headers: X-User-Id: 1
{
  "subject": "Toán cao cấp",
  "day_of_week": "monday",
  "start_time": "08:00",
  "end_time": "09:30",
  "room": "A101",
  "teacher": "Th.S Nguyễn Văn A"
}

# Lấy lịch thứ 2
GET /schedules?day_of_week=monday
Headers: X-User-Id: 1

# Cập nhật
PUT /schedules/1
Headers: X-User-Id: 1
{
  "room": "A202"
}

# Xóa
DELETE /schedules/1
Headers: X-User-Id: 1
```

### **3. Tạo Sự Kiện Cá Nhân**

```bash
# Tạo
POST /events
Headers: X-User-Id: 1
{
  "title": "Nộp đồ án",
  "description": "Đồ án Mạng máy tính",
  "start": "2026-01-20T14:00:00",
  "end": "2026-01-20T15:00:00",
  "remind_before_minutes": 30,
  "notify_via": ["telegram"]
}

# Lấy danh sách
GET /events
Headers: X-User-Id: 1
```

### **4. Sự Kiện Công Khai (Admin)**

```bash
# Admin tạo
POST /public-events
Headers: X-User-Id: 0 (admin user)
{
  "title": "Lịch thi cuối kỳ",
  "description": "Thi tất cả môn học",
  "start_date": "2026-01-20T08:00:00",
  "end_date": "2026-02-05T17:00:00",
  "event_type": "exam",
  "target_groups": ["all"]
}

# Sinh viên xem
GET /public-events

# Lọc theo loại
GET /public-events?event_type=exam
```

### **5. AI Agent - Chat Tự Động (LLM)**

```bash
# Gửi câu hỏi - LLM tự động phân tích intent
POST /chat
Headers: X-User-Id: 1
{
  "text": "Hôm nay tôi có lịch gì?"
}

# Response (intent được xác định bởi LLM)
{
  "ok": true,
  "action": "get_schedule",
  "result": {
    "events": [...]
  },
  "messages": ["Bạn có 2 buổi học trong ngày."]
}

# Chat tự nhiên (không liên quan lịch học)
POST /chat
Headers: X-User-Id: 1
{
  "text": "Xin chào, bạn tên gì?"
}

# Response (LLM trả lời như AI bình thường)
{
  "ok": true,
  "action": "chat",
  "result": {
    "response": "Xin chào! Tôi là trợ lý ảo của bạn..."
  },
  "messages": ["Xin chào! Tôi là trợ lý ảo của bạn..."]
}
```

### **6. AI Agent Cổ Điển** (Nếu không dùng LLM)

```bash
POST /agent/interpret
Headers: X-User-Id: 1
{
  "intent": "get_schedule",
  "confidence": 0.95,
  "raw_text": "Hôm nay tôi có lịch gì?",
  "date": "2026-01-15"
}

# Response
{
  "ok": true,
  "action": "get_schedule",
  "result": {
    "events": [...]
  },
  "messages": ["Dưới đây là lịch của bạn hôm nay..."],
  "needs_clarification": false
}
```

### **6. Kết Nối Telegram**

```bash
# Kết nối
POST /telegram/connect
Headers: X-User-Id: 1
{
  "chat_id": "987654321"
}

# Webhook nhận cập nhật
POST /telegram/webhook
{
  "update_id": 123,
  "message": {
    "chat": {"id": "987654321"},
    "text": "/today"
  }
}
```

---

## 🔐 Xác Thực

- **Header**: `X-User-Id` (user ID) cho các API cần xác thực
- **Token**: Trả về access token sau khi đăng nhập
- **TODO**: Tích hợp JWT thực cho production

---

## 🧪 Chạy Test

```bash
# Tất cả test
pytest -q

# Test cụ thể
pytest tests/test_schedules_and_public_events.py -q

# Verbose
pytest -v
```

---

## 📦 Cài Đặt & Chạy

### **Chuẩn Bị**

```bash
# Tạo virtual environment
python -m venv venv
.\venv\Scripts\activate

# Cài dependencies
pip install -r requirements.txt
```

### **Chạy Server**

```bash
uvicorn app.main:app --reload
# Truy cập: http://localhost:8000/docs (Swagger UI)
```

### **Chạy Test**

```bash
pytest -q
```

---

## 🔄 Quy Trình Làm Việc

### **Sinh viên**

1. Đăng ký tài khoản
2. Nhập lịch học từng tuần
3. Tạo sự kiện/deadline riêng
4. Kết nối Telegram để nhận nhắc
5. Hỏi AI agent về lịch (LLM sẽ phân tích)

### **Admin**

1. Tạo sự kiện công khai (thi, khai giảng, etc.)
2. Quản lý các sự kiện
3. Xóa/cập nhật sự kiện nếu cần

### **Background (Scheduler)**

- Mỗi 1 phút kiểm tra các sự kiện sắp tới
- Gửi lời nhắc Telegram tới sinh viên

---

## 📊 Hiện Tại & Tiếp Theo

### ✅ Đã Triển Khai

- [x] Auth (đăng ký, đăng nhập, hash password)
- [x] Events CRUD (sự kiện cá nhân)
- [x] Schedules CRUD (lịch học cá nhân)
- [x] Public Events (sự kiện công khai - admin)
- [x] AI Agent (phân tích intent)
- [x] Scheduler (gửi nhắc tự động)
- [x] Telegram scaffold (sẵn sàng tích hợp)
- [x] 21 Unit Tests

### 📋 TODO (Priority)

1. **MongoDB** - Di chuyển từ in-memory storage
2. **Real LLM** - Tích hợp OpenAI / Hugging Face (thay vì mock)
3. **Real Telegram Bot API** - Thay vì in-memory outbox
4. **Admin Role** - Xác thực admin cho public-events
5. **React Frontend** - UI cho sinh viên
6. **CI/CD** - GitHub Actions
7. **Deployment** - Docker + Azure / AWS

---

## 🤖 Cho AI Khác Tiếp Nhận Dự Án

### **Hiểu Kiến Trúc**

1. **Tách riêng**:

   - `app/core/` - Logic nghiệp vụ (không phụ thuộc FastAPI)
   - `app/api/endpoints/` - Routes (FastAPI)
   - `app/schemas/` - Pydantic models (validation)

2. **In-Memory → MongoDB**:

   - Tất cả các hàm trong `core/` sử dụng `_USERS`, `_EVENTS`, etc.
   - Chỉ cần thay thế dict thành query MongoDB
   - Tests có thể mock hoặc dùng test database

3. **Bộ Lập Lịch**:

   - `scheduler.py` chạy background job mỗi 1 phút
   - Kết nối tất cả các module (events, telegram, auth)
   - Dễ mở rộng cho các tác vụ khác

4. **AI Agent**:
   - `agent.py` có dispatcher pattern
   - Dễ thêm intent mới (chỉ cần thêm handler)
   - Sẵn sàng cho LLM thực

### **Quy Trình Tiếp Tục**

1. Đọc file này trước
2. Xem `docs/agent-spec.md` để hiểu schema
3. Xem `docs/mongodb-schema.md` để hiểu cấu trúc DB
4. Chạy test: `pytest -q`
5. Chạy server: `uvicorn app.main:app --reload`
6. Thử API tại http://localhost:8000/docs

### **Thêm Feature Mới**

```
1. Tạo model trong app/core/new_feature.py
2. Tạo endpoint trong app/api/endpoints/new_feature.py
3. Tạo schema trong app/schemas/new_feature.py
4. Thêm router vào app/main.py
5. Viết test trong tests/test_new_feature.py
6. Chạy: pytest tests/test_new_feature.py -q
```

---

## 📞 Liên Hệ & Ghi Chú

- **Ngôn ngữ**: Python 3.10+
- **Framework**: FastAPI
- **Scheduler**: APScheduler
- **Testing**: pytest
- **Docs**: OpenAPI/Swagger (tại `/docs`)

**Chúc bạn thành công!** 🎉
