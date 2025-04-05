import streamlit as st
import random
import os
import google.generativeai as genai

# Configure your Gemini API Key
os.environ["GOOGLE_API_KEY"] = "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# Initialize Gemini model
model = genai.GenerativeModel('gemini-pro')

# Define a list of SQL questions
questions = [
    {"question": "Write a SQL query to get all details about users from the 'users' table."},
    {"question": "Write a SQL query to count the total number of users in the 'users' table."},
    {"question": "Write a SQL query to get all users older than 30 from the 'users' table."},
    {"question": "Write a SQL query to find all orders with a status of 'Pending' from the 'orders' table."},
    {"question": "Write a SQL query to find the most recent order from the 'orders' table by order date."},
    {"question": "Write a SQL query to find the average order amount from the 'orders' table."},
    {"question": "Write a SQL query to find users who have not placed any orders in the 'orders' table."},
    {"question": "Write a SQL query to calculate the total amount spent by each user by joining the 'users' and 'orders' tables."},
    {"question": "Write a SQL query to count how many orders each user has placed using a LEFT JOIN between 'users' and 'orders'."},
    {"question": "Write a SQL query to find users from 'New York' or 'Chicago' in the 'users' table."}
]

# Function to evaluate user's answer using Gemini
def evaluate_answer(user_answer, question):
    prompt = f"""
    Question: {question}
    User Answer: {user_answer}

    Evaluate if the SQL is correct. If incorrect, provide the correct query and explanation.
    """
    response = model.generate_content(prompt)
    return response.text

# UI setup
st.title("SQL Practice Quiz with AI Feedback")
st.markdown("Test your SQL skills and get feedback from Gemini AI.")

if "current_question" not in st.session_state:
    st.session_state.current_question = random.choice(questions)

if "user_score" not in st.session_state:
    st.session_state.user_score = 0

question_text = st.session_state.current_question["question"]
st.subheader("Question:")
st.write(question_text)

user_sql = st.text_area("Your SQL Query", height=150)

if st.button("Submit Answer"):
    if user_sql.strip() == "":
        st.warning("Please enter your SQL query before submitting.")
    else:
        with st.spinner("Evaluating your answer..."):
            feedback = evaluate_answer(user_sql, question_text)
        st.markdown("### Feedback from Gemini:")
        st.write(feedback)

        # Optionally update score
        if "correct" in feedback.lower():
            st.session_state.user_score += 1
            st.success("Great! Your answer looks correct.")

        st.markdown(f"**Score:** {st.session_state.user_score}")

        if st.button("Next Question"):
            st.session_state.current_question = random.choice(questions)
            st.experimental_rerun()
