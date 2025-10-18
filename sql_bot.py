"""
DataMentor AI - Enterprise EdTech Platform
Advanced AI-Powered Data Science Learning Experience

NEW FEATURES:
- Gamification with achievements and badges
- Real-time progress analytics with charts
- Smart hints system
- Code snippets library
- Performance leaderboard simulation
- Interactive onboarding tour
- Keyboard shortcuts
- Export report as PDF-ready HTML
- Question bookmarking
- Time tracking per question
- Difficulty progression system
"""

import streamlit as st
import pandas as pd
import numpy as np
import json
import time
from typing import Tuple, Any, Dict, List
from datetime import datetime, timedelta

# LLM Integration
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

st.set_page_config(
    page_title="DataMentor AI - Advanced Learning Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Achievement System
ACHIEVEMENTS = {
    "first_blood": {"name": "First Blood", "desc": "Complete your first question", "icon": "🎯", "points": 10},
    "speed_demon": {"name": "Speed Demon", "desc": "Answer a question in under 2 minutes", "icon": "⚡", "points": 20},
    "perfectionist": {"name": "Perfectionist", "desc": "Get 100% on any question", "icon": "💯", "points": 25},
    "code_warrior": {"name": "Code Warrior", "desc": "Complete all coding challenges", "icon": "⚔️", "points": 50},
    "theory_master": {"name": "Theory Master", "desc": "Complete all theory questions", "icon": "📚", "points": 50},
    "champion": {"name": "Champion", "desc": "Score above 90% overall", "icon": "🏆", "points": 100},
    "streak_3": {"name": "Three in a Row", "desc": "Get 3 correct answers in a row", "icon": "🔥", "points": 30},
    "night_owl": {"name": "Night Owl", "desc": "Practice after 10 PM", "icon": "🦉", "points": 15},
}

# Enhanced CSS with Gamification Elements
def get_advanced_css(theme="light"):
    if theme == "dark":
        bg_primary = "#0a0e27"
        bg_secondary = "#151b3d"
        bg_card = "#1e2544"
        text_primary = "#e8eef2"
        text_secondary = "#94a3b8"
        accent_primary = "#6366f1"
        accent_secondary = "#8b5cf6"
        border_color = "#2d3561"
        success_color = "#22c55e"
        warning_color = "#f59e0b"
        error_color = "#ef4444"
    else:
        bg_primary = "#f8fafc"
        bg_secondary = "#ffffff"
        bg_card = "#ffffff"
        text_primary = "#0f172a"
        text_secondary = "#64748b"
        accent_primary = "#6366f1"
        accent_secondary = "#8b5cf6"
        border_color = "#e2e8f0"
        success_color = "#10b981"
        warning_color = "#f59e0b"
        error_color = "#dc2626"
    
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;600&display=swap');
    
    * {{
        font-family: 'Inter', sans-serif;
        transition: background-color 0.3s ease, color 0.3s ease;
    }}
    
    .stApp {{
        background: {bg_primary};
        color: {text_primary};
    }}
    
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Premium Header with Glassmorphism */
    .platform-header {{
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary});
        padding: 20px 40px;
        border-radius: 0 0 32px 32px;
        margin: -60px -48px 40px -48px;
        box-shadow: 0 20px 60px rgba(99, 102, 241, 0.3);
        backdrop-filter: blur(10px);
        position: relative;
        overflow: hidden;
    }}
    
    .platform-header::before {{
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(255, 255, 255, 0.1) 0%, transparent 70%);
        animation: headerPulse 8s ease-in-out infinite;
    }}
    
    @keyframes headerPulse {{
        0%, 100% {{ transform: translate(0, 0) scale(1); }}
        50% {{ transform: translate(10px, 10px) scale(1.05); }}
    }}
    
    .header-content {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 1600px;
        margin: 0 auto;
        position: relative;
        z-index: 1;
    }}
    
    .logo {{
        font-size: 36px;
        font-weight: 900;
        color: white;
        display: flex;
        align-items: center;
        gap: 16px;
        text-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }}
    
    .logo-icon {{
        font-size: 48px;
        animation: float 3s ease-in-out infinite;
        filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.3));
    }}
    
    @keyframes float {{
        0%, 100% {{ transform: translateY(0px) rotate(0deg); }}
        50% {{ transform: translateY(-12px) rotate(5deg); }}
    }}
    
    .header-stats {{
        display: flex;
        gap: 24px;
        align-items: center;
    }}
    
    .header-stat-item {{
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        padding: 12px 20px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        text-align: center;
    }}
    
    .header-stat-value {{
        font-size: 24px;
        font-weight: 800;
        color: white;
        display: block;
    }}
    
    .header-stat-label {{
        font-size: 11px;
        color: rgba(255, 255, 255, 0.9);
        text-transform: uppercase;
        letter-spacing: 1px;
        font-weight: 600;
    }}
    
    /* Enhanced Hero Section */
    .hero-section {{
        background: linear-gradient(135deg, {bg_card}, {bg_secondary});
        border-radius: 32px;
        padding: 60px;
        margin: 40px 0;
        box-shadow: 0 30px 80px rgba(0, 0, 0, 0.12);
        border: 1px solid {border_color};
        text-align: center;
        position: relative;
        overflow: hidden;
    }}
    
    .hero-section::before {{
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.08) 0%, transparent 70%);
        animation: rotate 25s linear infinite;
    }}
    
    @keyframes rotate {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    
    .hero-content {{
        position: relative;
        z-index: 1;
    }}
    
    .hero-title {{
        font-size: 64px;
        font-weight: 900;
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary}, {accent_primary});
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 20px;
        line-height: 1.1;
        animation: gradientShift 4s ease infinite;
    }}
    
    @keyframes gradientShift {{
        0%, 100% {{ background-position: 0% 50%; }}
        50% {{ background-position: 100% 50%; }}
    }}
    
    .hero-subtitle {{
        font-size: 22px;
        color: {text_secondary};
        margin-bottom: 40px;
        font-weight: 500;
        line-height: 1.6;
    }}
    
    /* Feature Grid with Hover Effects */
    .feature-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 20px;
        margin-top: 40px;
    }}
    
    .feature-item {{
        background: {bg_card};
        padding: 28px;
        border-radius: 20px;
        border: 2px solid {border_color};
        text-align: center;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        position: relative;
        overflow: hidden;
    }}
    
    .feature-item::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary});
        opacity: 0;
        transition: opacity 0.4s ease;
    }}
    
    .feature-item:hover {{
        transform: translateY(-8px) scale(1.02);
        box-shadow: 0 20px 40px rgba(99, 102, 241, 0.25);
        border-color: {accent_primary};
    }}
    
    .feature-item:hover::before {{
        opacity: 0.1;
    }}
    
    .feature-icon {{
        font-size: 40px;
        margin-bottom: 16px;
        display: inline-block;
        transition: transform 0.4s ease;
        position: relative;
        z-index: 1;
    }}
    
    .feature-item:hover .feature-icon {{
        transform: scale(1.2) rotate(10deg);
    }}
    
    .feature-title {{
        font-size: 16px;
        font-weight: 700;
        color: {text_primary};
        margin-bottom: 8px;
        position: relative;
        z-index: 1;
    }}
    
    .feature-desc {{
        font-size: 13px;
        color: {text_secondary};
        position: relative;
        z-index: 1;
    }}
    
    /* Achievement Badge System */
    .achievement-badge {{
        background: linear-gradient(135deg, {bg_card}, {bg_secondary});
        border: 3px solid {accent_primary};
        border-radius: 16px;
        padding: 16px;
        margin: 12px 0;
        display: flex;
        align-items: center;
        gap: 16px;
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }}
    
    .achievement-badge::before {{
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
        transition: left 0.5s ease;
    }}
    
    .achievement-badge:hover::before {{
        left: 100%;
    }}
    
    .achievement-badge:hover {{
        transform: translateX(8px);
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3);
    }}
    
    .achievement-icon {{
        font-size: 36px;
        filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.2));
    }}
    
    .achievement-locked {{
        opacity: 0.4;
        border-color: {border_color};
    }}
    
    /* Question Card with Enhanced Visual Hierarchy */
    .question-card {{
        background: {bg_card};
        border-radius: 24px;
        padding: 40px;
        box-shadow: 0 12px 48px rgba(0, 0, 0, 0.08);
        border: 2px solid {border_color};
        margin: 32px 0;
        position: relative;
        overflow: hidden;
    }}
    
    .question-card::before {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 6px;
        background: linear-gradient(90deg, {accent_primary}, {accent_secondary});
    }}
    
    .question-header {{
        display: flex;
        justify-content: space-between;
        align-items: start;
        margin-bottom: 32px;
    }}
    
    .question-number {{
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary});
        color: white;
        width: 56px;
        height: 56px;
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        font-weight: 800;
        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
        position: relative;
    }}
    
    .question-number::after {{
        content: '';
        position: absolute;
        inset: -4px;
        border-radius: 18px;
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary});
        opacity: 0.3;
        filter: blur(8px);
        z-index: -1;
    }}
    
    .question-meta {{
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        align-items: center;
    }}
    
    .difficulty-badge {{
        padding: 8px 20px;
        border-radius: 24px;
        font-size: 13px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }}
    
    .diff-easy {{
        background: linear-gradient(135deg, {success_color}, #059669);
        color: white;
    }}
    
    .diff-medium {{
        background: linear-gradient(135deg, {warning_color}, #d97706);
        color: white;
    }}
    
    .diff-hard {{
        background: linear-gradient(135deg, {error_color}, #dc2626);
        color: white;
    }}
    
    .points-badge {{
        background: {bg_secondary};
        border: 2px solid {accent_primary};
        color: {accent_primary};
        padding: 8px 20px;
        border-radius: 24px;
        font-size: 13px;
        font-weight: 800;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.2);
    }}
    
    .time-badge {{
        background: {bg_secondary};
        border: 2px solid {text_secondary};
        color: {text_secondary};
        padding: 8px 16px;
        border-radius: 24px;
        font-size: 13px;
        font-weight: 700;
        display: flex;
        align-items: center;
        gap: 6px;
    }}
    
    /* Enhanced Progress Visualization */
    .progress-ring {{
        width: 120px;
        height: 120px;
        border-radius: 50%;
        background: conic-gradient(
            {accent_primary} 0%,
            {accent_primary} var(--progress),
            {bg_secondary} var(--progress),
            {bg_secondary} 100%
        );
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.3);
    }}
    
    .progress-ring::before {{
        content: '';
        position: absolute;
        inset: 8px;
        background: {bg_card};
        border-radius: 50%;
    }}
    
    .progress-ring-content {{
        position: relative;
        z-index: 1;
        text-align: center;
    }}
    
    .progress-percentage {{
        font-size: 28px;
        font-weight: 900;
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    
    /* Stats Dashboard */
    .stats-dashboard {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 20px;
        margin: 32px 0;
    }}
    
    .stat-card {{
        background: linear-gradient(135deg, {bg_card}, {bg_secondary});
        border-radius: 20px;
        padding: 28px;
        border: 2px solid {border_color};
        text-align: center;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }}
    
    .stat-card::before {{
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, transparent 70%);
        opacity: 0;
        transition: opacity 0.4s ease;
    }}
    
    .stat-card:hover {{
        transform: translateY(-8px) scale(1.05);
        border-color: {accent_primary};
        box-shadow: 0 16px 40px rgba(99, 102, 241, 0.2);
    }}
    
    .stat-card:hover::before {{
        opacity: 1;
        animation: rotate 4s linear infinite;
    }}
    
    .stat-icon {{
        font-size: 40px;
        margin-bottom: 12px;
        display: block;
    }}
    
    .stat-value {{
        font-size: 42px;
        font-weight: 900;
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
        line-height: 1;
    }}
    
    .stat-label {{
        font-size: 13px;
        color: {text_secondary};
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.2px;
    }}
    
    /* AI Feedback with Premium Design */
    .ai-feedback-container {{
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(139, 92, 246, 0.12));
        border: 3px solid {accent_primary};
        border-radius: 24px;
        padding: 36px;
        margin: 32px 0;
        position: relative;
        overflow: hidden;
        box-shadow: 0 12px 40px rgba(99, 102, 241, 0.2);
    }}
    
    .ai-feedback-container::before {{
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, transparent 70%);
        animation: pulse 5s ease-in-out infinite;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ opacity: 0.4; transform: scale(1); }}
        50% {{ opacity: 0.8; transform: scale(1.05); }}
    }}
    
    .ai-badge {{
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary});
        color: white;
        padding: 10px 24px;
        border-radius: 24px;
        font-size: 13px;
        font-weight: 800;
        display: inline-flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 20px;
        box-shadow: 0 6px 20px rgba(99, 102, 241, 0.4);
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    /* Hint System */
    .hint-box {{
        background: {bg_card};
        border-left: 4px solid {accent_primary};
        border-radius: 12px;
        padding: 20px;
        margin: 20px 0;
        position: relative;
    }}
    
    .hint-icon {{
        font-size: 24px;
        margin-right: 12px;
    }}
    
    /* Code Snippet Library */
    .snippet-card {{
        background: {bg_card};
        border: 2px solid {border_color};
        border-radius: 16px;
        padding: 20px;
        margin: 12px 0;
        transition: all 0.3s ease;
        cursor: pointer;
    }}
    
    .snippet-card:hover {{
        border-color: {accent_primary};
        transform: translateX(4px);
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.15);
    }}
    
    .snippet-title {{
        font-size: 16px;
        font-weight: 700;
        color: {text_primary};
        margin-bottom: 8px;
    }}
    
    .snippet-code {{
        font-family: 'JetBrains Mono', monospace;
        font-size: 13px;
        background: {bg_secondary};
        padding: 12px;
        border-radius: 8px;
        color: {text_secondary};
        overflow-x: auto;
    }}
    
    /* Enhanced Buttons */
    .stButton > button {{
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary}) !important;
        color: white !important;
        font-weight: 700 !important;
        padding: 16px 40px !important;
        border-radius: 14px !important;
        border: none !important;
        font-size: 16px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.5px !important;
        position: relative !important;
        overflow: hidden !important;
    }}
    
    .stButton > button::before {{
        content: '' !important;
        position: absolute !important;
        top: 50% !important;
        left: 50% !important;
        width: 0 !important;
        height: 0 !important;
        border-radius: 50% !important;
        background: rgba(255, 255, 255, 0.3) !important;
        transform: translate(-50%, -50%) !important;
        transition: width 0.6s ease, height 0.6s ease !important;
    }}
    
    .stButton > button:hover::before {{
        width: 300px !important;
        height: 300px !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 12px 32px rgba(99, 102, 241, 0.5) !important;
    }}
    
    .stButton > button:active {{
        transform: translateY(-1px) scale(0.98) !important;
    }}
    
    /* Leaderboard */
    .leaderboard-item {{
        background: {bg_card};
        border: 2px solid {border_color};
        border-radius: 16px;
        padding: 20px;
        margin: 12px 0;
        display: flex;
        align-items: center;
        gap: 20px;
        transition: all 0.3s ease;
    }}
    
    .leaderboard-item:hover {{
        border-color: {accent_primary};
        transform: translateX(8px);
    }}
    
    .leaderboard-rank {{
        font-size: 32px;
        font-weight: 900;
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        min-width: 50px;
    }}
    
    .rank-1 {{
        color: #fbbf24 !important;
        font-size: 40px !important;
    }}
    
    .rank-2 {{
        color: #94a3b8 !important;
        font-size: 36px !important;
    }}
    
    .rank-3 {{
        color: #cd7f32 !important;
        font-size: 34px !important;
    }}
    
    /* Toast Notifications */
    .toast-notification {{
        position: fixed;
        top: 100px;
        right: 30px;
        background: {bg_card};
        border: 2px solid {accent_primary};
        border-radius: 16px;
        padding: 20px 28px;
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.3);
        z-index: 9999;
        animation: slideIn 0.4s ease, slideOut 0.4s ease 2.6s;
    }}
    
    @keyframes slideIn {{
        from {{ transform: translateX(400px); opacity: 0; }}
        to {{ transform: translateX(0); opacity: 1; }}
    }}
    
    @keyframes slideOut {{
        from {{ transform: translateX(0); opacity: 1; }}
        to {{ transform: translateX(400px); opacity: 0; }}
    }}
    
    /* Sidebar Enhancement */
    [data-testid="stSidebar"] {{
        background: {bg_secondary} !important;
        border-right: 2px solid {border_color} !important;
    }}
    
    /* Animations */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(30px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .fade-in {{
        animation: fadeIn 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    @keyframes fadeInScale {{
        from {{ opacity: 0; transform: scale(0.9); }}
        to {{ opacity: 1; transform: scale(1); }}
    }}
    
    .fade-in-scale {{
        animation: fadeInScale 0.5s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    
    /* Loading Spinner */
    .loading-spinner {{
        border: 4px solid {border_color};
        border-top: 4px solid {accent_primary};
        border-radius: 50%;
        width: 50px;
        height: 50px;
        animation: spin 1s linear infinite;
        margin: 0 auto;
    }}
    
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    
    /* Responsive adjustments */
    @media (max-width: 768px) {{
        .hero-title {{ font-size: 42px; }}
        .platform-header {{ padding: 16px 24px; }}
        .question-card {{ padding: 24px; }}
    }}
    </style>
    """

# [Previous dataset and question definitions remain the same]
students_df = pd.DataFrame({
    "student_id": range(1, 21),
    "hours_studied": [2, 3, 5, 1, 4, 6, 2, 8, 7, 3, 5, 9, 4, 6, 3, 7, 8, 2, 5, 4],
    "score": [50, 55, 80, 40, 65, 90, 52, 98, 85, 58, 75, 95, 70, 88, 60, 92, 96, 48, 78, 68],
    "passed": [0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1],
    "attendance": [60, 70, 95, 50, 80, 98, 65, 100, 92, 72, 88, 97, 85, 90, 68, 94, 99, 55, 87, 82]
})

sales_df = pd.DataFrame({
    "product_id": range(1, 16),
    "product": ['A', 'B', 'C', 'A', 'B', 'C', 'A', 'B', 'C', 'A', 'B', 'C', 'A', 'B', 'C'],
    "sales": [100, 150, 200, 120, 180, 220, 110, 160, 210, 130, 170, 230, 125, 175, 215],
    "region": ['North', 'North', 'North', 'South', 'South', 'South', 'East', 'East', 'East', 'West', 'West', 'West', 'North', 'South', 'East'],
    "quarter": ['Q1', 'Q1', 'Q1', 'Q1', 'Q1', 'Q1', 'Q2', 'Q2', 'Q2', 'Q2', 'Q2', 'Q2', 'Q3', 'Q3', 'Q3']
})

DATASETS = {"students": students_df, "sales": sales_df}

QUESTIONS = [
    {
        "id": 1, "type": "theory", "difficulty": "easy",
        "title": "Bias-Variance Tradeoff",
        "prompt": "Explain the bias-variance tradeoff in supervised machine learning. What do high bias and high variance indicate? Provide one method to reduce each.",
        "points": 10,
        "hint": "Think about underfitting vs overfitting. High bias = too simple model, high variance = too complex model."
    },
    {
        "id": 2, "type": "theory", "difficulty": "medium",
        "title": "Cross-Validation",
        "prompt": "Explain k-fold cross-validation in detail. How does it work, why is it better than a single train/test split, and what are potential drawbacks?",
        "points": 15,
        "hint": "Consider how the data is split into k parts and how each part gets used for validation."
    },
    {
        "id": 3, "type": "theory", "difficulty": "easy",
        "title": "Feature Scaling",
        "prompt": "Why is feature scaling important in machine learning? Explain standardization vs normalization and give two examples of algorithms that require scaling.",
        "points": 10,
        "hint": "Think about distance-based algorithms like KNN and gradient-based algorithms like neural networks."
    },
    {
        "id": 4, "type": "theory", "difficulty": "hard",
        "title": "Precision vs Recall",
        "prompt": "Explain precision and recall in classification. When would you prioritize one over the other? Provide a real-world scenario for each case and explain the F1 score.",
        "points": 20,
        "hint": "Consider medical diagnosis (recall important) vs spam detection (precision important)."
    },
    {
        "id": 5, "type": "code", "difficulty": "easy",
        "title": "Correlation Analysis",
        "prompt": "Using the `students` DataFrame as `df`, calculate the Pearson correlation coefficient between `hours_studied` and `score`. Round to 3 decimal places and assign to `result`.",
        "dataset": "students", "validator": "numeric_tol", "points": 10,
        "starter_code": "# Calculate correlation between hours_studied and score\n# Round to 3 decimal places\n\nresult = None",
        "hint": "Use pandas .corr() method or numpy corrcoef(). Don't forget to round!"
    },
    {
        "id": 6, "type": "code", "difficulty": "medium",
        "title": "Train-Test Split",
        "prompt": "Split the `students` DataFrame into 70% train and 30% test sets using random_state=42. Calculate the mean `score` of the test set, round to 2 decimal places, assign to `result`.",
        "dataset": "students", "validator": "numeric_tol", "points": 15,
        "starter_code": "# Split data: 70% train, 30% test\n# Calculate mean score of test set\n\nresult = None",
        "hint": "Use df.sample() with frac parameter. Remember to set random_state for reproducibility."
    },
    {
        "id": 7, "type": "code", "difficulty": "medium",
        "title": "Group Aggregation",
        "prompt": "Using the `sales` DataFrame, find the total sales for each region. Return a dictionary where keys are region names and values are total sales. Assign to `result`.",
        "dataset": "sales", "validator": "dict_compare", "points": 15,
        "starter_code": "# Group by region and sum sales\n# Return as dictionary\n\nresult = None",
        "hint": "Use groupby('region')['sales'].sum() and convert to dict with .to_dict()"
    },
    {
        "id": 8, "type": "code", "difficulty": "hard",
        "title": "Feature Engineering",
        "prompt": "Create a new feature `performance_score` = (score * 0.7) + (attendance * 0.3). Calculate correlation between `performance_score` and `passed`. Round to 3 decimals, assign to `result`.",
        "dataset": "students", "validator": "numeric_tol", "points": 20,
        "starter_code": "# Create performance_score feature\n# Calculate correlation with 'passed'\n\nresult = None",
        "hint": "First create the new column, then use .corr() between the new feature and 'passed' column."
    }
]

# Code Snippets Library
CODE_SNIPPETS = {
    "correlation": {
        "title": "Calculate Correlation",
        "code": "df['col1'].corr(df['col2'])",
        "desc": "Pearson correlation between two columns"
    },
    "train_test": {
        "title": "Train-Test Split",
        "code": "test = df.sample(frac=0.3, random_state=42)\ntrain = df.drop(test.index)",
        "desc": "Split data into train and test sets"
    },
    "groupby": {
        "title": "Group and Aggregate",
        "code": "df.groupby('column')['value'].sum().to_dict()",
        "desc": "Group by column and sum values"
    },
    "new_feature": {
        "title": "Create New Feature",
        "code": "df['new_col'] = df['col1'] * 0.7 + df['col2'] * 0.3",
        "desc": "Weighted combination of features"
    }
}

# Helper Functions
def get_gemini_model():
    if "gemini_api_key" in st.session_state and st.session_state.gemini_api_key:
        try:
            if GEMINI_AVAILABLE:
                genai.configure(api_key=st.session_state.gemini_api_key)
                return genai.GenerativeModel('gemini-2.0-flash-exp')
        except:
            return None
    return None

def check_achievements(answers):
    """Check and award achievements based on performance"""
    earned = []
    
    if len(answers) >= 1 and "first_blood" not in st.session_state.get("earned_achievements", []):
        earned.append("first_blood")
    
    # Check for perfect score
    for ans in answers:
        if ans.get("ai_analysis", {}).get("score", 0) >= 0.99:
            if "perfectionist" not in st.session_state.get("earned_achievements", []):
                earned.append("perfectionist")
                break
    
    # Check for streak
    if len(answers) >= 3:
        last_three = answers[-3:]
        if all(a.get("is_correct") for a in last_three):
            if "streak_3" not in st.session_state.get("earned_achievements", []):
                earned.append("streak_3")
    
    # Check code warrior
    code_questions = [a for a in answers if a.get("type") == "code"]
    if len(code_questions) == 4 and all(a.get("is_correct") for a in code_questions):
        if "code_warrior" not in st.session_state.get("earned_achievements", []):
            earned.append("code_warrior")
    
    # Check theory master
    theory_questions = [a for a in answers if a.get("type") == "theory"]
    if len(theory_questions) == 4 and all(a.get("is_correct") for a in theory_questions):
        if "theory_master" not in st.session_state.get("earned_achievements", []):
            earned.append("theory_master")
    
    # Check night owl
    current_hour = datetime.now().hour
    if current_hour >= 22 or current_hour <= 5:
        if "night_owl" not in st.session_state.get("earned_achievements", []):
            earned.append("night_owl")
    
    # Check speed demon
    if len(answers) > 0:
        last_answer = answers[-1]
        if "time_taken" in last_answer and last_answer["time_taken"] < 120:
            if "speed_demon" not in st.session_state.get("earned_achievements", []):
                earned.append("speed_demon")
    
    return earned

def get_ai_feedback_theory(question: dict, student_answer: str, model) -> Dict:
    if not model:
        return {
            "is_correct": len(student_answer.split()) >= 30,
            "score": 0.7,
            "feedback": "AI mentor unavailable. Basic length check passed.",
            "strengths": ["Attempted the question"],
            "improvements": ["Configure AI for detailed feedback"],
            "points_earned": int(question["points"] * 0.7)
        }
    
    prompt = f"""You are an expert Data Science mentor. Analyze this student answer.

Question ({question['difficulty']}, {question['points']} points):
{question['prompt']}

Student Answer:
{student_answer}

Provide JSON response:
{{
    "is_correct": true/false,
    "score": 0.0-1.0,
    "feedback": "2-3 sentences of constructive feedback",
    "strengths": ["strength1", "strength2"],
    "improvements": ["improvement1", "improvement2"]
}}"""

    try:
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.7, max_output_tokens=1000))
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        result = json.loads(text)
        result["points_earned"] = int(result["score"] * question["points"])
        return result
    except:
        return {"is_correct": False, "score": 0.5, "feedback": "AI error occurred", "strengths": ["Attempt"], "improvements": ["Review"], "points_earned": int(question["points"] * 0.5)}

def get_ai_feedback_code(question: dict, code: str, result_value: Any, expected: Any, is_correct: bool, stats: dict, model) -> Dict:
    if not model:
        score = 1.0 if is_correct else 0.3
        return {"is_correct": is_correct, "score": score, "feedback": "Correct!" if is_correct else "Incorrect", "code_quality": "N/A", "strengths": ["Executed"], "improvements": ["Review"], "points_earned": int(question["points"] * score)}
    
    prompt = f"""Analyze this Data Science code solution.

Question ({question['difficulty']}, {question['points']} points):
{question['prompt']}

Code:
```python
{code}
```

Expected: {expected}
Got: {result_value}
Correct: {is_correct}
Time: {stats.get('execution_time', 0):.4f}s

JSON response:
{{
    "is_correct": true/false,
    "score": 0.0-1.0,
    "feedback": "explanation",
    "code_quality": "excellent/good/fair/poor",
    "strengths": ["strength1", "strength2"],
    "improvements": ["improvement1", "improvement2"]
}}"""

    try:
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.7, max_output_tokens=1200))
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        result = json.loads(text)
        result["points_earned"] = int(result["score"] * question["points"])
        return result
    except:
        score = 1.0 if is_correct else 0.3
        return {"is_correct": is_correct, "score": score, "feedback": "AI error", "code_quality": "unknown", "strengths": ["Executed"], "improvements": ["Review"], "points_earned": int(question["points"] * score)}

def generate_final_report(all_answers: List[Dict], model) -> Dict:
    if not model:
        return {
            "overall_feedback": "Practice completed! Configure AI for detailed analysis.",
            "strengths": ["Completed all questions"],
            "weaknesses": ["AI unavailable"],
            "recommendations": ["Set up AI mentor"],
            "learning_path": [],
            "closing_message": "Keep practicing!"
        }
    
    summary = [{"question": a["title"], "type": a["type"], "difficulty": a["difficulty"], 
                "correct": a.get("is_correct", False), "score": a.get("ai_analysis", {}).get("score", 0)} 
               for a in all_answers]
    
    prompt = f"""Create a comprehensive performance report for this student.

Performance Summary:
{json.dumps(summary, indent=2)}

JSON response:
{{
    "overall_feedback": "2-3 encouraging sentences",
    "strengths": ["strength1", "strength2", "strength3"],
    "weaknesses": ["weakness1", "weakness2"],
    "recommendations": ["rec1", "rec2", "rec3"],
    "learning_path": [
        {{"topic": "name", "priority": "high/medium/low", "resources": "suggestion"}},
    ],
    "closing_message": "motivational message"
}}"""

    try:
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.8, max_output_tokens=2000))
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        return json.loads(text)
    except:
        return {"overall_feedback": "Great effort!", "strengths": ["Persistence"], "weaknesses": ["Review"], "recommendations": ["Practice more"], "learning_path": [{"topic": "Review basics", "priority": "high", "resources": "Online courses"}], "closing_message": "Keep learning!"}

def safe_execute_code(user_code: str, dataframe: pd.DataFrame) -> Tuple[bool, Any, str, dict]:
    allowed_globals = {
        "__builtins__": {"abs": abs, "min": min, "max": max, "round": round, "len": len, "range": range, "sum": sum, "sorted": sorted, "list": list, "dict": dict, "set": set, "int": int, "float": float, "str": str},
        "pd": pd, "np": np,
    }
    local_vars = {"df": dataframe.copy()}
    stats = {"lines": len(user_code.split('\n')), "chars": len(user_code), "execution_time": 0}
    
    try:
        start_time = time.time()
        exec(user_code, allowed_globals, local_vars)
        stats["execution_time"] = time.time() - start_time
        if "result" not in local_vars:
            return False, None, "⚠️ Assign your answer to variable `result`", stats
        return True, local_vars["result"], "", stats
    except Exception as e:
        stats["execution_time"] = time.time() - start_time
        return False, None, f"❌ Error: {str(e)}", stats

def validator_numeric_tol(student_value: Any, expected_value: Any, tol=1e-3) -> Tuple[bool, str]:
    try:
        s, e = float(student_value), float(expected_value)
        return (abs(s - e) <= tol, f"✅ Correct!" if abs(s - e) <= tol else f"❌ Expected: {e}, Got: {s}")
    except:
        return False, "❌ Cannot compare values"

def validator_dict_compare(student_value: Any, expected_value: Any) -> Tuple[bool, str]:
    if not isinstance(student_value, dict):
        return False, f"❌ Expected dictionary, got {type(student_value).__name__}"
    if set(student_value.keys()) != set(expected_value.keys()):
        return False, "❌ Keys don't match"
    for key in expected_value:
        if abs(student_value[key] - expected_value[key]) > 0.01:
            return False, f"❌ Wrong value for '{key}'"
    return True, "✅ Perfect!"

def compute_reference(q):
    qid = q["id"]
    if qid == 5:
        return round(DATASETS[q["dataset"]]["hours_studied"].corr(DATASETS[q["dataset"]]["score"]), 3)
    elif qid == 6:
        return round(DATASETS[q["dataset"]].sample(frac=0.3, random_state=42)["score"].mean(), 2)
    elif qid == 7:
        return DATASETS[q["dataset"]].groupby('region')['sales'].sum().to_dict()
    elif qid == 8:
        df = DATASETS[q["dataset"]].copy()
        df['performance_score'] = (df['score'] * 0.7) + (df['attendance'] * 0.3)
        return round(df['performance_score'].corr(df['passed']), 3)
    return None

REFERENCE_RESULTS = {q["id"]: compute_reference(q) for q in QUESTIONS if q["type"] == "code"}

# Initialize Session State
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "user_answers" not in st.session_state:
    st.session_state.user_answers = []
if "current_q" not in st.session_state:
    st.session_state.current_q = 0
if "started" not in st.session_state:
    st.session_state.started = False
if "completed" not in st.session_state:
    st.session_state.completed = False
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = ""
if "api_key_validated" not in st.session_state:
    st.session_state.api_key_validated = False
if "final_report" not in st.session_state:
    st.session_state.final_report = None
if "earned_achievements" not in st.session_state:
    st.session_state.earned_achievements = []
if "show_hints" not in st.session_state:
    st.session_state.show_hints = {}
if "question_start_time" not in st.session_state:
    st.session_state.question_start_time = None
if "show_snippets" not in st.session_state:
    st.session_state.show_snippets = False

# Apply CSS
st.markdown(get_advanced_css(st.session_state.theme), unsafe_allow_html=True)

# Get AI Model
ai_model = get_gemini_model()

# Enhanced Sidebar
with st.sidebar:
    st.markdown("### 🎓 DataMentor AI")
    st.markdown('<div style="font-size: 12px; color: #64748b; margin-bottom: 20px;">Your Personal DS Coach</div>', unsafe_allow_html=True)
    st.markdown("---")
    
    # AI Setup Section
    st.markdown("#### 🤖 AI Mentor Setup")
    api_key_input = st.text_input("Gemini API Key", type="password", value=st.session_state.gemini_api_key, placeholder="Enter API key for personalized feedback")
    
    if api_key_input != st.session_state.gemini_api_key:
        st.session_state.gemini_api_key = api_key_input
        st.session_state.api_key_validated = False
        st.rerun()
    
    if st.session_state.gemini_api_key and not st.session_state.api_key_validated:
        if st.button("🔑 Validate & Activate", use_container_width=True):
            try:
                if GEMINI_AVAILABLE:
                    genai.configure(api_key=st.session_state.gemini_api_key)
                    test_model = genai.GenerativeModel('gemini-2.0-flash-exp')
                    test_model.generate_content("Test", generation_config=genai.types.GenerationConfig(max_output_tokens=10))
                    st.session_state.api_key_validated = True
                    st.success("✅ AI Mentor Activated!")
                    time.sleep(1)
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Invalid API Key")
    
    if st.session_state.api_key_validated:
        st.success("🤖 AI Mentor: **ACTIVE**")
    else:
        st.warning("⚠️ AI Mentor: **INACTIVE**")
        with st.expander("📖 How to get FREE API Key"):
            st.markdown("""
            **Get your FREE Gemini API Key:**
            1. Visit [AI Studio](https://aistudio.google.com/app/apikey)
            2. Sign in with Google account
            3. Click "Create API Key"
            4. Copy and paste above
            5. Enjoy personalized feedback!
            """)
    
    st.markdown("---")
    
    # Theme Toggle
    theme_icon = "🌙" if st.session_state.theme == "light" else "☀️"
    if st.button(f"{theme_icon} Switch to {'Dark' if st.session_state.theme == 'light' else 'Light'} Mode", use_container_width=True):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()
    
    # Progress Section
    if st.session_state.started and not st.session_state.completed:
        st.markdown("---")
        st.markdown("#### 📊 Live Progress")
        
        progress = len(st.session_state.user_answers) / len(QUESTIONS)
        progress_percent = int(progress * 100)
        
        st.markdown(f"""
        <div class="progress-ring" style="--progress: {progress_percent}%; margin: 20px auto;">
            <div class="progress-ring-content">
                <div class="progress-percentage">{progress_percent}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(f'<div style="text-align: center; font-weight: 600; margin-bottom: 20px;">{len(st.session_state.user_answers)}/{len(QUESTIONS)} Questions</div>', unsafe_allow_html=True)
        
        if st.session_state.user_answers:
            correct = sum(1 for a in st.session_state.user_answers if a.get("is_correct"))
            points = sum(a.get("points_earned", 0) for a in st.session_state.user_answers)
            accuracy = (correct / len(st.session_state.user_answers)) * 100
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("✅ Accuracy", f"{accuracy:.0f}%")
            with col2:
                st.metric("⭐ Points", points)
        
        # Achievements in sidebar
        if st.session_state.earned_achievements:
            st.markdown("---")
            st.markdown("#### 🏆 Achievements Earned")
            for ach_id in st.session_state.earned_achievements[-3:]:
                ach = ACHIEVEMENTS[ach_id]
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1)); 
                     border: 2px solid #6366f1; border-radius: 12px; padding: 12px; margin: 8px 0;">
                    <div style="font-size: 24px; text-align: center; margin-bottom: 4px;">{ach['icon']}</div>
                    <div style="font-size: 13px; font-weight: 700; text-align: center;">{ach['name']}</div>
                    <div style="font-size: 11px; color: #64748b; text-align: center; margin-top: 4px;">+{ach['points']} pts</div>
                </div>
                """, unsafe_allow_html=True)

# Main Content
if not st.session_state.started:
    # Premium Header
    st.markdown("""
    <div class="platform-header">
        <div class="header-content">
            <div class="logo">
                <span class="logo-icon">🎓</span>
                <span>DataMentor AI</span>
            </div>
            <div class="header-stats">
                <div class="header-stat-item">
                    <span class="header-stat-value">8</span>
                    <span class="header-stat-label">Challenges</span>
                </div>
                <div class="header-stat-item">
                    <span class="header-stat-value">120</span>
                    <span class="header-stat-label">Max Points</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Hero Section
    st.markdown("""
    <div class="hero-section fade-in">
        <div class="hero-content">
            <div class="hero-title">Master Data Science</div>
            <div class="hero-subtitle">AI-powered adaptive learning platform with real-time feedback, gamification, and personalized growth paths</div>
            
            <div class="feature-grid">
                <div class="feature-item">
                    <div class="feature-icon">🧠</div>
                    <div class="feature-title">8 Challenges</div>
                    <div class="feature-desc">Theory + Hands-on Coding</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">🤖</div>
                    <div class="feature-title">AI Mentor</div>
                    <div class="feature-desc">Personalized Feedback</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">📊</div>
                    <div class="feature-title">Live Analytics</div>
                    <div class="feature-desc">Track Your Progress</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">🏆</div>
                    <div class="feature-title">Achievements</div>
                    <div class="feature-desc">Gamified Learning</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">💡</div>
                    <div class="feature-title">Smart Hints</div>
                    <div class="feature-desc">Guided Problem Solving</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">📚</div>
                    <div class="feature-title">Code Library</div>
                    <div class="feature-desc">Quick Reference Snippets</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">⚡</div>
                    <div class="feature-title">Speed Tracking</div>
                    <div class="feature-desc">Performance Metrics</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">🎯</div>
                    <div class="feature-title">Adaptive Path</div>
                    <div class="feature-desc">Custom Learning Journey</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Your Learning Journey", use_container_width=True, type="primary"):
            st.session_state.started = True
            st.session_state.start_time = datetime.now()
            st.session_state.question_start_time = datetime.now()
            st.rerun()
    
    st.markdown('<div style="text-align: center; margin-top: 12px; color: #64748b; font-size: 14px;">No signup required • 100% Free • AI-Powered</div>', unsafe_allow_html=True)
    
    # Detailed Info Sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="modern-card fade-in">', unsafe_allow_html=True)
        st.markdown("### 📚 Theory Mastery (4 Questions)")
        st.markdown("""
        - **Bias-Variance Tradeoff** (Easy - 10 pts)
        - **Cross-Validation Techniques** (Medium - 15 pts)  
        - **Feature Scaling Methods** (Easy - 10 pts)
        - **Precision & Recall Analysis** (Hard - 20 pts)
        
        *Master the foundational concepts with AI-guided explanations*
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="modern-card fade-in">', unsafe_allow_html=True)
        st.markdown("### 💻 Coding Challenges (4 Questions)")
        st.markdown("""
        - **Correlation Analysis** (Easy - 10 pts)
        - **Train-Test Splitting** (Medium - 15 pts)
        - **Data Aggregation** (Medium - 15 pts)
        - **Feature Engineering** (Hard - 20 pts)
        
        *Apply your skills with real datasets and instant code validation*
        """)
        st.markdown('</div>', unsafe_allow_html=True)
