# MongoDB Schema (Draft)

## Collections

### users

- \_id: ObjectId
- email: string (unique, indexed)
- hashed_password: string
- salt: string
- full_name: string (optional)
- telegram_chat_id: string (optional)
- created_at: datetime
- timezone: string (optional)

Indexes:

- { email: 1 } (unique)
- { telegram_chat_id: 1 } (sparse)

---

### events

- \_id: ObjectId
- user_id: ObjectId (ref users)
- title: string
- description: string (optional)
- start: datetime (tz-aware, stored in UTC)
- end: datetime (tz-aware)
- remind_before_minutes: int (default 30)
- notify_via: array[string] (e.g., ["telegram", "email"]) default ["telegram"]
- recurring: object|null (type, pattern)
- created_at: datetime
- updated_at: datetime

Indexes:

- { user_id: 1, start: 1 }
- { start: 1 }

---

## Migration plan (dev → prod)

1. Start with in-memory/mock implementation for rapid iteration and tests.
2. Add MongoDB connection via Motor (async) or PyMongo wrapper in production.
3. Write data access layer `app/db/mongo.py` that exposes basic CRUD interfaces for `users` and `events`.
4. Create migration scripts (Python) or use `mongodump/mongorestore` for data migration if needed.
5. Add indexes and validate test data with integration tests in staging.
6. Switch feature flags and environment variables to point to real DB.

Notes:

- Use UTC storage for datetimes and convert to user's timezone on output.
- Consider storing user timezone to allow correct day boundaries for "hôm nay" queries.
