from dotenv import load_dotenv
from pathlib import Path
import os
import io
import base64
from PIL import Image
import httpx

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ChatAction

from scraper import get_fashion_news_with_summary

# ----------------- .env -----------------
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY")
YANDEX_REGION = os.environ.get("YANDEX_REGION")
YANDEX_IMAGE_MODEL = "general-image-analysis"

if not TELEGRAM_TOKEN or not YANDEX_API_KEY:
    raise ValueError("❌ TELEGRAM_TOKEN или YANDEX_API_KEY не найдены")

user_conversations = {}
keywords = ["мода", "новости моды", "fashion", "тренды"]


async def get_fashion_news():
    return get_fashion_news_with_summary()


async def analyze_image_yandex(image_bytes, caption=""):
    url = f"https://{YANDEX_REGION}.api.cloud.yandex.net/ai/v1/models/{YANDEX_IMAGE_MODEL}:predict"
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    prompt = f"Проанализируй модный образ на фото. {caption}"

    payload = {"instances": [{"text": prompt, "image": image_base64}]}
    headers = {"Authorization": f"Bearer {YANDEX_API_KEY}"}

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("predictions", [{}])[0].get("output_text", "Анализ недоступен")
        except Exception as e:
            print(f"❌ Ошибка анализа изображения: {e}")
            return "Ошибка при анализе изображения"


# ----------------- Обработчики -----------------
async def start(update: Update, context):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    user_conversations[user_id] = []
    await update.message.reply_text(f"👋 Привет, {user_name}! Отправь текст или фото.")


async def help_command(update: Update, context):
    await update.message.reply_text(
        "💡 Примеры:\n- Как подобрать одежду?\n- Оцени мой образ\n- Новости моды: 'мода', 'тренды'"
    )


async def clear_history(update: Update, context):
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    await update.message.reply_text("✨ История очищена!")


async def trends(update: Update, context):
    await update.message.reply_text("⏳ Собираю новости...")
    try:
        news = await get_fashion_news()
        await update.message.reply_text(news, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка при формировании новостей: {e}")


async def handle_message(update: Update, context):
    user_id = update.effective_user.id
    user_message = update.message.text
    if user_id not in user_conversations:
        user_conversations[user_id] = []

    user_conversations[user_id].append({"role": "user", "content": user_message})
    await update.message.chat.send_action(ChatAction.TYPING)

    if any(k.lower() in user_message.lower() for k in keywords):
        news = await get_fashion_news()
        await update.message.reply_text(news, parse_mode="Markdown")
        return

    prompt = f"Ты AI-стилист. Ответь подробно на сообщение:\n{user_message}"
    url = f"https://{YANDEX_REGION}.api.cloud.yandex.net/ai/v1/models/general-text-summarizer:predict"
    payload = {"instances": [{"text": prompt}]}
    headers = {"Authorization": f"Bearer {YANDEX_API_KEY}"}

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            answer = data.get("predictions", [{}])[0].get("output_text", "Ответ недоступен")
        except Exception as e:
            answer = f"😔 Ошибка: {e}"

    await update.message.reply_text(answer)


async def handle_photo(update: Update, context):
    user_id = update.effective_user.id
    if user_id not in user_conversations:
        user_conversations[user_id] = []

    await update.message.chat.send_action(ChatAction.UPLOAD_PHOTO)
    try:
        photo = update.message.photo[-1]
        photo_file = await photo.get_file()
        photo_bytes = await photo_file.download_as_bytearray()

        image = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
        image.thumbnail((1024, 1024))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=85)
        processed_bytes = buffer.getvalue()

        caption = update.message.caption or ""
        analysis = await analyze_image_yandex(processed_bytes, caption)
        await update.message.reply_text(analysis)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка обработки фото: {e}")


# ----------------- Main -----------------
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(CommandHandler("trends", trends))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.run_polling()


if __name__ == "__main__":
    main()
