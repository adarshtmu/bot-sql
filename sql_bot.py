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

import streamlit as st
import google.generativeai as genai
import pandas as pd

# ✅ Must be the first Streamlit command in the script
st.set_page_config(
    page_title="SQL Mentor - Interactive SQL Query Practice",
    page_icon=":bar_chart:",
    layout="wide"
)

# Now you can safely do other Streamlit operations
hide_github = """
    <style>
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_github, unsafe_allow_html=True)
# Define a custom CSS style to enhance the UI
custom_css = """
<style>
/* Gradient background */
body {
    background: linear-gradient(to right, #1e3c72, #2a5298);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: #fff;
}

/* Hide the default Streamlit header and footer */
header, footer {
    visibility: hidden;
}

/* Custom container with dark background and rounded corners */
.section {
    background-color: rgba(0, 0, 0, 0.3);
    padding: 2rem;
    margin-bottom: 2rem;
    border-radius: 10px;
}

/* Headings */
h1, h2, h3, h4 {
    color: #ffd700; /* Gold color for contrast */
    margin-top: 0;
}

/* Table styles */
table {
    color: #000;
    background-color: #fff;
    border-radius: 5px;
    overflow: hidden;
}
thead tr {
    background-color: #c9d1d9 !important;
}
tbody tr:nth-child(even) {
    background-color: #f6f8fa;
}

/* Button styles */
button {
    background-color: #ffd700 !important;
    color: #000 !important;
    border-radius: 5px !important;
    border: none !important;
    font-weight: bold !important;
    padding: 0.6rem 1rem !important;
    cursor: pointer !important;
}
button:hover {
    background-color: #ffbf00 !important;
}

/* Progress bar override */
[data-testid="stProgress"] > div > div > div > div {
    background-image: linear-gradient(to right, #ffd700 , #ffc107);
}

/* Expander styling */
.streamlit-expanderHeader {
    font-weight: bold;
    color: #ffd700;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ----- SET UP GEMINI API -----
gemini_api_key = "REPLACE_WITH_YOUR_GEMINI_API_KEY"
genai.configure(api_key=gemini_api_key)
# NOTE: Make sure you use a valid model name from the Gemini ListModels, e.g., 'chat-bison-001' or similar
model = genai.GenerativeModel("chat-bison-001")  

# ----- SAMPLE DATA -----
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

# ----- STATE INITIALIZATION -----
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

# ----- HELPER FUNCTIONS -----
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
                return pd.DataFrame({"count": [len(sample_table)]}).reset_index(drop=True)
            
            # Handle AVG(column)
            elif "avg(" in select_part:
                column = select_part.split("avg(")[1].split(")")[0].strip()
                return pd.DataFrame({"avg": [sample_table[column].mean()]}).reset_index(drop=True)
            
            # Handle SUM(column)
            elif "sum(" in select_part:
                column = select_part.split("sum(")[1].split(")")[0].strip()
                return pd.DataFrame({"sum": [sample_table[column].sum()]}).reset_index(drop=True)
            
            # Handle SELECT * (all columns)
            elif "*" in select_part:
                if "where" in from_part:
                    condition = from_part.split("where")[1].strip()
                    condition = condition.replace("=", "==")
                    result = sample_table.query(condition)
                else:
                    result = sample_table.copy()
                return result.reset_index(drop=True)
            
            # Handle specific columns
            else:
                columns = [col.strip() for col in select_part.split(",")]
                if "where" in from_part:
                    condition = from_part.split("where")[1].strip()
                    condition = condition.replace("=", "==")
                    result = sample_table.query(condition)[columns]
                else:
                    result = sample_table[columns]
                return result.reset_index(drop=True)
        
        else:
            return "Query simulation is only supported for SELECT statements."
    
    except Exception as e:
        return f"Error simulating query: {str(e)}"

def evaluate_answer(question, correct_answer, student_answer, sample_table):
    """Evaluate the user's answer using Gemini API and simulate the query."""
    # Simulate the expected query (correct answer)
    expected_result = simulate_query(correct_answer, sample_table)
    
    # Simulate the actual query (user's answer)
    actual_result = simulate_query(student_answer, sample_table)
    
    # Determine correctness
    if isinstance(expected_result, pd.DataFrame) and isinstance(actual_result, pd.DataFrame):
        is_correct = expected_result.equals(actual_result)
    else:
        is_correct = str(expected_result) == str(actual_result)
    
    # Provide a short default feedback
    if is_correct:
        feedback = "Correct answer! Well done."
    else:
        feedback = f"Incorrect answer. Expected result was:\n{expected_result}"
    
    # Evaluate using Gemini (replace 'student' with 'you' in the output)
    prompt = f"""
    Question: {question}
    Correct Answer: {correct_answer}
    Your Answer: {student_answer}
    Expected Query Result: {expected_result}
    Actual Query Result: {actual_result}
    Evaluate your answer and provide feedback. Mention if the answer is correct or incorrect, and explain why.
    """
    try:
        response = model.generate_content(prompt)
        feedback_api = response.text
        feedback_api = feedback_api.replace("student", "you")
    except Exception as e:
        # If Gemini call fails, fall back to default feedback
        feedback_api = f"{feedback}\n\n[Gemini API Error: {e}]"
    
    return feedback_api, is_correct, expected_result, actual_result

def calculate_score(user_answers):
    correct_answers = sum(1 for ans in user_answers if ans["is_correct"])
    total_questions = len(user_answers)
    return (correct_answers / total_questions) * 100

def analyze_performance(user_answers):
    correct_questions = [ans["question"] for ans in user_answers if ans["is_correct"]]
    incorrect_questions = [ans["question"] for ans in user_answers if not ans["is_correct"]]
    
    feedback = {
        "strengths": correct_questions,
        "weaknesses": incorrect_questions,
        "overall_feedback": ""
    }
    
    prompt = f"""
    You answered {len(correct_questions)} out of {len(user_answers)} questions correctly.
    Correct Questions: {correct_questions}
    Incorrect Questions: {incorrect_questions}
    Provide detailed feedback on your overall performance, including areas of strength and weakness.
    """
    try:
        response = model.generate_content(prompt)
        feedback["overall_feedback"] = response.text
    except Exception as e:
        feedback["overall_feedback"] = f"[Gemini API Error: {e}]"
    
    return feedback

def get_emoji(is_correct):
    return "😊" if is_correct else "😢"

# ----- MAIN LAYOUT -----
# Wrap the main sections in "section" containers for a nicer look

if not st.session_state.quiz_started:
    with st.container():
        st.markdown("<h1 style='text-align: center;'>SQL Mentor - Interactive SQL Query Practice</h1>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div class='section'>", unsafe_allow_html=True)
        st.write("### Welcome to Your SQL Learning Journey!")
        st.markdown(
            """
            **Important Note:**
            - This quiz uses **MySQL** conventions for all SQL queries.
            - Ensure your answers follow MySQL syntax (e.g., `LIMIT` for row limits, etc.).
            - If you're familiar with other SQL dialects, some syntax may differ.
            """,
            unsafe_allow_html=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='section'>", unsafe_allow_html=True)
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(
                """
                In this interactive SQL quiz, you'll work with two interconnected tables:
                - **Employees Table**: Tracks employee details (ID, name, department, salary, manager).
                - **Departments Table**: Contains department locations.
                """
            )
        with col2:
            st.markdown("#### Tables Overview")
            table_overview = pd.DataFrame({
                "Table": ["Employees", "Departments"],
                "Rows": [len(employees_table), len(departments_table)]
            })
            st.table(table_overview)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Table Previews
    with st.container():
        st.markdown("<div class='section'>", unsafe_allow_html=True)
        st.write("### 🔍 Table Previews")
        tab1, tab2 = st.tabs(["Employees", "Departments"])
        with tab1:
            st.write("**Employees Table**")
            st.dataframe(employees_table)
        with tab2:
            st.write("**Departments Table**")
            st.dataframe(departments_table)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # About This Quiz
    with st.container():
        st.markdown("<div class='section'>", unsafe_allow_html=True)
        with st.expander("📝 About This Quiz"):
            st.write("""
            - You'll solve several SQL query challenges.
            - Each question tests a different SQL concept.
            - Immediate feedback after each answer.
            - Final score and detailed performance analysis.
            - **SQL Dialect:** MySQL
            """)
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Start Quiz
    with st.container():
        if st.button("🚀 Start SQL Challenge"):
            st.session_state.quiz_started = True
            st.experimental_rerun()

# Quiz in progress
if st.session_state.quiz_started and not st.session_state.quiz_completed:
    with st.container():
        st.markdown("<div class='section'>", unsafe_allow_html=True)
        # Display chat history
        if st.session_state.user_answers:
            st.write("### Chat History")
            for i, ans in enumerate(st.session_state.user_answers):
                with st.expander(f"Question {i + 1}: {ans['question']}", expanded=True):
                    st.write(f"**Your Answer:** {ans['student_answer']}")
                    if ans["is_correct"]:
                        st.markdown(
                            f"<span style='color:lightgreen'>✅ **Feedback:** {ans['feedback']} {get_emoji(True)}</span>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"<span style='color:salmon'>❌ **Feedback:** {ans['feedback']} {get_emoji(False)}</span>",
                            unsafe_allow_html=True
                        )
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
        st.markdown("</div>", unsafe_allow_html=True)

    with st.container():
        st.markdown("<div class='section'>", unsafe_allow_html=True)
        progress = (st.session_state.current_question + 1) / len(sql_questions)
        st.progress(progress)
        st.write(f"**Progress:** {st.session_state.current_question + 1}/{len(sql_questions)} questions completed.")
        
        # Display current question
        question_data = sql_questions[st.session_state.current_question]
        st.write(f"**Question {st.session_state.current_question + 1}:** {question_data['question']}")
        
        st.write("**Sample Table:**")
        st.dataframe(question_data["sample_table"])
        
        # Answer input
        student_answer = st.text_input("Your answer:", key=f"answer_{st.session_state.current_question}")
        
        # Submit answer
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
                
                # Show immediate feedback
                if is_correct:
                    st.markdown(f"<span style='color:lightgreen'>**Feedback:** {feedback} {get_emoji(True)}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color:salmon'>**Feedback:** {feedback} {get_emoji(False)}</span>", unsafe_allow_html=True)
                
                # Move to next question or await final submission
                if st.session_state.current_question < len(sql_questions) - 1:
                    st.session_state.current_question += 1
                    st.experimental_rerun()
                else:
                    st.session_state.awaiting_final_submission = True
                    st.experimental_rerun()
            else:
                st.warning("Please enter an answer before submitting.")
        
        # Final submission
        if st.session_state.awaiting_final_submission:
            if st.button("Submit All Answers"):
                st.session_state.quiz_completed = True
                st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# Quiz completed
if st.session_state.quiz_completed:
    with st.container():
        st.markdown("<div class='section'>", unsafe_allow_html=True)
        st.balloons()
        st.markdown("<h1>Quiz Completed!</h1>", unsafe_allow_html=True)
        
        score = calculate_score(st.session_state.user_answers)
        st.write(f"**Your Score:** {score:.2f}%")
        
        if score < 50:
            st.markdown(
                """
                <div style="background-color: #ffcccc; padding: 20px; border-radius: 10px; text-align: center;">
                    <h2 style="color: #000000;">Your score is below 50% 😢</h2>
                    <p style="font-size: 18px; color: #000000;">Book a mentor now to upgrade your SQL skills!</p>
                    <a href="https://www.corporatebhaiya.com/" target="_blank">
                        <button>Book Now</button>
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
                        <button>Book Now</button>
                    </a>
                </div>
                """,
                unsafe_allow_html=True
            )
        
        if st.button("📊 Detailed Feedback"):
            st.session_state.show_detailed_feedback = True
            st.experimental_rerun()
        
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
            st.experimental_rerun()
        st.markdown("</div>", unsafe_allow_html=True)
