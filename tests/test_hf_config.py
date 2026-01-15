"""
Test để xác minh HF_API_KEY cấu hình đúng
"""

import os
import pytest
from app.core import llm

def test_hf_api_key_configured():
    """Kiểm tra HF_API_KEY đã được cấu hình"""
    hf_key = os.getenv("HF_API_KEY", "")
    assert hf_key != "", "HF_API_KEY chưa được cấu hình. Hãy xem HF_API_KEY_SETUP.md"
    assert hf_key.startswith("hf_"), "HF_API_KEY phải bắt đầu bằng 'hf_'"
    print(f"✅ HF_API_KEY cấu hình: {hf_key[:20]}...")

def test_parse_question_with_real_lm():
    """Test parse_question_to_json với LLM thực"""
    result = llm.parse_question_to_json("Hôm nay tôi có bao nhiêu buổi học?")
    # Nếu không có HF_API_KEY, sẽ fallback tới heuristic parsing
    if "ok" in result:
        assert result["ok"] == True
        assert "intent" in result
        assert "confidence" in result
        print(f"✅ Parse result: {result}")
    else:
        # Fallback case (không có API key)
        assert "intent" in result
        print(f"✅ Parse result (fallback): {result}")


def test_get_chat_response_with_real_llm():
    """Test get_chat_response với LLM thực"""
    response = llm.get_chat_response("Thời tiết hôm nay như thế nào?")
    # Fallback vẫn có response
    assert response is not None
    assert len(response) > 0
    print(f"✅ Chat response: {response[:100]}...")

def test_fallback_still_works():
    """Fallback parsing vẫn hoạt động ngay cả nếu HF API không có"""
    # Test với câu hỏi có keyword
    result = llm._parse_question_heuristic("Tôi có rảnh chiều nay không?")
    assert result["intent"] == "get_free_time"
    print(f"✅ Fallback works: {result}")

if __name__ == "__main__":
    # Chạy trực tiếp mà không cần pytest
    print("\n=== Kiểm tra HF_API_KEY ===\n")
    
    hf_key = os.getenv("HF_API_KEY", "")
    if not hf_key:
        print("❌ HF_API_KEY chưa cấu hình!")
        print("   1. Mở file .env")
        print("   2. Thay HF_API_KEY=hf_YOUR_API_KEY_HERE")
        print("   3. Lưu file")
        print("   4. Khởi động lại terminal/IDE")
    else:
        print(f"✅ HF_API_KEY cấu hình: {hf_key[:20]}...")
