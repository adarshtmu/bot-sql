"""
AI-Powered Data Science Practice Platform
Enterprise-Grade EdTech UI with Advanced Features

Features:
- Modern, professional UI inspired by leading EdTech platforms
- Real-time AI mentor feedback with Gemini integration
- Interactive progress tracking and analytics dashboard
- Smooth animations and transitions
- Responsive design with dark/light themes
- Comprehensive performance reports with visualizations
"""

import os
import streamlit as st
import pandas as pd
import numpy as np
import json
import time
from typing import Tuple, Any, Dict, List
from datetime import datetime
import streamlit.components.v1 as components

# LLM Integration
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# HARD-CODED GEMINI KEY (set your key here)
# WARNING: Hard-coding secrets in source files is insecure for production.
# Replace the placeholder below with your actual key if you understand the risks,
# or better: set via environment variable and load from os.environ.
HARD_CODED_GEMINI_API_KEY = "AIzaSyCipiGM8HxiPiVtfePpGN-TiIk5JVBO6_M"

st.set_page_config(
    page_title="DataMentor AI - Practice Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS with Modern EdTech Design
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
    else:
        bg_primary = "#f8fafc"
        bg_secondary = "#ffffff"
        bg_card = "#ffffff"
        text_primary = "#0f172a"
        text_secondary = "#64748b"
        accent_primary = "#6366f1"
        accent_secondary = "#8b5cf6"
        border_color = "#e2e8f0"
    
    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {{
        font-family: 'Inter', sans-serif;
    }}
    
    .stApp {{
        background: {bg_primary};
        color: {text_primary};
    }}
    
    /* Hide Streamlit branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    
    /* Custom Header */
    .platform-header {{
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary});
        padding: 24px 32px;
        border-radius: 0 0 24px 24px;
        margin: -60px -48px 32px -48px;
        box-shadow: 0 10px 40px rgba(99, 102, 241, 0.2);
    }}
    
    .header-content {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        max-width: 1400px;
        margin: 0 auto;
    }}
    
    .logo-section {{
        display: flex;
        align-items: center;
        gap: 16px;
    }}
    
    .logo {{
        font-size: 32px;
        font-weight: 800;
        color: white;
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    
    .logo-icon {{
        font-size: 40px;
        animation: float 3s ease-in-out infinite;
    }}
    
    @keyframes float {{
        0%, 100% {{ transform: translateY(0px); }}
        50% {{ transform: translateY(-10px); }}
    }}
    
    .tagline {{
        color: rgba(255, 255, 255, 0.9);
        font-size: 14px;
        font-weight: 500;
        letter-spacing: 0.5px;
    }}
    
    /* Hero Section */
    .hero-section {{
        background: linear-gradient(135deg, {bg_card}, {bg_secondary});
        border-radius: 24px;
        padding: 48px;
        margin: 32px 0;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08);
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
        background: radial-gradient(circle, rgba(99, 102, 241, 0.05) 0%, transparent 70%);
        animation: rotate 20s linear infinite;
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
        font-size: 56px;
        font-weight: 800;
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 16px;
        line-height: 1.2;
    }}
    
    .hero-subtitle {{
        font-size: 20px;
        color: {text_secondary};
        margin-bottom: 32px;
        font-weight: 500;
    }}
    
    .feature-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 16px;
        margin-top: 32px;
    }}
    
    .feature-item {{
        background: {bg_card};
        padding: 20px;
        border-radius: 16px;
        border: 1px solid {border_color};
        text-align: center;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }}
    
    .feature-item:hover {{
        transform: translateY(-4px);
        box-shadow: 0 12px 24px rgba(99, 102, 241, 0.15);
    }}
    
    .feature-icon {{
        font-size: 32px;
        margin-bottom: 12px;
    }}
    
    .feature-title {{
        font-size: 14px;
        font-weight: 600;
        color: {text_primary};
        margin-bottom: 4px;
    }}
    
    .feature-desc {{
        font-size: 12px;
        color: {text_secondary};
    }}
    
    /* Card Components */
    .modern-card {{
        background: {bg_card};
        border-radius: 20px;
        padding: 32px;
        margin: 24px 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
        border: 1px solid {border_color};
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }}
    
    .modern-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
    }}
    
    .card-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 24px;
        padding-bottom: 16px;
        border-bottom: 2px solid {border_color};
    }}
    
    .card-title {{
        font-size: 24px;
        font-weight: 700;
        color: {text_primary};
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    
    /* Question Card */
    .question-card {{
        background: {bg_card};
        border-radius: 20px;
        padding: 32px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
        border: 2px solid {border_color};
        margin: 24px 0;
    }}
    
    .question-header {{
        display: flex;
        justify-content: space-between;
        align-items: start;
        margin-bottom: 24px;
    }}
    
    .question-number {{
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary});
        color: white;
        width: 48px;
        height: 48px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        font-weight: 700;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }}
    
    .question-meta {{
        display: flex;
        gap: 12px;
        align-items: center;
    }}
    
    .difficulty-badge {{
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}
    
    .diff-easy {{
        background: linear-gradient(135deg, #10b981, #059669);
        color: white;
    }}
    
    .diff-medium {{
        background: linear-gradient(135deg, #f59e0b, #d97706);
        color: white;
    }}
    
    .diff-hard {{
        background: linear-gradient(135deg, #ef4444, #dc2626);
        color: white;
    }}
    
    .points-badge {{
        background: {bg_secondary};
        border: 2px solid {accent_primary};
        color: {accent_primary};
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
    }}
    
    /* Progress Components */
    .progress-section {{
        background: linear-gradient(135deg, {bg_card}, {bg_secondary});
        border-radius: 20px;
        padding: 24px;
        margin: 24px 0;
        border: 1px solid {border_color};
    }}
    
    .progress-header {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }}
    
    .progress-title {{
        font-size: 16px;
        font-weight: 600;
        color: {text_primary};
    }}
    
    .progress-value {{
        font-size: 14px;
        font-weight: 700;
        color: {accent_primary};
    }}
    
    .progress-bar-container {{
        background: {bg_secondary};
        border-radius: 12px;
        height: 12px;
        overflow: hidden;
        position: relative;
    }}
    
    .progress-bar-fill {{
        height: 100%;
        background: linear-gradient(90deg, {accent_primary}, {accent_secondary});
        border-radius: 12px;
        transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }}
    
    .progress-bar-fill::after {{
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
        animation: shimmer 2s infinite;
    }}
    
    @keyframes shimmer {{
        0% {{ transform: translateX(-100%); }}
        100% {{ transform: translateX(100%); }}
    }}
    
    /* Stats Grid */
    .stats-grid {{
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin: 24px 0;
    }}
    
    .stat-card {{
        background: linear-gradient(135deg, {bg_card}, {bg_secondary});
        border-radius: 16px;
        padding: 24px;
        border: 1px solid {border_color};
        text-align: center;
        transition: transform 0.3s ease;
    }}
    
    .stat-card:hover {{
        transform: scale(1.05);
    }}
    
    .stat-value {{
        font-size: 36px;
        font-weight: 800;
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 8px;
    }}
    
    .stat-label {{
        font-size: 14px;
        color: {text_secondary};
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }}
    
    /* AI Feedback */
    .ai-feedback-container {{
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
        border: 2px solid {accent_primary};
        border-radius: 20px;
        padding: 28px;
        margin: 24px 0;
        position: relative;
        overflow: hidden;
    }}
    
    .ai-feedback-container::before {{
        content: '';
        position: absolute;
        top: -50%;
        right: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, transparent 70%);
        animation: pulse 4s ease-in-out infinite;
    }}
    
    @keyframes pulse {{
        0%, 100% {{ opacity: 0.5; }}
        50% {{ opacity: 1; }}
    }}
    
    .ai-badge {{
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary});
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 16px;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3);
    }}
    
    .feedback-content {{
        position: relative;
        z-index: 1;
    }}
    
    .feedback-score {{
        text-align: center;
        padding: 32px;
        margin: 24px 0;
    }}
    
    .score-circle {{
        width: 160px;
        height: 160px;
        border-radius: 50%;
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary});
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        margin: 0 auto 16px;
        box-shadow: 0 12px 40px rgba(99, 102, 241, 0.4);
        position: relative;
    }}
    
    .score-circle::before {{
        content: '';
        position: absolute;
        inset: 8px;
        background: {bg_card};
        border-radius: 50%;
    }}
    
    .score-content {{
        position: relative;
        z-index: 1;
        text-align: center;
    }}
    
    .score-number {{
        font-size: 48px;
        font-weight: 800;
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary});
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }}
    
    .score-label {{
        font-size: 14px;
        color: {text_secondary};
        font-weight: 600;
    }}
    
    /* Insight Boxes */
    .insight-box {{
        border-radius: 16px;
        padding: 20px;
        margin: 16px 0;
        border-left: 4px solid;
    }}
    
    .insight-strength {{
        background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05));
        border-left-color: #22c55e;
    }}
    
    .insight-weakness {{
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.05));
        border-left-color: #ef4444;
    }}
    
    .insight-recommendation {{
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(59, 130, 246, 0.05));
        border-left-color: #3b82f6;
    }}
    
    .insight-title {{
        font-size: 16px;
        font-weight: 700;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }}
    
    /* Buttons */
    .stButton > button {{
        background: linear-gradient(135deg, {accent_primary}, {accent_secondary}) !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 14px 32px !important;
        border-radius: 12px !important;
        border: none !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(99, 102, 241, 0.3) !important;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 24px rgba(99, 102, 241, 0.4) !important;
    }}
    
    /* Code Editor Styling */
    .stCodeBlock {{
        border-radius: 12px !important;
        border: 1px solid {border_color} !important;
    }}
    
    /* Input Fields */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {{
        border-radius: 12px !important;
        border: 2px solid {border_color} !important;
        padding: 12px 16px !important;
        font-size: 14px !important;
        transition: border-color 0.3s ease !important;
    }}
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {{
        border-color: {accent_primary} !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
    }}
    
    /* Success/Error Messages */
    .element-container .stAlert {{
        border-radius: 12px !important;
        border: none !important;
        padding: 16px 20px !important;
    }}
    
    /* Animations */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .fade-in {{
        animation: fadeIn 0.6s ease;
    }}
    
    /* Learning Path */
    .learning-path-item {{
        background: {bg_card};
        border: 2px solid {border_color};
        border-radius: 16px;
        padding: 24px;
        margin: 16px 0;
        transition: all 0.3s ease;
    }}
    
    .learning-path-item:hover {{
        border-color: {accent_primary};
        transform: translateX(8px);
    }}
    
    .priority-high {{
        border-left: 4px solid #ef4444;
    }}
    
    .priority-medium {{
        border-left: 4px solid #f59e0b;
    }}
    
    .priority-low {{
        border-left: 4px solid #22c55e;
    }}
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] {{
        background: {bg_secondary} !important;
        border-right: 1px solid {border_color} !important;
    }}
    
    [data-testid="stSidebar"] .element-container {{
        padding: 8px 0;
    }}
    </style>
    """

# Datasets
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

# Questions Bank
QUESTIONS = [
    {
        "id": 1, "type": "theory", "difficulty": "easy",
        "title": "Bias-Variance Tradeoff",
        "prompt": "Explain the bias-variance tradeoff in supervised machine learning. What do high bias and high variance indicate? Provide one method to reduce each.",
        "points": 10
    },
    {
        "id": 2, "type": "theory", "difficulty": "medium",
        "title": "Cross-Validation",
        "prompt": "Explain k-fold cross-validation in detail. How does it work, why is it better than a single train/test split, and what are potential drawbacks?",
        "points": 15
    },
    {
        "id": 3, "type": "theory", "difficulty": "easy",
        "title": "Feature Scaling",
        "prompt": "Why is feature scaling important in machine learning? Explain standardization vs normalization and give two examples of algorithms that require scaling.",
        "points": 10
    },
    {
        "id": 4, "type": "theory", "difficulty": "hard",
        "title": "Precision vs Recall",
        "prompt": "Explain precision and recall in classification. When would you prioritize one over the other? Provide a real-world scenario for each case and explain the F1 score.",
        "points": 20
    },
    {
        "id": 5, "type": "code", "difficulty": "easy",
        "title": "Correlation Analysis",
        "prompt": "Using the `students` DataFrame as `df`, calculate the Pearson correlation coefficient between `hours_studied` and `score`. Round to 3 decimal places and assign to `result`.",
        "dataset": "students", "validator": "numeric_tol", "points": 10,
        "starter_code": "# Calculate correlation between hours_studied and score\n# Round to 3 decimal places\n\nresult = None"
    },
    {
        "id": 6, "type": "code", "difficulty": "medium",
        "title": "Train-Test Split",
        "prompt": "Split the `students` DataFrame into 70% train and 30% test sets using random_state=42. Calculate the mean `score` of the test set, round to 2 decimal places, assign to `result`.",
        "dataset": "students", "validator": "numeric_tol", "points": 15,
        "starter_code": "# Split data: 70% train, 30% test\n# Calculate mean score of test set\n\nresult = None"
    },
    {
        "id": 7, "type": "code", "difficulty": "medium",
        "title": "Group Aggregation",
        "prompt": "Using the `sales` DataFrame, find the total sales for each region. Return a dictionary where keys are region names and values are total sales. Assign to `result`.",
        "dataset": "sales", "validator": "dict_compare", "points": 15,
        "starter_code": "# Group by region and sum sales\n# Return as dictionary\n\nresult = None"
    },
    {
        "id": 8, "type": "code", "difficulty": "hard",
        "title": "Feature Engineering",
        "prompt": "Create a new feature `performance_score` = (score * 0.7) + (attendance * 0.3). Calculate correlation between `performance_score` and `passed`. Round to 3 decimals and assign to `result`.",
        "dataset": "students", "validator": "numeric_tol", "points": 20,
        "starter_code": "# Create performance_score feature\n# Calculate correlation with 'passed'\n\nresult = None"
    }
]

# LLM Functions
def get_gemini_model():
    # Prefer explicit hard-coded key if provided, otherwise session state or environment
    api_key = None
    if HARD_CODED_GEMINI_API_KEY and HARD_CODED_GEMINI_API_KEY != "REPLACE_WITH_YOUR_GEMINI_KEY":
        api_key = HARD_CODED_GEMINI_API_KEY
    elif "gemini_api_key" in st.session_state and st.session_state.gemini_api_key:
        api_key = st.session_state.gemini_api_key
    elif "GEMINI_API_KEY" in os.environ:
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        return None

    try:
        if GEMINI_AVAILABLE:
            genai.configure(api_key=api_key)
            return genai.GenerativeModel('gemini-2.0-flash-exp')
    except Exception:
        return None
    return None

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
    "feedback": "2-3 sentences",
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
    except Exception:
        return {"is_correct": False, "score": 0.5, "feedback": "AI error", "strengths": ["Attempt"], "improvements": ["Review"], "points_earned": int(question["points"] * 0.5)}

def get_ai_feedback_code(question: dict, code: str, result_value: Any, expected: Any, is_correct: bool, stats: dict, model) -> Dict:
    """
    Analyze code answers using Gemini model when available.
    Robust fallback when model is None or an error occurs.
    """
    # Fallback deterministic response when model is not available
    if not model:
        score = 1.0 if is_correct else 0.3
        return {
            "is_correct": is_correct,
            "score": score,
            "feedback": "Correct!" if is_correct else "Incorrect",
            "code_quality": "N/A",
            "strengths": ["Executed"],
            "improvements": ["Review"],
            "points_earned": int(score * question.get("points", 0))
        }

    # Construct prompt for the LLM
    prompt = f"""Analyze this Data Science code solution.

Question ({question.get('difficulty')}, {question.get('points')} points):
{question.get('prompt')}

Code:
```python
{code}

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
        return {"is_correct": is_correct, "score": score, "feedback": "AI error", "code_quality": "unknown", "strengths": ["Executed"], "improvements": ["Review"], "points_earned": int(question["point[...]

def generate_final_report(all_answers: List[Dict], model) -> Dict:
    if not model:
        return {
            "overall_feedback": "Practice completed! Configure AI for detailed analysis.",
            "strengths": ["Completed all questions"],
            "weaknesses": ["AI unavailable"],
            "recommendations": ["Set up AI mentor"],
            "learning_path": []
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

# Code Execution
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

# Session State
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

# Apply CSS
st.markdown(get_advanced_css(st.session_state.theme), unsafe_allow_html=True)

# Get AI Model
ai_model = get_gemini_model()

# Sidebar
with st.sidebar:
    st.markdown("### 🎓 DataMentor AI")
    st.markdown("---")
    
    st.markdown("#### 🤖 AI Mentor Setup")
    api_key_input = st.text_input("Gemini API Key", type="password", value=st.session_state.gemini_api_key, placeholder="Enter API key")
    
    if api_key_input != st.session_state.gemini_api_key:
        st.session_state.gemini_api_key = api_key_input
        st.session_state.api_key_validated = False
        st.rerun()
    
    if st.session_state.gemini_api_key and not st.session_state.api_key_validated:
        if st.button("🔑 Validate Key", use_container_width=True):
            try:
                if GEMINI_AVAILABLE:
                    genai.configure(api_key=st.session_state.gemini_api_key)
                    test_model = genai.GenerativeModel('gemini-2.0-flash-exp')
                    test_model.generate_content("Test", generation_config=genai.types.GenerationConfig(max_output_tokens=10))
                    st.session_state.api_key_validated = True
                    st.success("✅ API Key Valid!")
                    time.sleep(1)
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Invalid Key")
    
    if st.session_state.api_key_validated:
        st.success("🤖 AI Mentor Active")
    else:
        st.warning("⚠️ AI Mentor Inactive")
        with st.expander("📖 Get API Key"):
            st.markdown("""
            **Get FREE Gemini API Key:**
            1. Visit: [AI Studio](https://aistudio.google.com/app/apikey)
            2. Sign in with Google
            3. Create API Key
            4. Paste above
            """)
    
    st.markdown("---")
    
    if st.button("🌓 Toggle Theme", use_container_width=True):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()
    
    if st.session_state.started and not st.session_state.completed:
        st.markdown("---")
        st.markdown("#### 📊 Progress")
        progress = len(st.session_state.user_answers) / len(QUESTIONS)
        st.markdown(f'<div class="progress-bar-container"><div class="progress-bar-fill" style="width: {progress*100}%"></div></div>', unsafe_allow_html=True)
        st.markdown(f"**{len(st.session_state.user_answers)}/{len(QUESTIONS)}** completed")
        
        if st.session_state.user_answers:
            correct = sum(1 for a in st.session_state.user_answers if a.get("is_correct"))
            points = sum(a.get("points_earned", 0) for a in st.session_state.user_answers)
            st.metric("✅ Correct", f"{correct}/{len(st.session_state.user_answers)}")
            st.metric("⭐ Points", points)

# Main Content
if not st.session_state.started:
    # Platform Header
    st.markdown("""
    <div class="platform-header">
        <div class="header-content">
            <div class="logo-section">
                <div class="logo">
                    <span class="logo-icon">🎓</span>
                    <span>DataMentor AI</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
# Hero Section
    components.html("""
    <div class="hero-section">
        <div class="hero-content">
            <div class="hero-title">Master Data Science</div>
            <div class="hero-subtitle">AI-powered practice platform with personalized feedback and adaptive learning</div>
            
            <div class="feature-grid">
                <div class="feature-item">
                    <div class="feature-icon">🧠</div>
                    <div class="feature-title">8 Challenges</div>
                    <div class="feature-desc">Theory + Coding</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">🤖</div>
                    <div class="feature-title">AI Mentor</div>
                    <div class="feature-desc">Real-time feedback</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">📊</div>
                    <div class="feature-title">Analytics</div>
                    <div class="feature-desc">Track progress</div>
                </div>
                <div class="feature-item">
                    <div class="feature-icon">🎯</div>
                    <div class="feature-title">Personalized</div>
                    <div class="feature-desc">Custom learning path</div>
                </div>
            </div>
        </div>
    </div>
    """, height=400)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Practice Session", use_container_width=True, type="primary"):
            st.session_state.started = True
            st.session_state.start_time = datetime.now()
            st.rerun()
    
    # Info sections
    st.markdown('<div class="modern-card fade-in">', unsafe_allow_html=True)
    st.markdown("### 📚 What You'll Practice")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Theory Questions (4)**")
        st.markdown("- Bias-Variance Tradeoff")
        st.markdown("- Cross-Validation")
        st.markdown("- Feature Scaling")
        st.markdown("- Precision & Recall")
    with col2:
        st.markdown("**Coding Challenges (4)**")
        st.markdown("- Correlation Analysis")
        st.markdown("- Train-Test Split")
        st.markdown("- Data Aggregation")
        st.markdown("- Feature Engineering")
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.completed:
    # Platform Header
    st.markdown("""
    <div class="platform-header">
        <div class="header-content">
            <div class="logo-section">
                <div class="logo">
                    <span class="logo-icon">🎓</span>
                    <span>DataMentor AI</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Calculate stats
    total_points = sum(a.get("points_earned", 0) for a in st.session_state.user_answers)
    max_points = sum(q["points"] for q in QUESTIONS)
    correct = sum(1 for a in st.session_state.user_answers if a.get("is_correct"))
    percentage = (total_points / max_points) * 100
    
    # Score Display
    st.markdown(f"""
    <div class="modern-card fade-in">
        <div class="feedback-score">
            <div style="font-size: 48px; margin-bottom: 16px;">🎉</div>
            <div style="font-size: 32px; font-weight: 800; margin-bottom: 24px;">Practice Session Complete!</div>
            <div class="score-circle">
                <div class="score-content">
                    <div class="score-number">{percentage:.0f}%</div>
                    <div class="score-label">SCORE</div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats Grid
    st.markdown('<div class="stats-grid">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{total_points}</div><div class="stat-label">Total Points</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{correct}/8</div><div class="stat-label">Correct</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="stat-card"><div class="stat-value">{len(st.session_state.user_answers)}</div><div class="stat-label">Completed</div></div>', unsafe_allow_html=True)
    with col4:
        duration = (datetime.now() - st.session_state.start_time).seconds // 60
        st.markdown(f'<div class="stat-card"><div class="stat-value">{duration}</div><div class="stat-label">Minutes</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Generate report if not exists
    if not st.session_state.final_report:
        with st.spinner("🤖 AI Mentor analyzing your performance..."):
            st.session_state.final_report = generate_final_report(st.session_state.user_answers, ai_model)
    
    report = st.session_state.final_report
    
    # Overall Feedback
    st.markdown('<div class="modern-card fade-in">', unsafe_allow_html=True)
    st.markdown("### 🤖 AI Mentor's Overall Assessment")
    st.markdown(f"_{report.get('overall_feedback', 'Great effort!')}_")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Strengths & Weaknesses
    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<div class="modern-card fade-in">', unsafe_allow_html=True)
        st.markdown("### 💪 Strengths")
        for strength in report.get('strengths', [])[:3]:
            st.markdown(f'<div class="insight-box insight-strength">✅ {strength}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="modern-card fade-in">', unsafe_allow_html=True)
        st.markdown("### 📈 Areas to Improve")
        for weakness in report.get('weaknesses', [])[:3]:
            st.markdown(f'<div class="insight-box insight-weakness">📚 {weakness}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Recommendations
    st.markdown('<div class="modern-card fade-in">', unsafe_allow_html=True)
    st.markdown("### 🎯 Personalized Recommendations")
    for rec in report.get('recommendations', [])[:3]:
        st.markdown(f'<div class="insight-box insight-recommendation">💡 {rec}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Learning Path
    learning_path = report.get('learning_path', [])
    if learning_path:
        st.markdown('<div class="modern-card fade-in">', unsafe_allow_html=True)
        st.markdown("### 🗺️ Your Personalized Learning Path")
        for item in learning_path[:3]:
            priority = item.get('priority', 'medium')
            st.markdown(f"""
            <div class="learning-path-item priority-{priority}">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;">
                    <div style="font-size: 18px; font-weight: 700;">{item.get('topic', 'Topic')}</div>
                    <span class="difficulty-badge diff-{'hard' if priority == 'high' else 'medium' if priority == 'medium' else 'easy'}">{priority} priority</span>
                </div>
                <div style="color: {st.session_state.theme == 'dark' and '#94a3b8' or '#64748b'};">{item.get('resources', 'Practice recommended')}</div>
            </div>
            """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Closing Message
    if 'closing_message' in report:
        st.markdown(f"""
        <div class="modern-card fade-in" style="text-align: center; padding: 40px;">
            <div style="font-size: 24px; font-weight: 700; margin-bottom: 16px;">💫</div>
            <div style="font-size: 18px; font-style: italic; color: {'#94a3b8' if st.session_state.theme == 'dark' else '#64748b'};">
                "{report['closing_message']}"
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔄 Start New Session", use_container_width=True, type="primary"):
            for key in ['user_answers', 'current_q', 'started', 'completed', 'final_report']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

else:
    # Platform Header
    st.markdown("""
    <div class="platform-header">
        <div class="header-content">
            <div class="logo-section">
                <div class="logo">
                    <span class="logo-icon">🎓</span>
                    <span>DataMentor AI</span>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Active Question
    if st.session_state.current_q < len(QUESTIONS):
        q = QUESTIONS[st.session_state.current_q]
        
        # Question Card
        st.markdown(f"""
        <div class="question-card fade-in">
            <div class="question-header">
                <div class="question-number">{q['id']}</div>
                <div class="question-meta">
                    <span class="difficulty-badge diff-{q['difficulty']}">{q['difficulty']}</span>
                    <span class="points-badge">{q['points']} points</span>
                </div>
            </div>
            <div style="margin-bottom: 24px;">
                <div style="font-size: 24px; font-weight: 700; margin-bottom: 12px;">{q['title']}</div>
                <div style="font-size: 16px; line-height: 1.6; color: {'#94a3b8' if st.session_state.theme == 'dark' else '#64748b'};">{q['prompt']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if q['type'] == 'theory':
            answer = st.text_area("Your Answer:", height=200, placeholder="Write your detailed answer here...")
            
            if st.button("Submit Answer", type="primary"):
                if answer.strip():
                    with st.spinner("🤖 AI Mentor analyzing your answer..."):
                        ai_analysis = get_ai_feedback_theory(q, answer, ai_model)
                        
                        st.session_state.user_answers.append({
                            "id": q['id'],
                            "title": q['title'],
                            "type": q['type'],
                            "difficulty": q['difficulty'],
                            "answer": answer,
                            "ai_analysis": ai_analysis,
                            "is_correct": ai_analysis.get("is_correct"),
                            "points_earned": ai_analysis.get("points_earned"),
                            "max_points": q['points']
                        })
                        
                        # Show feedback
                        score = ai_analysis.get("score", 0)
                        is_correct = ai_analysis.get("is_correct", False)
                        
                        if is_correct:
                            status_color = "#22c55e"
                            emoji = "✅"
                        elif score >= 0.5:
                            status_color = "#f59e0b"
                            emoji = "⚡"
                        else:
                            status_color = "#ef4444"
                            emoji = "📚"
                        
                        st.markdown(f"""
                        <div class="ai-feedback-container fade-in">
                            <div class="feedback-content">
                                <div class="ai-badge">{emoji} AI MENTOR FEEDBACK</div>
                                <div style="font-size: 20px; font-weight: 700; color: {status_color}; margin-bottom: 16px;">
                                    Score: {ai_analysis.get('points_earned', 0)}/{q['points']} points ({score*100:.0f}%)
                                </div>
                                <div style="margin-bottom: 20px;">{ai_analysis.get('feedback', '')}</div>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 24px;">
                                    <div>
                                        <div class="insight-title">💪 Strengths</div>
                                        {''.join([f'<div class="insight-box insight-strength">{s}</div>' for s in ai_analysis.get('strengths', [])])}
                                    </div>
                                    <div>
                                        <div class="insight-title">📈 Improvements</div>
                                        {''.join([f'<div class="insight-box insight-weakness">{i}</div>' for i in ai_analysis.get('improvements', [])])}
                                    </div>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        st.session_state.current_q += 1
                        if st.session_state.current_q >= len(QUESTIONS):
                            st.session_state.completed = True
                        
                        if st.button("➡️ Next Question", type="primary"):
                            st.rerun()
                else:
                    st.warning("Please provide an answer before submitting.")
        
        else:  # Code question
            if 'dataset' in q:
                with st.expander("📊 View Dataset"):
                    st.dataframe(DATASETS[q['dataset']], use_container_width=True)
            
            code = st.text_area("Your Code:", value=q.get('starter_code', ''), height=200)
            
            if st.button("▶️ Run Code", type="primary"):
                if code.strip():
                    success, result, error, stats = safe_execute_code(code, DATASETS.get(q['dataset'], pd.DataFrame()))
                    
                    if success and result is not None:
                        expected = REFERENCE_RESULTS.get(q['id'])
                        validator = globals()[f"validator_{q['validator']}"]
                        is_correct, msg = validator(result, expected)
                        
                        with st.spinner("🤖 AI Mentor analyzing your code..."):
                            ai_analysis = get_ai_feedback_code(q, code, result, expected, is_correct, stats, ai_model)
                            
                            st.session_state.user_answers.append({
                                "id": q['id'],
                                "title": q['title'],
                                "type": q['type'],
                                "difficulty": q['difficulty'],
                                "code": code,
                                "result": result,
                                "expected": expected,
                                "ai_analysis": ai_analysis,
                                "is_correct": is_correct,
                                "points_earned": ai_analysis.get("points_earned"),
                                "max_points": q['points']
                            })
                            
                            # Show feedback
                            score = ai_analysis.get("score", 0)
                            
                            if is_correct:
                                status_color = "#22c55e"
                                emoji = "✅"
                            elif score >= 0.5:
                                status_color = "#f59e0b"
                                emoji = "⚡"
                            else:
                                status_color = "#ef4444"
                                emoji = "❌"
                            
                            st.markdown(f"""
                            <div class="ai-feedback-container fade-in">
                                <div class="feedback-content">
                                    <div class="ai-badge">{emoji} AI MENTOR FEEDBACK</div>
                                    <div style="font-size: 20px; font-weight: 700; color: {status_color}; margin-bottom: 16px;">
                                        Score: {ai_analysis.get('points_earned', 0)}/{q['points']} points ({score*100:.0f}%)
                                    </div>
                                    
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                                        <div>
                                            <div style="font-weight: 600; margin-bottom: 8px;">Your Result:</div>
                                            <code>{result}</code>
                                        </div>
                                        <div>
                                            <div style="font-weight: 600; margin-bottom: 8px;">Expected:</div>
                                            <code>{expected}</code>
                                        </div>
                                    </div>
                                    
                                    <div style="margin-bottom: 20px;">{ai_analysis.get('feedback', '')}</div>
                                    
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 24px;">
                                        <div>
                                            <div class="insight-title">💪 Code Strengths</div>
                                            {''.join([f'<div class="insight-box insight-strength">{s}</div>' for s in ai_analysis.get('strengths', [])])}
                                        </div>
                                        <div>
                                            <div class="insight-title">📈 Improvements</div>
                                            {''.join([f'<div class="insight-box insight-weakness">{i}</div>' for i in ai_analysis.get('improvements', [])])}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.session_state.current_q += 1
                            if st.session_state.current_q >= len(QUESTIONS):
                                st.session_state.completed = True
                            
                            if st.button("➡️ Next Question", type="primary"):
                                st.rerun()
                    else:
                        st.error(error)
                else:
                    st.warning("Please write code before running.")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px; color: #94a3b8; font-size: 14px;">
    <div style="margin-bottom: 8px;">🎓 <strong>DataMentor AI</strong> - Your Personal Data Science Practice Platform</div>
    <div>Powered by Gemini AI | Built with Streamlit</div>
</div>
""", unsafe_allow_html=True)













