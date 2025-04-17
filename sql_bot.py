import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import duckdb # Import DuckDB

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
# WARNING: Hardcoding API keys is insecure. Consider environment variables or secrets for deployment.
gemini_api_key = "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k" # Your specific API Key

if not gemini_api_key: # Basic check if the key is empty
    st.error("🚨 Gemini API Key is missing in the code.")
    st.stop()

try:
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"🚨 Failed to configure Gemini API or access the model: {e}")
    st.stop()


# --- Sample Data ---
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
    "order_date": pd.to_datetime(["2024-02-01", "2024-02-05", "2024-02-10", "2024-02-15", "2024-02-20"]),
    "status": ["Completed", "pending", "Completed", "Shipped", "Cancelled"]  # Using lowercase "pending" for consistency
})
original_tables = {
    "users": users_table,
    "orders": orders_table
}

# --- SQL Questions List ---
sql_questions = [
    { "question": "Write a SQL query to get all details about users from the 'users' table.", "correct_answer_example": "SELECT * FROM users;", "sample_table": users_table, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to count the total number of users in the 'users' table.", "correct_answer_example": "SELECT COUNT(*) AS user_count FROM users;", "sample_table": users_table, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to get all users older than 30 from the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE age > 30;", "sample_table": users_table, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to find all orders with a status of 'Pending' from the 'orders' table.", "correct_answer_example": "SELECT * FROM orders WHERE LOWER(status) = 'pending';", "sample_table": orders_table, "relevant_tables": ["orders"] },  # Updated to use LOWER()
    { "question": "Write a SQL query to find the most recent order from the 'orders' table by order date.", "correct_answer_example": "SELECT * FROM orders ORDER BY order_date DESC LIMIT 1;", "sample_table": orders_table, "relevant_tables": ["orders"] },
    { "question": "Write a SQL query to find the average order amount from the 'orders' table.", "correct_answer_example": "SELECT AVG(amount) AS average_amount FROM orders;", "sample_table": orders_table, "relevant_tables": ["orders"] },
    { "question": "Write a SQL query to find users from 'New York' or 'Chicago' in the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE LOWER(city) IN (LOWER('New York'), LOWER('Chicago'));", "sample_table": users_table, "relevant_tables": ["users"] },  # Updated to use LOWER()
    { "question": "Write a SQL query to find users who have not placed any orders. Use the 'users' and 'orders' tables.", "correct_answer_example": "SELECT u.* FROM users u LEFT JOIN orders o ON u.user_id = o.user_id WHERE o.order_id IS NULL;", "sample_table": users_table, "relevant_tables": ["users", "orders"] },
    { "question": "Write a SQL query to calculate the total amount spent by each user by joining the 'users' and 'orders' tables.", "correct_answer_example": "SELECT u.name, SUM(o.amount) AS total_spent FROM users u JOIN orders o ON u.user_id = o.user_id GROUP BY u.name ORDER BY u.name;", "sample_table": users_table, "relevant_tables": ["users", "orders"] },
    { "question": "Write a SQL query to count how many orders each user has placed using a LEFT JOIN between 'users' and 'orders'. Include users with zero orders.", "correct_answer_example": "SELECT u.name, COUNT(o.order_id) AS order_count FROM users u LEFT JOIN orders o ON u.user_id = o.user_id GROUP BY u.name ORDER BY u.name;", "sample_table": users_table, "relevant_tables": ["users", "orders"] }
]

# --- Session State Initialization ---
if "user_answers" not in st.session_state: st.session_state.user_answers = []
if "current_question" not in st.session_state: st.session_state.current_question = 0
if "quiz_started" not in st.session_state: st.session_state.quiz_started = False
if "quiz_completed" not in st.session_state: st.session_state.quiz_completed = False
if "show_detailed_feedback" not in st.session_state: st.session_state.show_detailed_feedback = False

# --- Helper Functions ---

def make_query_case_insensitive(sql_query):
    """Makes string comparisons in SQL queries case-insensitive by adding LOWER() function"""
    # Common patterns for string comparisons in SQL
    patterns = [
        # status = 'value' pattern
        (r"status\s*=\s*'([^']*)'", r"LOWER(status) = LOWER('\1')"),
        # city = 'value' pattern
        (r"city\s*=\s*'([^']*)'", r"LOWER(city) = LOWER('\1')"),
        # name = 'value' pattern
        (r"name\s*=\s*'([^']*)'", r"LOWER(name) = LOWER('\1')"),
        # email = 'value' pattern
        (r"email\s*=\s*'([^']*)'", r"LOWER(email) = LOWER('\1')"),
        # status IN ('value1', 'value2') pattern
        (r"status\s+IN\s*\(([^)]*)\)", lambda m: f"LOWER(status) IN ({','.join([f'LOWER({x.strip()})' for x in m.group(1).split(',')])})")
    ]
    
    modified_query = sql_query
    for pattern, replacement in patterns:
        modified_query = re.sub(pattern, replacement, modified_query, flags=re.IGNORECASE)
    
    return modified_query

def smart_query_evaluator(sql_query, tables_dict):
    """Evaluates SQL query with automatic case sensitivity handling"""
    if not sql_query or not sql_query.strip():
        return "Simulation Error: No query provided.", False
    if not tables_dict:
        return "Simulation Error: No tables provided for context.", False
    
    # Try to make the query case-insensitive
    case_insensitive_query = make_query_case_insensitive(sql_query)
    case_fix_applied = (case_insensitive_query != sql_query)
    
    # Try the case-insensitive query first
    con = None
    try:
        con = duckdb.connect(database=':memory:', read_only=False)
        for table_name, df in tables_dict.items():
            if isinstance(df, pd.DataFrame): con.register(str(table_name), df)
            else: print(f"Warning [simulate_query]: Item '{table_name}' not a DataFrame.")
        
        # Try the case-insensitive query first
        try:
            result_df = con.execute(case_insensitive_query).df()
            con.close()
            return result_df, case_fix_applied
        except Exception as e:
            # If case-insensitive query fails, try the original query
            try:
                result_df = con.execute(sql_query).df()
                con.close()
                return result_df, False
            except Exception as e2:
                error_message = f"Simulation Error: Failed to execute query. Reason: {str(e2)}"
                try:
                    e_str = str(e2).lower()
                    binder_match = re.search(r'(binder error|catalog error|parser error).*referenced column "([^"]+)" not found', e_str)
                    syntax_match = re.search(r'syntax error.*at or near ""([^"]+)""', e_str)
                    if binder_match: error_message += f"\n\n**Hint:** Use single quotes (') for text values like `'{binder_match.group(2)}'` instead of double quotes (\")."
                    elif syntax_match: error_message += f"\n\n**Hint:** Use single quotes (') for text values like `'{syntax_match.group(1)}'` instead of double quotes (\")."
                except Exception as e_hint: print(f"Error generating hint: {e_hint}")
                if con:
                    try: con.close()
                    except: pass
                return error_message, False
    except Exception as e:
        error_message = f"Simulation Error: Failed to execute query. Reason: {str(e)}"
        try:
            e_str = str(e).lower()
            binder_match = re.search(r'(binder error|catalog error|parser error).*referenced column "([^"]+)" not found', e_str)
            syntax_match = re.search(r'syntax error.*at or near ""([^"]+)""', e_str)
            if binder_match: error_message += f"\n\n**Hint:** Use single quotes (') for text values like `'{binder_match.group(2)}'` instead of double quotes (\")."
            elif syntax_match: error_message += f"\n\n**Hint:** Use single quotes (') for text values like `'{syntax_match.group(1)}'` instead of double quotes (\")."
        except Exception as e_hint: print(f"Error generating hint: {e_hint}")
        if con:
            try: con.close()
            except: pass
        return error_message, False

def simulate_query_duckdb(sql_query, tables_dict):
    """Legacy simulation function that calls the smart evaluator"""
    result, _ = smart_query_evaluator(sql_query, tables_dict)
    return result

def get_table_schema(table_name, tables_dict):
    """Gets column names for a given table name."""
    if table_name in tables_dict and isinstance(tables_dict[table_name], pd.DataFrame):
        return tables_dict[table_name].columns.astype(str).tolist()
    return []

def evaluate_answer_with_llm(question_data, student_answer, original_tables_dict):
    """Evaluate the user's answer using Gemini API and simulate using DuckDB."""
    if not student_answer.strip(): return "Please provide an answer.", False, "N/A", "N/A", "No input.", False
    question = question_data["question"]; relevant_table_names = question_data["relevant_tables"]; correct_answer_example = question_data["correct_answer_example"]
    schema_info = ""
    if not relevant_table_names: schema_info = "No table schema context.\n"
    else:
        for name in relevant_table_names:
            columns = get_table_schema(name, original_tables_dict)
            if columns:
                try: df = original_tables_dict[name]; dtypes = df.dtypes.to_string() if isinstance(df, pd.DataFrame) else "N/A"; schema_info += f"Table '{name}': Columns {columns}\n DataTypes:\n{dtypes}\n\n"
                except Exception as e_schema: schema_info += f"Table '{name}': Columns {columns} (Schema Error: {e_schema})\n\n"
            else: schema_info += f"Table '{name}': Schema not found.\n"

    # Add note about case-insensitivity to the prompt
    case_insensitivity_note = """
    Note: This SQL quiz accepts case-insensitive string comparisons. For example, both of these are considered correct:
    - WHERE status = 'pending'
    - WHERE status = 'Pending'
    - WHERE LOWER(status) = 'pending'
    """

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
    
    {case_insensitivity_note}

    **Analysis Instructions:**

    * **Correctness:** Does the student's query accurately and completely answer the **Question** based on the **Relevant Table Schemas**? Consider edge cases if applicable (e.g., users with no orders, data types for comparisons).
    * **Validity:** Is the query syntactically valid SQL? Briefly mention any syntax errors.
    * **Logic:** Does the query use appropriate SQL clauses (SELECT, FROM, WHERE, JOIN, GROUP BY, ORDER BY, aggregates, etc.) correctly for the task? Is the logic sound? Are comparisons appropriate for the data types?
    * **Alternatives:** Briefly acknowledge if the student used a valid alternative approach (e.g., different JOIN type if appropriate, subquery vs. JOIN). Efficiency is a minor point unless significantly poor.
    * **Feedback:** Provide clear, constructive feedback in a friendly, encouraging, casual Hindi tone (like a helpful senior or 'bhaiya' talking to a learner).
        * If correct: Praise the student (e.g., "Wah yaar, zabardast query likhi hai! Bilkul sahi logic lagaya.") and briefly explain *why* it's correct or mention if it's a common/good way.
        * If incorrect: Gently point out the error (e.g., "Arre yaar, yahaan thoda sa check karo..." or "Ek chhoti si galti ho gayi hai..."). Explain *what* is wrong (syntax - like using " vs ' for strings, logic, columns, etc.)... Suggest how to fix it or what the correct concept/approach might involve (e.g., "Yahaan `LEFT JOIN` use karna better rahega kyunki..." or "WHERE clause mein condition check karo... Status ek text hai, toh quotes use karna hoga..."). Avoid just giving the full correct query away unless needed for a specific small fix explanation. Keep it encouraging.
    * **Verdict:** Conclude your entire response with *exactly* one line formatted as: "Verdict: Correct" or "Verdict: Incorrect". This line MUST be the very last line.

    **Begin Evaluation:**
    """

    feedback_llm = "AI feedback failed."; is_correct_llm = False; llm_output = "Error: No LLM response."
    try:
        response = model.generate_content(prompt);
        if response.parts: llm_output = "".join(part.text for part in response.parts)
        else: llm_output = response.text
        llm_output = llm_output.strip(); verdict_match = re.search(r'^Verdict:\s*(Correct|Incorrect)\s*$', llm_output, re.M | re.I)
        if verdict_match: is_correct_llm = (verdict_match.group(1).lower() == "correct"); feedback_llm = llm_output[:verdict_match.start()].strip()
        else: st.warning(f"⚠️ Could not parse AI verdict."); print(f"WARNING: Could not parse verdict:\n{llm_output}"); feedback_llm = llm_output + "\n\n_(System Note: Correctness check failed.)_"; is_correct_llm = False
        feedback_llm = feedback_llm.replace("student", "aap")
    except Exception as e: st.error(f"🚨 AI Error: {e}"); print(f"ERROR: Gemini call: {e}"); feedback_llm = f"AI feedback error: {e}"; is_correct_llm = False; llm_output = f"Error: {e}"

    # Use smart query evaluator for both student answer and correct example
    actual_result_sim, case_fix_applied = smart_query_evaluator(student_answer, original_tables_dict)
    expected_result_sim, _ = smart_query_evaluator(correct_answer_example, original_tables_dict)
    
    return feedback_llm, is_correct_llm, expected_result_sim, actual_result_sim, llm_output, case_fix_applied

def calculate_score(user_answers):
    """Calculate the score based on correct answers."""
    if not user_answers: return 0
    correct = sum(1 for ans in user_answers if ans.get("is_correct", False))
    total = len(user_answers)
    return (correct / total) * 100 if total > 0 else 0

def analyze_performance(use
(Content truncated due to size limit. Use line ranges to read in chunks)
