import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import mysql.connector
from mysql.connector import Error

# --- Custom CSS ---
hide_streamlit_style = """
<style>
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
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Set up Gemini API ---
gemini_api_key = "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k"  # Replace with your actual Gemini API Key
if not gemini_api_key or gemini_api_key == "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k":
    st.error("🚨 Gemini API Key is missing. Please add your key in the code.")
    st.stop()

try:
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"🚨 Failed to configure Gemini API: {e}")
    st.stop()

# --- MySQL Configuration ---
mysql_config = {
    'host': 'localhost',  # Update with your MySQL host
    'user': 'your_username',  # Update with your MySQL user
    'password': 'your_password',  # Update with your MySQL password
    'database': 'sql_quiz_db'  # Update with your MySQL database
}

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
    "status": ["Completed", "Pending", "Completed", "Shipped", "Cancelled"]
})

original_tables = {
    "users": users_table,
    "orders": orders_table
}

# --- SQL Questions List ---
sql_questions = [
    {"question": "Write a SQL query to get all details about users from the 'users' table.", "correct_answer_example": "SELECT * FROM users;", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to count the total number of users in the 'users' table.", "correct_answer_example": "SELECT COUNT(*) AS user_count FROM users;", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to get all users older than 30 from the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE age > 30;", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to find all orders with a status of 'Pending' from the 'orders' table.", "correct_answer_example": "SELECT * FROM orders WHERE status = 'Pending';", "sample_table": orders_table, "relevant_tables": ["orders"]},
    {"question": "Write a SQL query to find users from 'chicago' in the 'users' table (test case-insensitivity).", "correct_answer_example": "SELECT * FROM users WHERE city = 'Chicago';", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to find the most recent order from the 'orders' table by order date.", "correct_answer_example": "SELECT * FROM orders ORDER BY order_date DESC LIMIT 1;", "sample_table": orders_table, "relevant_tables": ["orders"]},
    {"question": "Write a SQL query to find the average order amount from the 'orders' table.", "correct_answer_example": "SELECT AVG(amount) AS average_amount FROM orders;", "sample_table": orders_table, "relevant_tables": ["orders"]},
    {"question": "Write a SQL query to find users from 'New York' or 'Chicago' in the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE city IN ('New York', 'Chicago');", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to find users who have not placed any orders. Use the 'users' and 'orders' tables.", "correct_answer_example": "SELECT u.* FROM users u LEFT JOIN orders o ON u.user_id = o.user_id WHERE o.order_id IS NULL;", "sample_table": users_table, "relevant_tables": ["users", "orders"]},
    {"question": "Write a SQL query to calculate the total amount spent by each user by joining the 'users' and 'orders' tables.", "correct_answer_example": "SELECT u.name, SUM(o.amount) AS total_spent FROM users u JOIN orders o ON u.user_id = o.user_id GROUP BY u.name ORDER BY u.name;", "sample_table": users_table, "relevant_tables": ["users", "orders"]},
    {"question": "Write a SQL query to count how many orders each user has placed using a LEFT JOIN between 'users' and 'orders'. Include users with zero orders.", "correct_answer_example": "SELECT u.name, COUNT(o.order_id) AS order_count FROM users u LEFT JOIN orders o ON u.user_id = o.user_id GROUP BY u.name ORDER BY u.name;", "sample_table": users_table, "relevant_tables": ["users", "orders"]}
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

# --- Helper Functions ---

def get_mysql_data_type(dtype):
    """Map pandas data types to MySQL data types."""
    dtype_str = str(dtype).lower()
    if 'int' in dtype_str:
        return 'INT'
    elif 'float' in dtype_str:
        return 'DECIMAL(10,2)'
    elif 'datetime' in dtype_str:
        return 'DATETIME'
    else:
        return 'VARCHAR(255)'

def create_mysql_tables(tables_dict, conn):
    """Create MySQL tables from pandas DataFrames."""
    cursor = conn.cursor()
    for table_name, df in tables_dict.items():
        if not isinstance(df, pd.DataFrame):
            continue
        # Define columns with appropriate MySQL data types
        columns = []
        for col, dtype in df.dtypes.items():
            mysql_type = get_mysql_data_type(dtype)
            columns.append(f"`{col}` {mysql_type}")
        create_table_query = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({', '.join(columns)})"
        cursor.execute(create_table_query)
        # Insert data
        for _, row in df.iterrows():
            placeholders = ', '.join(['%s'] * len(row))
            insert_query = f"INSERT INTO `{table_name}` VALUES ({placeholders})"
            cursor.execute(insert_query, tuple(row))
    conn.commit()
    cursor.close()

def standardize_quotes(sql_query):
    """Convert double quotes to single quotes for string literals, preserving double quotes for identifiers."""
    # Replace double-quoted string literals with single quotes
    # Matches "text" but not "table_name" as identifier
    pattern = r'(\b\w+\b\s*=\s*|IN\s*\()\"([^"]+)\"'
    standardized_query = re.sub(pattern, r"\1'\2'", sql_query)
    return standardized_query

def simulate_query_mysql(sql_query, tables_dict):
    """Simulates an SQL query using MySQL on in-memory pandas DataFrames."""
    if not sql_query or not sql_query.strip():
        return "Simulation Error: No query provided."
    if not tables_dict:
        return "Simulation Error: No tables provided for context."

    conn = None
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(**mysql_config)
        # Create tables
        create_mysql_tables(tables_dict, conn)
        cursor = conn.cursor()

        # Standardize quotes (convert double to single for string literals)
        modified_sql_query = standardize_quotes(sql_query)

        # Execute the query
        cursor.execute(modified_sql_query)
        if cursor.description:
            # Fetch results for SELECT queries
            results = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            result_df = pd.DataFrame(results, columns=columns)
            cursor.close()
            conn.close()
            return result_df
        else:
            # For non-SELECT queries (unlikely in this quiz)
            conn.commit()
            cursor.close()
            conn.close()
            return pd.DataFrame()  # Return empty DataFrame for non-SELECT

    except Error as e:
        error_message = f"Simulation Error: Failed to execute query. Reason: {str(e)}"
        # Parse MySQL-specific errors
        e_str = str(e).lower()
        table_match = re.search(r"table '.*\.([^']+)' doesn't exist", e_str)
        column_match = re.search(r"unknown column '([^']+)'", e_str)
        syntax_match = re.search(r"you have an error in your sql syntax.*near '([^']+)'", e_str)

        if table_match:
            error_message += f"\n\n**Hint:** Table '{table_match.group(1)}' might be misspelled. Available tables: {list(tables_dict.keys())}."
        elif column_match:
            error_message += f"\n\n**Hint:** Column '{column_match.group(1)}' might be misspelled or doesn't exist."
        elif syntax_match:
            error_message += f"\n\n**Hint:** Check syntax near '{syntax_match.group(1)}'. Use single quotes (') for strings."
        else:
            error_message += "\n\n**Hint:** Check your syntax, table/column names, and use single quotes (') for strings."

        print(f"ERROR [simulate_query_mysql]: {error_message}\nOriginal Query: {sql_query}\nAttempted Query: {modified_sql_query}")
        if conn:
            try:
                conn.close()
            except:
                pass
        return error_message

def get_table_schema(table_name, tables_dict):
    """Gets column names for a given table name."""
    if table_name in tables_dict and isinstance(tables_dict[table_name], pd.DataFrame):
        return tables_dict[table_name].columns.astype(str).tolist()
    return []

def evaluate_answer_with_llm(question_data, student_answer, original_tables_dict):
    """Evaluate the user's answer using Gemini API and simulate using MySQL."""
    if not student_answer.strip():
        return "Please provide an answer.", False, "N/A", "N/A", "No input."

    question = question_data["question"]
    relevant_table_names = question_data["relevant_tables"]
    correct_answer_example = question_data["correct_answer_example"]

    schema_info = ""
    if not relevant_table_names:
        schema_info = "No table schema context.\n"
    else:
        for name in relevant_table_names:
            columns = get_table_schema(name, original_tables_dict)
            if columns:
                try:
                    df = original_tables_dict[name]
                    dtypes = df.dtypes.to_string() if isinstance(df, pd.DataFrame) else "N/A"
                    schema_info += f"Table '{name}': Columns {columns}\n DataTypes:\n{dtypes}\n\n"
                except Exception as e_schema:
                    schema_info += f"Table '{name}': Columns {columns} (Schema Error: {e_schema})\n\n"
            else:
                schema_info += f"Table '{name}': Schema not found.\n"

    prompt = f"""
You are an expert SQL evaluator acting as a friendly SQL mentor. Analyze the student's SQL query based on the question asked and the provided table schemas (including data types). Assume **MySQL** syntax.

**Evaluation Task:**

1. **Question:** {question}
2. **Relevant Table Schemas:**
{schema_info.strip()}
3. **Student's SQL Query:**
```sql
{student_answer}

    **Analysis Instructions:**

    * **Correctness:** Does the student's query accurately and completely answer the **Question** based on the **Relevant Table Schemas**? Consider edge cases if applicable (e.g., users with no orders, data types for comparisons).
        **>>> IMPORTANT QUIZ CONTEXT FOR CORRECTNESS <<<**
        For *this specific quiz*, assume that simple equality comparisons (`=`) involving the text columns `'status'` (in `orders`) and `'city'` (in `users`) are effectively **CASE-INSENSITIVE** (as is the default behavior in MySQL).
        Therefore, a query like `WHERE status = 'pending'` **should be considered CORRECT** if the question asks for 'Pending' status, even if the student did not use explicit `LOWER()` or `UPPER()` functions.
        Evaluate the *logic* of the query based on this assumed case-insensitivity for these specific columns (`status`, `city`). Penalize only if the core logic (joins, other conditions, selected columns etc.) is wrong.

    * **Validity:** Is the query syntactically valid SQL? Briefly mention any syntax errors unrelated to the case-insensitivity rule above.
    * **Logic:** Does the query use appropriate SQL clauses (SELECT, FROM, WHERE, JOIN, GROUP BY, ORDER BY, aggregates, etc.) correctly for the task? Is the logic sound? Are comparisons appropriate for the data types (keeping the case-insensitivity rule for `status`/`city` in mind)?
    * **Alternatives:** Briefly acknowledge if the student used a valid alternative approach (e.g., different JOIN type if appropriate, subquery vs. JOIN).
    * **Feedback:** Provide clear, constructive feedback in a friendly, encouraging, casual Hindi tone (like a helpful senior or 'bhaiya' talking to a learner).
        * If correct (considering the case-insensitivity rule): Praise the student (e.g., "Wah yaar, zabardast query likhi hai! Bilkul sahi logic lagaya.") and briefly explain *why* it's correct. You can optionally add a small note like "Aur haan, yaad rakhna ki asal databases mein kabhi kabhi case ka dhyaan rakhna padta hai, par yahaan is quiz ke liye yeh bilkul sahi hai!".
        * If incorrect (due to reasons *other* than case-sensitivity on `status`/`city`): Gently point out the error (e.g., "Arre yaar, yahaan thoda sa check karo..." or "Ek chhoti si galti ho gayi hai..."). Explain *what* is wrong (syntax, logic, columns, joins, other conditions etc.). Suggest how to fix it. **Do NOT mark the query incorrect or suggest using LOWER()/UPPER() *solely* because of case differences in the `status` or `city` columns if the rest of the logic is correct.**
    * **Verdict:** Conclude your entire response with *exactly* one line formatted as: "Verdict: Correct" or "Verdict: Incorrect". This line MUST be the very last line.

    **Begin Evaluation:**
    """
    # ***** MODIFIED PROMPT END *****


    feedback_llm = "AI feedback failed."; is_correct_llm = False; llm_output = "Error: No LLM response."
    try:
        response = model.generate_content(prompt);
        # Handle potential different response structures
        if hasattr(response, 'text'):
            llm_output = response.text
        elif hasattr(response, 'parts') and response.parts:
             llm_output = "".join(part.text for part in response.parts)
        else:
             try:
                 llm_output = f"AI Response Blocked or Empty. Prompt Feedback: {response.prompt_feedback}"
             except Exception:
                 llm_output = "Error: Received unexpected or empty response from AI."

        llm_output = llm_output.strip()
        verdict_match = re.search(r'^Verdict:\s*(Correct|Incorrect)\s*$', llm_output, re.M | re.I)
        if verdict_match:
            is_correct_llm = (verdict_match.group(1).lower() == "correct")
            feedback_llm = llm_output[:verdict_match.start()].strip()
            feedback_llm = re.sub(r'\s*Verdict:\s*(Correct|Incorrect)?\s*$', '', feedback_llm, flags=re.M | re.I).strip()
        else:
            st.warning(f"⚠️ Could not parse AI verdict from response.")
            print(f"WARNING: Could not parse verdict from LLM output:\n---\n{llm_output}\n---")
            feedback_llm = llm_output + "\n\n_(System Note: AI correctness check might be unreliable as verdict wasn't found.)_"
            is_correct_llm = False # Default to incorrect if verdict unclear

        feedback_llm = feedback_llm.replace("student", "aap")
    except Exception as e:
        st.error(f"🚨 AI Error during evaluation: {e}")
        print(f"ERROR: Gemini call failed: {e}")
        feedback_llm = f"AI feedback generation error: {e}"
        is_correct_llm = False
        llm_output = f"Error during AI call: {e}"

    # Simulate student's query (using the modified function)
    actual_result_sim = simulate_query_mysql(student_answer, original_tables_dict)
    # Simulate correct query (using the modified function for consistency)
    expected_result_sim = simulate_query_mysql(correct_answer_example, original_tables_dict)

    return feedback_llm, is_correct_llm, expected_result_sim, actual_result_sim, llm_output

# ... (Keep calculate_score, analyze_performance, get_emoji, display_simulation the same) ...
# ... (Keep Streamlit UI code: Start Screen, Quiz In Progress, Quiz Completed Screen, Fallback) ...

def calculate_score(user_answers):
    """Calculate the score based on correct answers."""
    if not user_answers: return 0
    correct = sum(1 for ans in user_answers if ans.get("is_correct", False))
    total = len(user_answers)
    return (correct / total) * 100 if total > 0 else 0

def analyze_performance(user_answers):
    """Analyze the user's performance and provide detailed feedback via LLM."""
    performance_data = { "strengths": [], "weaknesses": [], "overall_feedback": "Analysis could not be completed." }
    if not user_answers:
        performance_data["overall_feedback"] = "Koi jawaab nahi diya gaya. Analysis possible nahi hai."; return performance_data

    try:
        correct_q = [ans["question"] for ans in user_answers if ans.get("is_correct")]
        incorrect_ans = [{"question": ans["question"], "your_answer": ans["student_answer"], "feedback_received": ans.get("feedback", "N/A")} for ans in user_answers if not ans.get("is_correct")]
        performance_data["strengths"] = correct_q; performance_data["weaknesses"] = [item["question"] for item in incorrect_ans]
        total_q, correct_c, score = len(user_answers), len(correct_q), calculate_score(user_answers)

        # Prepare summary of incorrect answers for the prompt
        incorrect_summary = ""
        if incorrect_ans:
            incorrect_summary = "In sawaalon mein thodi galti hui:\n"
            for idx, item in enumerate(incorrect_ans):
                incorrect_summary += f"  {idx+1}. Sawaal: {item['question']}\n     Aapka Jawaab: `{item['your_answer']}`\n     Feedback Mila: {item['feedback_received'][:150]}...\n" # Limit feedback length
            incorrect_summary = incorrect_summary.strip()
        else:
            incorrect_summary = "Koi galat jawaab nahi! Bahut badhiya!"

        # Prepare summary of correct answers
        correct_summary = ""
        if correct_q:
            correct_summary = "Yeh sawaal bilkul sahi kiye:\n"
            for idx, q_text in enumerate(correct_q):
                correct_summary += f"  - {q_text}\n"
            correct_summary = correct_summary.strip()
        else:
            correct_summary = "Is baar koi jawaab sahi nahi hua."

        prompt = f"""
        Ek SQL learner ne ek practice quiz complete kiya hai. Unki performance ka analysis karke ek friendly, motivating summary feedback casual Hindi mein (jaise ek senior/mentor deta hai) provide karo.

        **Quiz Performance Summary:**
        - Total Questions Attempted: {total_q}
        - Correct Answers: {correct_c}
        - Final Score: {score:.2f}%

        **Correctly Answered Questions:**
        {correct_summary if correct_q else '(Koi nahi)'}

        **Incorrectly Answered Questions & Feedback:**
        {incorrect_summary if incorrect_ans else '(Koi nahi)'}

        **Task:**
        Ab, neeche diye gaye structure mein overall performance ka ek summary feedback do:
        1.  **Overall Impression:** Score aur general performance pe ek positive ya encouraging comment (e.g., "Overall performance kaafi achhi rahi!", "Thodi aur practice lagegi, but potential hai!").
        2.  **Strengths:** Agar kuch specific concepts sahi kiye hain (jo correct answers se pata chale), unko highlight karo (e.g., "SELECT aur WHERE clause ka use aache se samajh aa gaya hai.", "JOINs wale sawaal sahi kiye, yeh achhi baat hai!"). General rakho agar specific pattern na dikhe.
        3.  **Areas for Improvement:** Jo concepts galat hue (incorrect answers se related), unko gently point out karo. Focus on concepts, not just specific mistakes (e.g., "JOIN ka logic thoda aur clear karna hoga shayad.", "Aggregate functions (COUNT, AVG) pe dhyaan dena.", "Syntax ki chhoti-moti galtiyan ho rahi hain, jaise single quotes vs double quotes ka use."). Specific examples quote mat karo, general areas batao.
        4.  **Next Steps / Encouragement:** Kuch encouraging words aur aage kya karna chahiye (e.g., "Keep practicing!", "Concept X ko revise kar lena.", "Aise hi lage raho, SQL aa jayega!").

        Bas plain text mein feedback generate karna hai. Casual tone rakhna.
        """
    except Exception as data_prep_error:
        print(f"Error preparing data for analysis: {data_prep_error}")
        performance_data["overall_feedback"] = f"Analysis data preparation failed: {data_prep_error}"; return performance_data

    try:
        response = model.generate_content(prompt); generated_feedback = None
        # Handle potential response structures again
        if hasattr(response, 'text'):
            generated_feedback = response.text.strip()
        elif hasattr(response, 'parts') and response.parts:
             generated_feedback = "".join(part.text for part in response.parts).strip()
        else:
             try:
                 generated_feedback = f"AI Response Blocked or Empty. Prompt Feedback: {response.prompt_feedback}"
             except Exception:
                 generated_feedback = "Error: Received unexpected or empty response from AI for summary."

        if generated_feedback:
            performance_data["overall_feedback"] = generated_feedback
        else:
            performance_data["overall_feedback"] = "AI response format unclear or empty for summary."; print(f"Warning: Unexpected LLM response for summary.")
    except Exception as e:
        print(f"Error generating performance summary: {e}")
        performance_data["overall_feedback"] = f"Summary generation error from AI: {e}"
    return performance_data


def get_emoji(is_correct):
    return "✅" if is_correct else "❌"

def display_simulation(title, result_data):
    """Helper function to display simulation results (DataFrame or error)."""
    st.write(f"**{title}:**")
    if isinstance(result_data, pd.DataFrame):
        if result_data.empty:
            st.info("_(Simulation resulted in an empty table)_")
        else:
            # Use use_container_width to allow table to expand
            st.dataframe(result_data.reset_index(drop=True), hide_index=True, use_container_width=True)
    elif isinstance(result_data, str) and "Simulation Error" in result_data:
        # Display the error message from simulate_query_mysql directly
        st.warning(result_data, icon="⚠️")  # Changed to warning for simulation errors
    elif result_data == "N/A":
        st.info("_(Simulation not applicable or not run)_")
    elif isinstance(result_data, str):  # Catch other string messages if any
        st.info(f"_{result_data}_")
    else:
        # Fallback for unexpected types
        st.error(f"_(Unexpected simulation result type: {type(result_data)})_")
        print(f"DEBUG: Unexpected simulation data type: {type(result_data)}, value: {result_data}")



# --- Streamlit App ---

# --- Start Screen ---
if not st.session_state.quiz_started:
    st.title("🚀 SQL Mentor - Interactive SQL Practice")
    st.markdown("### Apne SQL Skills Ko Test Aur Improve Karein!")
    st.markdown("""
        **📌 Important Notes:**
        - This quiz uses standard **SQL syntax** (similar to MySQL/PostgreSQL).
        - String comparisons (like `WHERE city = 'new york'`) are simulated to be **case-insensitive** for common text columns (`status`, `city`).
        - Your queries are evaluated by an AI for correctness and logic.
        - Query simulation is powered by MySQL to show results on sample data.
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
        try:
            table_overview_data = {"Table": list(original_tables.keys()),
                                   "Rows": [len(df) for df in original_tables.values()],
                                   "Columns": [len(df.columns) for df in original_tables.values()]}
            st.dataframe(pd.DataFrame(table_overview_data), hide_index=True)
        except Exception as e:
            st.error(f"Error displaying table overview: {e}")

    st.write("### 🔍 Table Previews");
    try:
        tab1, tab2 = st.tabs(["Users Table", "Orders Table"])
        with tab1: st.dataframe(users_table, hide_index=True, use_container_width=True)
        with tab2: st.dataframe(orders_table, hide_index=True, use_container_width=True)
    except Exception as e:
         st.error(f"Error displaying table previews: {e}")

    with st.expander("📝 Quiz Ke Baare Mein"):
        st.write(f"""
        - Aapko {len(sql_questions)} SQL query challenges solve karne honge.
        - Har jawaab ke baad AI Mentor se immediate feedback milega.
        - **SQL Dialect Focus:** Standard SQL (MySQL/PostgreSQL like).
        - Case-insensitivity for `status` and `city` columns in `WHERE =` clauses is simulated.
        """)
    if st.button("🚀 Start SQL Challenge!"):
        st.session_state.quiz_started = True; st.session_state.user_answers = []; st.session_state.current_question = 0; st.session_state.quiz_completed = False; st.session_state.show_detailed_feedback = False; st.rerun()

# --- Quiz In Progress ---
elif st.session_state.quiz_started and not st.session_state.quiz_completed:
    st.title("✍️ SQL Query Challenge")

    # --- Display Previous Answers and Feedback ---
    if st.session_state.user_answers:
        st.markdown("---"); st.subheader("📖 Ab Tak Ke Jawaab Aur Feedback")
        # Display newest first
        for i, ans_data in enumerate(reversed(st.session_state.user_answers)):
            q_num = len(st.session_state.user_answers) - i;
            is_correct = ans_data.get('is_correct', False) # Default to False if key missing
            with st.expander(f"Question {q_num}: {ans_data['question']} {get_emoji(is_correct)}", expanded=False):
                st.write(f"**Aapka Jawaab:**"); st.code(ans_data.get('student_answer', '(No answer provided)'), language='sql');
                st.write(f"**SQL Mentor Feedback:**");
                feedback_text = ans_data.get('feedback', 'Feedback not available.')
                if is_correct: st.success(feedback_text)
                else: st.error(feedback_text);

                # --- Display Simulation Results Vertically ---
                st.markdown("---") # Separator before tables
                display_simulation("Simulated Result (Your Query Output)", ans_data.get("actual_result"))
                st.divider() # Optional: Add a visual divider between the two tables
                display_simulation("Simulated Result (Example Query Output)", ans_data.get("expected_result"))

    # --- Display Current Question ---
    st.markdown("---")
    current_question_data = sql_questions[st.session_state.current_question]
    st.subheader(f"❓ Sawaal {st.session_state.current_question + 1}:")
    st.write(current_question_data["question"])
    student_answer = st.text_area("Apna SQL Query Yahaan Likhein:", key=f"question_{st.session_state.current_question}", height=100)

    # --- Handle Submission ---
    if st.button("✅ Jawaab Submit Karein"):
        with st.spinner("Jawaab check kiya ja raha hai..."):
            (feedback, is_correct, expected_result_sim, actual_result_sim, llm_output) = evaluate_answer_with_llm(current_question_data, student_answer, original_tables)
            st.session_state.user_answers.append({
                "question": current_question_data["question"],
                "student_answer": student_answer,
                "feedback": feedback,
                "is_correct": is_correct,
                "expected_result": expected_result_sim,
                "actual_result": actual_result_sim,
                "llm_raw_output": llm_output
            })

            if st.session_state.current_question < len(sql_questions) - 1:
                st.session_state.current_question += 1
                st.rerun()  # Go to the next question
            else:
                st.session_state.quiz_completed = True
                st.rerun()

# --- Quiz Completed Screen ---
elif st.session_state.quiz_started and st.session_state.quiz_completed:
    st.title("🎉 Quiz Complete!")
    st.subheader("Yeh rahi aapki performance summary:")
    final_score = calculate_score(st.session_state.user_answers)
    st.write(f"Aapka Final Score: {final_score:.2f}%")

    performance_analysis = analyze_performance(st.session_state.user_answers)
    st.write(performance_analysis["overall_feedback"])

    if st.button("Detailed Performance Analysis"):
        st.session_state.show_detailed_feedback = True
        st.rerun()

    if st.session_state.show_detailed_feedback:
        st.subheader("Detailed Performance Breakdown")
        with st.expander("Strengths 💪", expanded=True):
            if performance_analysis["strengths"]:
                for strength in performance_analysis["strengths"]:
                    st.success(f"- {strength}")
            else:
                st.info("Koi khaas strengths nahi dikhi.")

        with st.expander("Areas for Improvement 💡", expanded=True):
            if performance_analysis["weaknesses"]:
                for weakness in performance_analysis["weaknesses"]:
                    st.warning(f"- {weakness}")
            else:
                st.info("Koi improvement areas nahi hain.")

        st.subheader("Complete Quiz Review")
        for i, ans_data in enumerate(st.session_state.user_answers):
            q_num = i + 1
            is_correct = ans_data.get('is_correct', False)
            with st.expander(f"Question {q_num}: {ans_data['question']} {get_emoji(is_correct)}", expanded=False):
                st.write(f"**Aapka Jawaab:**"); st.code(ans_data.get('student_answer', '(No answer provided)'), language='sql');
                st.write(f"**SQL Mentor Feedback:**");
                feedback_text = ans_data.get('feedback', 'Feedback not available.')
                if is_correct: st.success(feedback_text)
                else: st.error(feedback_text);
                st.markdown("---")
                display_simulation("Simulated Result (Your Query)", ans_data.get("actual_result"))
                st.divider()
                display_simulation("Simulated Result (Correct Answer)", ans_data.get("expected_result"))
                st.markdown("---")
                st.write("**LLM Raw Output (For Debugging):**"); st.code(ans_data.get('llm_raw_output', 'No raw output'), language='text')

    st.markdown("---")
    if st.button("🔄 Restart Quiz"):
        st.session_state.quiz_started = True; st.session_state.quiz_completed = False; st.session_state.current_question = 0; st.session_state.user_answers = []; st.session_state.show_detailed_feedback = False; st.rerun()

# --- Fallback ---
else:
    st.write("Unexpected state. Please restart the quiz.")
