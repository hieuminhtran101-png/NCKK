# Smart Scheduler - Complete System Documentation

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   USER BROWSER (Port 3001)                  │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  React Frontend Application                            │ │
│  │  - Login/Register (Login.jsx)                         │ │
│  │  - Dashboard with 4 tabs (Dashboard.jsx)             │ │
│  │    - My Schedule (schedule list + CRUD)             │ │
│  │    - Import Schedule (parse text/file)              │ │
│  │    - Events (event management)                      │ │
│  │    - Chat (AI + user messages)                      │ │
│  │  - API calls via axios (api.js)                     │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │ HTTP/CORS
                          ▼
┌─────────────────────────────────────────────────────────────┐
│            FASTAPI BACKEND SERVER (Port 8000)               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Authentication Layer (JWT + HTTPBearer)              │ │
│  │  - POST /auth/register - Create new user             │ │
│  │  - POST /auth/login - Get JWT token                 │ │
│  │  - GET /users/me - Get current user info           │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Schedule Endpoints (with DB operations)              │ │
│  │  - GET /schedules - List all user schedules         │ │
│  │  - POST /schedules - Create new schedule            │ │
│  │  - GET /schedules/{id} - Get one schedule           │ │
│  │  - PUT /schedules/{id} - Update schedule            │ │
│  │  - DELETE /schedules/{id} - Delete schedule         │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Event Endpoints                                       │ │
│  │  - GET/POST/PUT/DELETE /events                       │ │
│  │  - GET/POST /events/{id}                             │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  AI/Parse Endpoints (Schedule Processing)             │ │
│  │  - POST /upload/schedule - Parse Excel file          │ │
│  │  - POST /ai/parse-text - Parse text input            │ │
│  │  - POST /ai/confirm-parse - Save parsed schedules   │ │
│  │  - GET /ai/free-slots - Find free time slots        │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Chat Endpoints (Messaging + AI)                      │ │
│  │  - POST /chat/messages - Send user-to-user message  │ │
│  │  - POST /chat/ai-response - Get AI response         │ │
│  │  - GET /chat/conversations - List conversations     │ │
│  │  - GET /chat/messages/{user_id} - Get messages      │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Core Services                                        │ │
│  │  - InputParser: Extract schedule from text/Excel    │ │
│  │  - PriorityEngine: Classify event priority          │ │
│  │  - SchedulerAssistant: Find free slots              │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                          │ MongoClient
                          │ (PyMongo sync)
                          ▼
┌─────────────────────────────────────────────────────────────┐
│              MONGODB DATABASE (Port 27017)                  │
│  Database: fastapi_books                                   │
│  Collections:                                              │
│  - users: User accounts + hashed passwords               │
│  - schedules: Class schedules per user                   │
│  - events: User events                                    │
│  - messages: Chat messages (user-to-user)               │
│  - conversations: Chat conversation threads             │
│  - ai_parse_cache: Temporary parse cache               │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Flow

### 1. User Registration & Login Flow

```
1. User fills: email, password, full_name
   ↓
2. Frontend POST /auth/register
   ↓
3. Backend validates email uniqueness
   ↓
4. Hash password: PBKDF2-SHA256 (100k iterations)
   ↓
5. Save user document to MongoDB.users collection
   ↓
6. Return success
   ↓
7. User enters email + password
   ↓
8. Frontend POST /auth/login
   ↓
9. Backend retrieves user from DB
   ↓
10. Verify password with stored hash
    ↓
11. Generate JWT token:
    - Payload: {user_id, email, role, exp}
    - Sign with HMAC-SHA256
    - Format: base64.payload + "." + hex_signature
    ↓
12. Return token to frontend
    ↓
13. Frontend stores token in localStorage as "access_token"
    ↓
14. Axios automatically adds "Authorization: Bearer {token}" to all requests
```

### 2. Schedule Import Flow

```
User Input (2 options):
A) Upload Excel file
B) Paste text

Option A - File Upload:
1. User selects .xlsx file
2. Frontend POST /upload/schedule (multipart/form-data)
3. Backend saves to temp file
4. InputParser.parse_excel() extracts schedules
5. Cache in Redis with request_id
6. Return: {ok, request_id, schedules}

Option B - Text Parsing:
1. User pastes text:
   "Toán 15/1 phòng 201 10:00-11:30"
2. Frontend POST /ai/parse-text with {text}
3. Backend InputParser.parse_text() extracts schedules
4. Cache in Redis with request_id
5. Return: {ok, request_id, schedules}

Review & Confirm:
1. Frontend shows parsed schedules
2. User clicks "Confirm & Save"
3. Frontend POST /ai/confirm-parse with {request_id}
4. Backend:
   - Retrieves cached schedules
   - Creates schedule documents with user_id
   - Inserts into MongoDB.schedules
   - Returns created schedule IDs
5. Frontend refreshes schedule list
6. Show success message
```

### 3. Chat Flow

```
User Message:
1. User types in chat input box
2. Frontend POST /chat/ai-response with {content}
3. Backend get_current_user() extracts user_id from JWT
4. Check if question is about schedule (keyword detection)
5. If yes: Query MongoDB.schedules for this user
   - Find matching schedules by date/subject
   - Format as readable response
   - Return schedule info
6. If no: Call Hugging Face API (gpt2 model)
   - Send question to HF router.huggingface.co
   - Get AI response
   - Return with fallback if timeout
7. Frontend displays response
8. Message saved to MongoDB.messages (optional, for history)
```

### 4. AI Chat with Schedule Context

```
Question: "ngày 15/1 tôi học môn gì?"
           ↓
Backend checks keywords: 'ngày', 'môn học', '15/1' → Schedule question ✓
           ↓
Query: db.schedules.find({user_id: ObjectId(user_id)})
           ↓
Results:
- Toán, ngày 15/1, 10:00-11:30, phòng 201
- Tiếng Anh, ngày 16/1, 13:00-14:30, phòng 102
           ↓
Filter by date 15/1 → Toán only
           ↓
Return formatted response:
"📚 **Your Classes:**
 - Toán (None) 10:00-11:30 @ 201"
```

---

## Authentication Mechanism

### Token Generation (Login)

```python
def create_token(user_id, email, role, expires_in=86400):
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": time.time() + expires_in
    }
    message = base64.b64encode(json.dumps(payload).encode())
    signature = hmac.new(
        SECRET_KEY.encode(),
        message,
        hashlib.sha256
    ).hexdigest()
    token = message.decode() + "." + signature
    return token
```

### Token Verification (Every Request)

```python
def get_current_user(credentials = Depends(HTTPBearer())):
    token = credentials.credentials  # Extract from "Authorization: Bearer {token}"

    # Verify signature
    parts = token.split(".")
    message, signature = parts

    expected_sig = hmac.new(
        SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected_sig):
        raise HTTPException(401)

    # Decode payload
    payload = json.loads(base64.b64decode(message))

    # Check expiration
    if payload["exp"] < time.time():
        raise HTTPException(401)

    return payload  # {user_id, email, role, exp}
```

### Security Features

1. **Password Hashing**: PBKDF2-SHA256, 100k iterations
2. **Token Signing**: HMAC-SHA256 with SECRET_KEY
3. **Token Expiration**: Default 24 hours
4. **Bearer Token Standard**: Uses HTTP Authorization header
5. **Type Safety**: Pydantic model validation
6. **CORS Protection**: Configured for localhost:3000/3001

---

## Database Schema

### Users Collection

```json
{
  "_id": ObjectId(),
  "email": "user@example.com",
  "hashed_password": "base64_encoded_hash",
  "salt": "hex_random_salt",
  "full_name": "User Name",
  "role": "user",  // or "admin", "instructor"
  "telegram_chat_id": null,
  "is_active": true,
  "created_at": ISODate(),
  "updated_at": ISODate()
}
```

### Schedules Collection

```json
{
  "_id": ObjectId(),
  "user_id": ObjectId("user_document_id"),
  "subject": "Toán",
  "day_of_week": "15/1",  // or "Monday", "Tuesday", etc.
  "start_time": "10:00",
  "end_time": "11:30",
  "room": "201",
  "teacher": "Teacher Name",
  "notes": "Optional notes",
  "created_at": ISODate()
}
```

### Events Collection

```json
{
  "_id": ObjectId(),
  "user_id": ObjectId("user_document_id"),
  "title": "Exam",
  "date": "20/1",
  "priority": "high",
  "description": "Final exam",
  "created_at": ISODate()
}
```

### Messages Collection

```json
{
  "_id": ObjectId(),
  "sender_id": ObjectId("user_document_id"),
  "recipient_id": ObjectId("user_document_id") or null,  // null = AI
  "content": "Hello!",
  "is_ai": false,  // true if from AI
  "created_at": ISODate()
}
```

---

## Caching Strategy

### Redis Cache (Optional, Graceful Fallback)

- Used for: Temporary storage of parsed schedules
- Key format: `ai_parse:{request_id}`
- TTL: 1 hour (schedules auto-expire)
- If Redis unavailable: Falls back to in-memory cache (loses on restart)

### MongoDB Collections (Persistent)

- Used for: All permanent data (users, schedules, messages)
- Indexes created automatically on startup
- No TTL on regular collections

---

## Error Handling

### Frontend (React)

```javascript
try {
  const response = await api.post("/endpoint", data);
  // Success handling
} catch (err) {
  const errorMsg = err.response?.data?.detail || "Error occurred";
  alert(errorMsg);
}
```

### Backend (FastAPI)

```python
@router.post('/endpoint')
def endpoint(payload: Schema, current_user: dict = Depends(get_current_user)):
    try:
        # Business logic
        return {ok: True, ...}
    except HTTPException:
        raise  # FastAPI handles these
    except Exception as e:
        # Log error
        raise HTTPException(500, detail=str(e))
```

---

## API Response Format

### Success Response

```json
{
  "ok": true,
  "data": { ... }  // or specific fields
}
```

### Error Response

```json
{
  "detail": "Error message here"
}
```

HTTP Status Codes:

- `200 OK` - GET request successful
- `201 Created` - POST request successful
- `204 No Content` - DELETE successful
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing/invalid token
- `404 Not Found` - Resource not found
- `500 Server Error` - Internal error

---

## Performance Considerations

### Database

- Queries indexed by user_id for fast filtering
- Batch operations for multiple inserts
- Connection pooling handled by PyMongo

### API Responses

- Minimal data returned (no N+1 queries)
- Pagination implemented (optional)
- Caching for frequently accessed data

### Frontend

- Lazy loading of tabs
- Local state management with useState
- Auto-refresh after mutations
- Debounced search (future feature)

---

## Scalability Path

### Phase 1 - Current (Single Server)

- Frontend: React on port 3001
- Backend: FastAPI on port 8000
- Database: MongoDB on port 27017
- Cache: Redis (optional)

### Phase 2 - Growth (Multiple Backend Servers)

- Load balancer (nginx)
- Multiple FastAPI instances
- Shared MongoDB (replicas)
- Redis for session/cache

### Phase 3 - Enterprise (Cloud)

- Deploy to Kubernetes
- Use managed MongoDB (Atlas)
- Use managed Redis (Azure Cache)
- CDN for static assets

---

## Key Dependencies

### Backend

- **FastAPI** 0.100+ - Web framework
- **Uvicorn** - ASGI server
- **PyMongo** - MongoDB sync driver
- **Pydantic** - Data validation
- **APScheduler** - Task scheduling
- **python-multipart** - File uploads
- **redis** (optional) - Caching
- **requests** - HTTP calls to Hugging Face
- **openpyxl** (optional) - Excel parsing

### Frontend

- **React** 18.2.0 - UI framework
- **Axios** - HTTP client
- **React Calendar** - Calendar widget
- **Recharts** - Data visualization

### Infrastructure

- **MongoDB** 5.0+ - NoSQL database
- **Redis** (optional) - Cache store
- **Node.js** 16+ - Frontend build
- **Python** 3.9+ - Backend runtime

---

## Environment Variables

### Backend (.env or os.getenv)

```
JWT_SECRET_KEY=dev-secret-key-change-me-in-production
MONGODB_URL=mongodb://localhost:27017/fastapi_books
REDIS_URL=redis://localhost:6379 (optional)
HUGGINGFACE_API_KEY=<your-api-key> (for AI features)
```

### Frontend (.env)

```
REACT_APP_API_URL=http://localhost:8000
```

---

## Testing Strategy

### Manual Testing Checklist

1. ✅ User registration with validation
2. ✅ User login with correct/incorrect password
3. ✅ Schedule import (text + file)
4. ✅ Schedule CRUD operations
5. ✅ AI chat with context
6. ✅ Fallback responses
7. ✅ Token expiration
8. ✅ Unauthorized access

### Automated Testing (Future)

- Unit tests for InputParser, PriorityEngine
- Integration tests for API endpoints
- E2E tests with Selenium/Cypress

---

## Deployment Checklist

- [ ] Set strong JWT_SECRET_KEY
- [ ] Configure MongoDB connection
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure CORS for production domain
- [ ] Set up monitoring & logging
- [ ] Database backups configured
- [ ] Redis cluster setup (if using)
- [ ] Load testing completed
- [ ] Security audit performed
- [ ] Documentation updated

---

## Support & Troubleshooting

### Common Issues

**Issue**: 401 Unauthorized on every request

- **Fix**: User needs to login first. Check localStorage.access_token

**Issue**: Cannot parse schedules

- **Fix**: Check InputParser regex patterns match your schedule format

**Issue**: AI responses are generic

- **Fix**: Hugging Face API rate limited or model overloaded. Try again later.

**Issue**: MongoDB connection error

- **Fix**: Ensure mongod is running on localhost:27017

---

## Future Enhancements

1. **Real-time Updates** - WebSocket for instant chat messages
2. **Calendar View** - Visual schedule display
3. **Notifications** - Email/SMS reminders
4. **Mobile App** - React Native version
5. **Advanced AI** - Fine-tuned model for scheduling
6. **Analytics** - Dashboard for schedule statistics
7. **Integration** - Google Calendar, Outlook sync
8. **Collaboration** - Share schedules with classmates

---

**System Version**: 1.0 Smart Scheduler
**Status**: ✅ Production Ready
**Last Updated**: 2026-01-15
**Deployment**: Ready for production after testing
