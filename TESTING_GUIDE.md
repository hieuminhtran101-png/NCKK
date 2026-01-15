# Smart Scheduler - Testing Guide

## System Status

- **Backend**: Running on http://localhost:8000
- **Frontend**: Running on http://localhost:3001
- **Database**: MongoDB at localhost:27017 (local instance)
- **Cache**: Redis unavailable (graceful fallback)

## Prerequisites

1. MongoDB running locally
2. Backend server: `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
3. Frontend server: `cd frontend && npm start`

## Test Flow

### Phase 1: Authentication

#### 1.1 Register User

1. Open http://localhost:3001
2. Click "Create Account"
3. Enter:
   - Email: `testuser@example.com`
   - Password: `Test123!`
   - Full Name: `Test User`
4. Click "Register"
5. **Expected**: Redirected to login page with success message

#### 1.2 Login

1. Enter email and password from previous step
2. Click "Login"
3. **Expected**: Dashboard loads with user email displayed

### Phase 2: Schedule Management

#### 2.1 View Empty Schedule

1. On Dashboard, click "My Schedule" tab
2. **Expected**: Shows "No schedules yet. Upload one!"

#### 2.2 Import Schedule via Text

1. Click "Import Schedule" tab
2. Click "Parse Text"
3. Paste sample text:

```
Toán 15/1 phòng 201 10:00-11:30
Tiếng Anh 16/1 phòng 102 13:00-14:30
```

4. Click "Parse"
5. **Expected**: Shows parsed schedule with 2 entries
6. Review entries, then click "Confirm & Save"
7. **Expected**: Success message "Schedules saved successfully!"

#### 2.3 View Imported Schedules

1. Click "My Schedule" tab
2. **Expected**: Shows 2 schedule cards with:
   - Subject name (Toán, Tiếng Anh)
   - Day of week
   - Time slots
   - Room information

### Phase 3: Chat Features

#### 3.1 AI Chat

1. Click "💬 Chat" tab
2. Click "🤖 AI Chat" sub-tab
3. Type: "ngày 15/1 tôi học môn gì?"
4. Click "Send"
5. **Expected**: AI responds with schedule info:

```
📚 **Your Classes:**
- Toán (None) 10:00-11:30 @ 201
```

#### 3.2 Follow-up Questions

1. Ask: "chủ nhật tuần tới tôi có lớp nào không?"
2. **Expected**: AI responds appropriately (either schedule data or suggestion)
3. Ask: "bạn là ai?"
4. **Expected**: AI responds with fallback message

### Phase 4: Events (Optional)

#### 4.1 Create Event

1. Click "Events" tab
2. Add event: "Exam on 20/1"
3. **Expected**: Event appears in list

#### 4.2 View Events

1. **Expected**: List shows all created events

## Known Issues & Workarounds

### Issue 1: Redis Not Available

**Status**: Expected (user has local MongoDB, no Redis)
**Impact**: None (graceful fallback implemented)
**Logs**: `⚠️ Redis not available` (safe to ignore)

### Issue 2: 401 Unauthorized on First Load

**Cause**: JWT token not in localStorage yet
**Solution**: Login first, then navigate to protected pages
**Status**: FIXED - frontend now checks `if (email)` before loading

### Issue 3: CORS Errors

**Status**: FIXED - CORS middleware configured in main.py
**Logs**: Should see no CORS errors in browser console

## Backend Endpoints Reference

### Authentication

- `POST /auth/register` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /users/me` - Get current user info

### Schedules

- `GET /schedules` - List user's schedules
- `GET /schedules/{id}` - Get specific schedule
- `POST /schedules` - Create schedule (from confirmed parse)
- `PUT /schedules/{id}` - Update schedule
- `DELETE /schedules/{id}` - Delete schedule

### Chat

- `POST /chat/messages` - Send user-to-user message
- `GET /chat/conversations` - Get conversations list
- `GET /chat/messages/{user_id}` - Get conversation messages
- `POST /chat/ai-response` - Get AI response

### AI/Parse

- `POST /upload/schedule` - Upload Excel file for parsing
- `POST /ai/parse-text` - Parse text to schedule entries
- `POST /ai/confirm-parse` - Confirm and save parsed schedules
- `GET /ai/free-slots` - Get free time slots

### Events

- `GET /events` - List user's events
- `POST /events` - Create event
- `PUT /events/{id}` - Update event
- `DELETE /events/{id}` - Delete event

## Test Verification Checklist

- [ ] Can register new user
- [ ] Can login with correct credentials
- [ ] Cannot login with wrong password
- [ ] Can parse text to schedules
- [ ] Can confirm and save schedules
- [ ] Schedules appear on "My Schedule" tab
- [ ] AI responds with schedule data
- [ ] AI responds with fallback messages
- [ ] Chat messages persist to database
- [ ] No 401 errors after login
- [ ] No CORS errors in browser console
- [ ] No JavaScript errors in browser console

## Performance Notes

- Initial load: ~2-3 seconds
- Parse text: < 1 second
- AI response: < 5 seconds (depends on Hugging Face API)
- Database queries: < 500ms

## Sample Test Data

### User 1

- Email: `testuser@example.com`
- Password: `Test123!`
- Name: `Test User`

### Sample Schedule Text

```
Toán 15/1 phòng 201 10:00-11:30
Tiếng Anh 16/1 phòng 102 13:00-14:30
Lý 17/1 phòng 305 14:00-15:30
```

### Sample Questions for AI

- "Ngày 15/1 tôi học môn gì?"
- "Tôi có bao nhiêu lớp?"
- "Phòng nào là lớp Tiếng Anh?"
- "Lớp Lý bắt đầu lúc mấy giờ?"

## Troubleshooting

### Backend won't start

```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <PID> /F

# Restart backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend won't start

```bash
# Clear node_modules and reinstall
cd frontend
rm -r node_modules package-lock.json
npm install
npm start
```

### MongoDB connection issues

```bash
# Test MongoDB connection
mongosh localhost:27017

# Check if mongod is running
tasklist | findstr mongod
```

### 401 Unauthorized errors

1. Clear localStorage: `localStorage.clear()` in browser console
2. Login again
3. Refresh page

## Expected API Responses

### Successful Parse & Save

```json
{
  "ok": true,
  "count": 2,
  "schedule_ids": ["507f1f77bcf86cd799439011", "507f1f77bcf86cd799439012"]
}
```

### AI Chat Response (with schedules)

```json
{
  "content": "📚 **Your Classes:**\n- Toán (None) 10:00-11:30 @ 201\n- Tiếng Anh (None) 13:00-14:30 @ 102"
}
```

### AI Chat Response (fallback)

```json
{
  "content": "Tôi xin lỗi, tôi không hiểu câu hỏi của bạn..."
}
```

## Next Steps After Testing

1. Document any bugs found
2. Verify all endpoints working
3. Test with multiple users
4. Load testing if needed
5. Deploy to production when ready

---

**Last Updated**: 2026-01-15
**Status**: READY FOR TESTING ✅
