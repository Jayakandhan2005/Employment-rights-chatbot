import plotly.graph_objects as go
import pandas as pd
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
from views.display import display_response_templates
try:
    nltk.download("vader_lexicon", quiet=True)
    sia = SentimentIntensityAnalyzer()
except Exception as e:
    st.error(f"Error setting up NLTK: {str(e)}")
def create_sentiment_distribution_chart(sentiment_data):
    labels = ["Positive", "Neutral", "Negative"]
    values = [
        sentiment_data["positive_count"],
        sentiment_data["neutral_count"],
        sentiment_data["negative_count"]
    ]
    colors = ['#2ecc71', '#95a5a6', '#e74c3c']
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.4,
        marker=dict(colors=colors)
    )])
    
    fig.update_layout(
        title="Sentiment Distribution",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Poppins, sans-serif")
    )
    
    return fig




def create_sentiment_trend_chart(data):
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    
    # Ensure timestamp is datetime type and sort by timestamp
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    
    # Create daily averages for more granular trend
    df['date'] = df['timestamp'].dt.date
    daily_sentiment = df.groupby('date').agg({
        'polarity': ['mean', 'count']
    }).reset_index()
    daily_sentiment.columns = ['date', 'polarity', 'count']
    
    # Create the figure
    fig = go.Figure()
    
    # Add main trend line
    fig.add_trace(go.Scatter(
        x=daily_sentiment['date'],
        y=daily_sentiment['polarity'],
        mode='lines+markers',
        line=dict(
            color='#4b6cb7',
            width=2,
            shape='spline',  # Makes the line curved
            smoothing=0.3
        ),
        marker=dict(
            size=8,
            color='#4b6cb7',
            line=dict(
                color='white',
                width=1
            )
        ),
        name='Sentiment Trend'
    ))
    
    # Add confidence band
    rolling_mean = daily_sentiment['polarity'].rolling(window=3, center=True).mean()
    rolling_std = daily_sentiment['polarity'].rolling(window=3, center=True).std()
    
    fig.add_trace(go.Scatter(
        x=daily_sentiment['date'].tolist() + daily_sentiment['date'].tolist()[::-1],
        y=(rolling_mean + rolling_std).tolist() + (rolling_mean - rolling_std).tolist()[::-1],
        fill='toself',
        fillcolor='rgba(75,108,183,0.1)',
        line=dict(color='rgba(255,255,255,0)'),
        name='Confidence Band',
        showlegend=False
    ))
    
    # Update layout with modern styling
    fig.update_layout(
        title={
            'text': "Sentiment Trend Over Time",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=20, family="Poppins, sans-serif")
        },
        xaxis_title="Date",
        yaxis_title="Sentiment Score",
        height=350,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Poppins, sans-serif"),
        yaxis=dict(
            range=[-1, 1],
            tickvals=[-1, -0.5, 0, 0.5, 1],
            ticktext=['Very Negative', 'Negative', 'Neutral', 'Positive', 'Very Positive'],
            gridcolor='rgba(75,108,183,0.1)',
            zerolinecolor='rgba(75,108,183,0.2)'
        ),
        xaxis=dict(
            gridcolor='rgba(75,108,183,0.1)',
            showgrid=True
        ),
        showlegend=False,
        hovermode='x unified'
    )
    
    # Add hover template
    fig.update_traces(
        hovertemplate="<b>Date:</b> %{x}<br>" +
                      "<b>Sentiment:</b> %{y:.2f}<br>" +
                      "<extra></extra>"
    )
    
    return fig
def create_platform_distribution_chart(data):
    """Create platform distribution chart with blue bars and platform logos"""
    # Count platform occurrences
    platform_counts = {}
    for post in data:
        platform = post['platform']
        platform_counts[platform] = platform_counts.get(platform, 0) + 1

    # Platform icons using Base64 encoded images
    platform_icons = {
        'Twitter': "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSIjMURBMUYyIj48cGF0aCBkPSJNMjMuOTUzIDQuNTdhMTAgMTAgMCAwMS0yLjgyNS43NzUgNC45NTggNC45NTggMCAwMDIuMTYzLTIuNzIzYy0uOTUxLjU1NS0yLjAwNS45NTktMy4xMjcgMS4xODRhNC45MiA0LjkyIDAgMDAtOC4zODQgNC40ODJDN...",
        'Reddit': "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSIjRkY0NTAwIj48cGF0aCBkPSJNMTIgMEExMiAxMiAwIDAwMCAxMmExMiAxMiAwIDAwMTIgMTIgMTIgMTIgMCAwMDEyLTEyQTEyIDEyIDAgMDAxMiAw...",
        'YouTube': "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSIjRkYwMDAwIj48cGF0aCBkPSJNMjMuNDk4IDYuMTg2YTMuMDE2IDMuMDE2IDAgMDAtMi4xMjItMi4xMzZDMTkuNTA1IDMuNTQ1IDEyIDMuNTQ1IDEyIDMuNTQ1cy03LjUwNSAwLTkuMzc3LjUwNUEzLjAxNyAzLjAxNyAwIDAwLjUwMiA2LjE4NkMwIDguMDcgMCAxMiAwIDEyczAgMy45My41MDIgNS44MTRhMy4wMTYgMy4wMTYgMCAwMDIuMTIyIDIuMTM2YzEuODcxLjUwNSA5LjM3Ni41MDUgOS4zNzYuNTA1czguMzA1IDAgMTAuMTc3LS41MDVhMy4wMTUgMy4wMTUgMC...",
        'Instagram': "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSIjRTEzMDZDIj48cGF0aCBkPSJNMTIgMi4xNjNjMy4yMDQgMCAzLjU4NC4wMTIgNC44NS4wNyAzLjI1Mi4xNDggNC43NzEgMS42OTEgNC45MTkgNC45MTkuMDU4IDEuMjY1LjA2OSAxLjY0NS4wNjkgNC44NDkgMCAzLjIwNS0uMDEyIDMuNTg0LS4wNjkgNC44NDktLjE0OSAzLjIyNS0xLjY2NCA0Ljc3MS00LjkxOSA0LjkxOS0xLjI2Ni4wNTgtMS42NDQuMDctNC44NS4wNy0zLjIwNCAwLTMuNTg0LS4wMTItNC44NDktLjA3LTMuMjYtLjE0OS00Ljc3MS0xLjY5OS00LjkxOS00LjkyLS4wNTgtMS4yNjUtLjA3LTEuNjQ0LS4wNy00Ljg0OSAwLTMuMjA0LjAxMy0zLjU4My4wNy00Ljg0OS4xNDktMy4yMjcgMS42NjQtNC43NzEgNC45MTktNC45MTkgMS4yNjYtLjA1NyAxLjY0NS0uMDY5IDQuODQ5LS4wNjl6TTEyIDBoLTIuMTYzYy0zLjI1OSAwLTMuNjY3LjAxNC00Ljk0Ny4wNzItNC4zNTguMi02Ljc4IDIuNjE4LTYuOTggNi45OC0uMDU5IDEuMjgxLS4wNzMgMS42ODktLjA3MyA0Ljk0OCAwIDMuMjU5LjAxNCAzLjY2OC4wNzIgNC45NDguMiA0LjM1OCAyLjYxOCA2Ljc4IDYuOTggNi45OC4wNTkgMS4yODEuMDczIDEuNjg5LjA3MyA0Ljk0OCAwIDMuMjU5LS4wMTQgMy42NjctLjA3MiA0Ljk0Ny0uMiA0LjM1NC0yLjYxNyA2Ljc4Mi02Ljk4IDYuOTc5LTEuMjgxLjA1OS0xLjY5LjA3My00Ljk0OS4wNzNzLTMuNjY3LS4wMTQtNC45NDctLjA3MmMtNC4zNTQtLjItNi43ODItMi42MTctNi45NzktNi45NzktLjA1OS0xLjI4MS0uMDczLTEuNjk0LS4wNzMtNC45NDkgMC0zLjI1OS4wMTQtMy42NjcuMDcyLTQuOTQ3LjI0NC00LjM1NC0yLjYxNy02Ljc4Mi02Ljk3OS02Ljk3OSAxLjI4MS0uMDU5IDEuNjk0LS4wNzMgNC45NDktLjA3M3oiLz48L3N2Zz4=",
        'News': "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSIjMkI2Q0IwIj48cGF0aCBkPSJNNyAxM2gxMHYxSDd6bTAtNGg1djFIN3ptMTAgOEg3di0xaDEwem0yLTEzdjE4SDV2LTJIMXYtNGgydi0ySDFWOGgyVjZIMVY0aDR2MTRoMTRWNGgtNnYtMmgxMnoiLz48L3N2Zz4="
    }

    # Create bar chart
    fig = go.Figure()

    # Add blue bars
    fig.add_trace(go.Bar(
        x=list(platform_counts.keys()),
        y=list(platform_counts.values()),
        marker_color='#1e40af',
        text=list(platform_counts.values()),
        textposition='outside',
    ))

    # Add platform logos as images
    for i, (platform, count) in enumerate(platform_counts.items()):
        if platform in platform_icons:
            fig.add_layout_image(
                dict(
                    source=platform_icons[platform],
                    xref="x",
                    yref="y",
                    x=platform,
                    y=count + (max(platform_counts.values()) * 0.15),  # Position above bar
                    sizex=0.5,  # Adjust size of logo
                    sizey=0.5,  # Adjust size of logo
                    xanchor="center",
                    yanchor="bottom"
                )
            )

    # Update layout
    fig.update_layout(
        title={
            'text': "Platform Distribution",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': dict(size=24, family="Poppins, sans-serif", color="#1e3a8a")
        },
        xaxis_title=None,
        yaxis_title="Number of Posts",
        height=500,
        margin=dict(l=20, r=20, t=100, b=20),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Poppins, sans-serif"),
        showlegend=False,
        xaxis=dict(
            showgrid=False,
            showline=True,
            linecolor='#e2e8f0',
            linewidth=2,
            ticks='outside',
            tickfont=dict(
                family='Poppins',
                size=12,
                color='#1e3a8a',
            ),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#e2e8f0',
            showline=True,
            linecolor='#e2e8f0',
            linewidth=2,
            ticks='outside',
            tickfont=dict(
                family='Poppins',
                size=12,
                color='#1e3a8a',
            ),
        ),
        bargap=0.4,
        images=[]  # Initialize empty images list
    )

    return fig