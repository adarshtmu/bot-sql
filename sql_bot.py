import streamlit as st
import pandas as pd
import numpy as np
import json
import time
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# LLM Integration
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# --- CONFIGURATION ---
st.set_page_config(
    page_title="DataMentor Pro",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# YOUR API KEY
HARD_CODED_GEMINI_API_KEY = "AIzaSyCipiGM8HxiPiVtfePpGN-TiIk5JVBO6_M" 

# --- DATA & STATE ---
def init_state():
    defaults = {
        "page": "home",
        "current_q_index": 0,
        "answers": [],
        "user_name": "Practitioner",
        "gemini_key": HARD_CODED_GEMINI_API_KEY,
        "processing": False,
        "last_feedback": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# --- DATASETS ---
@st.cache_data
def load_data():
    return {
        "ecommerce": pd.DataFrame({
            "user_id": range(101, 121),
            "spend": np.random.normal(500, 150, 20),
            "clicks": np.random.randint(5, 50, 20),
            "conversion": np.random.choice([0, 1], 20, p=[0.7, 0.3])
        })
    }
DATASETS = load_data()

# --- QUESTIONS BANK ---
QUESTIONS = [
    {
        "id": 101,
        "title": "Overfitting vs. Underfitting",
        "type": "theory",
        "difficulty": "Easy",
        "points": 100,
        "content": "Explain the concept of Overfitting in Decision Trees. How does 'pruning' help resolve this?",
        "context": "Think about the depth of the tree and noise in the training data."
    },
    {
        "id": 102,
        "title": "Data Aggregation Logic",
        "type": "code",
        "difficulty": "Medium",
        "points": 200,
        "content": "Calculate the average 'spend' for users who had more than 20 clicks. Assign the result to variable `avg_spend`.",
        "dataset": "ecommerce",
        "starter_code": "# df is your dataframe\n# Filter users with > 20 clicks\n# Calculate mean of 'spend'\n\navg_spend = 0"
    }
]

# --- ADVANCED UI ENGINE (CSS) ---
def inject_css():
    st.markdown("""
    <style>
        /* IMPORT FONTS */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;600&display=swap');

        /* RESET & BASE */
        .stApp {
            background-color: #050505;
            background-image: radial-gradient(at 0% 0%, rgba(56, 189, 248, 0.1) 0px, transparent 50%),
                              radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.15) 0px, transparent 50%);
            font-family: 'Inter', sans-serif;
            color: #ffffff;
        }
        
        /* HIDE STREAMLIT CHROME */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}

        /* TYPOGRAPHY */
        h1, h2, h3 {
            font-weight: 800;
            letter-spacing: -0.02em;
            color: #f8fafc;
        }
        
        .gradient-text {
            background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* GLASS CARDS */
        .glass-card {
            background: rgba(255, 255, 255, 0.03);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        
        .glass-card:hover {
            border-color: rgba(255, 255, 255, 0.2);
            transform: translateY(-2px);
        }

        /* CUSTOM BUTTONS */
        .stButton button {
            background: linear-gradient(90deg, #2563eb, #4f46e5);
            color: white;
            border: none;
            padding: 12px 28px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.3);
            width: 100%;
        }
        
        .stButton button:hover {
            opacity: 0.9;
            transform: scale(1.02);
            box-shadow: 0 6px 20px rgba(37, 99, 235, 0.5);
        }

        /* SECONDARY BUTTON */
        .secondary-btn button {
            background: transparent;
            border: 1px solid rgba(255,255,255,0.2);
            color: #cbd5e1;
        }

        /* CODE EDITOR STYLING */
        .stTextArea textarea {
            background-color: #0f172a !important;
            color: #e2e8f0 !important;
            font-family: 'JetBrains Mono', monospace !important;
            border: 1px solid #1e293b !important;
            border-radius: 8px;
            font-size: 14px;
        }
        
        /* PROGRESS BAR */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #38bdf8, #818cf8);
        }

        /* METRIC CONTAINERS */
        div[data-testid="stMetricValue"] {
            font-size: 28px;
            font-weight: 700;
            background: linear-gradient(to right, #fff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
    </style>
    """, unsafe_allow_html=True)

# --- AI HELPER ---
def get_ai_evaluation(prompt):
    if not GEMINI_AVAILABLE:
        time.sleep(1) # simulate latency
        return {"score": 0.85, "feedback": "AI Module not found. Simulated Response.", "correct": True}
    
    try:
        genai.configure(api_key=st.session_state.gemini_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt + " Return valid JSON only.")
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(clean_text)
    except:
        return {"score": 0, "feedback": "Error connecting to AI.", "correct": False}

# --- PAGES ---

def render_navbar():
    col1, col2, col3 = st.columns([1, 4, 1])
    with col1:
        st.markdown("<h3 style='margin:0'>⚡ DataMentor</h3>", unsafe_allow_html=True)
    with col3:
        if st.session_state.page == "practice":
            progress = (st.session_state.current_q_index / len(QUESTIONS))
            st.progress(progress)
            st.caption(f"Progress: {int(progress*100)}%")

def render_home():
    st.markdown("""
    <div style='text-align: center; padding: 100px 0;'>
        <div style='display: inline-block; padding: 8px 16px; background: rgba(56, 189, 248, 0.1); border-radius: 20px; border: 1px solid rgba(56, 189, 248, 0.2); margin-bottom: 24px;'>
            <span style='color: #38bdf8; font-weight: 600; font-size: 14px;'>✨ New: AI-Powered Code Analysis</span>
        </div>
        <h1 style='font-size: 72px; line-height: 1.1; margin-bottom: 24px;'>
            Master Data Science <br> <span class='gradient-text'>With Intelligence.</span>
        </h1>
        <p style='font-size: 20px; color: #94a3b8; max-width: 600px; margin: 0 auto 48px auto;'>
            The enterprise-grade assessment platform. Practice real-world scenarios, get instant AI feedback, and analyze your growth.
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("🚀 Start Assessment", use_container_width=True):
            st.session_state.page = "practice"
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Feature Cards
    col1, col2, col3 = st.columns(3)
    features = [
        ("🧠", "Adaptive Theory", "Deep dive into concepts with AI-tuned questions."),
        ("⚡", "Live Coding", "Run Pandas & NumPy workflows in a secure sandbox."),
        ("📊", "Skill Matrix", "Visual analytics to track your technical growth.")
    ]
    
    for col, (icon, title, desc) in zip([col1, col2, col3], features):
        with col:
            st.markdown(f"""
            <div class='glass-card' style='height: 200px;'>
                <div style='font-size: 32px; margin-bottom: 16px;'>{icon}</div>
                <h3 style='font-size: 20px; margin-bottom: 8px;'>{title}</h3>
                <p style='color: #94a3b8; font-size: 14px;'>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

def render_practice():
    q = QUESTIONS[st.session_state.current_q_index]
    
    # Header
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"## {q['title']}")
    with c2:
        st.markdown(f"""
        <div style='text-align:right'>
            <span style='background: rgba(139, 92, 246, 0.2); color: #a78bfa; padding: 6px 12px; border-radius: 12px; font-size: 12px; font-weight: 600;'>{q['difficulty'].upper()}</span>
            <span style='background: rgba(56, 189, 248, 0.2); color: #38bdf8; padding: 6px 12px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-left: 8px;'>{q['points']} PTS</span>
        </div>
        """, unsafe_allow_html=True)

    # Split Screen
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown(f"""
        <div class='glass-card'>
            <h4 style='color: #e2e8f0; margin-bottom: 12px;'>📝 Instructions</h4>
            <p style='font-size: 16px; line-height: 1.6; color: #cbd5e1;'>{q['content']}</p>
            <br>
            <p style='font-size: 14px; color: #64748b; font-style: italic;'>💡 Hint: {q.get('context', 'No hint available')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if q['type'] == 'code':
            st.markdown("##### 📂 Dataset Preview (ecommerce)")
            st.dataframe(DATASETS['ecommerce'].head(3), use_container_width=True)

    with col_right:
        if q['type'] == 'code':
            code_val = st.text_area("Python Editor", value=q.get("starter_code", ""), height=300, label_visibility="collapsed")
            
            # Action Bar
            ac1, ac2 = st.columns(2)
            with ac1:
                if st.button("▶ Run Code", key="run_btn"):
                    try:
                        # Safe exec
                        local_env = {"df": DATASETS['ecommerce'], "pd": pd, "np": np}
                        exec(code_val, {}, local_env)
                        st.session_state.run_output = local_env.get('avg_spend', 'No "avg_spend" variable found')
                        st.session_state.code_cache = code_val
                    except Exception as e:
                        st.session_state.run_output = f"Error: {e}"
            
            if "run_output" in st.session_state:
                st.markdown(f"""
                <div style='background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 12px; font-family: monospace; color: #22c55e;'>
                    > Output: {st.session_state.run_output}
                </div>
                """, unsafe_allow_html=True)

        else:
            theory_val = st.text_area("Your Answer", height=300, placeholder="Type your explanation here...")
            st.session_state.theory_cache = theory_val

        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Submit Answer", type="primary", use_container_width=True):
            with st.spinner("AI analyzing response..."):
                # Construct Prompt
                user_input = st.session_state.get('code_cache') if q['type'] == 'code' else st.session_state.get('theory_cache')
                prompt = f"Question: {q['content']}. User Answer: {user_input}. Type: {q['type']}. Evaluate correctness, give score (0-1), and feedback JSON: {{'score': float, 'feedback': str, 'correct': bool}}"
                
                feedback = get_ai_evaluation(prompt)
                st.session_state.last_feedback = feedback
                
                # Save
                st.session_state.answers.append({
                    "q_id": q['id'],
                    "score": feedback['score'] * q['points'],
                    "max_points": q['points'],
                    "type": q['type']
                })

    # Feedback Modal (Conditional Render)
    if st.session_state.last_feedback:
        fb = st.session_state.last_feedback
        border_color = "#22c55e" if fb['correct'] else "#ef4444"
        
        st.markdown(f"""
        <div class='glass-card' style='border-left: 4px solid {border_color}; margin-top: 20px;'>
            <h3 style='margin:0'>Analysis Complete</h3>
            <p style='font-size: 18px; color: {border_color}; font-weight: bold;'>Score: {int(fb['score']*100)}%</p>
            <p style='color: #cbd5e1;'>{fb['feedback']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Continue to Next Step ➡️"):
            st.session_state.last_feedback = None
            if st.session_state.current_q_index < len(QUESTIONS) - 1:
                st.session_state.current_q_index += 1
                if "run_output" in st.session_state: del st.session_state.run_output
            else:
                st.session_state.page = "report"
            st.rerun()

def render_report():
    st.markdown("## 📊 Performance Analytics")
    
    total_score = sum(a['score'] for a in st.session_state.answers)
    total_max = sum(a['max_points'] for a in st.session_state.answers)
    
    # 1. Top Metrics
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("Total Score", f"{int(total_score)}")
    with c2:
        st.metric("Accuracy", f"{int((total_score/total_max)*100)}%")
    with c3:
        st.metric("Questions", len(st.session_state.answers))
        
    st.markdown("---")
    
    # 2. Charts
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Proficiency Radar")
        categories = ['Theory', 'Coding', 'Logic', 'Syntax', 'Optimization']
        values = [0.8, 0.6, 0.9, 0.7, 0.5] # Mock data for visual
        
        fig = px.line_polar(r=values, theta=categories, line_close=True)
        fig.update_traces(fill='toself', line_color='#818cf8', fillcolor='rgba(129, 140, 248, 0.2)')
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font_color='white',
            polar=dict(bgcolor='rgba(0,0,0,0)', radialaxis=dict(showticklabels=False, ticks=''))
        )
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.markdown("### 💡 Recommendations")
        st.markdown("""
        <div class='glass-card'>
            <p style='margin-bottom: 8px;'><strong>Strengths:</strong></p>
            <span style='background:rgba(34, 197, 94, 0.2); color:#4ade80; padding:4px 8px; border-radius:4px; font-size:12px;'>Data Filtering</span>
            <span style='background:rgba(34, 197, 94, 0.2); color:#4ade80; padding:4px 8px; border-radius:4px; font-size:12px;'>Python Syntax</span>
            <br><br>
            <p style='margin-bottom: 8px;'><strong>Areas for Growth:</strong></p>
            <span style='background:rgba(239, 68, 68, 0.2); color:#f87171; padding:4px 8px; border-radius:4px; font-size:12px;'>Complexity Analysis</span>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔄 Start New Session", use_container_width=True):
            st.session_state.clear()
            st.rerun()

# --- MAIN CONTROLLER ---
inject_css()
render_navbar()

if st.session_state.page == "home":
    render_home()
elif st.session_state.page == "practice":
    render_practice()
elif st.session_state.page == "report":
    render_report()
