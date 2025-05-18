import random
from datetime import datetime
from textblob import TextBlob

def get_random_headers():
    """Generate random headers for web requests"""
    return {
        'User-Agent': random.choice([
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        ]),
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://www.google.com/'
    }

def get_sentiment_label(polarity):
    """Convert polarity score to sentiment label"""
    if polarity > 0.1:
        return 'Positive'
    elif polarity < -0.1:
        return 'Negative'
    return 'Neutral'

def format_content(text):
    """Clean and format content text"""
    return text.strip()

def parse_datetime(date_str):
    """Parse datetime from string"""
    try:
        return datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z')
    except:
        return datetime.now()