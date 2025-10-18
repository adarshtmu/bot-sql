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

import streamlit as st
import pandas as pd
import numpy as np
import json
import time
from typing import Tuple, Any, Dict, List
from datetime import datetime

# LLM Integration
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

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
        "prompt": "Create a new feature `performance_score` = (score * 0.7) + (attendance * 0.3). Calculate correlation between `performance_score` and `passed`. Round to 3 decimals, assign to `result`.",
        "dataset": "students", "validator": "numeric_tol", "points": 20,
        "starter_code": "# Create performance_score feature\n# Calculate correlation with 'passed'\n\nresult = None"
    }
]

# LLM Functions
def get_gemini_model():
    if "gemini_api_key" in st.session_state and st.session_state.gemini_api_key:
        try:
            if GEMINI_AVAILABLE:
                genai.configure(api_key=st.session_state.gemini_api_key)
                return genai.GenerativeModel('gemini-2.0-flash')
        except Exception as e:
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
    except:
        return {"is_correct": False, "score": 0.5, "feedback": "AI error", "strengths": ["Attempt"], "improvements": ["Review"], "points_earned": int(question["points"] * 0.5)}

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
        return {"is_correct": is_correct, "score": score, "feedback": "AI error", "code_quality": "unknown", "strengths": ["Executed"], "improvements": ["Review
