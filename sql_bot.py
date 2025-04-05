import re
import streamlit as st
import google.generativeai as genai
import pandas as pd

# Custom CSS to hide Streamlit and GitHub elements
hide_streamlit_style = """
    <style>
        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .viewerBadge_container__1QSob {display: none !important;}  /* Hides the GitHub profile image */
        .stDeployButton {display: none !important;} /* Hides deploy button */
        [data-testid="stToolbar"] {display: none !important;} /* Hides Streamlit toolbar */
        [data-testid="stDecoration"] {display: none !important;} /* Hides Streamlit branding */
        [data-testid="stDeployButton"] {display: none !important;} /* Hides Streamlit deploy button */
        .st-emotion-cache-1r8d6ul {display: none !important;} /* Additional class for profile image */
        .st-emotion-cache-1jicfl2 {display: none !important;} /* Hides Streamlit's footer */
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# Set up Gemini API
gemini_api_key = "YOUR_GEMINI_API_KEY"  # Replace with your Gemini API key
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

# Define sample tables for the quiz

# Users Table
users_table = pd.DataFrame({
    "user_id": [1, 2, 3, 4],
    "name": ["Alice", "Bob", "Charlie", "David"],
    "email": ["alice@example.com", "bob@example.com", "charlie@example.com", "david@example.com"],
    "age": [25, 30, 35, 40],
    "city": ["New York", "Los Angeles", "Chicago", "Houston"]
})

# Orders Table
orders_table = pd.DataFrame({
    "order_id": [101, 102, 103, 104, 105],
    "user_id": [1, 2, 3, 1, 4],
    "amount": [50.00, 75.50, 120.00, 200.00, 35.00],
    "order_date": ["2024-02-01", "2024-02-05", "2024-02-10", "2024-02-15", "2024-02-20"],
    "status": ["Completed", "Pending", "Completed", "Shipped", "Cancelled"]
})

# Create a merged table for join-based queries
merged_table = pd.merge(users_table, orders_table, on="user_id", how="inner")

# Updated SQL Questions list (no restriction on quotes)
sql_questions = [
    {
        "question": "Write a SQL query to get all details about users from the 'users' table.",
        "correct_answer": "SELECT * FROM users;",
        "sample_table": users_table
    },
    {
        "question": "Write a SQL query to count the total number of users in the 'users' table.",
        "correct_answer": "SELECT COUNT(*) FROM users;",
        "sample_table": users_table
    },
    {
        "question": "Write a SQL query to get all users older than 30 from the 'users' table.",
        "correct_answer": "SELECT * FROM users WHERE age > 30;",
        "sample_table": users_table
    },
    {
        "question": "Write a SQL query to find all orders with a status of 'Pending' from the 'orders' table.",
        "correct_answer": "SELECT * FROM orders WHERE status = 'Pending';",
        "sample_table": orders_table
    },
    {
        "question": "Write a SQL query to find the most recent order from the 'orders' table by order date.",
        "correct_answer": "SELECT * FROM orders ORDER BY order_date DESC LIMIT 1;",
        "sample_table": orders_table
    },
    {
        "question": "Write a SQL query to find the average order amount from the 'orders' table.",
        "correct_answer": "SELECT AVG(amount) FROM orders;",
        "sample_table": orders_table
    },
    {
        "question": "Write a SQL query to find users who have not placed any orders in the 'orders' table.",
        "correct_answer": "SELECT * FROM users WHERE user_id NOT IN (SELECT DISTINCT user_id FROM orders);",
        "sample_table": users_table
    },
    {
        "question": "Write a SQL query to calculate the total amount spent by each user by joining the 'users' and 'orders' tables.",
        "correct_answer": (
            "SELECT users.name, SUM(orders.amount) AS total_spent FROM users "
            "JOIN orders ON users.user_id = orders.user_id GROUP BY users.name;"
        ),
        "sample_table": merged_table
    },
    {
        "question": "Write a SQL query to count how many orders each user has placed using a LEFT JOIN between 'users' and 'orders'.",
        "correct_answer": (
            "SELECT users.name, COUNT(orders.order_id) AS order_count FROM users "
            "LEFT JOIN orders ON users.user_id = orders.user_id GROUP BY users.name;"
        ),
        "sample_table": merged_table
    },
    {
        "question": "Write a SQL query to find users from 'New York' or 'Chicago' in the 'users' table.",
        "correct_answer": "SELECT * FROM users WHERE city IN ('New York', 'Chicago');",
        "sample_table": users_table
    }
]

# Initialize session state variables
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
        # Check that essential keywords exist
        lower_q = query.lower()
        if "select" not in lower_q or "from" not in lower_q:
            return "Invalid query: missing SELECT or FROM"
        
        # Remove trailing semicolon and extra whitespace (preserving literal case)
        query = query.strip().replace(";", "")
        
        # Split into parts using case-insensitive search for keywords
        select_lower = query.lower().split("select", 1)[1]
        select_part = select_lower.split("from", 1)[0].strip()
        from_part = query.split("from", 1)[1].strip()  # preserve literal casing

        # Handle COUNT(*)
        if "count(*)" in select_part:
            result = pd.DataFrame({"count": [len(sample_table)]})
            return result.reset_index(drop=True)
        
        # Handle AVG(column)
        elif "avg(" in select_part:
            column = query.split("avg(", 1)[1].split(")", 1)[0].strip()
            result = pd.DataFrame({"avg": [sample_table[column].mean()]})
            return result.reset_index(drop=True)
        
        # Handle SUM(column)
        elif "sum(" in select_part:
            column = query.split("sum(", 1)[1].split(")", 1)[0].strip()
            result = pd.DataFrame({"sum": [sample_table[column].sum()]})
            return result.reset_index(drop=True)
        
        # Handle SELECT * (all columns)
        elif "*" in select_part:
            if "where" in from_part.lower():
                # Extract the WHERE condition preserving original case
                condition = query.split("where", 1)[1].strip()
                # Normalize quotes: convert double quotes to single quotes
                condition = condition.replace("\"", "'")
                # Replace '=' with '==' using regex (only single '=' not part of '==' or '!=')
                condition = re.sub(r'(?<![=!])=(?![=])', '==', condition)
                result = sample_table.query(condition)
            else:
                result = sample_table.copy()
            return result.reset_index(drop=True)
        
        # Handle specific columns (simplified; not for complex queries)
        else:
            columns = [col.strip() for col in select_part.split(",")]
            if "where" in from_part.lower():
                condition = query.split("where", 1)[1].strip()
                condition = condition.replace("\"", "'")
                condition = re.sub(r'(?<![=!])=(?![=])', '==', condition)
                result = sample_table.query(condition)[columns]
            else:
                result = sample_table[columns]
            return result.reset_index(drop=True)
    except Exception as e:
        return f"Error simulating query: {str(e)}"

def evaluate_answer(question, correct_answer, student_answer, sample_table):
    """Evaluate the user's answer using Gemini API and simulate the query."""
    expected_result = simulate_query(correct_answer, sample_table)
    actual_result = simulate_query(student_answer, sample_table)
    
    # Reset indexes for proper DataFrame comparison (if applicable)
    if isinstance(expected_result, pd.DataFrame):
        expected_result = expected_result.reset_index(drop=True)
    if isinstance(actual_result, pd.DataFrame):
        actual_result = actual_result.reset_index(drop=True)
    
    # Compare results using DataFrame equality if possible
    if isinstance(expected_result, pd.DataFrame) and isinstance(actual_result, pd.DataFrame):
        is_correct = expected_result.equals(actual_result)
    else:
        is_correct = str(expected_result) == str(actual_result)
    
    # Prepare verdict flag for the LLM prompt
    correctness_text = "Yes" if is_correct else "No"
    
    # Build the prompt for Gemini API with the verdict included
    prompt = f"""
    Question: {question}
    Correct Answer: {correct_answer}
    Your Answer: {student_answer}
    Expected Query Result: {expected_result}
    Actual Query Result: {actual_result}
    Is Correct? {correctness_text}

    Ab ek dost ke andaaz mein Hindi mein feedback dein. Agar aapka jawab sahi hai, toh kuch aise kehna: "Wah yaar, zabardast jawab diya!" Aur agar jawab galat hai, toh casually bolna: "Arre yaar, thoda gadbad ho gaya, koi baat nahi, agli baar aur accha karna." Thoda detail mein bhi batana ki kya chuk hua ya sahi kyu hai.
    """
    response = model.generate_content(prompt)
    feedback_api = response.text.replace("student", "aap")
    
    return feedback_api, is_correct, expected_result, actual_result

def calculate_score(user_answers):
    """Calculate the score based on correct answers."""
    correct_answers = sum(1 for ans in user_answers if ans["is_correct"])
    total_questions = len(user_answers)
    return (correct_answers / total_questions) * 100

def analyze_performance(user_answers):
    """Analyze the user's performance and provide detailed feedback."""
    correct_questions = [ans["question"] for ans in user_answers if ans["is_correct"]]
    incorrect_questions = [ans["question"] for ans in user_answers if not ans["is_correct"]]
    
    feedback = {
        "strengths": correct_questions,
        "weaknesses": incorrect_questions,
        "overall_feedback": ""
    }
    
    prompt = f"""
    Aapne {len(user_answers)} mein se {len(correct_questions)} sawalon ka sahi jawab diya.
    Sahi jawab wale sawal: {correct_questions}
    Galat jawab wale sawal: {incorrect_questions}
    Ab ek dost ke tarah casual Hindi mein overall performance ka feedback dein.
    """
    response = model.generate_content(prompt)
    feedback["overall_feedback"] = response.text
    
    return feedback

def get_emoji(is_correct):
    return "😊" if is_correct else "😢"

# Streamlit App UI
if not st.session_state.quiz_started:
    st.title("SQL Mentor - Interactive SQL Query Practice")
    st.write("### Welcome to Your SQL Learning Journey!")
    
    st.markdown("""
    **📌 Important Note:**
    - This quiz uses **MySQL syntax** for all SQL queries.
    - You may use single or double quotes for string literals.
    """)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("""
        In this interactive SQL quiz, you'll work with two main tables:
        - **Users Table**: Contains user details such as ID, name, email, age, and city.
        - **Orders Table**: Stores order details including order ID, user ID, amount, order date, and status.
        """)
    with col2:
        st.markdown("#### Tables Overview")
        table_overview = pd.DataFrame({
            "Table": ["Users", "Orders"],
            "Rows": [len(users_table), len(orders_table)]
        })
        st.table(table_overview)
    
    st.write("### 🔍 Table Previews")
    tab1, tab2 = st.tabs(["Users", "Orders"])
    with tab1:
        st.write("**Users Table**")
        st.dataframe(users_table)
    with tab2:
        st.write("**Orders Table**")
        st.dataframe(orders_table)
    
    with st.expander("📝 About This Quiz"):
        st.write("""
        - You will solve 10 progressive SQL query challenges.
        - Each question tests a different SQL concept.
        - Immediate feedback is provided after each answer.
        - Your final score and detailed performance analysis will be shown at the end.
        - **SQL Dialect:** MySQL
        """)
    
    if st.button("🚀 Start SQL Challenge"):
        st.session_state.quiz_started = True
        st.rerun()

if st.session_state.quiz_started and not st.session_state.quiz_completed:
    if st.session_state.user_answers:
        st.write("### Chat History")
        for i, ans in enumerate(st.session_state.user_answers):
            with st.expander(f"Question {i + 1}: {ans['question']}", expanded=True):
                st.write(f"**Your Answer:** {ans['student_answer']}")
                if ans["is_correct"]:
                    st.markdown(
                        f"<span style='color:green'>✅ **Feedback:** {ans['feedback']} {get_emoji(True)}</span>",
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f"<span style='color:red'>❌ **Feedback:** {ans['feedback']} {get_emoji(False)}</span>",
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
                st.markdown(
                    f"<span style='color:green'>**Feedback:** {feedback} {get_emoji(True)}</span>",
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"<span style='color:red'>**Feedback:** {feedback} {get_emoji(False)}</span>",
                    unsafe_allow_html=True
                )
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

if st.session_state.quiz_completed:
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
