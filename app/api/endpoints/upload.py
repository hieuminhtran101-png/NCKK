"""
File Upload & AI Processing Endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Header, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import tempfile
import os
from app.db.mongodb import get_db
from app.core.ai_agent import InputParser, PriorityEngine, Priority
from app.core.redis import cache_ai_parse, get_ai_parse
from app.core.auth_mongo import verify_token, get_current_user
from bson import ObjectId
import uuid
from datetime import datetime

# Schemas
class ParseConfirmRequest(BaseModel):
    request_id: str

class ParseTextRequest(BaseModel):
    text: str

router = APIRouter()

@router.post('/upload/schedule')
async def upload_schedule(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    """Upload Excel file to parse schedule"""
    try:
        user_id = current_user.get("user_id")
        
        # Save temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name
        
        try:
            # Parse Excel
            schedules = InputParser.parse_excel(tmp_path)
            
            if not schedules:
                raise HTTPException(status_code=400, detail="No schedule found in file")
            
            # Convert to dict
            parsed_data = [s.to_dict() for s in schedules]
            
            # Cache result
            request_id = str(uuid.uuid4())
            cache_ai_parse(request_id, {"schedules": parsed_data, "user_id": user_id})
            
            return {
                "ok": True,
                "request_id": request_id,
                "count": len(parsed_data),
                "schedules": parsed_data
            }
        finally:
            os.unlink(tmp_path)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/ai/parse-text')
def parse_text(payload: ParseTextRequest, current_user: dict = Depends(get_current_user)):
    """Parse raw text to extract schedule"""
    try:
        text = payload.text
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        user_id = current_user.get("user_id")
        
        # Parse text
        schedules = InputParser.parse_text(text)
        
        if not schedules:
            raise HTTPException(status_code=400, detail="Could not parse schedule from text")
        
        # Convert to dict
        parsed_data = [s.to_dict() for s in schedules]
        
        # Cache result
        request_id = str(uuid.uuid4())
        cache_ai_parse(request_id, {"schedules": parsed_data, "user_id": user_id})
        
        return {
            "ok": True,
            "request_id": request_id,
            "count": len(parsed_data),
            "schedules": parsed_data
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post('/ai/confirm-parse')
def confirm_parse(payload: ParseConfirmRequest, current_user: dict = Depends(get_current_user)):
    """Confirm parsed schedules and save to DB"""
    try:
        user_id = current_user.get("user_id")
        request_id = payload.request_id
        
        # Get from cache
        cached = get_ai_parse(request_id)
        if not cached:
            raise HTTPException(status_code=400, detail="Request not found or expired")
        
        schedules = cached.get("schedules", [])
        
        # Save to MongoDB
        db = get_db()
        schedules_col = db["schedules"]
        
        inserted_ids = []
        for schedule in schedules:
            schedule["user_id"] = ObjectId(user_id)
            schedule["created_at"] = datetime.utcnow()
            result = schedules_col.insert_one(schedule)
            inserted_ids.append(str(result.inserted_id))
        
        return {
            "ok": True,
            "count": len(inserted_ids),
            "schedule_ids": inserted_ids
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/ai/priority/{event_id}')
def get_event_priority(event_id: str, current_user: dict = Depends(get_current_user)):
    """Get priority classification for event"""
    try:
        db = get_db()
        events_col = db["events"]
        
        event = events_col.find_one({"_id": ObjectId(event_id)})
        if not event:
            raise HTTPException(status_code=404, detail="Event not found")
        
        priority = PriorityEngine.classify(event)
        
        return {
            "ok": True,
            "event_id": event_id,
            "priority": priority.value
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get('/ai/free-slots')
def get_free_slots(date: str, duration: int = 60, current_user: dict = Depends(get_current_user)):
    """Get free time slots for given date"""
    try:
        user_id = current_user.get("user_id")
        
        db = get_db()
        schedules_col = db["schedules"]
        
        # Get user's schedules
        user_schedules = list(schedules_col.find({"user_id": ObjectId(user_id)}))
        
        # Find free slots
        from app.core.ai_agent import SchedulerAssistant
        free_slots = SchedulerAssistant.find_free_slots(user_schedules, date, duration)
        
        return {
            "ok": True,
            "date": date,
            "free_slots": free_slots
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
