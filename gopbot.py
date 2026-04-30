import asyncio
import requests
import os
import re
import time
import hashlib
import hmac
import base64
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# =========================
# 🔑 CONFIG (ENV)
# =========================
TOKEN = os.getenv("8715231099:AAHqwqVIzTtmq1sSifZnOvuIzUzNfIWTtvs")
ACR_HOST = "identify-ap-southeast-1.acrcloud.com"
ACR_ACCESS_KEY = os.getenv("296c929b5dc7ba13d230b5ef1124f920")
ACR_ACCESS_SECRET = os.getenv("mabjWhiYNpQWMbzzq43LckcuiOMLVYCIeZLVa9NH")

# =========================
# LOG
# =========================
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
dp = Dispatcher()

print(">>> ĐANG CHẠY GOPBOT <<<")

# =========================
# MENU
# =========================
@dp.message(Command("start"))
async def start(msg: types.Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📥 Tải TikTok", callback_data="tiktok")],
            [InlineKeyboardButton(text="🎵 Check nhạc", callback_data="music")]
        ]
    )
    await msg.answer("👋 Chọn chức năng:", reply_markup=keyboard)

# =========================
# BUTTON
# =========================
@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    if callback.data == "tiktok":
        await callback.message.answer("📎 Gửi link TikTok")
    elif callback.data == "music":
        await callback.message.answer("📎 Gửi file MP3")
    await callback.answer()

# =========================
# CLEAN
# =========================
def clean_url(url):
    return url.split("?")[0]

def safe_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

# =========================
# API TIKTOK
# =========================
def api_1(url):
    try:
        api = f"https://tdownv4.sl-bjs.workers.dev/?down={url}"
        res = requests.get(api, timeout=10).json()
        return {"audio": res.get("audio_url"), "title": res.get("title")}
    except:
        return None

def api_2(url):
    try:
        api = f"https://www.tikwm.com/api/?url={url}"
        res = requests.get(api, timeout=10).json()
        if res.get("data"):
            return {
                "audio": res["data"].get("music"),
                "title": res["data"].get("title")
            }
    except:
        return None
    return None

# =========================
# ACRCloud
# =========================
def recognize(file_path):
    http_method = "POST"
    http_uri = "/v1/identify"
    data_type = "audio"
    signature_version = "1"
    timestamp = str(int(time.time()))

    string_to_sign = "\n".join([
        http_method, http_uri, ACR_ACCESS_KEY,
        data_type, signature_version, timestamp
    ])

    sign = base64.b64encode(
        hmac.new(ACR_ACCESS_SECRET.encode('ascii'),
                 string_to_sign.encode('ascii'),
                 digestmod=hashlib.sha1).digest()
    ).decode('ascii')

    with open(file_path, 'rb') as f:
        files = {'sample': f}
        data = {
            'access_key': ACR_ACCESS_KEY,
            'sample_bytes': os.path.getsize(file_path),
            'timestamp': timestamp,
            'signature': sign,
            'data_type': data_type,
            'signature_version': signature_version
        }

        url = f"http://{ACR_HOST}{http_uri}"
        res = requests.post(url, files=files, data=data)

    return res.json()

# =========================
# HANDLE
# =========================
@dp.message()
async def handle(message: types.Message):
    print("📩 Nhận:", message.text)

    # ===== TIKTOK =====
    if message.text and "tiktok.com" in message.text:
        url = clean_url(message.text)
        msg = await message.answer("⏳ Đang tải...")

        data = api_1(url)
        if not data or not data.get("audio"):
            data = api_2(url)

        if data and data.get("audio"):
            title = safe_filename(data.get("title") or "TikTok Audio")

            await message.answer_audio(
                audio=data["audio"],
                title=title,
                performer="TikTok",
                filename=f"{title}.mp3"
            )
            await msg.delete()
        else:
            await msg.edit_text("❌ Không tải được!")

        return

    # ===== CHECK NHẠC =====
    if message.audio or message.document:
        await message.answer("⏳ Đang xử lý...")

        file_path = None

        try:
            if message.audio:
                file_id = message.audio.file_id
                original_name = message.audio.file_name or "audio.mp3"
            else:
                file_id = message.document.file_id
                original_name = message.document.file_name or "audio.mp3"

            file = await bot.get_file(file_id)
            file_path = f"{message.message_id}_{original_name}"
            await bot.download_file(file.file_path, file_path)

            result = recognize(file_path)
            print("ACR RESULT:", result)

            title = "Không xác định"
            artist = ""
            status = "🟢 Không bản quyền"

            if result.get("status", {}).get("code") == 0 and "metadata" in result:
                music = result['metadata']['music'][0]
                title = music.get('title', 'Unknown')
                artist = music.get('artists', [{}])[0].get('name', 'Unknown')
                status = "🔴 Có bản quyền"

            caption = f"""🎵 {title} {('- ' + artist) if artist else ''}
📌 {status}"""

            await message.answer_document(
                types.FSInputFile(file_path),
                caption=caption
            )

        except Exception as e:
            print("Lỗi:", e)
            await message.answer("❌ Lỗi xử lý nhạc")

        finally:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)

        return

# =========================
# RUN
# =========================
async def main():
    print("🤖 Bot đang chạy...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print("CRASH:", e)
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
