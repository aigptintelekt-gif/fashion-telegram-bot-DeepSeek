import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_site(url, selectors, site_name, max_items=10):
    """
    Универсальная функция парсинга сайта.
    Возвращает список заголовков с активными ссылками (Markdown).
    """
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
            if link:
                if not link.startswith("http"):
                    link = url.rstrip("/") + link
                items.append(f"[{text}]({link})")
            else:
                items.append(text)

        if not items:
            print(f"⚠️ {site_name}: не найдено заголовков по селекторам {selectors}")
            return None

        print(f"✅ {site_name}: найдено {len(items)} заголовков")
        return f"✨ **{site_name}**\n" + "\n".join(items)

    except Exception as e:
        print(f"❌ {site_name}: ошибка {e}")
        return None
def fetch_article_text(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Собираем весь текст статьи
        paragraphs = soup.find_all("p")
        text = "\n".join([p.get_text(strip=True) for p in paragraphs])
        return text[:3000]  # ограничиваем для LLM, чтобы не перегружать
    except Exception as e:
        print(f"Ошибка при парсинге статьи {url}: {e}")
        return ""

# ----------------- Источники модных новостей -----------------
def fetch_wgsn():
    return fetch_site("https://www.wgsn.com/en", "h2, h3 a", "WGSN")

def fetch_coloro():
    return fetch_site("https://coloro.com/", "h2, h3 a", "Coloro")

def fetch_bof():
    return fetch_site("https://www.businessoffashion.com/", "h3 a", "Business of Fashion")

def fetch_nike():
    return fetch_site("https://about.nike.com/en/newsroom", "h2 a", "Nike News")

def fetch_footy():
    return fetch_site("https://www.footyheadlines.com/", "h3 a", "FootyHeadlines")

def fetch_sports_style():
    return fetch_site("https://www.sports.ru/style/", "h2 a, h3 a", "Sports.ru — Стиль")

def fetch_wwd():
    return fetch_site("https://wwd.com/", "h3 a", "WWD")

def fetch_blueprint():
    return fetch_site("https://theblueprint.ru/", "h2 a, h3 a", "Blueprint")

# ----------------- Сбор всех новостей -----------------
def get_all_fashion_updates():
    updates = [
        fetch_wgsn(),
        fetch_coloro(),
        fetch_bof(),
        fetch_nike(),
        fetch_footy(),
        fetch_sports_style(),
        fetch_wwd(),
        fetch_blueprint(),
    ]
    # Убираем None
    filtered = [u for u in updates if u]
    return "\n\n".join(filtered) if filtered else "Нет свежих модных новостей 😔"

# ----------------- Тест парсера -----------------
if __name__ == "__main__":
    print("🚀 Проверка парсера модных новостей:")
    news = get_all_fashion_updates()
    print(news)
