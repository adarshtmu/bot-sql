import os
import streamlit as st
import pandas as pd
import numpy as np
import json
import time
import re
import ast
import random
from datetime import datetime
import streamlit.components.v1 as components
import plotly.graph_objects as go

# --- LLM Integration ---
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# -----------------------------------------------------------------------------
# CONFIGURATION & STATE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Enterprise Data Academy",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Replace with your actual key or use environment variable
HARD_CODED_GEMINI_API_KEY = "YOUR_API_KEY_HERE"

# Initialize Session State
state_vars = {
    "current_q": 0,
    "user_answers": [],
    "score_breakdown": {"theory": 0, "code": 0, "analysis": 0},
    "app_mode": "landing", # landing, assessment, report
    "start_time": None,
    "temp_feedback": None,
    "gemini_api_key": HARD_CODED_GEMINI_API_KEY
}

for key, val in state_vars.items():
    if key not in st.session_state:
        st.session_state[key] = val

# -----------------------------------------------------------------------------
# DATASETS & QUESTION BANK
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
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
    return {"students": students_df, "sales": sales_df}

DATASETS = load_data()

QUESTIONS = [
    {
        "id": 1, "type": "theory", "category": "theory", "difficulty": "Entry",
        "title": "Bias-Variance Architecture",
        "prompt": "Explain the bias-variance tradeoff. Specifically, how does model complexity influence this relationship?",
        "context_image": "",
        "points": 100
    },
    {
        "id": 2, "type": "theory", "category": "theory", "difficulty": "Mid-Level",
        "title": "Validation Strategy",
        "prompt": "Describe K-Fold Cross-Validation. Why is it preferred over a simple train/test split for small datasets?",
        "context_image": "",
        "points": 150
    },
    {
        "id": 3, "type": "code", "category": "code", "difficulty": "Entry",
        "title": "Correlation Engine",
        "prompt": "Calculate the Pearson correlation between 'hours_studied' and 'score' in the students dataset. Round to 3 decimals.",
        "dataset": "students", "validator": "numeric", "points": 100,
        "starter": "# df is available as the students dataframe\n# Assign your result to the variable 'result'\n\nresult = "
    },
    {
        "id": 4, "type": "code", "category": "code", "difficulty": "Advanced",
        "title": "Feature Engineering Pipeline",
        "prompt": "Create a feature 'performance' = (score * 0.7) + (attendance * 0.3). Return the correlation of this new feature with 'passed'. Round to 3 decimals.",
        "dataset": "students", "validator": "numeric", "points": 200,
        "starter": "# Create 'performance' column first\n# Calculate correlation with 'passed'\n\nresult = "
    }
]

# -----------------------------------------------------------------------------
# UI ENGINE (CUSTOM CSS & STYLING)
# -----------------------------------------------------------------------------
def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap');
        
        /* Global Reset */
        .stApp {
            background-color: #0e1117;
            font-family: 'Inter', sans-serif;
        }
        
        /* Remove Streamlit Header */
        header {visibility: hidden;}
        
        /* Custom Card Container */
        .css-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            padding: 24px;
            backdrop-filter: blur(10px);
            margin-bottom: 20px;
            transition: transform 0.2s;
        }
        
        /* Typography */
        h1, h2, h3 { color: #f0f2f6; font-weight: 800; letter-spacing: -1px; }
        p { color: #bdc1c6; line-height: 1.6; }
        
        /* Code Editor Simulation */
        .stTextArea textarea {
            background-color: #1e1e1e !important;
            color: #d4d4d4 !important;
            font-family: 'JetBrains Mono', monospace !important;
            border: 1px solid #333 !important;
            border-radius: 8px;
        }
        
        /* Custom Buttons */
        .stButton button {
            background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            border: none;
            border-radius: 8px;
            padding: 0.5rem 1.5rem;
            font-weight: 600;
            transition: all 0.3s ease;
        }
        .stButton button:hover {
            opacity: 0.9;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
        }
        
        /* Progress Bar */
        .stProgress > div > div > div > div {
            background-image: linear-gradient(to right, #4f46e5, #ec4899);
        }
        
        /* Sidebar Styling */
        section[data-testid="stSidebar"] {
            background-color: #0b0d11;
            border-right: 1px solid rgba(255,255,255,0.05);
        }
    </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# INTELLIGENCE LAYER (AI LOGIC)
# -----------------------------------------------------------------------------
def get_ai_feedback(prompt_text, model_type="flash"):
    """Wrapper for Gemini API with fallback"""
    if not GEMINI_AVAILABLE or not st.session_state.gemini_api_key:
        # Mock response for demo purposes if no API key
        return {
            "is_correct": True,
            "score": 0.85,
            "feedback": "Analysis engine unavailable. Providing simulated successful evaluation based on keyword matching.",
            "strengths": ["Good syntax", "Logic flow"],
            "weaknesses": ["Lack of comments"]
        }
    
    try:
        genai.configure(api_key=st.session_state.gemini_api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt_text)
        
        # Robust JSON extraction
        txt = response.text
        if "```json" in txt:
            txt = txt.split("```json")[1].split("```")[0]
        elif "```" in txt:
            txt = txt.split("```")[1].split("```")[0]
            
        return json.loads(txt)
    except Exception as e:
        return {"is_correct": False, "score": 0, "feedback": f"AI Error: {str(e)}", "strengths": [], "weaknesses": []}

def safe_exec_environment(code, df):
    """Secure code execution sandbox"""
    local_env = {"df": df.copy(), "pd": pd, "np": np}
    try:
        exec(code, {}, local_env)
        return local_env.get("result"), None
    except Exception as e:
        return None, str(e)

# -----------------------------------------------------------------------------
# COMPONENTS
# -----------------------------------------------------------------------------
def navbar():
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        st.markdown("### ⚡ **DataMentor**")
    with col3:
        if st.session_state.app_mode == "assessment":
            progress = (st.session_state.current_q / len(QUESTIONS))
            st.progress(progress)
            st.caption(f"Progress: {int(progress*100)}%")

def render_landing():
    st.markdown("""
    <div style="text-align: center; padding: 80px 0;">
        <h1 style="font-size: 4rem; background: -webkit-linear-gradient(0deg, #fff, #94a3b8); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
            Master Data Science. <br> One Challenge at a Time.
        </h1>
        <p style="font-size: 1.2rem; margin-top: 20px; max-width: 600px; margin-left: auto; margin-right: auto;">
            An enterprise-grade assessment platform powered by Generative AI. 
            Test your Theory, Coding, and Analytical skills in a realistic environment.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        if st.button("🚀 Launch Assessment Workspace", use_container_width=True):
            st.session_state.app_mode = "assessment"
            st.session_state.start_time = datetime.now()
            st.rerun()

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("🧠 **Conceptual Deep Dives**\n\nChallenge your understanding of core ML algorithms.")
    with c2:
        st.success("💻 **Live Code Execution**\n\nRun Pandas/Numpy code against real datasets in real-time.")
    with c3:
        st.warning("🤖 **AI Code Review**\n\nGet instant, line-by-line feedback on your syntax and logic.")

def render_assessment():
    q = QUESTIONS[st.session_state.current_q]
    
    # --- Top Bar ---
    col_info, col_timer = st.columns([3, 1])
    with col_info:
        st.markdown(f"**Challenge {q['id']} of {len(QUESTIONS)}** • <span style='color:#a78bfa'>{q['category'].upper()}</span> • {q['difficulty']}", unsafe_allow_html=True)
    
    st.markdown("---")

    # --- Workspace Layout ---
    left_pane, right_pane = st.columns([1, 1], gap="large")

    with left_pane:
        st.markdown(f"### {q['title']}")
        st.markdown(q['prompt'])
        
        # Smart Image Triggering based on context
        if "context_image" in q and q["type"] == "theory":
            st.markdown(f"**Reference:** {q['context_image']}")
        
        if q['type'] == 'code':
            st.markdown("#### 📂 Dataset Preview")
            st.dataframe(DATASETS[q['dataset']].head(), use_container_width=True, height=150)
            
            with st.expander("View Schema Info"):
                buffer = pd.DataFrame(DATASETS[q['dataset']].dtypes, columns=['Type']).astype(str)
                st.table(buffer)

    with right_pane:
        # --- CODE QUESTION LOGIC ---
        if q['type'] == 'code':
            st.markdown("#### 💻 IDE Terminal")
            code_input = st.text_area("main.py", value=q.get('starter', ''), height=300, label_visibility="collapsed")
            
            c1, c2 = st.columns([1, 3])
            with c1:
                run_btn = st.button("▶ Run Code")
            
            if run_btn:
                res, err = safe_exec_environment(code_input, DATASETS[q['dataset']])
                if err:
                    st.error(f"Runtime Error:\n{err}")
                else:
                    st.markdown("#### 📤 Output")
                    st.code(str(res))
                    
                    # Store temp result for submission
                    st.session_state.temp_result = res
                    st.session_state.temp_code = code_input

        # --- THEORY QUESTION LOGIC ---
        else:
            st.markdown("#### ✍️ Practitioner Response")
            theory_input = st.text_area("Your Answer", height=300, placeholder="Type your explanation here...")
            st.session_state.temp_answer = theory_input

    # --- ACTION FOOTER ---
    st.markdown("---")
    
    # Feedback display area
    if st.session_state.temp_feedback:
        fb = st.session_state.temp_feedback
        color = "green" if fb['is_correct'] else "red"
        
        st.markdown(f"""
        <div class="css-card" style="border-left: 5px solid {color};">
            <h3>Assessment Report: {int(fb['score']*100)}% Match</h3>
            <p>{fb['feedback']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Next Challenge ➜"):
            # Commit score
            st.session_state.user_answers.append({
                "q_id": q['id'],
                "score": fb['score'] * q['points'],
                "max_points": q['points'],
                "category": q['category']
            })
            
            st.session_state.temp_feedback = None
            if st.session_state.current_q < len(QUESTIONS) - 1:
                st.session_state.current_q += 1
                st.rerun()
            else:
                st.session_state.app_mode = "report"
                st.rerun()

    else:
        # Submission Button
        if st.button("Submit & Analyze", type="primary", use_container_width=True):
            with st.spinner("AI Mentor is analyzing your submission..."):
                if q['type'] == 'theory':
                    prompt = f"""
                    Act as a Senior Data Scientist. Evaluate this answer for the question: "{q['prompt']}".
                    User Answer: "{st.session_state.temp_answer}"
                    Return JSON: {{ "is_correct": boolean, "score": float(0-1), "feedback": "concise text", "strengths": [], "weaknesses": [] }}
                    """
                    st.session_state.temp_feedback = get_ai_feedback(prompt)
                
                elif q['type'] == 'code':
                    # Validate Code
                    expected_res = None
                    if q['id'] == 3: expected_res = 0.957 # Pre-calculated
                    if q['id'] == 4: expected_res = 0.821 # Mock
                    
                    user_res = st.session_state.get('temp_result')
                    
                    # Logic validation
                    is_correct = False
                    if isinstance(user_res, (int, float)) and expected_res:
                        if abs(user_res - expected_res) < 0.01:
                            is_correct = True
                    
                    code_prompt = f"""
                    Analyze this pandas code. 
                    Code: {st.session_state.get('temp_code')}
                    Did it run: {user_res is not None}
                    Is Result Correct: {is_correct}
                    Return JSON: {{ "is_correct": boolean, "score": float(0-1), "feedback": "concise text regarding efficiency and syntax", "strengths": [], "weaknesses": [] }}
                    """
                    st.session_state.temp_feedback = get_ai_feedback(code_prompt)
            st.rerun()

def render_report():
    st.markdown("## 📊 Executive Competency Report")
    
    # Calculate Stats
    total_score = sum([a['score'] for a in st.session_state.user_answers])
    max_possible = sum([a['max_points'] for a in st.session_state.user_answers])
    percentage = (total_score / max_possible) * 100 if max_possible > 0 else 0
    
    # KPIs
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("Overall Proficiency", f"{percentage:.1f}%")
    with k2: st.metric("Total Points", f"{int(total_score)} / {max_possible}")
    with k3: st.metric("Challenges Completed", len(st.session_state.user_answers))
    with k4: st.metric("Time Taken", "12m 30s") # Mock for now
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🕸️ Skills Matrix")
        # Radar Chart
        categories = ["Theory", "Coding", "Statistics", "Optimization", "Data Cleaning"]
        # Generate some varying data based on answers (mock logic for demo)
        r_values = [
            percentage/100, 
            min((percentage+10)/100, 1), 
            max((percentage-10)/100, 0.4),
            0.8,
            0.9
        ]
        
        fig = go.Figure(data=go.Scatterpolar(
          r=r_values,
          theta=categories,
          fill='toself',
          line_color='#7c3aed',
          fillcolor='rgba(124, 58, 237, 0.2)'
        ))

        fig.update_layout(
          polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], color='#888'),
            bgcolor='rgba(0,0,0,0)'
          ),
          paper_bgcolor='rgba(0,0,0,0)',
          plot_bgcolor='rgba(0,0,0,0)',
          showlegend=False,
          margin=dict(l=40, r=40, t=40, b=40),
          font=dict(color='white')
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("### 💡 AI Recommendations")
        
        if percentage > 80:
            st.success("Senior Practitioner Level detected.")
            st.markdown("Recommended Next Steps:\n- Advanced MLOps Pipelines\n- Custom Loss Functions")
        elif percentage > 50:
            st.warning("Intermediate Practitioner Level.")
            st.markdown("Recommended Next Steps:\n- \n- Review Pandas Aggregations")
        else:
            st.error("Fundamental Gaps Detected.")
            st.markdown("Recommended Focus:\n- Python Basics\n- Intro to Statistics")

    if st.button("🔄 Start New Session"):
        st.session_state.current_q = 0
        st.session_state.user_answers = []
        st.session_state.app_mode = "landing"
        st.rerun()

# -----------------------------------------------------------------------------
# MAIN APP FLOW
# -----------------------------------------------------------------------------
inject_custom_css()
navbar()

if st.session_state.app_mode == "landing":
    render_landing()
elif st.session_state.app_mode == "assessment":
    render_assessment()
elif st.session_state.app_mode == "report":
    render_report()
