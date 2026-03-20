# app/service/gpa_notification_service.py

from telegram import Bot
from datetime import datetime, timezone
from app.core.database import user_collection, student_course_collection
from app.service.gpa_service import get_gpa_summary, get_gpa_context_for_ai
import os

bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))


# ─────────────────────────────────────────
# (CŨ) Cảnh báo GPA hàng tuần — thứ Hai 8:00
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

        if current >= target:
            continue

        gap = round(target - current, 2)

        if needed is not None and needed > 4.0:
            message = (
                f"🚨 *Cảnh báo GPA nghiêm trọng!*\n\n"
                f"📊 GPA hiện tại: *{current}/4.0*\n"
                f"🎯 Mục tiêu: *{target}/4.0*\n"
                f"❌ Với {remaining} TC còn lại, điểm cần đạt ({needed}/4.0) vượt quá tối đa!\n\n"
                f"💡 Hãy xem xét điều chỉnh mục tiêu hoặc đăng ký học lại các môn điểm thấp."
            )
        else:
            needed_str = f"{needed}/4.0" if needed else "đã đủ 🎉"
            message = (
                f"📊 *Cập nhật GPA tuần này*\n\n"
                f"GPA hiện tại : *{current}/4.0*\n"
                f"Mục tiêu     : *{target}/4.0*\n"
                f"Còn thiếu    : *{gap} điểm*\n"
                f"Tín chỉ còn  : *{remaining} TC*\n"
                f"Cần TB/TC    : *{needed_str}*\n\n"
                f"💪 Cố lên! Mỗi môn tốt là một bước gần mục tiêu hơn."
            )

        try:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        except Exception as e:
            print(f"[GPA Alert] Lỗi gửi Telegram {student_id}: {e}")


# ─────────────────────────────────────────
# (CŨ) Nhắc môn tín chỉ cao đầu tháng
# ─────────────────────────────────────────
async def send_weak_course_reminders():
    users = list(user_collection.find({"is_telegram_linked": True}))
    for user in users:
        student_id = user["student_id"]
        chat_id    = user.get("telegram_chat_id")
        if not chat_id:
            continue

        ctx     = get_gpa_context_for_ai(student_id)
        weak    = ctx.get("weak_courses", [])
        pending = ctx.get("pending_courses", [])[:3]

        if not weak and not pending:
            continue

        lines = ["📚 *Gợi ý học kỳ này từ MindBot:*\n"]
        if weak:
            lines.append("🔴 *Môn nên học lại để cải thiện GPA:*")
            for w in weak[:3]:
                lines.append(f"  • {w.get('course_name')} — {w.get('letter')} ({w.get('credits')} TC)")
        if pending:
            lines.append("\n🟡 *Môn tín chỉ cao chưa hoàn thành:*")
            for p in pending:
                lines.append(f"  • {p['course_name']} ({p['credits']} TC)")
        lines.append("\n💡 Ưu tiên các môn tín chỉ cao để cải thiện GPA hiệu quả nhất!")

        try:
            await bot.send_message(chat_id=chat_id, text="\n".join(lines), parse_mode="Markdown")
        except Exception as e:
            print(f"[Weak Reminder] Lỗi gửi Telegram {student_id}: {e}")


# ─────────────────────────────────────────
# (MỚI) Nhắc ngay khi GPA tụt sau lần nhập điểm
# Gọi trực tiếp từ gpa_service.add_grade()
# ─────────────────────────────────────────
async def notify_gpa_drop(student_id: str, gpa_before: float, gpa_after: float, course_name: str):
    """
    Được trigger ngay sau khi add_grade() nếu GPA tụt.
    gpa_before: GPA trước khi lưu điểm môn này
    gpa_after:  GPA sau khi tính lại
    course_name: tên môn vừa nhập để hiển thị trong thông báo
    """
    if gpa_after >= gpa_before:
        return  # GPA không tụt → không gửi

    user = user_collection.find_one({"student_id": student_id})
    if not user or not user.get("is_telegram_linked"):
        return

    chat_id = user.get("telegram_chat_id")
    if not chat_id:
        return

    summary   = get_gpa_summary(student_id)
    drop      = round(gpa_before - gpa_after, 2)
    target    = summary.target_gpa if summary else 0
    needed    = summary.needed_avg_for_target if summary else None
    remaining = summary.remaining_credits if summary else 0

    if needed and needed > 4.0:
        advice = f"⚠️ Cần >{needed}/4.0 cho {remaining} TC còn lại — vượt quá mức tối đa. Cân nhắc học lại môn điểm thấp!"
    elif needed:
        advice = f"📌 Cần trung bình *{needed}/4.0* cho {remaining} TC còn lại để đạt mục tiêu."
    else:
        advice = "✅ GPA vẫn đang đạt mục tiêu!"

    message = (
        f"📉 *GPA vừa giảm sau khi nhập điểm*\n\n"
        f"📚 Môn vừa nhập : *{course_name}*\n"
        f"GPA trước       : *{gpa_before}/4.0*\n"
        f"GPA sau         : *{gpa_after}/4.0*\n"
        f"Giảm            : *{drop} điểm*\n"
        f"Mục tiêu        : *{target}/4.0*\n\n"
        f"{advice}"
    )

    try:
        await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
    except Exception as e:
        print(f"[GPA Drop] Lỗi gửi Telegram {student_id}: {e}")


# ─────────────────────────────────────────
# (MỚI) Báo cáo GPA tháng — ngày 1 hàng tháng
# ─────────────────────────────────────────
async def send_monthly_gpa_report():
    """
    Chạy ngày 1 hàng tháng lúc 8:00.
    Tổng hợp toàn bộ số liệu GPA của tháng vừa qua.
    """
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

        # Đếm số môn nhập trong tháng này
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        new_grades  = student_course_collection.count_documents({
            "student_id": student_id,
            "updated_at": {"$gte": month_start}
        })

        # Xếp loại học lực
        if current >= 3.6:
            rank = "Xuất sắc 🏆"
        elif current >= 3.2:
            rank = "Giỏi 🌟"
        elif current >= 2.5:
            rank = "Khá 👍"
        elif current >= 2.0:
            rank = "Trung bình"
        else:
            rank = "Yếu ⚠️"

        # Trạng thái so với mục tiêu
        if current >= target:
            status = f"✅ Đang đạt mục tiêu"
        else:
            gap    = round(target - current, 2)
            status = f"⚠️ Còn thiếu {gap} điểm"

        needed_str = f"{needed}/4.0" if needed and needed <= 4.0 else ("Không thể đạt ❌" if needed else "Đã đạt ✅")

        message = (
            f"📋 *Báo cáo GPA tháng {month}*\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"📊 *GPA tích lũy* : *{current}/4.0*\n"
            f"🏅 Xếp loại      : {rank}\n"
            f"🎯 Mục tiêu      : {target}/4.0\n"
            f"📈 Trạng thái    : {status}\n\n"
            f"📚 *Tiến độ tín chỉ*\n"
            f"Đã hoàn thành : {completed}/{total} TC ({progress}%)\n"
            f"Còn lại       : {remaining} TC\n"
            f"Cần TB mỗi TC : {needed_str}\n\n"
            f"🗓 Tháng này nhập : *{new_grades} môn*\n\n"
            f"{'💪 Tiếp tục cố gắng để đạt mục tiêu!' if current < target else '🎉 Tuyệt vời! Duy trì phong độ nhé!'}"
        )

        try:
            await bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        except Exception as e:
            print(f"[Monthly Report] Lỗi gửi Telegram {student_id}: {e}")