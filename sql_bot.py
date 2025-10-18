"""
Data Science Practice Bot (Streamlit)

Features:
- 5 questions total: 3 theory (text answers) and 2 coding (Python code to run against sample DataFrame)
- Advanced but different UI (glassmorphism / pastel gradient cards)
- Safe-ish execution sandbox for coding questions: students must set `result` variable in their code.
- Automatic evaluation for coding questions (numeric tolerance / exact match for strings)
- Simple keyword-based checks for theory answers (can be replaced with an LLM call if you add API keys)
- Instructions included for integrating an LLM (optional)
NOTE: Executing arbitrary code submitted by users is inherently risky. This example restricts the execution namespace
to a small set of safe modules (pandas/numpy/random). Use with caution and only in trusted environments.
"""

import streamlit as st
import pandas as pd
import numpy as np
import textwrap
import re
from typing import Tuple, Any

st.set_page_config(page_title="Data Science Practice Bot", layout="wide")

# --------------------------
# CSS / UI (different style than SQL bot)
# --------------------------
ui_css = """
<style>
/* Pastel glass cards, centered layout */
body, .stApp {
    background: linear-gradient(135deg, #f6f9ff 0%, #fff7fb 50%, #fdfde7 100%);
    color: #0b2545;
    font-family: Inter, system-ui, -apple-system, "Helvetica Neue", Arial;
}

/* Card */
.card {
    background: rgba(255, 255, 255, 0.75);
    border-radius: 14px;
    box-shadow: 0 8px 30px rgba(50, 50, 93, 0.08);
    padding: 18px;
    margin-bottom: 18px;
    border: 1px solid rgba(255,255,255,0.6);
}

/* Hero */
.hero-title {
    font-size: 40px;
    font-weight: 700;
    margin-bottom: 6px;
    color: #0b2545;
}
.hero-sub {
    color: #345;
    margin-bottom: 14px;
    opacity: 0.9;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(90deg, #7bdff6 0%, #b39cff 100%) !important;
    color: #06203a !important;
    font-weight: 600;
    padding: 12px 20px;
    border-radius: 12px;
    border: none;
}

/* Code box styling (a little darker) */
[data-testid="stCodeBlock"] pre {
    background: #0f1724 !important;
    color: #e6f2ff !important;
    border-radius: 8px !important;
}

/* Small helpers */
.kv {
    color: #0b2545;
    font-weight: 600;
}
.progress-pill {
    display:inline-block;
    padding:6px 12px;
    background:linear-gradient(90deg,#e3f6ff,#f0e6ff);
    border-radius:999px;
    color:#06203a;
    font-weight:600;
}
</style>
"""
st.markdown(ui_css, unsafe_allow_html=True)

# --------------------------
# Sample datasets (small and deterministic)
# --------------------------
# A simple student study dataset useful for coding tasks
students_df = pd.DataFrame({
    "student_id": range(1, 11),
    "hours_studied": [2, 3, 5, 1, 4, 6, 2, 8, 7, 3],
    "score": [50, 55, 80, 40, 65, 90, 52, 98, 85, 58],
    "passed": [0, 0, 1, 0, 1, 1, 0, 1, 1, 0]
})

# A simple synthetic dataset for a second coding question
measurements_df = pd.DataFrame({
    "id": range(1, 9),
    "temp_c": [20.1, 21.3, 19.8, 23.0, 22.2, 20.5, 21.0, 19.9],
    "humidity": [30, 35, 28, 40, 38, 32, 33, 29]
})

DATASETS = {
    "students": students_df,
    "measurements": measurements_df
}

# --------------------------
# Questions: 3 theory, 2 coding
# --------------------------
QUESTIONS = [
    {
        "id": 1,
        "type": "theory",
        "title": "Bias-Variance Tradeoff",
        "prompt": "Explain the bias-variance tradeoff in supervised machine learning. Include what high bias and high variance mean, and one way to reduce each.",
        "keywords": ["bias", "variance", "overfitting", "underfitting", "reduce bias", "reduce variance"]
    },
    {
        "id": 2,
        "type": "theory",
        "title": "Cross-Validation",
        "prompt": "What is k-fold cross-validation and why is it useful? Briefly describe how it works and one advantage over a single train/test split.",
        "keywords": ["k-fold", "fold", "validation", "train", "test", "average", "variance"]
    },
    {
        "id": 3,
        "type": "theory",
        "title": "Feature Scaling",
        "prompt": "Why is feature scaling (e.g., standardization or min-max scaling) important before certain models? Give one example of a model that benefits from scaling.",
        "keywords": ["scaling", "standardization", "min-max", "normalization", "gradient descent", "svm", "k-nearest", "distance"]
    },
    {
        "id": 4,
        "type": "code",
        "title": "Correlation Task",
        "prompt": textwrap.dedent("""\
            Using the `students` DataFrame provided as `df`, compute the Pearson correlation
            between `hours_studied` and `score`. Set your final numeric answer in a variable named `result`.
            Round the value to 3 decimal places (e.g., 0.123).
            Example:
                # your code...
                result = round(df['hours_studied'].corr(df['score']), 3)
            """),
        "dataset": "students",
        "validator": "numeric_tol",  # built-in validator name
    },
    {
        "id": 5,
        "type": "code",
        "title": "Train/Test Mean Score",
        "prompt": textwrap.dedent("""\
            Using the `students` DataFrame as `df`, split it into train and test sets using a 70/30 split.
            Use random seed = 42 so the split is deterministic. Compute the mean `score` on the test set
            and assign it to `result` rounded to 3 decimal places.
            Hint: you can use numpy or sample with frac and random_state.
            Example:
                test = df.sample(frac=0.3, random_state=42)
                result = round(test['score'].mean(), 3)
            """),
        "dataset": "students",
        "validator": "numeric_tol"
    }
]

# --------------------------
# Helpers: evaluation and safe execution
# --------------------------
def simple_theory_check(answer_text: str, keywords: list) -> Tuple[bool, str]:
    """
    Very simple keyword-based heuristic to determine if a theory answer is likely complete.
    Returns (is_correct, feedback_message).
    """
    if not answer_text or not answer_text.strip():
        return False, "No answer provided. Try explaining the concept in your own words."

    text = answer_text.lower()
    hits = [kw for kw in keywords if kw in text]
    score = len(hits) / max(1, len(keywords))

    if score >= 0.6:
        feedback = f"Good! Your answer touched on several key points ({', '.join(hits)}). Expand examples for full credit."
        return True, feedback
    elif score >= 0.3:
        feedback = f"Partial: you mentioned {', '.join(hits)}. Try to include more core concepts to make it complete."
        return False, feedback
    else:
        return False, "Your answer missed key concepts. Try to include definitions and at least one example or mitigation."

def run_student_code(user_code: str, dataframe: pd.DataFrame) -> Tuple[bool, Any, str]:
    """
    Execute student code in a restricted namespace.
    The student must assign the final answer to a variable called `result`.
    Returns (success_flag, result_value_or_error_message, stdout/traceback).
    """
    # Prepare a restricted globals namespace
    allowed_globals = {
        "__builtins__": {
            "abs": abs, "min": min, "max": max, "round": round, "len": len,
            "range": range, "sum": sum
        },
        "pd": pd,
        "np": np,
    }

    # Local namespace where student's result will be stored
    local_vars = {"df": dataframe.copy()}

    # Execute code (wrapped) and capture exceptions
    try:
        # Only allow students to use `df`, `pd`, `np`
        exec(user_code, allowed_globals, local_vars)
        if "result" not in local_vars:
            return False, None, "Please assign your final answer to a variable named `result`."
        return True, local_vars["result"], ""
    except Exception as e:
        return False, None, f"Error while executing your code: {e}"

def validator_numeric_tol(student_value: Any, expected_value: Any, tol=1e-3) -> Tuple[bool, str]:
    try:
        s = float(student_value)
        e = float(expected_value)
        if abs(s - e) <= tol:
            return True, f"Matches expected value within tolerance ({tol}). Your result: {s}"
        else:
            return False, f"Result differs. Expected ~{e}, found {s} (difference {abs(s-e):.4f})."
    except Exception as ex:
        return False, f"Could not convert values to numeric for comparison: {ex}"

# Precompute expected results for coding questions (reference solutions)
def compute_reference_for_question(q):
    if q["id"] == 4:
        df = DATASETS[q["dataset"]]
        val = round(df["hours_studied"].corr(df["score"]), 3)
        return val
    elif q["id"] == 5:
        df = DATASETS[q["dataset"]]
        test = df.sample(frac=0.3, random_state=42)
        val = round(test["score"].mean(), 3)
        return val
    return None

REFERENCE_RESULTS = {q["id"]: compute_reference_for_question(q) for q in QUESTIONS if q["type"] == "code"}

# --------------------------
# Session state init
# --------------------------
if "ds_user_answers" not in st.session_state:
    st.session_state.ds_user_answers = []
if "ds_current" not in st.session_state:
    st.session_state.ds_current = 0
if "ds_started" not in st.session_state:
    st.session_state.ds_started = False
if "ds_completed" not in st.session_state:
    st.session_state.ds_completed = False

# --------------------------
# App UI flow
# --------------------------
def show_home():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div style="display:flex; justify-content:space-between; align-items:center;">', unsafe_allow_html=True)
    st.markdown('<div><div class="hero-title">Data Science Practice Bot</div><div class="hero-sub">3 theory + 2 coding questions · Friendly mentor feedback · Beautiful UI</div></div>', unsafe_allow_html=True)
    st.markdown('<div style="text-align:right;"><span class="progress-pill">Beginner → Advance</span></div>', unsafe_allow_html=True)
    st.markdown('</div>')
    st.markdown('<hr/>', unsafe_allow_html=True)
    st.markdown("""
    <div style="display:flex; gap:1rem; align-items:center;">
      <div style="flex:1">
        <h4 style="margin:0;">What you will do</h4>
        <ul>
          <li>Answer 3 short theoretical questions (text).</li>
          <li>Solve 2 Python coding tasks using the provided DataFrame `df`.</li>
          <li>For coding tasks: set your final answer inside a variable named <code>result</code>.</li>
        </ul>
      </div>
      <div style="width:300px;">
        <h4 style="margin-bottom:6px;">Datasets available</h4>
        <ul>
          <li><code>students</code> (study hours & scores)</li>
          <li><code>measurements</code> (temps & humidity)</li>
        </ul>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Data Science Practice"):
            st.session_state.ds_started = True
            st.session_state.ds_user_answers = []
            st.session_state.ds_current = 0
            st.session_state.ds_completed = False
            st.experimental_rerun()

def show_question(qidx: int):
    q = QUESTIONS[qidx]
    st.markdown(f'<div class="card">', unsafe_allow_html=True)
    st.markdown(f'<h3 style="margin-top:0;">Q{qidx+1}. {q["title"]}</h3>', unsafe_allow_html=True)
    st.markdown(f'<div style="color:#234;">{q["prompt"].replace("\\n", "<br/>")}</div>', unsafe_allow_html=True)

    # Show dataset preview if relevant
    if q.get("dataset"):
        ds_name = q["dataset"]
        if ds_name in DATASETS:
            st.markdown(f"**Dataset `{ds_name}` preview:**")
            st.dataframe(DATASETS[ds_name].head(8), use_container_width=True)

    # Input area
    if q["type"] == "theory":
        answer = st.text_area("Your explanation:", height=180, key=f"theory_{qidx}")
        if st.button("Submit Answer", key=f"submit_theory_{qidx}"):
            is_correct, feedback = simple_theory_check(answer, q["keywords"])
            st.session_state.ds_user_answers.append({
                "id": q["id"],
                "type": q["type"],
                "question": q["prompt"],
                "student_answer": answer,
                "is_correct": is_correct,
                "feedback": feedback
            })
            # Move to next
            if qidx + 1 < len(QUESTIONS):
                st.session_state.ds_current = qidx + 1
            else:
                st.session_state.ds_completed = True
            st.experimental_rerun()

    elif q["type"] == "code":
        # Provide a starter code template that student can edit
        starter = f"""# Use df (a pandas DataFrame) that is the dataset '{q['dataset']}'
# Your final answer must be assigned to a variable named `result`.
# Example:
# result = round(df['hours_studied'].corr(df['score']), 3)

"""
        answer_code = st.text_area("Write your Python code here (assign final value to variable `result`):",
                                   value=starter, height=260, key=f"code_{qidx}")

        cols = st.columns([1, 1, 1])
        with cols[0]:
            if st.button("Run & Submit", key=f"run_submit_{qidx}"):
                df = DATASETS[q["dataset"]]
                success, res, stderr = run_student_code(answer_code, df)
                if not success:
                    st.error(stderr)
                else:
                    # Validate against reference
                    expected = REFERENCE_RESULTS.get(q["id"])
                    if q.get("validator") == "numeric_tol":
                        ok, message = validator_numeric_tol(res, expected, tol=1e-3)
                    else:
                        ok = (res == expected)
                        message = f"Expected: {expected}, got: {res}"
                    st.session_state.ds_user_answers.append({
                        "id": q["id"],
                        "type": q["type"],
                        "question": q["prompt"],
                        "student_answer": answer_code,
                        "is_correct": ok,
                        "feedback": message,
                        "student_result": res,
                        "expected_result": expected
                    })
                    if qidx + 1 < len(QUESTIONS):
                        st.session_state.ds_current = qidx + 1
                    else:
                        st.session_state.ds_completed = True
                    st.experimental_rerun()

        with cols[1]:
            if st.button("Run (Preview only)", key=f"run_preview_{qidx}"):
                df = DATASETS[q["dataset"]]
                success, res, stderr = run_student_code(answer_code, df)
                if not success:
                    st.error(stderr)
                else:
                    st.success("Code executed. Current `result` value:")
                    st.code(repr(res))
        with cols[2]:
            if st.button("Show Reference Solution", key=f"ref_{qidx}"):
                # show reference solution - helpful for learning
                # generate a small reference snippet based on question id
                ref = ""
                if q["id"] == 4:
                    ref = "result = round(df['hours_studied'].corr(df['score']), 3)"
                elif q["id"] == 5:
                    ref = "test = df.sample(frac=0.3, random_state=42)\nresult = round(test['score'].mean(), 3)"
                st.code(ref, language="python")

    st.markdown('</div>', unsafe_allow_html=True)

def show_results():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<h2>🏁 Results & Feedback</h2>', unsafe_allow_html=True)
    total = len(st.session_state.ds_user_answers)
    correct = sum(1 for a in st.session_state.ds_user_answers if a.get("is_correct"))
    score_pct = (correct / total) * 100 if total else 0
    st.markdown(f"<div style='font-size:18px;'><span class='kv'>Score:</span> {correct}/{total} ({score_pct:.1f}%)</div>", unsafe_allow_html=True)
    st.markdown("<hr/>", unsafe_allow_html=True)

    for i, ans in enumerate(st.session_state.ds_user_answers, start=1):
        with st.expander(f"Q{i}: {ans['type'].upper()} — {'Correct' if ans['is_correct'] else 'Incorrect'}", expanded=False):
            st.markdown("**Your submission:**")
            if ans["type"] == "theory":
                st.write(ans["student_answer"] or "_No answer provided_")
            else:
                st.code(ans["student_answer"], language="python")
                st.markdown(f"**Your computed `result`:** `{ans.get('student_result', 'N/A')}`")
                st.markdown(f"**Expected (reference):** `{ans.get('expected_result', 'N/A')}`")
            st.markdown("**Feedback:**")
            st.write(ans["feedback"])
            st.markdown("---")
    st.markdown("</div>", unsafe_allow_html=True)

    # Offer retry
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🔁 Retry Quiz"):
            for k in ["ds_user_answers", "ds_current", "ds_started", "ds_completed"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.experimental_rerun()
    with col2:
        if st.button("🏠 Back to Home"):
            for k in ["ds_user_answers", "ds_current", "ds_started", "ds_completed"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.experimental_rerun()

# --------------------------
# Optional: LLM integration placeholder
# --------------------------
"""
If you want to replace the simple heuristic checks for theory answers with an LLM-based evaluation,
you can integrate an LLM (OpenAI, Gemini, etc.). For safety and privacy, do NOT hard-code API keys
in source code that gets committed. Instead read from environment variables or Streamlit secrets.

A possible workflow:
- Build a prompt that includes the question, the student's answer, and evaluation rubric.
- Send the prompt to the LLM and parse whether the answer is Correct/Incorrect and ask for feedback.
- Store feedback in st.session_state like we do above.

Example (pseudo):
def evaluate_with_llm(question, answer):
    prompt = f"..."
    llm_resp = call_your_llm(prompt)
    return parsed_result_bool, parsed_feedback
"""

# --------------------------
# Main render
# --------------------------
st.title("📚 Data Science Practice Bot")
st.markdown("<div style='margin-bottom:18px'>A focused 5-question practice: 3 theory + 2 code. Clear feedback, deterministic datasets.</div>", unsafe_allow_html=True)

if not st.session_state.ds_started:
    show_home()
else:
    if not st.session_state.ds_completed:
        current_index = st.session_state.ds_current
        show_question(current_index)
    else:
        show_results()
        
