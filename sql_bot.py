import streamlit as st

hide_github = """
    <style>
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_github, unsafe_allow_html=True)

import google.generativeai as genai
import pandas as pd

# Set up Gemini API
gemini_api_key = "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k"  # Replace with your Gemini API key
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.0-flash')



# Sample Tables for Quiz
employees_table = pd.DataFrame({
    "employee_id": [0, 1, 2, 3, 4, 5, 6, 7],
    "name": ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Helen"],
    "department": ["HR", "Sales", "IT", "Marketing", "Finance", "IT", "Sales", "HR"],
    "salary": [50000, 60000, 70000, 55000, 65000, 75000, 62000, 52000],
    "manager_id": [None, 101, 101, 102, 102, 103, 103, 104]
})

departments_table = pd.DataFrame({
    "dept_id": ["HR", "Sales", "IT", "Marketing", "Finance"],
    "location": ["New York", "Chicago", "San Francisco", "Boston", "Seattle"]
})

# SQL Questions (using MySQL syntax)
sql_questions = [
    {
        "question": "Write a query to select all columns from the employees table.",
        "correct_answer": "SELECT * FROM employees",
        "sample_table": employees_table
    },
    {
        "question": "Write a query to select only the names of all employees.",
        "correct_answer": "SELECT name FROM employees",
        "sample_table": employees_table
    },
    {
        "question": "Retrieve employees with salary greater than 60000.",
        "correct_answer": "SELECT * FROM employees WHERE salary > 60000",
        "sample_table": employees_table
    },
    {
        "question": "Count the number of employees in each department.",
        "correct_answer": "SELECT department, COUNT(*) as employee_count FROM employees GROUP BY department",
        "sample_table": employees_table
    },
    {
        "question": "Perform an INNER JOIN between employees and departments tables to list employee names with department locations.",
        "correct_answer": "SELECT e.name, d.location FROM employees e INNER JOIN departments d ON e.department = d.dept_id",
        "sample_table": pd.merge(employees_table, departments_table, left_on='department', right_on='dept_id')
    },
    {
        "question": "Select employees who have a manager (non-null manager_id).",
        "correct_answer": "SELECT * FROM employees WHERE manager_id IS NOT NULL",
        "sample_table": employees_table
    },
    {
        "question": "List employees sorted by salary in ascending order.",
        "correct_answer": "SELECT * FROM employees ORDER BY salary ASC",
        "sample_table": employees_table
    }
]

# Initialize Session State
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

# Custom CSS for Professional Design
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');
body { 
    background-color: #1E1E1E; 
    color: #FFFFFF; 
    font-family: 'Roboto', sans-serif; 
}
.stButton>button { 
    background-color: #005f73; 
    color: #FFFFFF; 
    border-radius: 8px; 
    padding: 10px 20px; 
}
.stButton>button:hover { 
    transform: scale(1.05); 
    background-color: #007f99; 
    transition: all 0.2s; 
}
.stTabs [data-baseweb="tab-highlight"] { 
    background-color: #005f73; 
}
.block-container { 
    padding: 20px; 
}
.stDataFrame table { 
    border-collapse: collapse; 
    width: 100%; 
}
.stDataFrame th { 
    background-color: #005f73; 
    padding: 10px; 
    color: #FFFFFF; 
}
.stDataFrame td { 
    padding: 8px; 
    border: 1px solid #333333; 
}
.stDataFrame tr:nth-child(even) { 
    background-color: #2E2E2E; 
}
.stDataFrame tr:hover { 
    background-color: #3A3A3A; 
}
h1, h2, h3 { 
    color: #FFFFFF; 
}
</style>
""", unsafe_allow_html=True)

# Hide Streamlit Header
st.markdown("<style>header {visibility: hidden;}</style>", unsafe_allow_html=True)

# Function to Render Introduction Section
def render_intro():
    st.title("SQL Mentor - Interactive SQL Query Practice")
    st.markdown("### Welcome to Your SQL Learning Journey!", unsafe_allow_html=True)
    st.markdown("""
    **📌 Important Note:**  
    - This quiz uses **MySQL syntax** for all SQL queries.  
    - Ensure your answers follow MySQL conventions (e.g., `LIMIT` for row limits, backticks for identifiers).  
    - If you're familiar with other SQL dialects (e.g., PostgreSQL, SQL Server), some syntax may differ.
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("In this interactive SQL quiz, you'll work with two interconnected tables:  \n- **Employees Table**: Tracks employee details like ID, name, department, salary, and manager.  \n- **Departments Table**: Contains department locations.")
    with col2:
        st.markdown("#### Tables Overview")
        table_overview = pd.DataFrame({
            "Table": ["Employees", "Departments"],
            "Rows": [len(employees_table), len(departments_table)]
        })
        st.table(table_overview)
    
    st.markdown("### 🔍 Table Previews")
    tab1, tab2 = st.tabs(["Employees", "Departments"])
    with tab1:
        st.write("**Employees Table**")
        st.dataframe(employees_table)
    with tab2:
        st.write("**Departments Table**")
        st.dataframe(departments_table)
    
    with st.expander("📝 About This Quiz"):
        st.write("""
        - You'll solve several SQL query challenges.  
        - Each question tests a different SQL concept.  
        - Immediate feedback after each answer.  
        - Final score and detailed performance analysis.  
        - **SQL Dialect:** MySQL
        """)
    
    if st.button("🚀 Start SQL Challenge"):
        st.session_state.quiz_started = True
        st.rerun()

# Function to Evaluate Answers (Simplified for Demo)
def evaluate_answer(question, correct_answer, student_answer, sample_table):
    student_answer = student_answer.strip().upper()
    correct_answer = correct_answer.upper()
    if student_answer == correct_answer:
        return "Correct! Well done!", True, sample_table, sample_table
    else:
        return f"Incorrect. The correct answer is: `{correct_answer}`", False, sample_table, None

# Function to Calculate Score
def calculate_score(user_answers):
    correct_count = sum(1 for answer in user_answers if answer["is_correct"])
    total_questions = len(user_answers)
    return (correct_count / total_questions) * 100 if total_questions > 0 else 0

# Function to Analyze Performance
def analyze_performance(user_answers):
    strengths = [answer["question"] for answer in user_answers if answer["is_correct"]]
    weaknesses = [answer["question"] for answer in user_answers if not answer["is_correct"]]
    overall_feedback = "You did well on basic queries but might need practice with joins and aggregations." if len(strengths) > len(weaknesses) else "Focus on mastering basic SQL syntax and joins."
    return {"strengths": strengths, "weaknesses": weaknesses, "overall_feedback": overall_feedback}

# Function to Render Quiz Section
def render_quiz():
    if not st.session_state.quiz_completed:
        progress = (st.session_state.current_question + 1) / len(sql_questions)
        st.progress(progress)
        st.write(f"**Progress:** {st.session_state.current_question + 1}/{len(sql_questions)} questions completed.")
        
        question_data = sql_questions[st.session_state.current_question]
        st.write(f"**Question {st.session_state.current_question + 1}:** {question_data['question']}")
        st.write("**Sample Table:**")
        st.dataframe(question_data["sample_table"])
        
        student_answer = st.text_input("Your answer:", key=f"answer_{st.session_state.current_question}")
        
        if st.button("Submit Answer"):
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
                if is_correct:
                    st.markdown(f"<span style='color:green'>**Feedback:** {feedback} 😊</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color:red'>**Feedback:** {feedback} 😢</span>", unsafe_allow_html=True)
                
                if st.session_state.current_question < len(sql_questions) - 1:
                    st.session_state.current_question += 1
                    st.rerun()
                else:
                    st.session_state.awaiting_final_submission = True
                    st.rerun()
            else:
                st.warning("Please enter an answer before submitting.")
        
        if st.session_state.awaiting_final_submission:
            if st.button("Submit All Answers"):
                st.session_state.quiz_completed = True
                st.rerun()
    else:
        st.balloons()
        st.markdown("<h1>Quiz Completed!</h1>", unsafe_allow_html=True)
        
        score = calculate_score(st.session_state.user_answers)
        st.write(f"**Your Score:** {score:.2f}%")
        
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
            st.rerun()
        
        if st.session_state.show_detailed_feedback:
            performance_feedback = analyze_performance(st.session_state.user_answers)
            st.write("### Detailed Performance Analysis")
            st.write("**Strengths (Questions you answered correctly):**")
            for i, question in enumerate(performance_feedback["strengths"]):
                st.success(f"{i + 1}. {question} ✅")
            st.write("**Weaknesses (Questions you answered incorrectly):**")
            for i, question in enumerate(performance_feedback["weaknesses"]):
                st.error(f"{i + 1}. {question} ❌")
            st.write("**Overall Feedback:**")
            st.info(performance_feedback["overall_feedback"])
        
        if st.button("🔄 Restart Quiz"):
            st.session_state.user_answers = []
            st.session_state.current_question = 0
            st.session_state.quiz_started = False
            st.session_state.quiz_completed = False
            st.session_state.show_detailed_feedback = False
            st.session_state.awaiting_final_submission = False
            st.rerun()

# Main App Logic
if not st.session_state.quiz_started:
    render_intro()
else:
    render_quiz()
