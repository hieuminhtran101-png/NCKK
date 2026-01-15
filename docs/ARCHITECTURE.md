# Kiến Trúc Hệ Thống

## 📐 Tổng Quan

```
┌─────────────────────────────────────────────────────────────┐
│                    SINH VIÊN / ADMIN                         │
│              (React Frontend - Chưa triển khai)              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────────┐
│                   FastAPI Server                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              app/api/endpoints/                       │  │
│  │  ├─ agent.py (POST /agent/interpret)                │  │
│  │  ├─ auth.py (register/login)                        │  │
│  │  ├─ events.py (CRUD sự kiện cá nhân)               │  │
│  │  ├─ schedules.py (CRUD lịch học)                   │  │
│  │  ├─ public_events.py (CRUD sự kiện công khai)      │  │
│  │  └─ telegram.py (connect/webhook)                   │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬───────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   ┌────────┐   ┌──────────────┐  ┌──────────────┐
   │ Core   │   │  Scheduler   │  │  Telegram    │
   │Logic   │   │  (Every 1min)│  │  (Outbox)    │
   │        │   │              │  │              │
   │- auth  │   │- check_and_  │  │- send_msg    │
   │- events│   │  send_remind │  │- handle_    │
   │- sched │   │  ers()       │  │  update()    │
   │- agent │   │              │  │              │
   │        │   │              │  │              │
   └────────┘   └──────────────┘  └──────────────┘
        │
        ▼
   ┌──────────────────────┐
   │  In-Memory Storage   │
   │  (Sẽ → MongoDB)      │
   │                      │
   │- _USERS             │
   │- _EVENTS            │
   │- _SCHEDULES         │
   │- _PUBLIC_EVENTS     │
   └──────────────────────┘
```

---

## 🏗️ Tầng (Layers)

### **1. Tầng API (Endpoints)**

**File**: `app/api/endpoints/*.py`

**Trách Nhiệm**:

- Xử lý HTTP requests/responses
- Xác thực header `X-User-Id`
- Chuyển dữ liệu từ Pydantic schemas sang core functions
- Trả về response với status code đúng

**Ví Dụ**:

```python
@router.post('/events', response_model=EventOut, status_code=201)
def create_event(payload: EventCreate, x_user_id: Optional[int] = Header(None)):
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Missing X-User-Id header")

    ev = events_core.create_event(int(x_user_id), payload.model_dump())
    return EventOut(**ev)
```

**Điểm Quan Trọng**:

- Không chứa logic nghiệp vụ
- Chỉ gọi các function từ `app/core/`
- Không phụ thuộc FastAPI ở tầng core

---

### **2. Tầng Core (Logic Chính)**

**File**: `app/core/*.py`

**Trách Nhiệm**:

- Nghiệp vụ logic
- CRUD operations
- Tính toán
- Không phụ thuộc FastAPI

**Các Module**:

#### **`auth.py`** - Xác Thực

```python
def create_user(email, password, full_name) -> Dict
def find_user_by_email(email) -> Optional[Dict]
def hash_password(password, salt) -> Dict
def verify_password(password, salt, hashed) -> bool
def create_access_token(data) -> str
def decode_access_token(token) -> Dict
```

#### **`events.py`** - Sự Kiện Cá Nhân

```python
def create_event(user_id, data) -> Dict
def list_events(user_id) -> List[Dict]
def get_event(user_id, event_id) -> Optional[Dict]
def update_event(user_id, event_id, data) -> Optional[Dict]
def delete_event(user_id, event_id) -> bool
```

#### **`schedules.py`** - Lịch Học

```python
def add_schedule_entry(user_id, subject, day, start_time, end_time, ...) -> Dict
def get_user_schedule(user_id, day_of_week=None) -> List[Dict]
def update_schedule_entry(user_id, entry_id, data) -> Optional[Dict]
def delete_schedule_entry(user_id, entry_id) -> bool
```

#### **`public_events.py`** - Sự Kiện Công Khai

```python
def create_public_event(title, description, start_date, ...) -> Dict
def list_public_events(event_type=None) -> List[Dict]
def get_public_event(event_id) -> Optional[Dict]
def update_public_event(event_id, data) -> Optional[Dict]
def delete_public_event(event_id) -> bool
```

#### **`agent.py`** - AI Agent

```python
def handle_parse(parse_result, user_id) -> Dict
  - Dispatcher pattern
  - Dựa vào intent gọi handler tương ứng
  - Trả về {ok, action, result, needs_clarification}
```

#### **`scheduler.py`** - Bộ Lập Lịch

```python
def init_scheduler()  # Khởi tạo APScheduler
def shutdown_scheduler()  # Tắt
def check_and_send_reminders()  # Chạy mỗi 1 phút
```

#### **`telegram.py`** - Telegram Integration

```python
def register_chat(user_id, chat_id)
def send_message(chat_id, text)  # Lưu vào OUTBOX
def handle_update(update)  # Xử lý webhook
```

---

### **3. Tầng Schema (Validation)**

**File**: `app/schemas/*.py`

**Trách Nhiệm**:

- Pydantic models
- Validate input/output
- Convert data types
- Type hints

**Cấu Trúc**:

```python
class ScheduleEntryCreate(BaseModel):
    subject: str
    day_of_week: str
    start_time: str
    end_time: str
    # Tự động validate khi tạo object

class ScheduleEntryOut(BaseModel):
    id: str
    subject: str
    # Serialize thành JSON
```

---

### **4. In-Memory Storage (Tạm Thời)**

**Hiện Tại**: Dict Python
**Tương Lai**: MongoDB

**Ví Dụ**:

```python
# app/core/events.py
_EVENTS: Dict[int, Dict] = {}  # user_id -> {event_id -> event_data}

_EVENTS[user_id] = {
    'event_id': {
        'id': '1',
        'title': 'Sự kiện',
        'start': datetime(...),
        ...
    }
}
```

**Để Chuyển Sang MongoDB**:

1. Tạo `app/db/mongodb.py` với connection
2. Thay thế mỗi function trong `core/` để dùng Motor/PyMongo
3. Tests sẽ vẫn hoạt động nếu mock database

---

## 🔄 Quy Trình Điển Hình

### **Tạo Sự Kiện**

```
1. Client gửi: POST /events
   Payload: {title, start, end, remind_before_minutes, ...}
   Headers: X-User-Id: 1

2. events.py endpoint nhận:
   - Validate: ScheduleEntryCreate (Pydantic)
   - Xác thực: Check X-User-Id
   - Gọi core: events_core.create_event(user_id, data)

3. Core logic (app/core/events.py):
   - Validate dữ liệu
   - Lưu vào _EVENTS[user_id][event_id]
   - Trả về event dict

4. Endpoint serialize:
   - EventOut(**event) → JSON
   - Return 201 Created

5. Response:
   {
     "id": "1",
     "title": "Sự kiện",
     "start": "2026-01-20T14:00:00",
     ...
   }

6. Scheduler:
   - Mỗi 1 phút chạy check_and_send_reminders()
   - Nếu đến thời gian → send_message(chat_id, ...)
```

---

## 🧠 AI Agent Flow

```
┌──────────────────────────────────────┐
│  LLM (3.5-5B model - Chưa thực)      │
│  Input: "Hôm nay tôi có lịch gì?"   │
│  Output: JSON {intent, entities...}  │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  POST /agent/interpret               │
│  {                                   │
│    intent: "get_schedule",           │
│    confidence: 0.95,                 │
│    raw_text: "Hôm nay...",          │
│    date: "2026-01-15"                │
│  }                                   │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  app/core/agent.py:handle_parse()   │
│  ├─ Check confidence > 0.7?         │
│  ├─ If yes: Call handler            │
│  │  - get_schedule → events_core... │
│  │  - get_free_time → calc_free...  │
│  │  - etc.                          │
│  └─ Return {ok, action, result}     │
└──────────────┬───────────────────────┘
               ▼
┌──────────────────────────────────────┐
│  Response                            │
│  {                                   │
│    "ok": true,                       │
│    "action": "get_schedule",         │
│    "result": { "events": [...] },   │
│    "messages": ["Lịch hôm nay..."]  │
│  }                                   │
└──────────────────────────────────────┘
```

---

## 🔌 Mở Rộng: Thêm Feature Mới

### **Thêm Intent Mới Cho AI Agent**

**File**: `app/core/agent.py`

```python
# 1. Thêm vào INTENT_HANDLERS
INTENT_HANDLERS = {
    "get_schedule": handle_get_schedule,
    "get_free_time": handle_get_free_time,
    "MY_NEW_INTENT": handle_my_new_intent,  # ← Thêm
}

# 2. Implement handler
def handle_my_new_intent(parsed, user_id):
    """Xử lý intent mới."""
    # Logic ở đây
    result = do_something(user_id, parsed)
    return {
        "ok": True,
        "action": "MY_NEW_INTENT",
        "result": result,
        "messages": ["Kết quả..."]
    }
```

### **Thêm Endpoint CRUD**

**File**: `app/core/my_feature.py`

```python
_MY_DATA: Dict = {}

def create(user_id, data):
    # ...
    return item

def list(user_id):
    # ...
    return items
```

**File**: `app/schemas/my_feature.py`

```python
class MyItemCreate(BaseModel):
    field1: str
    field2: int

class MyItemOut(BaseModel):
    id: str
    field1: str
    field2: int
```

**File**: `app/api/endpoints/my_feature.py`

```python
router = APIRouter(prefix="/my-feature", tags=["my_feature"])

@router.post("", response_model=MyItemOut, status_code=201)
def create_item(payload: MyItemCreate, x_user_id: Optional[int] = Header(None)):
    # ...
```

**File**: `app/main.py`

```python
from app.api.endpoints.my_feature import router as my_feature_router
app.include_router(my_feature_router)
```

---

## 📊 Data Flow

### **Lưu Sự Kiện**

```
Request → Endpoint → Pydantic Validate
  → Core Create → In-Memory Store → Response

POST /events
  {title, start, ...}
    ↓
  @router.post
    ↓
  EventCreate (Pydantic)
    ↓
  events_core.create_event()
    ↓
  _EVENTS[user_id][event_id] = {data}
    ↓
  EventOut (**event)
    ↓
  {id, title, ...} JSON
```

### **Gửi Nhắc**

```
Scheduler (every 1 min)
    ↓
check_and_send_reminders()
    ↓
  For each user:
    - List events
    - Check reminder_time < now < reminder_time + 1min
    - If yes:
      - Get chat_id từ auth._USERS[user_id]
      - Call telegram.send_message(chat_id, msg)
    ↓
TELEGRAM_OUTBOX.append((chat_id, msg))
    ↓
(Trong production: gửi tới Telegram API)
```

---

## 🧪 Testing Strategy

### **Unit Tests**

- Test `app/core/*.py` functions độc lập
- Không cần FastAPI
- Mock data từ in-memory storage

### **Integration Tests**

- Test endpoints `/api/endpoints/*.py`
- Kiểm tra request/response validation
- Kiểm tra status codes

### **Example**:

```python
def test_create_event():
    # Prepare
    user_id = 1
    payload = {...}

    # Act
    resp = client.post('/events', json=payload, headers={'X-User-Id': str(user_id)})

    # Assert
    assert resp.status_code == 201
    assert resp.json()['title'] == 'Event'
```

---

## 🔐 Bảo Mật (TODO)

- [ ] Rate limiting
- [ ] Admin role check (tạm thời skip)
- [ ] HTTPS
- [ ] CORS
- [ ] Input sanitization
- [ ] JWT thực với exp, refresh tokens

---

## 📈 Performance (TODO)

- [ ] Cache lịch học (nếu không thay đổi)
- [ ] Pagination cho list endpoints
- [ ] Database indexing
- [ ] Connection pooling (MongoDB)

---

## 🐳 Deployment (TODO)

```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app/ app/
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

```bash
docker build -t ai-schedule-bot .
docker run -p 8000:8000 ai-schedule-bot
```

---

## 📝 Tóm Tắt

| Layer   | File             | Trách Nhiệm                    |
| ------- | ---------------- | ------------------------------ |
| API     | `endpoints/*.py` | HTTP requests, validation      |
| Core    | `core/*.py`      | Business logic                 |
| Schema  | `schemas/*.py`   | Data validation, serialization |
| Storage | Dict/MongoDB     | Persistent data                |

**Quy tắc vàng**: Core logic độc lập → dễ test, dễ migrate

---
