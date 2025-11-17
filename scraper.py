import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_wgsn():
    url = "https://www.wgsn.com/en"
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        items = [x.get_text(strip=True) for x in soup.select("h2, h3")][:10]
        return "WGSN:\n" + "\n".join(items)
    except Exception as e:
        return f"WGSN: ошибка: {e}"


def fetch_coloro():
    url = "https://coloro.com/"
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        items = [x.get_text(strip=True) for x in soup.select("h2, h3")][:10]
        return "Coloro:\n" + "\n".join(items)
    except Exception as e:
        return f"Coloro: ошибка: {e}"


def fetch_bof():
    url = "https://www.businessoffashion.com/"
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        articles = [x.get_text(strip=True) for x in soup.select("h3")][:10]
        return "Business of Fashion:\n" + "\n".join(articles)
    except Exception as e:
        return f"BoF: ошибка: {e}"


def fetch_nike():
    url = "https://about.nike.com/en/newsroom"
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        titles = [x.get_text(strip=True) for x in soup.select("h2")][:10]
        return "Nike News:\n" + "\n".join(titles)
    except Exception as e:
        return f"Nike: ошибка: {e}"


def fetch_footy():
    url = "https://www.footyheadlines.com/"
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        titles = [x.get_text(strip=True) for x in soup.select("h3")][:10]
        return "FootyHeadlines:\n" + "\n".join(titles)
    except Exception as e:
        return f"Footy: ошибка: {e}"


def fetch_sports_style():
    url = "https://www.sports.ru/style/"
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        titles = [x.get_text(strip=True) for x in soup.select("h2, h3")][:10]
        return "Sports.ru — Стиль:\n" + "\n".join(titles)
    except Exception as e:
        return f"Sports: ошибка: {e}"


def fetch_wwd():
    url = "https://wwd.com/"
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        titles = [x.get_text(strip=True) for x in soup.select("h3")][:10]
        return "WWD:\n" + "\n".join(titles)
    except Exception as e:
        return f"WWD: ошибка: {e}"


def fetch_blueprint():
    url = "https://theblueprint.ru/"
    try:
        html = requests.get(url, headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        titles = [x.get_text(strip=True) for x in soup.select("h2, h3")][:10]
        return "Blueprint:\n" + "\n".join(titles)
    except Exception as e:
        return f"Blueprint: ошибка: {e}"


def get_all_fashion_updates():
    return "\n\n".join([
        fetch_wgsn(),
        fetch_coloro(),
        fetch_bof(),
        fetch_nike(),
        fetch_footy(),
        fetch_sports_style(),
        fetch_wwd(),
        fetch_blueprint(),
    ])
