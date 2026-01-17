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

# Datasets & Questions (unchanged)
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

# === NEW: STUNNING FRONT PAGE UI (Replaces old hero) ===
if not st.session_state.started:

    # Ultra-modern 3D Glassmorphic CSS
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    * { box-sizing: border-box; }

    html, body, [class*="css"] {
        font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #533483 100%);
        background-attachment: fixed;
        min-height: 100vh;
        overflow-x: hidden;
    }

    /* 3D Rotating Cube */
    .cube-container {
        position: fixed;
        top: 50%; right: 10%;
        width: 80px; height: 80px;
        perspective: 1000px;
        pointer-events: none;
        z-index: 1;
    }

    .cube {
        width: 100%; height: 100%;
        position: relative;
        transform-style: preserve-3d;
        animation: rotateCube 15s linear infinite;
    }

    .cube-face {
        position: absolute;
        width: 80px; height: 80px;
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1), rgba(255, 255, 255, 0.05));
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(10px);
    }

    .cube-face.front { transform: rotateY(0deg) translateZ(40px); }
    .cube-face.back { transform: rotateY(180deg) translateZ(40px); }
    .cube-face.right { transform: rotateY(90deg) translateZ(40px); }
    .cube-face.left { transform: rotateY(-90deg) translateZ(40px); }
    .cube-face.top { transform: rotateX(90deg) translateZ(40px); }
    .cube-face.bottom { transform: rotateX(-90deg) translateZ(40px); }

    @keyframes rotateCube {
        0% { transform: rotateX(0deg) rotateY(0deg); }
        100% { transform: rotateX(360deg) rotateY(360deg); }
    }

    /* Hero Container */
    .hero-container {
        background: linear-gradient(135deg,
            rgba(255, 255, 255, 0.15) 0%,
            rgba(255, 255, 255, 0.1) 50%,
            rgba(255, 255, 255, 0.05) 100%);
        backdrop-filter: blur(30px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 1rem 2rem;
        border-radius: 40px;
        margin: -7rem auto 0.5rem auto;
        max-width: 1100px;
        box-shadow: 0 40px 100px rgba(0, 0, 0, 0.3),
                    0 20px 50px rgba(120, 119, 198, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.3);
        position: relative;
        overflow: hidden;
        z-index: 10;
        transform: perspective(1000px) rotateX(5deg);
        transition: transform 0.3s ease;
    }

    .hero-container:hover {
        transform: perspective(1000px) rotateX(0deg) translateY(-10px);
    }

    .hero-title {
        font-size: 4.5rem;
        font-weight: 800;
        margin-bottom: 1.5rem;
        background: linear-gradient(135deg, #ffffff 0%, #e2e8f0 50%, #cbd5e1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.1;
        letter-spacing: -3px;
        text-shadow: 0 10px 30px rgba(255, 255, 255, 0.3);
    }

    .hero-subtitle {
        font-size: 1.4rem;
        color: rgba(255, 255, 255, 0.8);
        margin-bottom: 3rem;
        font-weight: 400;
        max-width: 700px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.6;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
    }

    /* CTA Button - Yellow Gradient */
    .stButton > button {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%) !important;
        color: #000000 !important;
        border-radius: 60px !important;
        border: none !important;
        padding: 2rem 5rem !important;
        font-weight: 700 !important;
        font-size: 1.8rem !important;
        box-shadow: 0 15px 35px rgba(255, 215, 0, 0.4) !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }

    .stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 20px 45px rgba(255, 215, 0, 0.5) !important;
        background: linear-gradient(135deg, #FFE44D 0%, #FFB347 100%) !important;
    }

    /* Stats Cards */
    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 2rem;
        margin: 3rem 0 2rem 0;
    }

    .stat-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0.1));
        border-radius: 25px;
        padding: 2rem;
        text-align: center;
        height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(20px);
    }

    .stat-icon { font-size: 3.5rem; margin-bottom: 1rem; }
    .stat-number { font-size: 1.5rem; font-weight: 800; color: #ffffff; margin-bottom: 0.5rem; }
    .stat-label { color: rgba(255, 255, 255, 0.8); font-weight: 600; font-size: 1.1rem; text-transform: uppercase; }

    /* Learning Path & Features */
    .learning-path, .features-grid, .testimonial {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.15), rgba(255, 255, 255, 0.05));
        padding: 3rem;
        border-radius: 30px;
        margin: 4rem 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
        backdrop-filter: blur(25px);
    }

    @media (max-width: 768px) {
        .hero-title { font-size: 2.8rem; }
        .hero-container { margin: -9rem auto -1rem auto; padding: 1rem; }
        .cube-container { display: none; }
    }

    /* New: ensure hero HTML injected via components.html appears white */
    .hero-section,
    .hero-section .hero-content,
    .hero-section .hero-title,
    .hero-section .hero-subtitle,
    .hero-section .feature-grid,
    .hero-section .feature-item,
    .hero-section .feature-title,
    .hero-section .feature-desc,
    .hero-section .feature-icon {
        color: #ffffff !important;
    }

    .hero-section .hero-subtitle,
    .hero-section .feature-desc {
        color: rgba(255,255,255,0.95) !important;
    }

    .hero-section .hero-title {
        font-weight: 800;
        font-size: 2.8rem;
        color: #ffffff !important;
    }

    .hero-section .feature-grid {
        display: flex;
        justify-content: center;
        gap: 1.25rem;
        margin-top: 1.25rem;
        flex-wrap: wrap;
    }

    .hero-section .feature-item {
        background: transparent;
        padding: 0.6rem 1rem;
        border-radius: 10px;
        text-align: center;
    }

    .hero-section .feature-icon {
        font-size: 2.2rem;
        margin-bottom: 0.4rem;
    }

    </style>
    """, unsafe_allow_html=True)

    # Animated Cube
    st.markdown("""
    <div class="cube-container">
        <div class="cube">
            <div class="cube-face front"></div>
            <div class="cube-face back"></div>
            <div class="cube-face right"></div>
            <div class="cube-face left"></div>
            <div class="cube-face top"></div>
            <div class="cube-face bottom"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Hero Section
    st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title" style="text-align: center;">DataMentor AI</h1>
        <p class="hero-subtitle" style="text-align: center;">
            Master Data Science with AI-powered practice, real-time feedback, and personalized learning paths.<br>
            Join <strong>thousands of learners</strong> advancing their careers one challenge at a time.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Centered Start Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Practice Session", key="start_session", use_container_width=True):
            st.session_state.started = True
            st.session_state.start_time = datetime.now()
            st.rerun()

    # Topics Covered
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1f2937 60%, #374151 100%);
                border-radius: 14px; padding: 2rem; margin: 3rem 0; box-shadow: 0 6px 32px rgba(0,0,0,0.12);">
      <h2 style="color: #60a5fa; text-align: center;">🚀 What You'll Master</h2>
      <ul style="color: #f3f4f6; font-size: 1.2rem; columns: 2; padding-left: 2rem;">
        <li>🧠 Bias-Variance & Overfitting</li>
        <li>🔄 Cross-Validation Techniques</li>
        <li>📏 Feature Scaling & Preprocessing</li>
        <li>⚖️ Precision, Recall & F1 Score</li>
        <li>📊 Correlation & Data Analysis</li>
        <li>✂️ Train-Test Splitting</li>
        <li>🗃️ GroupBy & Aggregation</li>
        <li>🔧 Feature Engineering</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)

    # Stats
    st.markdown("""
    <div class="stats-container">
        <div class="stat-card">
            <div class="stat-icon">🎯</div>
            <span class="stat-number">8</span>
            <div class="stat-label">Challenges</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">⏱️</div>
            <span class="stat-number">20-40</span>
            <div class="stat-label">Minutes</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">🏆</div>
            <span class="stat-number">70+</span>
            <div class="stat-label">Points Possible</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">🤖</div>
            <span class="stat-number">AI</span>
            <div class="stat-label">Mentor Feedback</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Learning Journey
    st.markdown("""
    <div class="learning-path">
        <h3 style="text-align: center; color: white;">🎯 Your Learning Journey</h3>
        <div style="display: flex; justify-content: space-around; flex-wrap: wrap; gap: 2rem; margin-top: 2rem;">
            <div style="text-align:center; color:white;"><div style="font-size:3rem;">1</div><div>Assessment</div></div>
            <div style="text-align:center; color:white;"><div style="font-size:3rem;">2</div><div>AI Feedback</div></div>
            <div style="text-align:center; color:white;"><div style="font-size:3rem;">3</div><div>Deep Practice</div></div>
            <div style="text-align:center; color:white;"><div style="font-size:3rem;">4</div><div>Mastery</div></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Features
    st.markdown("""
    <div class="features-grid">
        <div style="padding:2rem; text-align:center;">
            <div style="font-size:3rem; margin-bottom:1rem;">🤖</div>
            <h3 style="color:white;">Personalized AI Mentor</h3>
            <p style="color:rgba(255,255,255,0.8);">Instant, detailed feedback on every answer</p>
        </div>
        <div style="padding:2rem; text-align:center;">
            <div style="font-size:3rem; margin-bottom:1rem;">📊</div>
            <h3 style="color:white;">Real Datasets</h3>
            <p style="color:rgba(255,255,255,0.8);">Practice with realistic data scenarios</p>
        </div>
        <div style="padding:2rem; text-align:center;">
            <div style="font-size:3rem; margin-bottom:1rem;">🔄</div>
            <h3 style="color:white;">Adaptive Challenges</h3>
            <p style="color:rgba(255,255,255,0.8);">Mixed theory and coding for complete mastery</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Testimonials
    st.markdown("""
    <div class="testimonial">
        <p style="font-size:1.3rem; font-style:italic; color:rgba(255,255,255,0.9);">
            "This platform helped me finally understand bias-variance and cross-validation. The AI feedback is incredibly insightful!"
        </p>
        <p style="color:white; font-weight:700;">— Adarsh, Data Science Learner</p>
    </div>
    """, unsafe_allow_html=True)


# LLM Functions
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

# ---- Add / Replace these helper functions and AI handlers ----

import re
import ast
import html

def parse_json_from_text(text: str) -> dict:
    """
    Robustly try to extract the first JSON object from model text.
    - Handles triple-backtick blocks with ```json ... ```
    - If plain JSON-like object appears, tries to find balanced {...} substring.
    - Falls back to ast.literal_eval (sometimes models return Python dict-like)
    """
    if not text:
        raise ValueError("Empty text")

    # try fenced ```json blocks first
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.S)
    if m:
        candidate = m.group(1)
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # try fenced ``` blocks that might include JSON
    m = re.search(r"```(?:json|python)?\s*(\{.*?\})\s*```", text, flags=re.S)
    if m:
        candidate = m.group(1)
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # try to find the first balanced {...}
    start = text.find('{')
    if start != -1:
        # scan forward to find a balanced close
        depth = 0
        for i in range(start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    candidate = text[start:i+1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        # try ast.literal_eval (some LLMs output single quotes / Python dict style)
                        try:
                            return ast.literal_eval(candidate)
                        except Exception:
                            break
                    break

    # final fallback: try to parse the whole text as JSON or Python literal
    try:
        return json.loads(text)
    except Exception:
        try:
            return ast.literal_eval(text)
        except Exception as e:
            raise ValueError("Could not extract JSON from text") from e

def simple_local_theory_analyzer(question: dict, student_answer: str) -> dict:
    """
    Lightweight deterministic analyzer used when LLM unavailable or when parsing fails.
    - Uses keyword overlap and length heuristics to produce a score and short feedback.
    """
    text = (student_answer or "").lower()
    tokens = set(re.findall(r"\w+", text))
    # small keyword lists per question id (extendable)
    keywords_by_q = {
        1: {"bias", "variance", "overfitting", "underfitting", "regularization"},
        2: {"k-fold", "cross", "validation", "folds", "train", "test"},
        3: {"scaling", "standardization", "normalization", "z-score", "min-max"},
        4: {"precision", "recall", "f1", "false", "positive", "negative"},
    }
    kws = keywords_by_q.get(question.get("id"), set())
    hits = len([k for k in kws if k in text])
    # length score
    length_score = min(max(len(text.split()) / 60, 0.0), 1.0)
    kw_score = min(hits / max(len(kws), 1), 1.0)
    score = 0.6 * kw_score + 0.4 * length_score
    feedback = "Good attempt. "
    if score > 0.7:
        feedback += "You covered the main points."
    elif score > 0.4:
        feedback += "You mentioned some concepts but can expand with examples and definitions."
    else:
        feedback += "Your answer is too short or missing key terms; expand on definitions and provide examples."
    return {
        "is_correct": score > 0.6,
        "score": float(round(score, 3)),
        "feedback": feedback,
        "strengths": ["Attempted the question"] if score > 0 else [],
        "improvements": ["Expand answer, mention key concepts and examples"],
        "points_earned": int(round(score * question.get("points", 0)))
    }

# Replace get_ai_feedback_theory with robust parsing + fallback
def get_ai_feedback_theory(question: dict, student_answer: str, model) -> Dict:
    # if no model, use local analyzer
    if not model:
        return simple_local_theory_analyzer(question, student_answer)

    prompt = f"""You are an expert Data Science mentor. Analyze this student answer.

Question ({question['difficulty']}, {question['points']} points):
{question['prompt']}

Student Answer:
{student_answer}

Provide a JSON-only response (no extra commentary). Example:
{{
  "is_correct": true,
  "score": 0.0,
  "feedback": "2-3 sentences",
  "strengths": ["strength1"],
  "improvements": ["improvement1"]
}}
"""
    try:
        response = model.generate_content(prompt, generation_config=genai.types.GenerationConfig(temperature=0.7, max_output_tokens=800))
        raw_text = getattr(response, "text", str(response)).strip()
        # store raw for debugging (visible in session state)
        st.session_state["last_ai_raw_theory"] = raw_text
        parsed = parse_json_from_text(raw_text)
        # guard types & compute points
        parsed["score"] = float(parsed.get("score", 0.0))
        parsed["points_earned"] = int(parsed.get("points_earned", int(parsed["score"] * question["points"])) if parsed.get("points_earned") is not None else int(parsed["score"] * question["points"]))
        return parsed
    except Exception as e:
        # parsing/LLM error: fallback deterministic analyzer and record raw
        st.session_state["last_ai_error_theory"] = {"error": str(e), "raw": st.session_state.get("last_ai_raw_theory", "")}
        return simple_local_theory_analyzer(question, student_answer)

# Replace get_ai_feedback_code with robust parsing + fallback
def get_ai_feedback_code(question: dict, code: str, result_value: Any, expected: Any, is_correct: bool, stats: dict, model) -> Dict:
    stats = stats or {}
    if not model:
        score = 1.0 if is_correct else 0.3
        return {
            "is_correct": is_correct,
            "score": score,
            "feedback": "Correct!" if is_correct else "Incorrect",
            "code_quality": "N/A",
            "strengths": ["Executed"],
            "improvements": ["Review logic or edge-cases"],
            "points_earned": int(round(score * question.get("points", 0)))
        }

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
            return {"is_correct": is_correct, "score": score, "feedback": "AI error", "code_quality": "unknown", "strengths": ["Executed"], "improvements": ["Review"], "points_earned": int(round(score * question.get("points", 0)))}

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
        return {"overall_feedback": "Great effort!", "strengths": ["Persistence"], "weaknesses": ["Review"], "recommendations": ["Practice more"], "learning_path": [{"topic": "Review basics", "priority": "medium", "resources": "Practice problems"}]}

# Code Execution
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
#st.markdown(get_advanced_css(st.session_state.theme), unsafe_allow_html=True)

# Get AI Model
ai_model = get_gemini_model()

# Sidebar
# Sidebar
# Sidebar (keep your existing one)
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
    # Replace the previous components.html(...) hero section with this block:
    
    components.html("""
    <div class="hero-section-root">
      <style>
        /* Styles inside the component iframe — these affect only the hero HTML */
        :root {
          --hero-bg: transparent;
          --text-color: #ffffff;
          --muted: rgba(255,255,255,0.9);
          --feature-gap: 1.25rem;
        }
    
        body {
          margin: 0;
          padding: 0;
          font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
          background: var(--hero-bg);
          color: var(--text-color);
        }
    
        .hero-section {
          display: flex;
          align-items: center;
          justify-content: center;
          flex-direction: column;
          padding: 18px 24px;
          width: 100%;
          box-sizing: border-box;
        }
    
        .hero-content {
          max-width: 1100px;
          width: 100%;
          text-align: center;
          padding: 0 8px;
        }
    
        .hero-title {
          font-size: 2.6rem;
          line-height: 1.05;
          font-weight: 800;
          margin: 0 0 8px 0;
          color: var(--text-color) !important;
          text-shadow: 0 6px 18px rgba(0,0,0,0.5);
        }
    
        .hero-subtitle {
          font-size: 1.05rem;
          margin: 0 auto 18px auto;
          max-width: 820px;
          color: var(--muted) !important;
          line-height: 1.45;
        }
    
        .feature-grid {
          display: flex;
          justify-content: center;
          gap: var(--feature-gap);
          margin-top: 12px;
          flex-wrap: wrap;
        }
    
        .feature-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          min-width: 140px;
          padding: 10px 12px;
          color: var(--text-color) !important;
          background: transparent;
          border-radius: 10px;
        }
    
        .feature-icon {
          font-size: 1.9rem;
          margin-bottom: 6px;
        }
    
        .feature-title {
          font-weight: 700;
          font-size: 1rem;
          margin-bottom: 4px;
          color: var(--text-color) !important;
        }
    
        .feature-desc {
          color: var(--muted) !important;
          font-size: 0.95rem;
        }
    
        /* Responsive tweaks */
        @media (max-width: 640px) {
          .hero-title { font-size: 1.9rem; }
          .feature-item { min-width: 110px; padding: 8px; }
          .feature-grid { gap: 0.75rem; }
        }
      </style>
    
      <div class="hero-section" role="region" aria-label="Hero">
        <div class="hero-content">
          <div class="hero-title">Master Data Science</div>
          <div class="hero-subtitle">
            AI-powered practice platform with personalized feedback and adaptive learning
          </div>
    
          <div class="feature-grid" aria-hidden="false">
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
    </div>
    """, height=420)
    
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
                        
                        # Show feedback (sanitized)
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

                        feedback_text = html.escape(ai_analysis.get('feedback', ''))
                        strengths_html = ''.join([f'<div class="insight-box insight-strength">✅ {html.escape(s)}</div>' for s in ai_analysis.get('strengths', [])])
                        improvements_html = ''.join([f'<div class="insight-box insight-weakness">📚 {html.escape(i)}</div>' for i in ai_analysis.get('improvements', [])])
                        
                        html_content = f"""
                        <div class="ai-feedback-container fade-in">
                            <div class="feedback-content">
                                <div class="ai-badge">{emoji} AI MENTOR FEEDBACK</div>
                                <div style="font-size: 20px; font-weight: 700; color: {status_color}; margin-bottom: 16px;">
                                    Score: {ai_analysis.get('points_earned', 0)}/{q['points']} points ({score*100:.0f}%)
                                </div>
                                <div style="margin-bottom: 20px;">{feedback_text}</div>
                                
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 24px;">
                                    <div>
                                        <div class="insight-title">💪 Strengths</div>
                                        {strengths_html}
                                    </div>
                                    <div>
                                        <div class="insight-title">📈 Improvements</div>
                                        {improvements_html}
                                    </div>
                                </div>
                            </div>
                        </div>
                        """
                        # Use components.html to avoid accidental markdown code-block parsing
                        components.html(html_content, height=360, scrolling=True)
                        
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
                            
                            # Show feedback (sanitized)
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
                            
                            # Present result/expected without letting any backticks or raw HTML break the UI
                            result_display = html.escape(json.dumps(result, indent=2)) if not isinstance(result, str) else html.escape(result)
                            expected_display = html.escape(json.dumps(expected, indent=2)) if not isinstance(expected, str) else html.escape(expected)
                            feedback_text = html.escape(ai_analysis.get('feedback', ''))
                            strengths_html = ''.join([f'<div class="insight-box insight-strength">✅ {html.escape(s)}</div>' for s in ai_analysis.get('strengths', [])])
                            improvements_html = ''.join([f'<div class="insight-box insight-weakness">📚 {html.escape(i)}</div>' for i in ai_analysis.get('improvements', [])])
                            
                            html_content = f"""
                            <div class="ai-feedback-container fade-in">
                                <div class="feedback-content">
                                    <div class="ai-badge">{emoji} AI MENTOR FEEDBACK</div>
                                    <div style="font-size: 20px; font-weight: 700; color: {status_color}; margin-bottom: 16px;">
                                        Score: {ai_analysis.get('points_earned', 0)}/{q['points']} points ({score*100:.0f}%)
                                    </div>
                                    
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px;">
                                        <div>
                                            <div style="font-weight: 600; margin-bottom: 8px;">Your Result:</div>
                                            <pre style="background:#f6f8fa;padding:12px;border-radius:8px;white-space:pre-wrap;">{result_display}</pre>
                                        </div>
                                        <div>
                                            <div style="font-weight: 600; margin-bottom: 8px;">Expected:</div>
                                            <pre style="background:#f6f8fa;padding:12px;border-radius:8px;white-space:pre-wrap;">{expected_display}</pre>
                                        </div>
                                    </div>
                                    
                                    <div style="margin-bottom: 20px;">{feedback_text}</div>
                                    
                                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 24px;">
                                        <div>
                                            <div class="insight-title">💪 Code Strengths</div>
                                            {strengths_html}
                                        </div>
                                        <div>
                                            <div class="insight-title">📈 Improvements</div>
                                            {improvements_html}
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """
                            components.html(html_content, height=460, scrolling=True)
                            
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
# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; padding: 20px; color: #94a3b8; font-size: 14px;">
    <div>🎓 <strong>DataMentor AI</strong> - Master Data Science with AI Guidance</div>
    <div>Powered by Gemini AI | Built with Streamlit</div>
</div>
""", unsafe_allow_html=True)


