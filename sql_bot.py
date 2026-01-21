# app.py
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

# ===============================
# PAGE CONFIG
# ===============================
st.set_page_config(
    page_title="DataMentor AI - Practice Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===============================
# SESSION STATE
# ===============================
DEFAULT_SESSION_STATE = {
    "theme": "light",
    "user_answers": [],
    "current_q": 0,
    "started": False,
    "completed": False,
    "final_report": None,

    # --- code question flow ---
    "code_ran": False,
    "code_submitted": False,
    "code_feedback": None
}

for k, v in DEFAULT_SESSION_STATE.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ===============================
# DATASETS
# ===============================
students_df = pd.DataFrame({
    "student_id": range(1, 21),
    "hours_studied": [2, 3, 5, 1, 4, 6, 2, 8, 7, 3, 5, 9, 4, 6, 3, 7, 8, 2, 5, 4],
    "score": [50, 55, 80, 40, 65, 90, 52, 98, 85, 58, 75, 95, 70, 88, 60, 92, 96, 48, 78, 68],
    "passed": [0, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1, 0, 1, 1],
    "attendance": [60, 70, 95, 50, 80, 98, 65, 100, 92, 72, 88, 97, 85, 90, 68, 94, 99, 55, 87, 82]
})

sales_df = pd.DataFrame({
    "product_id": range(1, 16),
    "product": ['A', 'B', 'C'] * 5,
    "sales": [100, 150, 200, 120, 180, 220, 110, 160, 210, 130, 170, 230, 125, 175, 215],
    "region": ['North','North','North','South','South','South','East','East','East','West','West','West','North','South','East'],
    "quarter": ['Q1']*6 + ['Q2']*6 + ['Q3']*3
})

DATASETS = {"students": students_df, "sales": sales_df}

# ===============================
# QUESTIONS
# ===============================
QUESTIONS = [
    {"id": 1,"type": "theory","difficulty": "easy","title": "Bias-Variance Tradeoff",
     "prompt": "Explain the bias-variance tradeoff in supervised machine learning.","points": 10},

    {"id": 2,"type": "theory","difficulty": "medium","title": "Cross-Validation",
     "prompt": "Explain k-fold cross-validation.","points": 15},

    {"id": 3,"type": "theory","difficulty": "easy","title": "Feature Scaling",
     "prompt": "Why is feature scaling important?","points": 10},

    {"id": 4,"type": "theory","difficulty": "hard","title": "Precision vs Recall",
     "prompt": "Explain precision, recall, and F1 score.","points": 20},

    {"id": 5,"type": "code","difficulty": "easy","title": "Correlation Analysis",
     "prompt": "Calculate Pearson correlation between hours_studied and score.",
     "dataset": "students","validator": "numeric_tol","points": 10,
     "starter_code": "result = None"},

    {"id": 6,"type": "code","difficulty": "medium","title": "Train-Test Split",
     "prompt": "Split 70/30 and compute mean score of test set.",
     "dataset": "students","validator": "numeric_tol","points": 15,
     "starter_code": "result = None"},
]

# ===============================
# HELPERS
# ===============================
def safe_execute_code(user_code: str, dataframe: pd.DataFrame):
    allowed_globals = {
        "__builtins__": {"abs": abs,"min": min,"max": max,"round": round,"len": len,"sum": sum},
        "pd": pd, "np": np,
    }
    local_vars = {"df": dataframe.copy()}
    try:
        exec(user_code, allowed_globals, local_vars)
        return True, local_vars.get("result"), ""
    except Exception as e:
        return False, None, str(e)

def validator_numeric_tol(a, b, tol=1e-3):
    try:
        return abs(float(a) - float(b)) <= tol
    except:
        return False

def compute_reference(q):
    if q["id"] == 5:
        return round(students_df["hours_studied"].corr(students_df["score"]), 3)
    if q["id"] == 6:
        return round(students_df.sample(frac=0.3, random_state=42)["score"].mean(), 2)

REFERENCE = {q["id"]: compute_reference(q) for q in QUESTIONS if q["type"] == "code"}

# ===============================
# START SCREEN
# ===============================
if not st.session_state.started:
    st.title("🎓 DataMentor AI")
    if st.button("🚀 Start Practice", type="primary"):
        st.session_state.started = True
        st.session_state.start_time = datetime.now()
        st.rerun()
    st.stop()

# ===============================
# COMPLETED
# ===============================
if st.session_state.completed:
    st.success("🎉 Practice Completed!")
    st.write("Thanks for practicing.")
    st.stop()

# ===============================
# ACTIVE QUESTION
# ===============================
q = QUESTIONS[st.session_state.current_q]

st.header(f"Question {q['id']}: {q['title']}")
st.write(q["prompt"])

# ===============================
# THEORY QUESTIONS
# ===============================
if q["type"] == "theory":
    key = f"answer_{q['id']}"
    answer = st.text_area("Your Answer", key=key)

    if st.button("Submit Answer", type="primary"):
        st.session_state.user_answers.append({
            "id": q["id"],
            "answer": answer,
            "type": "theory"
        })
        st.session_state.current_q += 1
        if st.session_state.current_q >= len(QUESTIONS):
            st.session_state.completed = True
        st.rerun()

# ===============================
# CODE QUESTIONS (FIXED FLOW)
# ===============================
else:
    code_key = f"code_{q['id']}"
    if code_key not in st.session_state:
        st.session_state[code_key] = q["starter_code"]

    st.text_area("Your Code", key=code_key, height=200)

    # ---- RUN CODE ----
    if st.button("▶️ Run Code"):
        ok, result, err = safe_execute_code(
            st.session_state[code_key],
            DATASETS[q["dataset"]]
        )

        if ok:
            expected = REFERENCE[q["id"]]
            is_correct = validator_numeric_tol(result, expected)

            st.session_state.code_feedback = {
                "result": result,
                "expected": expected,
                "is_correct": is_correct
            }
            st.session_state.code_ran = True
        else:
            st.error(err)

    # ---- SHOW FEEDBACK ----
    if st.session_state.code_ran and st.session_state.code_feedback:
        fb = st.session_state.code_feedback
        st.code(fb["result"], language="python")
        st.code(fb["expected"], language="python")

        st.success("Correct") if fb["is_correct"] else st.error("Incorrect")

        # ---- SUBMIT ANSWER ----
        if st.button("✅ Submit Answer"):
            st.session_state.user_answers.append({
                "id": q["id"],
                "code": st.session_state[code_key],
                "result": fb["result"],
                "correct": fb["is_correct"],
                "type": "code"
            })
            st.session_state.code_submitted = True

    # ---- NEXT QUESTION ----
    if st.session_state.code_submitted:
        if st.button("⏭️ Next Question", type="primary"):
            st.session_state.current_q += 1
            st.session_state.code_ran = False
            st.session_state.code_submitted = False
            st.session_state.code_feedback = None
            st.session_state[code_key] = ""

            if st.session_state.current_q >= len(QUESTIONS):
                st.session_state.completed = True
            st.rerun()
