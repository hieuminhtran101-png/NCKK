"""
Test LLM integration.
"""

import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.core import llm
from app.core import agent as agent_core
from datetime import datetime, timedelta

def test_parse_question_to_json():
    """Test phân tích câu hỏi thành JSON."""
    # Test hỏi lịch học
    result = llm.parse_question_to_json("Hôm nay tôi có lịch gì?")
    assert "intent" in result
    assert "confidence" in result
    assert result["intent"] in ["get_schedule", "chat"]
    print(f"✓ Phân tích 'Hôm nay tôi có lịch gì?': {result['intent']}")

def test_parse_question_free_time():
    """Test phân tích hỏi thời gian rảnh."""
    result = llm.parse_question_to_json("Chiều nay tôi có rảnh không?")
    assert "intent" in result
    print(f"✓ Phân tích 'Chiều nay tôi có rảnh không?': {result['intent']}")

def test_parse_question_chat():
    """Test phân tích chat không liên quan."""
    result = llm.parse_question_to_json("Thời tiết hôm nay như thế nào?")
    assert result["intent"] == "chat"
    assert result["confidence"] == 1.0
    print(f"✓ Phân tích 'Thời tiết hôm nay...': {result['intent']}")

def test_get_chat_response():
    """Test lấy response chat tự nhiên."""
    response = llm.get_chat_response("Xin chào, bạn tên gì?")
    assert isinstance(response, str)
    assert len(response) > 0
    print(f"✓ Chat response: {response[:50]}...")

def test_handle_chat_intent():
    """Test xử lý intent 'chat'."""
    parsed = {
        "intent": "chat",
        "confidence": 1.0,
        "raw_text": "Bạn biết gì về Python không?",
        "entities": {}
    }
    
    result = agent_core.handle_parse(parsed, user_id=1)
    assert result["ok"] == True
    assert result["action"] == "chat"
    assert "response" in result["result"]
    assert len(result["messages"]) > 0
    print(f"✓ Chat intent response: {result['messages'][0][:50]}...")

def test_agent_with_low_confidence():
    """Test khi confidence thấp."""
    parsed = {
        "intent": "get_schedule",
        "confidence": 0.3,  # Thấp
        "raw_text": "Một cái gì đó",
        "entities": {}
    }
    
    result = agent_core.handle_parse(parsed, user_id=1)
    assert result["ok"] == False
    assert result["needs_clarification"] == True
    print(f"✓ Low confidence: {result['messages'][0]}")

if __name__ == '__main__':
    print("Testing LLM integration...\n")
    
    test_parse_question_to_json()
    test_parse_question_free_time()
    test_parse_question_chat()
    test_get_chat_response()
    test_handle_chat_intent()
    test_agent_with_low_confidence()
    
    print("\n✅ Tất cả test LLM qua!")
