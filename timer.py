import asyncio
import os
import yt_dlp
from io import BytesIO
from PIL import Image, ImageEnhance, ImageFilter
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

# تابع پخش موزیک از YouTube
async def download_and_play_youtube_music(query: str, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'noplaylist': True,
        'quiet': True,
    }

    await context.bot.send_message(chat_id=chat_id, text=f"🔍 در حال جستجوی '{query}' در YouTube...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            audio_file = ydl.prepare_filename(info['entries'][0]).replace(".webm", ".mp3").replace(".m4a", ".mp3")

        with open(audio_file, 'rb') as f:
            await context.bot.send_audio(chat_id=chat_id, audio=f, caption=f"🎶 پخش: {query}")

        os.remove(audio_file)

    except Exception as e:
        await context.bot.send_message(chat_id=chat_id, text=f"❌ خطا در دانلود موزیک: {e}")

# دکمه‌ها از music.txt خوانده شود
async def show_music_from_txt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    try:
        with open("music.txt", "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip() and "|" in line]
    except FileNotFoundError:
        await query.message.edit_caption("❌ فایل music.txt پیدا نشد.")
        return

    context.user_data["music_list"] = lines

    buttons = []
    for i, line in enumerate(lines):
        title, _ = line.split("|", 1)
        buttons.append([InlineKeyboardButton(title, callback_data=f"music_{i}")])

    buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")])

    await query.message.edit_caption(
        caption="🎵 لطفاً موزیکی را انتخاب کنید:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# پردازش دکمه‌های موزیک txt
async def handle_music_selection(index: int, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    music_list = context.user_data.get("music_list", [])
    if 0 <= index < len(music_list):
        _, query = map(str.strip, music_list[index].split("|", 1))
        await download_and_play_youtube_music(query, context, chat_id)
    else:
        await context.bot.send_message(chat_id=chat_id, text="❌ موزیک انتخابی معتبر نیست.")

async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data

    if data.startswith("music_"):
        index = int(data.split("_")[1])
        await handle_music_selection(index, context, query.message.chat_id)
    elif data == "back_to_menu":
        timer_img = resize_image("timer.png")
        await query.message.edit_media(
            media=InputMediaPhoto(media=timer_img, caption="⏱ لطفاً مدت زمان تایمر را انتخاب کنید:"),
            reply_markup=get_main_menu()
        )
    elif data == "show_music":
        await show_music_from_txt(update, context)

# تابع ساخت منوی اصلی
def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎵 موزیک", callback_data="show_music")]
    ])

# تابع شروع تایمر (تعریف شده برای جلوگیری از ارور)
async def start_timer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⏱ تایمر آماده است. لطفاً مدت زمان را انتخاب کنید.")

# هندلر اصلی دکمه‌ها
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await callback_router(update, context)

# هندلر پیام متنی
async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("پیام متنی دریافت شد.")

# داخل main اضافه کن:
def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("timer", start_timer_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(CallbackQueryHandler(callback_router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    print("✅ ربات تایمر در حال اجراست...")
    app.run_polling()

if __name__ == '__main__':
    main()
