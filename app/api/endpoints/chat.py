"""
Chat endpoints - User-to-User + User-to-AI chat
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.db.mongodb import get_db
from app.core.auth_mongo import get_current_user
from bson import ObjectId
import json

router = APIRouter(prefix="/chat", tags=["chat"])

# Schemas
class MessageCreate(BaseModel):
    recipient_id: Optional[str] = None  # None = AI chat
    content: str

class MessageOut(BaseModel):
    id: str
    sender_id: str
    recipient_id: Optional[str]
    content: str
    created_at: datetime
    is_ai: bool = False

class ConversationOut(BaseModel):
    id: str
    participant1_id: str
    participant2_id: str
    last_message: str
    last_message_time: datetime

# Store active WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict = {}  # {user_id: websocket}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def broadcast_to_user(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception as e:
                print(f"Error sending to {user_id}: {e}")
    
    async def send_personal(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            try:
                await self.active_connections[user_id].send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

# POST /chat/messages - Send message (user-to-user or user-to-ai)
@router.post("/messages", response_model=MessageOut)
def send_message(
    payload: MessageCreate,
    current_user: dict = Depends(get_current_user)
):
    """Send message to user or AI"""
    db = get_db()
    user_id = current_user.get('user_id')
    
    message_data = {
        "sender_id": ObjectId(user_id),
        "recipient_id": ObjectId(payload.recipient_id) if payload.recipient_id else None,
        "content": payload.content,
        "created_at": datetime.utcnow(),
        "is_ai": payload.recipient_id is None  # None recipient = AI chat
    }
    
    result = db["messages"].insert_one(message_data)
    message_data["id"] = str(result.inserted_id)
    message_data["sender_id"] = str(message_data["sender_id"])
    if message_data["recipient_id"]:
        message_data["recipient_id"] = str(message_data["recipient_id"])
    
    return message_data

# GET /chat/conversations - Get list of conversations
@router.get("/conversations", response_model=List[ConversationOut])
def get_conversations(current_user: dict = Depends(get_current_user)):
    """Get all conversations for current user"""
    db = get_db()
    user_id = ObjectId(current_user.get('user_id'))
    
    # Group messages by recipient
    conversations = []
    pipeline = [
        {
            "$match": {
                "$or": [
                    {"sender_id": user_id},
                    {"recipient_id": user_id}
                ],
                "is_ai": False  # Only user-to-user conversations
            }
        },
        {
            "$sort": {"created_at": -1}
        },
        {
            "$group": {
                "_id": {
                    "$cond": [
                        {"$eq": ["$sender_id", user_id]},
                        "$recipient_id",
                        "$sender_id"
                    ]
                },
                "last_message": {"$first": "$content"},
                "last_message_time": {"$first": "$created_at"}
            }
        }
    ]
    
    results = list(db["messages"].aggregate(pipeline))
    
    for conv in results:
        other_user_id = conv["_id"]
        conversations.append({
            "id": f"{user_id}_{other_user_id}",
            "participant1_id": str(user_id),
            "participant2_id": str(other_user_id),
            "last_message": conv["last_message"],
            "last_message_time": conv["last_message_time"]
        })
    
    return conversations

# GET /chat/messages/{recipient_id} - Get messages with user
@router.get("/messages/{recipient_id}", response_model=List[MessageOut])
def get_messages(
    recipient_id: str,
    current_user: dict = Depends(get_current_user),
    limit: int = 50
):
    """Get message history with user"""
    db = get_db()
    user_id = ObjectId(current_user.get('user_id'))
    other_id = ObjectId(recipient_id)
    
    messages = list(db["messages"].find({
        "$or": [
            {"sender_id": user_id, "recipient_id": other_id},
            {"sender_id": other_id, "recipient_id": user_id}
        ],
        "is_ai": False
    }).sort("created_at", 1).limit(limit))
    
    return [
        {
            "id": str(msg["_id"]),
            "sender_id": str(msg["sender_id"]),
            "recipient_id": str(msg["recipient_id"]) if msg.get("recipient_id") else None,
            "content": msg["content"],
            "created_at": msg["created_at"],
            "is_ai": msg.get("is_ai", False)
        }
        for msg in messages
    ]

# GET /chat/ai-messages - Get AI chat history
@router.get("/ai-messages", response_model=List[MessageOut])
def get_ai_messages(
    current_user: dict = Depends(get_current_user),
    limit: int = 50
):
    """Get message history with AI"""
    db = get_db()
    user_id = ObjectId(current_user.get('user_id'))
    
    messages = list(db["messages"].find({
        "sender_id": user_id,
        "is_ai": True
    }).sort("created_at", -1).limit(limit))
    
    messages.reverse()  # Reverse để oldest first
    
    return [
        {
            "id": str(msg["_id"]),
            "sender_id": str(msg["sender_id"]),
            "recipient_id": None,
            "content": msg["content"],
            "created_at": msg["created_at"],
            "is_ai": True
        }
        for msg in messages
    ]

# POST /chat/ai-response - Get AI response
@router.post("/ai-response")
def get_ai_response(
    payload: MessageCreate,
    current_user: dict = Depends(get_current_user)
):
    """Get AI response with context from database"""
    import os
    import requests
    import random
    
    db = get_db()
    user_id = current_user.get('user_id')
    print(f"\n=== AI Chat Request ===")
    print(f"User: {user_id}")
    print(f"Question: {payload.content}")
    
    # Save user message
    user_msg = {
        "sender_id": ObjectId(user_id),
        "recipient_id": None,
        "content": payload.content,
        "created_at": datetime.utcnow(),
        "is_ai": True
    }
    db["messages"].insert_one(user_msg)
    
    # Check if question is about schedule
    question_lower = payload.content.lower()
    schedule_keywords = ['môn học', 'lớp', 'thời khóa', 'schedule', 'class', 'lesson', 'ngày', 'hôm']
    is_schedule_question = any(keyword in question_lower for keyword in schedule_keywords)
    print(f"Is schedule question: {is_schedule_question}")
    
    ai_response = None
    
    # Try to answer with database context
    if is_schedule_question:
        try:
            user_obj_id = ObjectId(user_id) if isinstance(user_id, str) else user_id
            schedules = list(db["schedules"].find({"user_id": user_obj_id}).limit(10))
            print(f"Found {len(schedules)} schedules in database")
            
            if schedules:
                schedule_list = "📚 **Your Classes:**\n"
                for s in schedules:
                    schedule_list += f"- {s.get('subject', 'N/A')} ({s.get('day_of_week', 'N/A')}) {s.get('start_time', 'N/A')}-{s.get('end_time', 'N/A')} @ {s.get('room', 'N/A')}\n"
                ai_response = schedule_list.strip()
                print(f"Returning schedule info: {len(schedule_list)} chars")
            else:
                ai_response = "📚 You haven't uploaded any schedules yet. Try uploading an Excel file in the Import Schedule tab!"
                print("No schedules found, suggesting upload")
        except Exception as e:
            print(f"Schedule query error: {e}")
            ai_response = f"📚 Error loading schedule: {str(e)}"
    
    # Fallback to HF API if not schedule question or if query fails
    if not ai_response:
        print("Trying Hugging Face API...")
        fallback_responses = [
            "That's interesting! 😊",
            "Thanks for sharing!",
            "I see what you mean.",
            "Great point! 👍",
            "I understand.",
            "Tell me more!",
            "That makes sense!"
        ]
        
        try:
            hf_token = os.getenv("HF_API_KEY")
            if not hf_token:
                ai_response = "🤖 AI offline (no API key configured)"
                print("HF_API_KEY not found")
            else:
                api_url = "https://router.huggingface.co/models/gpt2"
                print(f"Calling HF API: {api_url}")
                
                response = requests.post(
                    api_url,
                    headers={"Authorization": f"Bearer {hf_token}"},
                    json={"inputs": payload.content[:50]},
                    timeout=10
                )
                
                print(f"HF API Status: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    ai_response = result[0].get("generated_text", "").strip()
                    if not ai_response:
                        ai_response = "🤖 " + random.choice(fallback_responses)
                    print(f"HF API Success: {len(ai_response)} chars")
                else:
                    print(f"HF API Error: {response.status_code} - {response.text}")
                    ai_response = "🤖 " + random.choice(fallback_responses)
        except requests.exceptions.Timeout:
            print("HF API Timeout")
            ai_response = "🤖 AI response timeout"
        except Exception as e:
            print(f"HF API Exception: {e}")
            ai_response = "🤖 " + random.choice(fallback_responses)
    
    # Save AI response
    ai_msg = {
        "sender_id": ObjectId("000000000000000000000000"),
        "recipient_id": ObjectId(user_id) if isinstance(user_id, str) else user_id,
        "content": ai_response,
        "created_at": datetime.utcnow(),
        "is_ai": True,
        "ai_generated": True
    }
    result = db["messages"].insert_one(ai_msg)
    print(f"AI Response saved: {ai_response[:50]}...\n")
    
    return {
        "id": str(result.inserted_id),
        "sender_id": "000000000000000000000000",
        "recipient_id": user_id,
        "content": ai_response,
        "created_at": datetime.utcnow(),
        "is_ai": True
    }
    
    return {
        "id": str(result.inserted_id),
        "sender_id": "000000000000000000000000",
        "recipient_id": user_id,
        "content": ai_response,
        "created_at": datetime.utcnow(),
        "is_ai": True
    }

# WebSocket /ws/chat/{recipient_id} - Real-time user chat
@router.websocket("/ws/{recipient_id}")
async def websocket_endpoint(websocket: WebSocket, recipient_id: str):
    """WebSocket for real-time user-to-user chat"""
    # Note: In production, should verify token from query params
    user_id = "authenticated_user"  # Simplified - should get from token
    
    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Save message to DB
            db = get_db()
            msg_data = {
                "sender_id": ObjectId(user_id),
                "recipient_id": ObjectId(recipient_id),
                "content": message.get("content"),
                "created_at": datetime.utcnow(),
                "is_ai": False
            }
            db["messages"].insert_one(msg_data)
            
            # Broadcast to recipient
            await manager.broadcast_to_user(recipient_id, {
                "type": "message",
                "sender_id": user_id,
                "content": message.get("content"),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Send confirmation back
            await websocket.send_json({
                "type": "sent",
                "content": message.get("content")
            })
    
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        # Notify recipient that user went offline
        await manager.broadcast_to_user(recipient_id, {
            "type": "user_offline",
            "user_id": user_id
        })

# WebSocket /ws/ai - Real-time AI chat
@router.websocket("/ws/ai")
async def websocket_ai(websocket: WebSocket):
    """WebSocket for real-time AI chat"""
    user_id = "authenticated_user"  # Simplified
    
    await manager.connect(f"ai_{user_id}", websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Get AI response
            # (same as POST /ai-response but via WebSocket)
            # Simplified implementation
            
            await websocket.send_json({
                "type": "ai_response",
                "content": "AI response here"
            })
    
    except WebSocketDisconnect:
        manager.disconnect(f"ai_{user_id}")
