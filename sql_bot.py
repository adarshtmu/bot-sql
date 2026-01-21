"""
AI-Powered Data Science Practice Platform
Complete Updated Code with Submit Button and Next Question Navigation
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

# Session State Initialization
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
if "show_feedback" not in st.session_state:
    st.session_state.show_feedback = False
if "current_feedback" not in st.session_state:
    st.session_state.current_feedback = None

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

# Questions Configuration
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

# Main Application Logic
if not st.session_state.started:
    # Landing Page (keeping original HTML)
    st.markdown("""
    <div style="text-align: center; padding: 40px;">
        <h1 style="font-size: 4rem; font-weight: 900; color: #8b5cf6; margin-bottom: 20px;">🎓 DataMentor AI</h1>
        <p style="font-size: 1.5rem; color: #64748b; margin-bottom: 40px;">
            Master Data Science with AI-powered practice
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Practice Session", use_container_width=True, type="primary", key="start_btn"):
            st.session_state.started = True
            st.session_state.start_time = datetime.now()
            st.rerun()

elif st.session_state.completed:
    # Results Page
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
    
    st.markdown("---")
    
    if st.button("🔄 Start New Practice Session", use_container_width=True, type="primary"):
        for key in list(st.session_state.keys()):
            if key.startswith(('answer_', 'code_', 'user_answers', 'current_q', 'started', 'completed', 'final_report', 'show_detailed_report', 'show_feedback', 'current_feedback')):
                del st.session_state[key]
        st.rerun()

else:
    # Active Question Display
    if st.session_state.current_q < len(QUESTIONS):
        q = QUESTIONS[st.session_state.current_q]
        
        st.markdown(f"""
        <div style="background: linear-gradient(145deg, rgba(255,255,255,0.1), rgba(255,255,255,0.05)); 
                    backdrop-filter: blur(30px); border-radius: 24px; padding: 40px; border: 1px solid rgba(255,255,255,0.2);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; flex-wrap: wrap;">
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
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if q['type'] == 'theory':
            # Theory Question Handling
            answer_key = f"answer_{q['id']}"
            if answer_key not in st.session_state:
                st.session_state[answer_key] = ""
            
            answer = st.text_area("Your Answer:", value=st.session_state[answer_key], height=200, 
                                 placeholder="Write your detailed answer here...", key=f"textarea_{q['id']}")
            st.session_state[answer_key] = answer
            
            # Show feedback if already submitted
            if st.session_state.show_feedback and st.session_state.current_feedback:
                ai_analysis = st.session_state.current_feedback
                score = ai_analysis.get("score", 0)
                
                st.markdown("---")
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
                
                st.markdown("---")
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("➡️ Next Question", type="primary", use_container_width=True, key=f"next_{q['id']}"):
                        st.session_state.current_q += 1
                        st.session_state.show_feedback = False
                        st.session_state.current_feedback = None
                        st.session_state[answer_key] = ""
                        
                        if st.session_state.current_q >= len(QUESTIONS):
                            st.session_state.completed = True
                        
                        st.rerun()
            else:
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
                            
                            st.session_state.show_feedback = True
                            st.session_state.current_feedback = ai_analysis
                            st.rerun()
                    else:
                        st.warning("Please provide an answer before submitting.")
        
        else:  # Code Question Handling
            if 'dataset' in q:
                with st.expander("📊 View Dataset"):
                    st.dataframe(DATASETS[q['dataset']], use_container_width=True)
            
            code_key = f"code_{q['id']}"
            if code_key not in st.session_state:
                st.session_state[code_key] = q.get('starter_code', '')
            
            code = st.text_area("Your Code:", value=st.session_state[code_key], height=200, key=f"code_editor_{q['id']}")
            st.session_state[code_key] = code
            
            # Show feedback if already submitted
            if st.session_state.show_feedback and st.session_state.current_feedback:
                ai_analysis = st.session_state.current_feedback
                result = ai_analysis.get('result')
                expected = ai_analysis.get('expected')
                is_correct = ai_analysis.get('is_correct')
                
                st.markdown("---")
                st.markdown("### 📤 Output")
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Your Result:**")
                    st.code(str(result), language="python")
                with col2:
                    st.markdown("**Expected:**")
                    st.code(str(expected), language="python")
                
                st.markdown(f"**Execution Time:** {ai_analysis.get('execution_time', 0):.4f}s")
                
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
                
                st.markdown("---")
                
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    if st.button("➡️ Next Question", type="primary", use_container_width=True, key=f"next_code_{q['id']}"):
                        st.session_state.current_q += 1
                        st.session_state.show_feedback = False
                        st.session_state.current_feedback = None
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

