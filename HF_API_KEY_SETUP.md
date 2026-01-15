# Hướng Dẫn Cấu Hình HF_API_KEY

## Bước 1: Lấy API Key từ Hugging Face

1. Truy cập https://huggingface.co/settings/tokens
2. Đăng nhập bằng tài khoản Hugging Face (hoặc tạo tài khoản mới)
3. Click "New token"
4. Chọn:
   - Name: `FastAPI Books`
   - Type: `Read` (đủ để dùng Inference API)
5. Copy token (bắt đầu bằng `hf_...`)

## Bước 2: Cấu Hình Token

### Option A: Dùng .env file (Recommended)

1. Mở file `.env` tại thư mục gốc
2. Thay thế:
   ```
   HF_API_KEY=hf_YOUR_API_KEY_HERE
   ```
   bằng:
   ```
   HF_API_KEY=hf_xxxxxxxxxxxxxxxxxxxxxx
   ```
3. Lưu file

### Option B: Set environment variable trực tiếp (Windows PowerShell)

```powershell
$env:HF_API_KEY = "hf_YOUR_API_KEY"
```

### Option C: Set environment variable vĩnh viễn (Windows)

```powershell
[Environment]::SetEnvironmentVariable("HF_API_KEY", "hf_YOUR_API_KEY", "User")
```

## Bước 3: Xác Minh Cấu Hình

Chạy lệnh:

```bash
pytest tests/test_llm.py -v -s
```

Kết quả mong đợi:

- Các response từ LLM sẽ thực tế (không còn fallback "Xin lỗi, tôi gặp vấn đề")
- Có thể chậm hơn lần đầu (Hugging Face khởi động model)

## Bước 4: Test /chat Endpoint với LLM Thực

```bash
# Khởi động server
python -m uvicorn app.main:app --reload

# Trong terminal khác, test:
curl -X POST http://localhost:8000/chat \
  -H "X-User-Id: 1" \
  -H "Content-Type: application/json" \
  -d '{"text": "Hôm nay tôi có lịch gì?"}'
```

## Bước 5: Các Model Khả Dụng

Hiện tại hỗ trợ:

| Model             | ID                                   | Tốc độ     | Chất lượng |
| ----------------- | ------------------------------------ | ---------- | ---------- |
| Mistral (default) | `mistralai/Mistral-7B-Instruct-v0.1` | ⭐⭐⭐⭐   | ⭐⭐⭐⭐   |
| Llama 2           | `meta-llama/Llama-2-7b-chat-hf`      | ⭐⭐⭐     | ⭐⭐⭐⭐   |
| Phi               | `microsoft/phi-2`                    | ⭐⭐⭐⭐⭐ | ⭐⭐⭐     |

Thay đổi model trong `parse_question_to_json()`:

```python
response = llm._call_hf_api(prompt, model="llama2")  # hoặc "phi"
```

## Troubleshooting

### "Xin lỗi, tôi gặp vấn đề" (vẫn fallback)

- Kiểm tra: HF_API_KEY có đúng không?
- Kiểm tra: Có kết nối internet không?
- Xem log: Tìm "HF API returned None" trong console

### Slow responses (chậm)

- Model Hugging Face tự khởi động (lần đầu ~30s)
- Yêu cầu tiếp theo nhanh hơn
- Có thể chuyển sang model nhẹ hơn (Phi)

### Rate limit (quá nhiều request)

- Hugging Face free tier giới hạn ~25 request/phút
- Upgrade lên Pro nếu cần
- Hoặc host model locally (xem phần Advanced)

## Advanced: Host Model Locally (Optional)

Thay vì dùng Hugging Face Inference API, có thể tải model:

```bash
pip install transformers torch
```

Và thay đổi `app/core/llm.py`:

```python
# Sau dòng import:
from transformers import pipeline

def _call_hf_api_local(prompt):
    pipe = pipeline("text-generation", model="mistralai/Mistral-7B-Instruct-v0.1")
    result = pipe(prompt, max_length=512)
    return result[0]['generated_text']
```

Điều này sẽ nhanh hơn (không delay) nhưng cần máy mạnh (>8GB RAM, GPU recommended).
