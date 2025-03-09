import streamlit as st
import google.generativeai as genai
import pandas as pd
from streamlit.components.v1 import html

# Advanced Custom CSS
advanced_style = """
<style>
    /* Main Container */
    .main {
        background-color: #f5f7fb;
        padding: 2rem;
    }
    
    /* Header Section */
    .header {
        background: linear-gradient(135deg, #2b5876 0%, #4e4376 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Progress Bar */
    .progress-container {
        display: flex;
        justify-content: space-between;
        margin: 2rem 0;
        position: relative;
    }
    
    .progress-step {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: #e0e0e0;
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1;
    }
    
    .progress-step.active {
        background: #4CAF50;
        color: white;
    }
    
    .progress-line {
        position: absolute;
        height: 4px;
        background: #e0e0e0;
        width: 100%;
        top: 50%;
        transform: translateY(-50%);
    }
    
    /* Question Card */
    .question-card {
        background: white;
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Code Input */
    .code-input {
        font-family: 'Fira Code', monospace !important;
        font-size: 14px !important;
        border: 2px solid #e0e0e0 !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }
    
    /* Result Badges */
    .correct-badge {
        background: #e8f5e9 !important;
        color: #2e7d32 !important;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #4CAF50;
    }
    
    .incorrect-badge {
        background: #ffebee !important;
        color: #c62828 !important;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #ef5350;
    }
    
    /* Table Styling */
    .dataframe {
        border-radius: 8px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    
    /* Button Styling */
    .stButton>button {
        background: #4CAF50 !important;
        color: white !important;
        border-radius: 25px !important;
        padding: 0.5rem 2rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(76,175,80,0.3) !important;
    }
</style>
"""

st.markdown(advanced_style, unsafe_allow_html=True)

# JavaScript for confetti animation
confetti_js = """
<script>
function confetti() {
    const duration = 3000;
    const end = Date.now() + duration;

    (function frame() {
        // Launch confetti from the left and right edges
        confetti({
            particleCount: 7,
            angle: 60,
            spread: 55,
            origin: { x: 0 },
            colors: ['#ff0000', '#00ff00', '#0000ff']
        });
        confetti({
            particleCount: 7,
            angle: 120,
            spread: 55,
            origin: { x: 1 },
            colors: ['#ff0000', '#00ff00', '#0000ff']
        });

        if (Date.now() < end) {
            requestAnimationFrame(frame);
        }
    }());
}
</script>
"""

# Set up Gemini API
gemini_api_key = "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k"
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

# Define sample tables
users_table = pd.DataFrame({
    "user_id": [1, 2, 3, 4],
    "name": ["Alice", "Bob", "Charlie", "David"],
    "email": ["alice@example.com", "bob@example.com", "charlie@example.com", "david@example.com"],
    "age": [25, 30, 35, 40],
    "city": ["New York", "Los Angeles", "Chicago", "Houston"]
})

orders_table = pd.DataFrame({
    "order_id": [101, 102, 103, 104, 105],
    "user_id": [1, 2, 3, 1, 4],
    "amount": [50.00, 75.50, 120.00, 200.00, 35.00],
    "order_date": ["2024-02-01", "2024-02-05", "2024-02-10", "2024-02-15", "2024-02-20"],
    "status": ["Completed", "Pending", "Completed", "Shipped", "Cancelled"]
})

merged_table = pd.merge(users_table, orders_table, on="user_id", how="inner")

# SQL Questions
sql_questions = [
    {
        "question": "Imagine you are the database guardian responsible for managing user data. Your task is to extract a complete snapshot of all users from the 'users' table. Write a SQL query that retrieves every column and every record so you can see all the details of each user.",
        "correct_answer": "SELECT * FROM users;",
        "sample_table": users_table
    },
    # ... (keep other questions the same as original)
]

# Session State Initialization
if "user_answers" not in st.session_state:
    st.session_state.user_answers = []
if "current_question" not in st.session_state:
    st.session_state.current_question = 0
if "quiz_started" not in st.session_state:
    st.session_state.quiz_started = False
if "quiz_completed" not in st.session_state:
    st.session_state.quiz_completed = False
if "show_detailed_feedback" not in st.session_state:
    st.session_state.show_detailed_feedback = False
if "awaiting_final_submission" not in st.session_state:
    st.session_state.awaiting_final_submission = False

def create_progress_steps(current, total):
    progress_html = f"""
    <div class="progress-container">
        <div class="progress-line"></div>
    """
    for i in range(total):
        active = "active" if i <= current else ""
        progress_html += f"""
        <div class="progress-step {active}">{i+1}</div>
        """
    progress_html += "</div>"
    return progress_html

def simulate_query(query, sample_table):
    # ... (keep original simulate_query implementation)

def evaluate_answer(question, correct_answer, student_answer, sample_table):
    # ... (keep original evaluate_answer implementation)

def calculate_score(user_answers):
    # ... (keep original calculate_score implementation)

def analyze_performance(user_answers):
    # ... (keep original analyze_performance implementation)

# Streamlit App Flow
if not st.session_state.quiz_started:
    st.markdown("<div class='header'><h1>🚀 SQL Mastery Challenge</h1></div>", unsafe_allow_html=True)
    
    cols = st.columns([2, 1])
    with cols[0]:
        st.markdown("""
        ## Welcome to Interactive SQL Training!
        **Hone your SQL skills with real-world challenges**
        - 🧠 10 progressively difficult questions
        - 📊 Real dataset challenges
        - 📝 Instant AI-powered feedback
        - 🏆 Final performance analysis
        """)
        
        if st.button("Start Challenge", key="start_btn"):
            st.session_state.quiz_started = True
            st.rerun()
    
    with cols[1]:
        st.markdown("### 📚 Dataset Overview")
        dataset_info = pd.DataFrame({
            'Table': ['Users', 'Orders'],
            'Records': [len(users_table), len(orders_table)],
            'Columns': [len(users_table.columns), len(orders_table.columns)]
        })
        st.dataframe(dataset_info, use_container_width=True)

elif st.session_state.quiz_started and not st.session_state.quiz_completed:
    html(create_progress_steps(st.session_state.current_question, len(sql_questions)))
    
    question_data = sql_questions[st.session_state.current_question]
    st.markdown(f"""
    <div class="question-card">
        <h3>Question {st.session_state.current_question + 1}</h3>
        <p>{question_data['question']}</p>
        <div style="margin: 1rem 0;">
            <h4>Sample Table</h4>
            {question_data['sample_table'].to_html(index=False)}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    student_answer = st.text_area("Write your SQL query:", 
                                height=150, 
                                key=f"input_{st.session_state.current_question}",
                                help="Use MySQL syntax. Example: SELECT * FROM users;")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("▶️ Submit & Continue", type="primary"):
            if student_answer.strip():
                feedback, is_correct, expected_result, actual_result = evaluate_answer(
                    question_data["question"],
                    question_data["correct_answer"],
                    student_answer,
                    question_data["sample_table"]
                )
                st.session_state.user_answers.append({
                    "question": question_data["question"],
                    "student_answer": student_answer,
                    "feedback": feedback,
                    "is_correct": is_correct,
                    "expected_result": expected_result,
                    "actual_result": actual_result
                })
                
                if st.session_state.current_question < len(sql_questions) - 1:
                    st.session_state.current_question += 1
                else:
                    st.session_state.awaiting_final_submission = True
                st.rerun()
            else:
                st.warning("Please enter an answer before submitting.")

elif st.session_state.quiz_completed:
    html(confetti_js)
    html("<script>confetti()</script>")
    
    score = calculate_score(st.session_state.user_answers)
    st.markdown(f"""
    <div class="header">
        <h1>🎉 Challenge Complete!</h1>
        <h3>Your Final Score: {score:.2f}%</h3>
    </div>
    """, unsafe_allow_html=True)
    
    if score < 50:
        st.markdown("""
        <div style="background-color: #ffcccc; padding: 20px; border-radius: 10px; text-align: center;">
            <h2 style="color: #000000;">Your score is below 50% 😢</h2>
            <p style="font-size: 18px; color: #000000;">Book a mentor now to upgrade your SQL skills!</p>
            <a href="https://www.corporatebhaiya.com/" target="_blank">
                <button style="background-color: #cc0000; color: white; padding: 10px 20px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer;">
                    Book Now
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background-color: #ccffcc; padding: 20px; border-radius: 10px; text-align: center;">
            <h2 style="color: #000000;">Great job scoring above 50%! 🎉</h2>
            <p style="font-size: 18px; color: #000000;">Take the next step with a mock interview and resume building session!</p>
            <a href="https://www.corporatebhaiya.com/" target="_blank">
                <button style="background-color: #008000; color: white; padding: 10px 20px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer;">
                    Book Now
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    if st.button("📊 Detailed Feedback"):
        st.session_state.show_detailed_feedback = True
    
    if st.session_state.show_detailed_feedback:
        performance_feedback = analyze_performance(st.session_state.user_answers)
        st.markdown("### Detailed Performance Analysis")
        
        with st.expander("✅ Strengths", expanded=True):
            for i, question in enumerate(performance_feedback["strengths"]):
                st.markdown(f"""
                <div class="correct-badge">
                    <b>Question {i+1}:</b> {question}
                </div>
                """, unsafe_allow_html=True)
        
        with st.expander("❌ Weaknesses", expanded=True):
            for i, question in enumerate(performance_feedback["weaknesses"]):
                st.markdown(f"""
                <div class="incorrect-badge">
                    <b>Question {i+1}:</b> {question}
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("### Overall Feedback")
        st.info(performance_feedback["overall_feedback"])
    
    if st.button("🔄 Restart Quiz"):
        st.session_state.user_answers = []
        st.session_state.current_question = 0
        st.session_state.quiz_started = False
        st.session_state.quiz_completed = False
        st.session_state.show_detailed_feedback = False
        st.session_state.awaiting_final_submission = False
        st.rerun()
