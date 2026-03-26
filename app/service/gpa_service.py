# app/service/gpa_service.py  — thêm các hàm mới, giữ nguyên các hàm cũ

from app.core.database import db
from app.schemas.gpa import StudentCourseCreate, GpaSummary, GpaPreset
from app.utils.mongo import mongo_to_dict
from datetime import datetime, timezone
from bson import ObjectId
from typing import Optional
import asyncio

course_collection         = db["courses"]
student_course_collection = db["student_courses"]
user_collection           = db["users"]

GRADE_TABLE = [
    (9.0, "A+", 4.0),
    (8.5, "A",  3.7),
    (8.0, "B+", 3.5),
    (7.0, "B",  3.0),
    (6.5, "C+", 2.5),
    (5.5, "C",  2.0),
    (5.0, "D+", 1.5),
    (4.0, "D",  1.0),
    (0.0, "F",  0.0),
]

GPA_PRESETS = {
    GpaPreset.AVERAGE:   2.0,
    GpaPreset.GOOD:      2.5,
    GpaPreset.VERY_GOOD: 3.2,
    GpaPreset.EXCELLENT: 3.6,
}

TOTAL_CREDITS_REQUIRED = 156


# ─────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────

def _convert_score(score_10: float) -> tuple[str, float]:
    for threshold, letter, score_4 in GRADE_TABLE:
        if score_10 >= threshold:
            return letter, score_4
    return "F", 0.0


def _get_course(course_code: str) -> Optional[dict]:
    return course_collection.find_one({"course_code": course_code})


def _recalc_gpa(student_id: str) -> dict:
    """Tính lại GPA. Môn học lại → lấy điểm cao nhất."""
    all_records = list(student_course_collection.find({"student_id": student_id}))

    best: dict[str, dict] = {}
    for rec in all_records:
        code = rec["course_code"]
        if code not in best or rec["score_4"] > best[code]["score_4"]:
            best[code] = rec

    total_weighted = 0.0
    total_credits  = 0
    all_credits    = 0

    for rec in best.values():
        course = _get_course(rec["course_code"])
        if not course:
            continue
        credits = course["credits"]
        all_credits += credits
        if rec["score_4"] > 0:
            total_credits += credits
        total_weighted += rec["score_4"] * credits

    gpa = round(total_weighted / all_credits, 2) if all_credits > 0 else 0.0
    return {"current_gpa": gpa, "total_credits_completed": total_credits}


# ─────────────────────────────────────────
# Seed
# ─────────────────────────────────────────

def seed_courses(courses: list) -> int:
    inserted = 0
    for c in courses:
        if not course_collection.find_one({"course_code": c["course_code"]}):
            course_collection.insert_one(c)
            inserted += 1
    return inserted


# ─────────────────────────────────────────
# Transcript — JOIN courses + student_courses
# Đây là hàm chính cho trang "Kết quả học tập"
# ─────────────────────────────────────────

def get_transcript(student_id: str) -> list:
    """
    Trả về toàn bộ danh sách môn học (courses làm khung).
    Môn đã có điểm → merge data từ student_courses vào.
    Môn chưa học   → score_10/score_4/letter = None.
    Kết quả sort theo: đã học trước, chưa học sau.
    """
    all_courses = list(course_collection.find({}))

    # Build lookup: course_code → bản ghi điểm tốt nhất
    all_records = list(student_course_collection.find({"student_id": student_id}))
    best_grade: dict[str, dict] = {}
    for rec in all_records:
        code = rec["course_code"]
        if code not in best_grade or rec["score_4"] > best_grade[code]["score_4"]:
            best_grade[code] = rec

    result = []
    for course in all_courses:
        c = mongo_to_dict(course)
        grade = best_grade.get(c["course_code"])
        if grade:
            c["score_10"] = grade["score_10"]
            c["score_4"]  = grade["score_4"]
            c["letter"]   = grade["letter"]
            c["semester"] = grade["semester"]
            c["grade_id"] = grade.get("id") or str(grade.get("_id", ""))
            c["done"]     = True
        else:
            c["score_10"] = None
            c["score_4"]  = None
            c["letter"]   = None
            c["semester"] = None
            c["grade_id"] = None
            c["done"]     = False
        result.append(c)

    # Đã học trước, chưa học sau
    result.sort(key=lambda x: (not x["done"]))
    return result


def get_pending_courses(student_id: str, limit: int = 10) -> list:
    """Chỉ lấy môn chưa có điểm, sort tín chỉ giảm dần."""
    transcript = get_transcript(student_id)
    pending = [c for c in transcript if not c["done"]]
    pending.sort(key=lambda x: x["credits"], reverse=True)
    return pending[:limit]


# ─────────────────────────────────────────
# Grade CRUD
# ─────────────────────────────────────────

def add_grade(student_id: str, data: StudentCourseCreate) -> Optional[dict]:
    course = _get_course(data.course_code)
    if not course:
        return None
 
    letter, score_4 = _convert_score(data.score_10)
    now = datetime.now(timezone.utc)
 
    user_before = user_collection.find_one({"student_id": student_id})
    gpa_before  = user_before.get("current_gpa", 0.0) if user_before else 0.0
 
    existing = student_course_collection.find_one({
        "student_id":  student_id,
        "course_code": data.course_code,
        "semester":    data.semester
    })
 
    if existing:
        student_course_collection.update_one(
            {"_id": existing["_id"]},
            {"$set": {"score_10": data.score_10, "score_4": score_4,
                      "letter": letter, "updated_at": now}}
        )
        doc = student_course_collection.find_one({"_id": existing["_id"]})
    else:
        doc = {
            "student_id":  student_id,
            "course_code": data.course_code,
            "score_10":    data.score_10,
            "score_4":     score_4,
            "letter":      letter,
            "semester":    data.semester,
            "updated_at":  now
        }
        result = student_course_collection.insert_one(doc)
        doc["_id"] = result.inserted_id
 
    # Tính lại GPA
    stats     = _recalc_gpa(student_id)
    gpa_after = stats["current_gpa"]
 
    user_collection.update_one(
        {"student_id": student_id},
        {"$set": {
            "current_gpa":             gpa_after,
            "total_credits_completed": stats["total_credits_completed"]
        }}
    )
 
    # Luôn notify sau mỗi lần nhập/sửa điểm thành công
    print(f"[DEBUG] add_grade done: student_id={student_id}, gpa_before={gpa_before}, gpa_after={gpa_after}")
    from app.service.gpa_notification_service import notify_grade_saved

    coro = notify_grade_saved(
        student_id=student_id,
        course_name=course.get("course_name", data.course_code),
        score_10=data.score_10,
        gpa_before=gpa_before,
        gpa_after=gpa_after,
    )

    try:
        loop = asyncio.get_running_loop()
        if loop.is_running():
            asyncio.create_task(coro)
    except RuntimeError:
        try:
            asyncio.run(coro)
        except Exception as e:
            print(f"[notify_grade_saved] failed: {e}")
 
    return mongo_to_dict(doc)


def get_grades(student_id: str, semester: Optional[str] = None) -> list:
    query = {"student_id": student_id}
    if semester:
        query["semester"] = semester
    records = list(student_course_collection.find(query))
    result = []
    for rec in records:
        d = mongo_to_dict(rec)
        course = _get_course(d["course_code"])
        if course:
            d["course_name"] = course["course_name"]
            d["credits"]     = course["credits"]
        d["updated_at"] = str(d.get("updated_at", ""))
        result.append(d)
    return result


def delete_grade(student_id: str, grade_id: str) -> bool:
    result = student_course_collection.delete_one({
        "_id":        ObjectId(grade_id),
        "student_id": student_id
    })
    if result.deleted_count:
        stats = _recalc_gpa(student_id)
        user_collection.update_one(
            {"student_id": student_id},
            {"$set": {
                "current_gpa":             stats["current_gpa"],
                "total_credits_completed": stats["total_credits_completed"]
            }}
        )
        return True
    return False


# ─────────────────────────────────────────
# GPA Summary + Target
# ─────────────────────────────────────────

def get_gpa_summary(student_id: str) -> Optional[GpaSummary]:
    user = user_collection.find_one({"student_id": student_id})
    if not user:
        return None

    current_gpa = user.get("current_gpa", 0.0)
    completed   = user.get("total_credits_completed", 0)
    target_gpa  = user.get("target_gpa", 2.5)
    remaining   = max(TOTAL_CREDITS_REQUIRED - completed, 0)
    progress    = round(completed / TOTAL_CREDITS_REQUIRED * 100, 1)

    needed = None
    if remaining > 0:
        needed_raw = (
            target_gpa * TOTAL_CREDITS_REQUIRED
            - current_gpa * completed
        ) / remaining
        needed = round(needed_raw, 2)
        if needed <= current_gpa:
            needed = None

    return GpaSummary(
        current_gpa=current_gpa,
        total_credits_completed=completed,
        total_credits_required=TOTAL_CREDITS_REQUIRED,
        remaining_credits=remaining,
        target_gpa=target_gpa,
        needed_avg_for_target=needed,
        progress_percent=progress
    )


def set_target_gpa(student_id: str, target_gpa: Optional[float] = None,
                   preset: Optional[GpaPreset] = None) -> Optional[float]:
    user = user_collection.find_one({"student_id": student_id})
    if not user:
        return None
    if target_gpa is not None:
        final_target = round(target_gpa, 2)
    elif preset:
        final_target = GPA_PRESETS[preset]
    else:
        return None
    user_collection.update_one(
        {"student_id": student_id},
        {"$set": {"target_gpa": final_target}}
    )
    return final_target


# ─────────────────────────────────────────
# AI context — KHÔNG dump hết 57 môn
# ─────────────────────────────────────────

def get_gpa_context_for_ai(student_id: str) -> dict:
    summary = get_gpa_summary(student_id)
    grades  = get_grades(student_id)
    weak    = [g for g in grades if g.get("score_4", 0) < 2.0]

    # Chỉ top 8 môn chưa học, tín chỉ cao nhất — AI không cần biết hết
    pending = get_pending_courses(student_id, limit=8)

    # Thêm danh sách tất cả môn học để AI có thể ánh xạ tên môn
    all_courses = list(course_collection.find({}, {"course_name": 1, "course_code": 1, "_id": 0}))

    return {
        "summary":         summary.model_dump() if summary else {},
        "grades":          grades,
        "weak_courses":    weak,
        "pending_courses": pending,
        "all_courses":     all_courses,  # Thêm này
    }