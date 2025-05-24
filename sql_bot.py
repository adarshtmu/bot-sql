import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import duckdb

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
        /* Increase global font size */
        body, .stMarkdown, .stText, .stTextArea, .stButton button, .stLinkButton a {
            font-size: 18px !important;
        }
        h1 {font-size: 32px !important; text-align: center; margin-bottom: 20px;} /* Adjusted H1 */
        h2 {font-size: 26px !important;} /* Adjusted H2 */
        h3 {font-size: 22px !important;} /* Adjusted H3 */
        /* Style for Start SQL Challenge! button */
        button[kind="primary"] {
            font-size: 22px !important; /* Adjusted */
            padding: 12px 25px !important; /* Adjusted */
            color: white !important;
            background-color: #d32f2f; /* Slightly darker red */
            border-radius: 8px; /* Consistent border radius */
            border: none;
        }
        button[kind="primary"]:hover {
            background-color: #c62828; /* Darker on hover */
        }
        /* Style for other buttons (Submit, Analysis, Retry) */
        .stButton button:not([kind="primary"]), .stLinkButton a {
            font-size: 18px !important; /* Adjusted */
            padding: 10px 20px !important; /* Adjusted */
            border-radius: 8px;
        }
        /* Feedback container styling */
        .feedback-container {
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05); /* Softer shadow */
            font-size: 17px !important; /* Slightly adjusted */
            border: 1px solid #e0e0e0;
        }
        .feedback-header {
            font-size: 20px !important; /* Adjusted */
            color: #1f77b4;
            margin-bottom: 10px;
            font-weight: bold;
        }
        .feedback-section {
            margin-top: 15px;
        }
        .strength-item, .weakness-item {
            font-size: 17px !important; /* Adjusted */
            margin: 5px 0;
        }
        /* Custom style for the score box */
        .score-box {
            text-align: center;
            padding: 20px;
            border: 2px solid #4CAF50;
            border-radius: 10px;
            background-color: #e8f5e9;
            margin-bottom: 15px;
        }
        .score-box .score-title {
            font-size: 18px; /* Adjusted */
            margin-bottom: 8px;
            color: #2e7d32; /* Darker green */
            font-weight: bold;
            text-transform: uppercase;
        }
        .score-box .score-value {
            font-size: 48px; /* Adjusted */
            font-weight: bold;
            margin-bottom: 5px;
            color: #1b5e20; /* Darkest green */
            line-height: 1.1;
        }
        .stProgress > div > div > div > div { /* Style for progress bar */
            background-color: #4CAF50 !important;
        }
        .stTabs [data-baseweb="tab-list"] { /* Style for tabs */
            gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 44px; /* Adjusted tab height */
            white-space: pre-wrap;
            background-color: #f0f2f6;
            border-radius: 8px 8px 0 0;
            padding: 10px 16px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #d32f2f; /* Red for selected tab */
            color: white;
            font-weight: bold;
        }
        .stAlert { /* Style for alerts/messages */
            border-radius: 8px;
            font-size: 17px !important;
        }
    </style>
"""
st.set_page_config(page_title="SQL Mentor", layout="wide") # Use wide layout
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Set up Gemini API ---
gemini_api_key = "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k"  # ⚠️ REPLACE WITH YOUR ACTUAL GEMINI API KEY

if not gemini_api_key or gemini_api_key == "YOUR_GEMINI_API_KEY":
    st.error("🚨 Gemini API Key is missing. Please add your key in the code (line 59). The app cannot function without it.")
    st.stop()

try:
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"🚨 Failed to configure Gemini API or access the model: {e}")
    st.stop()

# --- Sample Data ---
users_table = pd.DataFrame({
    "user_id": [1, 2, 3, 4, 5],
    "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
    "email": ["alice@example.com", "bob@example.com", "charlie@example.com", "david@example.com", "eve@example.com"],
    "age": [25, 30, 35, 40, 28],
    "city": ["New York", "Los Angeles", "Chicago", "Houston", "Chicago"]
})
orders_table = pd.DataFrame({
    "order_id": [101, 102, 103, 104, 105, 106, 107],
    "user_id": [1, 2, 3, 1, 4, 2, 5],
    "amount": [50.00, 75.50, 120.00, 200.00, 35.00, 150.00, 90.00],
    "order_date": pd.to_datetime(["2024-02-01", "2024-02-05", "2024-02-10", "2024-02-15", "2024-02-20", "2024-03-01", "2024-03-05"]),
    "status": ["Completed", "Pending", "Completed", "Shipped", "Cancelled", "Completed", "Pending"]
})
original_tables = {
    "users": users_table.copy(),
    "orders": orders_table.copy()
}

# --- SQL Questions List ---
sql_questions = [
    {"question": "Write a SQL query to get all details about users from the 'users' table.", "correct_answer_example": "SELECT * FROM users;", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to count the total number of users in the 'users' table.", "correct_answer_example": "SELECT COUNT(*) AS user_count FROM users;", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to get all users older than 30 from the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE age > 30;", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to find all orders with a status of 'Pending' from the 'orders' table.", "correct_answer_example": "SELECT * FROM orders WHERE status = 'Pending';", "sample_table": orders_table, "relevant_tables": ["orders"]},
    {"question": "Write a SQL query to find users from 'Chicago' in the 'users' table (test case-insensitivity).", "correct_answer_example": "SELECT * FROM users WHERE city = 'Chicago';", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to find the average order amount from the 'orders' table.", "correct_answer_example": "SELECT AVG(amount) AS average_amount FROM orders;", "sample_table": orders_table, "relevant_tables": ["orders"]},
    {"question": "Write a SQL query to find users whose orders are still pending. Use the 'users' and 'orders' tables.","correct_answer_example": "SELECT u.name, u.email FROM users u JOIN orders o ON u.user_id = o.user_id WHERE o.status = 'Pending';","sample_table": users_table,"relevant_tables": ["users", "orders"]},
    {"question": "Write a SQL query to calculate the total amount spent by each user. List user name and total amount, ordered by total amount descending. Use the 'users' and 'orders' tables.", "correct_answer_example": "SELECT u.name, SUM(o.amount) AS total_spent FROM users u JOIN orders o ON u.user_id = o.user_id GROUP BY u.name ORDER BY total_spent DESC;", "sample_table": users_table, "relevant_tables": ["users", "orders"]}
]

# --- Session State Initialization ---
if "user_answers" not in st.session_state: st.session_state.user_answers = []
if "current_question" not in st.session_state: st.session_state.current_question = 0
if "quiz_started" not in st.session_state: st.session_state.quiz_started = False
if "quiz_completed" not in st.session_state: st.session_state.quiz_completed = False
if "detailed_analysis_content" not in st.session_state: st.session_state.detailed_analysis_content = None
if "force_regenerate_analysis" not in st.session_state: st.session_state.force_regenerate_analysis = True


# --- Helper Functions ---
def simulate_query_duckdb(sql_query, tables_dict):
    if not sql_query or not sql_query.strip():
        return "Simulation Error: No query provided."
    if not tables_dict:
        return "Simulation Error: No tables provided for context."

    con = None
    processed_query_for_ilike = sql_query

    try:
        double_quote_pattern = r'"([^"]*)"'
        processed_query_for_ilike = re.sub(double_quote_pattern, r"'\1'", sql_query)
    except Exception:
        processed_query_for_ilike = sql_query

    modified_sql_query = processed_query_for_ilike
    final_executed_query = modified_sql_query
    case_insensitive_columns = {"orders": ["status"], "users": ["city"]}
    flat_insensitive_columns = [col for cols in case_insensitive_columns.values() for col in cols]

    if flat_insensitive_columns:
        try:
            col_pattern_part = "|".join([r"\b" + re.escape(col) + r"\b" for col in flat_insensitive_columns])
            pattern = rf"(.*?)({col_pattern_part})(\s*=\s*)('[^']+')"
            def replace_with_ilike(match):
                pre_context, col_name, _, literal = match.groups()
                space_prefix = "" if not pre_context or pre_context.endswith((" ", "(", ",")) else " "
                return f"{pre_context}{space_prefix}{col_name} ILIKE {literal}"
            modified_sql_query = re.sub(pattern, replace_with_ilike, processed_query_for_ilike, flags=re.IGNORECASE)
            final_executed_query = modified_sql_query
        except Exception:
            final_executed_query = processed_query_for_ilike
    try:
        con = duckdb.connect(database=':memory:', read_only=False)
        for table_name, df in tables_dict.items():
            if isinstance(df, pd.DataFrame):
                con.register(str(table_name), df)
        result_df = con.execute(final_executed_query).df()
        return result_df
    except Exception as e:
        error_message = f"Simulation Error: {str(e)}"
        e_str = str(e).lower()
        hint = ""
        if "ILIKE" in str(e).upper() or (modified_sql_query != processed_query_for_ilike and "syntax error" in e_str):
            hint = "\n\n**Hint:** The simulation tried using case-insensitive matching (ILIKE). Check your SQL syntax."
        else:
            catalog_match = re.search(r'table with name "([^"]+)" does not exist', e_str)
            binder_match = re.search(r'column "([^"]+)" not found', e_str)
            syntax_match = re.search(r'syntax error at or near "([^"]+)"', e_str) or \
                           re.search(r'syntax error at end of input', e_str) or \
                           re.search(r'syntax error at:', e_str)
            type_match = re.search(r'conversion error:.*try cast\("([^"]+)"', e_str)

            if catalog_match: hint = f"\n\n**Hint:** Table '{catalog_match.group(1)}' might be misspelled. Available: {list(tables_dict.keys())}."
            elif binder_match: hint = f"\n\n**Hint:** Column '{binder_match.group(1)}' might be misspelled."
            elif syntax_match:
                problem_area = syntax_match.group(1) if syntax_match.groups() and syntax_match.lastindex == 1 else "indicated location"
                hint = f"\n\n**Hint:** Check SQL syntax near `{problem_area}`. Use single quotes for text (e.g., `'example'`)."
            elif type_match: hint = f"\n\n**Hint:** Type mismatch with '{type_match.group(1)}'."
            elif "syntax error" in e_str: hint = "\n\n**Hint:** Double-check SQL syntax. Use single quotes for strings."
        if not hint: hint = "\n\n**Hint:** Check query syntax, table/column names, and data types. Use single quotes for strings."
        error_message += hint
        return error_message
    finally:
        if con:
            try: con.close()
            except: pass

def get_table_schema(table_name, tables_dict):
    if table_name in tables_dict and isinstance(tables_dict[table_name], pd.DataFrame):
        return tables_dict[table_name].columns.astype(str).tolist()
    return []

def evaluate_answer_with_llm(question_data, student_answer, original_tables_dict):
    if not student_answer or not student_answer.strip():
        return "Please provide an answer.", False, "N/A", "N/A", "No input."

    question = question_data["question"]
    relevant_table_names = question_data["relevant_tables"]
    correct_answer_example = question_data["correct_answer_example"]

    schema_info = ""
    if not relevant_table_names:
        schema_info = "No specific table schema context provided.\n"
    else:
        for name in relevant_table_names:
            columns = get_table_schema(name, original_tables_dict)
            if columns:
                try:
                    df = original_tables_dict[name]
                    dtypes_str = df.dtypes.to_string() if isinstance(df, pd.DataFrame) else "N/A"
                    schema_info += f"Table '{name}':\n  Columns: {columns}\n  DataTypes:\n{dtypes_str}\n\n"
                except Exception as e_schema:
                    schema_info += f"Table '{name}': Columns {columns} (Error getting schema details: {e_schema})\n\n"
            else:
                schema_info += f"Table '{name}': Schema information not found.\n"

    prompt = f"""
    You are an expert SQL evaluator acting as a friendly SQL mentor. Analyze the student's SQL query.
    Assume standard SQL syntax (MySQL/PostgreSQL).

    **Evaluation Task:**
    1.  **Question:** {question}
    2.  **Relevant Table Schemas:**
        {schema_info.strip()}
    3.  **Student's SQL Query:**
        ```sql
        {student_answer}
        ```

    **Analysis Instructions:**
    * **Correctness:** Does the query accurately answer the **Question** based on the **Schemas**?
      * **QUIZ CONTEXT:** For *this quiz*, equality comparisons (`=`) on text columns `'status'` (in `orders`) and `'city'` (in `users`) are **CASE-INSENSITIVE**.  A query like `WHERE status = 'pending'` is CORRECT if the question implies 'Pending'. Evaluate logic based on this.
      * **QUIZ CONTEXT:** Both single (') and double (") quotes for string literals are acceptable.
    * **Validity:** Is the query syntactically valid (ignoring quote style if logic is okay)?
    * **Logic:** Are SQL clauses (SELECT, FROM, WHERE, JOIN, GROUP BY, etc.) used correctly?
    * **Feedback:** Provide clear, constructive feedback in a friendly, encouraging, casual Hindi tone.
        * If incorrect (for reasons *other* than case on `status`/`city` or double quotes): Gently point out errors. Explain what's wrong. Suggest fixes. **Do NOT mark incorrect or suggest `LOWER()`/`UPPER()` or single quotes *solely* for these quiz-specific allowances if logic is fine.**
    * **Verdict:** Conclude with *exactly* one line: "Verdict: Correct" or "Verdict: Incorrect". This MUST be the last line.

    **Begin Evaluation:**
    """

    feedback_llm = "AI feedback generation failed."; is_correct_llm = False; llm_output = "Error: No LLM response."
    try:
        response = model.generate_content(prompt)
        extracted_text = None
        if hasattr(response, 'text'): extracted_text = response.text
        elif hasattr(response, 'parts') and response.parts:
            extracted_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
        else: extracted_text = f"AI Response Blocked/Empty. Prompt Feedback: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'N/A'}"

        if not extracted_text or not extracted_text.strip():
            llm_output = "Error: Received empty response from AI."
        else:
            llm_output = extracted_text.strip()
            verdict_match = re.search(r'^Verdict:\s*(Correct|Incorrect)\s*$', llm_output, re.MULTILINE | re.IGNORECASE)
            if verdict_match:
                is_correct_llm = (verdict_match.group(1).lower() == "correct")
                feedback_llm = llm_output[:verdict_match.start()].strip()
                feedback_llm = re.sub(r'\s*Verdict:\s*(Correct|Incorrect)?\s*$', '', feedback_llm, flags=re.MULTILINE | re.IGNORECASE).strip()
            else:
                feedback_llm = llm_output + "\n\n_(System Note: AI verdict parsing failed.)_"
                is_correct_llm = False # Default to incorrect if verdict not found
    except Exception as e_resp:
        llm_output = f"Error processing AI response: {e_resp}"
        feedback_llm = f"AI response processing error: {e_resp}"
        is_correct_llm = False

    actual_result_sim = simulate_query_duckdb(student_answer, original_tables_dict)
    expected_result_sim = simulate_query_duckdb(correct_answer_example, original_tables_dict)

    return feedback_llm, is_correct_llm, expected_result_sim, actual_result_sim, llm_output

def calculate_score(user_answers):
    if not user_answers: return 0.0
    correct_count = sum(1 for ans in user_answers if ans.get("is_correct", False))
    return (correct_count / len(user_answers)) * 100 if user_answers else 0.0

def analyze_performance(user_answers):
    performance_data = {
        "overall_feedback": "Performance analysis could not be completed."
    }
    if not user_answers:
        performance_data["overall_feedback"] = "Koi jawaab nahi diya gaya. Analysis possible nahi hai."
        return performance_data

    correct_q_texts = [ans["question"] for ans in user_answers if ans.get("is_correct")]
    incorrect_ans_details = [
        {"question": ans["question"], "your_answer": ans["student_answer"],
         "feedback_received": ans.get("feedback", "N/A")}
        for ans in user_answers if not ans.get("is_correct")
    ]
    total_q, correct_c = len(user_answers), len(correct_q_texts)
    score = calculate_score(user_answers)

    incorrect_summary = "Koi galat jawaab nahi! Bahut badhiya!"
    if incorrect_ans_details:
        incorrect_summary = "In sawaalon mein thodi galti hui:\n"
        for idx, item in enumerate(incorrect_ans_details):
            feedback_snippet = item['feedback_received'][:150].strip() + ('...' if len(item['feedback_received']) > 150 else '')
            incorrect_summary += f"  {idx+1}. Sawaal: {item['question']}\n     Aapka Jawaab: `{item['your_answer']}`\n     Feedback Mila: {feedback_snippet}\n"

    correct_summary = "Is baar koi jawaab sahi nahi hua."
    if correct_q_texts:
        correct_summary = "Yeh sawaal bilkul sahi kiye:\n" + "\n".join([f"  - {q_text}" for q_text in correct_q_texts])

    prompt = f"""
    Ek SQL learner ne quiz complete kiya hai. Unki performance ka analysis karke friendly, motivating summary feedback casual Hindi mein do.

    **Quiz Performance:**
    - Total Questions: {total_q}, Correct: {correct_c}, Score: {score:.2f}%
    - Correctly Answered:
    {correct_summary}
    - Incorrectly Answered & Feedback Snippets:
    {incorrect_summary}

    **Quiz Context:** Case-insensitivity for `status`/`city` and flexible quotes were allowed.

    **Task:** Generate overall performance feedback:
    1.  **Overall Impression:** Score/performance pe comment (e.g., "Overall performance kaafi achhi rahi!").
    2.  **Strengths:** Agar kuch concepts sahi kiye hain, unko highlight karo.
    3.  **Areas for Improvement:** Jo concepts galat hue, unko gently point out. Focus on concepts.
    4.  **Next Steps / Encouragement:** Aage kya karna chahiye (e.g., "Keep practicing!").

    Bas plain text mein feedback generate karna hai. Sidhe feedback se shuru karo.
    """
    try:
        response = model.generate_content(prompt)
        generated_feedback = None
        if hasattr(response, 'text'): generated_feedback = response.text.strip()
        elif hasattr(response, 'parts') and response.parts:
            generated_feedback = "".join(part.text for part in response.parts if hasattr(part, 'text')).strip()
        else: generated_feedback = f"AI Response Blocked/Empty for summary. Prompt Feedback: {response.prompt_feedback if hasattr(response, 'prompt_feedback') else 'N/A'}"

        if generated_feedback:
            performance_data["overall_feedback"] = generated_feedback
        else:
            performance_data["overall_feedback"] = "AI response format unclear or empty for summary analysis."
    except Exception as e:
        performance_data["overall_feedback"] = f"Summary generation error from AI: {e}"
    return performance_data

def get_emoji(is_correct):
    return "✅" if is_correct else "❌"

def display_simulation(title, result_data):
    st.markdown(f"**{title}:**")
    if isinstance(result_data, pd.DataFrame):
        if result_data.empty: st.info("_(Simulation resulted in an empty table)_")
        else: st.dataframe(result_data.reset_index(drop=True), hide_index=True, use_container_width=True)
    elif isinstance(result_data, str) and "Simulation Error" in result_data:
        st.warning(result_data, icon="⚠️")
    elif result_data == "N/A": st.info("_(Simulation not applicable or not run)_")
    elif isinstance(result_data, str): st.info(f"_{result_data}_")
    else: st.error(f"_(Unexpected simulation result type: {type(result_data)})_")


# --- Streamlit App UI ---

# --- Start Screen ---
if not st.session_state.quiz_started:
    st.markdown("<h1>🚀 SQL Mentor - Interactive SQL Practice</h1>", unsafe_allow_html=True)
    st.markdown("### Apne SQL Skills Ko Test Aur Improve Karein!")
    st.markdown("""
        **📌 Important Notes:**
        - This quiz uses standard **SQL syntax** (similar to MySQL/PostgreSQL).
        - String comparisons (e.g., `WHERE city = 'new york'`) for `'status'` (in `orders`) and `'city'` (in `users`) columns are simulated to be **case-insensitive**.
        - **Both single quotes (') and double quotes (") are accepted** for string literals.
        - Queries are evaluated by an AI for correctness and logic. DuckDB simulates query execution.
        """)

    col1_intro, col2_overview = st.columns([2, 1])
    with col1_intro:
        st.write("""
        Is interactive quiz mein, aap do sample tables ke saath kaam karenge:
        - **`users` Table**: User details (ID, naam, email, umar, sheher).
        - **`orders` Table**: Order details (ID, user ID, amount, date, status).
        """)
    with col2_overview:
        st.markdown("#### Tables Overview")
        try:
            table_overview_data = {"Table": list(original_tables.keys()),
                                   "Rows": [len(df) for df in original_tables.values()],
                                   "Columns": [len(df.columns) for df in original_tables.values()]}
            st.dataframe(pd.DataFrame(table_overview_data).set_index("Table"), use_container_width=True)
        except Exception as e: st.error(f"Error displaying table overview: {e}")

    st.markdown("### 🔍 Table Previews & Schemas")
    tab_users, tab_orders = st.tabs([f"📄 Users ({len(users_table)} rows)", f"📄 Orders ({len(orders_table)} rows)"])
    with tab_users:
        st.dataframe(users_table, hide_index=True, use_container_width=True)
        st.caption(f"Columns: {', '.join(users_table.columns.tolist())}")
    with tab_orders:
        st.dataframe(orders_table, hide_index=True, use_container_width=True)
        st.caption(f"Columns: {', '.join(orders_table.columns.tolist())}")

    with st.expander("📝 Quiz Ke Baare Mein Aur Tips"):
        st.write(f"""
        - Aapko **{len(sql_questions)} SQL query challenges** solve karne honge.
        - Har jawaab ke baad AI Mentor se **immediate feedback** milega.
        - **Focus:** Standard SQL. Case-insensitivity and flexible quotes are for this quiz only.
        - **Tip:** Carefully check column names and table names before submitting!
        """)

    if st.button("🚀 Start SQL Challenge!", type="primary", use_container_width=True):
        st.session_state.quiz_started = True
        st.session_state.user_answers = []
        st.session_state.current_question = 0
        st.session_state.quiz_completed = False
        if 'detailed_analysis_content' in st.session_state: del st.session_state.detailed_analysis_content
        st.session_state.force_regenerate_analysis = True
        st.rerun()

# --- Quiz In Progress Screen ---
elif st.session_state.quiz_started and not st.session_state.quiz_completed:
    current_q_index = st.session_state.current_question
    current_q_data = sql_questions[current_q_index]

    st.markdown(f"<h1>✍️ SQL Challenge: Question {current_q_index + 1} / {len(sql_questions)}</h1>", unsafe_allow_html=True)
    st.markdown(f"### {current_q_data['question']}")

    st.markdown("---")
    st.markdown("#### Relevant Table Information:")
    for table_name in current_q_data["relevant_tables"]:
        if table_name in original_tables:
            with st.expander(f"Schema & Sample: '{table_name}' table", expanded=(len(current_q_data["relevant_tables"])==1)):
                st.dataframe(original_tables[table_name].head(3), hide_index=True, use_container_width=True)
                st.caption(f"Columns: {', '.join(original_tables[table_name].columns.tolist())}")
    st.markdown("---")

    user_query_key = f"query_input_{current_q_index}"
    user_query = st.text_area("Aapka SQL Query Yahaan Likhein:", height=150, key=user_query_key,
                              placeholder="Jaise ki: SELECT * FROM users WHERE age > 25;")

    submit_button_key = f"submit_{current_q_index}"
    if st.button("✅ Submit Query", key=submit_button_key, type="primary", use_container_width=True):
        if user_query and user_query.strip():
            with st.spinner("🧠 AI Mentor aapki query evaluate kar raha hai..."):
                feedback, is_correct, expected_res, actual_res, llm_log = evaluate_answer_with_llm(
                    current_q_data, user_query, original_tables
                )
            st.session_state.user_answers.append({
                "question_number": current_q_index + 1,
                "question": current_q_data["question"],
                "student_answer": user_query,
                "feedback": feedback,
                "is_correct": is_correct,
                "expected_result": expected_res,
                "actual_result": actual_res,
                "llm_log": llm_log # For debugging if needed
            })
            # Force rerun to display feedback and next/finish button correctly
            st.rerun()
        else:
            st.warning("💡 Query likhna bhool gaye? Kripya apna SQL query enter karein.")

    # Display feedback for the *last submitted* answer if available
    if st.session_state.user_answers and st.session_state.user_answers[-1]["question_number"] == current_q_index + 1:
        last_answer = st.session_state.user_answers[-1]
        st.markdown("---")
        st.subheader(f"📝 Feedback for Question {last_answer['question_number']} {get_emoji(last_answer['is_correct'])}")
        st.markdown("<div class='feedback-container'>", unsafe_allow_html=True)
        st.markdown(last_answer["feedback"])
        st.markdown("</div>", unsafe_allow_html=True)

        display_simulation("Simulated Result (Aapki Query ka Output)", last_answer.get("actual_result", "N/A"))
        if not last_answer['is_correct'] or \
           (isinstance(last_answer.get("actual_result"), pd.DataFrame) and \
            isinstance(last_answer.get("expected_result"), pd.DataFrame) and \
            not last_answer["actual_result"].equals(last_answer["expected_result"])):
            display_simulation("Simulated Result (Expected Output for reference)", last_answer.get("expected_result", "N/A"))
        st.markdown("---")

        if current_q_index < len(sql_questions) - 1:
            if st.button("➡️ Agla Sawaal", use_container_width=True):
                st.session_state.current_question += 1
                st.rerun()
        else:
            if st.button("🏁 Finish Quiz & View Results", use_container_width=True, type="primary"):
                st.session_state.quiz_completed = True
                st.session_state.force_regenerate_analysis = True
                st.rerun()

# --- Quiz Completion / Results Screen ---
elif st.session_state.quiz_completed:
    st.balloons()
    st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>🎉 Badhai Ho! Challenge Poora Hua!</h1>", unsafe_allow_html=True)
    st.markdown("---")

    score = calculate_score(st.session_state.user_answers)

    st.subheader("📊 Aapka Final Score")
    score_col, message_col = st.columns([1, 2])

    with score_col:
        st.markdown(
            f"<div class='score-box'>"
            f"<p class='score-title'>SCORE</p>"
            f"<p class='score-value'>{score:.0f}%</p>" # Display score without decimal for cleaner look
            f"</div>", unsafe_allow_html=True
        )
    st.progress(int(score) / 100)

    with message_col:
        if score >= 80:
            st.success(f"🏆 **Shabaash! Aapne {score:.0f}% ya usse zyada score kiya!**")
            st.markdown("Aap apna SQL certificate generate kar sakte hain (feature jald hi aa raha hai!).")
            # if st.button("📄 Generate Your Certificate", type="primary", key="generate_cert_final", use_container_width=True):
            #     st.success("📜 Certificate generated! (Yeh abhi ek placeholder hai.)")
        elif score >= 50:
            st.info(f"👍 **Achhi Koshish!** Aapka score {score:.0f}% hai. Certificate ke liye 80% chahiye. Thodi aur mehnat se aap zaroor achieve kar lenge!")
        else:
            st.warning(f"😟 **Koi Baat Nahi!** Aapka score {score:.0f}% hai. Himmat mat haro, practice karte raho aur concepts ko revise karo!")
    st.markdown("---")

    st.subheader("💡 AI Mentor Se Detailed Performance Analysis")
    with st.expander("🔍 Dekhein Detailed Analysis", expanded=True): # Expanded by default on results page
        if st.session_state.get('force_regenerate_analysis', True) or \
           st.session_state.detailed_analysis_content is None:
            with st.spinner("🤖 AI Mentor aapka performance analyze kar raha hai... Intezaar kijiye..."):
                analysis_result = analyze_performance(st.session_state.user_answers)
                st.session_state.detailed_analysis_content = analysis_result
                st.session_state.force_regenerate_analysis = False

        if st.session_state.detailed_analysis_content:
            analysis_data = st.session_state.detailed_analysis_content
            st.markdown("<div class='feedback-container'>", unsafe_allow_html=True)
            st.markdown(f"<p class='feedback-header'>AI Mentor Ki Raay:</p>", unsafe_allow_html=True)
            if analysis_data and "overall_feedback" in analysis_data:
                st.markdown(analysis_data["overall_feedback"])
            else:
                st.warning("Analysis abhi available nahi hai ya generate nahi ho paya.")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Analysis generate nahi hua. Refresh karke dekhein.")

    st.markdown("---")
    if st.button("🔁 Dobara Try Karein?", key="retry_final", use_container_width=True):
        st.session_state.user_answers = []
        st.session_state.current_question = 0
        st.session_state.quiz_started = True
        st.session_state.quiz_completed = False
        if 'detailed_analysis_content' in st.session_state: del st.session_state.detailed_analysis_content
        st.session_state.force_regenerate_analysis = True
        st.rerun()
