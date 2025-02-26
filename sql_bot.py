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
gemini_api_key = "AIzaSyD3eATxXF344ZQGW8FKCgXDUcJkcB5TYA"  # Replace with your Gemini API key
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-pro')

# Sample Tables for Quiz
employees_table = pd.DataFrame({
    "employee_id": [101, 102, 103, 104, 105, 106, 107, 108],
    "name": ["Alice", "Bob", "Charlie", "David", "Eve", "Frank", "Grace", "Helen"],
    "department": ["HR", "Sales", "IT", "Marketing", "Finance", "IT", "Sales", "HR"],
    "salary": [50000, 60000, 70000, 55000, 65000, 75000, 62000, 52000],
    "manager_id": [None, 101, 101, 102, 102, 103, 103, 104]
})

departments_table = pd.DataFrame({
    "dept_id": ["HR", "Sales", "IT", "Marketing", "Finance"],
    "location": ["New York", "Chicago", "San Francisco", "Boston", "Seattle"]
})

# Revised SQL questions using only the Employees and Departments tables with easier queries
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

# Initialize session state
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

def simulate_query(query, sample_table):
    """Simulate SQL queries on a pandas DataFrame in a flexible way."""
    try:
        query = query.strip().lower().replace(";", "")
        
        # Handle SELECT queries
        if query.startswith("select"):
            # Extract the part after SELECT and before FROM
            select_part = query.split("select")[1].split("from")[0].strip()
            from_part = query.split("from")[1].strip()
            
            # Handle COUNT(*)
            if "count(*)" in select_part:
                result = pd.DataFrame({"count": [len(sample_table)]})
                return result.reset_index(drop=True)
            
            # Handle AVG(column)
            elif "avg(" in select_part:
                column = select_part.split("avg(")[1].split(")")[0].strip()
                result = pd.DataFrame({"avg": [sample_table[column].mean()]})
                return result.reset_index(drop=True)
            
            # Handle SUM(column)
            elif "sum(" in select_part:
                column = select_part.split("sum(")[1].split(")")[0].strip()
                result = pd.DataFrame({"sum": [sample_table[column].sum()]})
                return result.reset_index(drop=True)
            
            # Handle SELECT * (all columns)
            elif "*" in select_part:
                if "where" in from_part:
                    # Extract the condition after WHERE
                    condition = from_part.split("where")[1].strip()
                    # Replace SQL equality operator with Python's
                    condition = condition.replace("=", "==")
                    result = sample_table.query(condition)
                else:
                    result = sample_table.copy()
                return result.reset_index(drop=True)
            
            # Handle specific columns
            else:
                columns = [col.strip() for col in select_part.split(",")]
                if "where" in from_part:
                    # Extract the condition after WHERE
                    condition = from_part.split("where")[1].strip()
                    # Replace SQL equality operator with Python's
                    condition = condition.replace("=", "==")
                    result = sample_table.query(condition)[columns]
                else:
                    result = sample_table[columns]
                return result.reset_index(drop=True)
        
        # Handle unsupported queries
        else:
            return "Query simulation is only supported for SELECT statements."
    
    except Exception as e:
        return f"Error simulating query: {str(e)}"
    
    except Exception as e:
        return f"Error simulating query: {str(e)}"

def evaluate_answer(question, correct_answer, student_answer, sample_table):
    """Evaluate the user's answer using Gemini API and simulate the query."""
    # Simulate the expected query (correct answer)
    expected_result = simulate_query(correct_answer, sample_table)
    
    # Simulate the actual query (user's answer)
    actual_result = simulate_query(student_answer, sample_table)
    
    # Determine if the answer is correct
    if isinstance(expected_result, pd.DataFrame) and isinstance(actual_result, pd.DataFrame):
        is_correct = expected_result.equals(actual_result)
    else:
        is_correct = str(expected_result) == str(actual_result)
    
    # Prepare feedback message
    if is_correct:
        feedback = "Correct answer! Well done."
    else:
        feedback = f"Incorrect answer. Expected result was:\n{expected_result}"
    
    # Evaluate the answer using Gemini API
    prompt = f"""
    Question: {question}
    Correct Answer: {correct_answer}
    Your Answer: {student_answer}
    Expected Query Result: {expected_result}
    Actual Query Result: {actual_result}
    Evaluate your answer and provide feedback. Mention if the answer is correct or incorrect, and explain why.
    """
    response = model.generate_content(prompt)
    feedback_api = response.text
    feedback_api = feedback_api.replace("student", "you")
    
    return feedback_api, is_correct, expected_result, actual_result

def calculate_score(user_answers):
    """Calculate the score based on correct answers."""
    correct_answers = sum(1 for ans in user_answers if ans["is_correct"])
    total_questions = len(user_answers)
    return (correct_answers / total_questions) * 100

def analyze_performance(user_answers):
    """Analyze the user's performance and provide detailed feedback."""
    # Calculate areas of strength and weakness
    correct_questions = [ans["question"] for ans in user_answers if ans["is_correct"]]
    incorrect_questions = [ans["question"] for ans in user_answers if not ans["is_correct"]]
    
    # Generate detailed feedback
    feedback = {
        "strengths": correct_questions,
        "weaknesses": incorrect_questions,
        "overall_feedback": ""
    }
    
    # Use Gemini API to generate overall feedback
    prompt = f"""
    You answered {len(correct_questions)} out of {len(user_answers)} questions correctly.
    Correct Questions: {correct_questions}
    Incorrect Questions: {incorrect_questions}
    Provide detailed feedback on your overall performance, including areas of strength and weakness.
    """
    response = model.generate_content(prompt)
    feedback["overall_feedback"] = response.text
    
    return feedback

def get_emoji(is_correct):
    return "😊" if is_correct else "😢"

# Streamlit App
if not st.session_state.quiz_started:
    st.title("SQL Mentor - Interactive SQL Query Practice")
    
    # Enhanced Table Introduction
    st.write("### Welcome to Your SQL Learning Journey!")
    
    # Inform the user about the SQL dialect
    st.markdown("""
    **📌 Important Note:**
    - This quiz uses **MySQL syntax** for all SQL queries.
    - Ensure your answers follow MySQL conventions (e.g., `LIMIT` for row limits, backticks for identifiers, etc.).
    - If you're familiar with other SQL dialects (e.g., PostgreSQL, SQL Server), some syntax may differ.
    """)
    
    # Create columns for visual layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("""
        In this interactive SQL quiz, you'll work with two interconnected tables:
        - **Employees Table**: Tracks employee details like ID, name, department, salary, and manager.
        - **Departments Table**: Contains department locations.
        """)
    
    with col2:
        st.markdown("#### Tables Overview")
        table_overview = pd.DataFrame({
            "Table": ["Employees", "Departments"],
            "Rows": [len(employees_table), len(departments_table)]
        })
        st.table(table_overview)
    
    # Detailed Table Previews
    st.write("### 🔍 Table Previews")
    
    # Create tabs for each table
    tab1, tab2 = st.tabs(["Employees", "Departments"])
    
    with tab1:
        st.write("**Employees Table**")
        st.dataframe(employees_table)
    
    with tab2:
        st.write("**Departments Table**")
        st.dataframe(departments_table)
    
    # Additional Context
    with st.expander("📝 About This Quiz"):
        st.write("""
        - You'll solve several SQL query challenges.
        - Each question tests a different SQL concept.
        - Immediate feedback after each answer.
        - Final score and detailed performance analysis.
        - **SQL Dialect:** MySQL
        """)
    
    # Start Quiz Button
    if st.button("🚀 Start SQL Challenge"):
        st.session_state.quiz_started = True
        st.rerun()

# Display chat history only when quiz is ongoing
if st.session_state.quiz_started and not st.session_state.quiz_completed:
    if st.session_state.user_answers:
        st.write("### Chat History")
        for i, ans in enumerate(st.session_state.user_answers):
            with st.expander(f"Question {i + 1}: {ans['question']}", expanded=True):
                st.write(f"**Your Answer:** {ans['student_answer']}")
                if ans["is_correct"]:
                    st.markdown(f"<span style='color:green'>✅ **Feedback:** {ans['feedback']} {get_emoji(True)}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color:red'>❌ **Feedback:** {ans['feedback']} {get_emoji(False)}</span>", unsafe_allow_html=True)
                st.write("**Expected Query Result:**")
                if isinstance(ans["expected_result"], pd.DataFrame):
                    st.dataframe(ans["expected_result"])
                else:
                    st.write(ans["expected_result"])
                st.write("**Actual Query Result:**")
                if isinstance(ans["actual_result"], pd.DataFrame):
                    st.dataframe(ans["actual_result"])
                else:
                    st.write(ans["actual_result"])
                st.write("---")

# Quiz logic
if st.session_state.quiz_started:
    if not st.session_state.quiz_completed:
        progress = (st.session_state.current_question + 1) / len(sql_questions)
        st.progress(progress)
        st.write(f"**Progress:** {st.session_state.current_question + 1}/{len(sql_questions)} questions completed.")
        
        # Display the current question
        question_data = sql_questions[st.session_state.current_question]
        st.write(f"**Question {st.session_state.current_question + 1}:** {question_data['question']}")
        
        # Display sample table
        st.write("**Sample Table:**")
        st.dataframe(question_data["sample_table"])
        
        # Input for user's answer
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
                    st.markdown(f"<span style='color:green'>**Feedback:** {feedback} {get_emoji(True)}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color:red'>**Feedback:** {feedback} {get_emoji(False)}</span>", unsafe_allow_html=True)
                
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
        st.markdown(
            """
            <h1 style="color: white; font-size: 36px; text-align: left;">
                Quiz Completed!
            </h1>
            """,
            unsafe_allow_html=True
        )
        
        score = calculate_score(st.session_state.user_answers)
        st.write(f"**Your Score:** {score:.2f}%")
        
        if score < 50:
            st.markdown(
                """
                <div style="background-color: #ffcccc; padding: 20px; border-radius: 10px; text-align: center;">
                    <h2 style="color: #000000;">Your score is below 50% 😢</h2>
                    <p style="font-size: 18px; color: #000000;">Book a mentor now to upgrade your SQL skills!</p>
                    <a href="https://www.corporatebhaiya.com/" target="_blank">
                        <button style="background-color: #cc0000; color: white; padding: 10px 20px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer;">
                            Book Now
                        </button>
                    </a>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                """
                <div style="background-color: #ccffcc; padding: 20px; border-radius: 10px; text-align: center;">
                    <h2 style="color: #000000;">Great job scoring above 50%! 🎉</h2>
                    <p style="font-size: 18px; color: #000000;">Take the next step with a mock interview and resume building session!</p>
                    <a href="https://www.corporatebhaiya.com/" target="_blank">
                        <button style="background-color: #008000; color: white; padding: 10px 20px; border: none; border-radius: 5px; font-size: 16px; cursor: pointer;">
                            Book Now
                        </button>
                    </a>
                </div>
                """,
                unsafe_allow_html=True
            )
        
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
