import streamlit as st
import google.generativeai as genai
import pandas as pd
from datetime import datetime

# Configure page settings for a cleaner look
st.set_page_config(
    page_title="SQL Mentor Pro",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for an advanced, professional UI inspired by HackerRank
custom_css = """
<style>
    /* Clean up Streamlit elements */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .viewerBadge_container__1QSob {display: none !important;}
    .stDeployButton {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    [data-testid="stDeployButton"] {display: none !important;}
    
    /* Modern UI elements */
    .main {
        background-color: #0e1117;
        color: #e0e0e0;
        font-family: 'Inter', 'Segoe UI', sans-serif;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #1a1e29;
    }
    
    /* Typography */
    h1 {
        color: #39e991;
        font-size: 2.2rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
    }
    
    h2 {
        color: #39e991;
        font-size: 1.8rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    
    h3 {
        color: #e0e0e0;
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 0.75rem;
    }
    
    /* Card-style elements */
    .question-card {
        background-color: #1e2433;
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid #39e991;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .table-card {
        background-color: #1e2433;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .sidebar-card {
        background-color: #1e2433;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    /* Button styling */
    .stButton button {
        background-color: #39e991;
        color: #0e1117;
        font-weight: 600;
        border-radius: 4px;
        border: none;
        padding: 0.6rem 1.2rem;
        transition: all 0.2s;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    .stButton button:hover {
        background-color: #2fd67e;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        transform: translateY(-2px);
    }
    
    .secondary-button button {
        background-color: transparent;
        color: #39e991;
        border: 1px solid #39e991;
    }
    
    .secondary-button button:hover {
        background-color: rgba(57, 233, 145, 0.1);
    }
    
    /* Table styling */
    .dataframe {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        border: 1px solid #2d3748;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 1rem;
    }
    
    .dataframe th {
        background-color: #2d3748;
        color: #39e991;
        padding: 0.75rem 1rem;
        text-align: left;
        font-weight: 600;
        border-bottom: 1px solid #3e4c63;
    }
    
    .dataframe td {
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #2d3748;
        color: #e0e0e0;
    }
    
    .dataframe tr:nth-child(even) {
        background-color: #212736;
    }
    
    .dataframe tr:hover {
        background-color: #2a3344;
    }
    
    /* Code editor */
    .stTextInput > div > div > input {
        background-color: #1a1f2c;
        color: #e0e0e0;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        border: 1px solid #2d3748;
        border-radius: 4px;
        padding: 0.75rem;
        height: 100px;
        font-size: 14px;
    }
    
    .sql-editor {
        background-color: #1a1f2c;
        border: 1px solid #2d3748;
        border-radius: 4px;
        padding: 0;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        margin-bottom: 1rem;
    }
    
    .sql-editor-header {
        background-color: #2d3748;
        padding: 0.5rem 1rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: #e0e0e0;
        font-size: 0.85rem;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }
    
    /* Progress bar styling */
    .stProgress > div > div {
        background-color: #39e991;
        height: 0.5rem;
        border-radius: 4px;
    }
    
    .stProgress > div {
        background-color: #2d3748;
        height: 0.5rem;
        border-radius: 4px;
    }
    
    /* Feedback styling */
    .feedback-correct {
        background-color: rgba(52, 211, 153, 0.2);
        color: #34d399;
        padding: 1rem;
        border-radius: 4px;
        margin-top: 1rem;
        border-left: 4px solid #34d399;
    }
    
    .feedback-incorrect {
        background-color: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        padding: 1rem;
        border-radius: 4px;
        margin-top: 1rem;
        border-left: 4px solid #ef4444;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0;
        background-color: #1e2433;
        border-radius: 8px 8px 0 0;
        padding: 0 4px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #e0e0e0;
        padding: 0.75rem 1.25rem;
        border-radius: 0;
        border-bottom: 2px solid transparent;
        margin: 0;
        transition: all 0.2s;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: transparent;
        color: #39e991;
        border-bottom: 2px solid #39e991;
        font-weight: 600;
    }
    
    /* Custom components */
    .timer {
        background-color: #1e2433;
        color: #e0e0e0;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        display: inline-block;
        font-family: monospace;
        margin-bottom: 1rem;
    }
    
    .badge {
        display: inline-block;
        padding: 0.25rem 0.5rem;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    
    .badge-easy {
        background-color: #10b981;
        color: #ffffff;
    }
    
    .badge-medium {
        background-color: #f59e0b;
        color: #ffffff;
    }
    
    .badge-hard {
        background-color: #ef4444;
        color: #ffffff;
    }
    
    /* Expander */
    .stExpander {
        border: 1px solid #2d3748;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 1rem;
    }
    
    .stExpander > details > summary {
        background-color: #212736;
        padding: 1rem;
        font-weight: 600;
        color: #e0e0e0;
    }
    
    .stExpander > details > summary:hover {
        background-color: #2a3344;
    }
    
    .stExpander > details > div {
        padding: 1rem;
        background-color: #1e2433;
    }
    
    /* Tooltips */
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: pointer;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #2d3748;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 0.5rem;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    
    /* Status indicators */
    .status-circle {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 0.5rem;
    }
    
    .status-completed {
        background-color: #10b981;
    }
    
    .status-in-progress {
        background-color: #f59e0b;
    }
    
    .status-not-started {
        background-color: #6b7280;
    }
    
    /* Profile section */
    .profile-section {
        display: flex;
        align-items: center;
        padding: 1rem;
        background-color: #1e2433;
        border-radius: 8px;
        margin-bottom: 1.5rem;
    }
    
    .profile-avatar {
        width: 50px;
        height: 50px;
        border-radius: 50%;
        background-color: #39e991;
        color: #0e1117;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 1.25rem;
        margin-right: 1rem;
    }
    
    .profile-info h3 {
        margin: 0;
        font-size: 1.25rem;
    }
    
    .profile-info p {
        margin: 0;
        color: #9ca3af;
    }
    
    /* Leaderboard */
    .leaderboard {
        background-color: #1e2433;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 1.5rem;
    }
    
    .leaderboard-header {
        background-color: #2d3748;
        padding: 0.75rem 1rem;
        font-weight: 600;
        color: #e0e0e0;
    }
    
    .leaderboard-row {
        display: flex;
        align-items: center;
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #2d3748;
    }
    
    .leaderboard-rank {
        width: 40px;
        font-weight: 600;
    }
    
    .leaderboard-name {
        flex-grow: 1;
    }
    
    .leaderboard-score {
        font-weight: 600;
        color: #39e991;
    }
    
    /* Result table */
    .result-table th {
        background-color: #2d3748;
        color: #39e991;
        padding: 0.6rem 1rem;
        text-align: left;
    }
    
    .result-table td {
        padding: 0.6rem 1rem;
        border-bottom: 1px solid #2d3748;
    }
    
    /* Query information */
    .query-info {
        display: flex;
        justify-content: space-between;
        background-color: #212736;
        padding: 0.5rem 1rem;
        border-radius: 4px;
        margin-bottom: 1rem;
        font-size: 0.85rem;
        color: #9ca3af;
    }
    
    /* Query execution status */
    .execution-status {
        display: flex;
        align-items: center;
        margin-top: 0.5rem;
        font-size: 0.85rem;
    }
    
    .execution-time {
        margin-left: 0.5rem;
        color: #9ca3af;
    }
    
    /* Hide default Streamlit spinner */
    div.stSpinner > div {
        visibility: hidden;
        display: none;
    }
    
    /* Custom spinner */
    .custom-spinner {
        width: 40px;
        height: 40px;
        border: 4px solid rgba(57, 233, 145, 0.2);
        border-left-color: #39e991;
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Set up Gemini API
gemini_api_key = "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k"  # Replace with your Gemini API key
genai.configure(api_key=gemini_api_key)
model = genai.GenerativeModel('gemini-2.0-flash')

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

# Expanded SQL Questions list with difficulty levels and categories
sql_questions = [
    {
        "question": "Imagine you are the database guardian responsible for managing user data. Your task is to extract a complete snapshot of all users from the 'users' table. Write a SQL query that retrieves every column and every record so you can see all the details of each user.",
        "correct_answer": "SELECT * FROM users;",
        "sample_table": users_table,
        "difficulty": "easy",
        "category": "Basic Queries",
        "points": 10
    },
    {
        "question": "As part of your data analytics duties, you need to determine the total number of users in the system. Write a SQL query that counts all the records in the 'users' table, giving you a clear tally of registered users.",
        "correct_answer": "SELECT COUNT(*) FROM users;",
        "sample_table": users_table,
        "difficulty": "easy",
        "category": "Aggregate Functions",
        "points": 10
    },
    {
        "question": "You are tasked with segmenting our audience for targeted outreach. Write a SQL query that retrieves all user records from the 'users' table where the age is greater than 30, helping you identify users in a specific age bracket.",
        "correct_answer": "SELECT * FROM users WHERE age > 30;",
        "sample_table": users_table,
        "difficulty": "easy",
        "category": "Filtering",
        "points": 15
    },
    {
        "question": "In your role as an order processing specialist, you must quickly identify which orders are still pending. Write a SQL query that selects all records from the 'orders' table with a status of 'Pending' so that you can follow up promptly.",
        "correct_answer": "SELECT * FROM orders WHERE status = 'Pending';",
        "sample_table": orders_table,
        "difficulty": "easy",
        "category": "Filtering",
        "points": 15
    },
    {
        "question": "To ensure our order tracking is up-to-date, you need to find the most recent order placed. Write a SQL query that orders the 'orders' table by the order date in descending order and retrieves just the top record, highlighting the latest transaction.",
        "correct_answer": "SELECT * FROM orders ORDER BY order_date DESC LIMIT 1;",
        "sample_table": orders_table,
        "difficulty": "medium",
        "category": "Sorting and Limiting",
        "points": 20
    },
    {
        "question": "For financial analysis, it's important to understand customer spending behavior. Write a SQL query that calculates the average order amount from the 'orders' table, providing insights into typical purchase values.",
        "correct_answer": "SELECT AVG(amount) FROM orders;",
        "sample_table": orders_table,
        "difficulty": "medium",
        "category": "Aggregate Functions",
        "points": 20
    },
    {
        "question": "To better engage with inactive customers, you need to identify users who have never placed an order. Write a SQL query that retrieves all user records from the 'users' table which do not have any associated entries in the 'orders' table.",
        "correct_answer": "SELECT * FROM users WHERE user_id NOT IN (SELECT DISTINCT user_id FROM orders);",
        "sample_table": users_table,
        "difficulty": "hard",
        "category": "Subqueries",
        "points": 30
    },
    {
        "question": "For a comprehensive spending analysis, write a SQL query that calculates the total amount spent by each user. Join the 'users' and 'orders' tables, sum the order amounts per user, and display each user's name along with their total expenditure.",
        "correct_answer": ("SELECT users.name, SUM(orders.amount) AS total_spent FROM users "
                           "JOIN orders ON users.user_id = orders.user_id GROUP BY users.name;"),
        "sample_table": merged_table,
        "difficulty": "hard",
        "category": "Joins and Grouping",
        "points": 35
    },
    {
        "question": "Understanding customer engagement is key. Write a SQL query that counts the number of orders each user has placed. Use a LEFT JOIN between the 'users' and 'orders' tables and display the user's name along with their order count.",
        "correct_answer": ("SELECT users.name, COUNT(orders.order_id) AS order_count FROM users "
                           "LEFT JOIN orders ON users.user_id = orders.user_id GROUP BY users.name;"),
        "sample_table": merged_table,
        "difficulty": "hard",
        "category": "Joins and Grouping",
        "points": 40
    },
    {
        "question": "For targeted regional marketing, you need to focus on users from specific cities. Write a SQL query that retrieves all user records from the 'users' table where the city is either 'New York' or 'Chicago'.",
        "correct_answer": "SELECT * FROM users WHERE city IN ('New York', 'Chicago');",
        "sample_table": users_table,
        "difficulty": "medium",
        "category": "Filtering",
        "points": 25
    }
]

# Initialization of session state variables
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
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "question_start_time" not in st.session_state:
    st.session_state.question_start_time = None
if "username" not in st.session_state:
    st.session_state.username = ""
if "email" not in st.session_state:
    st.session_state.email = ""
if "registration_complete" not in st.session_state:
    st.session_state.registration_complete = False
if "show_hints" not in st.session_state:
    st.session_state.show_hints = False
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True
if "view_mode" not in st.session_state:
    st.session_state.view_mode = "split"
if "total_score" not in st.session_state:
    st.session_state.total_score = 0

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
                
                # Handle ORDER BY and LIMIT
                if "order by" in from_part:
                    order_part = from_part.split("order by")[1].strip()
                    if "limit" in order_part:
                        order_col = order_part.split("limit")[0].strip()
                        limit_val = int(order_part.split("limit")[1].strip())
                    else:
                        order_col = order_part
                        limit_val = None
                    
                    # Handle DESC
                    if "desc" in order_col:
                        order_col = order_col.replace("desc", "").strip()
                        result = result.sort_values(by=order_col, ascending=False)
                    else:
                        order_col = order_col.replace("asc", "").strip()
                        result = result.sort_values(by=order_col)
                    
                    if limit_val:
                        result = result.head(limit_val)
                
                return result.reset_index(drop=True)
            
            # Handle specific columns (not fully featured for complex queries)
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
    
    # Generate detailed, friendly feedback using Gemini API
    prompt = f"""
    Question: {question}
    Correct Answer: {correct_answer}
    Your Answer: {student_answer}
    Expected Query Result: {expected_result}
    Actual Query Result: {actual_result}
    
    You are a friendly SQL mentor. Please give constructive, encouraging feedback in Hindi with casual tone.
    If the answer is correct, start with "Shabash!" or "Bilkul sahi!". If incorrect, start with "Thoda sa galti hai" or "Koi baat nahi".
    Explain why the answer is correct or what could be improved, focusing on SQL concepts.
    Keep feedback under 3 sentences.
    """
    
    response = model.generate_content(prompt)
    feedback_api = response.text
    
    return feedback_api, is_correct, expected_result, actual_result

def calculate_score(user_answers):
    """Calculate the score based on correct answers and their difficulty."""
    total_points = 0
    for ans in user_answers:
        if ans["is_correct"]:
            total_points += ans["points"]
    return total_points

def analyze_performance(user_answers):
    """Analyze the user's performance and provide detailed feedback."""
    # Calculate areas of strength and weakness by category
    categories = {}
    for ans in user_answers:
        category = ans["category"]
        if category not in categories:
            categories[category] = {"total": 0, "correct": 0}
        
        categories[category]["total"] += 1
        if ans["is_correct"]:
            categories[category]["correct"] += 1
    
    # Generate category-based strengths and weaknesses
    strengths = [cat for cat, data in categories.items() if data["correct"]/data["total"] >= 0.7]
    weaknesses = [cat for cat, data in categories.items() if data["correct"]/data["total"] < 0.5]
    
    # Generate detailed feedback
    feedback = {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "category_performance": categories,
        "overall_feedback": ""
    }
    
    # Get personalized feedback from Gemini
    total_correct = sum(1 for ans in user_answers if ans["is_correct"])
    prompt = f"""
    The user completed a SQL quiz with {len(user_answers)} questions and got {total_correct} correct.
    Strengths in categories: {strengths}
    Weaknesses in categories: {weaknesses}
    
    Please provide a personalized, encouraging feedback in Hindi with a casual, friendly tone.
    Mention their strengths first, then areas for improvement, and end with motivation for future learning.
    Keep it under 5 sentences.
    """
    response = model.generate_content(prompt)
    feedback["overall_feedback"] = response.text
    
    return feedback

def get_badge_color(difficulty):
    if difficulty == "easy":
        return "badge-easy"
    elif difficulty == "medium":
        return "badge-medium"
    else:
        return "badge-hard"

def format_time(seconds):
    """Format seconds into mm:ss format."""
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def get_hint(question, correct_answer):
    """Generate a hint for the current question using Gemini API."""
    prompt = f"""
    For this SQL question: "{question}"
    The correct answer is: {correct_answer}
    
    Generate a helpful hint that guides the user in the right direction without giving away the answer.
    The hint should be one sentence only, in Hindi, with a casual, friendly tone.
    """
    
    response = model.generate_content(prompt)
    return response.text

# Registration Page
if not st.session_state.registration_complete:
    st.markdown('<h1 style="color:#39e991">SQL Mentor Pro - Interactive SQL Practice Platform</h1>', unsafe_allow_html=True)
    
    # Custom registration form with columns
    st.markdown('<div class="question-card">', unsafe_allow_html=True)
    st.markdown('<h2>Welcome to Your SQL Learning Journey!</h2>', unsafe
