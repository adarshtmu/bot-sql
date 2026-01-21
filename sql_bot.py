import streamlit as st
import pandas as pd
import numpy as np
import json
import time
import plotly.express as px
import plotly.graph_objects as go

# LLM Integration
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# --- CONFIGURATION ---
st.set_page_config(
    page_title="DataMentor Enterprise",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API KEY (Replace with your actual key)
HARD_CODED_GEMINI_API_KEY = "AIzaSyCipiGM8HxiPiVtfePpGN-TiIk5JVBO6_M"

# --- DATASETS ---
@st.cache_data
def load_data():
    # Dataset 1: E-commerce
    ecommerce = pd.DataFrame({
        "user_id": range(101, 121),
        "spend": [500, 150, 300, 450, 600, 120, 800, 320, 110, 90, 550, 620, 410, 200, 300, 400, 700, 150, 250, 900],
        "clicks": [25, 10, 15, 22, 35, 8, 45, 18, 5, 4, 30, 32, 21, 12, 16, 20, 38, 9, 14, 50],
        "category": ['Electronics', 'Fashion', 'Home', 'Electronics', 'Fashion', 'Home', 'Electronics', 'Fashion', 'Home', 'Electronics', 'Fashion', 'Home', 'Electronics', 'Fashion', 'Home', 'Electronics', 'Fashion', 'Home', 'Electronics', 'Fashion']
    })
    
    # Dataset 2: Housing
    housing = pd.DataFrame({
        "sqft": [1500, 2000, 1200, 1800, 2500, 1100, 3000, 1600, 2100, 1400],
        "price": [300, 450, 250, 380, 550, 220, 700, 320, 460, 290],
        "bedrooms": [3, 4, 2, 3, 4, 2, 5, 3, 4, 3]
    })
    return {"ecommerce": ecommerce, "housing": housing}

DATASETS = load_data()

# --- 8-QUESTION CURRICULUM ---
QUESTIONS = [
    {
        "id": 1,
        "title": "Bias-Variance Tradeoff",
        "type": "theory",
        "difficulty": "Easy",
        "points": 100,
        "content": "Explain the Bias-Variance Tradeoff. What happens to bias and variance as model complexity increases?",
        "context": "",
        "hint": "Think about Underfitting (High Bias) vs Overfitting (High Variance)."
    },
    {
        "id": 2,
        "title": "Filter High Spenders",
        "type": "code",
        "difficulty": "Easy",
        "points": 100,
        "content": "Using the `ecommerce` dataset, filter for rows where 'spend' is greater than 400. Assign the result to `high_rollers`.",
        "dataset": "ecommerce",
        "starter_code": "# Filter rows where spend > 400\n\nhigh_rollers = df[...]"
    },
    {
        "id": 3,
        "title": "Precision vs Recall",
        "type": "theory",
        "difficulty": "Medium",
        "points": 150,
        "content": "In a cancer detection model, which metric is more critical to maximize: Precision or Recall? Explain why.",
        "context": "",
        "hint": "Recall = True Positives / (True Positives + False Negatives). Is a False Negative dangerous here?"
    },
    {
        "id": 4,
        "title": "Group Aggregation",
        "type": "code",
        "difficulty": "Medium",
        "points": 150,
        "content": "Calculate the average 'clicks' per 'category' in the `ecommerce` dataset. Assign the resulting Series to `cat_clicks`.",
        "dataset": "ecommerce",
        "starter_code": "# Group by category and find mean of clicks\n\ncat_clicks = ..."
    },
    {
        "id": 5,
        "title": "K-Means Elbow Method",
        "type": "theory",
        "difficulty": "Medium",
        "points": 150,
        "content": "Describe the 'Elbow Method' in K-Means clustering. What does the x-axis and y-axis represent in the elbow plot?",
        "context": "",
        "hint": "We are looking at Inertia (WCSS) vs Number of Clusters (k)."
    },
    {
        "id": 6,
        "title": "Feature Engineering",
        "type": "code",
        "difficulty": "Hard",
        "points": 200,
        "content": "Create a new column 'price_per_sqft' in the `housing` dataset (price / sqft). Return the correlation between 'bedrooms' and this new column.",
        "dataset": "housing",
        "starter_code": "# Create 'price_per_sqft'\n# Calculate corr with 'bedrooms'\n\nresult = ..."
    },
    {
        "id": 7,
        "title": "Handling Imbalanced Data",
        "type": "theory",
        "difficulty": "Hard",
        "points": 200,
        "content": "Your dataset has 99% Class A and 1% Class B. Naming 2 techniques to handle this imbalance during training.",
        "context": "",
        "hint": "Think about resampling techniques (Up/Down) or algorithmic changes."
    },
    {
        "id": 8,
        "title": "Missing Data Imputation",
        "type": "code",
        "difficulty": "Hard",
        "points": 200,
        "content": "Assume the 'spend' column has missing values. Write code to fill NaNs with the median of the column.",
        "dataset": "ecommerce",
        "starter_code": "# Fill NA in 'spend' with median\n\ndf['spend'] = ..."
    }
]

# --- STATE MANAGEMENT ---
def init_state():
    if "page" not in st.session_state: st.session_state.page = "home"
    if "current_q_index" not in st.session_state: st.session_state.current_q_index = 0
    if "answers" not in st.session_state: st.session_state.answers = []
    if "gemini_key" not in st.session_state: st.session_state.gemini_key = HARD_CODED_GEMINI_API_KEY
    if "last_feedback" not in st.session_state: st.session_state.last_feedback = None

init_state()

# --- CSS STYLING ENGINE ---
def inject_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=Fira+Code:wght@400;600&display=swap');
        
        /* APP CONTAINER */
        .stApp {
            background-color: #020617;
            background-image: 
                radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.15) 0px, transparent 50%),
                radial-gradient(at 100% 100%, rgba(168, 85, 247, 0.15) 0px, transparent 50%);
            font-family: 'Inter', sans-serif;
        }

        /* SIDEBAR */
        section[data-testid="stSidebar"] {
            background-color: #0f172a;
            border-right: 1px solid rgba(255,255,255,0.05);
        }

        /* GLASS CARD */
        .glass-card {
            background: rgba(30, 41, 59, 0.4);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        }
        
        /* CODE EDITOR */
        .stTextArea textarea {
            background-color: #020617 !important;
            color: #e2e8f0 !important;
            font-family: 'Fira Code', monospace !important;
            border: 1px solid #334155 !important;
        }

        /* BUTTONS */
        .stButton button {
            background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
            color: white;
            border: none;
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s;
        }
        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(79, 70, 229, 0.4);
        }

        /* TYPOGRAPHY */
        h1, h2, h3 { color: #f8fafc; font-weight: 800; }
        p, li { color: #94a3b8; line-height: 1.6; }
        
        /* PROGRESS INDICATORS */
        .step-indicator {
            padding: 8px 12px;
            border-radius: 6px;
            margin-bottom: 8px;
            font-size: 13px;
            cursor: default;
        }
        .step-active { background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
        .step-done { background: rgba(34, 197, 94, 0.1); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.2); }
        .step-pending { background: rgba(255, 255, 255, 0.03); color: #64748b; }
    </style>
    """, unsafe_allow_html=True)

# --- AI ENGINE ---
def get_ai_evaluation(prompt):
    if not GEMINI_AVAILABLE:
        time.sleep(1.5)
        return {"score": 0.9, "feedback": "Simulation: Excellent answer. You covered key points.", "correct": True}
    
    try:
        genai.configure(api_key=st.session_state.gemini_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt + " Return strict JSON: {'score': float, 'feedback': str, 'correct': bool}")
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except:
        return {"score": 0, "feedback": "AI Connection Error.", "correct": False}

# --- COMPONENTS ---

def render_sidebar():
    with st.sidebar:
        st.markdown("### 🧬 DataMentor")
        st.markdown("---")
        
        if st.session_state.page == "practice":
            st.markdown("#### 🗺️ Challenge Map")
            
            for idx, q in enumerate(QUESTIONS):
                status = "step-pending"
                icon = "○"
                
                # Logic to determine status
                if idx < st.session_state.current_q_index:
                    status = "step-done"
                    icon = "✔"
                elif idx == st.session_state.current_q_index:
                    status = "step-active"
                    icon = "▶"
                
                st.markdown(f"""
                <div class='step-indicator {status}'>
                    {icon} <b>Q{idx+1}:</b> {q['title']}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            current = st.session_state.current_q_index + 1
            total = len(QUESTIONS)
            st.caption(f"Progress: {int((current/total)*100)}%")
            st.progress(current/total)

def render_home():
    # Dynamic Stats
    total_q = len(QUESTIONS)
    total_pts = sum(q['points'] for q in QUESTIONS)
    est_time = f"{total_q * 3} mins"
    
    st.markdown("""
    <div style='text-align: center; padding: 60px 0;'>
        <h1 style='font-size: 64px; margin-bottom: 16px; background: linear-gradient(to right, #60a5fa, #c084fc); -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
            Data Science Bootcamp
        </h1>
        <p style='font-size: 20px; max-width: 700px; margin: 0 auto; color: #94a3b8;'>
            Advanced Enterprise Assessment Platform.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Metrics Grid
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Total Challenges", total_q)
    with c2: st.metric("Max Points", total_pts)
    with c3: st.metric("Est. Duration", est_time)
    with c4: st.metric("Difficulty", "Adaptive")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Syllabus Preview
    st.markdown("### 📚 Syllabus Preview")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Theory Modules")
        for q in QUESTIONS:
            if q['type'] == 'theory':
                st.markdown(f"**{q['title']}** - *{q['difficulty']}*")
                
    with col2:
        st.markdown("#### Coding Labs")
        for q in QUESTIONS:
            if q['type'] == 'code':
                st.markdown(f"**{q['title']}** - *{q['difficulty']}*")
    
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    
    _, btn_col, _ = st.columns([1,2,1])
    with btn_col:
        if st.button("🚀 Begin Assessment", use_container_width=True):
            st.session_state.page = "practice"
            st.rerun()

def render_practice():
    q = QUESTIONS[st.session_state.current_q_index]
    
    # Header
    st.markdown(f"""
    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;'>
        <h2 style='margin:0'>Question {q['id']}: {q['title']}</h2>
        <span style='background: #334155; padding: 6px 16px; border-radius: 20px; font-size: 14px; font-weight: bold; color: #e2e8f0;'>
            {q['points']} PTS
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Main Split
    left, right = st.columns([1, 1], gap="medium")
    
    with left:
        st.markdown(f"""
        <div class='glass-card'>
            <h4 style='color: #93c5fd; margin-bottom: 8px;'>📋 Problem Statement</h4>
            <p style='font-size: 1.1rem; color: #f1f5f9;'>{q['content']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Context Image Trigger
        if "context" in q:
            st.markdown(f"**Visual Reference:** {q['context']}")
            
        if q['type'] == 'code':
            with st.expander(f"📂 Dataset Preview: {q['dataset']}", expanded=True):
                st.dataframe(DATASETS[q['dataset']].head(), use_container_width=True)
                st.caption(f"Rows: {len(DATASETS[q['dataset']])} | Columns: {list(DATASETS[q['dataset']].columns)}")
    
    with right:
        st.markdown("#### 🛠️ Workspace")
        
        if q['type'] == 'code':
            code = st.text_area("Python Editor", value=q['starter_code'], height=250, label_visibility="collapsed")
            
            if st.button("▶ Run Code"):
                try:
                    local_env = {"df": DATASETS[q['dataset']], "pd": pd, "np": np}
                    exec(code, {}, local_env)
                    # Try to find a variable result
                    output = "Code executed successfully."
                    for key, val in local_env.items():
                        if key not in ["df", "pd", "np", "__builtins__"]:
                            output = f"{key} = {val}"
                    st.success(f"Output: {output}")
                    st.session_state.temp_input = code
                except Exception as e:
                    st.error(f"Runtime Error: {e}")
            else:
                st.session_state.temp_input = code
                
        else:
            ans = st.text_area("Your Response", height=250, placeholder="Explain your reasoning...")
            st.session_state.temp_input = ans
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Submit & Verify", type="primary", use_container_width=True):
            with st.spinner("🤖 AI Analyst Evaluating..."):
                prompt = f"Question: {q['content']}. User Answer: {st.session_state.temp_input}. Type: {q['type']}. Strict Evaluation."
                feedback = get_ai_evaluation(prompt)
                st.session_state.last_feedback = feedback
                
                # Save Answer
                st.session_state.answers.append({
                    "id": q['id'],
                    "score": feedback['score'] * q['points'],
                    "max": q['points'],
                    "title": q['title'],
                    "type": q['type']
                })
                st.rerun()

    # Feedback Overlay
    if st.session_state.last_feedback:
        fb = st.session_state.last_feedback
        color = "#22c55e" if fb['correct'] else "#f59e0b"
        
        st.markdown(f"""
        <div class='glass-card' style='border: 1px solid {color}; box-shadow: 0 0 20px {color}40;'>
            <h3 style='color: {color}'>Evaluation Complete</h3>
            <p><b>Feedback:</b> {fb['feedback']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Next Challenge ➡️", type="primary"):
            st.session_state.last_feedback = None
            if st.session_state.current_q_index < len(QUESTIONS) - 1:
                st.session_state.current_q_index += 1
            else:
                st.session_state.page = "report"
            st.rerun()

def render_report():
    st.markdown("## 📊 Comprehensive Analytics Report")
    
    total_score = sum(a['score'] for a in st.session_state.answers)
    max_score = sum(a['max'] for a in st.session_state.answers)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown(f"""
        <div class='glass-card' style='text-align:center'>
            <h1 style='font-size: 4rem; color: #38bdf8;'>{int(total_score)}</h1>
            <p>Total Points Scored</p>
            <hr style='border-color: rgba(255,255,255,0.1)'>
            <h3>{int(total_score/max_score*100)}%</h3>
            <p>Proficiency Rating</p>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        # Performance by Category (Theory vs Code)
        theory_pts = sum(a['score'] for a in st.session_state.answers if a['type']=='theory')
        code_pts = sum(a['score'] for a in st.session_state.answers if a['type']=='code')
        
        data = pd.DataFrame({
            "Category": ["Theory Mastery", "Coding Skills"],
            "Score": [theory_pts, code_pts]
        })
        
        fig = px.bar(data, x="Score", y="Category", orientation='h', text="Score", color="Category", 
                     color_discrete_sequence=['#818cf8', '#34d399'])
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='white')
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📝 Detailed Question Breakdown")
    for ans in st.session_state.answers:
        with st.expander(f"{ans['title']} - {int(ans['score'])}/{ans['max']}"):
            st.write("Review complete. Specific feedback available in previous session steps.")

    if st.button("🔄 Restart Assessment"):
        st.session_state.clear()
        st.rerun()

# --- APP FLOW ---
inject_css()
render_sidebar()

if st.session_state.page == "home":
    render_home()
elif st.session_state.page == "practice":
    render_practice()
elif st.session_state.page == "report":
    render_report()
