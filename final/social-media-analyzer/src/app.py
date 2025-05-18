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
from views.display import (
    display_posts,
    display_crisis_posts,
    display_crisis_alert,
    display_duplicates,
    display_recommendations,
    display_response_templates,
    display_issue_detection
)
from utils.helpers import process_data, display_metrics, detect_duplicates
from services.analyzer import (
    analyze_sentiment,
    detect_crisis,
    generate_response_templates_with_groq,
    detect_issues_with_groq,
    generate_recommendations_with_groq
)
from utils.charts import (
    create_sentiment_distribution_chart,
    create_sentiment_trend_chart,
    create_platform_distribution_chart
)
# ...existing imports...

# Configure Streamlit with wider layout
st.set_page_config(
    page_title="BRAMS - Reputation Management System", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Groq client
client = Groq(api_key="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")

# Download NLTK resources
try:
    nltk.download("vader_lexicon", quiet=True)
    sia = SentimentIntensityAnalyzer()
except Exception as e:
    st.error(f"Error setting up NLTK: {str(e)}")
    

# Modern Social Media Icons as SVG (embedded in Base64 to avoid external dependencies)
SOCIAL_ICONS = {
    'Twitter': """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="#1DA1F2">
            <path d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"/>
        </svg>
    """,
    'Reddit': """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="#FF4500">
            <path d="M12 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0zm5.01 4.744c.688 0 1.25.561 1.25 1.249a1.25 1.25 0 0 1-2.498.056l-2.597-.547-.8 3.747c1.824.07 3.48.632 4.674 1.488.308-.309.73-.491 1.207-.491.968 0 1.754.786 1.754 1.754 0 .716-.435 1.333-1.01 1.614a3.111 3.111 0 0 1 .042.52c0 2.694-3.13 4.87-7.004 4.87-3.874 0-7.004-2.176-7.004-4.87 0-.183.015-.366.043-.534A1.748 1.748 0 0 1 4.028 12c0-.968.786-1.754 1.754-1.754.463 0 .898.196 1.207.49 1.207-.883 2.878-1.43 4.744-1.487l.885-4.182a.342.342 0 0 1 .14-.197.35.35 0 0 1 .238-.042l2.906.617a1.214 1.214 0 0 1 1.108-.701zM9.25 12C8.561 12 8 12.562 8 13.25c0 .687.561 1.248 1.25 1.248.687 0 1.248-.561 1.248-1.249 0-.688-.561-1.249-1.249-1.249zm5.5 0c-.687 0-1.248.561-1.248 1.25 0 .687.561 1.248 1.249 1.248.688 0 1.249-.561 1.249-1.249 0-.687-.562-1.249-1.25-1.249zm-5.466 3.99a.327.327 0 0 0-.231.094.33.33 0 0 0 0 .463c.842.842 2.484.913 2.961.913.477 0 2.105-.056 2.961-.913a.361.361 0 0 0 .029-.463.33.33 0 0 0-.464 0c-.547.533-1.684.73-2.512.73-.828 0-1.979-.196-2.512-.73a.326.326 0 0 0-.232-.095z"/>
        </svg>
    """,
    'YouTube': """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="#FF0000">
            <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
        </svg>
    """,
    'Instagram': """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="#E1306C">
            <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
        </svg>
    """,
    'News': """
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="#2B6CB0">
            <path d="M7 13h10v1H7zm0-4h5v1H7zm10 8H7v-1h10zm2-13v18H5V4h14zm2-2H3v22h18V2z"/>
        </svg>
    """
}

# Enhanced CSS styling with animations
st.markdown("""
<style>
/* Google Fonts Import */
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

/* General Styles */
.stApp {
    font-family: 'Poppins', sans-serif;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

/* Animated Header */
.main-header {
    background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    color: white;
    margin-bottom: 30px;
    position: relative;
    overflow: hidden;
    transition: all 0.3s ease;
}

.main-header:hover {
    transform: translateY(-5px);
}

.main-header:after {
    content: "";
    position: absolute;
    top: 0;
    left: -50%;
    width: 200%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
    transform: skewX(-25deg);
    animation: shine 3s infinite;
}

@keyframes shine {
    0% { left: -100%; }
    100% { left: 100%; }
}

.header-title {
    font-size: 2.5rem;
    font-weight: 700;
    margin-bottom: 5px;
}

.header-subtitle {
    font-weight: 300;
    opacity: 0.8;
}

/* Animated Post Cards */
.post-card { 
    padding: 20px;
    margin: 15px 0;
    border-radius: 15px;
    background: #ffffff;
    box-shadow: 0 8px 20px rgba(0,0,0,0.05);
    transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    border-top: 5px solid transparent;
}

.post-card:hover { 
    transform: translateY(-5px);
    box-shadow: 0 15px 30px rgba(0,0,0,0.1);
}

.twitter:hover { border-top-color: #1DA1F2; }
.reddit:hover { border-top-color: #FF4500; }
.youtube:hover { border-top-color: #FF0000; }
.instagram:hover { border-top-color: #E1306C; }
.news:hover { border-top-color: #2B6CB0; }

.platform-tag {
    font-size: 0.8em;
    padding: 6px 15px;
    border-radius: 30px;
    display: inline-flex;
    align-items: center;
    margin-bottom: 15px;
    font-weight: 500;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
}

.twitter { background: #1DA1F210; border-left: 4px solid #1DA1F2; }
.reddit { background: #FF450010; border-left: 4px solid #FF4500; }
.youtube { background: #FF000010; border-left: 4px solid #FF0000; }
.instagram { background: #E1306C10; border-left: 4px solid #E1306C; }
.news { background: #2B6CB010; border-left: 4px solid #2B6CB0; }

.icon-container {
    display: inline-flex;
    align-items: center;
    margin-right: 10px;
}

/* Content Styling */
.post-content {
    white-space: pre-line;
    line-height: 1.5;
    max-height: 4.5em; /* 3 lines * 1.5 line-height */
    overflow: hidden;
    text-overflow: ellipsis;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
}

/* Enhanced Metric Boxes with Animation */
.metrics-row {
    display: flex;
    flex-wrap: wrap;
    gap: 20px;
    margin-bottom: 30px;
}

.metric-box {
    padding: 25px;
    border-radius: 15px;
    background: white;
    flex: 1;
    min-width: 200px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.metric-box:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
}

.metric-box:after {
    content: "";
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 5px;
}

.metric-box.total:after { background: linear-gradient(90deg, #3498db, #2980b9); }
.metric-box.positive:after { background: linear-gradient(90deg, #2ecc71, #27ae60); }
.metric-box.negative:after { background: linear-gradient(90deg, #e74c3c, #c0392b); }
.metric-box.score:after { background: linear-gradient(90deg, #9b59b6, #8e44ad); }

.metric-value {
    font-size: 2.5rem;
    font-weight: 700;
    margin: 5px 0;
}

.metric-label {
    color: #666;
    font-size: 1rem;
    font-weight: 500;
}

/* Fancy Chart Container */
.chart-container {
    background: white;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 30px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    transition: all 0.3s ease;
    border-left: 5px solid #4b6cb7;
}

.chart-container:hover {
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
}

.chart-title {
    font-size: 1.2rem;
    font-weight: 600;
    margin-bottom: 15px;
    color: #333;
}

/* Loading Animation */
.loading-animation {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 40px;
}

.loading-dot {
    width: 12px;
    height: 12px;
    margin: 0 8px;
    border-radius: 50%;
    background-color: #4b6cb7;
    animation: pulse 1.5s infinite ease-in-out;
}

.loading-dot:nth-child(2) { animation-delay: 0.3s; }
.loading-dot:nth-child(3) { animation-delay: 0.6s; }

@keyframes pulse {
    0%, 100% { transform: scale(0.8); opacity: 0.5; }
    50% { transform: scale(1.2); opacity: 1; }
}

/* Sentiment Badge Styles */
.sentiment-badge {
    padding: 6px 12px;
    border-radius: 20px;
    font-size: 0.9em;
    font-weight: 500;
    display: inline-block;
    color: white; /* Text color */
}

.sentiment-badge.positive {
    background-color: #2ecc71; /* Green for positive sentiment */
}

.sentiment-badge.negative {
    background-color: #e74c3c; /* Red for negative sentiment */
}

.sentiment-badge.neutral {
    background-color: #95a5a6; /* Gray for neutral sentiment */
}

/* Crisis Alert Styles */
.crisis-alert {
    background: linear-gradient(90deg, #ff4d4d, #ff1a1a);
    color: white;
    padding: 20px;
    border-radius: 15px;
    margin-bottom: 30px;
    box-shadow: 0 10px 30px rgba(255,0,0,0.2);
    animation: pulse-alert 2s infinite;
}

@keyframes pulse-alert {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.02); }
}

.crisis-title {
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
}

.crisis-title svg {
    margin-right: 10px;
}

.crisis-metrics {
    display: flex;
    justify-content: space-between;
    margin-top: 15px;
}

.crisis-metric {
    text-align: center;
    padding: 10px;
    background: rgba(255,255,255,0.1);
    border-radius: 10px;
    flex: 1;
    margin: 0 5px;
}

.crisis-metric-value {
    font-size: 1.5rem;
    font-weight: 700;
}

.crisis-metric-label {
    font-size: 0.9rem;
    opacity: 0.9;
}

/* View Crisis Details Button */
.view-crisis-btn {
    display: inline-block;
    margin-top: 15px;
    padding: 8px 16px;
    background-color: white;
    color: #ff4d4d;
    border-radius: 5px;
    text-decoration: none;
    font-weight: 600;
    transition: all 0.3s ease;
}

.view-crisis-btn:hover {
    background-color: #f0f0f0;
    transform: translateY(-2px);
}

/* Crisis posts section */
.crisis-posts-section {
    margin-top: 30px;
    padding-top: 20px;
    border-top: 1px solid #eee;
    display: none;
}

.crisis-posts-section:target {
    display: block;
}

.crisis-section-title {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 20px;
    color: #333;
}

/* Issue Detection Section */
.issue-detection {
    background: white;
    border-radius: 15px;
    padding: 20px;
    margin-top: 30px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    border-left: 5px solid #4b6cb7;
}

.issue-header {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 20px;
    color: #333;
    display: flex;
    align-items: center;
}

.issue-header svg {
    margin-right: 10px;
}

.issue-card {
    padding: 15px;
    margin-bottom: 15px;
    border-radius: 10px;
    background: #f8f9fa;
    border-left: 4px solid #4b6cb7;
}

.issue-title {
    font-weight: 600;
    margin-bottom: 10px;
    color: #2c3e50;
    display: flex;
    align-items: center;
}

.issue-title svg {
    margin-right: 10px;
}

.issue-stats {
    display: flex;
    gap: 15px;
    margin-bottom: 10px;
}

.issue-stat {
    background: rgba(75,108,183,0.1);
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 0.9rem;
}

.issue-stat-value {
    font-weight: 700;
    color: #4b6cb7;
}

.recommendations {
    margin-top: 15px;
    padding-top: 15px;
    border-top: 1px dashed #ddd;
}

.recommendation {
    display: flex;
    align-items: flex-start;
    margin-bottom: 10px;
}

.recommendation-badge {
    background: #4b6cb7;
    color: white;
    border-radius: 50%;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 10px;
    flex-shrink: 0;
    font-size: 0.8rem;
}

.recommendation-content {
    flex: 1;
}

/* Response Templates Section - Enhanced */
.response-templates {
    background: white;
    border-radius: 15px;
    padding: 20px;
    margin-top: 30px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    border-left: 5px solid #4b6cb7;
}

.template-header {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 20px;
    color: #333;
    display: flex;
    align-items: center;
}

.template-header svg {
    margin-right: 10px;
}

.template-card {
    padding: 20px;
    margin-bottom: 20px;
    border-radius: 12px;
    background: #f8f9fa;
    border-left: 4px solid #4b6cb7;
    transition: all 0.3s ease;
    box-shadow: 0 3px 10px rgba(0,0,0,0.05);
}

.template-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}

.template-title {
    font-weight: 700;
    margin-bottom: 15px;
    color: #2c3e50;
    font-size: 1.2rem;
    display: flex;
    align-items: center;
}

.template-title svg {
    margin-right: 10px;
}

.template-content {
    white-space: pre-line;
    line-height: 1.6;
    margin-bottom: 15px;
    padding: 15px;
    background: white;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
}

.template-actions {
    display: flex;
    gap: 12px;
    margin-top: 15px;
}

.template-btn {
    padding: 8px 16px;
    border-radius: 6px;
    border: none;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 8px;
}

.template-btn svg {
    width: 16px;
    height: 16px;
}

.template-btn.edit {
    background: #3498db;
    color: white;
}

.template-btn.edit:hover {
    background: #2980b9;
    transform: translateY(-2px);
}

.template-btn.use {
    background: #2ecc71;
    color: white;
}

.template-btn.use:hover {
    background: #27ae60;
    transform: translateY(-2px);
}

.template-btn.copy {
    background: #9b59b6;
    color: white;
}

.template-btn.copy:hover {
    background: #8e44ad;
    transform: translateY(-2px);
}

/* Template Editor */
.template-editor {
    margin-top: 15px;
    padding: 15px;
    background: white;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
}

.template-editor textarea {
    width: 100%;
    min-height: 150px;
    padding: 12px;
    border-radius: 6px;
    border: 1px solid #ddd;
    font-family: 'Poppins', sans-serif;
    resize: vertical;
}

.editor-actions {
    display: flex;
    gap: 12px;
    margin-top: 15px;
}

.editor-btn {
    padding: 8px 16px;
    border-radius: 6px;
    border: none;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.2s ease;
}

.editor-btn.save {
    background: #2ecc71;
    color: white;
}

.editor-btn.save:hover {
    background: #27ae60;
    transform: translateY(-2px);
}

.editor-btn.cancel {
    background: #e74c3c;
    color: white;
}

.editor-btn.cancel:hover {
    background: #c0392b;
    transform: translateY(-2px);
}

/* Spam Detection Section */
.spam-detection {
    background: white;
    border-radius: 15px;
    padding: 20px;
    margin-top: 30px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
    border-left: 5px solid #ff6b6b;
}

.spam-header {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 20px;
    color: #333;
    display: flex;
    align-items: center;
}

.spam-header svg {
    margin-right: 10px;
}

.spam-card {
    padding: 15px;
    margin-bottom: 15px;
    border-radius: 10px;
    background: #fff5f5;
    border-left: 4px solid #ff6b6b;
}

.spam-title {
    font-weight: 600;
    margin-bottom: 10px;
    color: #d63031;
    display: flex;
    align-items: center;
}

.spam-title svg {
    margin-right: 10px;
}

.spam-stats {
    display: flex;
    gap: 15px;
    margin-bottom: 10px;
}

.spam-stat {
    background: rgba(255,107,107,0.1);
    padding: 8px 12px;
    border-radius: 8px;
    font-size: 0.9rem;
}

.spam-stat-value {
    font-weight: 700;
    color: #ff6b6b;
}

.spam-example {
    background: white;
    padding: 10px;
    border-radius: 8px;
    margin: 10px 0;
    border: 1px solid #ffecec;
}

.spam-post {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px dashed #eee;
}

.spam-post:last-child {
    border-bottom: none;
}

.spam-post-content {
    flex: 1;
}

.spam-post-link {
    margin-left: 15px;
}

/* Hidden section that will be shown when clicking View Crisis Details */
.hidden-section {
    display: none;
}

/* Show section when target is crisis-posts-section */
:target {
    display: block;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .metrics-row {
        flex-direction: column;
    }
    
    .metric-box {
        min-width: 100%;
    }
    
    .template-actions {
        flex-direction: column;
    }
    
    .template-btn {
        width: 100%;
        justify-content: center;
    }
}
</style>

<!-- Animated Header -->
<div class="main-header">
    <div class="header-title">BRAMS</div>
    <div class="header-subtitle">Advanced Social Media Reputation Management System</div>
</div>
""", unsafe_allow_html=True)

def main():
    # Initialize session state variables if they don't exist
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.previous_keyword = None
        st.session_state.current_keyword = None
        st.session_state.should_refresh = False
        st.session_state.analysis_complete = False
        st.session_state.crisis_data = None
    
    st.sidebar.markdown('<div class="sidebar-header">BRAMS Controls</div>', unsafe_allow_html=True)
    st.sidebar.markdown('### 🔍 Brand Monitoring')
    
    # Get current keyword
    current_keyword = st.sidebar.text_input("Enter Brand/Keyword", value="")
    
    # Check if keyword has changed
    if current_keyword != st.session_state.current_keyword and st.session_state.current_keyword is not None:
        st.session_state.should_refresh = True
        st.session_state.analysis_complete = False
        st.session_state.crisis_data = None
        # Clear all session state except control variables
        for key in list(st.session_state.keys()):
            if key not in ['initialized', 'previous_keyword', 'current_keyword', 'should_refresh', 'analysis_complete', 'crisis_data']:
                del st.session_state[key]
    
    # Update current keyword
    st.session_state.current_keyword = current_keyword
    
    analyze_brand = st.sidebar.button("Analyze Brand Reputation")

    if analyze_brand and current_keyword:
        st.session_state.should_refresh = True
        st.session_state.analysis_complete = False
        
        with st.spinner("Analyzing brand reputation..."):
            data = process_data(current_keyword)
            if data:
                st.session_state.data = data
                st.session_state.keyword = current_keyword
                st.session_state.last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Detect crisis and store in session state
                crisis_data = detect_crisis(data, current_keyword)
                if crisis_data:
                    st.session_state.crisis_data = crisis_data
                    if crisis_data.get('is_crisis', False):
                        st.warning(f"⚠️ Crisis Alert: {crisis_data.get('title', 'Potential crisis detected')}")
                
                # Detect issues and generate recommendations
                with st.spinner("Analyzing issues and generating recommendations..."):
                    detected_issues = detect_issues_with_groq(data, current_keyword)
                    if detected_issues:
                        st.session_state.detected_issues = detected_issues
                        recommendations = generate_recommendations_with_groq(detected_issues, current_keyword)
                        if recommendations:
                            st.session_state.recommendations = recommendations
                            
                        response_templates = generate_response_templates_with_groq(detected_issues, current_keyword)
                        if response_templates:
                            st.session_state.response_templates = response_templates
                
                st.session_state.duplicates = detect_duplicates(data)
                st.session_state.analysis_complete = True
                st.rerun()
    
    # Rest of your existing main function code for displaying results...
    st.sidebar.markdown('### 🎚 Filter Options')
    platform_options = ["All", "Twitter", "Reddit", "YouTube", "Instagram", "News"]
    platform_filter = st.sidebar.selectbox("Platform", platform_options)
    
    sentiment_options = ["All", "Positive", "Neutral", "Negative"]
    sentiment_filter = st.sidebar.selectbox("Sentiment", sentiment_options)
    st.sidebar.markdown('### ℹ About')
    st.sidebar.info(
        "BRAMS monitors social media platforms to track brand reputation. "
        "The system analyzes sentiment and provides insights to help businesses "
        "understand public perception."
    )
    
    if st.sidebar.button("Export Report (CSV)"):
        if 'data' in st.session_state:
            df = pd.DataFrame(st.session_state.data)
            csv = df.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="brand_report.csv">Download CSV File</a>'
            st.sidebar.markdown(href, unsafe_allow_html=True)
        else:
            st.sidebar.warning("No data to export. Run an analysis first.")
    
    if 'data' not in st.session_state:
        st.markdown("""
     <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 30px;">
        <h2>Welcome to BRAMS</h2>
        <p>Monitor your brand's reputation across social media platforms in real-time.</p>
        <p>Enter a brand name in the sidebar and click "Analyze Brand Reputation" to get started.</p>
        
        <div class="logo">
            <div class="text">
                <h1>BRAMS</h1>
                <p>COMMENTS SPEAKS</p>
            </div>
            <div class="hashtags">
                <span>#</span>
                <span>#</span>
                <span>#</span>
                <span>#</span>
                <span>#</span>
                <span>#</span>
                <span>#</span>
                <span>#</span>
            </div>
        </div>
     </div>

     <style>
        @import url('https://fonts.googleapis.com/css2?family=Serif:wght@700&family=Montserrat:wght@600&display=swap');

        .logo {
            position: relative;
            width: 350px;
            height: 350px;
            display: flex;
            justify-content: center;
            align-items: center;
            background: navy; /* Changed from blue to navy */
            border-radius: 50%;
            margin: 40px auto;
        }

        .text {
            position: absolute;
            text-align: center;
            width: 100%;
            transform: translateY(-50%);
            top: 50%;
        }

        .text h1 {
            margin: 0;
            padding: 0;
            font-size: 3rem;
            font-family: 'Serif', serif;
            letter-spacing: 2px;
            color: #fff;
            white-space: nowrap;
            line-height: 1;
        }

        .text p {
            margin: 10px 0 0;
            font-size: 1rem;
            font-family: 'Montserrat', sans-serif;
            color: white;
            font-weight: bold;
            letter-spacing: 2px;
        }

        .hashtags {
            position: absolute;
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            animation: rotateCircle 8s linear infinite;
        }

        .hashtags span {
            position: absolute;
            font-size: 2rem;
            font-weight: bold;
            color: white;
        }

        @keyframes rotateCircle {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .hashtags span:nth-child(1) { transform: rotate(0deg) translate(150px); }
        .hashtags span:nth-child(2) { transform: rotate(45deg) translate(150px); }
        .hashtags span:nth-child(3) { transform: rotate(90deg) translate(150px); }
        .hashtags span:nth-child(4) { transform: rotate(135deg) translate(150px); }
        .hashtags span:nth-child(5) { transform: rotate(180deg) translate(150px); }
        .hashtags span:nth-child(6) { transform: rotate(225deg) translate(150px); }
        .hashtags span:nth-child(7) { transform: rotate(270deg) translate(150px); }
        .hashtags span:nth-child(8) { transform: rotate(315deg) translate(150px); }
     </style>
     """, unsafe_allow_html=True)
         
    elif st.session_state.analysis_complete:
        # Display analysis results
        st.markdown(f"## Brand Analysis: {st.session_state.keyword}")
        st.markdown(f"<p style='color: #666;'>Last updated: {st.session_state.last_updated}</p>", unsafe_allow_html=True)
        
        sentiment_data = analyze_sentiment(st.session_state.data)
        display_metrics(sentiment_data)
        
        # Display crisis alert if available
        if 'crisis_data' in st.session_state and st.session_state.crisis_data:
            display_crisis_alert(st.session_state.crisis_data)
            if st.session_state.crisis_data.get('is_crisis', False):
                display_crisis_posts(st.session_state.crisis_data)
        
        # Display duplicates if available
        if 'duplicates' in st.session_state:
            display_duplicates(st.session_state.duplicates)
        
        # Display charts
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            sentiment_chart = create_sentiment_distribution_chart(sentiment_data)
            st.plotly_chart(sentiment_chart, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            trend_chart = create_sentiment_trend_chart(st.session_state.data)
            st.plotly_chart(trend_chart, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            platform_chart = create_platform_distribution_chart(st.session_state.data)
            st.plotly_chart(platform_chart, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Display issues and recommendations
        if 'detected_issues' in st.session_state and st.session_state.detected_issues:
            display_issue_detection(st.session_state.detected_issues, current_keyword)
            
            if 'recommendations' in st.session_state and st.session_state.recommendations:
                display_recommendations(st.session_state.recommendations)
            
            if 'response_templates' in st.session_state and st.session_state.response_templates:
                display_response_templates(st.session_state.response_templates)
        
        # Display filtered posts
        st.markdown("## Recent Mentions")
        display_posts(st.session_state.data, platform_filter, sentiment_filter)

if __name__ == "__main__":
    main()