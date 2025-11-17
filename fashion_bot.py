# ----------------- imports -----------------
from dotenv import load_dotenv
from pathlib import Path
import os
import io
import base64
import httpx
from PIL import Image

# Telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ChatAction

# Парсер модных новостей
from scraper import get_all_fashion_updates

# ----------------- Переменные окружения -----------------
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")

if not TELEGRAM_TOKEN or not DEEPSEEK_API_KEY:
    raise ValueError(
        "❌ Не найдены токены! Добавьте TELEGRAM_TOKEN и DEEPSEEK_API_KEY в Heroku Config Vars"
    )

# ----------------- Настройки DeepSeek -----------------
API_URL = "https://api.deepseek.com/v1/chat/completions"
FASHION_SYSTEM_PROMPT = """Ты — экспертный AI-агент в области fashion-индустрии, сочетающий роли профессионального стилиста и продюсера.

ТВОИ РОЛИ:

🎨 КАК СТИЛИСТ:
- Анализируй образы с профессиональной точки зрения (силуэт, цвет, пропорции, текстуры)
- Давай конкретные, применимые советы по стилю
- Учитывай типы фигур, цветотипы, lifestyle клиента
- Создавай капсульные гардеробы и луки для разных случаев
- Рекомендуй сочетания вещей и аксессуаров
- Следи за актуальными трендами, но адаптируй их под индивидуальность

🎬 КАК ПРОДЮСЕР:
- Помогай планировать fashion-проекты (съемки, показы, кампании)
- Консультируй по бюджетированию и тайминг съемок
- Давай советы по выбору команды (фотографы, визажисты, модели)
- Помогай с концепцией и настроением проекта
- Консультируй по локациям и реквизиту

СТИЛЬ ОБЩЕНИЯ:
- Профессиональный, но дружелюбный
- Вдохновляющий и мотивирующий
- Используй модную терминологию, но объясняй сложные понятия
- Будь конкретным: вместо "носи что-то яркое" → "попробуй блейзер в оттенке electric blue"
- Используй эмодзи умеренно для структуры (✨, 👗, 💫, 🎨)

При анализе фото:
- Детально описывай что видишь
- Выделяй удачные элементы
- Предлагай улучшения тактично
- Рекомендуй конкретные альтернативы."""

# ----------------- Хранилище истории -----------------
user_conversations = {}

# ----------------- Вспомогательная функция для DeepSeek -----------------
def call_deepseek(messages):
    payload = {
        "model": "deepseek-chat",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024
    }
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    response = httpx.post(API_URL, headers=headers, json=payload, timeout=60)
    if response.status_code == 400:
        raise ValueError(f"❌ Ошибка 400: {response.text}")
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]

# ----------------- Формирование новостей с выжимкой -----------------
def summarize_news(news_items, batch_size=5):
    """
    Берет список новостей и формирует краткую выжимку через DeepSeek.
    batch_size — сколько новостей за один вызов, чтобы не превышать лимит.
    """
    summaries = []
    for i in range(0, len(news_items), batch_size):
        batch = news_items[i:i + batch_size]
        messages = [
            {"role": "system", "content": "Ты — AI-стилист и журналист моды. Сделай краткую выжимку из каждой новости в 1–2 предложения."}
        ]
        for news in batch:
            messages.append({
                "role": "user",
                "content": f"Новость: {news['title']} ({news['url']})"
            })
        try:
            summary = call_deepseek(messages)
            summaries.extend(summary.split("\n"))
        except Exception as e:
            summaries.extend([f"⚠️ Не удалось получить выжимку для этого пакета: {e}"])
    return summaries

def format_fashion_news():
    """
    Собирает данные с парсеров и формирует текст для Telegram.
    Каждая новость — с кликабельным заголовком и краткой выжимкой.
    """
    raw_updates = get_all_fashion_updates()
    sections = raw_updates.split("\n\n")

    news_items = []
    for section in sections:
        if not section.strip():
            continue
        lines = section.split("\n")
        for line in lines[1:]:
            if "|" in line:
                title, url = map(str.strip, line.split("|", 1))
            else:
                title, url = line.strip(), "#"
            news_items.append({"title": title, "url": url})

    # Получаем краткие выжимки
    summaries = summarize_news(news_items)

    # Формируем Markdown сообщение
    final_lines = []
    for item, summary in zip(news_items, summaries):
        final_lines.append(f"• [{item['title']}]({item['url']}) — {summary}")

    return "📰 **Новости моды с краткой выжимкой:**\n\n" + "\n\n".join(final_lines)

# ----------------- Обработчики -----------------
async def trends(update: Update, context):
    await update.message.reply_text("⏳ Собираю свежие модные новости и делаю краткую выжимку...")
    try:
        summary_text = format_fashion_news()
        await update.message.reply_text(summary_text, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка при формировании трендов: {e}")

async def start(update: Update, context):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    user_conversations[user_id] = []
    welcome_message = f"""👋 Привет, {user_name}! Я — твой Fashion AI Agent! 
Отправь текст или фото, чтобы получить советы по стилю."""
    await update.message.reply_text(welcome_message)

async def help_command(update: Update, context):
    help_text = """💡 Примеры вопросов:
- Как подобрать одежду на вечер?
- Оцени мой образ на фото.
- Дай советы по стилю для зимы."""
    await update.message.reply_text(help_text)

async def clear_history(update: Update, context):
    user_id = update.effective_user.id
    user_conversations[user_id] = []
    await update.message.reply_text("✨ История диалога очищена!")

# ----------------- Текстовые сообщения -----------------
keywords = ["мода", "новости моды", "fashion", "тренды"]

async def handle_message(update: Update, context):
    user_id = update.effective_user.id
    user_message = update.message.text
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    user_conversations[user_id].append({"role": "user", "content": user_message})
    await update.message.chat.send_action(ChatAction.TYPING)

    if any(word.lower() in user_message.lower() for word in keywords):
        try:
            summary_text = format_fashion_news()
            await update.message.reply_text(summary_text, parse_mode="Markdown")
        except Exception as e:
            await update.message.reply_text(f"⚠️ Ошибка при формировании трендов: {e}")
        return

    try:
        messages = [{"role": "system", "content": FASHION_SYSTEM_PROMPT}] + user_conversations[user_id]
        assistant_message = call_deepseek(messages)
        user_conversations[user_id].append({"role": "assistant", "content": assistant_message})
        if len(user_conversations[user_id]) > 20:
            user_conversations[user_id] = user_conversations[user_id][-20:]
        await update.message.reply_text(assistant_message)
    except Exception as e:
        await update.message.reply_text(f"😔 Произошла ошибка: {e}\nПопробуйте /clear")
        print(f"Error: {e}")

# ----------------- Фото сообщения -----------------
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

        caption = update.message.caption or "Проанализируй этот образ детально"
        user_conversations[user_id].append(
            {"role": "user", "content": f"{caption}\n[Фото прикреплено]"}
        )

        await update.message.chat.send_action(ChatAction.TYPING)
        messages = [{"role": "system", "content": FASHION_SYSTEM_PROMPT}] + user_conversations[user_id]
        assistant_message = call_deepseek(messages)
        user_conversations[user_id].append({"role": "assistant", "content": assistant_message})
        if len(user_conversations[user_id]) > 20:
            user_conversations[user_id] = user_conversations[user_id][-20:]
        await update.message.reply_text(assistant_message)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка обработки фото: {e}\nПопробуйте отправить уменьшенное фото.")
        print(f"Photo error: {e}")

# ----------------- Основная функция -----------------
def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear_history))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CommandHandler("trends", trends))
    app.run_polling()

if __name__ == "__main__":
    main()
