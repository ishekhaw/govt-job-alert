import requests
from bs4 import BeautifulSoup
from db import save_job
from scrapers.utils import extract_date, is_within_last_month

def scrape_toi_news():
    """Scrape education news from Times of India"""
    url = 'https://timesofindia.indiatimes.com/education/news'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        all_links = soup.find_all('a', href=True)
        
        news_items = []
        for link in all_links:
            href = link['href']
            text = link.get_text().strip()
            
            # Filter for education/news related links
            if (('education' in href.lower() or 'news' in href.lower() or 'result' in href.lower()) 
                and len(text) > 10 and not text.startswith(('http', 'https'))):
                
                if not href.startswith('http'):
                    href = 'https://timesofindia.indiatimes.com' + href
                
                # Check if it's a recent news item (within last month)
                # For news, we'll assume they're recent if they contain result-related keywords
                if any(keyword in text.lower() for keyword in ['result', 'exam', 'board', 'cbse', 'icse', 'admit', 'answer']):
                    news_items.append({
                        'title': text,
                        'link': href,
                        'source': 'TOI'
                    })
                    
                    if len(news_items) >= 10:  # Limit to 10 news items
                        break
        
        # Save news items to database with a special source
        for item in news_items:
            save_job(
                title=item['title'],
                link=item['link'],
                source='TOI_NEWS',
                description=f"Education news from Times of India: {item['title']}"
            )
            
        print(f"Scraped {len(news_items)} education news items from Times of India")
        
    except Exception as e:
        print(f"Error scraping Times of India news: {e}")