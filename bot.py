#!/usr/bin/env python3
"""
بوت تيليجرام - نتائج امتحانات السادس الابتدائي ذي قار 2025-2026
للتشغيل: python3 bot.py
"""

import sqlite3
import logging
import os
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes
)

# ──────────────────────────────────────────
#  الإعدادات — غيّر هذه القيم فقط
# ──────────────────────────────────────────
BOT_TOKEN = "ضع_توكن_البوت_هنا"        # من @BotFather
DB_PATH   = "students.db"              # مسار قاعدة البيانات

# ──────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── نتائج emoji ───
RESULT_EMOJI = {
    "ناجح":  "✅",
    "راسب":  "❌",
    "مكمل":  "🔄",
}

SUBJECT_NAMES = {
    "islamic": "التربية الإسلامية",
    "arabic":  "اللغة العربية",
    "english": "اللغة الإنجليزية",
    "math":    "الرياضيات",
    "social":  "الاجتماعيات",
    "science": "العلوم",
}


def get_student(exam_no: str) -> dict | None:
    """البحث عن طالب بالرقم الامتحاني"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    row = c.execute(
        "SELECT * FROM students WHERE exam_no = ?",
        (exam_no.strip(),)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def format_result(s: dict) -> str:
    """تنسيق رسالة النتيجة"""
    emoji = RESULT_EMOJI.get(s["result"], "📋")

    # شريط تقدم بصري للمعدل
    avg = float(s["average"])
    filled = int(avg / 10)
    bar = "█" * filled + "░" * (10 - filled)

    lines = [
        f"📋 *نتيجة الامتحان الوزاري*",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"👤 *الاسم:* {s['name']}",
        f"🔢 *الرقم الامتحاني:* `{s['exam_no']}`",
        f"🏫 *المدرسة:* {s['school_name']}",
        f"📍 *القاطع:* {s['district']}",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"",
        f"📚 *الدرجات:*",
        f"",
    ]

    subjects = [
        ("islamic", "📖"),
        ("arabic",  "📝"),
        ("english", "🔤"),
        ("math",    "🔢"),
        ("social",  "🌍"),
        ("science", "🔬"),
    ]

    for key, ico in subjects:
        grade = int(s[key])
        # لون الدرجة
        if grade >= 90:
            mark = "🟢"
        elif grade >= 75:
            mark = "🟡"
        elif grade >= 50:
            mark = "🟠"
        else:
            mark = "🔴"
        lines.append(f"{ico} {SUBJECT_NAMES[key]}: *{grade}/100* {mark}")

    lines += [
        f"",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"📊 *المجموع الكلي:* {s['total']}/600",
        f"📈 *المعدل:* {avg:.2f}%",
        f"▓ {bar} ▓",
        f"",
        f"🏆 *النتيجة النهائية:* {emoji} *{s['result']}*",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"",
        f"_نتائج السادس الابتدائي - ذي قار 2025/2026_",
    ]

    return "\n".join(lines)


# ─── معالجات البوت ───

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 *أهلاً بك في بوت نتائج السادس الابتدائي*\n"
        "🏫 *محافظة ذي قار - العام الدراسي 2025/2026*\n\n"
        "📌 *طريقة الاستخدام:*\n"
        "أرسل رقمك الامتحاني مباشرةً وسيظهر لك النتيجة.\n\n"
        "✏️ *مثال:*\n"
        "`222620001002`\n\n"
        "ℹ️ الرقم الامتحاني مكوّن من 12 رقم."
    )
    await update.message.reply_text(msg, parse_mode="Markdown")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # تحقق أن الرسالة تبدو وكأنها رقم امتحاني
    clean = text.replace(" ", "").replace("-", "")

    if not clean.isdigit():
        await update.message.reply_text(
            "⚠️ الرجاء إرسال *الرقم الامتحاني فقط*.\n"
            "مثال: `222620001002`",
            parse_mode="Markdown"
        )
        return

    if len(clean) != 12:
        await update.message.reply_text(
            f"⚠️ الرقم الامتحاني يجب أن يكون *12 رقماً*.\n"
            f"الرقم الذي أرسلته يحتوي على {len(clean)} رقم.",
            parse_mode="Markdown"
        )
        return

    # إرسال رسالة انتظار
    wait_msg = await update.message.reply_text("🔍 جاري البحث...")

    student = get_student(clean)

    if student:
        result_text = format_result(student)
        await wait_msg.edit_text(result_text, parse_mode="Markdown")
        logger.info(f"Found: {clean} → {student['name']}")
    else:
        await wait_msg.edit_text(
            f"❌ *لم يتم العثور على نتيجة*\n\n"
            f"الرقم الامتحاني `{clean}` غير موجود في قاعدة البيانات.\n\n"
            f"تأكد من صحة الرقم وأعد المحاولة.",
            parse_mode="Markdown"
        )
        logger.info(f"Not found: {clean}")


async def error_handler(update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"خطأ: {context.error}")


# ─── تشغيل البوت ───

def main():
    if BOT_TOKEN == "ضع_توكن_البوت_هنا":
        print("❌ الخطأ: لم يتم تعيين توكن البوت!")
        print("   افتح ملف bot.py وغيّر قيمة BOT_TOKEN")
        return

    if not os.path.exists(DB_PATH):
        print(f"❌ الخطأ: ملف قاعدة البيانات غير موجود: {DB_PATH}")
        return

    # اختبار قاعدة البيانات
    conn = sqlite3.connect(DB_PATH)
    count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    conn.close()
    print(f"✅ قاعدة البيانات جاهزة: {count:,} طالب")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)

    print("🤖 البوت يعمل... اضغط Ctrl+C للإيقاف")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
