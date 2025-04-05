import streamlit as st
import google.generativeai as genai
import pandas as pd
import re # Import regex for parsing LLM output and simulation

# --- Custom CSS ---
hide_streamlit_style = """
    <style>
        header {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        .viewerBadge_container__1QSob {display: none !important;} /* Hides the GitHub profile image */
        .stDeployButton {display: none !important;} /* Hides deploy button */
        [data-testid="stToolbar"] {display: none !important;} /* Hides Streamlit toolbar */
        [data-testid="stDecoration"] {display: none !important;} /* Hides Streamlit branding */
        [data-testid="stDeployButton"] {display: none !important;} /* Hides Streamlit deploy button */
        .st-emotion-cache-1r8d6ul {display: none !important;} /* Additional class for profile image */
        .st-emotion-cache-1jicfl2 {display: none !important;} /* Hides Streamlit's footer */
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Set up Gemini API ---
# IMPORTANT: Replace with your actual Gemini API Key
# Consider using Streamlit Secrets for API key management in deployment
# --- Set up Gemini API ---
# WARNING: Hardcoding API keys is insecure. Consider environment variables or secrets for deployment.
gemini_api_key = "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k" # Your specific API Key

if not gemini_api_key: # Basic check if the key is empty
    st.error("🚨 Gemini API Key is missing in the code.")
    st.stop()

try:
    genai.configure(api_key=gemini_api_key)
    # Use a model suitable for complex reasoning like query analysis
    # gemini-1.5-flash is a good balance of capability and speed
    model = genai.GenerativeModel('gemini-1.5-flash')
    # Optional: Add a check to see if the model is accessible
    # model.generate_content("Test", generation_config=genai.types.GenerationConfig(max_output_tokens=5))
    # st.success("Gemini Model Configured Successfully.") # Optional success message
except Exception as e:
    st.error(f"🚨 Failed to configure Gemini API or access the model: {e}")
    st.stop()

try:
    genai.configure(api_key=gemini_api_key)
    # Use a model suitable for complex reasoning like query analysis
    # gemini-1.5-flash is a good balance of capability and speed
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"🚨 Failed to configure Gemini API: {e}")
    st.stop()


# --- Sample Data ---

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
    # Ensure order_date is datetime type for potential date comparisons in simulation
    "order_date": pd.to_datetime(["2024-02-01", "2024-02-05", "2024-02-10", "2024-02-15", "2024-02-20"]),
    "status": ["Completed", "Pending", "Completed", "Shipped", "Cancelled"]
})

# Store original tables for schema reference by the LLM
original_tables = {
    "users": users_table,
    "orders": orders_table
}

# Create a merged table (primarily for simulation if needed, LLM uses original schemas)
# Be careful with simulation on merged tables if the question implies separate tables.
merged_table = pd.merge(users_table, orders_table, on="user_id", how="inner")


# --- SQL Questions List (Updated with relevant_tables) ---
sql_questions = [
    {
        "question": "Write a SQL query to get all details about users from the 'users' table.",
        "correct_answer_example": "SELECT * FROM users;", # Example for reference/simulation
        "sample_table": users_table, # Table for simulation display
        "relevant_tables": ["users"] # Tables for LLM schema context
    },
    {
        "question": "Write a SQL query to count the total number of users in the 'users' table.",
        "correct_answer_example": "SELECT COUNT(*) FROM users;",
        "sample_table": users_table,
        "relevant_tables": ["users"]
    },
    {
        "question": "Write a SQL query to get all users older than 30 from the 'users' table.",
        "correct_answer_example": "SELECT * FROM users WHERE age > 30;",
        "sample_table": users_table,
        "relevant_tables": ["users"]
    },
    {
        "question": "Write a SQL query to find all orders with a status of 'Pending' from the 'orders' table.",
        "correct_answer_example": "SELECT * FROM orders WHERE status = 'Pending';",
        "sample_table": orders_table,
        "relevant_tables": ["orders"]
    },
    {
        "question": "Write a SQL query to find the most recent order from the 'orders' table by order date.",
        "correct_answer_example": "SELECT * FROM orders ORDER BY order_date DESC LIMIT 1;",
        "sample_table": orders_table,
        "relevant_tables": ["orders"]
    },
    {
        "question": "Write a SQL query to find the average order amount from the 'orders' table.",
        "correct_answer_example": "SELECT AVG(amount) FROM orders;",
        "sample_table": orders_table,
        "relevant_tables": ["orders"]
    },
    {
        "question": "Write a SQL query to find users who have not placed any orders. Use the 'users' and 'orders' tables.",
        "correct_answer_example": "SELECT u.* FROM users u LEFT JOIN orders o ON u.user_id = o.user_id WHERE o.order_id IS NULL;",
        "sample_table": users_table, # Primary result table for simulation
        "relevant_tables": ["users", "orders"]
    },
    {
        "question": "Write a SQL query to calculate the total amount spent by each user by joining the 'users' and 'orders' tables.",
        "correct_answer_example": ("SELECT u.name, SUM(o.amount) AS total_spent FROM users u "
                           "JOIN orders o ON u.user_id = o.user_id GROUP BY u.name;"),
        "sample_table": merged_table, # Simulation can use merged here
        "relevant_tables": ["users", "orders"]
    },
    {
        "question": "Write a SQL query to count how many orders each user has placed using a LEFT JOIN between 'users' and 'orders'. Include users with zero orders.",
        "correct_answer_example": ("SELECT u.name, COUNT(o.order_id) AS order_count FROM users u "
                           "LEFT JOIN orders o ON u.user_id = o.user_id GROUP BY u.name;"),
        "sample_table": merged_table, # Simulation can use merged here
        "relevant_tables": ["users", "orders"]
    },
    {
        "question": "Write a SQL query to find users from 'New York' or 'Chicago' in the 'users' table.",
        "correct_answer_example": "SELECT * FROM users WHERE city IN ('New York', 'Chicago');",
        "sample_table": users_table,
        "relevant_tables": ["users"]
    }
]

# --- Session State Initialization ---
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
# Removed awaiting_final_submission, as submit now happens per question


# --- Helper Functions ---

def simulate_query(query, sample_table):
# --- Inside simulate_query function ---

        # Handle SELECT * or specific columns
        select_match = re.match(r"select\s+(.*?)\s+from.*", query, re.IGNORECASE)
        if select_match:
            select_part = select_match.group(1).strip()

            # --- WHERE Clause Processing ---
            result_df = sample_table.copy() # Start with the full table
            where_match = re.search(r"where\s+(.*)", query, re.IGNORECASE)
            condition_applied = False # Flag if WHERE clause was processed
            if where_match:
                condition = where_match.group(1).strip()
                # Process the condition string for pandas.query()
                try:
                    # Convert SQL-style string comparisons: col = 'value' or col = "value" -> col == "value"
                    condition = re.sub(r"(\w+)\s*=\s*('|\")(.+?)\2", r'\1 == "\3"', condition)
                    # Convert numeric/boolean equality: col = 123 -> col == 123
                    condition = re.sub(r"(\w+)\s*=\s*(\d+\.?\d*|True|False)", r'\1 == \2', condition, flags=re.IGNORECASE)
                    # Handle AND/OR (case-insensitive)
                    condition = re.sub(r"\s+and\s+", " & ", condition, flags=re.IGNORECASE)
                    condition = re.sub(r"\s+or\s+", " | ", condition, flags=re.IGNORECASE)
                    # Handle IN operator: city in ('New York', 'Chicago') -> city.isin(["New York", "Chicago"])
                    in_match = re.search(r"(\w+)\s+in\s+\((.+)\)", condition, flags=re.IGNORECASE)
                    if in_match:
                        col_in, values_in_str = in_match.groups()
                        values_list = [f'"{v.strip().strip( "\' ")}"' for v in values_in_str.split(',')]
                        pandas_in_clause = f"{col_in}.isin([{', '.join(values_list)}])"
                        condition = condition.replace(in_match.group(0), pandas_in_clause)
                    # Handle other comparison operators (>, <, >=, <=)
                    condition = re.sub(r"(\w+)\s*(>|>=|<|<=)\s*(\d+\.?\d*)", r"\1 \2 \3", condition)
                    condition = re.sub(r"(\w+)\s*(>|>=|<|<=)\s*('|\")(.+?)\3", r'\1 \2 "\4"', condition)

                    # --- Enhanced Debug Prints ---
                    print("-" * 20)
                    print(f"DEBUG [simulate_query]: Original WHERE condition: {where_match.group(1).strip()}")
                    print(f"DEBUG [simulate_query]: Processed condition for pandas.query: {condition}")
                    print(f"DEBUG [simulate_query]: DataFrame dtypes before query:\n{result_df.dtypes}")
                    # Check if the relevant column exists before trying to access it
                    filter_col_match = re.match(r"(\w+)\s*==", condition) # Basic check for equality condition column
                    if filter_col_match:
                        filter_col = filter_col_match.group(1)
                        if filter_col in result_df.columns:
                             print(f"DEBUG [simulate_query]: Unique '{filter_col}' values before query: {result_df[filter_col].unique()}")
                        else:
                             print(f"DEBUG [simulate_query]: Column '{filter_col}' not found before query.")
                    else:
                         print(f"DEBUG [simulate_query]: Could not determine filter column from condition '{condition}' for unique value check.")
                    # --- End Enhanced Debug Prints ---

                    result_df = result_df.query(condition) # The actual filtering
                    condition_applied = True

                    # --- Debug Print After Query ---
                    print(f"DEBUG [simulate_query]: DataFrame shape after query: {result_df.shape}")
                    # print(f"DEBUG [simulate_query]: DataFrame after query:\n{result_df}") # Uncomment to see full df
                    print("-" * 20)
                    # --- End Debug Print After Query ---

                except Exception as e_cond:
                     print(f"DEBUG [simulate_query]: Error during sample_table.query execution for condition '{condition}': {e_cond}")
                     # Return error string instead of empty DataFrame on simulation failure
                     return f"Simulation Error: Could not apply condition '{where_match.group(1)}'. Reason: {e_cond}"
            # ... [rest of the function remains the same] ...


def get_table_schema(table_name, tables_dict):
    """Gets column names for a given table name."""
    if table_name in tables_dict:
        # Return column names as a list of strings
        return tables_dict[table_name].columns.astype(str).tolist()
    return []

def evaluate_answer_with_llm(question_data, student_answer, original_tables_dict):
    """Evaluate the user's answer using Gemini API based on question intent and schema."""
    if not student_answer.strip():
        return "Please provide an answer.", False, "N/A", "N/A", "No input."

    question = question_data["question"]
    relevant_table_names = question_data["relevant_tables"]
    # Keep correct_answer for reference if needed, e.g., showing one possible solution
    correct_answer_example = question_data["correct_answer_example"]

    # --- Schema Information ---
    schema_info = ""
    if not relevant_table_names:
         schema_info = "No specific table schema provided for context.\n"
    else:
        for name in relevant_table_names:
            columns = get_table_schema(name, original_tables_dict)
            if columns:
                # Include data types for better context
                dtypes = original_tables_dict[name].dtypes.to_string()
                schema_info += f"Table '{name}': Columns {columns}\n DataTypes:\n{dtypes}\n\n"
            else:
                # Try to infer from sample_table if original not found (less ideal)
                fallback_df = question_data.get("sample_table")
                if isinstance(fallback_df, pd.DataFrame) and not fallback_df.empty:
                     fallback_cols = fallback_df.columns.astype(str).tolist()
                     fallback_dtypes = fallback_df.dtypes.to_string()
                     schema_info += f"Table '{name}' (inferred): Columns {fallback_cols}\n DataTypes:\n{fallback_dtypes}\n\n"
                else:
                    schema_info += f"Table '{name}': Schema not found.\n"

    # --- LLM Prompt ---
    prompt = f"""
    You are an expert SQL evaluator acting as a friendly SQL mentor. Analyze the student's SQL query based on the question asked and the provided table schemas (including data types). Assume standard SQL syntax (like MySQL/PostgreSQL).

    **Evaluation Task:**

    1.  **Question:** {question}
    2.  **Relevant Table Schemas:**
        {schema_info.strip()}
    3.  **Student's SQL Query:**
        ```sql
        {student_answer}
        ```

    **Analysis Instructions:**

    * **Correctness:** Does the student's query accurately and completely answer the **Question** based on the **Relevant Table Schemas**? Consider edge cases if applicable (e.g., users with no orders, data types for comparisons).
    * **Validity:** Is the query syntactically valid SQL? Briefly mention any syntax errors.
    * **Logic:** Does the query use appropriate SQL clauses (SELECT, FROM, WHERE, JOIN, GROUP BY, ORDER BY, aggregates, etc.) correctly for the task? Is the logic sound? Are comparisons appropriate for the data types?
    * **Alternatives:** Briefly acknowledge if the student used a valid alternative approach (e.g., different JOIN type if appropriate, subquery vs. JOIN). Efficiency is a minor point unless significantly poor.
    * **Feedback:** Provide clear, constructive feedback in a friendly, encouraging, casual Hindi tone (like a helpful senior or 'bhaiya' talking to a learner).
        * If correct: Praise the student (e.g., "Wah yaar, zabardast query likhi hai! Bilkul sahi logic lagaya.") and briefly explain *why* it's correct or mention if it's a common/good way.
        * If incorrect: Gently point out the error (e.g., "Arre yaar, yahaan thoda sa check karo..." or "Ek chhoti si galti ho gayi hai..."). Explain *what* is wrong (syntax, logic, wrong columns/tables, missed conditions, data type mismatch) and *why*. Suggest how to fix it or what the correct concept/approach might involve (e.g., "Yahaan `LEFT JOIN` use karna better rahega kyunki..." or "WHERE clause mein condition check karo... Status ek text hai, toh quotes use karna hoga..."). Avoid just giving the full correct query away unless needed for a specific small fix explanation. Keep it encouraging.
    * **Verdict:** Conclude your entire response with *exactly* one line formatted as: "Verdict: Correct" or "Verdict: Incorrect". This line MUST be the very last line.

    **Begin Evaluation:**
    """

    # --- Call Gemini API ---
    try:
        # Use generate_content for potential future features like safety settings
        response = model.generate_content(prompt)
        # Access the text part of the response
        # Handle potential lack of text or parts in the response object
        if response.parts:
            llm_output = "".join(part.text for part in response.parts)
        else:
            # Fallback for simpler response structures or if parts is empty
             llm_output = response.text # Assuming response.text exists

        llm_output = llm_output.strip()
        # print(f"DEBUG: LLM Raw Output:\n---\n{llm_output}\n---") # Uncomment for debugging

        # --- Parse LLM Response ---
        feedback_llm = llm_output
        is_correct_llm = False

        # Find the verdict line (case-insensitive, anchoring to end of string potentially safer)
        # Use re.MULTILINE and check end of string ($) for robustness
        verdict_match = re.search(r'^Verdict:\s*(Correct|Incorrect)\s*$', llm_output, re.MULTILINE | re.IGNORECASE)

        if verdict_match:
            verdict = verdict_match.group(1).lower()
            is_correct_llm = (verdict == "correct")
            # Remove the verdict line from the feedback string for cleaner display
            feedback_llm = llm_output[:verdict_match.start()].strip()
        else:
            # If verdict line is missing or malformed, log it, default to incorrect
            st.warning(f"⚠️ System Warning: Could not parse final verdict from AI feedback. Please review feedback carefully.")
            print(f"WARNING: Could not parse verdict from LLM output. Full output was:\n{llm_output}") # Log for server-side debugging
            # Keep the full output as feedback in this case
            feedback_llm = llm_output + "\n\n_(System Note: Automatic correctness check failed. Review feedback manually.)_"
            is_correct_llm = False # Default to incorrect if parsing fails

        # Replace placeholder just in case LLM uses it literally
        feedback_llm = feedback_llm.replace("student", "aap")

    except Exception as e:
        st.error(f"🚨 Error communicating with AI model: {e}")
        print(f"ERROR: Exception during Gemini API call: {e}") # Log the error
        feedback_llm = f"Maaf karna yaar, AI feedback generate karne mein kuch dikkat aa gayi: {e}"
        is_correct_llm = False # Assume incorrect on error
        llm_output = f"Error: {e}" # Store error message

    # --- Simulation for Comparison Display (using sample_table) ---
    # Ensure simulation uses the correct table intended for the question's simulation display
    simulation_table = question_data.get("sample_table")
    if not isinstance(simulation_table, pd.DataFrame):
         simulation_table = pd.DataFrame() # Avoid errors if sample_table is missing/invalid

    # Simulate the *student's* query
    actual_result_sim = simulate_query(student_answer, simulation_table)
    # Simulate one *possible* correct answer for reference
    expected_result_sim = simulate_query(correct_answer_example, simulation_table)


    return feedback_llm, is_correct_llm, expected_result_sim, actual_result_sim, llm_output # Return raw output too for potential debugging


def calculate_score(user_answers):
    """Calculate the score based on correct answers."""
    if not user_answers:
        return 0
    correct_answers_count = sum(1 for ans in user_answers if ans.get("is_correct", False))
    total_questions = len(user_answers)
    return (correct_answers_count / total_questions) * 100 if total_questions > 0 else 0

def analyze_performance(user_answers):
    """Analyze the user's performance and provide detailed feedback via LLM."""
    if not user_answers:
        return {"strengths": [], "weaknesses": [], "overall_feedback": "Koi jawab nahi diya gaya."}

    correct_questions = [ans["question"] for ans in user_answers if ans.get("is_correct")]
    incorrect_answers = [
        {
            "question": ans["question"],
            "your_answer": ans["student_answer"],
            "feedback_received": ans.get("feedback", "N/A") # Use .get for safety
         } for ans in user_answers if not ans.get("is_correct")
    ]

    # Generate detailed feedback using LLM
    feedback_summary = {
        "strengths": correct_questions,
        "weaknesses_info": incorrect_answers, # Send more info to LLM
        "overall_feedback": ""
    }

    total_q = len(user_answers)
    correct_q_count = len(correct_questions)
    score = calculate_score(user_answers)

    # Prepare incorrect answers summary for the prompt
    incorrect_summary = "\n".join([
        f"  Q: {item['question']}\n    Aapka Jawaab: {item['your_answer']}\n    Feedback Mila: {item['feedback_received']}\n"
        for item in incorrect_answers
    ]).strip() if incorrect_answers else "Koi nahi! Sab sahi the!"

    prompt = f"""
    Ek student ne SQL quiz diya hai. Unke performance ka summary neeche hai:

    Total Questions: {total_q}
    Correct Answers: {correct_q_count}
    Score: {score:.2f}%

    Correctly Answered Questions:
    {chr(10).join(f'  - {q}' for q in correct_questions) if correct_questions else '  (Koi nahi)'}

    Incorrectly Answered Questions (with their answer and feedback given):
    {incorrect_summary}

    Task: Ab ek dost ki tarah, casual Hindi mein overall performance ka ek summary feedback do.
    - Achhe performance ko appreciate karo (score aur sahi jawaabon ka zikr karo).
    - Jin topics mein galti hui (incorrect answers ke basis par), unko gently highlight karo aur improve karne ke liye encourage karo. Feedback received ko consider karke common themes batao, jaise ki 'JOINs pe thoda aur practice karo' ya 'WHERE clause mein string values ko quotes mein daalna yaad rakho'.
    - Ek positive aur motivating tone rakho. Final score ke hisaab se encouragement adjust karo (e.g., high score = "keep it up", low score = "koi baat nahi, practice se improve hoga").
    """

    try:
        response = model.generate_content(prompt)
        if response.parts:
            feedback_summary["overall_feedback"] = "".join(part.text for part in response.parts).strip()
        else:
             feedback_summary["overall_feedback"] = response.text.strip() # Fallback

    except Exception as e:
        print(f"Error generating performance summary with LLM: {e}")
        feedback_summary["overall_feedback"] = f"Performance summary generate karne mein dikkat aa gayi: {e}"

    # Return structure compatible with existing display code
    feedback_display = {
        "strengths": correct_questions,
        "weaknesses": [item["question"] for item in incorrect_answers], # Keep original structure for display list
        "overall_feedback": feedback_summary["overall_feedback"]
    }
    return feedback_display


def get_emoji(is_correct):
    return "✅" if is_correct else "❌"


# --- Streamlit App ---

# --- Start Screen ---
if not st.session_state.quiz_started:
    st.title("🚀 SQL Mentor - Interactive SQL Practice")

    st.markdown("### Apne SQL Skills Ko Test Aur Improve Karein!")

    st.markdown("""
    **📌 Important Note:**
    - This quiz assumes standard **SQL syntax** (similar to MySQL/PostgreSQL).
    - Your queries will be evaluated by an AI for correctness and logic.
    - Query simulation is basic and may not perfectly match a real database. Focus on the AI feedback.
    """)

    col1, col2 = st.columns([2, 1])

    with col1:
        st.write("""
        Is interactive quiz mein, aap do sample tables ke saath kaam karenge:
        - **Users Table**: User details jaise ID, naam, email, umar, aur sheher.
        - **Orders Table**: Order details jaise ID, user ID, amount, order date, aur status.
        """)

    with col2:
        st.markdown("#### Tables Overview")
        # Use original_tables dict for overview
        table_overview_data = {
            "Table": list(original_tables.keys()),
            "Rows": [len(df) for df in original_tables.values()],
            "Columns": [len(df.columns) for df in original_tables.values()]
         }
        st.dataframe(pd.DataFrame(table_overview_data), hide_index=True)


    st.write("### 🔍 Table Previews")

    tab1, tab2 = st.tabs(["Users Table", "Orders Table"])

    with tab1:
        st.dataframe(users_table, hide_index=True)

    with tab2:
        st.dataframe(orders_table, hide_index=True)

    with st.expander("📝 Quiz Ke Baare Mein"):
        st.write(f"""
        - Aapko {len(sql_questions)} SQL query challenges solve karne honge.
        - Har sawaal alag SQL concept test karega.
        - Har jawaab ke baad AI Mentor se immediate feedback milega.
        - Aapka final score aur detailed performance analysis end mein dikhaya jayega.
        - **SQL Dialect Focus:** Standard SQL (MySQL/PostgreSQL like)
        """)

    if st.button("🚀 Start SQL Challenge!"):
        st.session_state.quiz_started = True
        # Reset potential previous quiz state just in case
        st.session_state.user_answers = []
        st.session_state.current_question = 0
        st.session_state.quiz_completed = False
        st.session_state.show_detailed_feedback = False
        st.rerun()


# --- Quiz In Progress ---
if st.session_state.quiz_started and not st.session_state.quiz_completed:

    st.title("✍️ SQL Query Challenge")

    # --- Display Past Answers (Chat History) ---
    if st.session_state.user_answers:
        st.markdown("---")
        st.subheader("📖 Ab Tak Ke Jawaab Aur Feedback")
        # Display newest first by reversing the list for display
        for i, ans_data in enumerate(reversed(st.session_state.user_answers)):
            q_num = len(st.session_state.user_answers) - i
            with st.expander(f"Question {q_num}: {ans_data['question']} {get_emoji(ans_data['is_correct'])}", expanded=False): # Start collapsed
                st.write(f"**Aapka Jawaab:**")
                st.code(ans_data['student_answer'], language='sql')
                st.write(f"**SQL Mentor Feedback:**")
                if ans_data.get("is_correct", False): # Use .get for safety
                    st.success(ans_data.get('feedback', 'No feedback provided.'))
                else:
                    st.error(ans_data.get('feedback', 'No feedback provided.'))

                # Display simulated results if available
                st.markdown("---")
                col_sim1, col_sim2 = st.columns(2)
                # Helper function to display simulation results cleanly
                def display_simulation(title, result_data):
                     st.write(f"**{title}:**")
                     if isinstance(result_data, pd.DataFrame):
                        if result_data.empty:
                            st.info("_(Simulation returned empty results)_")
                        else:
                            st.dataframe(result_data, hide_index=True)
                     elif isinstance(result_data, str) and "Simulation Error" in result_data:
                          st.warning(result_data) # Show simulation errors clearly
                     elif result_data == "N/A":
                         st.info("_(Simulation not applicable)_")
                     else:
                         st.info("_(Simulation result not available or invalid)_")

                with col_sim1:
                    display_simulation("Simulated Result (Aapka Query)", ans_data.get("actual_result"))
                with col_sim2:
                     display_simulation("Simulated Result (Example Query)", ans_data.get("expected_result"))

        st.markdown("---")


    # --- Current Question ---
    current_q_index = st.session_state.current_question
    if current_q_index < len(sql_questions):
        question_data = sql_questions[current_q_index]

        st.subheader(f"Sawaal {current_q_index + 1} / {len(sql_questions)}")
        st.markdown(f"**{question_data['question']}**")

        st.write("**Relevant Table(s) Preview:**")
        # Show previews of tables relevant to *this* question
        rel_tables = question_data.get("relevant_tables", [])
        if rel_tables:
            tabs = st.tabs([f"{name.capitalize()} Table" for name in rel_tables])
            for i, table_name in enumerate(rel_tables):
                with tabs[i]:
                    if table_name in original_tables:
                        st.dataframe(original_tables[table_name], hide_index=True)
                    else:
                        st.warning(f"Schema/Preview for '{table_name}' not found.")
        else:
             st.info("No specific tables indicated for preview for this question.")


        # Use text_area for multi-line SQL input
        student_answer = st.text_area("Apna SQL Query Yahaan Likhein:", key=f"answer_{current_q_index}", height=150)

        # Submit Button
        if st.button("✅ Submit Answer", key=f"submit_{current_q_index}"):
            if student_answer.strip():
                with st.spinner("AI Mentor aapka jawaab check kar raha hai..."):
                    # Call the LLM evaluation function
                    feedback, is_correct, expected_sim, actual_sim, llm_raw = evaluate_answer_with_llm(
                        question_data,
                        student_answer,
                        original_tables
                    )

                # Append result to session state BEFORE potentially showing feedback & advancing
                st.session_state.user_answers.append({
                    "question": question_data["question"],
                    "student_answer": student_answer,
                    "feedback": feedback,
                    "is_correct": is_correct,
                    "expected_result": expected_sim, # Simulated result of example correct answer
                    "actual_result": actual_sim,     # Simulated result of student's answer
                    "llm_raw_output": llm_raw        # Store raw output for debugging
                })

                # Decide next step
                if current_q_index < len(sql_questions) - 1:
                    st.session_state.current_question += 1 # Move to next question index
                else:
                    st.session_state.quiz_completed = True # Mark quiz as completed

                st.rerun() # Rerun to display history/next question/results screen

            else:
                st.warning("Please enter your SQL query before submitting.")

        # Progress Bar
        progress = (current_q_index) / len(sql_questions) # Progress based on questions attempted
        st.progress(progress)
        st.caption(f"Question {current_q_index + 1} of {len(sql_questions)}")

    else:
        # This state should ideally not be reached if logic is correct, but as a fallback:
        st.warning("Quiz state error. Showing results.")
        st.session_state.quiz_completed = True # Mark as completed to show results
        st.rerun()


# --- Quiz Completed Screen ---
if st.session_state.quiz_completed:
    st.balloons()
    st.title("🎉 Quiz Complete!")

    score = calculate_score(st.session_state.user_answers)
    st.metric(label="Your Final Score", value=f"{score:.2f}%")

    # --- Display Final Answers and Feedback ---
    st.subheader("📝 Final Review: Aapke Jawaab Aur Feedback")
    # Helper function to display simulation results cleanly (defined again for scope)
    def display_simulation(title, result_data):
        st.write(f"**{title}:**")
        if isinstance(result_data, pd.DataFrame):
            if result_data.empty:
                st.info("_(Simulation returned empty results)_")
            else:
                st.dataframe(result_data, hide_index=True)
        elif isinstance(result_data, str) and "Simulation Error" in result_data:
            st.warning(result_data) # Show simulation errors clearly
        elif result_data == "N/A":
            st.info("_(Simulation not applicable)_")
        else:
            st.info("_(Simulation result not available or invalid)_")

    for i, ans_data in enumerate(st.session_state.user_answers):
        with st.expander(f"Question {i + 1}: {ans_data['question']} {get_emoji(ans_data['is_correct'])}", expanded=False):
            st.write(f"**Aapka Jawaab:**")
            st.code(ans_data.get('student_answer', '(No answer provided)'), language='sql')
            st.write(f"**SQL Mentor Feedback:**")
            if ans_data.get("is_correct", False):
                st.success(ans_data.get('feedback', 'No feedback provided.'))
            else:
                st.error(ans_data.get('feedback', 'No feedback provided.'))
             # Display simulated results if available
            st.markdown("---")
            col_sim1, col_sim2 = st.columns(2)
            with col_sim1:
                display_simulation("Simulated Result (Aapka Query)", ans_data.get("actual_result"))
            with col_sim2:
                display_simulation("Simulated Result (Example Query)", ans_data.get("expected_result"))

    st.markdown("---") # Separator

    # --- Call to Action Buttons ---
    col_cta_1, col_cta_2 = st.columns(2)
    with col_cta_1:
        if st.button("📊 Detailed Performance Analysis"):
            st.session_state.show_detailed_feedback = not st.session_state.show_detailed_feedback # Toggle
            st.rerun() # Rerun to show/hide the feedback section

    with col_cta_2:
        # Corporate Bhaiya CTA (Conditional) - Example Link
        if score < 60: # Adjusted threshold
             st.error("Score thoda kam hai. Practice jaari rakhein!")
             # Simple link button is safer than JS redirect unless needed
             st.link_button("Need Help? Connect with a Mentor", "https://www.corporatebhaiya.com/", use_container_width=True)
        else:
             st.success("Bahut badhiya score! Keep it up! 👍")
             st.link_button("Next Steps? Mock Interview Practice", "https://www.corporatebhaiya.com/mock-interview", use_container_width=True) # Example specific link


    # --- Detailed Feedback Section ---
    if st.session_state.show_detailed_feedback:
        st.markdown("---")
        st.subheader("📈 Detailed Performance Analysis (AI Generated)")
        with st.spinner("AI performance summary generate kar raha hai..."):
            performance_feedback = analyze_performance(st.session_state.user_answers)

        st.write("**Overall Feedback:**")
        st.info(performance_feedback.get("overall_feedback", "Summary not available.")) # Use .get

        st.write("**Strengths (Questions answered correctly):**")
        strengths = performance_feedback.get("strengths", [])
        if strengths:
            for i, question in enumerate(strengths):
                st.success(f"{i + 1}. {question} ✅")
        else:
            st.write("_(No questions answered correctly in this attempt.)_")

        st.write("**Areas for Improvement (Questions answered incorrectly):**")
        weaknesses = performance_feedback.get("weaknesses", [])
        if weaknesses:
            for i, question in enumerate(weaknesses):
                st.error(f"{i + 1}. {question} ❌")
        else:
             st.write("_(No questions answered incorrectly. Great job!)_")


    # --- Restart Button ---
    st.markdown("---")
    if st.button("🔄 Restart Quiz"):
        # Clear all relevant session state variables
        keys_to_reset = ["user_answers", "current_question", "quiz_started",
                         "quiz_completed", "show_detailed_feedback"]
        for key in keys_to_reset:
            if key in st.session_state:
                del st.session_state[key]
        # Re-initialize needed states
        st.session_state.current_question = 0
        st.session_state.quiz_started = False
        st.rerun()
