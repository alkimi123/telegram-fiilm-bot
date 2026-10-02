import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
STORAGE_CHAT_ID = int(os.environ["STORAGE_CHAT_ID"])
BOT_USERNAME = os.environ.get("BOT_USERNAME", "FilmAutoUpload2026Bot")


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running")

    def log_message(self, format, *args):
        pass


def start_health_server():
    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args

    if not args:
        await update.message.reply_text(
            "سلام 👋\n"
            "لینک دریافت فیلم را از کانال باز کن تا فیلم برایت ارسال شود."
        )
        return

    code = args[0]

    if not code.startswith("m_"):
        await update.message.reply_text("لینک فیلم معتبر نیست.")
        return

    try:
        message_id = int(code[2:])
    except ValueError:
        await update.message.reply_text("شناسه فیلم معتبر نیست.")
        return

    try:
        await context.bot.copy_message(
            chat_id=update.effective_chat.id,
            from_chat_id=STORAGE_CHAT_ID,
            message_id=message_id,
        )
    except Exception:
        await update.message.reply_text(
            "متأسفانه این فیلم در حال حاضر در دسترس نیست."
        )


async def save_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message

    # فقط خود صاحب ربات می‌تواند فیلم جدید ثبت کند.
    # OWNER_ID را بعداً در Render تنظیم می‌کنیم.
    owner_id = int(os.environ["OWNER_ID"])

    if update.effective_user.id != owner_id:
        await message.reply_text(
            "این بخش فقط برای مدیر ربات فعال است."
        )
        return

    try:
        copied = await context.bot.copy_message(
            chat_id=STORAGE_CHAT_ID,
            from_chat_id=message.chat_id,
            message_id=message.message_id,
        )

        message_id = copied.message_id

        link = f"https://t.me/{BOT_USERNAME}?start=m_{message_id}"

        await message.reply_text(
            "✅ فیلم ثبت شد.\n\n"
            "🔗 لینک دریافت:\n"
            f"{link}\n\n"
            "این لینک را می‌توانی زیر معرفی فیلم در کانالت قرار بدهی."
        )

    except Exception:
        await message.reply_text(
            "❌ ذخیره فیلم انجام نشد. تنظیمات ربات را بررسی کن."
        )


def main():
    threading.Thread(
        target=start_health_server,
        daemon=True
    ).start()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    media_filter = (
        filters.VIDEO
        | filters.Document.VIDEO
    )

    app.add_handler(
        MessageHandler(media_filter, save_media)
    )

    print("Bot started...")
    app.run_polling()


if __name__ == "__main__":
    main()
