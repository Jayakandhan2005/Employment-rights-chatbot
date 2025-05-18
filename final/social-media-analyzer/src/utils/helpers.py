import streamlit as st
import requests
import time
import random
import json
import pandas as pd
import feedparser
import urllib.parse
from datetime import datetime, timedelta
from textblob import TextBlob
import nltk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from nltk.sentiment import SentimentIntensityAnalyzer
import plotly.express as px
import plotly.graph_objects as go
import base64
from datetime import datetime
import pandas as pd
from textblob import TextBlob
from nltk.sentiment import SentimentIntensityAnalyzer
import textwrap
import hashlib
from collections import defaultdict
import re
from groq import Groq

# Import scraping functions
from services.scraper import (
    scrape_twitter,
    scrape_reddit, 
    scrape_youtube,
    scrape_instagram,
    scrape_news
)
def process_data(keyword):
    with st.spinner('Gathering social media data...'):
        progress_bar = st.progress(0)
        st.markdown("""
        <div class="loading-animation">
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
            <div class="loading-dot"></div>
        </div>
        """, unsafe_allow_html=True)
        
        twitter_data = scrape_twitter(keyword)
        progress_bar.progress(20)
        
        reddit_data = scrape_reddit(keyword)
        progress_bar.progress(40)
        
        youtube_data = scrape_youtube(keyword)
        progress_bar.progress(60)
        
        instagram_data = scrape_instagram(keyword)
        progress_bar.progress(80)
        
        news_data = scrape_news(keyword)
        progress_bar.progress(100)
        
        all_data = twitter_data + reddit_data + youtube_data + instagram_data + news_data
        
        # URL-based deduplication
        seen_urls = set()
        deduped_data = []
        for post in all_data:
            if post['url'] not in seen_urls:
                deduped_data.append(post)
                seen_urls.add(post['url'])
        
        st.markdown('<div style="height: 40px;"></div>', unsafe_allow_html=True)
        
        return deduped_data
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

# ...rest of your existing functions...
def display_metrics(sentiment_data):
     st.markdown('<div class="metrics-row">', unsafe_allow_html=True)
    
    # Total Posts
     st.markdown(f'''
    <div class="metric-box total">
        <div class="metric-label">Total Mentions</div>
        <div class="metric-value">{sentiment_data["total_posts"]}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Positive Posts
     positive_pct = round(sentiment_data["positive_count"]/sentiment_data["total_posts"]*100) if sentiment_data["total_posts"] > 0 else 0
     st.markdown(f'''
    <div class="metric-box positive">
        <div class="metric-label">Positive Sentiment</div>
        <div class="metric-value positive">{positive_pct}%</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Negative Posts
     negative_pct = round(sentiment_data["negative_count"]/sentiment_data["total_posts"]*100) if sentiment_data["total_posts"] > 0 else 0
     st.markdown(f'''
    <div class="metric-box negative">
        <div class="metric-label">Negative Sentiment</div>
        <div class="metric-value negative">{negative_pct}%</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Brand Score
     st.markdown(f'''
    <div class="metric-box score">
        <div class="metric-label">Brand Score</div>
        <div class="metric-value">{sentiment_data["brand_score"]}/100</div>
    </div>
    ''', unsafe_allow_html=True)
    
     st.markdown('</div>', unsafe_allow_html=True)
 


def get_sentiment_label(polarity):
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"

def format_content(content, max_lines=3, max_length=250):
    cleaned = ' '.join(content.split())
    wrapped = textwrap.fill(cleaned, width=60)
    lines = wrapped.split('\n')[:max_lines]
    truncated = '\n'.join(lines)
    if len(truncated) > max_length:
        truncated = truncated[:max_length].rsplit(' ', 1)[0] + '...'
    return truncated

def parse_datetime(dt_str):
    try:
        formats = [
            "%a, %d %b %Y %H:%M:%S %Z",
            "%a, %d %b %Y %H:%M:%S %z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%a %b %d %H:%M:%S %Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(dt_str, fmt)
            except ValueError:
                continue
        
        try:
            from dateutil.parser import parse
            return parse(dt_str)
        except ImportError:
            pass
        
        return datetime.now()
    except:
        return datetime.now()

def detect_duplicates(data):
    """
    Fast duplicate detection using text similarity and pattern matching.
    Returns data in the format expected by the display functions.
    """
    try:
        # Limit the number of posts to analyze
        MAX_POSTS = 50
        data = data[:MAX_POSTS]
        
        # Initialize result structure
        result = {
            'duplicate_groups': [],
            'cross_platform_groups': [],
            'spam_posts': []
        }

        # Create normalized content for comparison
        processed_posts = []
        for post in data:
            # Normalize content for comparison
            content = post['content'].lower().strip()
            # Remove URLs
            content = re.sub(r'http\S+|www.\S+', '', content)
            # Remove special characters and extra spaces
            content = re.sub(r'[^\w\s]', '', content)
            content = ' '.join(content.split())
            
            processed_posts.append({
                'post': post,
                'normalized_content': content,
                'words': set(content.split())
            })

        # Find duplicates using word overlap
        seen_pairs = set()
        for i, post1 in enumerate(processed_posts):
            for j, post2 in enumerate(processed_posts[i+1:], i+1):
                if (i, j) in seen_pairs:
                    continue
                    
                # Calculate word overlap ratio
                common_words = post1['words'] & post2['words']
                total_words = len(post1['words'] | post2['words'])
                
                if total_words > 0:
                    similarity = len(common_words) / total_words
                    
                    # If content is very similar
                    if similarity > 0.7:  # 70% similarity threshold
                        if post1['post']['platform'] == post2['post']['platform']:
                            # Add to duplicate groups
                            result['duplicate_groups'].append({
                                'posts': [post1['post'], post2['post']],
                                'platform': post1['post']['platform'],
                                'similarity': round(similarity * 100, 2)
                            })
                        else:
                            # Add to cross-platform groups
                            result['cross_platform_groups'].append({
                                'posts': [post1['post'], post2['post']],
                                'platforms': [post1['post']['platform'], post2['post']['platform']],
                                'similarity': round(similarity * 100, 2)
                            })
                        seen_pairs.add((i, j))

        # Quick spam detection using simple patterns
        spam_patterns = {
            'promotional': r'(buy|discount|offer|sale|promo|click here|limited time)',
            'suspicious_urls': r'bit\.ly|tinyurl|goo\.gl',
            'spam_phrases': r'(make money|work from home|earn \$|100% free)'
        }

        for post in data:
            content = post['content'].lower()
            for spam_type, pattern in spam_patterns.items():
                if re.search(pattern, content):
                    # Add to spam posts
                    result['spam_posts'].append({
                        'post': post,
                        'type': spam_type,
                        'platform': post['platform']
                    })
                    break  # One spam type per post is enough

        # Ensure we have the minimum required structure even if empty
        if not result['duplicate_groups']:
            result['duplicate_groups'] = []
        if not result['cross_platform_groups']:
            result['cross_platform_groups'] = []
        if not result['spam_posts']:
            result['spam_posts'] = []

        return result

    except Exception as e:
        st.error(f"Error in duplicate detection: {str(e)}")
        # Return empty structure in case of error
        return {
            'duplicate_groups': [],
            'cross_platform_groups': [],
            'spam_posts': []
        }

    