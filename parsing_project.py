import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import pandas as pd
import os

# 1. Настройки
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
BASE_URL = "https://quotes.toscrape.com/"

def get_html(url):
    """Скачивает HTML страницы с защитой от ошибок."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"[-] Ошибка загрузки {url}: {e}")
        return None

def parse_page(html):
    """Извлекает данные (цитаты, авторы, теги) из HTML."""
    soup = BeautifulSoup(html, "html.parser")
    quotes_data = []
    
    # Ищем все блоки с цитатами
    rows = soup.select("div.quote")
    
    for row in rows:
        text_el = row.select_one("span.text")
        author_el = row.select_one("small.author")
        
        # Проверка на наличие элементов (защита от нестандартной верстки)
        text = text_el.text.strip() if text_el else ""
        author = author_el.text.strip() if author_el else "Неизвестен"
        
        # Собираем теги в список
        tags = [t.text.strip() for t in row.select("div.tags a.tag")]
        
        quotes_data.append({
            "text": text,
            "author": author,
            "tag": tags,
        })
        
    return quotes_data, soup

def main():
    all_quotes = []
    url = BASE_URL
    
    # Ограничиваем парсинг 5 страницами (для демонстрации)
    for page_num in range(1, 6): 
        print(f"[*] Парсим страницу {page_num}...")
        
        html = get_html(url)
        if not html:
            break
            
        page_data, soup = parse_page(html)
        all_quotes.extend(page_data)

        # Ищем кнопку "Следующая страница"
        next_btn = soup.select_one("li.next a")
        if next_btn:
            url = urljoin(url, next_btn["href"])
        else:
            print("[*] Дальнейших страниц нет.")
            break
            
        time.sleep(1) # Пауза, чтобы не забанили

    print(f"[+] Всего собрано записей: {len(all_quotes)}")
    return all_quotes

def save_to_excel(quotes, filename="quotes_filtered.xlsx"):
    """Фильтрует цитаты и сохраняет в Excel."""
    if not quotes:
        print("[-] Нет данных для сохранения.")
        return

    # Фильтрация: оставляем только цитаты с > 2 тегов
    filtered_quotes = [q for q in quotes if len(q["tag"]) > 2]
    print(f"[*] Цитат с тегами более 2: {len(filtered_quotes)}")
    
    if not filtered_quotes:
        print("[-] Подходящих цитат не найдено.")
        return

    df = pd.DataFrame(filtered_quotes)
    # Превращаем список тегов в красивую строку через запятую
    df["tag"] = df["tag"].apply(lambda x: ", ".join(x))
    
    # Удаляем старый файл, если он есть, чтобы не путать данные
    if os.path.exists(filename):
        os.remove(filename)
        
    df.to_excel(filename, index=False)
    print(f"[+] Данные успешно сохранены в файл: {filename}")

if __name__ == "__main__":
    quotes = main()
    save_to_excel(quotes)