# music_player.py
import os
from pyrogram import Client
from pytgcalls import PyTgCalls
from pytgcalls.types.input_stream import InputAudioStream, InputStream
from pytgcalls.types.input_stream.quality import HighQualityAudio

API_ID = int(os.getenv("TG_API_ID"))
API_HASH = os.getenv("TG_API_HASH")
SESSION = "userbot"  # یا اسم session string
GROUP_ID = int(os.getenv("GROUP_ID"))  # آیدی گروه که بات باید توش پخش کنه

app = Client(SESSION, api_id=API_ID, api_hash=API_HASH)
pytgcalls = PyTgCalls(app)

async def play_audio(filename):
    await pytgcalls.join_group_call(
        GROUP_ID,
        InputStream(
            InputAudioStream(
                f"music/{filename}",
                HighQualityAudio()
            )
        )
    )

@app.on_message()
async def control(client, message):
    if message.text.startswith("پخش "):
        filename = message.text[5:].strip()
        if os.path.exists(f"music/{filename}"):
            await play_audio(filename)
            await message.reply("🎵 موزیک در حال پخش است.")
        else:
            await message.reply("❌ موزیک یافت نشد.")

app.start()
pytgcalls.start()
print("🎶 Music player is ready")
input("Press Enter to exit...\n")
