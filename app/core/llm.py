"""
Tích hợp LLM từ Hugging Face.
Dùng Inference API hoặc tải model locally.
"""

import os
import json
import requests
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Hugging Face API settings
HF_API_KEY = os.getenv("HF_API_KEY", "")  # Set environment variable để dùng
HF_API_URL = "https://api-inference.huggingface.co/models/"

# Models khả dụng
MODELS = {
    "mistral": "mistralai/Mistral-7B-Instruct-v0.1",
    "llama2": "meta-llama/Llama-2-7b-chat",
    "phi": "microsoft/phi-2",
}

# Sử dụng model nào (có thể thay đổi)
DEFAULT_MODEL = MODELS["mistral"]


def _call_hf_api(prompt: str, model: str = DEFAULT_MODEL) -> Optional[str]:
    """
    Gọi Hugging Face Inference API.
    
    Args:
        prompt: Prompt để gửi tới LLM
        model: Model name
    
    Returns:
        Kết quả từ LLM hoặc None nếu lỗi
    """
    if not HF_API_KEY:
        logger.warning("HF_API_KEY chưa được set - sẽ dùng mock response")
        return None
    
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    url = f"{HF_API_URL}{model}"
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.7,
            "top_p": 0.9,
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        # API trả về list với generated text
        if isinstance(result, list) and len(result) > 0:
            return result[0].get("generated_text", "")
        
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Lỗi gọi Hugging Face API: {e}")
        return None


def parse_question_to_json(question: str) -> Dict[str, Any]:
    """
    Chuyển câu hỏi tự nhiên sang JSON có cấu trúc.
    
    Args:
        question: Câu hỏi của sinh viên (tiếng Việt)
    
    Returns:
        {
            intent: "get_schedule" | "get_free_time" | "check_availability" | "create_event" | "chat",
            confidence: 0.0-1.0,
            entities: {...},
            raw_text: question
        }
    """
    
    prompt = f"""Bạn là AI trợ lý phân tích ý định của sinh viên.
Phân tích câu hỏi sau và trả về JSON:

Câu hỏi: "{question}"

Hướng dẫn:
1. Nếu hỏi về lịch học (ví dụ: "Hôm nay tôi có lịch gì?", "Lịch thứ 2 ra sao?"):
   - intent: "get_schedule"
   - Trích xuất ngày/thời gian nếu có
   
2. Nếu hỏi về thời gian rảnh (ví dụ: "Tôi có thời gian rảnh không?", "Chiều mai rảnh không?"):
   - intent: "get_free_time"
   - Trích xuất thời gian nếu có
   
3. Nếu kiểm tra có lịch vào thời gian cụ thể (ví dụ: "Thứ 3 lúc 10h tôi có bận không?"):
   - intent: "check_availability"
   - Trích xuất thời gian
   
4. Nếu tạo sự kiện/deadline mới (ví dụ: "Nhắc tôi nộp đồ án vào thứ 5"):
   - intent: "create_event"
   - Trích xuất tiêu đề sự kiện, thời gian
   
5. Nếu không liên quan lịch học hoặc chỉ là trò chuyện bình thường:
   - intent: "chat"
   - confidence: 1.0

Trả về CHỈ JSON (không có text khác):
{{
    "intent": "...",
    "confidence": 0.0-1.0,
    "entities": {{}},
    "raw_text": "{question}"
}}"""
    
    response = _call_hf_api(prompt)
    
    if response:
        try:
            # Tìm JSON trong response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Lỗi parse JSON từ LLM: {e}, response: {response}")
    
    # Fallback: dùng heuristic đơn giản nếu LLM không hoạt động
    return _parse_question_heuristic(question)


def _parse_question_heuristic(question: str) -> Dict[str, Any]:
    """
    Fallback: parse câu hỏi bằng heuristic đơn giản.
    """
    q_lower = question.lower()
    
    if any(w in q_lower for w in ["lịch", "lịch học", "lịch này", "lịch nào", "có lịch gì", "bài học"]):
        return {
            "intent": "get_schedule",
            "confidence": 0.8,
            "entities": {},
            "raw_text": question
        }
    elif any(w in q_lower for w in ["rảnh", "có rảnh", "có bận", "bận không", "thời gian rảnh"]):
        return {
            "intent": "get_free_time",
            "confidence": 0.8,
            "entities": {},
            "raw_text": question
        }
    elif any(w in q_lower for w in ["kiểm tra", "chiều", "sáng", "chiều tối", "lúc"]) and any(w in q_lower for w in ["bận", "rảnh", "có"]):
        return {
            "intent": "check_availability",
            "confidence": 0.7,
            "entities": {},
            "raw_text": question
        }
    elif any(w in q_lower for w in ["nhắc", "tạo", "nộp", "deadline", "sự kiện", "lịch mới"]):
        return {
            "intent": "create_event",
            "confidence": 0.75,
            "entities": {},
            "raw_text": question
        }
    else:
        return {
            "intent": "chat",
            "confidence": 1.0,
            "entities": {},
            "raw_text": question
        }


def get_chat_response(message: str, context: Optional[str] = None) -> str:
    """
    Lấy response chat tự nhiên từ LLM.
    
    Args:
        message: Tin nhắn từ người dùng
        context: Bối cảnh (lịch học hiện tại, v.v.)
    
    Returns:
        Phản hồi tự nhiên
    """
    
    context_str = ""
    if context:
        context_str = f"\n\nBối cảnh:\n{context}\n"
    
    prompt = f"""Bạn là một AI trợ lý vui vẻ, thân thiện cho sinh viên.
Trả lời câu hỏi/yêu cầu của sinh viên một cách tự nhiên bằng tiếng Việt.{context_str}

Sinh viên: {message}
AI: """
    
    response = _call_hf_api(prompt)
    
    if response:
        # Làm sạch response
        response = response.strip()
        # Nếu response bắt đầu bằng phần prompt, cắt bỏ
        if "AI:" in response:
            response = response.split("AI:")[-1].strip()
        return response
    
    # Fallback simple response
    return "Xin lỗi, tôi gặp vấn đề. Vui lòng thử lại sau."


def extract_date_from_question(question: str) -> Optional[str]:
    """
    Trích xuất ngày tháng từ câu hỏi.
    TODO: Dùng LLM hoặc datetime parsing
    """
    # Fallback đơn giản
    if "hôm nay" in question.lower():
        return "today"
    elif "mai" in question.lower():
        return "tomorrow"
    elif "thứ" in question.lower():
        # TODO: Parse thứ mấy
        pass
    
    return None
