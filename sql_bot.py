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

# --- CONFIGURATION & SESSION STATE ---
st.set_page_config(
    page_title="DataMentor AI - Practice Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
if "current_q_submitted" not in st.session_state:
    st.session_state.current_q_submitted = False
if "current_q_feedback" not in st.session_state:
    st.session_state.current_q_feedback = None
if "final_report" not in st.session_state:
    st.session_state.final_report = None

# LLM Integration
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

HARD_CODED_GEMINI_API_KEY = "AIzaSyCipiGM8HxiPiVtfePpGN-TiIk5JVBO6_M"

# --- DATASETS ---
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
    {"id": 1, "type": "theory", "difficulty": "easy", "title": "Bias-Variance Tradeoff", "prompt": "Explain the bias-variance tradeoff in supervised machine learning. What do high bias and high variance indicate? Provide one method to reduce each.", "points": 10},
    {"id": 2, "type": "theory", "difficulty": "medium", "title": "Cross-Validation", "prompt": "Explain k-fold cross-validation in detail. How does it work, why is it better than a single train/test split, and what are potential drawbacks?", "points": 15},
    {"id": 3, "type": "theory", "difficulty": "easy", "title": "Feature Scaling", "prompt": "Why is feature scaling important in machine learning? Explain standardization vs normalization and give two examples of algorithms that require scaling.", "points": 10},
    {"id": 4, "type": "theory", "difficulty": "hard", "title": "Precision vs Recall", "prompt": "Explain precision and recall in classification. When would you prioritize one over the other? Provide a real-world scenario for each case and explain the F1 score.", "points": 20},
    {"id": 5, "type": "code", "difficulty": "easy", "title": "Correlation Analysis", "prompt": "Using the `students` DataFrame as `df`, calculate the Pearson correlation coefficient between `hours_studied` and `score`. Round to 3 decimal places and assign to `result`.", "dataset": "students", "validator": "numeric_tol", "points": 10, "starter_code": "result = None"},
    {"id": 6, "type": "code", "difficulty": "medium", "title": "Train-Test Split", "prompt": "Split the `students` DataFrame into 70% train and 30% test sets using random_state=42. Calculate the mean `score` of the test set, round to 2 decimal places, assign to `result`.", "dataset": "students", "validator": "numeric_tol", "points": 15, "starter_code": "result = None"},
    {"id": 7, "type": "code", "difficulty": "medium", "title": "Group Aggregation", "prompt": "Using the `sales` DataFrame, find the total sales for each region. Return a dictionary where keys are region names and values are total sales. Assign to `result`.", "dataset": "sales", "validator": "dict_compare", "points": 15, "starter_code": "result = None"},
    {"id": 8, "type": "code", "difficulty": "hard", "title": "Feature Engineering", "prompt": "Create a new feature `performance_score` = (score * 0.7) + (attendance * 0.3). Calculate correlation between `performance_score` and `passed`. Round to 3 decimals and assign to `result`.", "dataset": "students", "validator": "numeric_tol", "points": 20, "starter_code": "result = None"}
]

# --- HELPER FUNCTIONS (Logic remains similar to original but integrated with new state) ---

def parse_json_from_text(text: str) -> dict:
    m = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.S)
    if m: return json.loads(m.group(1))
    start = text.find('{')
    if start != -1:
        try: return json.loads(text[start:text.rfind('}')+1])
        except: pass
    raise ValueError("JSON Error")

def get_gemini_model():
    if not GEMINI_AVAILABLE: return None
    try:
        genai.configure(api_key=HARD_CODED_GEMINI_API_KEY)
        return genai.GenerativeModel('gemini-2.0-flash-exp')
    except: return None

ai_model = get_gemini_model()

def get_ai_feedback_theory(question: dict, student_answer: str, model) -> Dict:
    prompt = f"Analyze this DS theory answer: {student_answer}. Question: {question['prompt']}. Provide JSON with is_correct (bool), score (0-1), feedback (string), strengths (list), improvements (list)."
    try:
        response = model.generate_content(prompt)
        parsed = parse_json_from_text(response.text)
        parsed["points_earned"] = int(parsed.get("score", 0) * question["points"])
        return parsed
    except:
        return {"is_correct": True, "score": 0.5, "feedback": "Good attempt!", "strengths": ["Completed"], "improvements": ["Add detail"], "points_earned": 5}

def get_ai_feedback_code(question: dict, code: str, result_val: Any, expected: Any, is_correct: bool, model) -> Dict:
    prompt = f"Analyze DS code: {code}. Expected {expected}, got {result_val}. Correct: {is_correct}. Provide JSON feedback."
    try:
        response = model.generate_content(prompt)
        parsed = parse_json_from_text(response.text)
        parsed["points_earned"] = int(parsed.get("score", 0) * question["points"])
        return parsed
    except:
        score = 1.0 if is_correct else 0.0
        return {"is_correct": is_correct, "score": score, "feedback": "Code processed.", "strengths": [], "improvements": [], "points_earned": int(score * question["points"])}

def safe_execute_code(user_code: str, dataframe: pd.DataFrame) -> Tuple[bool, Any, str, dict]:
    allowed_globals = {"pd": pd, "np": np, "__builtins__": {k: __builtins__[k] for k in ['abs', 'min', 'max', 'round', 'len', 'range', 'sum', 'list', 'dict']}}
    local_vars = {"df": dataframe.copy()}
    try:
        exec(user_code, allowed_globals, local_vars)
        if "result" not in local_vars: return False, None, "⚠️ Assign the final value to `result`", {}
        return True, local_vars["result"], "", {}
    except Exception as e:
        return False, None, f"❌ Error: {str(e)}", {}

def validator_numeric_tol(s_val, e_val, tol=1e-3):
    try: return (abs(float(s_val) - float(e_val)) <= tol), ""
    except: return False, ""

def validator_dict_compare(s_val, e_val):
    if not isinstance(s_val, dict): return False, ""
    return s_val == e_val, ""

def compute_reference(qid):
    if qid == 5: return round(students_df["hours_studied"].corr(students_df["score"]), 3)
    if qid == 6: return round(students_df.sample(frac=0.3, random_state=42)["score"].mean(), 2)
    if qid == 7: return sales_df.groupby('region')['sales'].sum().to_dict()
    if qid == 8:
        df = students_df.copy()
        df['performance_score'] = (df['score'] * 0.7) + (df['attendance'] * 0.3)
        return round(df['performance_score'].corr(df['passed']), 3)
    return None

REFERENCE_RESULTS = {q["id"]: compute_reference(q["id"]) for q in QUESTIONS if q["type"] == "code"}

# --- SIDEBAR & THEME ---
with st.sidebar:
    st.title("🎓 DataMentor AI")
    st.write("---")
    if ai_model: st.success("🤖 AI Mentor Online")
    if st.button("🌓 Toggle Theme"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()
    if st.session_state.started and not st.session_state.completed:
        st.progress(st.session_state.current_q / len(QUESTIONS))
        st.write(f"Question {st.session_state.current_q + 1} of {len(QUESTIONS)}")

# --- UI LOGIC ---

if not st.session_state.started:
    # (Hero UI script here - omitted for brevity, use your existing HTML component)
    st.markdown("# Welcome to DataMentor AI")
    if st.button("🚀 Start Practice Session", type="primary", use_container_width=True):
        st.session_state.started = True
        st.session_state.start_time = datetime.now()
        st.rerun()

elif st.session_state.completed:
    st.balloons()
    st.title("Practice Complete!")
    # Summary calculation...
    if st.button("Restart Session"):
        st.session_state.clear()
        st.rerun()

else:
    q_idx = st.session_state.current_q
    q = QUESTIONS[q_idx]

    st.markdown(f"### Question {q_idx + 1}")
    st.title(q["title"])
    st.info(q["prompt"])

    # --- CODE OR THEORY UI ---
    if q["type"] == "code":
        st.markdown(f"**Dataset:** `{q['dataset']}` (available as variable `df`)")
        user_input = st.text_area("Write your code here:", value=q["starter_code"], height=200, key=f"code_in_{q_idx}", disabled=st.session_state.current_q_submitted)
        
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("▶️ Run Code", use_container_width=True, disabled=st.session_state.current_q_submitted):
                success, res, err, _ = safe_execute_code(user_input, DATASETS[q["dataset"]])
                if success: st.code(f"Result: {res}")
                else: st.error(err)
        with col2:
            if st.button("✅ Submit & Grade", type="primary", use_container_width=True, disabled=st.session_state.current_q_submitted):
                success, res, err, _ = safe_execute_code(user_input, DATASETS[q["dataset"]])
                if not success:
                    st.error(f"Cannot submit. Fix errors first: {err}")
                else:
                    ref = REFERENCE_RESULTS[q["id"]]
                    is_corr, _ = validator_numeric_tol(res, ref) if q["validator"] == "numeric_tol" else validator_dict_compare(res, ref)
                    with st.spinner("AI Grading..."):
                        fb = get_ai_feedback_code(q, user_input, res, ref, is_corr, ai_model)
                        st.session_state.current_q_feedback = fb
                        st.session_state.current_q_submitted = True
                        st.session_state.user_answers.append({**q, "user_code": user_input, **fb})
                        st.rerun()
    else:
        user_input = st.text_area("Your explanation:", height=200, key=f"theory_in_{q_idx}", disabled=st.session_state.current_q_submitted)
        if st.button("Submit Answer", type="primary", disabled=st.session_state.current_q_submitted):
            with st.spinner("AI Evaluating..."):
                fb = get_ai_feedback_theory(q, user_input, ai_model)
                st.session_state.current_q_feedback = fb
                st.session_state.current_q_submitted = True
                st.session_state.user_answers.append({**q, "user_answer": user_input, **fb})
                st.rerun()

    # --- FEEDBACK & NAVIGATION SECTION ---
    if st.session_state.current_q_submitted:
        st.markdown("---")
        fb = st.session_state.current_q_feedback
        if fb["is_correct"]: st.success(f"✅ Correct! Points: {fb['points_earned']}")
        else: st.warning(f"🧐 Review Needed. Points: {fb['points_earned']}")
        
        st.write(f"**Mentor Feedback:** {fb['feedback']}")
        
        # Next Button - Manual Trigger
        col_n1, col_n2 = st.columns([1, 4])
        with col_n1:
            if st.button("Next Question ➡️", type="primary"):
                if st.session_state.current_q + 1 < len(QUESTIONS):
                    st.session_state.current_q += 1
                    st.session_state.current_q_submitted = False
                    st.session_state.current_q_feedback = None
                    st.rerun()
                else:
                    st.session_state.completed = True
                    st.rerun()
        with col_n2:
            if st.button("🔄 Try Again (Reset This Question)"):
                st.session_state.user_answers.pop()
                st.session_state.current_q_submitted = False
                st.session_state.current_q_feedback = None
                st.rerun()
