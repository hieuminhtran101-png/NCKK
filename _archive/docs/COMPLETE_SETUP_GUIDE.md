# 🚀 Hướng Dẫn Hoàn Chỉnh - Cấu Hình HF_API_KEY + Telegram Flow

## Phần 1: Cấu Hình HF_API_KEY (LLM Integration)

### Cách 1: Dùng Script Setup (Dễ nhất)

```bash
python setup_hf_key.py
```

Script này sẽ:

- Hỏi bạn nhập Hugging Face API Key
- Lưu vào `.env`
- Test cấu hình tự động

### Cách 2: Manual Setup

1. **Lấy API Key:**

   - Truy cập: https://huggingface.co/settings/tokens
   - Đăng nhập (hoặc tạo tài khoản)
   - Click "New token" → chọn "Read" → Copy

2. **Cấu hình:**

   - Mở file `.env`
   - Thay:
     ```
     HF_API_KEY=hf_YOUR_API_KEY_HERE
     ```
     bằng API key thực tế:
     ```
     HF_API_KEY=hf_xxxxxxxxxxxxxxxxxxx
     ```

3. **Reload Environment:**
   - Đóng terminal hiện tại
   - Mở terminal mới
   - Kiểm tra: `echo $env:HF_API_KEY`

### Cách 3: Set Environment Variable (Tạm thời)

**PowerShell:**

```powershell
$env:HF_API_KEY = "hf_your_api_key"
```

**CMD:**

```cmd
set HF_API_KEY=hf_your_api_key
```

---

## Phần 2: Test LLM Integration

### Test 1: Unit Tests

```bash
pytest tests/test_hf_config.py -v
```

Mong đợi:

```
test_hf_api_key_configured PASSED ✅
test_parse_question_with_real_lm PASSED ✅
test_get_chat_response_with_real_llm PASSED ✅
```

### Test 2: Full Test Suite

```bash
pytest -v
```

Nên có 32+ tests passing

### Test 3: API Test với cURL

```bash
# 1. Khởi động server
python -m uvicorn app.main:app --reload

# 2. Trong terminal khác, test /chat
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hôm nay tôi có bao nhiêu buổi học?"}'
```

Phản hồi mong đợi:

```json
{
  "ok": true,
  "action": "get_schedule",
  "result": {...},
  "messages": ["Hôm nay bạn có 3 buổi học..."]
}
```

---

## Phần 3: Telegram Bot Integration Flow

### Kiến Trúc Hiện Tại

```
┌─ Web App (User logs in)
│  │
│  └─ Button "Connect Telegram Bot"
│     │
│     └─ Generate token (JWT)
│        │
│        └─ Show QR Code / Link to:
│           https://t.me/YourBot?start=TOKEN
│
├─ Telegram Bot (/start with token)
│  │
│  └─ Xác thực token
│  │
│  └─ POST /telegram/connect
│     (chat_id + user_id)
│
├─ Telegram sends updates to webhook
│  │
│  └─ POST /telegram/webhook
│     └─ handle_update()
│        ├─ Lấy telegram_user_id từ update
│        └─ Tìm user_id trong hệ thống
│           └─ Gán link
│
└─ User can now:
   - Chat với bot
   - Xem lịch: /today
   - Chat tự nhiên
   - Nhận reminders tự động
```

### Các Endpoint Telegram Hiện Có

1. **POST /telegram/connect**

   - Headers: `X-User-Id: 1`
   - Body: `{"chat_id": "123456789"}`
   - Response: `{"ok": true}`

2. **POST /telegram/webhook**
   - Nhận JSON update từ Telegram
   - Xử lý /today command
   - Đọc chat_id → tìm user → xử lý

### Còn Cần Thêm (Phase 2)

- [ ] Web button "Connect Telegram"
- [ ] Generate + validate JWT token (/start?token=xxx)
- [ ] Real Telegram Bot token (từ BotFather)
- [ ] Set webhook URL trên Telegram server
- [ ] Chat natural language forwarding to LLM
- [ ] Auto-send reminders via Telegram

### Setup Telegram Bot (Future)

```bash
# 1. Chat với BotFather trên Telegram
# /newbot → nhập tên → nhận bot token

# 2. Lưu token vào .env
HF_API_KEY=hf_xxx
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklmnoPQRstuvWXYzabcdefg

# 3. Set webhook URL
# POST https://api.telegram.org/botTOKEN/setWebhook
# {"url": "https://your-domain.com/telegram/webhook"}

# 4. Kiểm tra
curl https://api.telegram.org/botTOKEN/getWebhookInfo
```

---

## Phần 4: Chạy Full System

### 1. Cấu hình tất cả

```bash
# Cấu hình HF_API_KEY
python setup_hf_key.py

# Tạo số dữ liệu test (tùy chọn)
# python scripts/seed_data.py
```

### 2. Khởi động server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test các endpoints

```bash
# Chat với LLM
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"text": "Chiều nay tôi rảnh không?"}'

# Agent interpret (manual)
curl -X POST http://localhost:8000/agent/interpret \
  -H "X-User-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "get_schedule",
    "confidence": 0.9,
    "entities": {"date": "2026-01-15"},
    "raw_text": "Hôm nay tôi có lịch gì?"
  }'

# Telegram webhook (when ready)
curl -X POST http://localhost:8000/telegram/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "chat": {"id": 12345},
      "text": "/today"
    }
  }'
```

---

## Phần 5: Troubleshooting

### LLM Response vẫn fallback

**Nguyên nhân:**

- HF_API_KEY chưa cấu hình
- API key không hợp lệ
- Hugging Face Inference API down
- Network issue

**Giải pháp:**

```bash
# 1. Kiểm tra HF_API_KEY
echo $env:HF_API_KEY

# 2. Chạy test
pytest tests/test_hf_config.py -v -s

# 3. Xem log chi tiết
python -c "from app.core import llm; print(llm.parse_question_to_json('test'))"

# 4. Kiểm tra internet
ping api-inference.huggingface.co
```

### Chậm response lần đầu

**Nguyên nhân:** Hugging Face tải model (~30s)

**Giải pháp:**

- Chờ lần đầu
- Lần tiếp theo nhanh hơn
- Hoặc chuyển model nhẹ hơn (Phi)

### Rate limit

**Nguyên nhân:** Free tier giới hạn

**Giải pháp:**

- Upgrade Hugging Face Pro
- Hoặc host model locally (xem Advanced Setup)

---

## Phần 6: Advanced (Optional)

### Host Model Locally

```bash
pip install transformers torch

# Trong app/core/llm.py thay _call_hf_api():
from transformers import pipeline
pipe = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.1")
```

### Switch Model

```python
# Trong parse_question_to_json():
# response = llm._call_hf_api(prompt, model="llama2")
# response = llm._call_hf_api(prompt, model="phi")
```

### Database Migration

Hiện tại dùng in-memory dicts. Để migrate MongoDB:

```bash
pip install motor  # hoặc pymongo

# Tạo app/db/mongodb.py
# Update app/core/*.py để dùng Motor
```

---

## ✅ Checklist Hoàn Thành

- [ ] Cấu hình HF_API_KEY (script hoặc manual)
- [ ] Chạy `pytest tests/test_hf_config.py` → PASSED
- [ ] Chạy `pytest -v` → 32+ PASSED
- [ ] Test `/chat` endpoint với cURL
- [ ] Kiểm tra log không có "fallback"
- [ ] Ready để ship LLM backend! 🎉

---

## Liên Hệ Support

Nếu gặp vấn đề:

1. Xem logs: `pytest -v -s`
2. Kiểm tra `.env` file
3. Xem HF_API_KEY_SETUP.md
4. Restart terminal/IDE

**Chúc mừng! Bạn đã cấu hình LLM integration thành công!** 🚀
