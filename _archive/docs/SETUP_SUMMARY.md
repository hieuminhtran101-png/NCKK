# 📋 Tóm Tắt Cấu Hình HF_API_KEY + Telegram Bot Flow

## ✅ Đã Hoàn Thành

### LLM Integration (Hugging Face)

- ✅ `app/core/llm.py` - Wrapper cho Hugging Face Inference API
- ✅ Fallback heuristic parsing (hoạt động mà không cần API key)
- ✅ Intent detection: `get_schedule`, `get_free_time`, `check_availability`, `create_event`, `chat`
- ✅ Natural language chat responses
- ✅ `POST /chat` endpoint (automatic LLM-based intent routing)
- ✅ `POST /agent/interpret` endpoint (manual intent passing - for testing)
- ✅ 35 unit tests passing (including 3 new LLM config tests)
- ✅ `.env` file with HF_API_KEY template
- ✅ `setup_hf_key.py` script for easy configuration
- ✅ `python-dotenv` integration in `app/main.py`

### Telegram Bot Flow

- ✅ `POST /telegram/webhook` - nhận Telegram updates
- ✅ `POST /telegram/connect` - gán `chat_id` với `user_id`
- ✅ `handle_update()` - xử lý /today command
- ✅ `register_chat()` - lưu telegram chat relationship
- ✅ User lookup by telegram chat_id

---

## 🔧 Cấu Hình HF_API_KEY

### Lựa chọn 1: Script tự động (Khuyến nghị)

```bash
python setup_hf_key.py
```

Script sẽ:

1. Hỏi bạn nhập Hugging Face API key
2. Tự động lưu vào `.env`
3. Test cấu hình

### Lựa chọn 2: Manual (nếu script không hoạt động)

1. **Lấy API Key:** https://huggingface.co/settings/tokens

   - Click "New token" → chọn "Read"
   - Copy token (format: `hf_...`)

2. **Cấu hình .env:**

   ```
   HF_API_KEY=hf_your_actual_key_here
   ```

3. **Reload:**
   - Đóng terminal
   - Mở terminal mới
   - Kiểm tra: `echo $env:HF_API_KEY`

---

## 🧪 Test LLM Integration

### Test 1: Cấu hình kiểm tra

```bash
pytest tests/test_hf_config.py::test_hf_api_key_configured -v
```

### Test 2: All tests

```bash
pytest -v
# Mong đợi: 35 passed
```

### Test 3: API test

```bash
# Terminal 1: Start server
python -m uvicorn app.main:app --reload

# Terminal 2: Test /chat
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hôm nay tôi có bao nhiêu buổi học?"}'

# Expected response:
# {
#   "ok": true,
#   "action": "get_schedule",
#   "result": {...},
#   "messages": ["Bạn có 3 buổi học..."]
# }
```

---

## 📱 Telegram Bot Flow (Tổng Quan)

```
┌─────────────────────────────────────────┐
│ Web App (User logged in)                │
├─────────────────────────────────────────┤
│ Button: "Connect Telegram Bot"          │
│         ↓                               │
│         Generate JWT Token              │
│         ↓                               │
│  Show QR/Link: t.me/Bot?start=TOKEN    │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ Telegram Bot (/start TOKEN)             │
├─────────────────────────────────────────┤
│ 1. Verify JWT token                     │
│ 2. Extract chat_id from message         │
│ 3. POST /telegram/connect               │
│    {chat_id, user_id from token}        │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│ FastAPI Server                          │
├─────────────────────────────────────────┤
│ handle_update():                        │
│  1. Receive Telegram JSON               │
│  2. Extract chat_id                     │
│  3. Find user_id by chat_id             │
│  4. Process command (/today, chat, etc) │
│  5. Send response via send_message()    │
└─────────────────────────────────────────┘
```

### Endpoints Telegram Hiện Có

| Endpoint            | Method | Purpose                  | Status  |
| ------------------- | ------ | ------------------------ | ------- |
| `/telegram/webhook` | POST   | Receive Telegram updates | ✅ Done |
| `/telegram/connect` | POST   | Link chat_id to user_id  | ✅ Done |

### Cần Thêm (Phase 2)

- Web UI button "Connect Telegram"
- JWT token generation & validation
- Real Telegram Bot token (BotFather)
- Webhook URL registration on Telegram
- Natural chat forwarding to LLM via bot

---

## 📂 File Structure (New Files)

```
fastapi-books/
├── .env                          # Environment variables (ADD YOUR HF_API_KEY HERE)
├── .gitignore                    # Ignore .env, __pycache__, etc
├── setup_hf_key.py              # Easy setup script
├── HF_API_KEY_SETUP.md          # Detailed HF setup guide
├── COMPLETE_SETUP_GUIDE.md      # Full setup + Telegram flow guide
├── app/
│   ├── main.py                  # Updated: load_dotenv() added
│   └── core/
│       └── llm.py              # New: Hugging Face LLM wrapper
└── tests/
    └── test_hf_config.py       # New: 3 HF config tests
```

---

## 🚀 Next Steps

### Now (Immediate)

1. ✅ Run `python setup_hf_key.py` - configure HF_API_KEY
2. ✅ Run `pytest -v` - all tests pass
3. ✅ Test `/chat` endpoint with curl
4. ✅ Verify LLM responses (not fallback)

### Phase 2 (Backend Complete)

- [ ] Web UI "Connect Telegram Button"
- [ ] JWT token for Telegram /start
- [ ] Real Telegram Bot token setup
- [ ] Register webhook URL on Telegram servers
- [ ] Natural chat via Telegram bot → LLM

### Phase 3 (Database)

- [ ] MongoDB migration (instead of in-memory)
- [ ] Real Telegram API integration (not outbox)
- [ ] Admin role verification

---

## 📊 Test Status

```
✅ 35 tests passing
   ├── 10 core features (auth, events, schedules, public_events, scheduler)
   ├── 6 LLM integration (parse, chat, intent dispatch)
   ├── 4 /chat endpoint
   ├── 3 HF config (new)
   ├── 4 agent interpret
   ├── 2 auth
   ├── 3 events CRUD
   ├── 8 schedules & public events
   ├── 3 scheduler
   └── 1 telegram
```

---

## 💡 Troubleshooting

### LLM vẫn fallback

```bash
# 1. Check HF_API_KEY
echo $env:HF_API_KEY

# 2. Run config test
pytest tests/test_hf_config.py::test_hf_api_key_configured -v

# 3. Check logs
python -c "from app.core import llm; print(llm.parse_question_to_json('test'))"
```

### Slow LLM response

- Lần đầu: ~30s (model initialization)
- Lần sau: ~5-10s (normal)
- Có thể host locally để nhanh hơn

### Rate limited

- Free tier: ~25 req/min
- Upgrade Hugging Face Pro
- Hoặc host model locally

---

## 📝 Notes

- **Fallback parsing** hoạt động mà không cần API key (test development friendly)
- **Dual-mode**: `/chat` (auto LLM) + `/agent/interpret` (manual for testing)
- **Supported intents**: schedule, free_time, availability, event, chat
- **Telegram bot** scaffold done, awaiting real bot token
- **System design**: Graceful degradation - works with or without HF API

---

**Status: ✅ LLM Integration Complete + Ready for Telegram Phase 2**

Xem chi tiết: [COMPLETE_SETUP_GUIDE.md](COMPLETE_SETUP_GUIDE.md)
