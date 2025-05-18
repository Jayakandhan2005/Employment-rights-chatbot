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
from groq import Groq
import textwrap
import hashlib
from collections import defaultdict
import re
from utils.common import (
    get_random_headers,
    get_sentiment_label,
    format_content,
    parse_datetime
)



def scrape_twitter(keyword):
    posts = []
    try:
        search_query = f"{keyword} review OR issue OR problem OR bug OR crash site:twitter.com"
        encoded_query = urllib.parse.quote(search_query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:100]:
            try:
                content = entry.title
                if keyword.lower() not in content.lower():
                    continue
                
                # Extract username from Twitter URL
                username = 'N/A'
                if 'twitter.com' in entry.link:
                    parts = entry.link.split('/')
                    if len(parts) > 3:
                        username = parts[3]
                
                analysis = TextBlob(content)
                polarity = round(analysis.sentiment.polarity, 2)
                sentiment = get_sentiment_label(polarity)

                # Estimate engagement (likes + retweets)
                engagement = "N/A"
                if "retweets" in content.lower() or "likes" in content.lower():
                    engagement_parts = content.split("·")
                    if len(engagement_parts) > 1:
                        engagement = engagement_parts[-1].strip()

                posts.append({
                    'platform': 'Twitter',
                    'username': username,
                    'content': format_content(content),
                    'engagement': engagement,
                    'timestamp': parse_datetime(entry.published) if hasattr(entry, 'published') else datetime.now(),
                    'url': entry.link,
                    'sentiment': sentiment,
                    'polarity': polarity
                })
            except: continue
    except Exception as e:
        st.error(f"Twitter Error: {str(e)}")
    return posts

def scrape_reddit(keyword):
    """Scrape Reddit using official JSON API with sentiment analysis"""
    posts = []
    try:
        # Use both search and subreddit endpoints for better coverage
        urls = [
            f"https://www.reddit.com/search.json?q={keyword}+review+OR+issue&sort=hot&limit=25",
            f"https://www.reddit.com/r/all/search.json?q={keyword}&sort=hot&limit=25"
        ]
        
        for url in urls:
            response = requests.get(url, headers=get_random_headers(), timeout=15)
            response.raise_for_status()
            
            data = response.json()
            for post in data['data']['children']:
                try:
                    pdata = post['data']
                    title = pdata['title'].strip()
                    selftext = pdata.get('selftext', '').strip()
                    
                    # Format content to be concise
                    if selftext:
                        # Take first 2-3 sentences from selftext
                        sentences = re.split(r'[.!?]+', selftext)
                        relevant_text = ' '.join(sentences[:3]).strip()
                        # Truncate if still too long
                        if len(relevant_text) > 200:
                            relevant_text = relevant_text[:197] + "..."
                        content = f"{title}\n{relevant_text}"
                    else:
                        content = title
                    
                    # Ensure content is not too long
                    if len(content) > 300:
                        content = content[:297] + "..."
                    
                    # Analyze sentiment
                    analysis = TextBlob(content)
                    polarity = round(analysis.sentiment.polarity, 2)
                    sentiment = get_sentiment_label(polarity)
                    
                    # Format engagement count
                    engagement = pdata.get('score', 0)
                    if engagement > 1000:
                        engagement = f"{round(engagement/1000, 1)}k"
                    
                    # Clean and format the content
                    formatted_content = content.replace('\n\n', '\n').strip()
                    
                    posts.append({
                        'platform': 'Reddit',
                        'username': pdata.get('author', 'anonymous'),
                        'content': formatted_content,
                        'engagement': engagement,
                        'timestamp': datetime.fromtimestamp(pdata['created_utc']),
                        'url': f"https://reddit.com{pdata['permalink']}",
                        'sentiment': sentiment,
                        'polarity': polarity,
                        'subreddit': pdata.get('subreddit', '')
                    })
                except Exception as e:
                    continue
                    
    except Exception as e:
        st.error(f"Reddit Error: {str(e)}")
    
    # Remove duplicates based on content
    seen_content = set()
    unique_posts = []
    for post in posts:
        content = post['content'].lower()
        if content not in seen_content:
            seen_content.add(content)
            unique_posts.append(post)
    
    return unique_posts[:25]  # Return top 25 unique posts

def scrape_youtube(keyword):
    posts = []
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"user-agent={get_random_headers()['User-Agent']}")

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get(f"https://www.youtube.com/results?search_query={keyword}+issue+problem")
        time.sleep(5)  # Wait for the page to load

        # Locate video elements
        videos = driver.find_elements(By.XPATH, "//ytd-video-renderer//a[@id='video-title']")
        for video in videos[:50]:  # Limit to 50 videos
            try:
                title = video.text
                link = video.get_attribute("href")
                
                # Use TextBlob for sentiment analysis, consistent with other scrapers
                analysis = TextBlob(title)
                polarity = round(analysis.sentiment.polarity, 2)
                sentiment = get_sentiment_label(polarity)

                # Get view count if available
                view_count = "N/A"
                metadata = video.find_elements(By.XPATH, ".//..//..//div[@id='metadata-line']/span")
                if len(metadata) > 0:
                    view_count = metadata[0].text

                posts.append({
                    'platform': 'YouTube',
                    'content': format_content(title),
                    'engagement': view_count,
                    'timestamp': datetime.now(),
                    'url': link,
                    'sentiment': sentiment,
                    'polarity': polarity
                })
            except Exception as e:
                print(f"Error processing video: {e}")
                continue
        driver.quit()
    except Exception as e:
        st.error(f"YouTube Error: {str(e)}")
    return posts

def scrape_instagram(keyword):
    posts = []
    try:
        search_query = f"site:instagram.com {keyword} issue OR problem OR bug"
        encoded_query = urllib.parse.quote(search_query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        feed = feedparser.parse(rss_url)
        seen_urls = set()
        for entry in feed.entries[:100]:
            try:
                if entry.link in seen_urls:
                    continue
                seen_urls.add(entry.link)
                
                content = entry.title
                username = 'N/A'
                if 'instagram.com' in entry.link:
                    parts = entry.link.split('/')
                    if len(parts) > 3:
                        username = parts[3]
                
                analysis = TextBlob(content)
                polarity = round(analysis.sentiment.polarity, 2)
                sentiment = get_sentiment_label(polarity)
                
                # Estimate engagement (likes + comments)
                engagement = "N/A"
                if "likes" in content.lower() or "comments" in content.lower():
                    engagement_parts = content.split("·")
                    if len(engagement_parts) > 1:
                        engagement = engagement_parts[-1].strip()
                
                posts.append({
                    'platform': 'Instagram',
                    'username': username,
                    'content': format_content(content),
                    'engagement': engagement,
                    'timestamp': parse_datetime(entry.published) if hasattr(entry, 'published') else datetime.now(),
                    'url': entry.link,
                    'sentiment': sentiment,
                    'polarity': polarity
                })
            except: continue
    except Exception as e:
        st.error(f"Instagram Error: {str(e)}")
    return posts

def scrape_news(keyword):
    posts = []
    try:
        search_query = f"{keyword} issue OR problem OR bug OR recall OR controversy"
        encoded_query = urllib.parse.quote(search_query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:100]:
            try:
                content = entry.title
                analysis = TextBlob(content)
                polarity = round(analysis.sentiment.polarity, 2)
                sentiment = get_sentiment_label(polarity)
                
                posts.append({
                    'platform': 'News',
                    'username': 'N/A',
                    'content': format_content(content),
                    'engagement': 'Article',
                    'timestamp': parse_datetime(entry.published) if hasattr(entry, 'published') else datetime.now(),
                    'url': entry.link,
                    'sentiment': sentiment,
                    'polarity': polarity
                })
            except: 
                continue
    except Exception as e:
        st.error(f"News Error: {str(e)}")
    return posts

