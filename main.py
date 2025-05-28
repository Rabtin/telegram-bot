import os
from telegram.ext import Application, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")

app = Application.builder().token(TOKEN).build()

async def start(update, context):
    await update.message.reply_text("سلام! من یه ربات ساده‌ام و روی Render اجرا می‌شم.")

app.add_handler(CommandHandler("start", start))

app.run_polling()
