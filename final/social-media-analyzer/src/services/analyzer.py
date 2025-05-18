from textblob import TextBlob
from datetime import datetime
from groq import Groq
from collections import defaultdict
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
from textblob import TextBlob
from datetime import datetime
from groq import Groq
from collections import defaultdict
import streamlit as st
import hashlib

client = Groq(
    api_key="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"
)


def analyze_sentiment(data):
    """Analyze sentiment with safe key access"""
    sentiment_counts = {"Positive": 0, "Negative": 0, "Neutral": 0}
    total_posts = len(data)
    
    # Safely count sentiments
    for post in data:
        # Get sentiment with default value of 'Neutral'
        sentiment = post.get('sentiment', 'Neutral')
        # Only increment if sentiment is one of our expected values
        if sentiment in sentiment_counts:
            sentiment_counts[sentiment] += 1
    
    # Calculate brand score safely
    if total_posts > 0:
        positive_percentage = (sentiment_counts["Positive"] / total_posts) * 100
        # Add bonus points for high positive percentage
        brand_score = min(100, positive_percentage + 15)
    else:
        brand_score = 0
    
    return {
        "total_posts": total_posts,
        "positive_count": sentiment_counts["Positive"],
        "negative_count": sentiment_counts["Negative"],
        "neutral_count": sentiment_counts["Neutral"],
        "brand_score": int(brand_score)
    }
GROQ_MODEL = "meta-llama/llama-4-maverick-17b-128e-instruct"  # Updated to Llama 4 Maverick model

def detect_issues_with_groq(data, keyword):
    """Detect issues from real reviews using Groq API"""
    try:
        # Filter negative posts
        negative_posts = [
            post for post in data 
            if post.get('sentiment', '') == "Negative"
        ]
        
        if not negative_posts:
            st.info("No negative posts found for analysis")
            return None

        # Format reviews for analysis with actual content
        reviews_text = "\n".join([
            f"Review {i+1}: {post['content']}"
            for i, post in enumerate(negative_posts[:15])  # Increased to 15 reviews
        ])

        # Create conversation prompt
        conversation = [
            {
                "role": "system",
                "content": f"You are a brand analyst. Extract specific issues from negative reviews about {keyword}."
            },
            {
                "role": "user",
                "content": f"""
                Analyze these negative reviews for {keyword} and identify main issues.
                Reviews:
                {reviews_text}

                Extract exactly 3 main issues. For each issue:
                1. Give a clear issue name
                2. Rate severity (High/Medium/Low)
                3. Include EXACT quotes from the reviews as examples
                
                Format your response exactly like this:
                Issue: [Issue Name]
                Severity: [Level]
                Examples:
                - [paste exact review quote]
                - [paste another exact quote]
                """
            }
        ]

        # Make API call
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=conversation,
            temperature=0.3,
            max_tokens=2000
        )

        # Process response
        result = []
        current_issue = None
        
        response_text = response.choices[0].message.content
        lines = response_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('Issue:'):
                if current_issue and current_issue.get('examples'):
                    result.append(current_issue)
                current_issue = {
                    'name': line.split(':', 1)[1].strip(),
                    'examples': [],
                    'severity': 'Medium',  # Default severity
                    'posts': []  # Initialize posts list
                }
            elif line.startswith('Severity:'):
                if current_issue:
                    current_issue['severity'] = line.split(':', 1)[1].strip()
            elif line.startswith('-') and current_issue:
                example = line[1:].strip()
                if example:
                    current_issue['examples'].append(example)

        # Add the last issue
        if current_issue and current_issue.get('examples'):
            result.append(current_issue)

        # Match examples to actual posts
        for issue in result:
            matching_posts = []
            for post in negative_posts:
                post_content = post['content'].lower()
                for example in issue['examples']:
                    # Relaxed matching to find partial matches
                    if any(part.lower() in post_content for part in example.split()):
                        matching_posts.append(post)
                        break

            issue['posts'] = matching_posts
            issue['count'] = len(matching_posts)
            issue['engagement'] = sum(
                int(str(p.get('engagement', '0')).replace('k', '000')) 
                if str(p.get('engagement', '0')).replace('k', '').isdigit() 
                else 0 
                for p in matching_posts
            )

        return result if result else None

    except Exception as e:
        st.error(f"Error in issue detection: {str(e)}")
        st.error(f"Response text: {response_text if 'response_text' in locals() else 'No response'}")
        return None

def generate_recommendations_with_groq(issues, keyword):
    """Generate recommendations based on detected issues"""
    try:
        if not issues:
            return None

        recommendations = []
        
        for issue in issues:
            # Get example posts with error handling
            example_posts = []
            if issue.get('posts'):
                example_posts = [p['content'] for p in issue['posts'][:3]]
            examples_text = "\n".join([f"- {ex}" for ex in example_posts]) if example_posts else "No example posts available"

            # Create a focused prompt for better recommendations
            conversation = [
                {
                    "role": "system",
                    "content": f"You are an expert PR and customer experience specialist for {keyword}. Generate specific, actionable recommendations to address customer concerns."
                },
                {
                    "role": "user",
                    "content": f"""
                    For {keyword}, address this critical issue:
                    Issue: {issue['name']}
                    Severity: {issue['severity']}
                    
                    Customer Feedback Examples:
                    {examples_text}

                    Provide:
                    1. Three specific, actionable steps to address this issue
                    2. A professional response template that:
                       - Acknowledges the concern
                       - Explains planned actions
                       - Maintains brand voice
                       - Shows commitment to resolution
                    """
                }
            ]

            try:
                # Make API call with error handling
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=conversation,
                    temperature=0.4,
                    max_tokens=1500
                )

                if not response.choices:
                    continue
                    
                response_text = response.choices[0].message.content
                
                # Parse response with improved error handling
                actions = []
                template = ""
                current_section = None
                
                for line in response_text.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Detect sections
                    if line.lower().startswith(('step', 'action', '1.', '2.', '3.')):
                        current_section = 'actions'
                        action = line.split('.', 1)[-1].strip()
                        if action:
                            actions.append(action)
                    elif line.lower().startswith(('template:', 'response:', 'suggested response:')):
                        current_section = 'template'
                        template = line.split(':', 1)[-1].strip()
                    elif current_section == 'template':
                        template += "\n" + line

                # Clean up and validate the results
                actions = [a for a in actions if len(a) > 10][:3]  # Keep only meaningful actions
                template = template.strip()
                
                if not actions:
                    actions = [
                        f"Investigate the {issue['name']} issue thoroughly",
                        f"Develop an action plan to address {issue['name']}",
                        "Implement improvements based on customer feedback"
                    ]
                
                if not template:
                    template = (
                        f"Dear valued customer,\n\n"
                        f"We appreciate your feedback regarding the {issue['name'].lower()} issue. "
                        f"We take your concerns seriously and are actively working on addressing this matter.\n\n"
                        f"Our team has initiated the following steps:\n"
                    )
                    
                    for action in actions:
                        template += f"- {action.lower()}\n"
                    
                    template += (
                        f"\nWe are committed to providing you with the best possible experience "
                        f"and will keep you updated on our progress.\n\n"
                        f"Thank you for your patience and understanding.\n\n"
                        f"Best regards,\n"
                        f"The {keyword} Team"
                    )

                recommendations.append({
                    'issue': issue['name'],
                    'severity': issue['severity'],
                    'actions': actions,
                    'template': template
                })

            except Exception as e:
                st.error(f"Error generating recommendation for {issue['name']}: {str(e)}")
                continue

        return recommendations if recommendations else None

    except Exception as e:
        st.error(f"Error in generate_recommendations_with_groq: {str(e)}")
        return None

def generate_response_templates_with_groq(issues, keyword):
    """Generate unique response templates using Groq AI with brand-specific context"""
    try:
        templates = []
        
        # Define brand-specific characteristics
        brand_profiles = {
            'apple': {
                'tone': 'professional and premium',
                'style': 'minimalist and sophisticated',
                'values': 'innovation, design, user experience',
                'products': ['iPhone', 'MacBook', 'iPad', 'Apple Watch'],
                'support_channel': 'Apple Support',
                'signature': 'Apple Care Team'
            },
            # ... rest of brand profiles ...
        }
        
        # Get brand profile or create default
        brand_key = keyword.lower()
        brand_profile = brand_profiles.get(brand_key, {
            'tone': 'professional and customer-focused',
            'style': 'balanced and solution-oriented',
            'values': 'quality, customer satisfaction, innovation',
            'products': [f'{keyword} products'],
            'support_channel': f'{keyword} Support',
            'signature': f'{keyword} Support Team'
        })
        
        session_key = f"{keyword}_{datetime.now().timestamp()}"
        
        for issue in issues:
            example_posts = []
            if issue.get('posts'):
                example_posts = [p['content'] for p in issue['posts'][:2]]
            examples_text = "\n".join([f"- {ex}" for ex in example_posts]) if example_posts else "No example posts available"

            conversation = [
                {
                    "role": "system",
                    "content": f"""You are a {brand_profile['tone']} customer service specialist for {keyword}.
                    Brand Voice: {brand_profile['style']}
                    Values: {brand_profile['values']}
                    Support: {brand_profile['support_channel']}
                    Create a response that is uniquely {keyword}-specific."""
                },
                {
                    "role": "user",
                    "content": f"""
                    Issue: {issue['name']}
                    Severity: {issue['severity']}
                    Customer Feedback: {examples_text}
                    
                    Create a response that:
                    1. Uses {keyword}'s voice
                    2. References: {', '.join(brand_profile['products'][:2])}
                    3. Includes case ID: {{case_id}}
                    4. Signs off as: {brand_profile['signature']}
                    
                    Make this response unique to {keyword}."""
                }
            ]

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=conversation,
                temperature=0.7,
                max_tokens=800
            )
            
            if not response.choices:
                continue
                
            response_text = response.choices[0].message.content
            
            formatted_response = f"""Case ID: #{session_key[:8]}
{response_text}

Best regards,
{brand_profile['signature']}
{brand_profile['support_channel']}"""
            
            template_id = hashlib.md5(f"{keyword}_{issue['name']}_{session_key}".encode()).hexdigest()[:8]
            
            templates.append({
                'issue': issue['name'],
                'severity': issue['severity'],
                'template': formatted_response.strip(),
                'template_id': template_id,
                'brand': keyword,
                'generated_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'session_key': session_key
            })

        return templates if templates else None

    except Exception as e:
        st.error(f"Error generating response templates: {str(e)}")
        return None
    
def detect_crisis(data, keyword):
    """
    Detect potential PR crises based on negative sentiment patterns and engagement metrics
    across all platforms including website reviews. Uses Llama 4 Maverick for enhanced analysis.
    """
    try:
        if not data:
            return None

        # Filter posts with significant engagement (>50 or contains 'k')
        def convert_engagement(eng):
            if isinstance(eng, (int, float)):
                return int(eng)
            if isinstance(eng, str):
                if 'k' in eng.lower():
                    return int(float(eng.lower().replace('k', '')) * 1000)
                try:
                    return int(eng)
                except ValueError:
                    return 0
            return 0

        # Format datetime for JSON serialization
        def format_datetime(dt):
            if isinstance(dt, datetime):
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(dt, str):
                try:
                    parsed_dt = datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")
                    return dt
                except ValueError:
                    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Filter significant posts and include all negative reviews
        significant_posts = [
            post for post in data
            if convert_engagement(post.get('engagement', 0)) > 50 or post.get('sentiment') == 'Negative'
        ]

        if not significant_posts:
            return None

        # Calculate metrics
        total_engagement = sum(convert_engagement(post.get('engagement', 0)) for post in significant_posts)
        negative_posts = [post for post in significant_posts if post.get('sentiment') == 'Negative']
        negative_percentage = (len(negative_posts) / len(significant_posts)) * 100 if significant_posts else 0

        # Prepare posts data with properly formatted datetime
        posts_data = []
        for post in significant_posts:
            post_data = {
                'content': str(post.get('content', '')),
                'platform': str(post.get('platform', 'Unknown')),
                'sentiment': str(post.get('sentiment', 'Neutral')),
                'engagement': convert_engagement(post.get('engagement', 0)),
                'url': str(post.get('url', '')),
                'username': str(post.get('username', 'anonymous')),
                'timestamp': format_datetime(post.get('timestamp', datetime.now()))
            }
            posts_data.append(post_data)

        # Create conversation prompt optimized for Llama 4 Maverick
        conversation = [
            {
                "role": "system",
                "content": """You are an expert brand reputation analyst. Your task is to analyze social media data 
                and identify potential PR crises. Provide your analysis in valid JSON format only.
                
                Important: Your response must be a valid JSON object. Do not include any additional text or formatting."""
            },
            {
                "role": "user",
                "content": f"""Analyze these social media posts for {keyword}:

Key Metrics:
- Total Posts: {len(significant_posts)}
- Negative Posts: {len(negative_posts)}
- Negative Rate: {negative_percentage:.1f}%
- Total Engagement: {total_engagement:,}

Return a JSON object with this exact structure:
{{
    "is_crisis": true/false,
    "title": "Crisis title",
    "description": "Crisis description",
    "risk_level": "High/Medium/Low",
    "main_concerns": ["concern1", "concern2"],
    "affected_platforms": ["platform1", "platform2"],
    "posts": {len(negative_posts)},
    "percentage": {negative_percentage:.1f},
    "engagement": {total_engagement},
    "all_crisis_posts": {json.dumps(posts_data[:5])}
}}"""
            }
        ]

        # Get analysis using Llama 4 Maverick
        response = client.chat.completions.create(
            messages=conversation,
            model=GROQ_MODEL,
            temperature=0.1,
            max_tokens=2000,
            top_p=0.9,
            stream=False
        )

        try:
            # Clean the response text
            response_text = response.choices[0].message.content.strip()
            # Remove any potential markdown code block markers
            response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            # Parse JSON
            analysis = json.loads(response_text)
            
            # Validate required fields
            required_fields = ['is_crisis', 'title', 'description', 'risk_level', 'main_concerns', 
                             'affected_platforms', 'posts', 'percentage', 'engagement', 'all_crisis_posts']
            
            missing_fields = [field for field in required_fields if field not in analysis]
            if missing_fields:
                st.error(f"Missing required fields in analysis: {missing_fields}")
                return None
            
            # Add brand information and timestamp
            analysis['brand'] = keyword
            analysis['analyzed_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Clean and validate numeric values
            try:
                analysis['posts'] = int(analysis['posts'])
                analysis['percentage'] = float(analysis['percentage'])
                analysis['engagement'] = int(analysis['engagement'])
            except (ValueError, TypeError) as e:
                st.error(f"Error converting numeric values: {str(e)}")
                return None
            
            # Ensure risk_level is valid
            if analysis['risk_level'] not in ['High', 'Medium', 'Low']:
                analysis['risk_level'] = 'Medium'

            # Ensure lists are valid
            analysis['main_concerns'] = list(analysis['main_concerns'])
            analysis['affected_platforms'] = list(analysis['affected_platforms'])
            
            return analysis

        except json.JSONDecodeError as e:
            st.error(f"Error parsing JSON response: {str(e)}")
            st.error(f"Raw response: {response_text}")
            return None
        except Exception as e:
            st.error(f"Error processing analysis: {str(e)}")
            return None

    except Exception as e:
        st.error(f"Error in crisis detection: {str(e)}")
        return None