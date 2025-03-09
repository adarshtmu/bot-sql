import streamlit as st
import google.generativeai as genai
import pandas as pd

# Custom CSS for a cleaner, more modern UI
st.markdown("""
<style>
    /* Overall page styling */
    .main {
        padding: 2rem;
        max-width: 1000px;
        margin: 0 auto;
    }
    
    /* Header styling */
    h1, h2, h3 {
        margin-bottom: 1.5rem;
        color: #1E88E5;
        font-weight: 600;
    }
    
    /* Card styling */
    .card {
        background-color: #1E1E1E;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 2rem;
        border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Table styling */
    .dataframe {
        width: 100%;
        margin-top: 1rem;
        margin-bottom: 2rem;
        border-collapse: separate;
        border-spacing: 0;
        border-radius: 8px;
        overflow: hidden;
    }
    
    .dataframe th {
        background-color: #2C3E50;
        color: white;
        text-align: left;
        padding: 12px 15px;
        font-weight: 500;
    }
    
    .dataframe td {
        padding: 10px 15px;
        border-bottom: 1px solid #333;
    }
    
    .dataframe tr:nth-child(even) {
        background-color: #222;
    }
    
    .dataframe tr:hover {
        background-color: #333;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #1E88E5;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-size: 16px;
        font-weight: 500;
        transition: all 0.3s;
    }
    
    .stButton > button:hover {
        background-color: #1565C0;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
    
    /* Progress bar styling */
    .stProgress > div > div {
        background-color: #1E88E5;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-size: 16px;
        font-weight: 500;
        color: #1E88E5;
    }
    
    /* Info box styling */
    .stAlert {
        padding: 16px;
        border-radius: 8px;
    }
    
    /* Text input styling */
    .stTextInput > div > div > input {
        border-radius: 8px;
        padding: 10px 15px;
        font-size: 16px;
        border: 1px solid #333;
    }
    
    /* Hide Streamlit elements */
    header {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .viewerBadge_container__1QSob {display: none !important;}
    .stDeployButton {display: none !important;}
    [data-testid="stToolbar"] {display: none !important;}
    [data-testid="stDecoration"] {display: none !important;}
    [data-testid="stDeployButton"] {display: none !important;}
    .st-emotion-cache-1r8d6ul {display: none !important;}
    .st-emotion-cache-1jicfl2 {display: none !important;}
</style>
""", unsafe_allow_html=True)

# Set up Gemini API
gemini_api_key = "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k"
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

# SQL Questions list with enhanced, detailed instructions
sql_questions = [
    {
        "question": "Imagine you are the database guardian responsible for managing user data. Your task is to extract a complete snapshot of all users from the 'users' table. Write a SQL query that retrieves every column and every record so you can see all the details of each user.",
        "correct_answer": "SELECT * FROM users;",
        "sample_table": users_table
    },
    # Add other questions here...
    # (remaining questions omitted for brevity)
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
    
    # Generate detailed, friendly feedback using Gemini API in Hindi with a casual tone.
    prompt = f"""
    Question: {question}
    Correct Answer: {correct_answer}
    Your Answer: {student_answer}
    Expected Query Result: {expected_result}
    Actual Query Result: {actual_result}
    
    Ab ek dost ke andaaz mein Hindi mein feedback dein. Agar aapka jawab sahi hai, toh kuch aise kehna: "Wah yaar, zabardast jawab diya!" Aur agar jawab galat hai, toh casually bolna: "Arre yaar, thoda gadbad ho gaya, koi baat nahi, agli baar aur accha karna." Thoda detail mein bhi batana ki kya chuk hua ya sahi kyu hai.
    """
    response = model.generate_content(prompt)
    feedback_api = response.text
    feedback_api = feedback_api.replace("student", "aap")
    
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


# Streamlit App - Welcome Page
if not st.session_state.quiz_started:
    st.markdown("<h1 style='text-align: center; color: #1E88E5;'>SQL Mentor - Interactive SQL Query Practice</h1>", unsafe_allow_html=True)
    
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### Welcome to Your SQL Learning Journey! 🚀")
    
    st.markdown("""
    **📌 Important Note:**
    - This quiz uses **MySQL syntax** for all SQL queries.
    - Ensure your answers follow MySQL conventions.
    """)
    
    st.markdown("<div style='display: flex; margin-top: 20px;'>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown("""
        In this interactive SQL quiz, you'll work with two main tables:
        
        **Users Table**: Contains user details such as ID, name, email, age, and city.
        
        **Orders Table**: Stores order details including order ID, user ID, amount, order date, and status.
        """)
    
    with col2:
        st.markdown("#### Tables Overview")
        table_overview = pd.DataFrame({
            "Table": ["Users", "Orders"],
            "Rows": [len(users_table), len(orders_table)]
        })
        st.table(table_overview)
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Table Previews section with improved styling
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 🔍 Table Previews")
    
    tab1, tab2 = st.tabs(["Users Table", "Orders Table"])
    
    with tab1:
        st.dataframe(users_table, use_container_width=True)
    
    with tab2:
        st.dataframe(orders_table, use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Quiz overview
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("### 📋 Quiz Overview")
    
    st.markdown("""
    - You'll solve 10 progressive SQL query challenges
    - Each question tests a different SQL concept
    - Immediate feedback after each answer
    - Final score and detailed analysis at the end
    """)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Call to action button
    st.markdown("<div style='text-align: center; margin-top: 30px;'>", unsafe_allow_html=True)
    if st.button("🚀 Start SQL Challenge", use_container_width=True):
        st.session_state.quiz_started = True
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# Quiz Page
if st.session_state.quiz_started and not st.session_state.quiz_completed:
    st.markdown("<h1 style='text-align: center; color: #1E88E5;'>SQL Challenge</h1>", unsafe_allow_html=True)
    
    # Progress indicator
    progress = (st.session_state.current_question + 1) / len(sql_questions)
    st.progress(progress)
    st.markdown(f"<p style='text-align: center; margin-bottom: 30px;'><b>Progress:</b> {st.session_state.current_question + 1}/{len(sql_questions)} questions completed</p>", unsafe_allow_html=True)
    
    # Current question
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    question_data = sql_questions[st.session_state.current_question]
    st.markdown(f"### Question {st.session_state.current_question + 1}")
    st.write(question_data["question"])
    
    # Sample table for reference
    st.markdown("#### Sample Table for Reference:")
    st.dataframe(question_data["sample_table"], use_container_width=True)
    
    # Answer input
    st.markdown("#### Your Answer:")
    student_answer = st.text_area("Enter your SQL query here:", key=f"answer_{st.session_state.current_question}", height=100)
    
    if st.button("Submit Answer", use_container_width=True):
        if student_answer.strip():
            feedback, is_correct, expected_result, actual_result = evaluate_answer(
                question_data["question"],
                question_data["correct_answer"],
                student_answer,
                question_data["sample_table"]
            )
            
            # Add to session state
            st.session_state.user_answers.append({
                "question": question_data["question"],
                "student_answer": student_answer,
                "feedback": feedback,
                "is_correct": is_correct,
                "expected_result": expected_result,
                "actual_result": actual_result
            })
            
            # Display feedback
            if is_correct:
                st.success(f"**Feedback:** {feedback}")
            else:
                st.error(f"**Feedback:** {feedback}")
                
            # Show query results
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Expected Result:**")
                if isinstance(expected_result, pd.DataFrame):
                    st.dataframe(expected_result, use_container_width=True)
                else:
                    st.write(expected_result)
            
            with col2:
                st.markdown("**Your Result:**")
                if isinstance(actual_result, pd.DataFrame):
                    st.dataframe(actual_result, use_container_width=True)
                else:
                    st.write(actual_result)
            
            # Move to next question
            if st.session_state.current_question < len(sql_questions) - 1:
                st.session_state.current_question += 1
                st.rerun()
            else:
                st.session_state.awaiting_final_submission = True
                st.markdown("### You've completed all questions!")
                if st.button("Finish Quiz", use_container_width=True):
                    st.session_state.quiz_completed = True
                    st.rerun()
        else:
            st.warning("Please enter an answer before submitting.")
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Previous questions/answers
    if st.session_state.user_answers:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### Previous Questions")
        
        for i, ans in enumerate(st.session_state.user_answers):
            with st.expander(f"Question {i + 1}", expanded=False):
                st.write(ans["question"])
                st.markdown("**Your Answer:**")
                st.code(ans["student_answer"])
                
                if ans["is_correct"]:
                    st.markdown(f"<span style='color: #4CAF50;'>✅ **Correct!** {ans['feedback']}</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<span style='color: #F44336;'>❌ **Not Quite Right.** {ans['feedback']}</span>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)

# Results Page
if st.session_state.quiz_completed:
    st.balloons()
    st.markdown("<h1 style='text-align: center; color: #1E88E5;'>Quiz Completed!</h1>", unsafe_allow_html=True)
    
    score = calculate_score(st.session_state.user_answers)
    
    # Score card
    st.markdown("<div class='card' style='text-align: center;'>", unsafe_allow_html=True)
    st.markdown(f"<h2>Your Score: {score:.1f}%</h2>", unsafe_allow_html=True)
    
    # Performance rating based on score
    if score >= 90:
        st.markdown("<h3 style='color: #4CAF50;'>Outstanding! 🌟</h3>", unsafe_allow_html=True)
    elif score >= 70:
        st.markdown("<h3 style='color: #2196F3;'>Great Job! 👍</h3>", unsafe_allow_html=True)
    elif score >= 50:
        st.markdown("<h3 style='color: #FF9800;'>Good Effort! 👍</h3>", unsafe_allow_html=True)
    else:
        st.markdown("<h3 style='color: #F44336;'>Keep Practicing! 💪</h3>", unsafe_allow_html=True)
    
    # CTA based on score
    if score < 50:
        st.markdown(
            """
            <div style="background-color: rgba(244, 67, 54, 0.1); padding: 20px; border-radius: 10px; margin-top: 20px; text-align: center; border: 1px solid #F44336;">
                <h3 style="color: #F44336;">Need to improve your SQL skills?</h3>
                <p style="font-size: 16px; margin-bottom: 20px;">Book a mentor session now to upgrade your SQL knowledge!</p>
                <a href="https://www.corporatebhaiya.com/" target="_blank">
                    <button style="background-color: #F44336; color: white; padding: 12px 24px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                        Book A Mentor
                    </button>
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div style="background-color: rgba(76, 175, 80, 0.1); padding: 20px; border-radius: 10px; margin-top: 20px; text-align: center; border: 1px solid #4CAF50;">
                <h3 style="color: #4CAF50;">Ready for the next level?</h3>
                <p style="font-size: 16px; margin-bottom: 20px;">Schedule a mock interview and resume building session!</p>
                <a href="https://www.corporatebhaiya.com/" target="_blank">
                    <button style="background-color: #4CAF50; color: white; padding: 12px 24px; border: none; border-radius: 8px; font-size: 16px; cursor: pointer; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);">
                        Level Up Your Career
                    </button>
                </a>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Detailed feedback section
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 View Detailed Feedback", use_container_width=True):
            st.session_state.show_detailed_feedback = True
            st.rerun()
    
    with col2:
        if st.button("🔄 Restart Quiz", use_container_width=True):
            st.session_state.user_answers = []
            st.session_state.current_question = 0
            st.session_state.quiz_started = False
            st.session_state.quiz_completed = False
            st.session_state.show_detailed_feedback = False
            st.session_state.awaiting_final_submission = False
            st.rerun()
    
    # Show detailed feedback if requested
    if st.session_state.show_detailed_feedback:
        performance_feedback = analyze_performance(st.session_state.user_answers)
        
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("### Detailed Performance Analysis")
        
        # Strengths and weaknesses in columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 💪 Strengths")
            if performance_feedback["strengths"]:
                for i, question in enumerate(performance_feedback["strengths"]):
                    st.markdown(f"✅ {question[:100]}...")
            else:
                st.markdown("No strengths identified.")
        
        with col2:
            st.markdown("#### 🎯 Areas to Improve")
            if performance_feedback["weaknesses"]:
                for i, question in enumerate(performance_feedback["weaknesses"]):
                    st.markdown(f"❌ {question[:100]}...")
            else:
                st.markdown("No weaknesses identified.")
        
        # Overall feedback
        st.markdown("#### 💬 Overall Feedback")
        st.info(performance_feedback["overall_feedback"])
        
        st.markdown("</div>", unsafe_allow_html=True)
