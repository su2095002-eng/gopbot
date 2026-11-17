import asyncio
import requests
import re

from aiogram import Bot, Dispatcher, types

# =========================
# 🔑 CONFIG (SỬA DÒNG NÀY)
# =========================
TOKEN = "8715231099:AAHqwqVIzTtmq1sSifZnOvuIzUzNfIWTtvs"

bot = Bot(token=TOKEN)
dp = Dispatcher()

print(">>> ĐANG CHẠY GOPBOT (CHỈ TẢI NHẠC TIKTOK) <<<")

# =========================
# 🎯 LỜI CHÀO
# =========================
@dp.message(lambda msg: msg.text == "/start")
async def start(msg: types.Message):
    await msg.answer("👋 Gửi link TikTok để bot tải nhạc MP3 về cho bạn!")

# =========================
# 🧹 CLEAN
# =========================
def clean_url(url):
    return url.split("?")[0]

def safe_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

# =========================
# 📥 API TIKTOK (2 API dự phòng cho nhau)
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
# 🤖 XỬ LÝ LINK TIKTOK
# =========================
@dp.message()
async def handle(message: types.Message):
    if message.text and "tiktok.com" in message.text:
        url = clean_url(message.text)
        msg = await message.answer("⏳ Đang tải...")

        # thử API 1 trước, nếu lỗi thì dùng API 2
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

# =========================
# ▶️ RUN
# =========================
async def main():
    print("🤖 Bot đang chạy...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
