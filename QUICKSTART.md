# ⚡ QUICKSTART - 5 Minute Setup

**Goal:** Get the system running in 5 minutes  
**Target:** All tests passing + server running

---

## 📝 Setup Checklist

```bash
# 1. Environment setup (1 min)
cd d:\fast-api-books
python -m venv venv
venv\Scripts\activate

# 2. Install dependencies (2 min)
pip install -r requirements.txt

# 3. Configure HF_API_KEY (1 min)
python setup_hf_key.py
# Or manually: echo HF_API_KEY=hf_YOUR_KEY >> .env

# 4. Verify tests pass (1 min)
pytest -v
# Expected: 35 passed ✅

# 5. Start server (done!)
python -m uvicorn app.main:app --reload
# Server: http://localhost:8000
# Docs: http://localhost:8000/docs
```

---

## 🧪 Quick Test Commands

```bash
# Health check
curl http://localhost:8000/health

# Chat with LLM (basic question)
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hôm nay tôi có lịch gì?"}'

# Chat with LLM (free time)
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"text": "Chiều nay tôi có rảnh không?"}'

# Chat with LLM (general chat)
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"text": "Thời tiết hôm nay thế nào?"}'
```

---

## ✅ Success Criteria

- [x] `pytest -v` shows **35 passed**
- [x] Server starts without errors
- [x] `GET /health` returns `{"status": "ok"}`
- [x] `/chat` endpoint responds (may be fallback if no HF key)
- [x] Visit http://localhost:8000/docs → interactive API explorer

---

## 🐛 Troubleshooting

| Problem                  | Solution                                          |
| ------------------------ | ------------------------------------------------- |
| `venv not found`         | Run: `python -m venv venv`                        |
| `pip install fails`      | Update pip: `python -m pip install --upgrade pip` |
| `pytest not found`       | Activate venv: `venv\Scripts\activate`            |
| `Port 8000 in use`       | Use different port: `--port 8001`                 |
| `MongoDB not found`      | Start MongoDB or use fallback mode                |
| `/chat returns fallback` | Set HF_API_KEY: `python setup_hf_key.py`          |

---

## 📖 Next Steps

1. ✅ **System running?** → Go to http://localhost:8000/docs
2. 📖 **Want details?** → Read START_HERE.md
3. 🔧 **Need help?** → Check TROUBLESHOOTING.md
4. 🤖 **Want LLM working?** → See LLM_CONFIG.md
5. 🤝 **Building bot?** → Read TELEGRAM_BOT.md

---

**Done!** Your system is ready. Now explore what you built! 🎉
