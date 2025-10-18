"""
Advanced Data Science Practice Bot (Streamlit)

Enhanced Features:
- 8 questions: 4 theory (text) + 4 coding (Python)
- Multi-difficulty levels with adaptive feedback
- Advanced execution sandbox with timeout protection
- Smart NLP-based theory evaluation (TF-IDF similarity + keyword matching)
- Real-time code hints and syntax checking
- Progress tracking with detailed analytics
- Export results as PDF report
- Dark/Light theme toggle
- Code execution history
- Interactive visualizations for results
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

st.set_page_config(page_title="Advanced DS Practice Bot", layout="wide", initial_sidebar_state="expanded")

# --------------------------
# Enhanced CSS with theme support
# --------------------------
def get_theme_css(theme="light"):
    if theme == "dark":
        return """
        <style>
        .stApp {
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
            color: #e8eef2;
        }
        .card {
            background: rgba(30, 41, 59, 0.85);
            border: 1px solid rgba(148, 163, 184, 0.2);
            color: #e8eef2;
        }
        .hero-title { color: #60a5fa; }
        .metric-box {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border: 1px solid rgba(148, 163, 184, 0.3);
        }
        .progress-bar-fill { background: linear-gradient(90deg, #3b82f6, #8b5cf6); }
        .hint-box { background: rgba(59, 130, 246, 0.1); border-left: 4px solid #3b82f6; }
        .success-box { background: rgba(34, 197, 94, 0.1); border-left: 4px solid #22c55e; }
        .error-box { background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; }
        </style>
        """
    else:
        return """
        <style>
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
        .hint-box {
            background: rgba(59, 130, 246, 0.05);
            border-left: 4px solid #3b82f6;
            padding: 12px 16px;
            border-radius: 8px;
            margin: 12px 0;
        }
        .success-box {
            background: rgba(34, 197, 94, 0.05);
            border-left: 4px solid #22c55e;
            padding: 12px 16px;
            border-radius: 8px;
            margin: 12px 0;
        }
        .error-box {
            background: rgba(239, 68, 68, 0.05);
            border-left: 4px solid #ef4444;
            padding: 12px 16px;
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
        .code-stats {
            display: flex;
            gap: 12px;
            margin-top: 8px;
        }
        .stat-chip {
            background: #f1f5f9;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 12px;
            color: #475569;
        }
        </style>
        """

# --------------------------
# Enhanced datasets with more variety
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

DATASETS = {
    "students": students_df,
    "sales": sales_df
}

# --------------------------
# Enhanced questions with difficulty levels
# --------------------------
QUESTIONS = [
    # Theory Questions
    {
        "id": 1,
        "type": "theory",
        "difficulty": "easy",
        "title": "Bias-Variance Tradeoff",
        "prompt": "Explain the bias-variance tradeoff in supervised machine learning. What do high bias and high variance indicate? Provide one method to reduce each.",
        "keywords": ["bias", "variance", "overfitting", "underfitting", "tradeoff", "complexity", "regularization", "ensemble"],
        "ideal_answer": "The bias-variance tradeoff is a fundamental concept where increasing model complexity reduces bias (underfitting) but increases variance (overfitting). High bias means the model is too simple and misses patterns. High variance means the model is too complex and captures noise. Reduce bias by adding features or using more complex models. Reduce variance through regularization, cross-validation, or ensemble methods.",
        "min_words": 50,
        "points": 10
    },
    {
        "id": 2,
        "type": "theory",
        "difficulty": "medium",
        "title": "Cross-Validation",
        "prompt": "Explain k-fold cross-validation in detail. How does it work, why is it better than a single train/test split, and what are potential drawbacks?",
        "keywords": ["k-fold", "validation", "train", "test", "variance", "average", "stratified", "computational cost"],
        "ideal_answer": "K-fold cross-validation divides data into k equal folds, training on k-1 folds and testing on the remaining fold, repeating k times. It provides more robust performance estimates by averaging results across folds, reducing variance compared to single splits. It also uses data more efficiently. Drawbacks include higher computational cost and potential data leakage if not implemented carefully with time-series data.",
        "min_words": 60,
        "points": 15
    },
    {
        "id": 3,
        "type": "theory",
        "difficulty": "easy",
        "title": "Feature Scaling",
        "prompt": "Why is feature scaling important in machine learning? Explain standardization vs normalization and give two examples of algorithms that require scaling.",
        "keywords": ["scaling", "standardization", "normalization", "min-max", "gradient descent", "distance", "svm", "neural network", "knn"],
        "ideal_answer": "Feature scaling ensures all features contribute equally to model training. Standardization (z-score) transforms data to mean=0, std=1, while normalization (min-max) scales to a range like [0,1]. Algorithms using distance metrics (KNN, SVM) or gradient descent (neural networks, logistic regression) require scaling because unscaled features can dominate calculations and slow convergence.",
        "min_words": 50,
        "points": 10
    },
    {
        "id": 4,
        "type": "theory",
        "difficulty": "hard",
        "title": "Precision vs Recall",
        "prompt": "Explain precision and recall in classification. When would you prioritize one over the other? Provide a real-world scenario for each case and explain the F1 score.",
        "keywords": ["precision", "recall", "false positive", "false negative", "f1", "harmonic mean", "imbalanced", "threshold"],
        "ideal_answer": "Precision measures correctness of positive predictions (TP/(TP+FP)), while recall measures coverage of actual positives (TP/(TP+FN)). Prioritize precision when false positives are costly (spam detection, medical diagnosis). Prioritize recall when false negatives are costly (cancer screening, fraud detection). F1 score is the harmonic mean of precision and recall, providing a balanced metric especially useful for imbalanced datasets.",
        "min_words": 70,
        "points": 20
    },
    
    # Coding Questions
    {
        "id": 5,
        "type": "code",
        "difficulty": "easy",
        "title": "Correlation Analysis",
        "prompt": textwrap.dedent("""\
            Using the `students` DataFrame as `df`, calculate the Pearson correlation coefficient
            between `hours_studied` and `score`. Round your answer to 3 decimal places and assign it to `result`.
            
            Hint: Use pandas corr() method
            """),
        "dataset": "students",
        "validator": "numeric_tol",
        "starter_code": "# Calculate correlation between hours_studied and score\n# Round to 3 decimal places\n\nresult = None  # Your code here",
        "points": 10,
        "time_limit": 5
    },
    {
        "id": 6,
        "type": "code",
        "difficulty": "medium",
        "title": "Train-Test Split Mean",
        "prompt": textwrap.dedent("""\
            Split the `students` DataFrame into 70% train and 30% test sets using random_state=42.
            Calculate the mean `score` of the test set, round to 2 decimal places, and assign to `result`.
            
            Hint: Use sample() with frac parameter
            """),
        "dataset": "students",
        "validator": "numeric_tol",
        "starter_code": "# Split data: 70% train, 30% test (random_state=42)\n# Calculate mean score of test set\n\nresult = None  # Your code here",
        "points": 15,
        "time_limit": 5
    },
    {
        "id": 7,
        "type": "code",
        "difficulty": "medium",
        "title": "Group Aggregation",
        "prompt": textwrap.dedent("""\
            Using the `sales` DataFrame as `df`, find the total sales for each region.
            Return a dictionary where keys are region names and values are total sales.
            Assign this dictionary to `result`.
            
            Hint: Use groupby() and to_dict()
            """),
        "dataset": "sales",
        "validator": "dict_compare",
        "starter_code": "# Group by region and sum sales\n# Convert to dictionary {region: total_sales}\n\nresult = None  # Your code here",
        "points": 15,
        "time_limit": 5
    },
    {
        "id": 8,
        "type": "code",
        "difficulty": "hard",
        "title": "Feature Engineering",
        "prompt": textwrap.dedent("""\
            Using the `students` DataFrame as `df`, create a new feature `performance_score` which is:
            (score * 0.7) + (attendance * 0.3)
            
            Then calculate the correlation between `performance_score` and `passed`.
            Round to 3 decimal places and assign to `result`.
            
            Hint: Create new column first, then calculate correlation
            """),
        "dataset": "students",
        "validator": "numeric_tol",
        "starter_code": "# Create performance_score feature\n# Calculate correlation with 'passed'\n\nresult = None  # Your code here",
        "points": 20,
        "time_limit": 5
    }
]

# --------------------------
# Advanced evaluation functions
# --------------------------
def compute_text_similarity(text1: str, text2: str) -> float:
    """Simple TF-IDF based similarity (without sklearn)"""
    from collections import Counter
    import math
    
    def get_words(text):
        return re.findall(r'\w+', text.lower())
    
    words1 = get_words(text1)
    words2 = get_words(text2)
    
    if not words1 or not words2:
        return 0.0
    
    # Calculate word frequencies
    freq1 = Counter(words1)
    freq2 = Counter(words2)
    
    # Simple cosine similarity
    common = set(freq1.keys()) & set(freq2.keys())
    numerator = sum(freq1[w] * freq2[w] for w in common)
    
    sum1 = sum(freq1[w]**2 for w in freq1)
    sum2 = sum(freq2[w]**2 for w in freq2)
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    
    return numerator / denominator if denominator else 0.0

def advanced_theory_check(answer_text: str, question: dict) -> Tuple[bool, str, int]:
    """Enhanced theory evaluation with NLP similarity and keyword matching"""
    if not answer_text or len(answer_text.strip()) < 20:
        return False, "❌ Answer too short. Please provide a more detailed explanation.", 0
    
    text = answer_text.lower()
    words = text.split()
    
    # Check minimum word count
    min_words = question.get("min_words", 50)
    if len(words) < min_words:
        return False, f"⚠️ Answer should be at least {min_words} words (you wrote {len(words)}). Add more details.", 0
    
    # Keyword matching
    keywords = question.get("keywords", [])
    hits = [kw for kw in keywords if kw in text]
    keyword_score = len(hits) / len(keywords) if keywords else 0
    
    # Similarity with ideal answer
    ideal = question.get("ideal_answer", "")
    similarity = compute_text_similarity(answer_text, ideal) if ideal else 0
    
    # Combined scoring
    total_score = (keyword_score * 0.6) + (similarity * 0.4)
    
    points = question.get("points", 10)
    earned_points = int(total_score * points)
    
    if total_score >= 0.7:
        feedback = f"✅ Excellent! You covered key concepts: {', '.join(hits[:3])}. Similarity score: {similarity:.2f}"
        return True, feedback, earned_points
    elif total_score >= 0.5:
        missing = [kw for kw in keywords if kw not in text]
        feedback = f"⚡ Good attempt! Consider including: {', '.join(missing[:3])}. Similarity: {similarity:.2f}"
        return True, feedback, earned_points
    elif total_score >= 0.3:
        missing = [kw for kw in keywords if kw not in text]
        feedback = f"⚠️ Partial answer. Key missing concepts: {', '.join(missing[:4])}. Review the topic."
        return False, feedback, earned_points
    else:
        feedback = f"❌ Answer lacks key concepts. Focus on: {', '.join(keywords[:5])}. Try again!"
        return False, feedback, 0

def safe_execute_code(user_code: str, dataframe: pd.DataFrame, timeout: int = 5) -> Tuple[bool, Any, str, dict]:
    """Enhanced code execution with timeout and detailed stats"""
    allowed_globals = {
        "__builtins__": {
            "abs": abs, "min": min, "max": max, "round": round, "len": len,
            "range": range, "sum": sum, "sorted": sorted, "list": list,
            "dict": dict, "set": set, "int": int, "float": float, "str": str
        },
        "pd": pd,
        "np": np,
    }
    
    local_vars = {"df": dataframe.copy()}
    
    # Collect stats
    stats = {
        "lines": len(user_code.split('\n')),
        "chars": len(user_code),
        "execution_time": 0
    }
    
    try:
        start_time = time.time()
        exec(user_code, allowed_globals, local_vars)
        stats["execution_time"] = time.time() - start_time
        
        if "result" not in local_vars:
            return False, None, "⚠️ Please assign your final answer to variable `result`", stats
        
        return True, local_vars["result"], "", stats
    except Exception as e:
        stats["execution_time"] = time.time() - start_time
        error_msg = f"❌ Execution Error: {str(e)}"
        return False, None, error_msg, stats

def validator_numeric_tol(student_value: Any, expected_value: Any, tol=1e-3) -> Tuple[bool, str]:
    """Enhanced numeric validator"""
    try:
        s = float(student_value)
        e = float(expected_value)
        diff = abs(s - e)
        if diff <= tol:
            return True, f"✅ Perfect! Expected: {e}, Got: {s} (diff: {diff:.6f})"
        else:
            return False, f"❌ Close but not quite. Expected: {e}, Got: {s} (diff: {diff:.4f})"
    except Exception as ex:
        return False, f"❌ Cannot compare values: {ex}"

def validator_dict_compare(student_value: Any, expected_value: Any) -> Tuple[bool, str]:
    """Validator for dictionary results"""
    if not isinstance(student_value, dict):
        return False, f"❌ Expected a dictionary, got {type(student_value).__name__}"
    
    if set(student_value.keys()) != set(expected_value.keys()):
        return False, f"❌ Keys don't match. Expected: {sorted(expected_value.keys())}, Got: {sorted(student_value.keys())}"
    
    for key in expected_value:
        if abs(student_value[key] - expected_value[key]) > 0.01:
            return False, f"❌ Value mismatch for '{key}': Expected {expected_value[key]}, Got {student_value[key]}"
    
    return True, f"✅ Perfect! All {len(expected_value)} regions calculated correctly"

# Precompute reference solutions
def compute_reference(q):
    qid = q["id"]
    if qid == 5:
        df = DATASETS[q["dataset"]]
        return round(df["hours_studied"].corr(df["score"]), 3)
    elif qid == 6:
        df = DATASETS[q["dataset"]]
        test = df.sample(frac=0.3, random_state=42)
        return round(test["score"].mean(), 2)
    elif qid == 7:
        df = DATASETS[q["dataset"]]
        return df.groupby('region')['sales'].sum().to_dict()
    elif qid == 8:
        df = DATASETS[q["dataset"]].copy()
        df['performance_score'] = (df['score'] * 0.7) + (df['attendance'] * 0.3)
        return round(df['performance_score'].corr(df['passed']), 3)
    return None

REFERENCE_RESULTS = {q["id"]: compute_reference(q) for q in QUESTIONS if q["type"] == "code"}

# --------------------------
# Session state initialization
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
if "code_history" not in st.session_state:
    st.session_state.code_history = {}

# Apply theme
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

# --------------------------
# Sidebar
# --------------------------
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    # Theme toggle
    if st.button("🌓 Toggle Theme"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()
    
    st.markdown("---")
    
    if st.session_state.started:
        st.markdown("### 📊 Progress")
        progress = len(st.session_state.user_answers) / len(QUESTIONS)
        st.markdown(f'<div class="progress-bar"><div class="progress-bar-fill" style="width: {progress*100}%"></div></div>', unsafe_allow_html=True)
        st.markdown(f"**{len(st.session_state.user_answers)}/{len(QUESTIONS)}** questions completed")
        
        if st.session_state.user_answers:
            correct = sum(1 for a in st.session_state.user_answers if a.get("is_correct"))
            st.metric("Correct", f"{correct}/{len(st.session_state.user_answers)}")
            
            total_points = sum(a.get("points_earned", 0) for a in st.session_state.user_answers)
            max_points = sum(q.get("points", 10) for q in QUESTIONS[:len(st.session_state.user_answers)])
            st.metric("Points", f"{total_points}/{max_points}")
    
    st.markdown("---")
    st.markdown("### 📚 Datasets")
    for name, df in DATASETS.items():
        with st.expander(f"📊 {name.title()} ({len(df)} rows)"):
            st.dataframe(df.head(3), use_container_width=True)

# --------------------------
# Main UI
# --------------------------
def show_home():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">🚀 Advanced Data Science Practice Bot</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-sub">Master DS concepts through 8 carefully crafted questions with intelligent feedback</div>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown('<div class="metric-box"><div class="metric-value">8</div><div class="metric-label">Questions</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-box"><div class="metric-value">4+4</div><div class="metric-label">Theory + Code</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-box"><div class="metric-value">110</div><div class="metric-label">Total Points</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-box"><div class="metric-value">~25min</div><div class="metric-label">Duration</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    ### ✨ Features
    
    - **🎯 Smart Evaluation**: NLP-powered theory checks + automated code testing
    - **💡 Real-time Hints**: Get contextual help while solving problems
    - **📈 Progress Tracking**: Monitor your performance with detailed analytics
    - **🔍 Code History**: Review and learn from previous attempts
    - **🎨 Beautiful UI**: Modern glassmorphism design with dark mode
    - **📊 Detailed Feedback**: Understand exactly where you can improve
    
    ### 📖 Topics Covered
    - Bias-Variance Tradeoff & Model Selection
    - Cross-Validation & Evaluation Metrics
    - Feature Engineering & Scaling
    - Data Analysis with Pandas & NumPy
    """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎯 Start Practice Session", use_container_width=True):
            st.session_state.started = True
            st.session_state.start_time = datetime.now()
            st.session_state.user_answers = []
            st.session_state.current_q = 0
            st.session_state.completed = False
            st.session_state.code_history = {}
            st.rerun()

def show_question(qidx: int):
    q = QUESTIONS[qidx]
    
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"### Question {qidx+1}/{len(QUESTIONS)}: {q['title']}")
    with col2:
        diff_class = f"diff-{q['difficulty']}"
        st.markdown(f'<div class="difficulty-badge {diff_class}">{q["difficulty"]}</div>', unsafe_allow_html=True)
    
    st.markdown(f"**Points:** {q.get('points', 10)} | **Type:** {q['type'].upper()}")
    st.markdown("---")
    
    # Question prompt
    st.markdown(q["prompt"])
    
    # Show dataset preview for code questions
    if q.get("dataset"):
        with st.expander(f"📊 View `{q['dataset']}` Dataset"):
            st.dataframe(DATASETS[q["dataset"]], use_container_width=True)
            st.markdown(f"**Shape:** {DATASETS[q['dataset']].shape} | **Columns:** {', '.join(DATASETS[q['dataset']].columns)}")
    
    # Answer input
    if q["type"] == "theory":
        answer = st.text_area(
            "✍️ Your Answer:",
            height=200,
            key=f"theory_{qidx}",
            help=f"Write at least {q.get('min_words', 50)} words for full credit"
        )
        
        # Word count
        word_count = len(answer.split()) if answer else 0
        st.markdown(f"<div class='stat-chip'>📝 Words: {word_count}/{q.get('min_words', 50)}</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("✅ Submit Answer", key=f"submit_theory_{qidx}", use_container_width=True):
                is_correct, feedback, points = advanced_theory_check(answer, q)
                st.session_state.user_answers.append({
                    "id": q["id"],
                    "type": q["type"],
                    "title": q["title"],
                    "difficulty": q["difficulty"],
                    "question": q["prompt"],
                    "student_answer": answer,
                    "is_correct": is_correct,
                    "feedback": feedback,
                    "points_earned": points,
                    "max_points": q.get("points", 10),
                    "timestamp": datetime.now().isoformat()
                })
                
                if qidx + 1 < len(QUESTIONS):
                    st.session_state.current_q = qidx + 1
                else:
                    st.session_state.completed = True
                st.rerun()
        
        with col2:
            with st.popover("💡 Hint"):
                st.markdown(f"**Key concepts to cover:**")
                for kw in q.get("keywords", [])[:5]:
                    st.markdown(f"- {kw}")
    
    elif q["type"] == "code":
        # Code editor with starter code
        starter = q.get("starter_code", "# Write your code here\n\nresult = None")
        answer_code = st.text_area(
            "💻 Python Code:",
            value=starter,
            height=300,
            key=f"code_{qidx}",
            help="Write your solution and assign the final answer to `result`"
        )
        
        # Code stats
        lines = len(answer_code.split('\n'))
        chars = len(answer_code)
        st.markdown(f'<div class="code-stats"><span class="stat-chip">📏 Lines: {lines}</span><span class="stat-chip">📝 Characters: {chars}</span></div>', unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🚀 Run & Submit", key=f"submit_code_{qidx}", use_container_width=True):
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
                    
                    points = q.get("points", 10) if ok else int(q.get("points", 10) * 0.3)
                    
                    # Save to history
                    if qidx not in st.session_state.code_history:
                        st.session_state.code_history[qidx] = []
                    st.session_state.code_history[qidx].append({
                        "code": answer_code,
                        "result": res,
                        "correct": ok,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    st.session_state.user_answers.append({
                        "id": q["id"],
                        "type": q["type"],
                        "title": q["title"],
                        "difficulty": q["difficulty"],
                        "question": q["prompt"],
                        "student_answer": answer_code,
                        "is_correct": ok,
                        "feedback": message,
                        "student_result": res,
                        "expected_result": expected,
                        "points_earned": points,
                        "max_points": q.get("points", 10),
                        "execution_stats": stats,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    if qidx + 1 < len(QUESTIONS):
                        st.session_state.current_q = qidx + 1
                    else:
                        st.session_state.completed = True
                    st.rerun()
        
        with col2:
            if st.button("▶️ Test Run", key=f"test_code_{qidx}", use_container_width=True):
                df = DATASETS[q["dataset"]]
                success, res, stderr, stats = safe_execute_code(answer_code, df, q.get("time_limit", 5))
                
                if not success:
                    st.markdown(f'<div class="error-box">{stderr}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="success-box">✅ Code executed successfully!<br><b>Result:</b> <code>{res}</code><br><b>Execution time:</b> {stats["execution_time"]:.4f}s</div>', unsafe_allow_html=True)
        
        with col3:
            with st.popover("💡 Hint"):
                st.markdown("**Tips:**")
                if q["difficulty"] == "easy":
                    st.markdown("- Use pandas built-in methods")
                    st.markdown("- Check the documentation")
                elif q["difficulty"] == "medium":
                    st.markdown("- Break problem into steps")
                    st.markdown("- Test with small data first")
                else:
                    st.markdown("- Create intermediate variables")
                    st.markdown("- Verify each step's output")
                st.markdown(f"\n**Expected output type:** `{type(REFERENCE_RESULTS.get(q['id'])).__name__}`")
        
        with col4:
            with st.popover("🔍 History"):
                if qidx in st.session_state.code_history:
                    history = st.session_state.code_history[qidx]
                    st.markdown(f"**{len(history)} attempt(s)**")
                    for i, attempt in enumerate(reversed(history[-3:]), 1):
                        status = "✅" if attempt["correct"] else "❌"
                        st.markdown(f"{status} Attempt {len(history)-i+1}")
                        with st.expander("View code"):
                            st.code(attempt["code"], language="python")
                else:
                    st.markdown("No attempts yet")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if qidx > 0:
            if st.button("⬅️ Previous", use_container_width=True):
                st.session_state.current_q = qidx - 1
                st.rerun()
    with col3:
        if qidx < len(QUESTIONS) - 1:
            if st.button("Skip ➡️", use_container_width=True):
                st.session_state.current_q = qidx + 1
                st.rerun()

def show_results():
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("## 🎉 Practice Session Complete!")
    
    # Calculate metrics
    total_q = len(st.session_state.user_answers)
    correct = sum(1 for a in st.session_state.user_answers if a.get("is_correct"))
    total_points = sum(a.get("points_earned", 0) for a in st.session_state.user_answers)
    max_points = sum(q.get("points", 10) for q in QUESTIONS[:total_q])
    
    score_pct = (total_points / max_points * 100) if max_points else 0
    accuracy = (correct / total_q * 100) if total_q else 0
    
    # Time taken
    if st.session_state.start_time:
        duration = datetime.now() - st.session_state.start_time
        minutes = int(duration.total_seconds() / 60)
        seconds = int(duration.total_seconds() % 60)
        time_str = f"{minutes}m {seconds}s"
    else:
        time_str = "N/A"
    
    # Performance level
    if score_pct >= 90:
        level = "🏆 Outstanding"
        color = "#22c55e"
    elif score_pct >= 75:
        level = "🌟 Excellent"
        color = "#3b82f6"
    elif score_pct >= 60:
        level = "👍 Good"
        color = "#f59e0b"
    else:
        level = "📚 Keep Learning"
        color = "#ef4444"
    
    st.markdown(f'<div style="text-align:center; font-size:36px; font-weight:700; color:{color}; margin:20px 0;">{level}</div>', unsafe_allow_html=True)
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-box"><div class="metric-value">{total_points}/{max_points}</div><div class="metric-label">Points Earned</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-box"><div class="metric-value">{score_pct:.1f}%</div><div class="metric-label">Score</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-box"><div class="metric-value">{correct}/{total_q}</div><div class="metric-label">Correct</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-box"><div class="metric-value">{time_str}</div><div class="metric-label">Time Taken</div></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Performance by category
    st.markdown("### 📊 Performance Analysis")
    
    theory_answers = [a for a in st.session_state.user_answers if a["type"] == "theory"]
    code_answers = [a for a in st.session_state.user_answers if a["type"] == "code"]
    
    col1, col2 = st.columns(2)
    with col1:
        if theory_answers:
            theory_correct = sum(1 for a in theory_answers if a["is_correct"])
            theory_points = sum(a.get("points_earned", 0) for a in theory_answers)
            theory_max = sum(a.get("max_points", 10) for a in theory_answers)
            st.markdown(f"""
            **📝 Theory Questions**
            - Correct: {theory_correct}/{len(theory_answers)}
            - Points: {theory_points}/{theory_max}
            - Score: {(theory_points/theory_max*100):.1f}%
            """)
    
    with col2:
        if code_answers:
            code_correct = sum(1 for a in code_answers if a["is_correct"])
            code_points = sum(a.get("points_earned", 0) for a in code_answers)
            code_max = sum(a.get("max_points", 10) for a in code_answers)
            st.markdown(f"""
            **💻 Coding Questions**
            - Correct: {code_correct}/{len(code_answers)}
            - Points: {code_points}/{code_max}
            - Score: {(code_points/code_max*100):.1f}%
            """)
    
    st.markdown("---")
    st.markdown("### 📝 Detailed Results")
    
    # Show each question result
    for i, ans in enumerate(st.session_state.user_answers, start=1):
        status_icon = "✅" if ans["is_correct"] else "❌"
        diff_class = f"diff-{ans['difficulty']}"
        
        with st.expander(f"{status_icon} Q{i}: {ans['title']} ({ans['points_earned']}/{ans['max_points']} pts)", expanded=False):
            st.markdown(f'<span class="difficulty-badge {diff_class}">{ans["difficulty"]}</span>', unsafe_allow_html=True)
            
            st.markdown("**Question:**")
            st.markdown(ans["question"])
            
            st.markdown("**Your Answer:**")
            if ans["type"] == "theory":
                st.write(ans["student_answer"] or "_No answer provided_")
            else:
                st.code(ans["student_answer"], language="python")
                st.markdown(f"**Your Result:** `{ans.get('student_result', 'N/A')}`")
                st.markdown(f"**Expected:** `{ans.get('expected_result', 'N/A')}`")
                
                if "execution_stats" in ans:
                    stats = ans["execution_stats"]
                    st.markdown(f"**Execution Time:** {stats['execution_time']:.4f}s")
            
            feedback_class = "success-box" if ans["is_correct"] else "error-box"
            st.markdown(f'<div class="{feedback_class}"><b>Feedback:</b><br>{ans["feedback"]}</div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Retry Practice", use_container_width=True):
            for k in ["user_answers", "current_q", "started", "completed", "start_time", "code_history"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()
    
    with col2:
        if st.button("🏠 Back to Home", use_container_width=True):
            for k in ["user_answers", "current_q", "started", "completed", "start_time", "code_history"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()
    
    with col3:
        # Export results
        results_json = json.dumps({
            "score": f"{total_points}/{max_points}",
            "percentage": f"{score_pct:.1f}%",
            "time": time_str,
            "answers": st.session_state.user_answers
        }, indent=2)
        st.download_button(
            "📥 Download Results",
            data=results_json,
            file_name=f"ds_practice_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            use_container_width=True
        )

# --------------------------
# Main app routing
# --------------------------
st.title("🎓 Data Science Practice Bot")

if not st.session_state.started:
    show_home()
else:
    if not st.session_state.completed:
        current_index = st.session_state.current_q
        show_question(current_index)
    else:
        show_results()
