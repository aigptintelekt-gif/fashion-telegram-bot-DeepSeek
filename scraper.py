import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import os
import httpx
import base64

YANDEX_API_KEY = os.environ.get("YANDEX_API_KEY")
YANDEX_REGION = os.environ.get("YANDEX_REGION")
YANDEX_TEXT_MODEL = "general-text-summarizer"

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ----------------- Функции парсинга -----------------
def fetch_site(url, selectors, site_name, max_items=5):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        items = []

        for x in soup.select(selectors)[:max_items]:
            text = x.get_text(strip=True)
            link = x.get("href")
            if not text:
                continue
            if link and not link.startswith("http"):
                link = urljoin(url, link)
            items.append({"title": text, "url": link or url})

        return {"site": site_name, "articles": items} if items else None
    except Exception as e:
        print(f"❌ {site_name}: ошибка {e}")
        return None


def fetch_article_text(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all("p")
        text = "\n".join([p.get_text(strip=True) for p in paragraphs])
        return text[:3000]
    except Exception as e:
        print(f"❌ Ошибка при парсинге статьи {url}: {e}")
        return ""


# ----------------- Сбор новостей -----------------
def get_sources():
    return [
        fetch_site("https://www.wgsn.com/en", "h2 a, h3 a", "WGSN"),
        fetch_site("https://coloro.com/", "h2 a, h3 a", "Coloro"),
        fetch_site("https://www.businessoffashion.com/", "h3 a", "Business of Fashion"),
        fetch_site("https://about.nike.com/en/newsroom", "h2 a", "Nike News"),
        fetch_site("https://www.footyheadlines.com/", "h3 a", "FootyHeadlines"),
        fetch_site("https://www.sports.ru/style/", "h2 a, h3 a", "Sports.ru — Стиль"),
        fetch_site("https://wwd.com/", "h3 a", "WWD"),
        fetch_site("https://theblueprint.ru/", "h2 a, h3 a", "Blueprint"),
    ]


# ----------------- Генерация кратких выжимок через YandexGPT -----------------
def summarize_articles_with_yandex(articles):
    url = f"https://{YANDEX_REGION}.api.cloud.yandex.net/ai/v1/models/{YANDEX_TEXT_MODEL}:predict"
    headers = {"Authorization": f"Bearer {YANDEX_API_KEY}"}
    summaries = []

    for art in articles:
        text = art.get("text") or ""
        if not text:
            continue

        prompt = f"Ты AI-стилист и журналист моды. Сделай краткую выжимку:\nЗаголовок: {art['title']}\nСсылка: {art['url']}\nТекст: {text}"

        payload = {"instances": [{"text": prompt}]}

        try:
            response = httpx.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            summary_text = data.get("predictions", [{}])[0].get("output_text", "")
            if not summary_text:
                summary_text = f"{art['title']} — краткая выжимка недоступна"
        except Exception as e:
            print(f"❌ YandexGPT ошибка для {art['title']}: {e}")
            summary_text = f"{art['title']} — ошибка при генерации"

        summaries.append(f"• [{art['title']}]({art['url']}): {summary_text}")

    return "\n".join(summaries)


def get_fashion_news_with_summary():
    sources = get_sources()
    news_summaries = []

    for src in sources:
        if not src:
            continue
        articles = src["articles"]
        for art in articles:
            art["text"] = fetch_article_text(art["url"])
        summary = summarize_articles_with_yandex(articles)
        news_summaries.append(f"✨ **{src['site']}**\n{summary}")

    return "\n\n".join(news_summaries) if news_summaries else "Нет свежих модных новостей 😔"


if __name__ == "__main__":
    print("🚀 Проверка парсера с YandexGPT:")
    news = get_fashion_news_with_summary()
    print(news)
