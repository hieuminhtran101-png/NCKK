# Smart Scheduler - Setup & Run Guide

## Prerequisites

✅ MongoDB running locally on `localhost:27017` (MongoDB Compass)
✅ Python 3.8+
✅ Node.js 16+
✅ All dependencies installed:

- Backend: `pip install -r requirements.txt`
- Frontend: `cd frontend && npm install`

---

## Startup Flow

### 1. Start Backend (Terminal 1)

```bash
cd D:\fast-api-books
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:

```
✅ Connected to MongoDB successfully
✅ Database: fastapi_books
INFO:     Application startup complete.
```

**Endpoints available:**

- `GET /health` → `{status: ok}`
- `POST /auth/register` → Register new user
- `POST /auth/login` → Login, get JWT token
- `GET /schedules` → Get user schedules (requires Bearer token)
- `GET /events` → Get user events (requires Bearer token)
- `POST /upload/schedule` → Upload Excel schedule
- `POST /ai/parse-text` → Parse text schedule
- `GET /ai/priority/{event_id}` → Classify event priority
- `GET /ai/free-slots` → Find free time slots

---

### 2. Start Frontend (Terminal 2)

```bash
cd D:\fast-api-books\frontend
npm start
```

Expected output:

```
Compiled successfully!
You can now view smart-scheduler-frontend in the browser.
  http://localhost:3000
```

---

## User Flow (End-to-End)

### Step 1: Register Account

1. Open http://localhost:3000
2. See Login page with "Switch to Register" link
3. Click "Switch to Register"
4. Enter email: `test@example.com`
5. Enter password: `pass123`
6. Click "Register"
7. Backend creates user in MongoDB
8. Token saved to localStorage
9. Auto-redirect to Dashboard

### Step 2: Dashboard Load

1. Dashboard mounts
2. Checks localStorage for token
3. If token exists:
   - `GET /schedules` → Load user schedules (empty on first login)
   - `GET /events` → Load user events (empty on first login)
4. Render 3 tabs: My Schedule, Import Schedule, Events

### Step 3: Import Schedules

Choose method A or B:

**Method A: Upload Excel File**

1. Click "Import Schedule" tab
2. Click "Upload Excel File" button
3. Select `.xlsx` file with schedule data
4. Backend parses Excel:
   - `POST /upload/schedule`
   - Uses InputParser.parse_excel()
   - Returns parsed schedules
5. Shows parsed data for review
6. Click "Confirm & Save"
   - `POST /ai/confirm-parse`
   - Saves to MongoDB
7. View in "My Schedule" tab

**Method B: Parse Text**

1. Click "Import Schedule" tab
2. Click "Parse Text" button
3. Paste schedule text (e.g., "Toán 15/1 phòng 201 10:00-11:30")
4. Click "Parse"
   - `POST /ai/parse-text`
   - Uses InputParser.parse_text() with regex
   - Returns parsed schedules
5. Click "Confirm & Save"
   - `POST /ai/confirm-parse`
   - Saves to MongoDB
6. View in "My Schedule" tab

### Step 4: View & Manage

- **My Schedule**: Grid view of all schedules
- **Events**: List of deadlines/events
- **Import Schedule**: Upload new schedules anytime

---

## Database Schema

### MongoDB Collections

**users**

```javascript
{
  _id: ObjectId,
  email: string,
  password_hash: string,
  password_salt: string,
  role: "user" | "instructor" | "admin",
  full_name: string,
  created_at: date
}
```

**schedules**

```javascript
{
  _id: ObjectId,
  user_id: ObjectId (ref: users),
  subject: string,
  day_of_week: string,
  start_time: string (HH:MM),
  end_time: string (HH:MM),
  room: string,
  teacher: string,
  notes: string
}
```

**events**

```javascript
{
  _id: ObjectId,
  user_id: ObjectId (ref: users),
  title: string,
  due_date: date,
  priority: string,
  status: string,
  description: string
}
```

---

## Troubleshooting

### Frontend keeps loading (spinning)

- **Cause**: API call failing, infinite useEffect retry
- **Fix**: Check browser console (F12) for error message
- **Verify**: `curl http://localhost:8000/health` → should return `{status: ok}`

### Login works but Dashboard shows nothing

- **Cause**: `/schedules` or `/events` endpoint failing
- **Check**: Backend logs for error (should show GET /schedules request)
- **Verify**: Token format in localStorage (should be: `authorization: "Bearer <token>"`)

### Backend won't start

- **Check**: MongoDB running? `MongoDB Compass` should show connected
- **Check**: Port 8000 free? `netstat -ano | findstr :8000`
- **Check**: All dependencies? `pip list | grep fastapi`

### Token invalid error

- **Cause**: Token expired or corrupted
- **Fix**: Clear localStorage and re-login
  ```javascript
  // In browser console:
  localStorage.clear();
  ```

---

## API Authentication

All endpoints except `/auth/register`, `/auth/login`, `/health` require:

```
Authorization: Bearer <JWT_TOKEN>
```

Frontend automatically adds this header via axios interceptor in `api.js`:

```javascript
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
```

---

## Environment Variables (.env)

```env
# Database
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=fastapi_books

# JWT
JWT_SECRET_KEY=super-secret-key-32-chars-minimum-here!!!
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Redis (Optional - app works without it)
REDIS_URL=redis://localhost:6379/0

# AI/LLM
HF_API_KEY=hf_YOUR_API_KEY_HERE

# Telegram (Optional)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
```

---

## Port Configuration

| Service  | Port  | URL                               |
| -------- | ----- | --------------------------------- |
| Backend  | 8000  | http://localhost:8000             |
| Frontend | 3000  | http://localhost:3000             |
| MongoDB  | 27017 | mongodb://localhost:27017         |
| Redis    | 6379  | redis://localhost:6379 (optional) |

---

## Development Tips

### Hot Reload

- **Backend**: Changes to `.py` files auto-reload (uvicorn watch)
- **Frontend**: Changes to `.jsx` files auto-reload (React development server)

### Test Endpoints with curl

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"pass123","full_name":"Test User","role":"user"}'

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"pass123"}'

# Get schedules (replace TOKEN with actual token)
curl -X GET http://localhost:8000/schedules \
  -H "Authorization: Bearer TOKEN"
```

### View Database

1. Open MongoDB Compass
2. Connect to `mongodb://localhost:27017`
3. Select database: `fastapi_books`
4. View collections: `users`, `schedules`, `events`

---

## Next Steps

1. ✅ Both Backend & Frontend running
2. ✅ Register & Login account
3. ✅ Import schedule via Excel or text
4. ⏳ Test AI classification (priority)
5. ⏳ Test scheduler assistant (free slots)
6. ⏳ Implement notifications (email/Telegram)
