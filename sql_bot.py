"""
AI-Powered Data Science Practice Bot with Gemini LLM Mentor

Features:
- 8 questions: 4 theory + 4 coding with multiple difficulty levels
- Gemini-powered mentor feedback for every answer (detailed, personalized)
- Comprehensive final report with strengths, weaknesses, and learning path
- Real-time AI analysis of code quality and theory understanding
- Beautiful modern UI with theme support
- Progress tracking and detailed analytics

Setup Instructions:
1. Get your FREE Gemini API key from: https://aistudio.google.com/app/apikey
2. Method 1 (Recommended): Create .streamlit/secrets.toml:
   GEMINI_API_KEY = "your-api-key-here"
3. Method 2: Set environment variable:
   export GEMINI_API_KEY="your-api-key-here"
4. Install: pip install google-generativeai streamlit pandas numpy
5. Run: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from typing import Tuple, Any, Dict, List
from datetime import datetime
import json
import os

# Gemini integration
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

st.set_page_config(page_title="AI DS Practice Bot", layout="wide", initial_sidebar_state="expanded")

# --------------------------
# Gemini Configuration
# --------------------------
def get_gemini_model():
    """Initialize Gemini model with API key from secrets or environment"""
    api_key = "AIzaSyCNhdM--Itg4WYqkZ5JJc0vZ21WvywcvaY"
    
    # Try Streamlit secrets first
    try:
        api_key = st.secrets.get("GEMINI_API_KEY")
    except:
        pass
    
    # Fall back to environment variable
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        return None, "No API key found. Please add GEMINI_API_KEY to secrets or environment."
    
    if not GEMINI_AVAILABLE:
        return None, "google-generativeai package not installed. Run: pip install google-generativeai"
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash')  # Using flash for faster responses
        return model, "AI Mentor Active!"
    except Exception as e:
        return None, f"Error initializing Gemini: {str(e)}"

# --------------------------
# CSS Styling
# --------------------------
def get_theme_css(theme="light"):
    if theme == "dark":
        return """
        <style>
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
        .stApp { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); color: #e8eef2; }
        .card { background: rgba(30, 41, 59, 0.85); border: 1px solid rgba(148, 163, 184, 0.2); border-radius: 16px; padding: 24px; margin-bottom: 20px; animation: fadeIn 0.5s ease; }
        .hero-title { color: #60a5fa; font-size: 48px; font-weight: 800; margin-bottom: 8px; }
        .ai-feedback { background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(139, 92, 246, 0.15)); border: 2px solid rgba(59, 130, 246, 0.3); border-radius: 12px; padding: 20px; margin: 20px 0; }
        .ai-badge { background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; margin-bottom: 10px; }
        .analyzing { animation: pulse 1.5s ease-in-out infinite; }
        </style>
        """
    else:
        return """
        <style>
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.7; } }
        .stApp { background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 50%, #dbeafe 100%); }
        .card { background: rgba(255, 255, 255, 0.95); border-radius: 16px; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08); padding: 24px; margin-bottom: 20px; animation: fadeIn 0.5s ease; }
        .hero-title { font-size: 48px; font-weight: 800; background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 8px; }
        .metric-box { background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); border-radius: 12px; padding: 16px; border: 2px solid #e2e8f0; text-align: center; }
        .metric-value { font-size: 32px; font-weight: 700; color: #3b82f6; }
        .metric-label { font-size: 14px; color: #64748b; text-transform: uppercase; }
        .difficulty-badge { display: inline-block; padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; text-transform: uppercase; }
        .diff-easy { background: #dcfce7; color: #166534; }
        .diff-medium { background: #fef3c7; color: #92400e; }
        .diff-hard { background: #fee2e2; color: #991b1b; }
        .ai-feedback { background: linear-gradient(135deg, rgba(59, 130, 246, 0.05), rgba(139, 92, 246, 0.05)); border: 2px solid rgba(59, 130, 246, 0.2); border-radius: 12px; padding: 20px; margin: 20px 0; }
        .ai-badge { background: linear-gradient(135deg, #3b82f6, #8b5cf6); color: white; padding: 6px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; display: inline-block; margin-bottom: 10px; }
        .analyzing { animation: pulse 1.5s ease-in-out infinite; }
        .strength-box { background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(34, 197, 94, 0.05)); border-left: 4px solid #22c55e; padding: 16px; border-radius: 8px; margin: 12px 0; }
        .weakness-box { background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(239, 68, 68, 0.05)); border-left: 4px solid #ef4444; padding: 16px; border-radius: 8px; margin: 12px 0; }
        .recommendation-box { background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(59, 130, 246, 0.05)); border-left: 4px solid #3b82f6; padding: 16px; border-radius: 8px; margin: 12px 0; }
        .progress-bar { background: #e2e8f0; border-radius: 10px; height: 10px; overflow: hidden; margin: 10px 0; }
        .progress-bar-fill { height: 100%; background: linear-gradient(90deg, #3b82f6 0%, #8b5cf6 100%); transition: width 0.4s ease; }
        .stButton > button { background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important; color: white !important; font-weight: 600; padding: 12px 24px; border-radius: 10px; border: none; transition: transform 0.2s; }
        .stButton > button:hover { transform: translateY(-2px); }
        </style>
        """

# --------------------------
# Sample Datasets
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
# Questions Database
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
# Gemini AI Analysis Functions
# --------------------------
def get_ai_feedback_theory(question: dict, student_answer: str, model) -> Dict:
    """Get detailed Gemini AI mentor feedback for theory answers"""
    if not model:
        return {
            "is_correct": len(student_answer.split()) >= 30,
            "score": 0.5,
            "feedback": "⚠️ AI mentor unavailable. Please add your Gemini API key for detailed analysis.",
            "strengths": ["Attempted the question"],
            "improvements": ["Add Gemini API key for personalized feedback"],
            "points_earned": int(question["points"] * 0.5)
        }
    
    prompt = f"""You are an expert Data Science mentor providing detailed, constructive feedback to a student.

Question ({question['difficulty']} difficulty, {question['points']} points):
{question['prompt']}

Student's Answer:
{student_answer}

Analyze this answer as a caring but thorough mentor and provide:
1. Overall assessment (correct/partially correct/incorrect)
2. Score from 0.0 to 1.0 based on accuracy and completeness
3. Detailed feedback (2-3 sentences explaining what's good and what's missing)
4. 2-3 specific strengths (what they understood well)
5. 2-3 specific areas for improvement with concrete study suggestions
6. Whether core concepts are understood

Respond in JSON format:
{{
    "is_correct": true/false,
    "score": 0.0-1.0,
    "feedback": "detailed constructive feedback",
    "strengths": ["strength1", "strength2"],
    "improvements": ["improvement1 with study tip", "improvement2 with study tip"],
    "core_concepts_understood": true/false
}}

Be encouraging and specific. Focus on learning, not just correctness."""

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
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        result["points_earned"] = int(result["score"] * question["points"])
        return result
    except Exception as e:
        st.error(f"❌ AI Analysis Error: {str(e)}")
        return {
            "is_correct": False,
            "score": 0.5,
            "feedback": f"Error getting AI feedback: {str(e)}. Your answer has been recorded.",
            "strengths": ["Attempted the question"],
            "improvements": ["Review the topic carefully"],
            "points_earned": int(question["points"] * 0.5)
        }

def get_ai_feedback_code(question: dict, student_code: str, result_value: Any, 
                         expected: Any, is_correct: bool, model) -> Dict:
    """Get detailed Gemini AI mentor feedback for code answers"""
    if not model:
        return {
            "is_correct": is_correct,
            "score": 1.0 if is_correct else 0.3,
            "feedback": "⚠️ AI mentor unavailable. Please add your Gemini API key for code review.",
            "code_quality": "Unknown",
            "strengths": ["Code executed successfully"],
            "improvements": ["Add Gemini API key for detailed code review"],
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
Correctness: {"✅ Correct" if is_correct else "❌ Incorrect"}

Analyze this code and provide:
1. Overall code quality (excellent/good/fair/needs improvement)
2. Score from 0.0 to 1.0 (correctness + code quality + efficiency)
3. Detailed feedback explaining the approach and any issues
4. 2-3 code strengths (good practices, correct methods)
5. 2-3 improvements (better approaches, optimization, best practices)
6. Optional: A better/more efficient approach if applicable

Respond in JSON format:
{{
    "is_correct": true/false,
    "score": 0.0-1.0,
    "feedback": "detailed constructive feedback",
    "code_quality": "excellent/good/fair/needs improvement",
    "strengths": ["strength1", "strength2"],
    "improvements": ["improvement1", "improvement2"],
    "better_approach": "optional: suggest if there's a significantly better way"
}}

Be specific and educational. Praise good practices, suggest concrete improvements."""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=1200,
            )
        )
        
        # Extract JSON
        response_text = response.text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        result = json.loads(response_text)
        result["points_earned"] = int(result["score"] * question["points"])
        return result
    except Exception as e:
        st.error(f"❌ AI Analysis Error: {str(e)}")
        fallback_score = 1.0 if is_correct else 0.3
        return {
            "is_correct": is_correct,
            "score": fallback_score,
            "feedback": f"Error getting AI feedback: {str(e)}. Your code has been recorded.",
            "code_quality": "unknown",
            "strengths": ["Code executed"],
            "improvements": ["Review solution approach"],
            "points_earned": int(question["points"] * fallback_score)
        }

def generate_final_report(all_answers: List[Dict], model) -> Dict:
    """Generate comprehensive final report with Gemini AI analysis"""
    if not model:
        return {
            "overall_feedback": "Practice session complete! Add your Gemini API key for detailed performance analysis.",
            "strengths": ["Completed all questions"],
            "weaknesses": ["AI analysis unavailable - add API key"],
            "recommendations": ["Set up Gemini API for personalized learning path"],
            "learning_path": [],
            "closing_message": "Keep practicing! Add your API key for AI-powered insights."
        }
    
    # Prepare performance summary
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
    
    total_q = len(all_answers)
    correct = sum(1 for a in all_answers if a.get("is_correct"))
    total_points = sum(a.get("points_earned", 0) for a in all_answers)
    max_points = sum(a.get("max_points", 0) for a in all_answers)
    
    prompt = f"""You are a senior Data Science mentor writing a comprehensive, personalized performance report.

The student completed {total_q} questions (4 theory + 4 coding) with the following results:
- Correct: {correct}/{total_q}
- Points: {total_points}/{max_points}

Detailed Performance:
{json.dumps(summary, indent=2)}

Create a thorough, personalized mentor report with:
1. Overall performance summary (3-4 sentences, be honest but encouraging)
2. Top 3-4 strengths (specific skills demonstrated well)
3. Top 3-4 weaknesses (specific areas needing work)
4. 4-5 actionable recommendations (concrete steps to improve)
5. Personalized learning path (4-5 prioritized topics with specific resources)
6. Motivational closing message

Respond in JSON format:
{{
    "overall_feedback": "comprehensive, personalized summary",
    "strengths": ["specific strength 1", "specific strength 2", "specific strength 3"],
    "weaknesses": ["specific weakness 1", "specific weakness 2", "specific weakness 3"],
    "recommendations": ["actionable rec 1", "actionable rec 2", "actionable rec 3", "actionable rec 4"],
    "learning_path": [
        {{"topic": "specific topic", "priority": "high/medium/low", "resources": "concrete resource suggestions"}},
        ...
    ],
    "closing_message": "personalized motivational message"
}}

Be specific, actionable, and encouraging. This is their learning journey."""

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.8,
                max_output_tokens=2500,
            )
        )
        
        # Extract JSON
        response_text = response.text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        return json.loads(response_text)
    except Exception as e:
        st.error(f"❌ Final Report Error: {str(e)}")
        return {
            "overall_feedback": f"Great work completing all {total_q} questions! You scored {total_points}/{max_points} points.",
            "strengths": ["Persistence", "Completed all questions"],
            "weaknesses": ["Add API key for detailed analysis"],
            "recommendations": ["Review incorrect answers", "Practice more problems"],
            "learning_path": [{"topic": "Review fundamentals", "priority": "high", "resources": "Online DS courses"}],
            "closing_message": "Keep learning and improving!"
        }

# --------------------------
# Code Execution
# --------------------------
def safe_execute_code(user_code: str, dataframe: pd.DataFrame) -> Tuple[bool, Any, str]:
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
    
    try:
        exec(user_code, allowed_globals, local_vars)
        
        if "result" not in local_vars:
            return False, None, "⚠️ Error: You must assign your answer to variable `result`"
        
        return True, local_vars["result"], ""
    except Exception as e:
        return False, None, f"❌ Execution Error: {str(e)}"

def validator_numeric_tol(student_value: Any, expected_value: Any, tol=1e-3) -> Tuple[bool, str]:
    """Validate numeric answers with tolerance"""
    try:
        s, e = float(student_value), float(expected_value)
        diff = abs(s - e)
        if diff <= tol:
            return True, f"✅ Correct! (Expected: {e}, Got: {s})"
        return False, f"❌ Incorrect. Expected: {e}, Got: {s}, Difference: {diff:.6f}"
    except:
        return False, f"❌ Cannot compare values. Expected number, got {type(student_value).__name__}"

def validator_dict_compare(student_value: Any, expected_value: Any) -> Tuple[bool, str]:
    """Validate dictionary answers"""
    if not isinstance(student_value, dict):
        return False, f"❌ Expected dictionary, got {type(student_value).__name__}"
    if set(student_value.keys()) != set(expected_value.keys()):
        return False, f"❌ Keys don't match. Expected: {set(expected_value.keys())}, Got: {set(student_value.keys())}"
    for key in expected_value:
        if abs(student_value[key] - expected_value[key]) > 0.01:
            return False, f"❌ Wrong value for '{key}'. Expected: {expected_value[key]}, Got: {student_value[key]}"
    return True, "✅ Perfect! All values match."

# Compute reference answers
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
# Session State Initialization
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

# Apply theme
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

# Initialize Gemini AI
ai_model, ai_status = get_gemini_model()

# --------------------------
# Sidebar
# --------------------------
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    if st.button("🌓 Toggle Theme"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()
    
    st.markdown("---")
    st.markdown("### 🤖 AI Mentor Status")
    
    if ai_model:
        st.success("✅ " + ai_status)
        st.info("💡 AI will analyze every answer you submit!")
    else:
        st.error("❌ AI Mentor Inactive")
        st.warning(ai_status)
        
        with st.expander("📖 Quick Setup Guide"):
            st.markdown("""
            **Get FREE Gemini API Key:**
            
            1. Visit: https://aistudio.google.com/app/apikey
            2. Click "Create API Key"
            3. Copy your key
            
            **Option 1: Streamlit Secrets (Recommended)**
            Create `.streamlit/secrets.toml`:
            ```toml
            GEMINI_API_KEY = "AIzaSyCNhdM--Itg4WYqkZ5JJc0vZ21WvywcvaY"
            ```
            
            **Option 2: Environment Variable**
            ```bash
            export GEMINI_API_KEY="AIzaSyCNhdM--Itg4WYqkZ5JJc0vZ21WvywcvaY"
            ```
            
            **Install Package:**
            ```bash
            pip install google-generativeai
            ```
            
            Then restart the app!
            """)
    
    if st.session_state.started:
        st.markdown("---")
        st.markdown("### 📊 Progress")
        progress = len(st.session_state.user_answers) / len(QUESTIONS)
        st.markdown(f'<div class="progress-bar"><div class="progress-bar-fill" style="width: {progress*100}%"></div></div>', unsafe_allow_html=True)
        st.markdown(f"**{len(st.session_state.user_answers)}/{len(QUESTIONS)}** completed")
        
        if st.session_state.user_answers:
            correct = sum(1 for a in st.session_state.user_answers if a.get("is_correct"))
            total_points = sum(a.get("points_earned", 0) for a in st.session_state.user_answers)
            st.metric("✅ Correct", f"{correct}/{len(st.session_state.user_answers)}")
            st.metric("🎯 Points", total_points)

# --------------------------
# Main UI Functions
# --------------------------
def show_home():
    """Home page with introduction"""
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">🤖 AI-Powered DS Practice Bot</div>', unsafe_allow_html=True)
    st.markdown('<p style="font-size: 18px; color: #64748b; margin-bottom: 20px;">Master Data Science with personalized Gemini AI mentor feedback on every answer</p>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="metric-box"><div class="metric-value">8</div><div class="metric-label">Questions</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-box"><div class="metric-value">4+4</div><div class="metric-label">Theory+Code</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-box"><div class="metric-value">110</div><div class="metric-label">Total Points</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-box"><div class="metric-value">🤖</div><div class="metric-label">AI Mentor</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### ✨ What Makes This Special
        
        - **🤖 Gemini AI Mentor**: Every answer gets detailed, personalized feedback
        - **📊 Deep Analysis**: Understand your strengths and weaknesses
        - **🎯 Smart Evaluation**: Not just right/wrong - learn WHY and HOW
        - **📈 Learning Path**: Personalized recommendations for what to study next
        - **💡 Code Reviews**: Detailed analysis of your coding approach
        - **📋 Final Report**: Complete performance analysis with insights
        """)
    
    with col2:
        st.markdown("""
        ### 🎓 You'll Practice
        
        - **Machine Learning**: Bias-Variance, Cross-Validation, Feature Scaling
        - **Model Evaluation**: Precision, Recall, F1 Score
        - **Data Analysis**: Pandas operations, correlations, aggregations
        - **Feature Engineering**: Creating and analyzing new features
        - **Statistical Analysis**: Data manipulation and insights
        - **Python Coding**: Practical data science implementations
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if not ai_model:
        st.warning("⚠️ AI Mentor is currently inactive. Add your Gemini API key to get AI-powered feedback on every answer! (See sidebar)")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start AI-Mentored Practice", use_container_width=True, type="primary"):
            st.session_state.started = True
            st.session_state.start_time = datetime.now()
            st.session_state.user_answers = []
            st.session_state.current_q = 0
            st.session_state.completed = False
            st.session_state.final_report = None
            st.rerun()

def show_question(qidx: int):
    """Display a question and handle submission"""
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
    
    st.markdown("---")
    
    # Handle Theory Questions
    if q["type"] == "theory":
        answer = st.text_area("✍️ Your Answer:", height=200, key=f"theory_{qidx}", 
                             placeholder="Type your detailed answer here...")
        word_count = len(answer.split()) if answer else 0
        st.caption(f"📝 Words: {word_count} | Minimum recommended: 50 words")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("✅ Submit & Get AI Feedback", key=f"submit_{qidx}", use_container_width=True, type="primary"):
                if not answer or len(answer.strip()) < 20:
                    st.error("⚠️ Please write a more detailed answer (at least 20 characters)")
                else:
                    with st.spinner("🤖 Gemini AI Mentor is analyzing your answer..."):
                        time.sleep(0.5)  # Small delay for UX
                        ai_analysis = get_ai_feedback_theory(q, answer, ai_model)
                    
                    # Show immediate feedback
                    st.markdown('<div class="ai-feedback">', unsafe_allow_html=True)
                    st.markdown('<div class="ai-badge">🤖 GEMINI AI FEEDBACK</div>', unsafe_allow_html=True)
                    st.markdown(f"**Score: {ai_analysis['score']:.1%}** | **Points: {ai_analysis['points_earned']}/{q['points']}**")
                    st.markdown(f"**{ai_analysis['feedback']}**")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if ai_analysis.get("strengths"):
                            st.success("**✨ Strengths:**")
                            for s in ai_analysis["strengths"]:
                                st.write(f"• {s}")
                    with col_b:
                        if ai_analysis.get("improvements"):
                            st.info("**📈 Areas to Improve:**")
                            for imp in ai_analysis["improvements"]:
                                st.write(f"• {imp}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
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
                    
                    time.sleep(2)  # Show feedback before moving
                    
                    if qidx + 1 < len(QUESTIONS):
                        st.session_state.current_q = qidx + 1
                    else:
                        st.session_state.completed = True
                    st.rerun()
        
        with col2:
            with st.popover("💡 Hints"):
                st.markdown("**Think about:**")
                st.markdown("• Key definitions and concepts")
                st.markdown("• Real-world examples")
                st.markdown("• Trade-offs and comparisons")
                st.markdown("• Practical applications")
    
    # Handle Code Questions
    elif q["type"] == "code":
        starter = q.get("starter_code", "result = None")
        answer_code = st.text_area("💻 Write Your Python Code:", value=starter, height=280, key=f"code_{qidx}")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🚀 Run & Submit", key=f"submit_{qidx}", use_container_width=True, type="primary"):
                df = DATASETS[q["dataset"]]
                success, res, stderr = safe_execute_code(answer_code, df)
                
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
                    
                    st.write(message)
                    
                    with st.spinner("🤖 Gemini AI Mentor is reviewing your code..."):
                        time.sleep(0.5)
                        ai_analysis = get_ai_feedback_code(q, answer_code, res, expected, ok, ai_model)
                    
                    # Show immediate feedback
                    st.markdown('<div class="ai-feedback">', unsafe_allow_html=True)
                    st.markdown('<div class="ai-badge">🤖 GEMINI CODE REVIEW</div>', unsafe_allow_html=True)
                    st.markdown(f"**Score: {ai_analysis['score']:.1%}** | **Points: {ai_analysis['points_earned']}/{q['points']}** | **Quality: {ai_analysis.get('code_quality', 'N/A')}**")
                    st.markdown(f"**{ai_analysis['feedback']}**")
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if ai_analysis.get("strengths"):
                            st.success("**✨ Code Strengths:**")
                            for s in ai_analysis["strengths"]:
                                st.write(f"• {s}")
                    with col_b:
                        if ai_analysis.get("improvements"):
                            st.info("**📈 Improvements:**")
                            for imp in ai_analysis["improvements"]:
                                st.write(f"• {imp}")
                    
                    if ai_analysis.get("better_approach"):
                        st.info(f"💡 **Better Approach:** {ai_analysis['better_approach']}")
                    st.markdown('</div>', unsafe_allow_html=True)
                    
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
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    time.sleep(2)
                    
                    if qidx + 1 < len(QUESTIONS):
                        st.session_state.current_q = qidx + 1
                    else:
                        st.session_state.completed = True
                    st.rerun()
        
        with col2:
            if st.button("▶️ Test Run", key=f"test_{qidx}", use_container_width=True):
                df = DATASETS[q["dataset"]]
                success, res, stderr = safe_execute_code(answer_code, df)
                
                if not success:
                    st.error(stderr)
                else:
                    st.success(f"✅ Code executed! Result: `{res}`")
        
        with col3:
            with st.popover("💡 Hints"):
                st.markdown("**Tips:**")
                st.markdown("• Use pandas/numpy methods")
                st.markdown("• Assign final answer to `result`")
                st.markdown("• Test with 'Test Run' first")
                st.markdown(f"• Expected type: `{type(REFERENCE_RESULTS.get(q['id'])).__name__}`")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Navigation
    st.markdown("---")
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
    """Display comprehensive final results with AI report"""
    
    # Generate final AI report if not done
    if not st.session_state.final_report:
        with st.spinner("🤖 Gemini AI Mentor is preparing your comprehensive performance report..."):
            time.sleep(1)
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
    st.markdown("### Powered by Gemini AI")
    
    if score_pct >= 90:
        grade, color = "🏆 Outstanding", "#22c55e"
    elif score_pct >= 75:
        grade, color = "🌟 Excellent", "#3b82f6"
    elif score_pct >= 60:
        grade, color = "👍 Good", "#f59e0b"
    else:
        grade, color = "📚 Keep Learning", "#ef4444"
    
    st.markdown(f'<div style="text-align:center; font-size:48px; font-weight:800; color:{color}; margin:20px 0;">{grade}</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-box"><div class="metric-value">{total_points}/{max_points}</div><div class="metric-label">Points Earned</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-box"><div class="metric-value">{score_pct:.1f}%</div><div class="metric-label">Score</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-box"><div class="metric-value">{correct}/{total_q}</div><div class="metric-label">Correct</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-box"><div class="metric-value">{time_str}</div><div class="metric-label">Time Taken</div></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # AI Mentor's Overall Assessment
    st.markdown('<div class="card ai-feedback">', unsafe_allow_html=True)
    st.markdown('<div class="ai-badge">🤖 GEMINI AI MENTOR - OVERALL ASSESSMENT</div>', unsafe_allow_html=True)
    st.markdown(f"### {report.get('overall_feedback', 'Great work on completing all questions!')}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Strengths and Weaknesses
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="strength-box">', unsafe_allow_html=True)
        st.markdown("### 💪 Your Strengths")
        for i, strength in enumerate(report.get("strengths", []), 1):
            st.markdown(f"**{i}.** {strength}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="weakness-box">', unsafe_allow_html=True)
        st.markdown("### 🎯 Areas for Growth")
        for i, weakness in enumerate(report.get("weaknesses", []), 1):
            st.markdown(f"**{i}.** {weakness}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Actionable Recommendations
    st.markdown('<div class="recommendation-box">', unsafe_allow_html=True)
    st.markdown("### 🚀 Actionable Recommendations")
    for i, rec in enumerate(report.get("recommendations", []), 1):
        st.markdown(f"**{i}.** {rec}")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Personalized Learning Path
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 📚 Your Personalized Learning Path")
    st.caption("Curated by Gemini AI based on your performance")
    
    for item in report.get("learning_path", []):
        priority_colors = {"high": "#ef4444", "medium": "#f59e0b", "low": "#22c55e"}
        priority = item.get("priority", "medium")
        color = priority_colors.get(priority, "#3b82f6")
        
        st.markdown(f"""
        <div style="background: rgba(59, 130, 246, 0.05); padding: 18px; border-radius: 10px; margin: 14px 0; border-left: 5px solid {color};">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <h4 style="margin: 0; color: #1e293b;">📖 {item.get('topic', 'Topic')}</h4>
                <span style="background: {color}; color: white; padding: 5px 14px; border-radius: 15px; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;">
                    {priority.upper()} PRIORITY
                </span>
            </div>
            <p style="margin: 4px 0 0 0; color: #475569; line-height: 1.6;">{item.get('resources', 'Practice more on this topic')}</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Detailed Question Breakdown
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 📝 Detailed Question-by-Question Analysis")
    
    for i, ans in enumerate(st.session_state.user_answers, 1):
        ai = ans.get("ai_analysis", {})
        status_icon = "✅" if ans["is_correct"] else "❌"
        diff_class = f"diff-{ans['difficulty']}"
        
        with st.expander(f"{status_icon} Q{i}: {ans['title']} ({ans['difficulty']}) - {ans['points_earned']}/{ans['max_points']} points", expanded=False):
            st.markdown(f'<span class="difficulty-badge {diff_class}">{ans["difficulty"]}</span>', unsafe_allow_html=True)
            
            st.markdown("**Question:**")
            st.info(ans["question"])
            
            st.markdown("**Your Answer:**")
            if ans["type"] == "theory":
                st.write(ans["student_answer"])
            else:
                st.code(ans["student_answer"], language="python")
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.metric("Your Result", ans.get('student_result', 'N/A'))
                with col_r2:
                    st.metric("Expected Result", ans.get('expected_result', 'N/A'))
            
            # AI Detailed Feedback
            st.markdown('<div class="ai-feedback">', unsafe_allow_html=True)
            st.markdown('<div class="ai-badge">🤖 GEMINI AI DETAILED FEEDBACK</div>', unsafe_allow_html=True)
            st.markdown(f"**Score: {ai.get('score', 0):.1%}** | **Assessment: {ai.get('feedback', 'N/A')}**")
            
            col1, col2 = st.columns(2)
            with col1:
                if ai.get("strengths"):
                    st.success("**✨ What You Did Well:**")
                    for s in ai["strengths"]:
                        st.markdown(f"• {s}")
            
            with col2:
                if ai.get("improvements"):
                    st.warning("**📈 How to Improve:**")
                    for imp in ai["improvements"]:
                        st.markdown(f"• {imp}")
            
            if ai.get("better_approach"):
                st.info(f"💡 **Suggested Better Approach:** {ai['better_approach']}")
            
            if ai.get("code_quality"):
                st.caption(f"Code Quality Rating: **{ai['code_quality']}**")
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Mentor's Closing Message
    if report.get("closing_message"):
        st.markdown('<div class="card ai-feedback">', unsafe_allow_html=True)
        st.markdown('<div class="ai-badge">🤖 YOUR MENTOR\'S FINAL MESSAGE</div>', unsafe_allow_html=True)
        st.markdown(f"## {report['closing_message']}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Action Buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Take Practice Again", use_container_width=True):
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
        # Export comprehensive report as JSON
        export_data = {
            "summary": {
                "score_percentage": f"{score_pct:.1f}%",
                "points": f"{total_points}/{max_points}",
                "correct_answers": f"{correct}/{total_q}",
                "time_taken": time_str,
                "timestamp": datetime.now().isoformat()
            },
            "gemini_ai_report": report,
            "detailed_answers": st.session_state.user_answers
        }
        
        st.download_button(
            "📥 Download Full Report (JSON)",
            data=json.dumps(export_data, indent=2),
            file_name=f"gemini_ds_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

# --------------------------
# Main Application Router
# --------------------------
def main():
    st.title("🎓 AI-Powered Data Science Practice Bot")
    st.caption("Powered by Google Gemini AI")
    
    if not st.session_state.started:
        show_home()
    else:
        if not st.session_state.completed:
            show_question(st.session_state.current_q)
        else:
            show_results()

if __name__ == "__main__":
    main()
