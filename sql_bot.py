import os
import streamlit as st
import pandas as pd
import numpy as np
import json
import time
from typing import Tuple, Any, Dict, List
from datetime import datetime
import re
import ast

# --- LLM Integration ---
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

HARD_CODED_GEMINI_API_KEY = "AIzaSyCipiGM8HxiPiVtfePpGN-TiIk5JVBO6_M"

st.set_page_config(
    page_title="DataMentor AI - Practice Platform",
    page_icon="🎓",
    layout="wide"
)

# --- Session State ---
if "current_q" not in st.session_state:
    st.session_state.current_q = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = []
if "started" not in st.session_state:
    st.session_state.started = False
if "completed" not in st.session_state:
    st.session_state.completed = False
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "last_feedback" not in st.session_state:
    st.session_state.last_feedback = None

# --- Datasets ---
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
    {"id": 1, "type": "theory", "title": "Bias-Variance Tradeoff", "prompt": "Explain the bias-variance tradeoff in supervised learning.", "points": 10},
    {"id": 2, "type": "theory", "title": "Feature Scaling", "prompt": "Why is feature scaling important in algorithms like KNN?", "points": 10},
    {"id": 5, "type": "code", "title": "Correlation Analysis", "prompt": "Calculate the correlation between `hours_studied` and `score`. Assign to `result`.", "dataset": "students", "points": 10, "starter_code": "result = df['hours_studied'].corr(df['score'])"},
    {"id": 7, "type": "code", "title": "Group Aggregation", "prompt": "Find total sales for each region. Assign to `result`.", "dataset": "sales", "points": 15, "starter_code": "result = df.groupby('region')['sales'].sum().to_dict()"}
]

# --- Core Functions ---
def get_gemini_model():
    if GEMINI_AVAILABLE:
        genai.configure(api_key=HARD_CODED_GEMINI_API_KEY)
        return genai.GenerativeModel('gemini-1.5-flash')
    return None

ai_model = get_gemini_model()

def safe_execute_code(user_code, df):
    local_vars = {"df": df.copy()}
    try:
        exec(user_code, {"pd": pd, "np": np, "__builtins__": __builtins__}, local_vars)
        return True, local_vars.get("result"), ""
    except Exception as e:
        return False, None, str(e)

def get_ai_feedback(q, answer, model, is_code=False, code_result=None):
    if not model:
        return {"is_correct": True, "score": 0.5, "feedback": "AI Offline: Saved your answer."}
    
    prompt = f"Question: {q['prompt']}\nUser Answer: {answer}\n"
    if is_code:
        prompt += f"Execution Result: {code_result}\n"
    prompt += "Return valid JSON only: {'is_correct': bool, 'score': float, 'feedback': str}"
    
    try:
        response = model.generate_content(prompt)
        # Clean up JSON from markdown if necessary
        clean_text = re.search(r'\{.*\}', response.text, re.DOTALL).group()
        return json.loads(clean_text)
    except:
        return {"is_correct": True, "score": 0.0, "feedback": "Evaluation error, but your progress is saved."}

# --- UI Layout ---
if not st.session_state.started:
    st.title("DataMentor AI 🎓")
    if st.button("🚀 Start Practice Session"):
        st.session_state.started = True
        st.rerun()

elif st.session_state.completed:
    st.success("Practice Session Complete!")
    total_score = sum([a.get('score', 0) * 100 for a in st.session_state.user_answers])
    st.metric("Overall Performance", f"{total_score/len(QUESTIONS):.1f}%")
    if st.button("Restart Session"):
        st.session_state.clear()
        st.rerun()

else:
    q = QUESTIONS[st.session_state.current_q]
    
    # Progress Sidebar
    st.sidebar.write(f"Question {st.session_state.current_q + 1} of {len(QUESTIONS)}")
    st.sidebar.progress((st.session_state.current_q) / len(QUESTIONS))

    st.subheader(f"Q{st.session_state.current_q + 1}: {q['title']}")
    st.info(q['prompt'])

    # Input Area (Disabled after submission)
    if q['type'] == "theory":
        user_input = st.text_area("Your Answer:", height=150, disabled=st.session_state.submitted)
    else:
        user_input = st.text_area("Python Code:", value=q.get("starter_code", ""), height=200, disabled=st.session_state.submitted)

    # ACTION BUTTONS
    if not st.session_state.submitted:
        if st.button("Submit Answer", type="primary"):
            with st.spinner("AI Mentor is reviewing..."):
                if q['type'] == "theory":
                    feedback = get_ai_feedback(q, user_input, ai_model)
                else:
                    success, val, err = safe_execute_code(user_input, DATASETS[q['dataset']])
                    feedback = get_ai_feedback(q, user_input, ai_model, is_code=True, code_result=val if success else err)
                    feedback["code_output"] = val if success else f"Error: {err}"
                
                # Save state
                st.session_state.last_feedback = feedback
                st.session_state.user_answers.append(feedback)
                st.session_state.submitted = True
                st.rerun()
    
    # FEEDBACK & NEXT BUTTON (Only visible after clicking Submit)
    if st.session_state.submitted:
        fb = st.session_state.last_feedback
        st.markdown("---")
        st.markdown("#### AI Mentor Feedback")
        
        # Style based on correctness
        if fb.get('is_correct'):
            st.success(fb['feedback'])
        else:
            st.warning(fb['feedback'])
            
        if "code_output" in fb:
            st.code(f"Output: {fb['code_output']}")

        # Navigation
        if st.session_state.current_q < len(QUESTIONS) - 1:
            if st.button("Next Question ➡️"):
                st.session_state.current_q += 1
                st.session_state.submitted = False
                st.session_state.last_feedback = None
                st.rerun()
        else:
            if st.button("Finish & View Results"):
                st.session_state.completed = True
                st.rerun()
