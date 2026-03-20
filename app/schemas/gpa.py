# app/schemas/gpa.py
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class LetterGrade(str, Enum):
    A_PLUS = "A+"; A = "A"; B_PLUS = "B+"; B = "B"
    C_PLUS = "C+"; C = "C"; D_PLUS = "D+"; D = "D"; F = "F"


class GpaPreset(str, Enum):
    AVERAGE   = "trung_binh"   # 2.0
    GOOD      = "kha"          # 2.5
    VERY_GOOD = "gioi"         # 3.2
    EXCELLENT = "xuat_sac"     # 3.6


# ── Course (seed) ────────────────────────────────
class CourseCreate(BaseModel):
    course_code: str
    course_name: str
    credits: int
    # ✅ bỏ major_code và group — không cần thiết


# ── Student course (điểm) ────────────────────────
class StudentCourseCreate(BaseModel):
    course_code: str
    score_10: float = Field(..., ge=0, le=10)
    semester: str


class StudentCourseUpdate(BaseModel):
    score_10: Optional[float] = Field(None, ge=0, le=10)
    semester: Optional[str]   = None


# ── GPA Summary ──────────────────────────────────
class GpaSummary(BaseModel):
    current_gpa: float
    total_credits_completed: int
    total_credits_required: int
    remaining_credits: int
    target_gpa: float
    needed_avg_for_target: Optional[float]
    progress_percent: float


# ── Target ───────────────────────────────────────
class SetTargetRequest(BaseModel):
    target_gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    preset: Optional[GpaPreset] = None


# ── Chat confirm ─────────────────────────────────
class GradeConfirmRequest(BaseModel):
    student_id: str
    course_code: str
    score_10: float
    semester: str