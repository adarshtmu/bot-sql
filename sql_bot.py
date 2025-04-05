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

# Updated SQL Questions with expected results
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
        "expected_result": orders_table[orders_table["status"] == "Pending"].reset_index(drop=True)
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

def normalize_dataframe(df):
    """Normalize dataframe for comparison by sorting columns and values"""
    if isinstance(df, pd.DataFrame):
        return df.sort_values(by=df.columns.tolist()).reset_index(drop=True)
    return df

def simulate_query(query, sample_table):
    """Simulate SQL queries on pandas DataFrame with enhanced handling"""
    try:
        query = re.sub(r'\s+', ' ', query.strip().lower().replace(";", ""))
        
        # Basic SELECT query parsing
        if query.startswith("select"):
            select_part = query.split("from")[0].replace("select", "").strip()
            from_part = query.split("from")[1].split("where")[0].strip() if "where" in query else query.split("from")[1].strip()
            
            # Handle aggregations
            agg_map = {
                "count(*)": lambda df: pd.DataFrame({"count": [len(df)]}),
                "avg(amount)": lambda df: pd.DataFrame({"avg": [df["amount"].mean()]}),
                "sum(amount)": lambda df: pd.DataFrame({"sum": [df["amount"].sum()]})
            }
            
            for agg_key, agg_func in agg_map.items():
                if agg_key in select_part:
                    return agg_func(sample_table)
            
            # Handle WHERE clauses
            if "where" in query:
                where_condition = query.split("where")[1].strip()
                where_condition = where_condition.replace("=", "==").replace("!=", "!").replace("''", "'")
                try:
                    filtered_df = sample_table.query(where_condition)
                except:
                    return f"Error in WHERE condition: {where_condition}"
            else:
                filtered_df = sample_table.copy()
            
            # Handle column selection
            if "*" in select_part:
                return filtered_df
            else:
                columns = [col.strip() for col in select_part.split(",")]
                return filtered_df[columns]
        
        # Handle ORDER BY with LIMIT
        if "order by" in query:
            order_part = query.split("order by")[1]
            column = order_part.split()[0].strip()
            direction = "ascending" if "desc" in order_part.lower() else "ascending"
            limit = int(re.search(r"limit (\d+)", query).group(1)) if "limit" in query else None
            sorted_df = sample_table.sort_values(column, ascending=(direction == "ascending"))
            return sorted_df.head(limit) if limit else sorted_df
        
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

# Remaining functions (calculate_score, analyze_performance, get_emoji) remain same as original
# Streamlit UI components remain same as original with proper variable name changes

# ... [Rest of the Streamlit UI code remains identical except for variable name changes from 'correct_answer' to 'expected_result']

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

# Streamlit App
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





