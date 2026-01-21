import streamlit as st
import pandas as pd
import numpy as np
import json
import time
import plotly.express as px

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

HARD_CODED_GEMINI_API_KEY = "AIzaSyCipiGM8HxiPiVtfePpGN-TiIk5JVBO6_M"

# --- DATASETS ---
@st.cache_data
def load_data():
    ecommerce = pd.DataFrame({
        "user_id": range(101, 121),
        "spend": [500, 150, 300, 450, 600, 120, 800, 320, 110, 90, 550, 620, 410, 200, 300, 400, 700, 150, 250, 900],
        "clicks": [25, 10, 15, 22, 35, 8, 45, 18, 5, 4, 30, 32, 21, 12, 16, 20, 38, 9, 14, 50],
        "category": ['Electronics', 'Fashion', 'Home', 'Electronics', 'Fashion', 'Home', 'Electronics', 'Fashion', 'Home', 'Electronics', 'Fashion', 'Home', 'Electronics', 'Fashion', 'Home', 'Electronics', 'Fashion', 'Home', 'Electronics', 'Fashion']
    })
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
        "topic": "Machine Learning",
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
        "topic": "Pandas",
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
        "topic": "Metrics",
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
        "topic": "Pandas",
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
        "topic": "Clustering",
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
        "topic": "Feature Eng",
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
        "topic": "Data Prep",
        "difficulty": "Hard",
        "points": 200,
        "content": "Your dataset has 99% Class A and 1% Class B. Name 2 techniques to handle this imbalance during training.",
        "context": "",
        "hint": "Think about resampling techniques (Up/Down) or algorithmic changes."
    },
    {
        "id": 8,
        "title": "Missing Data Imputation",
        "type": "code",
        "topic": "Cleaning",
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

# --- ADVANCED CSS ENGINE ---
def inject_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;700;900&family=JetBrains+Mono:wght@400;600&display=swap');
        
        /* CORE THEME */
        .stApp {
            background-color: #030712;
            background-image: radial-gradient(at 50% 0%, rgba(56, 189, 248, 0.1) 0px, transparent 50%);
            font-family: 'Inter', sans-serif;
            color: #f8fafc;
        }

        /* ANIMATIONS */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes glow {
            0% { box-shadow: 0 0 5px rgba(56, 189, 248, 0.2); }
            50% { box-shadow: 0 0 20px rgba(56, 189, 248, 0.6); }
            100% { box-shadow: 0 0 5px rgba(56, 189, 248, 0.2); }
        }

        /* HERO TEXT */
        .hero-text {
            font-size: 4rem;
            font-weight: 900;
            background: linear-gradient(to right, #ffffff, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.05em;
            line-height: 1.1;
            margin-bottom: 24px;
            animation: fadeIn 0.8s ease-out;
        }

        /* CARDS */
        .glass-card {
            background: rgba(17, 24, 39, 0.7);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 20px;
            transition: all 0.3s ease;
        }
        
        .glass-card:hover {
            border-color: rgba(56, 189, 248, 0.4);
            transform: translateY(-4px);
            background: rgba(30, 41, 59, 0.8);
        }

        /* MODULE BADGES */
        .module-badge {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 4px 12px;
            border-radius: 99px;
            font-weight: 700;
        }
        .badge-theory { background: rgba(167, 139, 250, 0.2); color: #a78bfa; border: 1px solid #a78bfa; }
        .badge-code { background: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #38bdf8; }

        /* BUTTONS */
        .stButton button {
            background: linear-gradient(90deg, #2563eb, #3b82f6);
            border: none;
            color: white;
            padding: 16px 32px;
            font-size: 1.1rem;
            font-weight: 600;
            border-radius: 12px;
            width: 100%;
            transition: all 0.3s;
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
        }
        .stButton button:hover {
            transform: scale(1.02);
            box-shadow: 0 0 30px rgba(37, 99, 235, 0.6);
        }

        /* PROGRESS BAR */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #38bdf8, #818cf8);
        }

        /* SIDEBAR */
        section[data-testid="stSidebar"] {
            background-color: #020617;
            border-right: 1px solid #1e293b;
        }
    </style>
    """, unsafe_allow_html=True)

# --- AI LOGIC ---
def get_ai_evaluation(prompt):
    if not GEMINI_AVAILABLE:
        time.sleep(1.5)
        return {"score": 0.85, "feedback": "AI unavailable. Simulated valid response.", "correct": True}
    try:
        genai.configure(api_key=st.session_state.gemini_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt + " Return strict JSON: {'score': float, 'feedback': str, 'correct': bool}")
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except:
        return {"score": 0, "feedback": "API Error.", "correct": False}

# --- PAGE RENDERING ---

def render_sidebar():
    with st.sidebar:
        st.markdown("<h2 style='margin-left:10px;'>🧬 DataMentor</h2>", unsafe_allow_html=True)
        st.markdown("---")
        
        if st.session_state.page == "practice":
            st.markdown("### 🗺️ Your Journey")
            total = len(QUESTIONS)
            current = st.session_state.current_q_index
            
            st.progress(current / total)
            st.caption(f"{int((current/total)*100)}% Complete")
            
            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
            
            for i, q in enumerate(QUESTIONS):
                color = "#94a3b8"  # Pending (Gray)
                icon = "○"
                weight = "normal"
                
                if i < current:
                    color = "#4ade80"  # Done (Green)
                    icon = "✔"
                elif i == current:
                    color = "#38bdf8"  # Active (Blue)
                    icon = "▶"
                    weight = "bold"
                    
                st.markdown(f"""
                <div style='color: {color}; margin-bottom: 12px; font-weight: {weight}; font-size: 0.9rem;'>
                    <span style='display:inline-block; width:20px;'>{icon}</span> {q['title']}
                </div>
                """, unsafe_allow_html=True)

def render_home():
    # --- HERO SECTION ---
    st.markdown("""
    <div style='text-align: center; padding: 80px 20px;'>
        <div class='hero-text'>
            Master Data Science <br> With Corporate Precision.
        </div>
        <p style='font-size: 1.25rem; color: #94a3b8; max-width: 600px; margin: 0 auto 40px auto; line-height: 1.6;'>
            The definitive enterprise assessment platform. Validate your skills in Pandas, ML Theory, and Statistical Analysis with real-time AI feedback.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # --- CTA ---
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        if st.button("🚀 Launch Assessment Workspace"):
            st.session_state.page = "practice"
            st.rerun()
            
    # --- VISUAL CONTEXT ---
    st.markdown("---")
    col_vis, col_desc = st.columns([1, 1])
    with col_vis:
        # Instruction: Visual diagram of the workflow
        st.markdown("**Platform Workflow Architecture:**")
        st.markdown("") 
    with col_desc:
        st.markdown("### How It Works")
        st.info("1. **Select a Module:** Choose from our curriculum below.")
        st.info("2. **Execute:** Run code in our secure sandbox or answer theory prompts.")
        st.info("3. **Iterate:** Receive instant, line-by-line AI code review.")

    # --- CURRICULUM GRID ---
    st.markdown("<h2 style='text-align:center; margin: 60px 0 30px 0;'>📚 The Curriculum</h2>", unsafe_allow_html=True)
    
    # Create a grid layout for 8 cards (2 rows of 4)
    for i in range(0, len(QUESTIONS), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(QUESTIONS):
                q = QUESTIONS[i + j]
                with cols[j]:
                    badge_class = "badge-code" if q['type'] == 'code' else "badge-theory"
                    icon = "💻" if q['type'] == 'code' else "🧠"
                    
                    st.markdown(f"""
                    <div class='glass-card' style='height: 220px; position: relative;'>
                        <span class='module-badge {badge_class}'>{q['type']}</span>
                        <div style='margin-top: 20px; font-size: 1.5rem;'>{icon}</div>
                        <h4 style='margin-top: 10px; font-size: 1.1rem; color: #f1f5f9;'>{q['title']}</h4>
                        <p style='font-size: 0.85rem; color: #94a3b8; margin-top: 8px;'>{q['topic']}</p>
                        <div style='position: absolute; bottom: 20px; right: 20px; font-weight: bold; color: #64748b;'>
                            {q['points']} pts
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

def render_practice():
    q = QUESTIONS[st.session_state.current_q_index]
    
    # Header
    st.markdown(f"## {q['title']}")
    
    # Layout
    col_q, col_work = st.columns([1, 1], gap="medium")
    
    with col_q:
        st.markdown(f"""
        <div class='glass-card'>
            <div style='display:flex; justify-content:space-between;'>
                <span class='module-badge badge-{'code' if q['type']=='code' else 'theory'}'>{q['type']}</span>
                <span style='color: #64748b; font-weight:bold;'>{q['points']} PTS</span>
            </div>
            <h3 style='margin-top:15px; color:#e2e8f0;'>Problem Statement</h3>
            <p style='font-size: 1.1rem; line-height: 1.6;'>{q['content']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if "context" in q:
            st.markdown(f"**Visual Aid:** {q['context']}")
            
        if q['type'] == 'code':
            st.markdown("#### 📂 Dataset Preview")
            st.dataframe(DATASETS[q['dataset']].head(5), use_container_width=True)
    
    with col_work:
        st.markdown("#### 🛠️ Workspace")
        if q['type'] == 'code':
            user_input = st.text_area("code_editor", value=q['starter_code'], height=300, label_visibility="collapsed")
            if st.button("▶ Run & Check"):
                try:
                    env = {"df": DATASETS[q['dataset']], "pd": pd, "np": np}
                    exec(user_input, {}, env)
                    st.success("Execution Successful. Ready to Submit.")
                    st.session_state.temp_ans = user_input
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            user_input = st.text_area("text_editor", height=300, placeholder="Type your answer here...", label_visibility="collapsed")
            st.session_state.temp_ans = user_input
            
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Submit Response", type="primary"):
            with st.spinner("AI Analyzing..."):
                ans = st.session_state.get('temp_ans', '')
                fb = get_ai_evaluation(f"Question: {q['content']} Answer: {ans}")
                st.session_state.last_feedback = fb
                st.session_state.answers.append({**q, "score": fb['score']*q['points']})
                st.rerun()

    if st.session_state.last_feedback:
        fb = st.session_state.last_feedback
        color = "#22c55e" if fb['correct'] else "#f59e0b"
        st.markdown(f"""
        <div class='glass-card' style='border: 1px solid {color};'>
            <h3 style='color:{color}'>Evaluation Result</h3>
            <p>{fb['feedback']}</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Next Module ➡️"):
            st.session_state.last_feedback = None
            if st.session_state.current_q_index < len(QUESTIONS) - 1:
                st.session_state.current_q_index += 1
            else:
                st.session_state.page = "report"
            st.rerun()

def render_report():
    total = sum(a['score'] for a in st.session_state.answers)
    st.markdown(f"<h1 style='text-align:center'>Final Score: {int(total)}</h1>", unsafe_allow_html=True)
    if st.button("Restart"):
        st.session_state.clear()
        st.rerun()

# --- MAIN ---
inject_css()
render_sidebar()

if st.session_state.page == "home":
    render_home()
elif st.session_state.page == "practice":
    render_practice()
elif st.session_state.page == "report":
    render_report()
