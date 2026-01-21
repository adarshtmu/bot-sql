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

# API KEY
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

# --- MODULES & QUESTION BANK ---
# We define modules first, then assign questions to them.
MODULES = {
    "m1": {"title": "Supervised Learning", "icon": "🧠", "desc": "Regression, Classification & Bias"},
    "m2": {"title": "Data Wrangling", "icon": "🐼", "desc": "Pandas Filtering & Aggregations"},
    "m3": {"title": "Model Evaluation", "icon": "⚖️", "desc": "Precision, Recall & Metrics"},
    "m4": {"title": "Unsupervised Learning", "icon": "✨", "desc": "Clustering & Dimensionality"}
}

QUESTIONS = [
    # MODULE 1: SUPERVISED LEARNING
    {
        "id": 1, "module": "m1", "title": "Bias-Variance Tradeoff", "type": "theory", "difficulty": "Easy", "points": 100,
        "content": "Explain the Bias-Variance Tradeoff. What happens to bias and variance as model complexity increases?",
        "context": "",
        "hint": "Think about Underfitting (High Bias) vs Overfitting (High Variance)."
    },
    {
        "id": 2, "module": "m1", "title": "Feature Importance", "type": "code", "difficulty": "Hard", "points": 200,
        "content": "Create a new column 'price_per_sqft' in the `housing` dataset. Return the correlation between 'bedrooms' and this new feature.",
        "dataset": "housing",
        "starter_code": "# Calculate corr between bedrooms and price_per_sqft\n\nresult = ..."
    },

    # MODULE 2: DATA WRANGLING
    {
        "id": 3, "module": "m2", "title": "Filter Logic", "type": "code", "difficulty": "Easy", "points": 100,
        "content": "Using `ecommerce`, filter for rows where 'spend' > 400. Assign the DataFrame to `high_rollers`.",
        "dataset": "ecommerce",
        "starter_code": "high_rollers = df[...]"
    },
    {
        "id": 4, "module": "m2", "title": "Group Aggregation", "type": "code", "difficulty": "Medium", "points": 150,
        "content": "Calculate the average 'clicks' per 'category' in `ecommerce`. Assign the Series to `cat_clicks`.",
        "dataset": "ecommerce",
        "starter_code": "cat_clicks = ..."
    },

    # MODULE 3: MODEL EVALUATION
    {
        "id": 5, "module": "m3", "title": "Precision vs Recall", "type": "theory", "difficulty": "Medium", "points": 150,
        "content": "In cancer detection, why is Recall often prioritized over Precision? Explain in terms of False Negatives.",
        "context": "",
        "hint": "What is the cost of missing a positive case?"
    },
    {
        "id": 6, "module": "m3", "title": "Handling Imbalance", "type": "theory", "difficulty": "Hard", "points": 200,
        "content": "Your dataset has 99% Class A and 1% Class B. Name 2 techniques to handle this imbalance.",
        "context": "",
        "hint": "Resampling or Class Weights."
    },

    # MODULE 4: UNSUPERVISED LEARNING
    {
        "id": 7, "module": "m4", "title": "K-Means Elbow", "type": "theory", "difficulty": "Medium", "points": 150,
        "content": "Describe the 'Elbow Method'. What variable is plotted on the Y-axis?",
        "context": "",
        "hint": "Inertia or WCSS."
    },
    {
        "id": 8, "module": "m4", "title": "Missing Imputation", "type": "code", "difficulty": "Hard", "points": 200,
        "content": "Fill missing values in the 'spend' column with the median. Write the Pandas syntax.",
        "dataset": "ecommerce",
        "starter_code": "df['spend'] = ..."
    }
]

# --- STATE MANAGEMENT ---
def init_state():
    defaults = {
        "page": "home",
        "active_module_id": None,     # Tracks which module is clicked
        "active_questions": [],       # The subset of questions for that module
        "current_q_index": 0,
        "answers": [],
        "gemini_key": HARD_CODED_GEMINI_API_KEY,
        "last_feedback": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# --- CSS ENGINE ---
def inject_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;600&display=swap');
        
        .stApp {
            background-color: #020617;
            background-image: radial-gradient(at 50% 0%, rgba(124, 58, 237, 0.15) 0px, transparent 50%);
            font-family: 'Inter', sans-serif;
            color: #f8fafc;
        }

        /* CARD STYLING */
        .module-card {
            background: rgba(30, 41, 59, 0.6);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 24px;
            transition: transform 0.2s;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        
        /* CUSTOM BUTTON WRAPPER */
        div[data-testid="column"] button {
            width: 100%;
            background: transparent;
            border: 1px solid rgba(56, 189, 248, 0.3);
            color: #38bdf8;
            border-radius: 8px;
            padding: 8px;
            transition: all 0.3s;
        }
        div[data-testid="column"] button:hover {
            background: rgba(56, 189, 248, 0.1);
            border-color: #38bdf8;
            color: white;
            box-shadow: 0 0 15px rgba(56, 189, 248, 0.3);
        }
        
        /* HERO & HEADERS */
        h1, h2 { font-weight: 800; letter-spacing: -1px; }
        .gradient-text {
            background: linear-gradient(to right, #60a5fa, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* EDITOR */
        .stTextArea textarea {
            background: #0f172a !important;
            color: #f1f5f9 !important;
            font-family: 'JetBrains Mono', monospace;
            border: 1px solid #334155 !important;
        }
        
        /* PROGRESS */
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #818cf8, #c084fc);
        }
    </style>
    """, unsafe_allow_html=True)

# --- AI ENGINE ---
def get_ai_evaluation(prompt):
    if not GEMINI_AVAILABLE:
        time.sleep(1)
        return {"score": 0.9, "feedback": "Simulated AI: Excellent work. Logic holds up.", "correct": True}
    try:
        genai.configure(api_key=st.session_state.gemini_key)
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt + " Return strict JSON: {'score': float, 'feedback': str, 'correct': bool}")
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except:
        return {"score": 0, "feedback": "AI Connection Failure.", "correct": False}

# --- PAGE LOGIC ---

def start_module(module_id):
    """Filters questions for the specific module and starts practice"""
    subset = [q for q in QUESTIONS if q['module'] == module_id]
    st.session_state.active_questions = subset
    st.session_state.active_module_id = module_id
    st.session_state.current_q_index = 0
    st.session_state.page = "practice"
    st.rerun()

def render_navbar():
    col1, col2 = st.columns([1, 5])
    with col1:
        st.markdown("### 🧬 DataMentor")
    with col2:
        if st.session_state.page == "practice":
            mod_title = MODULES[st.session_state.active_module_id]['title']
            idx = st.session_state.current_q_index + 1
            total = len(st.session_state.active_questions)
            st.markdown(f"<div style='text-align:right; color:#94a3b8; padding-top:10px;'>Active Module: <b>{mod_title}</b> | Q {idx}/{total}</div>", unsafe_allow_html=True)

def render_home():
    # Hero
    st.markdown("""
    <div style='text-align: center; padding: 60px 0 40px 0;'>
        <h1 style='font-size: 3.5rem; margin-bottom: 10px;'>
            Enterprise <span class='gradient-text'>Skill Validation</span>
        </h1>
        <p style='color: #cbd5e1; font-size: 1.2rem; max-width: 600px; margin: 0 auto;'>
            Select a specialized module below to begin your targeted assessment.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    
    # --- INTERACTIVE CURRICULUM GRID ---
    st.markdown("### 📚 Select a Learning Module")
    st.markdown("Click 'Start Module' to load the specific question set for that topic.")
    
    # We iterate through modules and create columns
    module_keys = list(MODULES.keys())
    
    # Row 1
    cols = st.columns(4)
    for i, col in enumerate(cols):
        if i < len(module_keys):
            mid = module_keys[i]
            mod = MODULES[mid]
            q_count = len([q for q in QUESTIONS if q['module'] == mid])
            
            with col:
                # Visual Card
                st.markdown(f"""
                <div class='module-card'>
                    <div style='font-size: 3rem; margin-bottom: 10px;'>{mod['icon']}</div>
                    <h3 style='font-size: 1.2rem; color: #f8fafc; margin-bottom: 5px;'>{mod['title']}</h3>
                    <p style='font-size: 0.9rem; color: #94a3b8; height: 40px;'>{mod['desc']}</p>
                    <div style='display:flex; justify-content:space-between; margin-top:15px; font-size:0.8rem; color:#64748b;'>
                        <span>{q_count} Challenges</span>
                        <span>Avg: 15m</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # FUNCTIONAL BUTTON BELOW CARD
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
                if st.button(f"Start {mod['title']}", key=f"btn_{mid}"):
                    start_module(mid)

def render_practice():
    # Use the active subset of questions
    q_list = st.session_state.active_questions
    q = q_list[st.session_state.current_q_index]
    
    # Layout
    col_q, col_work = st.columns([1, 1], gap="medium")
    
    with col_q:
        st.markdown(f"""
        <div style='background:rgba(255,255,255,0.03); padding:24px; border-radius:16px; border:1px solid rgba(255,255,255,0.1);'>
            <div style='display:flex; justify-content:space-between; margin-bottom:16px;'>
                <span style='background:rgba(56, 189, 248, 0.2); color:#38bdf8; padding:4px 12px; border-radius:12px; font-size:0.8rem; font-weight:bold;'>{q['type'].upper()}</span>
                <span style='color:#94a3b8;'>{q['points']} PTS</span>
            </div>
            <h2 style='font-size:1.5rem; margin-bottom:16px;'>{q['title']}</h2>
            <p style='font-size:1.1rem; line-height:1.6;'>{q['content']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Context Image Trigger
        if "context" in q:
            st.markdown(f"**Visual Reference:** {q['context']}")
            
        if q['type'] == 'code':
            st.markdown("#### 📂 Active Dataset")
            st.dataframe(DATASETS[q['dataset']].head(3), use_container_width=True)
            
    with col_work:
        st.markdown("#### 🛠️ Solution Workspace")
        
        if q['type'] == 'code':
            user_input = st.text_area("Code Editor", value=q['starter_code'], height=300, label_visibility="collapsed")
            if st.button("▶ Run Code"):
                try:
                    env = {"df": DATASETS[q['dataset']], "pd": pd, "np": np}
                    exec(user_input, {}, env)
                    st.success("Code Executed Successfully.")
                    st.session_state.temp_input = user_input
                except Exception as e:
                    st.error(f"Runtime Error: {e}")
        else:
            user_input = st.text_area("Theory Editor", height=300, placeholder="Type your detailed answer...", label_visibility="collapsed")
            st.session_state.temp_input = user_input

        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Submit Response", type="primary", use_container_width=True):
            with st.spinner("AI Analyst Evaluating..."):
                ans = st.session_state.get('temp_input', '')
                fb = get_ai_evaluation(f"Question: {q['content']} Answer: {ans}")
                st.session_state.last_feedback = fb
                st.session_state.answers.append({**q, "score": fb['score']*q['points']})
                st.rerun()

    # Feedback Overlay
    if st.session_state.last_feedback:
        fb = st.session_state.last_feedback
        color = "#22c55e" if fb['correct'] else "#f59e0b"
        st.markdown(f"""
        <div style='margin-top:20px; padding:20px; background:rgba(15, 23, 42, 0.9); border-left:4px solid {color}; border-radius:8px;'>
            <h3 style='color:{color}; margin:0;'>Analysis Complete</h3>
            <p style='color:#e2e8f0; margin-top:8px;'>{fb['feedback']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("Next Challenge ➡️", type="secondary"):
            st.session_state.last_feedback = None
            if st.session_state.current_q_index < len(q_list) - 1:
                st.session_state.current_q_index += 1
            else:
                st.session_state.page = "report"
            st.rerun()

def render_report():
    st.markdown("<h1 style='text-align:center; margin-bottom:40px;'>Module Complete! 🎓</h1>", unsafe_allow_html=True)
    
    # Filter answers for this specific module run
    mod_id = st.session_state.active_module_id
    relevant_answers = [a for a in st.session_state.answers if a['module'] == mod_id]
    
    total = sum(a['score'] for a in relevant_answers)
    max_pts = sum(a['points'] for a in relevant_answers)
    
    c1, c2 = st.columns([1, 1])
    with c1:
         st.markdown(f"""
         <div style='text-align:center; background:rgba(30,41,59,0.5); padding:40px; border-radius:20px;'>
            <div style='font-size:4rem; font-weight:bold; color:#38bdf8;'>{int(total)}</div>
            <div style='color:#94a3b8;'>Points Earned</div>
         </div>
         """, unsafe_allow_html=True)
         
    with c2:
        st.markdown("### 🔍 Performance Breakdown")
        if relevant_answers:
            df = pd.DataFrame(relevant_answers)
            st.dataframe(df[['title', 'type', 'score']], use_container_width=True)
    
    st.markdown("<br><hr><br>", unsafe_allow_html=True)
    if st.button("⬅️ Return to Module Selection", use_container_width=True):
        st.session_state.page = "home"
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
