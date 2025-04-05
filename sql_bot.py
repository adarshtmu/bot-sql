import streamlit as st
import google.generativeai as genai
import pandas as pd
import re # Import regex for parsing LLM output

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
try:
    # Try getting the key from secrets first
    gemini_api_key = st.secrets["GEMINI_API_KEY"]
except (FileNotFoundError, KeyError):
    # Fallback or default if secrets aren't set
    gemini_api_key = "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k" # Replace with your key if not using secrets

# Basic check if the key looks like a placeholder
if gemini_api_key == "YOUR_GEMINI_API_KEY" or not gemini_api_key:
    st.error("🚨 Gemini API Key not found. Please set it using Streamlit Secrets (key: GEMINI_API_KEY) or replace the placeholder in the code.")
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
    "order_date": pd.to_datetime(["2024-02-01", "2024-02-05", "2024-02-10", "2024-02-15", "2024-02-20"]), # Use datetime
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
    """
    Simulate SQL SELECT queries on a pandas DataFrame.
    NOTE: This is a basic simulator and may not handle all SQL syntax correctly.
    It's primarily for displaying expected/actual results based on simple queries.
    The LLM evaluation is the primary method for judging correctness.
    """
    if not isinstance(sample_table, pd.DataFrame) or sample_table.empty:
        return "Invalid or empty sample table provided for simulation."

    try:
        # Very basic parsing - attempts common patterns. Likely to fail on complex queries.
        query = query.strip().lower().replace(";", "")

        # Handle COUNT(*)
        if re.match(r"select\s+count\(\s*\*\s*\)\s+from\s+\w+", query):
            return pd.DataFrame({"count": [len(sample_table)]})

        # Handle AVG(column)
        avg_match = re.match(r"select\s+avg\((\w+)\)\s+from\s+\w+", query)
        if avg_match:
            col = avg_match.group(1)
            if col in sample_table.columns:
                return pd.DataFrame({f"avg_{col}": [sample_table[col].mean()]})
            else: return f"Column '{col}' not found for AVG."

        # Handle SUM(column) with GROUP BY (simple case)
        sum_group_match = re.match(r"select\s+(\w+(?:\.\w+)?)\s*,\s*sum\((\w+(?:\.\w+)?)\)\s*(?:as\s+\w+)?\s+from\s+[\w\s\.\=]+group\s+by\s+\1", query, re.IGNORECASE)
        if sum_group_match:
            group_col = sum_group_match.group(1).split('.')[-1] # Handle potential alias.col
            sum_col = sum_group_match.group(2).split('.')[-1]
            if group_col in sample_table.columns and sum_col in sample_table.columns:
                 # Pandas groupby().sum() can simulate this
                result = sample_table.groupby(group_col)[sum_col].sum().reset_index()
                # Rename sum column if needed (basic alias handling)
                alias_match = re.search(r"sum\(\w+(?:\.\w+)?\)\s+as\s+(\w+)", query, re.IGNORECASE)
                if alias_match:
                    result = result.rename(columns={sum_col: alias_match.group(1)})
                return result
            else: return f"Columns '{group_col}' or '{sum_col}' not found for SUM/GROUP BY."


        # Handle SELECT *
        if query.startswith("select *"):
            # Basic WHERE clause handling (simple conditions)
            where_match = re.search(r"where\s+(.*)", query)
            if where_match:
                condition = where_match.group(1)
                # VERY basic condition parsing - replace SQL operators. Prone to errors.
                try:
                    condition = condition.replace("=", "==").replace("'", "\"").replace(" and ", " & ").replace(" or ", " | ")
                    # Handle IN operator crudely
                    in_match = re.search(r"(\w+)\s+in\s+\(([^)]+)\)", condition)
                    if in_match:
                        col_in, values_in = in_match.groups()
                        values_list = [v.strip().strip('"') for v in values_in.split(',')]
                        condition = condition.replace(in_match.group(0), f"{col_in}.isin({values_list})")

                    # Handle > , < , >=, <= (ensure they are not part of strings)
                    condition = re.sub(r"(\w+)\s*(>|>=|<|<=)\s*(\d+)", r"\1 \2 \3", condition)
                    condition = re.sub(r"(\w+)\s*(>|>=|<|<=)\s*'([^']*)'", r"\1 \2 '\3'", condition) # Dates/Strings might fail

                    result = sample_table.query(condition)
                except Exception as e_cond:
                     return f"Error simulating WHERE clause '{condition}': {e_cond}"
            else:
                result = sample_table.copy()

            # Basic ORDER BY
            order_match = re.search(r"order by\s+(\w+)(\s+desc)?", query)
            if order_match:
                order_col = order_match.group(1)
                desc = bool(order_match.group(2))
                if order_col in result.columns:
                    result = result.sort_values(by=order_col, ascending=not desc)
                else: return f"Column '{order_col}' not found for ORDER BY."

            # Basic LIMIT
            limit_match = re.search(r"limit\s+(\d+)", query)
            if limit_match:
                limit = int(limit_match.group(1))
                result = result.head(limit)

            return result.reset_index(drop=True)

        # If no specific pattern matches, return error
        return "Simulation for this specific query type is not fully supported."

    except Exception as e:
        # Catch any other unexpected error during simulation
        # import traceback
        # traceback.print_exc() # Uncomment for detailed debug trace
        return f"Error simulating query: {str(e)}"


def get_table_schema(table_name, tables_dict):
    """Gets column names for a given table name."""
    if table_name in tables_dict:
        # Return column names as a list of strings
        return tables_dict[table_name].columns.astype(str).tolist()
    return []

def evaluate_answer_with_llm(question_data, student_answer, original_tables_dict):
    """Evaluate the user's answer using Gemini API based on question intent and schema."""
    if not student_answer.strip():
        return "Please provide an answer.", False, "N/A", "N/A"

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
                schema_info += f"Table '{name}': Columns {columns}\n"
            else:
                # Try to infer from sample_table if original not found (less ideal)
                fallback_cols = question_data.get("sample_table", pd.DataFrame()).columns.astype(str).tolist()
                if fallback_cols:
                     schema_info += f"Table '{name}' (inferred): Columns {fallback_cols}\n"
                else:
                    schema_info += f"Table '{name}': Schema not found.\n"

    # --- LLM Prompt ---
    prompt = f"""
    You are an expert SQL evaluator acting as a friendly SQL mentor. Analyze the student's SQL query based on the question asked and the provided table schemas. Assume standard SQL syntax (like MySQL/PostgreSQL).

    **Evaluation Task:**

    1.  **Question:** {question}
    2.  **Relevant Table Schemas:**
        {schema_info.strip()}
    3.  **Student's SQL Query:**
        ```sql
        {student_answer}
        ```

    **Analysis Instructions:**

    * **Correctness:** Does the student's query accurately and completely answer the **Question** based on the **Relevant Table Schemas**? Consider edge cases if applicable (e.g., users with no orders).
    * **Validity:** Is the query syntactically valid SQL? Briefly mention any syntax errors.
    * **Logic:** Does the query use appropriate SQL clauses (SELECT, FROM, WHERE, JOIN, GROUP BY, ORDER BY, aggregates, etc.) correctly for the task? Is the logic sound?
    * **Alternatives:** Briefly acknowledge if the student used a valid alternative approach (e.g., different JOIN type if appropriate, subquery vs. JOIN). Efficiency is a minor point unless significantly poor.
    * **Feedback:** Provide clear, constructive feedback in a friendly, encouraging, casual Hindi tone (like a helpful senior or 'bhaiya' talking to a learner).
        * If correct: Praise the student (e.g., "Wah yaar, zabardast query likhi hai! Bilkul sahi logic lagaya.") and briefly explain *why* it's correct or mention if it's a common/good way.
        * If incorrect: Gently point out the error (e.g., "Arre yaar, yahaan thoda sa check karo..." or "Ek chhoti si galti ho gayi hai..."). Explain *what* is wrong (syntax, logic, wrong columns/tables, missed conditions) and *why*. Suggest how to fix it or what the correct concept/approach might involve (e.g., "Yahaan `LEFT JOIN` use karna better rahega kyunki..." or "WHERE clause mein condition check karo..."). Avoid just giving the full correct query away unless needed for a specific small fix explanation. Keep it encouraging.
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
             llm_output = response.text


        llm_output = llm_output.strip()
        # print(f"DEBUG: LLM Raw Output:\n---\n{llm_output}\n---") # Uncomment for debugging

        # --- Parse LLM Response ---
        feedback_llm = llm_output
        is_correct_llm = False

        # Find the verdict line (case-insensitive, anchoring to end of string potentially safer)
        verdict_match = re.search(r'^Verdict:\s*(Correct|Incorrect)$', llm_output, re.MULTILINE | re.IGNORECASE)

        if verdict_match:
            verdict = verdict_match.group(1).lower()
            is_correct_llm = (verdict == "correct")
            # Remove the verdict line from the feedback string for cleaner display
            feedback_llm = llm_output[:verdict_match.start()].strip()
        else:
            # If verdict line is missing or malformed, log it, default to incorrect
            st.warning(f"⚠️ System Warning: Could not parse final verdict from LLM response. Please review feedback carefully.")
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
    simulation_table = question_data.get("sample_table", pd.DataFrame())
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
            "feedback_received": ans["feedback"]
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
        f"  Q: {item['question']}\n    A: {item['your_answer']}\n    F: {item['feedback_received']}"
        for item in incorrect_answers
    ]) if incorrect_answers else "Koi nahi! Sab sahi the!"

    prompt = f"""
    Ek student ne SQL quiz diya hai. Unke performance ka summary neeche hai:

    Total Questions: {total_q}
    Correct Answers: {correct_q_count}
    Score: {score:.2f}%

    Correctly Answered Questions:
    {chr(10).join(f'  - {q}' for q in correct_questions) if correct_questions else '  (None)'}

    Incorrectly Answered Questions (with their answer and feedback given):
    {incorrect_summary}

    Task: Ab ek dost ki tarah, casual Hindi mein overall performance ka ek summary feedback do.
    - Achhe performance ko appreciate karo.
    - Jin topics mein galti hui (incorrect answers ke basis par), unko highlight karo aur improve karne ke liye encourage karo. General areas batao jaise ki 'JOINs pe thoda aur dhyan do' ya 'Aggregate functions aapse miss ho gaye'.
    - Ek positive aur motivating tone rakho.
    """

    try:
        response = model.generate_content(prompt)
        if response.parts:
            feedback_summary["overall_feedback"] = "".join(part.text for part in response.parts).strip()
        else:
             feedback_summary["overall_feedback"] = response.text.strip()

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
    return "✅" if is_correct else "❌" # Changed emojis slightly


# --- Streamlit App ---

# --- Start Screen ---
if not st.session_state.quiz_started:
    st.title("🚀 SQL Mentor - Interactive SQL Practice")

    st.markdown("### Apne SQL Skills Ko Test Aur Improve Karein!")

    st.markdown("""
    **📌 Important Note:**
    - This quiz assumes standard **SQL syntax** (similar to MySQL/PostgreSQL).
    - Your queries will be evaluated by an AI for correctness and logic.
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
                if ans_data["is_correct"]:
                    st.success(ans_data['feedback'])
                else:
                    st.error(ans_data['feedback'])

                # Display simulated results if available
                st.markdown("---")
                col_sim1, col_sim2 = st.columns(2)
                with col_sim1:
                    st.write("**Simulated Result (Aapka Query):**")
                    if isinstance(ans_data["actual_result"], pd.DataFrame):
                        st.dataframe(ans_data["actual_result"], hide_index=True)
                    elif isinstance(ans_data["actual_result"], str):
                         st.warning(f"Simulation Note: {ans_data['actual_result']}") # Show simulation errors/notes
                    else:
                        st.info("Simulation result not available.")

                with col_sim2:
                     st.write("**Simulated Result (Example Correct Query):**")
                     if isinstance(ans_data["expected_result"], pd.DataFrame):
                         st.dataframe(ans_data["expected_result"], hide_index=True)
                     elif isinstance(ans_data["expected_result"], str):
                         st.warning(f"Simulation Note: {ans_data['expected_result']}")
                     else:
                         st.info("Simulation result not available.")
        st.markdown("---")


    # --- Current Question ---
    current_q_index = st.session_state.current_question
    if current_q_index < len(sql_questions):
        question_data = sql_questions[current_q_index]

        st.subheader(f"Sawaal {current_q_index + 1} / {len(sql_questions)}")
        st.markdown(f"**{question_data['question']}**")

        st.write("**Relevant Table(s) Preview:**")
        # Show previews of tables relevant to *this* question
        rel_tables = question_data["relevant_tables"]
        tabs = st.tabs([f"{name.capitalize()} Table" for name in rel_tables])
        for i, table_name in enumerate(rel_tables):
            with tabs[i]:
                if table_name in original_tables:
                    st.dataframe(original_tables[table_name], hide_index=True)
                else:
                    st.warning(f"Schema/Preview for '{table_name}' not found.")


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
        st.warning("Quiz state error. Restarting.")
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
    for i, ans_data in enumerate(st.session_state.user_answers):
        with st.expander(f"Question {i + 1}: {ans_data['question']} {get_emoji(ans_data['is_correct'])}", expanded=False):
            st.write(f"**Aapka Jawaab:**")
            st.code(ans_data['student_answer'], language='sql')
            st.write(f"**SQL Mentor Feedback:**")
            if ans_data["is_correct"]:
                st.success(ans_data['feedback'])
            else:
                st.error(ans_data['feedback'])
             # Display simulated results if available
            st.markdown("---")
            col_sim1, col_sim2 = st.columns(2)
            with col_sim1:
                 st.write("**Simulated Result (Aapka Query):**")
                 if isinstance(ans_data["actual_result"], pd.DataFrame):
                     st.dataframe(ans_data["actual_result"], hide_index=True)
                 elif isinstance(ans_data["actual_result"], str):
                      st.warning(f"Simulation Note: {ans_data['actual_result']}")
                 else:
                      st.info("Simulation result not available.")
            with col_sim2:
                 st.write("**Simulated Result (Example Correct Query):**")
                 if isinstance(ans_data["expected_result"], pd.DataFrame):
                     st.dataframe(ans_data["expected_result"], hide_index=True)
                 elif isinstance(ans_data["expected_result"], str):
                      st.warning(f"Simulation Note: {ans_data['expected_result']}")
                 else:
                      st.info("Simulation result not available.")

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
             if st.button("Need Help? Connect with a Mentor"):
                  # Redirect using JavaScript - Replace URL if needed
                 st.markdown('<meta http-equiv="refresh" content="0; url=https://www.corporatebhaiya.com/" />', unsafe_allow_html=True)
                 # st.link_button("Connect with a Mentor", "https://www.corporatebhaiya.com/") # Alternative simple link
        else:
             st.success("Bahut badhiya score! Keep it up! 👍")
             if st.button("Next Steps? Mock Interview Practice"):
                 st.markdown('<meta http-equiv="refresh" content="0; url=https://www.corporatebhaiya.com/mock-interview" />', unsafe_allow_html=True) # Example specific link
                 # st.link_button("Prepare for Interviews", "https://www.corporatebhaiya.com/mock-interview")


    # --- Detailed Feedback Section ---
    if st.session_state.show_detailed_feedback:
        st.markdown("---")
        st.subheader("📈 Detailed Performance Analysis (AI Generated)")
        with st.spinner("AI performance summary generate kar raha hai..."):
            performance_feedback = analyze_performance(st.session_state.user_answers)

        st.write("**Overall Feedback:**")
        st.info(performance_feedback["overall_feedback"]) # Display LLM generated summary

        st.write("**Strengths (Questions you answered correctly):**")
        if performance_feedback["strengths"]:
            for i, question in enumerate(performance_feedback["strengths"]):
                st.success(f"{i + 1}. {question} ✅")
        else:
            st.write("_(No questions answered correctly in this attempt.)_")

        st.write("**Areas for Improvement (Questions answered incorrectly):**")
        if performance_feedback["weaknesses"]:
            for i, question in enumerate(performance_feedback["weaknesses"]):
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
