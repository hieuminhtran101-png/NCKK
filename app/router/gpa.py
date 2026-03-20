# app/router/gpa.py
from fastapi import APIRouter, Header, HTTPException
from app.schemas.gpa import (
    StudentCourseCreate, GradeConfirmRequest,
    SetTargetRequest, CourseCreate, GpaSummary,
)
from app.service.gpa_service import (
    add_grade, get_grades, delete_grade,
    get_gpa_summary, set_target_gpa,
    seed_courses, get_transcript, get_pending_courses,
)

router = APIRouter(prefix="/api/gpa", tags=["GPA"])


# ── Seed ────────────────────────────────────────────────────────────
@router.post("/courses/seed")
def seed_course_list(courses: list[CourseCreate]):
    inserted = seed_courses([c.model_dump() for c in courses])
    return {"message": f"Đã thêm {inserted} môn mới"}


# ── Transcript (trang kết quả học tập) ──────────────────────────────
@router.get("/transcript")
def transcript(student_id: str = Header()):
    """
    Trả về toàn bộ danh sách môn (courses làm khung).
    Môn đã học: có điểm, letter, semester.
    Môn chưa học: score_10/letter = null.
    FE dùng endpoint này để render bảng giống trang trường.
    """
    data = get_transcript(student_id)
    done    = [d for d in data if d["done"]]
    pending = [d for d in data if not d["done"]]
    return {
        "total_courses":  len(data),
        "done_count":     len(done),
        "pending_count":  len(pending),
        "data":           data,
    }


# ── Pending courses (môn chưa học) ──────────────────────────────────
@router.get("/courses/pending")
def pending_courses(student_id: str = Header(), limit: int = 10):
    """Top N môn chưa học, sort tín chỉ giảm dần. Dùng cho AI gợi ý."""
    data = get_pending_courses(student_id, limit=limit)
    return {"count": len(data), "data": data}


# ── Grades CRUD ──────────────────────────────────────────────────────
@router.post("/grades")
def add_student_grade(data: StudentCourseCreate, student_id: str = Header()):
    result = add_grade(student_id, data)
    if not result:
        raise HTTPException(status_code=404, detail="Môn học không tồn tại")
    return {"message": "Nhập điểm thành công", "data": result}


@router.get("/grades")
def list_grades(student_id: str = Header(), semester: str = None):
    return {"data": get_grades(student_id, semester)}


@router.delete("/grades/{grade_id}")
def remove_grade(grade_id: str, student_id: str = Header()):
    if not delete_grade(student_id, grade_id):
        raise HTTPException(status_code=404, detail="Không tìm thấy bản ghi điểm")
    return {"message": "Đã xoá điểm và cập nhật GPA"}


# ── GPA Summary ─────────────────────────────────────────────────────
@router.get("/summary", response_model=GpaSummary)
def gpa_summary(student_id: str = Header()):
    summary = get_gpa_summary(student_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")
    return summary


# ── Target GPA ──────────────────────────────────────────────────────
@router.patch("/target")
def update_target_gpa(data: SetTargetRequest, student_id: str = Header()):
    if data.target_gpa is None and data.preset is None:
        raise HTTPException(status_code=400, detail="Cần truyền target_gpa hoặc preset")
    result = set_target_gpa(student_id, data.target_gpa, data.preset)
    if result is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")
    return {"message": f"Đã set mục tiêu GPA: {result}", "target_gpa": result}


# ── Confirm từ chat ──────────────────────────────────────────────────
@router.post("/grades/confirm")
def confirm_grade_from_chat(data: GradeConfirmRequest):
    result = add_grade(data.student_id, StudentCourseCreate(
        course_code=data.course_code,
        score_10=data.score_10,
        semester=data.semester
    ))
    if not result:
        raise HTTPException(status_code=404, detail="Môn học không tồn tại")
    return {"message": "Đã lưu điểm thành công", "data": result}