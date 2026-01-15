#!/usr/bin/env python3
"""
Setup script để cấu hình HF_API_KEY dễ dàng
"""

import os
import sys
from pathlib import Path

def main():
    print("=" * 60)
    print("⚙️  FastAPI Books - HF_API_KEY Setup")
    print("=" * 60)
    
    # Kiểm tra .env file
    env_path = Path(".env")
    
    print("\n📝 Hướng dẫn lấy Hugging Face API Key:")
    print("   1. Truy cập: https://huggingface.co/settings/tokens")
    print("   2. Click 'New token'")
    print("   3. Copy token (bắt đầu bằng 'hf_')")
    
    api_key = input("\n🔑 Nhập Hugging Face API Key: ").strip()
    
    if not api_key:
        print("❌ API Key không được để trống!")
        return
    
    if not api_key.startswith("hf_"):
        print("⚠️  Cảnh báo: API Key nên bắt đầu bằng 'hf_'")
        confirm = input("   Tiếp tục? (y/n): ").strip().lower()
        if confirm != "y":
            return
    
    # Đọc .env hiện tại
    env_content = ""
    if env_path.exists():
        with open(env_path, "r") as f:
            env_content = f.read()
    
    # Cập nhật hoặc tạo mới
    if "HF_API_KEY=" in env_content:
        # Replace existing key
        lines = env_content.split("\n")
        new_lines = []
        for line in lines:
            if line.startswith("HF_API_KEY="):
                new_lines.append(f"HF_API_KEY={api_key}")
            else:
                new_lines.append(line)
        env_content = "\n".join(new_lines)
    else:
        # Add new key
        if env_content and not env_content.endswith("\n"):
            env_content += "\n"
        env_content += f"HF_API_KEY={api_key}\n"
    
    # Ghi file
    with open(env_path, "w") as f:
        f.write(env_content)
    
    print(f"\n✅ Đã lưu API Key vào .env")
    print(f"   {env_path.absolute()}")
    
    print("\n🧪 Testing cấu hình...")
    os.environ["HF_API_KEY"] = api_key
    
    try:
        from app.core import llm
        result = llm.parse_question_to_json("Hôm nay có lịch gì?")
        if result.get("ok"):
            print(f"✅ Parse test passed!")
            print(f"   Intent: {result.get('intent')}")
            print(f"   Confidence: {result.get('confidence')}")
        else:
            print(f"⚠️  Parse test returned error (có thể API key không hợp lệ)")
    except Exception as e:
        print(f"⚠️  Test error: {e}")
        print("   Hãy chạy: pytest tests/test_hf_config.py -v")
    
    print("\n🚀 Tiếp theo:")
    print("   1. Khởi động server: python -m uvicorn app.main:app --reload")
    print("   2. Test /chat endpoint:")
    print("      curl -X POST http://localhost:8000/chat \\")
    print("        -H 'X-User-Id: 1' \\")
    print("        -H 'Content-Type: application/json' \\")
    print("        -d '{\"text\": \"Hôm nay tôi có lịch gì?\"}'")
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
