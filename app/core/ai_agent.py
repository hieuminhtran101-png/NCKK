"""
AI Agent Service - Parser, Priority Engine, Scheduler Assistant
"""

import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
import json

class Priority(str, Enum):
    """Priority levels"""
    CRITICAL = "critical"  # Red
    HIGH = "high"          # Orange
    NORMAL = "normal"      # Yellow
    LOW = "low"            # Gray

class ParsedSchedule:
    """Parsed schedule item"""
    def __init__(self, subject: str, day: str, start_time: str, end_time: str, 
                 location: str = "", notes: str = ""):
        self.subject = subject
        self.day = day
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
        self.notes = notes
    
    def to_dict(self):
        return {
            "subject": self.subject,
            "day": self.day,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "location": self.location,
            "notes": self.notes
        }

class InputParser:
    """Parse Excel, Image, Text input"""
    
    @staticmethod
    def parse_excel(file_path: str) -> List[ParsedSchedule]:
        """Parse Excel file to extract schedule"""
        try:
            import openpyxl
            
            wb = openpyxl.load_workbook(file_path)
            ws = wb.active
            
            schedules = []
            for row in ws.iter_rows(min_row=2, values_only=True):
                if not row[0]:
                    continue
                    
                subject = str(row[0]).strip() if row[0] else ""
                day = str(row[1]).strip() if len(row) > 1 and row[1] else ""
                start_time = str(row[2]).strip() if len(row) > 2 and row[2] else ""
                end_time = str(row[3]).strip() if len(row) > 3 and row[3] else ""
                location = str(row[4]).strip() if len(row) > 4 and row[4] else ""
                notes = str(row[5]).strip() if len(row) > 5 and row[5] else ""
                
                if subject and day:
                    schedules.append(ParsedSchedule(subject, day, start_time, end_time, location, notes))
            
            return schedules
        except Exception as e:
            print(f"Error parsing Excel: {e}")
            return []
    
    @staticmethod
    def parse_text(text: str) -> List[ParsedSchedule]:
        """Parse raw text to extract schedule"""
        schedules = []
        lines = text.split('\n')
        
        for line in lines:
            if not line.strip():
                continue
            
            # Pattern: "Toán ngày 15/1 phòng 201 8am-10am"
            # Môn học + ngày + phòng + giờ
            parsed = InputParser._parse_line(line.strip())
            if parsed:
                schedules.append(parsed)
        
        return schedules
    
    @staticmethod
    def _parse_line(line: str) -> Optional[ParsedSchedule]:
        """Parse single line"""
        try:
            # Subject
            subject_match = re.search(r'^([A-Za-z0-9ÀÁẢẤẦẼẾ\s]+?)(?:\s+(?:ngày|on|dạy|lớp))', line, re.IGNORECASE)
            subject = subject_match.group(1).strip() if subject_match else ""
            
            # Date
            date_match = re.search(r'(?:ngày|on)?\s*(\d{1,2})/(\d{1,2})(?:/(\d{4}))?', line)
            day = f"{date_match.group(1)}/{date_match.group(2)}" if date_match else ""
            
            # Location
            location_match = re.search(r'(?:phòng|room|p\.?)\s*([A-Z0-9]+)', line, re.IGNORECASE)
            location = location_match.group(1) if location_match else ""
            
            # Time
            time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(?:am|pm|h)?\s*-\s*(\d{1,2}):?(\d{2})?\s*(?:am|pm|h)?', line, re.IGNORECASE)
            start_time = f"{time_match.group(1)}:{time_match.group(2) or '00'}" if time_match else ""
            end_time = f"{time_match.group(3)}:{time_match.group(4) or '00'}" if time_match else ""
            
            if subject and day:
                return ParsedSchedule(subject, day, start_time, end_time, location)
            
            return None
        except:
            return None
    
    @staticmethod
    def parse_image(image_path: str) -> str:
        """Parse image using OCR"""
        try:
            from PIL import Image
            import pytesseract
            
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img, lang='vie+eng')
            return text
        except Exception as e:
            print(f"Error parsing image: {e}")
            return ""

class PriorityEngine:
    """Classify notification priority"""
    
    CRITICAL_KEYWORDS = [
        "phòng", "room", "thay đổi", "change", "thi", "exam", "kiểm tra", "test"
    ]
    
    HIGH_KEYWORDS = [
        "nộp", "submit", "deadline", "hạn chót", "phải", "must", "deadline"
    ]
    
    LOW_KEYWORDS = [
        "ghi chú", "note", "thông báo", "notice", "nhắc nhở", "reminder"
    ]
    
    @staticmethod
    def classify(event: Dict[str, Any]) -> Priority:
        """Classify event priority"""
        score = 0
        text = (event.get('subject', '') + ' ' + event.get('notes', '')).lower()
        
        # Check critical keywords
        for keyword in PriorityEngine.CRITICAL_KEYWORDS:
            if keyword in text:
                score += 10
        
        # Check high keywords
        for keyword in PriorityEngine.HIGH_KEYWORDS:
            if keyword in text:
                score += 5
        
        # Check low keywords
        for keyword in PriorityEngine.LOW_KEYWORDS:
            if keyword in text:
                score -= 3
        
        # Determine priority
        if score >= 10:
            return Priority.CRITICAL
        elif score >= 5:
            return Priority.HIGH
        elif score >= 0:
            return Priority.NORMAL
        else:
            return Priority.LOW

class SchedulerAssistant:
    """Suggest free time slots"""
    
    @staticmethod
    def find_free_slots(user_schedules: List[Dict], date: str, 
                       duration_minutes: int = 60) -> List[Dict[str, str]]:
        """Find free time slots for given date"""
        
        # Create busy times from schedules
        busy_times = []
        for schedule in user_schedules:
            if schedule.get('day') == date:
                start = SchedulerAssistant._time_to_minutes(schedule.get('start_time', ''))
                end = SchedulerAssistant._time_to_minutes(schedule.get('end_time', ''))
                if start and end:
                    busy_times.append((start, end))
        
        # Sort busy times
        busy_times.sort()
        
        # Find free slots
        free_slots = []
        current_time = 8 * 60  # 8am
        end_time = 18 * 60     # 6pm
        
        for start, end in busy_times:
            if current_time < start:
                free_slots.append({
                    "start": SchedulerAssistant._minutes_to_time(current_time),
                    "end": SchedulerAssistant._minutes_to_time(start),
                    "duration_minutes": start - current_time
                })
            current_time = max(current_time, end)
        
        # Last slot
        if current_time < end_time:
            free_slots.append({
                "start": SchedulerAssistant._minutes_to_time(current_time),
                "end": SchedulerAssistant._minutes_to_time(end_time),
                "duration_minutes": end_time - current_time
            })
        
        # Filter by minimum duration
        return [slot for slot in free_slots if slot['duration_minutes'] >= duration_minutes]
    
    @staticmethod
    def _time_to_minutes(time_str: str) -> Optional[int]:
        """Convert "HH:MM" to minutes"""
        try:
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1]) if len(parts) > 1 else 0
            return hours * 60 + minutes
        except:
            return None
    
    @staticmethod
    def _minutes_to_time(minutes: int) -> str:
        """Convert minutes to "HH:MM" """
        hours = minutes // 60
        mins = minutes % 60
        return f"{hours:02d}:{mins:02d}"
