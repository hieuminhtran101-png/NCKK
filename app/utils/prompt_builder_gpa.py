# app/utils/prompt_builder_gpa.py

def build_gpa_section(gpa_context: dict) -> str:
    summary  = gpa_context.get("summary", {})
    weak     = gpa_context.get("weak_courses", [])
    pending  = gpa_context.get("pending_courses", [])

    current_gpa = summary.get("current_gpa", 0)
    target_gpa  = summary.get("target_gpa", 2.5)
    completed   = summary.get("total_credits_completed", 0)
    remaining   = summary.get("remaining_credits", 0)
    needed      = summary.get("needed_avg_for_target")
    progress    = summary.get("progress_percent", 0)
    total_req   = summary.get("total_credits_required", 156)

    status_line = (
        f"Dang DAT muc tieu GPA ({current_gpa} >= {target_gpa})"
        if current_gpa >= target_gpa
        else f"Dang THAP HON muc tieu {round(target_gpa - current_gpa, 2)} diem"
    )

    weak_text = ""
    if weak:
        weak_text = "Mon can cai thien (diem < 2.0):\n"
        for w in weak[:5]:
            weak_text += f"  - {w.get('course_name','?')} ({w.get('course_code')}): {w.get('letter')} | {w.get('credits')} TC\n"

    pending_text = ""
    if pending:
        pending_text = "Mon chua hoc (tin chi cao nhat):\n"
        for p in pending[:5]:
            pending_text += f"  - {p['course_name']} ({p['course_code']}): {p['credits']} TC\n"

    needed_line = (
        f"De dat muc tieu -> can TB {needed}/4.0 cho {remaining} TC con lai"
        if needed is not None
        else ("Da hoan thanh du tin chi!" if remaining == 0 else "GPA hien tai da du dat muc tieu")
    )

    return f"""
=== THONG TIN GPA SINH VIEN ===
GPA hien tai      : {current_gpa}/4.0
Muc tieu GPA     : {target_gpa}/4.0
Tin chi hoan thanh: {completed}/{total_req} TC ({progress}%)
Tin chi con lai   : {remaining} TC
Trang thai        : {status_line}
{needed_line}

{weak_text}
{pending_text}
================================""".strip()


def build_gpa_actions_section(pending_courses: list = None, all_courses: list = None) -> str:
    course_lookup = ""
    if all_courses:
        course_lookup = "\nBANG TRA TAT CA MA MON (dung khi add_grade hoac tim mon):\n"
        for c in all_courses:
            course_lookup += f'  "{c["course_name"]}" -> course_code: "{c["course_code"]}"\n'
    elif pending_courses:
        course_lookup = "\nBANG TRA MA MON (bat buoc dung khi add_grade):\n"
        for c in pending_courses:
            course_lookup += f'  "{c["course_name"]}" -> course_code: "{c["course_code"]}"\n'

    return f"""
[GPA ACTIONS]
- "add_grade"       -> nhap diem mon hoc (cho xac nhan)
- "get_grades"      -> xem bang diem
- "get_gpa_summary" -> xem GPA, tien do, diem can dat
- "set_target_gpa"  -> dat muc tieu GPA
- "delete_grade"    -> xoa 1 ban ghi diem
- "gpa_advice"      -> AI tu van GPA

PARAMS:
add_grade:
  {{ "course_code": "CS202", "score_10": 7.5, "semester": "2024.2" }}
  WARNING: course_code PHAI la MA MON - tra BANG TRA ben duoi
  WARNING: KHONG duoc dung ten mon nhu "Toan roi rac" lam course_code
  WARNING: Khong tim thay ma mon -> action="answer", hoi lai sinh vien
  WARNING: KHONG tu luu - reply BAT BUOC hoi: "Ban co muon luu diem nay khong?"

get_grades:      {{ "semester": "2024.2" }} hoac {{}} cho tat ca
get_gpa_summary: {{}}
set_target_gpa:  {{ "target_gpa": 3.2 }} hoac {{ "preset": "gioi" }}
delete_grade:    {{ "grade_id": "..." }}
gpa_advice:      {{}}
{course_lookup}
PRESET: trung_binh=2.0 | kha=2.5 | gioi=3.2 | xuat_sac=3.6
"""

# ==============================================================
# PATCH ai_service.py — dòng 180, sửa 1 dòng duy nhất:
#
# CŨ:
#   gpa_actions = build_gpa_actions_section(
#       pending_courses=gpa_context.get("pending_courses", [])
#   )
#
# MỚI:
#   gpa_actions = build_gpa_actions_section(
#       pending_courses=gpa_context.get("pending_courses", []),
#       all_courses=gpa_context.get("all_courses", [])
#   )
#
# Lý do: truyền danh sách tất cả môn học vào để AI
# có bảng tra mã môn ngay trong prompt → không hallucinate tên môn
# ==============================================================