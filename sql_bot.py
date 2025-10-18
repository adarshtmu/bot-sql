"""
AI-Powered Data Science Practice Bot with LLM Mentor

Advanced Features:
- 8 questions: 4 theory + 4 coding with multiple difficulty levels
- LLM-powered mentor feedback for every answer (detailed, personalized)
- Comprehensive final report with strengths, weaknesses, and learning path
- Real-time AI analysis of code quality and theory understanding
- Beautiful modern UI with theme support
- Progress tracking and detailed analytics

NOTE: Requires Anthropic API key. Set via Streamlit secrets or environment variable.
"""

import streamlit as st
import pandas as pd
import numpy as np
import textwrap
import re
import time
from typing import Tuple, Any, Dict, List
from datetime import datetime
import json
import os

# For LLM integration
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    st.warning("⚠️ Install google-generativeai package for AI mentor: `pip install google-generativeai`")

st.set_page_config(page_title="AI DS Practice Bot", layout="wide", initial_sidebar_state="expanded")

# --------------------------
# LLM Configuration
# --------------------------
def get_gemini_model():
    """Get Gemini model - API key entered directly in app"""
    
    # Check if API key is already in session state
    if "gemini_api_key" in st.session_state and st.session_state.gemini_api_key:
        try:
            if GEMINI_AVAILABLE:
                genai.configure(api_key=st.session_state.gemini_api_key)
                return genai.GenerativeModel('gemini-2.0-flash')
        except Exception as e:
            st.error(f"Invalid API key: {str(e)}")
            return None
    
    return None

# --------------------------
# Enhanced CSS with animations
# --------------------------
def get_theme_css(theme="light"):
    if theme == "dark":
        return """
        <style>
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        .stApp {
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
            color: #e8eef2;
        }
        .card {
            background: rgba(30, 41, 59, 0.85);
            border: 1px solid rgba(148, 163, 184, 0.2);
            color: #e8eef2;
            animation: fadeIn 0.5s ease;
        }
        .hero-title { color: #60a5fa; }
        .ai-feedback {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.15));
            border: 2px solid rgba(59, 130, 246, 0.3);
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
            position: relative;
        }
        .ai-badge {
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 10px;
        }
        </style>
        """
    else:
        return """
        <style>
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.8; } }
        
        .stApp {
            background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #dbeafe 100%);
            color: #0f172a;
        }
        .card {
            background: rgba(255, 255, 255, 0.95);
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
            padding: 24px;
            margin-bottom: 20px;
            border: 1px solid rgba(148, 163, 184, 0.2);
            backdrop-filter: blur(10px);
            animation: fadeIn 0.5s ease;
        }
        .hero-title {
            font-size: 48px;
            font-weight: 800;
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }
        .hero-sub {
            color: #64748b;
            font-size: 18px;
            margin-bottom: 16px;
        }
        .metric-box {
            background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
            border-radius: 12px;
            padding: 16px;
            border: 2px solid #e2e8f0;
            text-align: center;
        }
        .metric-value {
            font-size: 32px;
            font-weight: 700;
            color: #3b82f6;
        }
        .metric-label {
            font-size: 14px;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .difficulty-badge {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .diff-easy { background: #dcfce7; color: #166534; }
        .diff-medium { background: #fef3c7; color: #92400e; }
        .diff-hard { background: #fee2e2; color: #991b1b; }
        .progress-bar {
            background: #e2e8f0;
            border-radius: 10px;
            height: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-bar-fill {
            height: 100%;
            background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%);
            transition: width 0.4s ease;
        }
        .ai-feedback {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.05), rgba(139, 92, 246, 0.05));
            border: 2px solid rgba(59, 130, 246, 0.2);
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
            position: relative;
        }
        .ai-badge {
            background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            color: white;
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            display: inline-block;
            margin-bottom: 10px;
        }
        .analyzing {
            animation: pulse 1.5s ease-in-out infinite;
        }
        .strength-box {
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05));
            border-left: 4px solid #22c55e;
            padding: 16px;
            border-radius: 8px;
            margin: 12px 0;
        }
        .weakness-box {
            background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.05));
            border-left: 4px solid #ef4444;
            padding: 16px;
            border-radius: 8px;
            margin: 12px 0;
        }
        .recommendation-box {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(59, 130, 246, 0.05));
            border-left: 4px solid #3b82f6;
            padding: 16px;
            border-radius: 8px;
            margin: 12px 0;
        }
        .stButton > button {
            background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
            color: white !important;
            font-weight: 600;
            padding: 12px 24px;
            border-radius: 10px;
            border: none;
            transition: transform 0.2s;
        }
        .stButton > button:hover {
            transform: translateY(-2px);
        }
        .report-section {
            background: white;
            border-radius: 12px;
            padding: 20px;
            margin: 16px 0;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        .score-ring {
            width: 150px;
            height: 150px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 36px;
            font-weight: 700;
            margin: 20px auto;
        }
        </style>
        """

# --------------------------
# Datasets
# --------------------------
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

# --------------------------
# Questions
# --------------------------
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

# --------------------------
# LLM-Powered Evaluation Functions
# --------------------------
def get_ai_feedback_theory(question: dict, student_answer: str, model) -> Dict:
    """Get detailed AI mentor feedback for theory answers"""
    if not model:
        return {
            "is_correct": len(student_answer.split()) >= 30,
            "score": 0.7,
            "feedback": "AI mentor unavailable. Basic check: answer length is adequate.",
            "strengths": ["Attempted the question"],
            "improvements": ["Add API key for detailed feedback"],
            "points_earned": int(question["points"] * 0.7)
        }
    
    prompt = f"""You are an expert Data Science mentor providing detailed, constructive feedback to a student.

Question ({question['difficulty']} difficulty, {question['points']} points):
{question['prompt']}

Student's Answer:
{student_answer}

Analyze this answer as a mentor and provide:
1. Overall assessment (correct/partially correct/incorrect)
2. Score from 0.0 to 1.0 (how well they answered)
3. Detailed feedback (2-3 sentences explaining what's good and what's missing)
4. 2-3 specific strengths (what they did well)
5. 2-3 specific areas for improvement (what to study more)
6. Whether the core concepts are understood

Respond in JSON format:
{{
    "is_correct": true/false,
    "score": 0.0-1.0,
    "feedback": "detailed feedback here",
    "strengths": ["strength1", "strength2"],
    "improvements": ["improvement1", "improvement2"],
    "core_concepts_understood": true/false
}}

Be encouraging but honest. Focus on learning, not just correctness."""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=1000,
            )
        )
        
        # Extract JSON from response
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        result["points_earned"] = int(result["score"] * question["points"])
        return result
    except Exception as e:
        return {
            "is_correct": False,
            "score": 0.5,
            "feedback": f"AI analysis error: {str(e)}. Please check your answer manually.",
            "strengths": ["Attempted the question"],
            "improvements": ["Review the topic"],
            "points_earned": int(question["points"] * 0.5)
        }

def get_ai_feedback_code(question: dict, student_code: str, result_value: Any, 
                         expected: Any, is_correct: bool, execution_stats: dict, model) -> Dict:
    """Get detailed AI mentor feedback for code answers"""
    if not model:
        return {
            "is_correct": is_correct,
            "score": 1.0 if is_correct else 0.3,
            "feedback": "Correct!" if is_correct else "Incorrect result.",
            "code_quality": "AI unavailable",
            "strengths": ["Code executed"],
            "improvements": ["Add API key for detailed feedback"],
            "points_earned": question["points"] if is_correct else int(question["points"] * 0.3)
        }
    
    prompt = f"""You are an expert Data Science coding mentor providing detailed code review.

Question ({question['difficulty']} difficulty, {question['points']} points):
{question['prompt']}

Student's Code:
```python
{student_code}
```

Expected Result: {expected}
Student's Result: {result_value}
Correctness: {"✓ Correct" if is_correct else "✗ Incorrect"}
Execution Time: {execution_stats.get('execution_time', 0):.4f}s

Analyze this code and provide:
1. Overall code quality assessment
2. Score from 0.0 to 1.0 (correctness + code quality)
3. Detailed feedback (explain approach, correctness, efficiency)
4. 2-3 code strengths (what they did well)
5. 2-3 areas for improvement (better approaches, optimization, style)
6. Any potential issues or edge cases they missed

Respond in JSON format:
{{
    "is_correct": true/false,
    "score": 0.0-1.0,
    "feedback": "detailed feedback",
    "code_quality": "excellent/good/fair/poor",
    "strengths": ["strength1", "strength2"],
    "improvements": ["improvement1", "improvement2"],
    "better_approach": "optional: suggest better method if applicable"
}}

Be specific and educational. Praise good practices, suggest improvements."""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=1200,
            )
        )
        
        # Extract JSON from response
        response_text = response.text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        result["points_earned"] = int(result["score"] * question["points"])
        return result
    except Exception as e:
        fallback_score = 1.0 if is_correct else 0.3
        return {
            "is_correct": is_correct,
            "score": fallback_score,
            "feedback": f"AI analysis error: {str(e)}",
            "code_quality": "unknown",
            "strengths": ["Code executed"],
            "improvements": ["Review approach"],
            "points_earned": int(question["points"] * fallback_score)
        }

def generate_final_report(all_answers: List[Dict], model) -> Dict:
    """Generate comprehensive final report with AI analysis"""
    if not model:
        return {
            "overall_feedback": "Complete! Add API key for detailed analysis.",
            "strengths": ["Completed all questions"],
            "weaknesses": ["AI analysis unavailable"],
            "recommendations": ["Set up Gemini API key"],
            "learning_path": []
        }
    
    # Prepare summary for AI
    summary = []
    for ans in all_answers:
        summary.append({
            "question": ans["title"],
            "type": ans["type"],
            "difficulty": ans["difficulty"],
            "correct": ans.get("is_correct", False),
            "score": ans.get("ai_analysis", {}).get("score", 0),
            "points": f"{ans.get('points_earned', 0)}/{ans.get('max_points', 10)}"
        })
    
    prompt = f"""You are a senior Data Science mentor writing a comprehensive performance report.

Student completed 8 questions (4 theory + 4 coding). Here's their performance:

{json.dumps(summary, indent=2)}

Create a detailed mentor report with:
1. Overall performance summary (2-3 sentences, be encouraging)
2. Top 3-4 strengths (specific skills they demonstrated well)
3. Top 3-4 weaknesses (areas needing improvement)
4. Detailed recommendations (3-4 specific actionable items)
5. Personalized learning path (3-4 topics to study next with resources)
6. Motivational closing message

Respond in JSON format:
{{
    "overall_feedback": "comprehensive summary",
    "strengths": ["strength1", "strength2", "strength3"],
    "weaknesses": ["weakness1", "weakness2", "weakness3"],
    "recommendations": ["rec1", "rec2", "rec3"],
    "learning_path": [
        {{"topic": "topic name", "priority": "high/medium/low", "resources": "suggested resources"}},
        ...
    ],
    "closing_message": "motivational message"
}}

Be specific, actionable, and encouraging. This is a learning experience."""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.8,
                max_output_tokens=2000,
            )
        )
        
        # Extract JSON from response
        response_text = response.text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        return json.loads(response_text)
    except Exception as e:
        return {
            "overall_feedback": "Good effort completing all questions!",
            "strengths": ["Persistence", "Attempted all questions"],
            "weaknesses": ["AI analysis unavailable"],
            "recommendations": ["Review incorrect answers", "Practice more"],
            "learning_path": [{"topic": "Review basics", "priority": "high", "resources": "Online courses"}],
            "closing_message": "Keep learning!"
        }

# --------------------------
# Code Execution
# --------------------------
def safe_execute_code(user_code: str, dataframe: pd.DataFrame, timeout: int = 5) -> Tuple[bool, Any, str, dict]:
    """Execute student code safely"""
    allowed_globals = {
        "__builtins__": {
            "abs": abs, "min": min, "max": max, "round": round, "len": len,
            "range": range, "sum": sum, "sorted": sorted, "list": list,
            "dict": dict, "set": set, "int": int, "float": float, "str": str
        },
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
        diff = abs(s - e)
        if diff <= tol:
            return True, f"✅ Correct! (Expected: {e}, Got: {s})"
        return False, f"❌ Expected: {e}, Got: {s}"
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

# Reference solutions
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

# --------------------------
# Session State
# --------------------------
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
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "final_report" not in st.session_state:
    st.session_state.final_report = None
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = ""
if "api_key_validated" not in st.session_state:
    st.session_state.api_key_validated = False

# Apply theme
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

# Get AI model
ai_model = get_gemini_model()

# --------------------------
# Sidebar
# --------------------------
with st.sidebar:
    st.markdown("### 🤖 AI Mentor Setup")
    
    # API Key Input
    api_key_input = st.text_input(
        "Gemini API Key",
        type="password",
        value=st.session_state.gemini_api_key,
        help="Get free API key from https://aistudio.google.com/app/apikey",
        placeholder="Enter your Gemini API key here"
    )
    
    if api_key_input != st.session_state.gemini_api_key:
        st.session_state.gemini_api_key = api_key_input
        st.session_state.api_key_validated = False
        st.rerun()
    
    # Validate API key button
    if st.session_state.gemini_api_key and not st.session_state.api_key_validated:
        if st.button("🔑 Validate API Key"):
            try:
                if GEMINI_AVAILABLE:
                    genai.configure(api_key=st.session_state.gemini_api_key)
                    test_model = genai.GenerativeModel('gemini-2.0-flash')
                    # Quick test
                    test_response = test_model.generate_content(
                        "Say 'OK' if you can read this.",
                        generation_config=genai.types.GenerationConfig(max_output_tokens=10)
                    )
                    st.session_state.api_key_validated = True
                    st.success("✅ API Key Valid! AI Mentor Active")
                    st.rerun()
                else:
                    st.error("❌ Please install: pip install google-generativeai")
            except Exception as e:
                st.error(f"❌ Invalid API Key: {str(e)}")
                st.session_state.api_key_validated = False
    
    # Show API status
    if st.session_state.api_key_validated:
        st.success("🤖 AI Mentor: ✅ Active")
    else:
        st.warning("🤖 AI Mentor: ⚠️ Not Configured")
        with st.expander("📖 How to get API Key"):
            st.markdown("""
            **Get Your FREE Gemini API Key:**
            
            1. Visit: https://aistudio.google.com/app/apikey
            2. Sign in with Google account
            3. Click "Create API Key"
            4. Copy the key
            5. Paste it above and click "Validate API Key"
            
            **Note:** Free tier includes generous limits!
            """)
    
    st.markdown("---")
    
    st.markdown("### ⚙️ Settings")
    
    if st.button("🌓 Toggle Theme"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()
    
    st.markdown("---")
    
    if st.session_state.started:
        st.markdown("### 📊 Progress")
        progress = len(st.session_state.user_answers) / len(QUESTIONS)
        st.markdown(f'<div class="progress-bar"><div class="progress-bar-fill" style="width: {progress*100}%"></div></div>', unsafe_allow_html=True)
        st.markdown(f"**{len(st.session_state.user_answers)}/{len(QUESTIONS)}** completed")
        
        if st.session_state.user_answers:
            correct = sum(1 for a in st.session_state.user_answers if a.get("is_correct"))
            total_points = sum(a.get("points_earned", 0) for a in st.session_state.user_answers)
            st.metric("Correct", f"{correct}/{len(st.session_state.user_answers)}")
            st.metric("Points", total_points)

# --------------------------
# Immediate Feedback Display Function
# --------------------------
def show_immediate_feedback(ai_analysis: Dict, question: dict, student_answer: str, 
                           answer_type: str, result_value=None, expected_value=None, stats=None):
    """Display immediate detailed feedback after each answer submission"""
    
    st.markdown("---")
    
    # Header with score
    is_correct = ai_analysis.get("is_correct", False)
    points_earned = ai_analysis.get("points_earned", 0)
    max_points = question["points"]
    score = ai_analysis.get("score", 0)
    
    if is_correct:
        header_color = "#22c55e"
        status_emoji = "✅"
        status_text = "Excellent Work!"
    elif score >= 0.5:
        header_color = "#f59e0b"
        status_emoji = "⚡"
        status_text = "Good Attempt!"
    else:
        header_color = "#ef4444"
        status_emoji = "📚"
        status_text = "Keep Learning!"
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {header_color}15, {header_color}05); 
                border: 2px solid {header_color}; border-radius: 12px; padding: 20px; margin: 20px 0;">
        <div style="text-align: center;">
            <div style="font-size: 48px; margin-bottom: 10px;">{status_emoji}</div>
            <div style="font-size: 28px; font-weight: 700; color: {header_color};">{status_text}</div>
            <div style="font-size: 20px; margin-top: 10px; color: #64748b;">
                Score: <strong style="color: {header_color};">{points_earned}/{max_points}</strong> points 
                ({score*100:.0f}% accuracy)
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # AI Mentor's Detailed Feedback
    st.markdown('<div class="ai-feedback">', unsafe_allow_html=True)
    st.markdown('<div class="ai-badge">🤖 AI MENTOR\'S DETAILED FEEDBACK</div>', unsafe_allow_html=True)
    
    # Main feedback
    feedback = ai_analysis.get("feedback", "Good effort!")
    st.markdown(f"### 📝 Analysis")
    st.markdown(feedback)
    
    # For code questions, show results comparison
    if answer_type == "code" and result_value is not None:
        st.markdown("### 💻 Code Execution Results")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            **Your Result:**  
            `{result_value}`
            """)
            if stats:
                st.markdown(f"⏱️ Execution time: `{stats.get('execution_time', 0):.4f}s`")
        with col2:
            st.markdown(f"""
            **Expected Result:**  
            `{expected_value}`
            """)
            if result_value == expected_value or (isinstance(result_value, (int, float)) and isinstance(expected_value, (int, float)) and abs(result_value - expected_value) < 0.001):
                st.success("✅ Perfect match!")
            else:
                st.warning("⚠️ Results don't match")
        
        # Code quality assessment
        code_quality = ai_analysis.get("code_quality", "N/A")
        if code_quality != "N/A":
            quality_colors = {
                "excellent": "#22c55e",
                "good": "#3b82f6", 
                "fair": "#f59e0b",
                "poor": "#ef4444"
            }
            quality_color = quality_colors.get(code_quality.lower(), "#64748b")
            st.markdown(f"""
            **Code Quality:** <span style="background: {quality_color}; color: white; padding: 4px 12px; 
            border-radius: 12px; font-weight: 600;">{code_quality.upper()}</span>
            """, unsafe_allow_html=True)
    
    # Strengths and Improvements side by side
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        strengths = ai_analysis.get("strengths", [])
        if strengths:
            st.markdown("### ✨ What You Did Well")
            for i, strength in enumerate(strengths, 1):
                st.markdown(f"""
                <div style="background: rgba(34, 197, 94, 0.1); padding: 12px; 
                            border-radius: 8px; margin: 8px 0; border-left: 3px solid #22c55e;">
                    <strong>{i}.</strong> {strength}
                </div>
                """, unsafe_allow_html=True)
    
    with col2:
        improvements = ai_analysis.get("improvements", [])
        if improvements:
            st.markdown("### 📈 Areas to Improve")
            for i, improvement in enumerate(improvements, 1):
                st.markdown(f"""
                <div style="background: rgba(59, 130, 246, 0.1); padding: 12px; 
                            border-radius: 8px; margin: 8px 0; border-left: 3px solid #3b82f6;">
                    <strong>{i}.</strong> {improvement}
                </div>
                """, unsafe_allow_html=True)
    
    # Better approach suggestion (if available)
    better_approach = ai_analysis.get("better_approach")
    if better_approach:
        st.markdown("---")
        st.markdown("### 💡 Pro Tip: Better Approach")
        st.info(better_approach)
    
    # Concept understanding (for theory)
    if answer_type == "theory":
        core_understood = ai_analysis.get("core_concepts_understood")
        if core_understood is not None:
            if core_understood:
                st.success("✅ **Core concepts understood** - You have a solid grasp of the fundamentals!")
            else:
                st.warning("⚠️ **Review core concepts** - Revisit the key definitions and principles.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Encouragement message
    if is_correct:
        encouragement = "🎉 Outstanding! You're mastering this topic. Keep up the excellent work!"
    elif score >= 0.7:
        encouragement = "👍 Great job! You're on the right track. Review the feedback to perfect your understanding."
    elif score >= 0.5:
        encouragement = "💪 Good effort! You've got the basics. Focus on the improvement areas to level up."
    else:
        encouragement = "📚 Don't worry! Learning takes time. Review the concepts and try similar problems for practice."
    
    st.info(encouragement)

# --------------------------
# UI Functions
# --------------------------
def show_home():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">🤖 AI-Powered DS Practice Bot</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Master Data Science with personalized AI mentor feedback on every answer</div>', unsafe_allow_html=True)
    
    # Check if API key is configured
    if not st.session_state.api_key_validated:
        st.warning("⚠️ **AI Mentor not configured!** Enter your Gemini API key in the sidebar to get personalized AI feedback.")
        st.info("💡 You can still practice without AI, but you'll miss detailed feedback and analysis.")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="metric-box"><div class="metric-value">8</div><div class="metric-label">Questions</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-box"><div class="metric-value">4+4</div><div class="metric-label">Theory+Code</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-box"><div class="metric-value">110</div><div class="metric-label">Total Points</div></div>', unsafe_allow_html=True)
    with col4:
        ai_status = "✅" if st.session_state.api_key_validated else "⚠️"
        st.markdown(f'<div class="metric-box"><div class="metric-value">{ai_status}</div><div class="metric-label">AI Mentor</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    ### ✨ What Makes This Special
    
    - **🤖 AI Mentor Feedback**: Every answer gets detailed, personalized feedback from Claude
    - **📊 Comprehensive Analysis**: Deep dive into your strengths and weaknesses
    - **🎯 Smart Evaluation**: Not just right/wrong - understand WHY and HOW
    - **📈 Learning Path**: Get personalized recommendations for what to study next
    - **💡 Code Reviews**: Detailed analysis of your coding approach and quality
    - **📋 Final Report**: Complete performance analysis with actionable insights
    
    ### 🎓 You'll Practice
    - Machine Learning fundamentals (Bias-Variance, Cross-Validation)
    - Model Evaluation (Precision, Recall, F1 Score)
    - Data Analysis with Pandas (Correlation, Grouping, Feature Engineering)
    - Statistical Analysis and Data Manipulation
    """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start AI-Mentored Practice", use_container_width=True):
            st.session_state.started = True
            st.session_state.start_time = datetime.now()
            st.session_state.user_answers = []
            st.session_state.current_q = 0
            st.session_state.completed = False
            st.session_state.final_report = None
            st.rerun()

def show_question(qidx: int):
    q = QUESTIONS[qidx]
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### Question {qidx+1}/{len(QUESTIONS)}: {q['title']}")
    with col2:
        diff_class = f"diff-{q['difficulty']}"
        st.markdown(f'<div class="difficulty-badge {diff_class}">{q["difficulty"]}</div>', unsafe_allow_html=True)
    
    st.markdown(f"**Points:** {q['points']} | **Type:** {q['type'].upper()}")
    st.markdown("---")
    st.markdown(q["prompt"])
    
    if q.get("dataset"):
        with st.expander(f"📊 View `{q['dataset']}` Dataset"):
            st.dataframe(DATASETS[q["dataset"]], use_container_width=True)
    
    # Answer input
    if q["type"] == "theory":
        answer = st.text_area("✍️ Your Answer:", height=200, key=f"theory_{qidx}")
        word_count = len(answer.split()) if answer else 0
        st.markdown(f"<small>📝 Words: {word_count}</small>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("✅ Submit & Get AI Feedback", key=f"submit_{qidx}", use_container_width=True):
                if not answer or len(answer.strip()) < 20:
                    st.error("⚠️ Please write a more detailed answer (at least 20 characters)")
                else:
                    with st.spinner("🤖 AI Mentor is analyzing your answer..."):
                        ai_analysis = get_ai_feedback_theory(q, answer, ai_model)
                    
                    # Show immediate feedback
                    show_immediate_feedback(ai_analysis, q, answer, "theory")
                    
                    # Save answer
                    st.session_state.user_answers.append({
                        "id": q["id"],
                        "type": q["type"],
                        "title": q["title"],
                        "difficulty": q["difficulty"],
                        "question": q["prompt"],
                        "student_answer": answer,
                        "is_correct": ai_analysis["is_correct"],
                        "ai_analysis": ai_analysis,
                        "points_earned": ai_analysis["points_earned"],
                        "max_points": q["points"],
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Show next question button
                    st.markdown("---")
                    col_next1, col_next2, col_next3 = st.columns([1, 2, 1])
                    with col_next2:
                        if qidx + 1 < len(QUESTIONS):
                            if st.button("➡️ Continue to Next Question", key=f"next_{qidx}", use_container_width=True):
                                st.session_state.current_q = qidx + 1
                                st.rerun()
                        else:
                            if st.button("🎯 Complete & View Final Report", key=f"finish_{qidx}", use_container_width=True):
                                st.session_state.completed = True
                                st.rerun()
        
        with col2:
            with st.popover("💡 Hint"):
                st.markdown("Think about:")
                st.markdown("- Key definitions")
                st.markdown("- Real-world examples")
                st.markdown("- Trade-offs involved")
    
    elif q["type"] == "code":
        starter = q.get("starter_code", "result = None")
        answer_code = st.text_area("💻 Python Code:", value=starter, height=280, key=f"code_{qidx}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Run & Submit", key=f"submit_{qidx}", use_container_width=True):
                df = DATASETS[q["dataset"]]
                success, res, stderr, stats = safe_execute_code(answer_code, df, q.get("time_limit", 5))
                
                if not success:
                    st.error(stderr)
                else:
                    expected = REFERENCE_RESULTS.get(q["id"])
                    validator = q.get("validator", "numeric_tol")
                    
                    if validator == "numeric_tol":
                        ok, message = validator_numeric_tol(res, expected)
                    elif validator == "dict_compare":
                        ok, message = validator_dict_compare(res, expected)
                    else:
                        ok = (res == expected)
                        message = f"Expected: {expected}, Got: {res}"
                    
                    with st.spinner("🤖 AI Mentor is reviewing your code..."):
                        ai_analysis = get_ai_feedback_code(q, answer_code, res, expected, ok, stats, ai_model)
                    
                    # Show immediate feedback
                    show_immediate_feedback(ai_analysis, q, answer_code, "code", res, expected, stats)
                    
                    # Save answer
                    st.session_state.user_answers.append({
                        "id": q["id"],
                        "type": q["type"],
                        "title": q["title"],
                        "difficulty": q["difficulty"],
                        "question": q["prompt"],
                        "student_answer": answer_code,
                        "is_correct": ok,
                        "student_result": res,
                        "expected_result": expected,
                        "ai_analysis": ai_analysis,
                        "points_earned": ai_analysis["points_earned"],
                        "max_points": q["points"],
                        "execution_stats": stats,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Show next question button
                    st.markdown("---")
                    col_next1, col_next2, col_next3 = st.columns([1, 2, 1])
                    with col_next2:
                        if qidx + 1 < len(QUESTIONS):
                            if st.button("➡️ Continue to Next Question", key=f"next_{qidx}", use_container_width=True):
                                st.session_state.current_q = qidx + 1
                                st.rerun()
                        else:
                            if st.button("🎯 Complete & View Final Report", key=f"finish_{qidx}", use_container_width=True):
                                st.session_state.completed = True
                                st.rerun()
        
        with col2:
            if st.button("▶️ Test Run", key=f"test_{qidx}", use_container_width=True):
                df = DATASETS[q["dataset"]]
                success, res, stderr, stats = safe_execute_code(answer_code, df)
                
                if not success:
                    st.error(stderr)
                else:
                    st.success(f"✅ Executed! Result: `{res}` (Time: {stats['execution_time']:.4f}s)")
        
        with col3:
            with st.popover("💡 Hint"):
                st.markdown("**Tips:**")
                st.markdown("- Use pandas methods")
                st.markdown("- Assign to `result`")
                st.markdown(f"- Return type: `{type(REFERENCE_RESULTS.get(q['id'])).__name__}`")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if qidx > 0 and st.button("⬅️ Previous", use_container_width=True):
            st.session_state.current_q = qidx - 1
            st.rerun()
    with col3:
        if qidx < len(QUESTIONS) - 1 and st.button("Skip ➡️", use_container_width=True):
            st.session_state.current_q = qidx + 1
            st.rerun()

def show_results():
    # Generate final report if not already done
    if not st.session_state.final_report:
        with st.spinner("🤖 AI Mentor is preparing your comprehensive performance report..."):
            st.session_state.final_report = generate_final_report(st.session_state.user_answers, ai_model)
    
    report = st.session_state.final_report
    
    # Calculate metrics
    total_q = len(st.session_state.user_answers)
    correct = sum(1 for a in st.session_state.user_answers if a.get("is_correct"))
    total_points = sum(a.get("points_earned", 0) for a in st.session_state.user_answers)
    max_points = sum(q["points"] for q in QUESTIONS[:total_q])
    score_pct = (total_points / max_points * 100) if max_points else 0
    
    if st.session_state.start_time:
        duration = datetime.now() - st.session_state.start_time
        time_str = f"{int(duration.total_seconds() / 60)}m {int(duration.total_seconds() % 60)}s"
    else:
        time_str = "N/A"
    
    # Header
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 🎓 Your Comprehensive Performance Report")
    
    if score_pct >= 90:
        grade, color = "🏆 Outstanding", "#22c55e"
    elif score_pct >= 75:
        grade, color = "🌟 Excellent", "#3b82f6"
    elif score_pct >= 60:
        grade, color = "👍 Good", "#f59e0b"
    else:
        grade, color = "📚 Keep Learning", "#ef4444"
    
    st.markdown(f'<div style="text-align:center; font-size:42px; font-weight:800; color:{color}; margin:20px 0;">{grade}</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-box"><div class="metric-value">{total_points}/{max_points}</div><div class="metric-label">Points</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-box"><div class="metric-value">{score_pct:.1f}%</div><div class="metric-label">Score</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-box"><div class="metric-value">{correct}/{total_q}</div><div class="metric-label">Correct</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-box"><div class="metric-value">{time_str}</div><div class="metric-label">Duration</div></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # AI Mentor's Overall Feedback
    st.markdown('<div class="card ai-feedback">', unsafe_allow_html=True)
    st.markdown('<div class="ai-badge">🤖 AI MENTOR OVERALL ASSESSMENT</div>', unsafe_allow_html=True)
    st.markdown(f"### {report.get('overall_feedback', 'Great work on completing all questions!')}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Strengths and Weaknesses
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="strength-box">', unsafe_allow_html=True)
        st.markdown("### 💪 Your Strengths")
        for strength in report.get("strengths", []):
            st.markdown(f"✅ **{strength}**")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="weakness-box">', unsafe_allow_html=True)
        st.markdown("### 🎯 Areas for Growth")
        for weakness in report.get("weaknesses", []):
            st.markdown(f"📌 **{weakness}**")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Recommendations
    st.markdown('<div class="recommendation-box">', unsafe_allow_html=True)
    st.markdown("### 🚀 Personalized Recommendations")
    for i, rec in enumerate(report.get("recommendations", []), 1):
        st.markdown(f"{i}. **{rec}**")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Learning Path
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 📚 Your Personalized Learning Path")
    
    for item in report.get("learning_path", []):
        priority_color = {"high": "#ef4444", "medium": "#f59e0b", "low": "#22c55e"}
        priority = item.get("priority", "medium")
        color = priority_color.get(priority, "#3b82f6")
        
        st.markdown(f"""
        <div style="background: rgba(59, 130, 246, 0.05); padding: 16px; border-radius: 8px; margin: 12px 0; border-left: 4px solid {color};">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <h4 style="margin: 0;">📖 {item.get('topic', 'Topic')}</h4>
                <span style="background: {color}; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;">
                    {priority.upper()} PRIORITY
                </span>
            </div>
            <p style="margin: 8px 0 0 0; color: #64748b;">{item.get('resources', 'Practice more on this topic')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Detailed Question Breakdown
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 📝 Detailed Question-by-Question Analysis")
    
    for i, ans in enumerate(st.session_state.user_answers, start=1):
        ai = ans.get("ai_analysis", {})
        status_icon = "✅" if ans["is_correct"] else "❌"
        diff_class = f"diff-{ans['difficulty']}"
        
        with st.expander(f"{status_icon} Q{i}: {ans['title']} - {ans['points_earned']}/{ans['max_points']} pts", expanded=False):
            st.markdown(f'<span class="difficulty-badge {diff_class}">{ans["difficulty"]}</span>', unsafe_allow_html=True)
            
            st.markdown("**Question:**")
            st.markdown(ans["question"])
            
            st.markdown("**Your Answer:**")
            if ans["type"] == "theory":
                st.write(ans["student_answer"])
            else:
                st.code(ans["student_answer"], language="python")
                st.markdown(f"**Result:** `{ans.get('student_result')}` | **Expected:** `{ans.get('expected_result')}`")
            
            # AI Feedback
            st.markdown('<div class="ai-feedback">', unsafe_allow_html=True)
            st.markdown('<div class="ai-badge">🤖 AI MENTOR FEEDBACK</div>', unsafe_allow_html=True)
            st.markdown(f"**{ai.get('feedback', 'Good attempt!')}**")
            
            col1, col2 = st.columns(2)
            with col1:
                if ai.get("strengths"):
                    st.markdown("**✨ What you did well:**")
                    for s in ai["strengths"]:
                        st.markdown(f"- {s}")
            
            with col2:
                if ai.get("improvements"):
                    st.markdown("**📈 How to improve:**")
                    for imp in ai["improvements"]:
                        st.markdown(f"- {imp}")
            
            if ai.get("better_approach"):
                st.info(f"💡 **Better approach:** {ai['better_approach']}")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Closing Message
    if report.get("closing_message"):
        st.markdown('<div class="card ai-feedback">', unsafe_allow_html=True)
        st.markdown('<div class="ai-badge">🤖 MENTOR\'S MESSAGE</div>', unsafe_allow_html=True)
        st.markdown(f"### {report['closing_message']}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Action Buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Retry Practice", use_container_width=True):
            for k in ["user_answers", "current_q", "started", "completed", "start_time", "final_report"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()
    
    with col2:
        if st.button("🏠 Back to Home", use_container_width=True):
            for k in ["user_answers", "current_q", "started", "completed", "start_time", "final_report"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()
    
    with col3:
        # Export comprehensive report
        export_data = {
            "summary": {
                "score": f"{total_points}/{max_points}",
                "percentage": f"{score_pct:.1f}%",
                "correct": f"{correct}/{total_q}",
                "time": time_str
            },
            "ai_report": report,
            "detailed_answers": st.session_state.user_answers
        }
        
        st.download_button(
            "📥 Download Full Report",
            data=json.dumps(export_data, indent=2),
            file_name=f"ds_mentor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

# --------------------------
# Main Routing
# --------------------------
st.title("🎓 AI-Powered Data Science Practice Bot")

if not st.session_state.started:
    show_home()
else:
    if not st.session_state.completed:
        show_question(st.session_state.current_q)
    else:
        show_results()

