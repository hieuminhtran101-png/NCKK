from app.core.database import user_collection
import os

def get_telegram_status(student_id: str):
    user = user_collection.find_one({"student_id": student_id})
    if not user:
        return None

    if user.get("is_telegram_linked"):
        return {
            "is_telegram_linked": True,
            "telegram_link": None
        }

    bot_username = os.getenv("TELEGRAM_BOT_USERNAME")
    return {
        "is_telegram_linked": False,
        "telegram_link": f"https://t.me/{bot_username}?start={student_id}"
    }

def link_telegram(student_id: str, chat_id: str):
    user = user_collection.find_one({"student_id": student_id})
    if not user:
        return False

    user_collection.update_one(
        {"student_id": student_id},
        {"$set": {
            "telegram_chat_id": chat_id,
            "is_telegram_linked": True
        }}
    )
    return True

def unlink_telegram(student_id: str):
    user = user_collection.find_one({"student_id": student_id})
    if not user:
        return False

    user_collection.update_one(
        {"student_id": student_id},
        {"$set": {
            "telegram_chat_id": None,
            "is_telegram_linked": False
        }}
    )
    return True