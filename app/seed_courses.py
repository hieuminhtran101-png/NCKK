# scripts/seed_courses.py
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from app.service.gpa_service import seed_courses

CNTT_COURSES = [
    # ── Đại cương ──────────────────────────────────────────────────
    {"course_code": "MATH101",   "course_name": "Toán giải tích",                          "credits": 3},
    {"course_code": "MATH101R",  "course_name": "Toán giải tích (học lại)",                "credits": 3},
    {"course_code": "MATH102",   "course_name": "Đại số tuyến tính",                       "credits": 2},
    {"course_code": "MATH201",   "course_name": "Xác suất thống kê",                       "credits": 4},
    {"course_code": "POLI101",   "course_name": "Triết học Mác-Lênin",                     "credits": 3},
    {"course_code": "POLI102",   "course_name": "Kinh tế chính trị",                       "credits": 2},
    {"course_code": "POLI103",   "course_name": "CNXH khoa học",                           "credits": 2},
    {"course_code": "POLI104",   "course_name": "Lịch sử Đảng",                            "credits": 2},
    {"course_code": "POLI105",   "course_name": "Tư tưởng Hồ Chí Minh",                   "credits": 2},
    {"course_code": "LAW101",    "course_name": "Pháp luật đại cương",                     "credits": 3},

    # ── Ngoại ngữ ──────────────────────────────────────────────────
    {"course_code": "ENGL101",   "course_name": "Tiếng Anh P1",                            "credits": 4},
    {"course_code": "ENGL102",   "course_name": "Tiếng Anh P2",                            "credits": 4},
    {"course_code": "ENGL103",   "course_name": "Tiếng Anh P3",                            "credits": 4},
    {"course_code": "ENGL104",   "course_name": "Tiếng Anh P4",                            "credits": 3},
    {"course_code": "ENGL105",   "course_name": "Tiếng Anh P5",                            "credits": 2},

    # ── Thể chất / QPAN ────────────────────────────────────────────
    {"course_code": "GDTC101",   "course_name": "GDTC 1",                                  "credits": 1},
    {"course_code": "ZUMBA101",  "course_name": "Zumba cơ bản",                            "credits": 1},
    {"course_code": "ZUMBA201",  "course_name": "Zumba nâng cao",                          "credits": 1},
    {"course_code": "SKILL101",  "course_name": "Kỹ năng mềm cơ bản",                     "credits": 3},
    {"course_code": "SKILL201",  "course_name": "Kỹ năng mềm nâng cao",                   "credits": 3},
    {"course_code": "QPAN101",   "course_name": "QPAN 1",                                  "credits": 3},
    {"course_code": "QPAN102",   "course_name": "QPAN 2",                                  "credits": 2},
    {"course_code": "QPAN103",   "course_name": "QPAN 3",                                  "credits": 2},
    {"course_code": "QPAN104",   "course_name": "QPAN 4",                                  "credits": 4},

    # ── Cơ sở ngành ────────────────────────────────────────────────
    {"course_code": "CS101",     "course_name": "Nhập môn CNTT",                           "credits": 3},
    {"course_code": "CS102",     "course_name": "Lập trình cơ bản",                        "credits": 3},
    {"course_code": "CS103",     "course_name": "Lập trình hướng đối tượng",               "credits": 3},
    {"course_code": "CS201",     "course_name": "Cấu trúc dữ liệu & giải thuật",          "credits": 3},
    {"course_code": "CS202",     "course_name": "Toán rời rạc",                            "credits": 3},
    {"course_code": "CS203",     "course_name": "Mạng máy tính",                           "credits": 2},
    {"course_code": "CS301",     "course_name": "Cơ sở dữ liệu",                          "credits": 3},
    {"course_code": "CS302",     "course_name": "Phân tích thiết kế HTTT",                "credits": 3},
    {"course_code": "CS303",     "course_name": "Công nghệ phần mềm",                     "credits": 3},

    # ── Chuyên ngành ───────────────────────────────────────────────
    {"course_code": "WEB101",    "course_name": "Lập trình mạng",                          "credits": 3},
    {"course_code": "MOB101",    "course_name": "Lập trình mobile",                        "credits": 3},
    {"course_code": "AI101",     "course_name": "Trí tuệ nhân tạo",                       "credits": 2},
    {"course_code": "AI201",     "course_name": "Học máy",                                 "credits": 2},
    {"course_code": "SEC101",    "course_name": "An toàn bảo mật thông tin",              "credits": 2},
    {"course_code": "DATA101",   "course_name": "Công nghệ dữ liệu",                      "credits": 2},
    {"course_code": "DATA201",   "course_name": "Dữ liệu lớn",                            "credits": 2},
    {"course_code": "IOT101",    "course_name": "Lập trình IoT",                           "credits": 2},
    {"course_code": "IMG101",    "course_name": "Xử lý ảnh",                              "credits": 2},
    {"course_code": "GIS101",    "course_name": "Hệ thống thông tin địa lý",             "credits": 2},
    {"course_code": "BCK101",    "course_name": "Blockchain",                              "credits": 2},
    {"course_code": "SCT101",    "course_name": "Smart city / nông nghiệp",               "credits": 2},
    {"course_code": "DIG101",    "course_name": "Chuyển đổi số",                          "credits": 2},
    {"course_code": "BIZ101",    "course_name": "Ứng dụng CNTT trong doanh nghiệp",      "credits": 3},
    {"course_code": "PM101",     "course_name": "Quản trị dự án CNTT",                   "credits": 2},
    {"course_code": "QA101",     "course_name": "Kiểm thử phần mềm",                     "credits": 2},

    # ── Thực tập / Đồ án ───────────────────────────────────────────
    {"course_code": "INT101",    "course_name": "Thực tập CNTT 1",                        "credits": 4},
    {"course_code": "INT102",    "course_name": "Thực tập CNTT 2",                        "credits": 4},
    {"course_code": "INT103",    "course_name": "Thực tập CNTT 3 (Front-End)",            "credits": 4},
    {"course_code": "INT104",    "course_name": "Thực tập CNTT 4 (Back-End)",             "credits": 4},
    {"course_code": "INT105",    "course_name": "Thực tập CNTT 5",                        "credits": 4},
    {"course_code": "INT106",    "course_name": "Thực tập CNTT 6",                        "credits": 4},
    {"course_code": "INT107",    "course_name": "Thực tập CNTT 7",                        "credits": 4},
    {"course_code": "INT401",    "course_name": "Thực tập tốt nghiệp",                   "credits": 4},
]

if __name__ == "__main__":
    inserted = seed_courses(CNTT_COURSES)
    total_credits = sum(c["credits"] for c in CNTT_COURSES)
    print(f"✅ Đã seed {inserted} môn học mới vào MongoDB.")
    print(f"📚 Tổng số môn: {len(CNTT_COURSES)} | Tổng tín chỉ: {total_credits} TC")