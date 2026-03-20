#app/core/database.py
from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["student_app"]

event_collection = db["events"]
user_collection = db["users"]
course_collection = db["courses"]          # ✅ thêm
student_course_collection = db["student_courses"]  # ✅ thêm

print("MONGO_URI:", MONGO_URI)
print("DB NAME:", db.name)
print("COLLECTIONS:", db.list_collection_names())