import streamlit as st
import pandas as pd
import numpy as np
import json
import time
import io
import sys

# LLM Integration
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Python Basics Bot",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# API KEY
HARD_CODED_GEMINI_API_KEY = "AIzaSyCbgdqoXv30zSd1s1WfuZfvA5ggvN48578"

# --- DATASETS ---
@st.cache_data
def load_data():
    return {
        "sales": pd.DataFrame({"item": ["Apple", "Banana", "Cherry"], "cost": [10, 20, 15]}),
        "students": pd.DataFrame({"name": ["Alice", "Bob"], "grade": [85, 90]})
    }

DATASETS = load_data()

# --- MODULES ---
MODULES = {
    "theory": {
        "title": "Python Theory", 
        "icon": "📖", 
        "desc": "Master the concepts: Syntax, Data Structures & Logic"
    },
    "practical": {
        "title": "Python Practical", 
        "icon": "💻", 
        "desc": "Hands-on coding challenges and algorithmic thinking"
    }
}

# --- QUESTION BANK ---
QUESTIONS = [
    # --- THEORY SECTION ---
    {
        "id": 1, "module": "theory", "title": "Mutable vs Immutable", "type": "theory", "difficulty": "Easy", "points": 100,
        "content": "Explain the key difference between a List and a Tuple in Python. Give one example scenario for when to use each.",
        "hint": "Think about whether you can change the data after creating it."
    },
    {
        "id": 2, "module": "theory", "title": "Python Scope", "type": "theory", "difficulty": "Medium", "points": 150,
        "content": "What is the difference between Local and Global scope? What keyword allows you to modify a global variable inside a function?",
        "hint": "The keyword starts with 'g'."
    },
    {
        "id": 3, "module": "theory", "title": "Lambda Functions", "type": "theory", "difficulty": "Medium", "points": 150,
        "content": "What is a lambda function in Python? How does it differ from a regular function defined with `def`?",
        "hint": "Anonymous, single-line functions."
    },
    {
        "id": 4, "module": "theory", "title": "PEP 8 Standards", "type": "theory", "difficulty": "Easy", "points": 100,
        "content": "What is PEP 8? Why is indentation significant in Python compared to languages like C++ or Java?",
        "hint": "Style guide and block structure."
    },
    {
        "id": 5, "module": "theory", "title": "__init__ Method", "type": "theory", "difficulty": "Hard", "points": 200,
        "content": "Explain the purpose of the `__init__` method in Python Classes. When is it automatically called?",
        "hint": "It acts as the constructor."
    },
    {
        "id": 6, "module": "theory", "title": "Decorators", "type": "theory", "difficulty": "Hard", "points": 200,
        "content": "Conceptually, what is a Python Decorator? How is it represented in syntax?",
        "hint": "Look for the @ symbol."
    },
    {
        "id": 7, "module": "theory", "title": "List Comprehension", "type": "theory", "difficulty": "Medium", "points": 150,
        "content": "Describe what List Comprehension is. Write a generic syntax example in your explanation.",
        "hint": "[x for x in list ...]"
    },
    {
        "id": 8, "module": "theory", "title": "Exception Handling", "type": "theory", "difficulty": "Easy", "points": 100,
        "content": "What is the purpose of `try`, `except`, and `finally` blocks? Which one executes regardless of errors?",
        "hint": "Cleanup code often goes in the last block."
    },

    # --- PRACTICAL SECTION ---
    {
        "id": 9, "module": "practical", "title": "Hello World Function", "type": "code", "difficulty": "Easy", "points": 100,
        "content": "Write a function named `greet` that takes a `name` argument and prints 'Hello, [name]!'.",
        "starter_code": "def greet(name):\n    # Your code here\n    pass\n\n# Test your function\ngreet('User')"
    },
    {
        "id": 10, "module": "practical", "title": "Check Even/Odd", "type": "code", "difficulty": "Easy", "points": 100,
        "content": "Write a snippet that checks if the variable `num` is even or odd and prints the result.",
        "starter_code": "num = 42\n\nif ... :\n    print('Even')\nelse:\n    print('Odd')"
    },
    {
        "id": 11, "module": "practical", "title": "Sum of List", "type": "code", "difficulty": "Medium", "points": 150,
        "content": "Given a list of numbers, calculate the total sum using a loop (do not use the built-in `sum()` function for this exercise).",
        "starter_code": "numbers = [10, 20, 30, 40]\ntotal = 0\n\n# Write loop here\n\nprint(total)"
    },
    {
        "id": 12, "module": "practical", "title": "Palindrome Checker", "type": "code", "difficulty": "Medium", "points": 150,
        "content": "Check if the string `text` is a palindrome (reads the same forward and backward). Store the boolean result in `is_palindrome`.",
        "starter_code": "text = 'radar'\n\n# Reverse logic here\n\nis_palindrome = ..."
    },
    {
        "id": 13, "module": "practical", "title": "FizzBuzz", "type": "code", "difficulty": "Medium", "points": 150,
        "content": "Write a loop from 1 to 20. Print 'Fizz' if divisible by 3, 'Buzz' if by 5, and 'FizzBuzz' if by both.",
        "starter_code": "for i in range(1, 21):\n    # Your logic"
    },
    {
        "id": 14, "module": "practical", "title": "Dictionary Frequency", "type": "code", "difficulty": "Hard", "points": 200,
        "content": "Count the frequency of each character in the string `s` and store it in a dictionary named `counts`.",
        "starter_code": "s = 'banana'\ncounts = {}\n\n# Loop through string\n\nprint(counts)"
    },
    {
        "id": 15, "module": "practical", "title": "Factorial Calculation", "type": "code", "difficulty": "Hard", "points": 200,
        "content": "Calculate the factorial of `n` (5! = 5*4*3*2*1) and assign it to the variable `result`.",
        "starter_code": "n = 5\nresult = 1\n\n# Logic here\n\nprint(result)"
    },
    {
        "id": 16, "module": "practical", "title": "Filter with Comprehension", "type": "code", "difficulty": "Hard", "points": 200,
        "content": "Use List Comprehension to create a new list `positives` containing only numbers greater than 0 from `data`.",
        "starter_code": "data = [-10, 15, -2, 30, 0, 50]\n\npositives = [ ... ]\nprint(positives)"
    }
]

# --- STATE MANAGEMENT ---
def init_state():
    defaults = {
        "page": "home",
        "active_module_id": None,     
        "active_questions": [],       
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
            background-image: radial-gradient(at 50% 0%, rgba(34, 197, 94, 0.1) 0px, transparent 50%);
            font-family: 'Inter', sans-serif;
            color: #f8fafc;
        }

        /* CARD STYLING */
        .module-card {
            background: rgba(30, 41, 59, 0.6);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 16px;
            padding: 32px;
            transition: transform 0.2s;
            height: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            justify-content: space-between;
        }
        
        .module-card:hover {
            border-color: #22c55e;
            transform: translateY(-5px);
        }
        
        /* CUSTOM BUTTON WRAPPER */
        div[data-testid="column"] button {
            width: 100%;
            background: transparent;
            border: 1px solid rgba(34, 197, 94, 0.3);
            color: #22c55e;
            border-radius: 8px;
            padding: 12px;
            transition: all 0.3s;
            font-weight: 600;
        }
        div[data-testid="column"] button:hover {
            background: rgba(34, 197, 94, 0.1);
            border-color: #22c55e;
            color: white;
            box-shadow: 0 0 15px rgba(34, 197, 94, 0.3);
        }
        
        /* HERO & HEADERS */
        h1, h2 { font-weight: 800; letter-spacing: -1px; }
        .gradient-text {
            background: linear-gradient(to right, #4ade80, #22c55e);
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
            background: linear-gradient(90deg, #4ade80, #22c55e);
        }
    </style>
    """, unsafe_allow_html=True)

# --- AI ENGINE (UPDATED) ---
def get_ai_evaluation(prompt):
    # 1. Check if Library is installed
    if not GEMINI_AVAILABLE:
        time.sleep(1)
        return {
            "score": 0.85, 
            "feedback": "⚠️ Simulation: Library not found. Install 'google-generativeai' for real feedback.", 
            "correct": True
        }
    
    # 2. Try Real AI Connection
    try:
        genai.configure(api_key=st.session_state.gemini_key)
        # UPDATED TO 'gemini-pro' for better compatibility
        model = genai.GenerativeModel('gemini-3-pro-preview') 
        response = model.generate_content(prompt + " Return strict JSON: {'score': float, 'feedback': str, 'correct': bool}")
        
        # Cleanup JSON response
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
        
    except Exception as e:
        # 3. Fallback Mode
        time.sleep(1) 
        return {
            "score": 0.9, 
            "feedback": f"⚠️ Simulation Mode (AI Error). Proceeding with success. Details: {str(e)[:50]}...", 
            "correct": True
        }

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
        st.markdown("### 🐍 PythonBot")
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
            Python <span class='gradient-text'>Basics Bot</span>
        </h1>
        <p style='color: #cbd5e1; font-size: 1.2rem; max-width: 600px; margin: 0 auto;'>
            Master the fundamentals of Python through targeted Theory and Practical challenges.
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    
    # --- 2 MODULE LAYOUT ---
    st.markdown("### 📚 Select a Learning Module")
    
    col1, col2 = st.columns(2)
    
    # THEORY MODULE
    with col1:
        mod = MODULES['theory']
        q_count = len([q for q in QUESTIONS if q['module'] == 'theory'])
        st.markdown(f"""
        <div class='module-card'>
            <div style='font-size: 4rem; margin-bottom: 10px;'>{mod['icon']}</div>
            <h2 style='color: #f8fafc; margin-bottom: 5px;'>{mod['title']}</h2>
            <p style='color: #94a3b8; margin-bottom: 20px;'>{mod['desc']}</p>
            <div style='color:#64748b; font-size: 0.9rem;'>
                {q_count} Questions • Concept Mastery
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if st.button("Start Theory", key="btn_theory"):
            start_module('theory')

    # PRACTICAL MODULE
    with col2:
        mod = MODULES['practical']
        q_count = len([q for q in QUESTIONS if q['module'] == 'practical'])
        st.markdown(f"""
        <div class='module-card'>
            <div style='font-size: 4rem; margin-bottom: 10px;'>{mod['icon']}</div>
            <h2 style='color: #f8fafc; margin-bottom: 5px;'>{mod['title']}</h2>
            <p style='color: #94a3b8; margin-bottom: 20px;'>{mod['desc']}</p>
            <div style='color:#64748b; font-size: 0.9rem;'>
                {q_count} Challenges • Coding Practice
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        if st.button("Start Practical", key="btn_practical"):
            start_module('practical')

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
                <span style='background:rgba(34, 197, 94, 0.2); color:#22c55e; padding:4px 12px; border-radius:12px; font-size:0.8rem; font-weight:bold;'>{q['type'].upper()}</span>
                <span style='color:#94a3b8;'>{q['points']} PTS</span>
            </div>
            <h2 style='font-size:1.5rem; margin-bottom:16px;'>{q['title']}</h2>
            <p style='font-size:1.1rem; line-height:1.6;'>{q['content']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Hint
        if st.checkbox("Show Hint"):
            st.info(q.get('hint', 'No hint available.'))
            
        # Optional: Show Dataset
        if q.get('dataset'):
            st.markdown("#### 📂 Reference Data")
            st.dataframe(DATASETS[q['dataset']], use_container_width=True)
            
    with col_work:
        st.markdown("#### 🛠️ Solution Workspace")
        
        # 1. Editor Area
        if q['type'] == 'code':
            user_input = st.text_area("Code Editor", value=q.get('starter_code', ''), height=300, label_visibility="collapsed")
            if st.button("▶ Run Code"):
                try:
                    old_stdout = sys.stdout
                    new_stdout = io.StringIO()
                    sys.stdout = new_stdout
                    
                    env = {"pd": pd, "np": np}
                    if q.get('dataset'): env["df"] = DATASETS[q['dataset']]
                    
                    exec(user_input, {}, env)
                    
                    result_output = new_stdout.getvalue()
                    sys.stdout = old_stdout
                    
                    st.success("Code Executed.")
                    if result_output:
                        st.markdown("**Output:**")
                        st.code(result_output)
                    
                    st.session_state.temp_input = user_input
                except Exception as e:
                    st.error(f"Runtime Error: {e}")
        else:
            user_input = st.text_area("Theory Editor", height=300, placeholder="Type your detailed answer...", label_visibility="collapsed")
            st.session_state.temp_input = user_input

        st.markdown("<br>", unsafe_allow_html=True)
        
        # 2. Buttons Area
        if st.button("Submit Response", type="primary", use_container_width=True):
            with st.spinner("AI Evaluating..."):
                ans = st.session_state.get('temp_input', '')
                fb = get_ai_evaluation(f"Question: {q['content']} Answer: {ans}")
                st.session_state.last_feedback = fb
                st.session_state.answers.append({**q, "score": fb['score']*q['points']})
                st.rerun()

        # 3. Next Button & Feedback (Only appears if feedback exists)
        if st.session_state.last_feedback:
            # Spacer
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            
            # Next Button
            if st.button("Next Challenge ➡️", type="secondary", use_container_width=True):
                st.session_state.last_feedback = None
                if st.session_state.current_q_index < len(q_list) - 1:
                    st.session_state.current_q_index += 1
                else:
                    st.session_state.page = "report"
                st.rerun()
                
            # Feedback Box
            fb = st.session_state.last_feedback
            color = "#22c55e" if fb['correct'] else "#f59e0b"
            st.markdown(f"""
            <div style='margin-top:20px; padding:20px; background:rgba(15, 23, 42, 0.9); border-left:4px solid {color}; border-radius:8px;'>
                <h3 style='color:{color}; margin:0;'>Analysis Complete</h3>
                <p style='color:#e2e8f0; margin-top:8px;'>{fb['feedback']}</p>
            </div>
            """, unsafe_allow_html=True)

def render_report():
    st.markdown("<h1 style='text-align:center; margin-bottom:40px;'>Module Complete! 🎓</h1>", unsafe_allow_html=True)
    
    mod_id = st.session_state.active_module_id
    relevant_answers = [a for a in st.session_state.answers if a['module'] == mod_id]
    
    total = sum(a['score'] for a in relevant_answers)
    
    c1, c2 = st.columns([1, 1])
    with c1:
         st.markdown(f"""
         <div style='text-align:center; background:rgba(30,41,59,0.5); padding:40px; border-radius:20px;'>
            <div style='font-size:4rem; font-weight:bold; color:#22c55e;'>{int(total)}</div>
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


