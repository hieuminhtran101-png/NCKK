# app/service/gpa_notification_service.py
from telegram import Bot
from datetime import datetime, timezone
from app.core.database import user_collection, student_course_collection
from app.service.gpa_service import get_gpa_summary, get_gpa_context_for_ai
import os

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))


# ─────────────────────────────────────────
# Helper: xếp loại + lời khen/chê
# ─────────────────────────────────────────
def _rank(gpa: float) -> tuple[str, str]:
    """Trả về (xếp loại, emoji)."""
    if gpa >= 3.6: return "Xuất sắc",  "🏆"
    if gpa >= 3.2: return "Giỏi",      "🌟"
    if gpa >= 2.5: return "Khá",       "👍"
    if gpa >= 2.0: return "Trung bình","📊"
    return "Yếu", "⚠️"

def _praise_or_warn(current: float, target: float, needed, remaining: int, weak_courses: list) -> str:
    """Tạo đoạn động viên hoặc cảnh báo tuỳ theo GPA."""
    rank_name, rank_emoji = _rank(current)

    # ── GPA ĐẠT hoặc VƯỢT mục tiêu → KHEN ──────────────────────────
    if current >= target:
        if current >= 3.6:
            praise = "🎉 Xuất sắc! Bạn đang dẫn đầu — duy trì phong độ này thật tuyệt vời!"
        elif current >= 3.2:
            praise = "🌟 Giỏi lắm! GPA của bạn rất ấn tượng. Tiếp tục phát huy nhé!"
        elif current >= 2.5:
            praise = "👍 Tốt lắm! Bạn đang đạt mục tiêu — hãy tiếp tục cố gắng!"
        else:
            praise = "✅ Bạn đã đạt mục tiêu GPA! Đừng để tuột nhé."
        return praise

    # ── GPA CHƯA ĐẠT → CẢNH BÁO + CHỈ SỐ CỤ THỂ ───────────────────
    gap = round(target - current, 2)

    if needed is None:
        return f"⚠️ Còn thiếu {gap} điểm so với mục tiêu. Hãy cố gắng hơn nhé!"

    if needed > 4.0:
        warn = (
            f"🚨 GPA còn thiếu *{gap} điểm* so với mục tiêu.\n"
            f"Với {remaining} TC còn lại, điểm TB cần đạt là *{needed}/4.0* — vượt quá giới hạn!\n"
            f"💡 Hãy cân nhắc *học lại các môn điểm thấp* để cải thiện GPA."
        )
    else:
        # Tính điểm thang 10 tương đương needed/4.0
        # Quy đổi ngược: 4.0→10, 3.6→9, 3.2→8, 2.5→6.5, 2.0→5
        score_10 = round(needed * 10 / 4, 1)
        warn = (
            f"💪 Còn thiếu *{gap} điểm* GPA.\n"
            f"Cần đạt TB *{needed}/4.0* (≈ *{score_10}/10*) cho *{remaining} TC* còn lại.\n"
        )
        if weak_courses:
            warn += "🔴 Môn nên ưu tiên cải thiện:\n"
            for w in weak_courses[:3]:
                warn += f"  • {w.get('course_name')} — hiện {w.get('letter')} ({w.get('credits')} TC)\n"

    return warn


# ─────────────────────────────────────────
# 1. Cảnh báo/khen GPA hàng tuần — thứ Hai 8:00
# ─────────────────────────────────────────
async def send_gpa_alerts():
    users = list(user_collection.find({"is_telegram_linked": True}))
    for user in users:
        student_id = user["student_id"]
        chat_id    = user.get("telegram_chat_id")
        if not chat_id:
            continue

        summary = get_gpa_summary(student_id)
        if not summary:
            continue

        current   = summary.current_gpa
        target    = summary.target_gpa
        needed    = summary.needed_avg_for_target
        remaining = summary.remaining_credits

        ctx          = get_gpa_context_for_ai(student_id)
        weak_courses = ctx.get("weak_courses", [])

        rank_name, rank_emoji = _rank(current)
        body = _praise_or_warn(current, target, needed, remaining, weak_courses)

        message = (
            f"📊 *Cập nhật GPA tuần này*\n\n"
            f"GPA hiện tại : *{current}/4.0* {rank_emoji} {rank_name}\n"
            f"Mục tiêu     : *{target}/4.0*\n"
            f"Tín chỉ còn  : *{remaining} TC*\n\n"
            f"{body}"
        )

        try:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        except Exception as e:
            print(f"[GPA Alert] Lỗi gửi {student_id}: {e}")


# ─────────────────────────────────────────
# 2. Nhắc ngay khi GPA tụt sau lần nhập điểm
# ─────────────────────────────────────────
async def notify_gpa_drop(student_id: str, gpa_before: float, gpa_after: float, course_name: str):
    if gpa_after > gpa_before:
        # GPA tăng → gửi khen
        await notify_gpa_rise(student_id, gpa_before, gpa_after, course_name)
        return

    if gpa_after == gpa_before:
        # GPA không đổi → không cần gửi báo động/khen
        return

    user = user_collection.find_one({"student_id": student_id})
    if not user or not user.get("is_telegram_linked"):
        return
    chat_id = user.get("telegram_chat_id")
    if not chat_id:
        return

    summary      = get_gpa_summary(student_id)
    ctx          = get_gpa_context_for_ai(student_id)
    weak_courses = ctx.get("weak_courses", [])

    drop      = round(gpa_before - gpa_after, 2)
    target    = summary.target_gpa    if summary else 0
    needed    = summary.needed_avg_for_target if summary else None
    remaining = summary.remaining_credits     if summary else 0

    body = _praise_or_warn(gpa_after, target, needed, remaining, weak_courses)

    message = (
        f"📉 *GPA vừa giảm sau khi nhập điểm*\n\n"
        f"📚 Môn vừa nhập : *{course_name}*\n"
        f"GPA trước       : *{gpa_before}/4.0*\n"
        f"GPA sau         : *{gpa_after}/4.0*\n"
        f"Giảm            : *{drop} điểm*\n"
        f"Mục tiêu        : *{target}/4.0*\n\n"
        f"{body}"
    )

    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
    except Exception as e:
        print(f"[GPA Drop] Lỗi gửi {student_id}: {e}")


# ─────────────────────────────────────────
# 3. Khen khi GPA tăng sau nhập điểm
# ─────────────────────────────────────────
async def notify_gpa_rise(student_id: str, gpa_before: float, gpa_after: float, course_name: str):
    user = user_collection.find_one({"student_id": student_id})
    if not user or not user.get("is_telegram_linked"):
        return
    chat_id = user.get("telegram_chat_id")
    if not chat_id:
        return

    summary      = get_gpa_summary(student_id)
    target       = summary.target_gpa if summary else 0
    rise         = round(gpa_after - gpa_before, 2)
    rank_name, rank_emoji = _rank(gpa_after)

    if gpa_after >= target:
        status = f"✅ Đã đạt mục tiêu *{target}/4.0*! Tuyệt vời!"
    else:
        gap    = round(target - gpa_after, 2)
        status = f"Còn *{gap} điểm* nữa là đạt mục tiêu {target}/4.0 — sắp tới rồi!"

    message = (
        f"📈 *GPA vừa tăng!*\n\n"
        f"📚 Môn vừa nhập : *{course_name}*\n"
        f"GPA trước       : *{gpa_before}/4.0*\n"
        f"GPA sau         : *{gpa_after}/4.0* {rank_emoji} {rank_name}\n"
        f"Tăng            : *+{rise} điểm*\n\n"
        f"{status}\n"
        f"💪 Tiếp tục phát huy nhé!"
    )

    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
    except Exception as e:
        print(f"[GPA Rise] Lỗi gửi {student_id}: {e}")


# ─────────────────────────────────────────
# 4. Báo cáo GPA tháng — ngày 1 hàng tháng
# ─────────────────────────────────────────
async def send_monthly_gpa_report():
    now   = datetime.now(timezone.utc)
    month = now.strftime("%m/%Y")

    users = list(user_collection.find({"is_telegram_linked": True}))

    for user in users:
        student_id = user["student_id"]
        chat_id    = user.get("telegram_chat_id")
        if not chat_id:
            continue

        summary = get_gpa_summary(student_id)
        if not summary:
            continue

        current   = summary.current_gpa
        target    = summary.target_gpa
        completed = summary.total_credits_completed
        total     = summary.total_credits_required
        remaining = summary.remaining_credits
        progress  = summary.progress_percent
        needed    = summary.needed_avg_for_target

        rank_name, rank_emoji = _rank(current)

        # Đếm môn nhập trong tháng
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_grades  = student_course_collection.count_documents({
            "student_id": student_id,
            "updated_at": {"$gte": month_start}
        })

        ctx          = get_gpa_context_for_ai(student_id)
        weak_courses = ctx.get("weak_courses", [])
        pending      = ctx.get("pending_courses", [])[:3]

        # Đoạn khen/chê
        body = _praise_or_warn(current, target, needed, remaining, weak_courses)

        # Gợi ý môn chưa học
        pending_lines = ""
        if pending:
            pending_lines = "\n🟡 *Môn tín chỉ cao chưa hoàn thành:*\n"
            for p in pending:
                pending_lines += f"  • {p['course_name']} ({p['credits']} TC)\n"
            pending_lines += "💡 Ưu tiên môn tín chỉ cao để cải thiện GPA hiệu quả nhất!"

        needed_str = (
            f"{needed}/4.0" if needed and needed <= 4.0
            else ("Không thể đạt ❌" if needed else "Đã đạt ✅")
        )

        message = (
            f"📋 *Báo cáo GPA tháng {month}*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📊 *GPA tích lũy* : *{current}/4.0* {rank_emoji} {rank_name}\n"
            f"🎯 Mục tiêu      : {target}/4.0\n"
            f"📚 Tín chỉ       : {completed}/{total} TC ({progress}%)\n"
            f"Còn lại          : {remaining} TC\n"
            f"Cần TB mỗi TC    : {needed_str}\n"
            f"🗓 Tháng này nhập: *{new_grades} môn*\n\n"
            f"{body}"
            f"{pending_lines}"
        )

        try:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        except Exception as e:
            print(f"[Monthly Report] Lỗi gửi {student_id}: {e}")