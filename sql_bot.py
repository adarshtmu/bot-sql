"""
AI-Powered Data Science Practice Platform
Enterprise-Grade EdTech UI with Advanced Features
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
import re
import ast
import html
escape_html = html.escape

# LLM Integration
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# HARD-CODED GEMINI KEY
HARD_CODED_GEMINI_API_KEY = "AIzaSyCipiGM8HxiPiVtfePpGN-TiIk5JVBO6_M"

st.set_page_config(
    page_title="DataMentor AI - Practice Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Helper Functions
def parse_json_from_text(text: str) -> dict:
    if not text:
        raise ValueError("Empty text")
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.S)
    if m:
        try:
            return json.loads(m.group(1))
        except:
            pass
    start = text.find('{')
    if start != -1:
        depth = 0
        for i in range(start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i+1])
                    except:
                        try:
                            return ast.literal_eval(text[start:i+1])
                        except:
                            break
    raise ValueError("Could not extract JSON")

def simple_local_theory_analyzer(question: dict, student_answer: str) -> dict:
    text = (student_answer or "").lower()
    tokens = set(re.findall(r"\w+", text))
    keywords_by_q = {
        1: {"bias", "variance", "overfitting", "underfitting", "regularization"},
        2: {"k-fold", "cross", "validation", "folds", "train", "test"},
        3: {"scaling", "standardization", "normalization", "z-score", "min-max"},
        4: {"precision", "recall", "f1", "false", "positive", "negative"},
    }
    kws = keywords_by_q.get(question.get("id"), set())
    hits = len([k for k in kws if k in text])
    length_score = min(max(len(text.split()) / 60, 0.0), 1.0)
    kw_score = min(hits / max(len(kws), 1), 1.0)
    score = 0.6 * kw_score + 0.4 * length_score
    feedback = "Good attempt. "
    if score > 0.7:
        feedback += "You covered the main points."
    elif score > 0.4:
        feedback += "You mentioned some concepts but can expand with examples."
    else:
        feedback += "Your answer needs more detail and key terms."
    return {
        "is_correct": score > 0.6,
        "score": float(round(score, 3)),
        "feedback": feedback,
        "strengths": ["Attempted the question"] if score > 0 else [],
        "improvements": ["Expand with examples and definitions"],
        "points_earned": int(round(score * question.get("points", 0)))
    }

def get_gemini_model():
    api_key = HARD_CODED_GEMINI_API_KEY or st.session_state.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        if GEMINI_AVAILABLE:
            genai.configure(api_key=api_key)
            return genai.GenerativeModel('gemini-2.0-flash-exp')
    except:
        return None
    return None

ai_model = get_gemini_model()

def get_ai_feedback_theory(question: dict, student_answer: str, model) -> Dict:
    if not model:
        return simple_local_theory_analyzer(question, student_answer)
    prompt = f"""Analyze this student answer.

Question: {question['prompt']}
Student Answer: {student_answer}

Provide JSON only:
{{
  "is_correct": true/false,
  "score": 0.0-1.0,
  "feedback": "2-3 sentences",
  "strengths": ["point1"],
  "improvements": ["point1"]
}}"""
    try:
        response = model.generate_content(prompt)
        raw_text = response.text.strip()
        parsed = parse_json_from_text(raw_text)
        parsed["score"] = float(parsed.get("score", 0.0))
        parsed["points_earned"] = int(parsed["score"] * question["points"])
        return parsed
    except:
        return simple_local_theory_analyzer(question, student_answer)

def get_ai_feedback_code(question: dict, code: str, result_value: Any, expected: Any, is_correct: bool, stats: dict, model) -> Dict:
    if not model:
        score = 1.0 if is_correct else 0.3
        return {
            "is_correct": is_correct,
            "score": score,
            "feedback": "Correct!" if is_correct else "Incorrect",
            "code_quality": "N/A",
            "strengths": ["Executed"],
            "improvements": ["Review logic"],
            "points_earned": int(score * question.get("points", 0))
        }
    prompt = f"""Analyze code solution.

Question: {question.get('prompt')}
Code: {code}
Expected: {expected}
Got: {result_value}
Correct: {is_correct}

JSON only:
{{
    "is_correct": true/false,
    "score": 0.0-1.0,
    "feedback": "explanation",
    "code_quality": "excellent/good/fair/poor",
    "strengths": ["point1"],
    "improvements": ["point1"]
}}"""
    try:
        response = model.generate_content(prompt)
        result = parse_json_from_text(response.text)
        result["points_earned"] = int(result["score"] * question["points"])
        return result
    except:
        score = 1.0 if is_correct else 0.3
        return {"is_correct": is_correct, "score": score, "feedback": "AI error", "code_quality": "unknown", "strengths": ["Executed"], "improvements": ["Review"], "points_earned": int(score * question.get("points", 0))}

def generate_final_report(all_answers: List[Dict], model) -> Dict:
    if not model:
        return {
            "overall_feedback": "Practice completed!",
            "strengths": ["Completed all questions"],
            "weaknesses": ["AI unavailable"],
            "recommendations": ["Keep practicing"],
            "learning_path": [],
            "closing_message": "Keep learning and growing!"
        }
    summary = [{"question": a["title"], "correct": a.get("is_correct", False)} for a in all_answers]
    prompt = f"""Create performance report.

Summary: {json.dumps(summary)}

JSON only:
{{
    "overall_feedback": "2-3 sentences",
    "strengths": ["point1", "point2"],
    "weaknesses": ["point1"],
    "recommendations": ["rec1", "rec2"],
    "learning_path": [{{"topic": "name", "priority": "high/medium/low", "resources": "suggestion"}}],
    "closing_message": "motivational message"
}}"""
    try:
        response = model.generate_content(prompt)
        return parse_json_from_text(response.text)
    except:
        return {"overall_feedback": "Great effort!", "strengths": ["Persistence"], "weaknesses": ["Review"], "recommendations": ["Practice more"], "learning_path": [], "closing_message": "Keep pushing forward!"}

def safe_execute_code(user_code: str, dataframe: pd.DataFrame) -> Tuple[bool, Any, str, dict]:
    allowed_globals = {
        "__builtins__": {"abs": abs, "min": min, "max": max, "round": round, "len": len, "range": range, "sum": sum, "sorted": sorted, "list": list, "dict": dict, "set": set, "int": int, "float": float},
        "pd": pd, "np": np,
    }
    local_vars = {"df": dataframe.copy()}
    stats = {"lines": len(user_code.split('\n')), "chars": len(user_code), "execution_time": 0}
    try:
        start_time = time.time()
        exec(user_code, allowed_globals, local_vars)
        stats["execution_time"] = time.time() - start_time
        if "result" not in local_vars:
            return False, None, "⚠️ Assign to `result`", stats
        return True, local_vars["result"], "", stats
    except Exception as e:
        stats["execution_time"] = time.time() - start_time
        return False, None, f"❌ Error: {str(e)}", stats

def validator_numeric_tol(student_value: Any, expected_value: Any, tol=1e-3) -> Tuple[bool, str]:
    try:
        s, e = float(student_value), float(expected_value)
        return (abs(s - e) <= tol, f"✅ Correct!" if abs(s - e) <= tol else f"❌ Expected: {e}, Got: {s}")
    except:
        return False, "❌ Cannot compare"

def validator_dict_compare(student_value: Any, expected_value: Any) -> Tuple[bool, str]:
    if not isinstance(student_value, dict):
        return False, f"❌ Expected dict"
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

# Sidebar
with st.sidebar:
    st.markdown("### 🎓 DataMentor AI")
    st.markdown("---")
    if ai_model:
        st.success("🤖 AI Mentor Active")
    else:
        st.warning("⚠️ AI Mentor Inactive")
    st.markdown("---")
    if st.button("🌓 Toggle Theme"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()
    if st.session_state.started and not st.session_state.completed:
        progress = len(st.session_state.user_answers) / len(QUESTIONS)
        st.progress(progress)
        st.write(f"**{len(st.session_state.user_answers)}/{len(QUESTIONS)}** completed")

# === ADVANCED FRONT PAGE UI ===
if not st.session_state.started:
    components.html("""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@400;500;600;700;800&display=swap');
    
    * { box-sizing: border-box; margin: 0; padding: 0; }
    
    body {
        font-family: 'Inter', -apple-system, sans-serif;
        background: linear-gradient(135deg, #0a0e27 0%, #1a1d3e 25%, #2d1b4e 50%, #1e0836 75%, #0f0520 100%);
        overflow-x: hidden;
        padding: 20px;
    }
    
    @keyframes gradientShift {
        0%, 100% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
    }
    
    .hero-wrapper {
        background: linear-gradient(270deg, #1e1b4b, #312e81, #4c1d95, #581c87);
        background-size: 800% 800%;
        animation: gradientShift 15s ease infinite;
        min-height: 100vh;
        position: relative;
        overflow: hidden;
        padding: 40px 20px;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-20px) rotate(180deg); }
    }
    
    .particle {
        position: absolute;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 50%;
        animation: float 6s ease-in-out infinite;
    }
    
    .hero-card {
        background: linear-gradient(145deg, rgba(255,255,255,0.12), rgba(255,255,255,0.05));
        backdrop-filter: blur(40px);
        border: 1px solid rgba(255, 255, 255, 0.18);
        border-radius: 32px;
        padding: 60px 40px;
        max-width: 1400px;
        margin: 0 auto;
        box-shadow: 
            0 8px 32px rgba(0,0,0,0.37),
            inset 0 1px 0 rgba(255,255,255,0.3),
            0 50px 100px -20px rgba(139, 92, 246, 0.3);
        transform: perspective(1000px) rotateX(2deg);
        transition: all 0.6s cubic-bezier(0.23, 1, 0.32, 1);
    }
    
    .hero-card:hover {
        transform: perspective(1000px) rotateX(0deg) translateY(-8px);
        box-shadow: 
            0 12px 48px rgba(0,0,0,0.5),
            inset 0 1px 0 rgba(255,255,255,0.4),
            0 60px 120px -20px rgba(139, 92, 246, 0.4);
    }
    
    .hero-title {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 5.5rem;
        font-weight: 900;
        line-height: 1.1;
        background: linear-gradient(135deg, #ffffff 0%, #f0f0ff 30%, #e0e0ff 60%, #d0d0ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        text-align: center;
        margin-bottom: 24px;
        letter-spacing: -4px;
        animation: titleGlow 3s ease-in-out infinite;
    }
    
    @keyframes titleGlow {
        0%, 100% { filter: brightness(1) drop-shadow(0 0 20px rgba(168, 85, 247, 0.4)); }
        50% { filter: brightness(1.1) drop-shadow(0 0 30px rgba(168, 85, 247, 0.6)); }
    }
    
    .hero-subtitle {
        font-size: 1.5rem;
        color: rgba(255, 255, 255, 0.85);
        text-align: center;
        max-width: 850px;
        margin: 0 auto 48px;
        line-height: 1.7;
        font-weight: 400;
    }
    
    .stats-row {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 24px;
        margin: 48px 0;
    }
    
    .stat-box {
        background: linear-gradient(145deg, rgba(168, 85, 247, 0.2), rgba(139, 92, 246, 0.1));
        backdrop-filter: blur(20px);
        border: 1px solid rgba(168, 85, 247, 0.3);
        border-radius: 20px;
        padding: 32px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .stat-box:hover {
        transform: scale(1.05);
        border-color: rgba(168, 85, 247, 0.5);
    }
    
    .stat-number {
        font-size: 3rem;
        font-weight: 900;
        color: #fbbf24;
        margin-bottom: 8px;
    }
    
    .stat-label {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 32px;
        margin: 64px 0;
    }
    
    .feature-card {
        background: linear-gradient(145deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05));
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 24px;
        padding: 40px;
        text-align: center;
        transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
        cursor: pointer;
    }
    
    .feature-card:hover {
        transform: translateY(-8px) scale(1.02);
        background: linear-gradient(145deg, rgba(255,255,255,0.15), rgba(255,255,255,0.08));
        box-shadow: 0 20px 40px rgba(168, 85, 247, 0.3);
        border-color: rgba(168, 85, 247, 0.4);
    }
    
    .feature-icon {
        font-size: 4rem;
        margin-bottom: 24px;
        display: inline-block;
        animation: bounce 2s ease-in-out infinite;
    }
    
    @keyframes bounce {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    .feature-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 12px;
    }
    
    .feature-desc {
        color: rgba(255, 255, 255, 0.8);
        font-size: 1.05rem;
        line-height: 1.6;
    }
    
    .topics-section {
        background: linear-gradient(145deg, rgba(30, 27, 75, 0.6), rgba(49, 46, 129, 0.4));
        backdrop-filter: blur(30px);
        border: 1px solid rgba(168, 85, 247, 0.2);
        border-radius: 28px;
        padding: 48px;
        margin: 64px 0;
    }
    
    .topics-title {
        font-size: 2.5rem;
        font-weight: 800;
        color: #ffffff;
        text-align: center;
        margin-bottom: 32px;
    }
    
    .topics-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 24px;
    }
    
    .topic-item {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 16px;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        transition: all 0.3s ease;
    }
    
    .topic-item:hover {
        background: rgba(168, 85, 247, 0.15);
        transform: translateX(8px);
    }
    
    .topic-emoji {
        font-size: 2rem;
    }
    
    .topic-text {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.15rem;
        font-weight: 500;
    }
    
    @media (max-width: 768px) {
        .hero-title { font-size: 3rem; letter-spacing: -2px; }
        .hero-subtitle { font-size: 1.1rem; }
        .hero-card { padding: 32px 24px; }
        .stats-row, .features-grid, .topics-grid { grid-template-columns: 1fr; }
    }
    </style>
    </head>
    <body>
    <div class="hero-wrapper">
        <div class="particle" style="top: 10%; left: 10%; width: 80px; height: 80px; animation-delay: 0s;"></div>
        <div class="particle" style="top: 70%; left: 80%; width: 60px; height: 60px; animation-delay: 2s;"></div>
        <div class="particle" style="top: 30%; right: 15%; width: 100px; height: 100px; animation-delay: 1s;"></div>
        <div class="particle" style="bottom: 20%; left: 70%; width: 70px; height: 70px; animation-delay: 3s;"></div>
        
        <div class="hero-card">
            <h1 class="hero-title">DataMentor AI</h1>
            <p class="hero-subtitle">
                Master Data Science with AI-powered practice, real-time feedback, and personalized learning paths. 
                Join thousands of learners advancing their careers one challenge at a time.
            </p>
            
            <div class="stats-row">
                <div class="stat-box">
                    <div class="stat-number">8</div>
                    <div class="stat-label">Challenges</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">30</div>
                    <div class="stat-label">Minutes</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">115</div>
                    <div class="stat-label">Total Points</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number">AI</div>
                    <div class="stat-label">Powered</div>
                </div>
            </div>
            
            <div class="features-grid">
                <div class="feature-card">
                    <div class="feature-icon">🧠</div>
                    <div class="feature-title">Theory Mastery</div>
                    <div class="feature-desc">Deep dive into ML concepts with expert explanations</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">💻</div>
                    <div class="feature-title">Code Practice</div>
                    <div class="feature-desc">Real-world coding challenges with instant validation</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">🤖</div>
                    <div class="feature-title">AI Mentor</div>
                    <div class="feature-desc">Personalized feedback on every answer you submit</div>
                </div>
                <div class="feature-card">
                    <div class="feature-icon">📊</div>
                    <div class="feature-title">Progress Tracking</div>
                    <div class="feature-desc">Detailed analytics and performance insights</div>
                </div>
            </div>
            
            <div class="topics-section">
                <h2 class="topics-title">🚀 What You'll Master</h2>
                <div class="topics-grid">
                    <div class="topic-item">
                        <div class="topic-emoji">🧠</div>
                        <div class="topic-text">Bias-Variance & Overfitting</div>
                    </div>
                    <div class="topic-item">
                        <div class="topic-emoji">🔄</div>
                        <div class="topic-text">Cross-Validation Techniques</div>
                    </div>
                    <div class="topic-item">
                        <div class="topic-emoji">📏</div>
                        <div class="topic-text">Feature Scaling & Preprocessing</div>
                    </div>
                    <div class="topic-item">
                        <div class="topic-emoji">⚖️</div>
                        <div class="topic-text">Precision, Recall & F1 Score</div>
                    </div>
                    <div class="topic-item">
                        <div class="topic-emoji">📊</div>
                        <div class="topic-text">Correlation & Data Analysis</div>
                    </div>
                    <div class="topic-item">
                        <div class="topic-emoji">✂️</div>
                        <div class="topic-text">Train-Test Splitting</div>
                    </div>
                    <div class="topic-item">
                        <div class="topic-emoji">🗃️</div>
                        <div class="topic-text">GroupBy & Aggregation</div>
                    </div>
                    <div class="topic-item">
                        <div class="topic-emoji">🔧</div>
                        <div class="topic-text">Feature Engineering</div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    </body>
    </html>
    """, height=1400)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Practice Session", use_container_width=True, type="primary", key="start_btn"):
            st.session_state.started = True
            st.session_state.start_time = datetime.now()
            st.rerun()

elif st.session_state.completed:
    # Calculate stats
    total_points = sum(a.get("points_earned", 0) for a in st.session_state.user_answers)
    max_points = sum(q["points"] for q in QUESTIONS)
    correct = sum(1 for a in st.session_state.user_answers if a.get("is_correct"))
    wrong = len(st.session_state.user_answers) - correct
    percentage = (total_points / max_points) * 100
    
    st.markdown(f"""
    <div style="text-align: center; padding: 60px 20px; background: linear-gradient(145deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05)); border-radius: 32px; backdrop-filter: blur(30px);">
        <div style="font-size: 64px; margin-bottom: 24px;">🎉</div>
        <h1 style="font-size: 3rem; color: white; margin-bottom: 16px;">Practice Complete!</h1>
        <div style="font-size: 5rem; font-weight: 900; color: #fbbf24; margin: 24px 0;">{percentage:.0f}%</div>
        <p style="font-size: 1.3rem; color: rgba(255,255,255,0.8);">Score: {total_points}/{max_points} points</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Points", f"{total_points}/{max_points}")
    with col2:
        st.metric("✅ Correct", f"{correct}")
    with col3:
        st.metric("❌ Wrong", f"{wrong}")
    with col4:
        duration = (datetime.now() - st.session_state.start_time).seconds // 60
        st.metric("⏱️ Time", f"{duration} min")
    
    if not st.session_state.final_report:
        with st.spinner("🤖 Generating your personalized report..."):
            st.session_state.final_report = generate_final_report(st.session_state.user_answers, ai_model)
    
    report = st.session_state.final_report
    
    st.markdown("---")
    st.markdown("### 🤖 AI Mentor's Overall Assessment")
    st.info(report.get('overall_feedback', 'Great work!'))
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### 💪 Strengths")
        for strength in report.get('strengths', [])[:3]:
            st.success(f"✅ {strength}")
    with col2:
        st.markdown("#### 📈 Areas to Improve")
        for weakness in report.get('weaknesses', [])[:3]:
            st.warning(f"📚 {weakness}")
    
    st.markdown("#### 🎯 Recommendations")
    for rec in report.get('recommendations', [])[:3]:
        st.info(f"💡 {rec}")
    
    if report.get('learning_path'):
        st.markdown("#### 🗺️ Your Learning Path")
        for item in report['learning_path'][:3]:
            priority = item.get('priority', 'medium')
            color = "🔴" if priority == "high" else "🟡" if priority == "medium" else "🟢"
            st.markdown(f"{color} **{item.get('topic', 'Topic')}** ({priority} priority): {item.get('resources', 'Practice')}")
    
    # DETAILED QUESTION-BY-QUESTION REPORT
    st.markdown("---")
    st.markdown("## 📋 Detailed Question Report")
    
    for idx, answer_data in enumerate(st.session_state.user_answers, 1):
        q_status = "✅ Correct" if answer_data.get("is_correct") else "❌ Wrong"
        status_color = "#22c55e" if answer_data.get("is_correct") else "#ef4444"
        
        with st.expander(f"**Question {idx}: {answer_data['title']}** - {q_status}", expanded=False):
            st.markdown(f"""
            <div style="background: linear-gradient(145deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03)); 
                        border-left: 4px solid {status_color}; padding: 20px; border-radius: 12px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 16px;">
                    <span style="color: white; font-weight: 600;">Type: {answer_data['type'].title()}</span>
                    <span style="color: white; font-weight: 600;">Difficulty: {answer_data['difficulty'].title()}</span>
                    <span style="color: {status_color}; font-weight: 700;">
                        {answer_data.get('points_earned', 0)}/{answer_data.get('max_points', 0)} points
                    </span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if answer_data['type'] == 'theory':
                st.markdown("**📝 Your Answer:**")
                st.text_area("", value=answer_data.get('answer', ''), height=150, disabled=True, key=f"review_answer_{idx}")
            else:
                st.markdown("**💻 Your Code:**")
                st.code(answer_data.get('code', ''), language="python")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Your Result:**")
                    st.code(str(answer_data.get('result', '')), language="python")
                with col2:
                    st.markdown("**Expected Result:**")
                    st.code(str(answer_data.get('expected', '')), language="python")
            
            ai_feedback = answer_data.get('ai_analysis', {})
            
            st.markdown("**🤖 AI Feedback:**")
            st.info(ai_feedback.get('feedback', 'No feedback available'))
            
            if ai_feedback.get('strengths'):
                st.markdown("**💪 Strengths:**")
                for s in ai_feedback.get('strengths', []):
                    st.success(f"• {s}")
            
            if ai_feedback.get('improvements'):
                st.markdown("**📈 Improvements:**")
                for i in ai_feedback.get('improvements', []):
                    st.warning(f"• {i}")
            
            if answer_data['type'] == 'code' and ai_feedback.get('code_quality'):
                quality = ai_feedback.get('code_quality', 'N/A')
                quality_color = {"excellent": "#22c55e", "good": "#3b82f6", "fair": "#f59e0b", "poor": "#ef4444"}.get(quality.lower(), "#64748b")
                st.markdown(f"**Code Quality:** <span style='color: {quality_color}; font-weight: 700;'>{quality.upper()}</span>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Start New Session", use_container_width=True, type="primary"):
            for key in list(st.session_state.keys()):
                if key.startswith(('answer_', 'code_', 'user_answers', 'current_q', 'started', 'completed', 'final_report')):
                    del st.session_state[key]
            st.rerun()
    with col2:
        # Download report as JSON
        report_data = {
            "summary": {
                "total_points": total_points,
                "max_points": max_points,
                "percentage": percentage,
                "correct": correct,
                "wrong": wrong
            },
            "questions": st.session_state.user_answers,
            "ai_report": report
        }
        st.download_button(
            label="📥 Download Full Report",
            data=json.dumps(report_data, indent=2),
            file_name=f"datamentor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

else:
    # Active Question
    if st.session_state.current_q < len(QUESTIONS):
        q = QUESTIONS[st.session_state.current_q]
        
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05)); 
                    backdrop-filter: blur(30px); border-radius: 24px; padding: 40px; border: 1px solid rgba(255,255,255,0.2);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
                <h2 style="color: white; font-size: 2rem;">Question {q['id']}</h2>
                <div>
                    <span style="background: {'#ef4444' if q['difficulty']=='hard' else '#f59e0b' if q['difficulty']=='medium' else '#22c55e'}; 
                                 color: white; padding: 8px 16px; border-radius: 20px; font-weight: 600; margin-right: 8px;">
                        {q['difficulty'].upper()}
                    </span>
                    <span style="background: #8b5cf6; color: white; padding: 8px 16px; border-radius: 20px; font-weight: 600;">
                        {q['points']} pts
                    </span>
                </div>
            </div>
            <h3 style="color: white; font-size: 1.5rem; margin-bottom: 16px;">{q['title']}</h3>
            <p style="color: rgba(255,255,255,0.8); font-size: 1.1rem; line-height: 1.6;">{q['prompt']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if q['type'] == 'theory':
            # Use session state key to track current answer
            answer_key = f"answer_{q['id']}"
            if answer_key not in st.session_state:
                st.session_state[answer_key] = ""
            
            answer = st.text_area("Your Answer:", value=st.session_state[answer_key], height=200, placeholder="Write your detailed answer here...", key=f"textarea_{q['id']}")
            st.session_state[answer_key] = answer
            
            if st.button("Submit Answer", type="primary", key=f"submit_{q['id']}"):
                if answer.strip():
                    with st.spinner("🤖 AI analyzing your answer..."):
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
                        
                        score = ai_analysis.get("score", 0)
                        st.success(f"✅ Score: {ai_analysis.get('points_earned', 0)}/{q['points']} points ({score*100:.0f}%)")
                        st.info(ai_analysis.get('feedback', ''))
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**💪 Strengths:**")
                            for s in ai_analysis.get('strengths', []):
                                st.write(f"• {s}")
                        with col2:
                            st.markdown("**📈 Improvements:**")
                            for i in ai_analysis.get('improvements', []):
                                st.write(f"• {i}")
                        
                        st.session_state.current_q += 1
                        # Clear the answer for next question
                        st.session_state[answer_key] = ""
                        
                        if st.session_state.current_q >= len(QUESTIONS):
                            st.session_state.completed = True
                        
                        time.sleep(0.5)  # Brief pause to show feedback
                        st.rerun()
                else:
                    st.warning("Please provide an answer before submitting.")
        
        else:  # Code question
            if 'dataset' in q:
                with st.expander("📊 View Dataset"):
                    st.dataframe(DATASETS[q['dataset']], use_container_width=True)
            
            # Use session state for code editor
            code_key = f"code_{q['id']}"
            if code_key not in st.session_state:
                st.session_state[code_key] = q.get('starter_code', '')
            
            code = st.text_area("Your Code:", value=st.session_state[code_key], height=200, key=f"code_editor_{q['id']}")
            st.session_state[code_key] = code
            
            if st.button("▶️ Run Code", type="primary", key=f"run_{q['id']}"):
                if code.strip():
                    success, result, error, stats = safe_execute_code(code, DATASETS.get(q['dataset'], pd.DataFrame()))
                    
                    if success and result is not None:
                        expected = REFERENCE_RESULTS.get(q['id'])
                        validator = globals()[f"validator_{q['validator']}"]
                        is_correct, msg = validator(result, expected)
                        
                        # Show output immediately
                        st.markdown("### 📤 Output")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Your Result:**")
                            st.code(str(result), language="python")
                        with col2:
                            st.markdown("**Expected:**")
                            st.code(str(expected), language="python")
                        
                        st.markdown(f"**Execution Time:** {stats.get('execution_time', 0):.4f}s")
                        
                        with st.spinner("🤖 AI analyzing your code..."):
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
                            
                            if is_correct:
                                st.success(f"✅ Correct! {ai_analysis.get('points_earned', 0)}/{q['points']} points")
                            else:
                                st.error(f"❌ Incorrect. {ai_analysis.get('points_earned', 0)}/{q['points']} points")
                            
                            st.info(ai_analysis.get('feedback', ''))
                            
                            col1, col2 = st.columns(2)
                            with col1:
                                st.markdown("**💪 Code Strengths:**")
                                for s in ai_analysis.get('strengths', []):
                                    st.write(f"• {s}")
                            with col2:
                                st.markdown("**📈 Improvements:**")
                                for i in ai_analysis.get('improvements', []):
                                    st.write(f"• {i}")
                            
                            st.session_state.current_q += 1
                            # Clear code for next question
                            st.session_state[code_key] = ""
                            
                            if st.session_state.current_q >= len(QUESTIONS):
                                st.session_state.completed = True
                            
                            time.sleep(0.5)
                            st.rerun()
                    else:
                        st.error(error)
                else:
                    st.warning("Please write code before running.")

st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 40px 20px; color: rgba(255,255,255,0.7);">
    <h3 style="color: white; margin-bottom: 16px;">🎓 Corporate Bhaiya Learning Platform</h3>
    <p style="font-size: 1.1rem; margin-bottom: 8px;">Empowering careers through expert mentorship</p>
    <p style="opacity: 0.8;">© 2025 All rights reserved</p>
</div>
""", unsafe_allow_html=True)
