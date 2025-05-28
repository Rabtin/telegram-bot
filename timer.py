import asyncio
import os
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

def resize_image(path, size=(128, 128)):
    try:
        with Image.open(path) as img:
            img = img.resize(size)
            bio = BytesIO()
            bio.name = 'resized.png'
            img.save(bio, 'PNG')
            bio.seek(0)
            return bio
    except FileNotFoundError:
        return None

def get_main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎣 آموزش مافیا", url="https://t.me/friendlymafiatrainning"),
         InlineKeyboardButton("🎮 گروه بازی", url="https://t.me/mafia_friendly3")],

        [InlineKeyboardButton("10", callback_data="timer_10"),
         InlineKeyboardButton("15", callback_data="timer_15"),
         InlineKeyboardButton("20", callback_data="timer_20")],

        [InlineKeyboardButton("30", callback_data="timer_30"),
         InlineKeyboardButton("45", callback_data="timer_45"),
         InlineKeyboardButton("60", callback_data="timer_60")],

        [InlineKeyboardButton("75", callback_data="timer_75"),
         InlineKeyboardButton("90", callback_data="timer_90"),
         InlineKeyboardButton("120", callback_data="timer_120")],
         
        [InlineKeyboardButton("⏱ تایمر دلخواه", callback_data="custom_timer"),
         InlineKeyboardButton("📌 چالش", callback_data="challenge_start")],
     
        [InlineKeyboardButton("🎭 کاور", callback_data="show_cover"),
         InlineKeyboardButton("🎬 سناریو", callback_data="show_scenario")],
        [InlineKeyboardButton("🌞 روز", callback_data="send_day"), InlineKeyboardButton("🧮 استعلام", callback_data="send_estelam"), InlineKeyboardButton("🌙 شب", callback_data="send_night")],
        [InlineKeyboardButton("🎵 موزیک", callback_data="show_music")]
    ])

async def handle_custom_timer_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_custom_timer"):
        context.user_data["awaiting_custom_timer"] = False
        try:
            seconds = int(update.message.text.strip())
            if seconds <= 0 or seconds > 3600:
                raise ValueError
        except ValueError:
            await update.message.reply_text("⛔ لطفاً عددی معتبر بین 1 تا 3600 وارد کنید.")
            return

        if "timer_task" in context.chat_data:
            await update.message.reply_text("⚠️ یک تایمر در حال اجراست. ابتدا آن را لغو کنید.")
            return

        await update.message.reply_text(f"✅ تایمر {seconds} ثانیه‌ای در حال شروع است...")

        async def countdown():
            try:
                progress_msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="شروع شمارش...")
                total_blocks = 10
                for elapsed in range(seconds):
                    progress = int((elapsed + 1) / seconds * total_blocks)
                    bar = '🟩' * progress + '⬜' * (total_blocks - progress)
                    percent = int((elapsed + 1) / seconds * 100)
                    await progress_msg.edit_text(f"{bar} {percent}%")
                    await asyncio.sleep(1)

                done_img = "done.png"
                if done_img:
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=done_img, caption="⏰ زمان شما به پایان رسید.")
                try:
                    with open("alarm.mp3", "rb") as audio:
                        await context.bot.send_audio(chat_id=update.effective_chat.id, audio=audio, caption="🔊 هشدار پایان تایمر")
                except FileNotFoundError:
                    await context.bot.send_message(chat_id=update.effective_chat.id, text="❗️ فایل صوتی یافت نشد.")

            except asyncio.CancelledError:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ تایمر لغو شد.")
            finally:
                context.chat_data.pop("timer_task", None)
                timer_img = resize_image("timer.png")
                if timer_img:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=timer_img,
                        caption="⏱ لطفاً یک تایمر جدید انتخاب کنید:",
                        reply_markup=get_main_menu()
                    )

        task = asyncio.create_task(countdown())
        context.chat_data["timer_task"] = task

        await update.message.reply_text(
            "برای لغو تایمر روی دکمه زیر بزن:",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("❌ لغو تایمر", callback_data="cancel_timer")
            ]])
        )

async def start_timer_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type in ["group", "supergroup"]:
        admins = await chat.get_administrators()
        if user.id not in [admin.user.id for admin in admins]:
            await update.message.reply_text("⛔ فقط ادمین‌های گروه می‌توانند از این دستور استفاده کنند.")
            return

    resized = resize_image("timer.png")
    if resized:
        await update.message.reply_photo(
            photo=resized,
            caption="⏱ لطفاً مدت زمان تایمر را انتخاب کنید:",
            reply_markup=get_main_menu()
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat = update.effective_chat
    user = update.effective_user

    if chat.type in ["group", "supergroup"]:
        admins = await chat.get_administrators()
        if user.id not in [admin.user.id for admin in admins]:
            await query.answer("⛔ فقط ادمین‌های گروه می‌توانند از دکمه‌ها استفاده کنند.", show_alert=True)
            return

    data = query.data
    await query.answer()

    if data.startswith("timer_"):
        seconds = int(data.split("_")[1])
        await query.message.reply_text(f"⏳ تایمر {seconds} ثانیه‌ای شروع شد...")

        async def countdown():
            try:
                progress_msg = await context.bot.send_message(chat_id=chat.id, text="شروع شمارش...")

                total_blocks = 10
                for elapsed in range(seconds):
                    progress = int((elapsed + 1) / seconds * total_blocks)
                    bar = '🟩' * progress + '⬜' * (total_blocks - progress)
                    percent = int((elapsed + 1) / seconds * 100)
                    await progress_msg.edit_text(f"{bar} {percent}%")
                    await asyncio.sleep(1)

                done_img = "done.png"
                await context.bot.send_photo(chat_id=chat.id, photo=done_img, caption="⏰ زمان شما به پایان رسید.")
                with open("alarm.mp3", "rb") as voice:
                    await context.bot.send_voice(chat_id=chat.id, voice=voice, caption="🔊 هشدار پایان تایمر")


            except asyncio.CancelledError:
                await context.bot.send_message(chat_id=chat.id, text="❌ تایمر لغو شد.")
                return

            finally:
                context.chat_data.pop("timer_task", None)

            timer_img = resize_image("timer.png")
            await context.bot.send_photo(
                chat_id=chat.id,
                photo=timer_img,
                caption="⏱ لطفاً یک تایمر جدید انتخاب کنید:",
                reply_markup=get_main_menu()
        )


        task = asyncio.create_task(countdown())
        context.chat_data["timer_task"] = task

        await context.bot.send_message(
            chat_id=chat.id,
            text="📝لغو تایمر :",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("❌ لغو تایمر", callback_data="cancel_timer")]
            ])
        )
   
    elif data == "cancel_timer":
        task = context.chat_data.get("timer_task")
        if task and not task.done():
            task.cancel()
        else:
            await query.message.reply_text("⏳ تایمر فعالی برای لغو وجود ندارد.")
            
    elif data == "custom_timer":
        context.user_data["awaiting_custom_timer"] = True
        await query.message.reply_text("⏱ لطفاً مدت زمان تایمر را به ثانیه وارد کنید (مثلاً: 45)")

    elif data == "back_to_menu":
        timer_img = resize_image("timer.png")
        await query.message.edit_media(
            media=InputMediaPhoto(media=timer_img, caption="⏱ لطفاً مدت زمان تایمر را انتخاب کنید:"),
            reply_markup=get_main_menu()
        )
    
    elif data == "show_cover":
        image_folder = "images"
        image_files = sorted([
            f for f in os.listdir(image_folder)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ])[:20]

        if not image_files:
            await query.message.edit_caption("❌ هیچ تصویری در پوشه 'images' پیدا نشد.")
            return

        await query.message.edit_caption("📸 کاورها ارسال شدند در آلبوم جداگانه.\n⬅️ برای بازگشت، از دکمه زیر استفاده کن:",
                                         reply_markup=InlineKeyboardMarkup([
                                             [InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")]
                                         ]))

        for i in range(0, len(image_files), 10):
            media_group = []
            batch = image_files[i:i + 10]
            for filename in batch:
                with open(os.path.join(image_folder, filename), "rb") as img_file:
                    media_group.append(InputMediaPhoto(img_file.read()))
            await context.bot.send_media_group(chat_id=chat.id, media=media_group)

    elif data == "show_scenario":
        try:
            with open("scenarios.txt", "r", encoding="utf-8") as file:
                lines = [line.strip() for line in file if "|" in line]

            if not lines:
                await query.message.edit_caption("⚠️ هیچ سناریویی در فایل موجود نیست.")
                return

            buttons, row = [], []
            for i, line in enumerate(lines):
                title, _ = map(str.strip, line.split("|", 1))
                row.append(InlineKeyboardButton(title, callback_data=f"scenario_{i}"))
                if (i + 1) % 5 == 0:
                    buttons.append(row)
                    row = []
            if row:
                buttons.append(row)

            buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")])
            context.user_data["scenarios"] = lines

            await query.message.edit_caption(
                caption="🎬 لطفاً یک سناریو را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        except FileNotFoundError:
            await query.message.edit_caption("❌ فایل 'scenarios.txt' یافت نشد.")

    elif data.startswith("scenario_"):
        index = int(data.split("_")[1])
        scenarios = context.user_data.get("scenarios", [])
        if 0 <= index < len(scenarios):
            _, content = map(str.strip, scenarios[index].split("|", 1))
            await context.bot.send_message(chat_id=chat.id, text=f"📜 {content}")
        else:
            await query.message.reply_text("❌ سناریوی انتخابی معتبر نیست.")

    elif data == "challenge_start":
        context.user_data["awaiting_challenge_count"] = True
        await query.message.reply_text("📌 لطفاً تعداد بازیکنان را وارد کنید (مثلاً: 9)")
    
    elif data == "send_day":
        try:
            with Image.open("rooz.png") as img:
                img = img.convert("RGB")
                img = ImageEnhance.Brightness(img).enhance(1.2)  # نور بیشتر
                img = img.filter(ImageFilter.SHARPEN)  # وضوح بیشتر

                bio = BytesIO()
                img.save(bio, format="PNG")
                bio.name = "rooz_effect.png"
                bio.seek(0)

                await context.bot.send_photo(chat_id=chat.id, photo=bio, caption="🌞 روز")
        except FileNotFoundError:
            await query.message.reply_text("❌ فایل rooz.png پیدا نشد.")
        
    elif data == "send_estelam":
        try:
            with open("estelam.png", "rb") as photo:
                await context.bot.send_photo(chat_id=chat.id, photo=photo, caption="🧮 استعلام")
        except FileNotFoundError:
            await query.message.reply_text("❌ فایل estelam.png پیدا نشد.")
    
    elif data == "send_night":
        try:
            with open("shab.png", "rb") as photo:
                await context.bot.send_photo(chat_id=chat.id, photo=photo, caption="🌙 شب")
        except FileNotFoundError:
            await query.message.reply_text("❌ فایل shab.png پیدا نشد.")
    elif data == "show_music":
        music_folder = "music"
        music_files = sorted([
            f for f in os.listdir(music_folder)
            if f.lower().endswith(".mp3")
        ])
    
        if not music_files:
            await query.message.edit_caption("⚠️ هیچ موزیکی در پوشه 'music/' یافت نشد.")
            return
    
        buttons, row = [], []
        for i, filename in enumerate(music_files):
            display_name = os.path.splitext(filename)[0]
            row.append(InlineKeyboardButton(display_name, callback_data=f"musicplay_{filename}"))
            if (i + 1) % 2 == 0:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
    
        buttons.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")])
    
        await query.message.edit_caption(
            caption="🎵 لطفاً موزیکی برای پخش در voice انتخاب کن:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )


    elif data.startswith("music_"):
        index = int(data.split("_")[1])
        music_list = context.user_data.get("music_list", [])
        if 0 <= index < len(music_list):
            _, command = map(str.strip, music_list[index].split("|", 1))
            await context.bot.send_message(chat_id=chat.id, text=f"{command}")
        else:
            await query.message.reply_text("❌ موزیک انتخابی معتبر نیست.")
    
    if data.startswith("challenge_toggle_"):
        index = int(data.split("_")[2])
        status = context.chat_data.get("challenge_status", [])
        if 0 <= index < len(status):
            status[index] = not status[index]
            new_text = "📌 وضعیت چالش:" + "  ".join([
                f"{i+1}.{'🤏' if v else ''}" for i, v in enumerate(status)
            ])
            message_id = context.chat_data.get("challenge_message_id")
            if message_id:
                await context.bot.edit_message_text(
                    chat_id=chat.id,
                    message_id=message_id,
                    text=new_text,
                    reply_markup=query.message.reply_markup
                )
        return

    if data == "challenge_reset":
        context.chat_data["challenge_status"] = [False] * context.chat_data.get("challenge_count", 0)
        new_text = "📌 وضعیت چالش:\n" + "  ".join([
            f"{i+1}." for i in range(len(context.chat_data["challenge_status"]))
        ])
        message_id = context.chat_data.get("challenge_message_id")
        if message_id:
            await context.bot.edit_message_text(
                chat_id=chat.id,
                message_id=message_id,
                text=new_text,
                reply_markup=query.message.reply_markup
            )
        return
    # برای پردازش دکمه‌های چالش، تابع handle_challenge_input را صدا بزن
    elif data.startswith("challenge_toggle_") or data == "challenge_reset":
        update.callback_query = query  # اجباری برای هماهنگی ساختار
        await handle_challenge_input(update, context)

async def handle_challenge_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_challenge_count"):
        context.user_data["awaiting_challenge_count"] = False
        try:
            count = int(update.message.text.strip())
            if count <= 0 or count > 50:
                raise ValueError
        except ValueError:
            await update.message.reply_text("⛔ لطفاً عددی معتبر بین 1 تا 50 وارد کنید.")
            return

        # ساخت وضعیت اولیه چالش
        context.chat_data["challenge_status"] = [False] * count

        # ذخیره پیام وضعیت برای ویرایش‌های بعدی
        buttons = []
        for i in range(count):
            buttons.append(InlineKeyboardButton(str(i + 1), callback_data=f"challenge_toggle_{i}"))

        keyboard = [buttons[i:i + 5] for i in range(0, len(buttons), 5)]
        keyboard.append([
            InlineKeyboardButton("🔄 ریست چالش‌ها", callback_data="challenge_reset"),
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")
        ])

        lines = []
        for i in range(0, count, 5):
            line = "  ".join([f"{j+1}." for j in range(i, min(i+5, count))])
            lines.append(line)
        text = "📌 وضعیت چالش:\n\n" + "\n".join(lines)


        msg = await update.message.reply_text(
            text=text,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

        context.chat_data["challenge_message_id"] = msg.message_id
        context.chat_data["challenge_message_text"] = text
        context.chat_data["challenge_count"] = count

    # مدیریت کلیک روی جایگاه چالش
    elif update.callback_query and update.callback_query.data.startswith("challenge_toggle_"):
        query = update.callback_query
        index = int(query.data.split("_")[2])
        status = context.chat_data.get("challenge_status", [])
        if 0 <= index < len(status):
            status[index] = not status[index]  # تغییر وضعیت

            # ساخت متن جدید
            new_text = "📌 وضعیت چالش:\n" + "  ".join([
                f"{i+1}.{'🤏' if v else ''}" for i, v in enumerate(status)
            ])

            message_id = context.chat_data.get("challenge_message_id")
            if message_id:
                await query.bot.edit_message_text(
                    chat_id=query.message.chat_id,
                    message_id=message_id,
                    text=new_text,
                    reply_markup=query.message.reply_markup
                )

    elif update.callback_query and update.callback_query.data == "challenge_reset":
        context.chat_data["challenge_status"] = [False] * context.chat_data.get("challenge_count", 0)
        new_text = "📌 وضعیت چالش:\n" + "  ".join([
            f"{i+1}." for i in range(len(context.chat_data["challenge_status"]))
        ])
        message_id = context.chat_data.get("challenge_message_id")
        if message_id:
            await update.callback_query.bot.edit_message_text(
                chat_id=update.callback_query.message.chat_id,
                message_id=message_id,
                text=new_text,
                reply_markup=update.callback_query.message.reply_markup
            )

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    # تایمر دلخواه
    if context.user_data.get("awaiting_custom_timer"):
        context.user_data["awaiting_custom_timer"] = False
        try:
            seconds = int(text)
            if seconds <= 0 or seconds > 3600:
                raise ValueError
        except ValueError:
            await update.message.reply_text("⛔ لطفاً عددی معتبر بین 1 تا 3600 وارد کنید.")
            return

        if "timer_task" in context.chat_data:
            await update.message.reply_text("⚠️ یک تایمر در حال اجراست. ابتدا آن را لغو کنید.")
            return

        await update.message.reply_text(f"✅ تایمر {seconds} ثانیه‌ای در حال شروع است...")

        async def countdown():
            try:
                msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="شروع شمارش...")
                total_blocks = 10
                for elapsed in range(seconds):
                    progress = int((elapsed + 1) / seconds * total_blocks)
                    bar = '🟩' * progress + '⬜' * (total_blocks - progress)
                    percent = int((elapsed + 1) / seconds * 100)
                    await msg.edit_text(f"{bar} {percent}%")
                    await asyncio.sleep(1)
                await context.bot.send_message(chat_id=update.effective_chat.id, text="⏰ زمان شما به پایان رسید.")
            except asyncio.CancelledError:
                await context.bot.send_message(chat_id=update.effective_chat.id, text="❌ تایمر لغو شد.")
            finally:
                context.chat_data.pop("timer_task", None)

        task = asyncio.create_task(countdown())
        context.chat_data["timer_task"] = task
        return

    # چالش
    if context.user_data.get("awaiting_challenge_count"):
        context.user_data["awaiting_challenge_count"] = False
        try:
            count = int(text)
            if count <= 0 or count > 50:
                raise ValueError
        except ValueError:
            await update.message.reply_text("⛔ لطفاً عددی معتبر بین 1 تا 50 وارد کنید.")
            return

        context.chat_data["challenge_status"] = [False] * count
        buttons = []
        for i in range(count):
            buttons.append(InlineKeyboardButton(str(i + 1), callback_data=f"challenge_toggle_{i}"))
        keyboard = [buttons[i:i + 5] for i in range(0, len(buttons), 5)]
        keyboard.append([
            InlineKeyboardButton("🔄 ریست چالش‌ها", callback_data="challenge_reset"),
            InlineKeyboardButton("🔙 بازگشت", callback_data="back_to_menu")
        ])


        lines = []
        for i in range(0, count, 5):
            line = "  ".join([f"{j+1}." for j in range(i, min(i+5, count))])
            lines.append(line)
        text_out = "📌 وضعیت چالش:\n\n" + "\n".join(lines)

        msg = await update.message.reply_text(text_out, reply_markup=InlineKeyboardMarkup(keyboard))
        context.chat_data["challenge_message_id"] = msg.message_id
        context.chat_data["challenge_message_text"] = text_out
        context.chat_data["challenge_count"] = count

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("timer", start_timer_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))


    
    print("✅ ربات تایمر در حال اجراست...")
    app.run_polling()

if __name__ == '__main__':
    main()
