import streamlit as st
import google.generativeai as genai
import pandas as pd
import re

# Custom CSS to hide Streamlit and GitHub elements
hide_streamlit_style = """
    <style>
        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .viewerBadge_container__1QSob {display: none !important;}
        .stDeployButton {display: none !important;}
        [data-testid="stToolbar"] {display: none !important;}
        [data-testid="stDecoration"] {display: none !important;}
        .st-emotion-cache-1r8d6ul {display: none !important;}
        .st-emotion-cache-1jicfl2 {display: none !important;}
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

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

# SQL Questions with expected results
sql_questions = [
    {
        "question": "Write a SQL query to get all details about users from the 'users' table.",
        "sample_table": users_table,
        "expected_result": users_table
    },
    {
        "question": "Write a SQL query to count the total number of users in the 'users' table.",
        "sample_table": users_table,
        "expected_result": pd.DataFrame({"count": [len(users_table)]})
    },
    {
        "question": "Write a SQL query to get all users older than 30 from the 'users' table.",
        "sample_table": users_table,
        "expected_result": users_table[users_table["age"] > 30].reset_index(drop=True)
    },
    {
        "question": "Write a SQL query to find all orders with a status of 'Pending' from the 'orders' table.",
        "sample_table": orders_table,
        "expected_result": orders_table[orders_table["status"] = "Pending"].reset_index(drop=True)
    },
    {
        "question": "Write a SQL query to find the most recent order from the 'orders' table by order date.",
        "sample_table": orders_table,
        "expected_result": orders_table.sort_values("order_date", ascending=False).head(1).reset_index(drop=True)
    },
    {
        "question": "Write a SQL query to find the average order amount from the 'orders' table.",
        "sample_table": orders_table,
        "expected_result": pd.DataFrame({"avg": [orders_table["amount"].mean()]})
    },
    {
        "question": "Write a SQL query to find users who have not placed any orders in the 'orders' table.",
        "sample_table": users_table,
        "expected_result": users_table[~users_table["user_id"].isin(orders_table["user_id"])].reset_index(drop=True)
    },
    {
        "question": "Write a SQL query to calculate the total amount spent by each user by joining the 'users' and 'orders' tables.",
        "sample_table": merged_table,
        "expected_result": merged_table.groupby("name")["amount"].sum().reset_index().rename(columns={"amount": "total_spent"})
    },
    {
        "question": "Write a SQL query to count how many orders each user has placed using a LEFT JOIN between 'users' and 'orders'.",
        "sample_table": merged_table,
        "expected_result": merged_table.groupby("name")["order_id"].count().reset_index().rename(columns={"order_id": "order_count"})
    },
    {
        "question": "Write a SQL query to find users from 'New York' or 'Chicago' in the 'users' table.",
        "sample_table": users_table,
        "expected_result": users_table[users_table["city"].isin(["New York", "Chicago"])].reset_index(drop=True)
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

def normalize_dataframe(df):
    """Normalize dataframe for comparison by sorting columns and values"""
    if isinstance(df, pd.DataFrame):
        return df.sort_values(by=df.columns.tolist()).reset_index(drop=True)
    return df


def simulate_query(query, sample_table):
    """Simulate SQL queries on pandas DataFrame with case-sensitive handling"""
    try:
        # Remove semicolons and clean whitespace (preserve case)
        query = re.sub(r'\s+', ' ', query.strip().replace(";", ""))
        
        # Handle WHERE clause quotes conversion (preserve case inside quotes)
        if "where" in query.lower():
            # Split query case-insensitively
            query_parts = re.split(r' where ', query, flags=re.IGNORECASE)
            where_part = query_parts[1] if len(query_parts) > 1 else ""
            
            # Convert double quotes to single quotes without changing case
            where_part = re.sub(r'"([^"]*)"', r"'\1'", where_part)
            query = query_parts[0] + " WHERE " + where_part

        # Case-insensitive parsing for SQL structure
        # SELECT clause
        select_match = re.match(r'^select\s+(.*?)\s+from\s+', query, re.IGNORECASE)
        if select_match:
            select_part = select_match.group(1).strip()
            from_part = query[select_match.end():].split('WHERE')[0].strip()
            
            # Handle aggregations (case-sensitive column names)
            agg_map = {
                r'count\(\*\)': lambda df: pd.DataFrame({"count": [len(df)]}),
                r'avg\(amount\)': lambda df: pd.DataFrame({"avg": [df["amount"].mean()]}),
                r'sum\(amount\)': lambda df: pd.DataFrame({"sum": [df["amount"].sum()]})
            }
            
            for agg_pattern, agg_func in agg_map.items():
                if re.search(agg_pattern, select_part, re.IGNORECASE):
                    return agg_func(sample_table)
            
            # Handle WHERE clauses (case-sensitive values)
            where_condition = ""
            if 'WHERE' in query.upper():
                where_condition = re.split(r' where ', query, flags=re.IGNORECASE)[1]
                try:
                    filtered_df = sample_table.query(where_condition)
                except Exception as e:
                    return f"Error in WHERE condition: {str(e)}"
            else:
                filtered_df = sample_table.copy()
            
            # Handle column selection (case-sensitive)
            if "*" in select_part:
                result_df = filtered_df
            else:
                columns = [col.strip() for col in select_part.split(",")]
                result_df = filtered_df[columns]
            
            # Handle ORDER BY (case-sensitive column names)
            if 'ORDER BY' in query.upper():
                order_part = re.split(r' order by ', query, flags=re.IGNORECASE)[1]
                order_col = re.split(r'\s+', order_part)[0].strip()
                direction = 'desc' if 'desc' in order_part.lower() else 'asc'
                limit = int(re.search(r'limit (\d+)', query).group(1)) if 'limit' in query.lower() else None
                result_df = result_df.sort_values(order_col, ascending=(direction == 'asc'))
                if limit:
                    result_df = result_df.head(limit)
            
            return result_df.reset_index(drop=True)
        
        return "Unsupported query type"
    
    except Exception as e:
        return f"Error simulating query: {str(e)}"

def evaluate_answer(question, expected_result, student_answer, sample_table):
    """Evaluate answer using result comparison and LLM analysis"""
    actual_result = simulate_query(student_answer, sample_table)
    
    # Normalize results for comparison
    norm_expected = normalize_dataframe(expected_result)
    norm_actual = normalize_dataframe(actual_result)
    
    try:
        is_correct = norm_expected.equals(norm_actual) if isinstance(norm_actual, pd.DataFrame) else str(expected_result) == str(actual_result)
    except:
        is_correct = False
    
    # Generate LLM feedback
    prompt = f"""
    SQL Question: {question}
    User's Answer: {student_answer}
    Expected Result: {expected_result}
    Actual Result: {actual_result}

    Provide detailed feedback in casual Hindi. Explain:
    1. If the answer is correct based on results
    2. What works well in the answer
    3. Any errors or improvements needed
    4. Alternative approaches if applicable
    Use friendly emojis and keep it under 150 words.
    Format: Start with "Bhaiya/Bhen! " if correct, "Arre Yaar! " if incorrect
    """
    
    response = model.generate_content(prompt)
    feedback = response.text.replace("**", "").replace("`", "")
    
    return feedback, is_correct, expected_result, actual_result

def calculate_score(user_answers):
    """Calculate the score based on correct answers"""
    correct_answers = sum(1 for ans in user_answers if ans["is_correct"])
    return (correct_answers / len(user_answers)) * 100

def analyze_performance(user_answers):
    """Analyze user performance and generate feedback"""
    correct = [ans["question"] for ans in user_answers if ans["is_correct"]]
    incorrect = [ans["question"] for ans in user_answers if not ans["is_correct"]]
    
    prompt = f"""
    User scored {len(correct)}/{len(user_answers)}.
    Correct Questions: {correct}
    Incorrect Questions: {incorrect}
    Generate friendly Hindi performance analysis with emojis.
    Highlight strengths and areas needing improvement.
    """
    response = model.generate_content(prompt)
    return response.text

def get_emoji(is_correct):
    return "✅" if is_correct else "❌"

# Streamlit UI Implementation
if not st.session_state.quiz_started:
    st.title("SQL Mentor - Interactive SQL Query Practice")
    
    st.write("### Welcome to Your SQL Learning Journey!")
    
    st.markdown("""
    **📌 Important Note:**
    - This quiz uses **MySQL syntax** for all SQL queries.
    - Ensure your answers follow MySQL conventions.
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
                    st.markdown(f"<span style='color:green'>✅ **Feedback:** {ans['feedback']}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color:red'>❌ **Feedback:** {ans['feedback']}</span>", unsafe_allow_html=True)
                st.write("**Expected Result:**")
                if isinstance(ans["expected_result"], pd.DataFrame):
                    st.dataframe(ans["expected_result"])
                else:
                    st.write(ans["expected_result"])
                st.write("**Actual Result:**")
                if isinstance(ans["actual_result"], pd.DataFrame):
                    st.dataframe(ans["actual_result"])
                else:
                    st.write(ans["actual_result"])
                st.write("---")
    
    # Get current question data
    current_index = st.session_state.current_question
    question_data = sql_questions[current_index]
    
    # Progress display
    progress = (current_index + 1) / len(sql_questions)
    st.progress(progress)
    st.write(f"**Progress:** {current_index + 1}/{len(sql_questions)} questions")
    
    # Question display
    st.write(f"**Question {current_index + 1}:** {question_data['question']}")
    st.write("**Sample Table:**")
    st.dataframe(question_data["sample_table"])
    
    # Answer input
    student_answer = st.text_input("Your SQL query:", key=f"answer_{current_index}")
    
    if st.button("Submit Answer"):
        if student_answer.strip():
            # Evaluate answer
            feedback, is_correct, expected, actual = evaluate_answer(
                question_data["question"],
                question_data["expected_result"],
                student_answer,
                question_data["sample_table"]
            )
            
            # Store answer
            st.session_state.user_answers.append({
                "question": question_data["question"],
                "student_answer": student_answer,
                "feedback": feedback,
                "is_correct": is_correct,
                "expected_result": expected,
                "actual_result": actual
            })
            
            # Move to next question or finish
            if current_index < len(sql_questions) - 1:
                st.session_state.current_question += 1
            else:
                st.session_state.awaiting_final_submission = True
            st.rerun()
        else:
            st.warning("Please enter an answer before submitting.")

if st.session_state.awaiting_final_submission:
    st.session_state.quiz_completed = True
    st.rerun()

if st.session_state.quiz_completed:
    st.balloons()
    st.markdown("<h1 style='text-align: left; color: #2e86c1;'>Quiz Completed! 🎉</h1>", unsafe_allow_html=True)
    
    # Calculate score
    score = calculate_score(st.session_state.user_answers)
    st.write(f"**Your Score:** {score:.2f}%")
    
    # Performance banner
    if score < 50:
        st.markdown("""
        <div style='background-color: #f8d7da; padding: 20px; border-radius: 10px;'>
            <h3 style='color: #721c24;'>Need Improvement 😢</h3>
            <p>Book a mentor session to boost your SQL skills!</p>
            <a href='https://www.corporatebhaiya.com/' target='_blank'>
                <button style='background-color: #dc3545; color: white; padding: 10px 20px; border: none; border-radius: 5px;'>
                    Book Mentor Session
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background-color: #d4edda; padding: 20px; border-radius: 10px;'>
            <h3 style='color: #155724;'>Great Job! 🚀</h3>
            <p>Practice more with advanced challenges!</p>
            <a href='https://www.corporatebhaiya.com/' target='_blank'>
                <button style='background-color: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 5px;'>
                    Advanced Exercises
                </button>
            </a>
        </div>
        """, unsafe_allow_html=True)
    
    # Detailed feedback
    if st.button("📊 Show Detailed Analysis"):
        performance_feedback = analyze_performance(st.session_state.user_answers)
        st.write("### Performance Breakdown")
        st.write(performance_feedback)
    
    # Restart option
    if st.button("🔄 Take Quiz Again"):
        st.session_state.user_answers = []
        st.session_state.current_question = 0
        st.session_state.quiz_started = False
        st.session_state.quiz_completed = False
        st.session_state.show_detailed_feedback = False
        st.session_state.awaiting_final_submission = False
        st.rerun()
