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
import textwrap
import hashlib
from collections import defaultdict
import re
from groq import Groq

from constants.icons import SOCIAL_ICONS
def display_duplicates(duplicates):
    """Display duplicate detection results with enhanced UI"""
    try:
        # Validate input
        if not isinstance(duplicates, dict) or not all(key in duplicates for key in ['duplicate_groups', 'cross_platform_groups', 'spam_posts']):
            st.error("Invalid duplicate data format")
            return
        
        # Check if there's any data to display
        if not any([duplicates['duplicate_groups'], duplicates['cross_platform_groups'], duplicates['spam_posts']]):
            st.info("No duplicate content or suspicious activity detected")
            return
        
        # Display duplicate content within same platform
        if duplicates['duplicate_groups']:
            st.markdown("""
            <div class="spam-section">
                <div class="spam-section-title">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="#ff6b6b">
                        <path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zM6 20V4h7v5h5v11H6z"/>
                    </svg>
                    Same Platform Duplicates
                </div>
                </div>
            """, unsafe_allow_html=True)

            for group in duplicates['duplicate_groups']:
                with st.expander(f"🔄 Similar content on {group['platform']} (Similarity: {group['similarity']}%)"):
                    for post in group['posts']:
                        st.markdown(f"""
                        <div class="post-card {post['platform'].lower()}">
                            <div class="platform-tag {post['platform'].lower()}">
                                <span>{post['platform']}</span>
                            </div>
                            <div class="post-content">{post['content']}</div>
                            <div class="post-meta">
                                <span>@{post.get('username', 'anonymous')}</span>
                                <a href="{post['url']}" target="_blank">View Source</a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

        # Display cross-platform duplicates
        if duplicates['cross_platform_groups']:
            st.markdown("""
            <div class="spam-section">
                <div class="spam-section-title">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="#4b6cb7">
                        <path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/>
                    </svg>
                    Cross-Platform Duplicates
                </div>
            </div>
            """, unsafe_allow_html=True)

            for group in duplicates['cross_platform_groups']:
                with st.expander(f"🔄 Similar content across {' & '.join(group['platforms'])} (Similarity: {group['similarity']}%)"):
                    for post in group['posts']:
                        st.markdown(f"""
                        <div class="post-card {post['platform'].lower()}">
                            <div class="platform-tag {post['platform'].lower()}">
                                <span>{post['platform']}</span>
                            </div>
                            <div class="post-content">{post['content']}</div>
                            <div class="post-meta">
                                <span>@{post.get('username', 'anonymous')}</span>
                                <a href="{post['url']}" target="_blank">View Source</a>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
        # Display spam posts
        if duplicates['spam_posts']:
            st.markdown("""
            <div class="spam-section">
                <div class="spam-section-title">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="#e74c3c">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                    </svg>
                    Potential Spam Content
                </div>
            </div>
            """, unsafe_allow_html=True)

            for post in duplicates['spam_posts']:
                with st.expander(f"⚠️ Suspicious content detected ({post['type']})"):
                                st.markdown(f"""
                    <div class="post-card {post['platform'].lower()}">
                        <div class="platform-tag {post['platform'].lower()}">
                            <span>{post['platform']}</span>
                                    </div>
                        <div class="post-content">{post['post']['content']}</div>
                        <div class="post-meta">
                            <span>@{post['post'].get('username', 'anonymous')}</span>
                            <a href="{post['post']['url']}" target="_blank">View Source</a>
                                    </div>
                                </div>
                                """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error displaying duplicate detection results: {str(e)}")
  # Updated to the correct model name
# Update the model constant at the top

def display_issue_detection(issues, keyword):
    """Display detected issues with recommendations"""
    if not issues:
        return
    
    st.markdown('<div class="issue-detection">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="issue-header">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#4b6cb7">
            <path d="M12 2L1 21h22L12 2zm0 3.5L18.5 19h-13L12 5.5z"/>
            <path d="M12 16c.8 0 1.5-.7 1.5-1.5S12.8 13 12 13s-1.5.7-1.5 1.5zm-1-5h2v-4h-2v4z"/>
        </svg>
        Detected Issues for {keyword}
    </div>
    """, unsafe_allow_html=True)
    
    for issue in issues:
        st.markdown('<div class="issue-card">', unsafe_allow_html=True)
        
        # Issue title and stats
        st.markdown(f"""
        <div class="issue-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="#e74c3c">
                <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
            </svg>
            {issue['name']} Issues
        </div>
        <div class="issue-stats">
            <div class="issue-stat">
                <span class="issue-stat-value">{len(issue.get('posts', []))}</span> reports
            </div>
            <div class="issue-stat">
                <span class="issue-stat-value">{issue['engagement']:,}</span> engagement
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Example posts (collapsible)
        actual_post_count = len(issue.get('posts', []))
        with st.expander(f"See {actual_post_count} example posts"):
            if actual_post_count > 0:
                for post in issue.get('posts', []):
                    platform = post.get('platform', 'Unknown')
                    platform_icon = SOCIAL_ICONS.get(platform, "")
                    url = post.get('url', '#')
                    
                    st.markdown(f'''
                    <div class="post-card {platform.lower()}">
                        <div class="platform-tag {platform.lower()}">
                            <span class="icon-container">{platform_icon}</span>{platform}
                        </div>
                        <div style="display:flex;align-items:center;gap:10px;">
                            <p class="post-content">{post['content']}</p>
                        </div>
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <div class="sentiment-badge negative">Negative</div>
                            <a href="{url}" target="_blank" class="view-source-btn">
                                <button style="background-color: #4b6cb7; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer;">
                                    View Source
                                </button>
                            </a>
                        </div>
                    </div>
                    ''', unsafe_allow_html=True)
            else:
                st.info("No example posts available for this issue.")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_recommendations(recommendations):
    """Display generated recommendations with enhanced UI"""
    if not recommendations or not isinstance(recommendations, list):
        st.info("No recommendations available.")
        return

    st.markdown("""
        <div class="recommendations-section">
            <h2 class="section-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#4b6cb7">
                    <path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1z"/>
                </svg>
                Recommended Actions
            </h2>
    """, unsafe_allow_html=True)

    for i, rec in enumerate(recommendations):
        if not isinstance(rec, dict):
            continue

        rec_id = f"rec_{i}"
        issue = rec.get('issue', 'General Recommendation')
        severity = rec.get('severity', 'Medium')
        actions = rec.get('actions', [])
        template = rec.get('template', '')

        # Initialize session state for this recommendation if not exists
        if rec_id not in st.session_state:
            st.session_state[rec_id] = {
                "editing": False,
                "template": template
            }

        # Create recommendation card
        st.markdown(f"""
            <div class="recommendation-card">
                <div class="recommendation-header">
                    <h3 class="recommendation-title">
                        {issue}
                        <span class="severity-badge {severity.lower()}">{severity}</span>
                    </h3>
                </div>
        """, unsafe_allow_html=True)

        # Display actions if available
        if actions:
            st.markdown('<div class="actions-list">', unsafe_allow_html=True)
            st.markdown('<h4>Recommended Actions:</h4>', unsafe_allow_html=True)
            for idx, action in enumerate(actions, 1):
                if action:  # Only display non-empty actions
                    st.markdown(f"""
                        <div class="action-item">
                            <span class="action-number">{idx}</span>
                            <span class="action-text">{action}</span>
                        </div>
                    """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # Handle template section
        if template:
            st.markdown('<div class="template-section">', unsafe_allow_html=True)
            st.markdown('<h4>Response Template:</h4>', unsafe_allow_html=True)

            if st.session_state[rec_id]["editing"]:
                edited_template = st.text_area(
                    "Edit template",
                    value=st.session_state[rec_id]["template"],
                    key=f"edit_{rec_id}"
                )
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Save", key=f"save_{rec_id}"):
                        st.session_state[rec_id]["template"] = edited_template
                        st.session_state[rec_id]["editing"] = False
                        st.rerun()
                with col2:
                    if st.button("Cancel", key=f"cancel_{rec_id}"):
                        st.session_state[rec_id]["editing"] = False
                        st.rerun()
            else:
                st.markdown(f"""
                    <div class="template-content">
                        {st.session_state[rec_id]["template"]}
                    </div>
                """, unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("Edit", key=f"edit_{rec_id}"):
                        st.session_state[rec_id]["editing"] = True
                        st.rerun()
                with col2:
                    if st.button("Copy", key=f"copy_{rec_id}"):
                        st.code(st.session_state[rec_id]["template"])
                        st.success("Template copied!")
                with col3:
                    if st.button("Use", key=f"use_{rec_id}"):
                        st.session_state["active_template"] = st.session_state[rec_id]["template"]
                        st.success("Template activated!")

            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Add custom CSS
    st.markdown("""
    <style>
    .recommendations-section {
        margin: 2rem 0;
        background: white;
        padding: 2rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .section-title {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        color: #1e3a8a;
        font-size: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .recommendation-card {
        background: #f8fafc;
        border-radius: 8px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border-left: 4px solid #4b6cb7;
    }
    .recommendation-title {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1rem;
        color: #1e3a8a;
        font-size: 1.2rem;
    }
    .severity-badge {
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    .severity-badge.high {
        background-color: #fee2e2;
        color: #dc2626;
    }
    .severity-badge.medium {
        background-color: #fef3c7;
        color: #d97706;
    }
    .severity-badge.low {
        background-color: #ecfdf5;
        color: #059669;
    }
    .actions-list {
        margin: 1rem 0;
    }
    .action-item {
        display: flex;
        align-items: flex-start;
        gap: 1rem;
        margin: 0.75rem 0;
        padding: 0.75rem;
        background: white;
        border-radius: 6px;
    }
    .action-number {
        background: #4b6cb7;
        color: white;
        width: 24px;
        height: 24px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.875rem;
    }
    .action-text {
        flex: 1;
        line-height: 1.5;
    }
    .template-section {
        margin-top: 1.5rem;
        padding-top: 1.5rem;
        border-top: 1px dashed #e2e8f0;
    }
    .template-content {
        background: white;
        padding: 1rem;
        border-radius: 6px;
        margin: 0.75rem 0;
        white-space: pre-wrap;
        font-family: 'Courier New', monospace;
        line-height: 1.5;
        border: 1px solid #e2e8f0;
    }
    </style>
    """, unsafe_allow_html=True)

def display_response_templates(templates):
    """Display generated response templates with enhanced UI and brand specificity"""
    if not templates:
        return
    
    st.markdown('<div class="response-templates">', unsafe_allow_html=True)
    st.markdown("""
    <div class="template-header">
        <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#4b6cb7">
            <path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
        </svg>
        Brand-Specific Response Templates
    </div>
    """, unsafe_allow_html=True)
    
    for i, template in enumerate(templates):
        template_key = f"template_{template['template_id']}"
        
        if template_key not in st.session_state:
            st.session_state[template_key] = {
                "editing": False,
                "template": template["template"],
                "brand": template["brand"],
                "generated_at": template["generated_at"]
            }
        
        st.markdown(f'''
        <div class="template-card">
            <div class="template-title">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="#4b6cb7">
                    <path d="M19 3h-4.18C14.4 1.84 13.3 1 12 1c-1.3 0-2.4.84-2.82 2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-7 0c.55 0 1 .45 1 1s-.45 1-1 1-1-.45-1-1 .45-1 1-1zm2 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
                </svg>
                {template["issue"]} Response for {template["brand"]}
                <span style="font-size: 0.8em; color: #666; margin-left: 10px;">ID: {template["template_id"]}</span>
            </div>
        ''', unsafe_allow_html=True)
        
        if st.session_state[template_key]["editing"]:
            edited_template = st.text_area(
                "Edit the template:", 
                value=st.session_state[template_key]["template"],
                key=f"editor_{template_key}",
                height=200
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Changes", key=f"save_{template_key}"):
                    st.session_state[template_key]["template"] = edited_template
                    st.session_state[template_key]["editing"] = False
                    st.success("Template updated successfully!")
            with col2:
                if st.button("❌ Cancel", key=f"cancel_{template_key}"):
                    st.session_state[template_key]["editing"] = False
                    st.rerun()
        else:
            st.markdown(f'''
            <div class="template-content">
                <div style="margin-bottom: 10px; color: #666;">
                    Generated: {template["generated_at"]}
                </div>
                {st.session_state[template_key]["template"]}
            </div>
            ''', unsafe_allow_html=True)
            
            st.markdown('<div class="template-actions">', unsafe_allow_html=True)
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✏ Edit Template", key=f"edit_{template_key}"):
                    st.session_state[template_key]["editing"] = True
                    st.rerun()
            
            with col2:
                if st.button("📋 Use Template", key=f"use_{template_key}"):
                    st.code(st.session_state[template_key]["template"], language="markdown")
                    st.success("Template ready to use! Copy the content above.")
            
            with col3:
                if st.button("📝 Copy to Clipboard", key=f"copy_{template_key}"):
                    st.session_state.copied_template = st.session_state[template_key]["template"]
                    st.success("Template copied to clipboard!")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def display_crisis_alert(crisis_data):
    """Display crisis alert with simple UI"""
    if not crisis_data:
        return
        
    st.markdown(f"""
    <div class="crisis-alert">
        <div class="crisis-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="white">
                <path d="M12 2L1 21h22L12 2zm0 3.5L18.5 19h-13L12 5.5z"/>
                <path d="M12 16c.8 0 1.5-.7 1.5-1.5S12.8 13 12 13s-1.5.7-1.5 1.5.7 1.5 1.5 1.5zm-1-5h2v-4h-2v4z"/>
            </svg>
            {crisis_data.get("title", "Potential PR Crisis Detected")}
        </div>
        <p>{crisis_data.get("description", "Multiple negative mentions detected that require attention.")}</p>
        <div class="crisis-metrics">
            <div class="crisis-metric">
                <div class="crisis-metric-value">{crisis_data.get("posts", 0)}</div>
                <div class="crisis-metric-label">Mentions</div>
            </div>
            <div class="crisis-metric">
                <div class="crisis-metric-value">{crisis_data.get("percentage", 0)}%</div>
                <div class="crisis-metric-label">Negative Sentiment</div>
            </div>
            <div class="crisis-metric">
                <div class="crisis-metric-value">{crisis_data.get("engagement", 0)}</div>
                <div class="crisis-metric-label">Engagement</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_crisis_posts(crisis_data):
    """Display crisis posts with normal post UI styling"""
    if not crisis_data or not crisis_data.get("all_crisis_posts"):
        return

    st.markdown("""
    <div class="section-header">
        <h2>Crisis-Related Posts</h2>
    </div>
    """, unsafe_allow_html=True)

    # Display each crisis post using normal post UI
    for post in crisis_data.get("all_crisis_posts", []):
        platform = post.get("platform", "Unknown")
        platform_icon = SOCIAL_ICONS.get(platform, "")
        content = post.get('content', 'No content available')
        url = post.get('url', '#')
        username = post.get('username', 'anonymous')
        engagement = post.get('engagement', 0)
        
        st.markdown(f'''
        <div class="post-card {platform.lower()}">
            <div class="platform-tag {platform.lower()}">
                <span class="icon-container">{platform_icon}</span>{platform}
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
                <p class="post-content">{content}</p>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div class="sentiment-badge negative">Negative</div>
                <a href="{url}" target="_blank" class="view-source-btn">
                    <button style="background-color: #4b6cb7; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer;">
                        View Source
                    </button>
                </a>
            </div>
        </div>
        ''', unsafe_allow_html=True)

def get_icon_for_concern(concern_text):
    """Get appropriate icon based on concern text"""
    CONCERN_ICONS = {
        'security': '🔒',
        'vulnerability': '🔓',
        'bug': '🐛',
        'performance': '⚡',
        'data': '💾',
        'privacy': '🔐',
        'service': '🔧',
        'content': '📺',
        'feature': '⚙️',
        'chat': '💬',
        'group': '👥',
        'ios': '📱',
        'app': '📱',
        'tv': '📺',
        'default': '⚠️'
    }
    
    concern_lower = concern_text.lower()
    for key, icon in CONCERN_ICONS.items():
        if key in concern_lower:
            return icon
    return CONCERN_ICONS['default']

def display_posts(data, platform_filter, sentiment_filter):
    """Display posts with safe sentiment handling"""
    filtered_data = data
    
    # Filter by platform
    if platform_filter != "All":
        filtered_data = [post for post in filtered_data if post.get('platform') == platform_filter]
    
    # Filter by sentiment with safe access
    if sentiment_filter != "All":
        filtered_data = [post for post in filtered_data if post.get('sentiment', 'Neutral') == sentiment_filter]
    
    if not filtered_data:
        st.info("No posts match your filters.")
        return
    
    for post in filtered_data:
        platform = post.get('platform', 'Unknown')
        platform_icon = SOCIAL_ICONS.get(platform, "")
        
        # Safe sentiment handling with default to neutral
        sentiment = post.get('sentiment', 'Neutral')
        sentiment_class = {
            "Positive": "positive",
            "Negative": "negative",
            "Neutral": "neutral"
        }.get(sentiment, "neutral")
        
        st.markdown(f'''
        <div class="post-card {platform.lower()}">
            <div class="platform-tag {platform.lower()}">
                <span class="icon-container">{platform_icon}</span>{platform}
            </div>
            <div style="display:flex;align-items:center;gap:10px;">
                <p class="post-content">{post.get('content', 'No content available')}</p>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <div class="sentiment-badge {sentiment_class}">{sentiment}</div>
                <a href="{post.get('url', '#')}" target="_blank" style="text-decoration: none;">
                    <button style="background-color: #4b6cb7; color: white; border: none; padding: 8px 16px; border-radius: 5px; cursor: pointer;">
                        View Source
                    </button>
                </a>
            </div>
        </div>
        ''', unsafe_allow_html=True)
