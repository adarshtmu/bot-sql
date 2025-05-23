import streamlit as st
import google.generativeai as genai
import pandas as pd
import re # Needed for regex query modification
import duckdb # Import DuckDB
# import copy # No longer needed

# --- Custom CSS ---
# Hides Streamlit's default header, footer, menu, deploy button, etc.
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
        /* Increase font size for Start SQL Challenge! button */
        button[kind="primary"] {
            font-size: 50px !important; /* Larger text */
            padding: 20px 20px !important; /* Increase button height/width */
            color: white !important; /* Text color */
            background-color: red; /* Background color (optional) */
            border-radius: 10px; /* Rounded corners (optional) */
        }

    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Set up Gemini API ---
# WARNING: Hardcoding API keys is insecure.
# For production, use Streamlit Secrets or environment variables.
# Replace "YOUR_API_KEY_HERE" with your actual Gemini API Key below.
gemini_api_key = "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k" # <--- IMPORTANT: PASTE YOUR GEMINI API KEY HERE

if not gemini_api_key or gemini_api_key == "YOUR_API_KEY_HERE": # Basic check
    st.error("🚨 Gemini API Key is missing or hasn't been replaced. Please add your key in the code.")
    st.stop()

try:
    genai.configure(api_key=gemini_api_key)
    # Using the 'gemini-1.5-flash' model for potentially faster responses
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"🚨 Failed to configure Gemini API or access the model: {e}")
    st.stop()


# --- Sample Data ---
# These pandas DataFrames simulate our database tables.
users_table = pd.DataFrame({
    "user_id": [1, 2, 3, 4],
    "name": ["Alice", "Bob", "Charlie", "David"],
    "email": ["alice@example.com", "bob@example.com", "charlie@example.com", "david@example.com"],
    "age": [25, 30, 35, 40],
    "city": ["New York", "Los Angeles", "Chicago", "Houston"] # Note mixed case cities
})
orders_table = pd.DataFrame({
    "order_id": [101, 102, 103, 104, 105],
    "user_id": [1, 2, 3, 1, 4],
    "amount": [50.00, 75.50, 120.00, 200.00, 35.00],
    "order_date": pd.to_datetime(["2024-02-01", "2024-02-05", "2024-02-10", "2024-02-15", "2024-02-20"]),
    "status": ["Completed", "Pending", "Completed", "Shipped", "Cancelled"] # Note mixed case statuses
})
# Dictionary holding the original tables for easy access
original_tables = {
    "users": users_table,
    "orders": orders_table
}

# --- SQL Questions List ---
# Each dictionary contains the question, a correct SQL example, the sample table for display,
# and the names of tables relevant for schema display and simulation context.
sql_questions = [
    { "question": "Write a SQL query to get all details about users from the 'users' table.", "correct_answer_example": "SELECT * FROM users;", "sample_table": users_table, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to count the total number of users in the 'users' table.", "correct_answer_example": "SELECT COUNT(*) AS user_count FROM users;", "sample_table": users_table, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to get all users older than 30 from the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE age > 30;", "sample_table": users_table, "relevant_tables": ["users"] },
    # Testing case-insensitivity for 'status'
    { "question": "Write a SQL query to find all orders with a status of 'Pending' from the 'orders' table.", "correct_answer_example": "SELECT * FROM orders WHERE status = 'Pending';", "sample_table": orders_table, "relevant_tables": ["orders"] },
    # Testing case-insensitivity for 'city'
    { "question": "Write a SQL query to find users from 'chicago' in the 'users' table (test case-insensitivity).", "correct_answer_example": "SELECT * FROM users WHERE city = 'Chicago';", "sample_table": users_table, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to find the most recent order from the 'orders' table by order date.", "correct_answer_example": "SELECT * FROM orders ORDER BY order_date DESC LIMIT 1;", "sample_table": orders_table, "relevant_tables": ["orders"] },
    { "question": "Write a SQL query to find the average order amount from the 'orders' table.", "correct_answer_example": "SELECT AVG(amount) AS average_amount FROM orders;", "sample_table": orders_table, "relevant_tables": ["orders"] },
    { "question": "Write a SQL query to find users from 'New York' or 'Chicago' in the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE city IN ('New York', 'Chicago');", "sample_table": users_table, "relevant_tables": ["users"] },
    # JOIN questions
    { "question": "Write a SQL query to find users who have not placed any orders. Use the 'users' and 'orders' tables.", "correct_answer_example": "SELECT u.* FROM users u LEFT JOIN orders o ON u.user_id = o.user_id WHERE o.order_id IS NULL;", "sample_table": users_table, "relevant_tables": ["users", "orders"] },
    { "question": "Write a SQL query to calculate the total amount spent by each user by joining the 'users' and 'orders' tables.", "correct_answer_example": "SELECT u.name, SUM(o.amount) AS total_spent FROM users u JOIN orders o ON u.user_id = o.user_id GROUP BY u.name ORDER BY u.name;", "sample_table": users_table, "relevant_tables": ["users", "orders"] },
]

# --- Session State Initialization ---
# Using Streamlit's session state to keep track of the quiz progress and user answers
# across reruns.
if "user_answers" not in st.session_state: st.session_state.user_answers = []
if "current_question" not in st.session_state: st.session_state.current_question = 0
if "quiz_started" not in st.session_state: st.session_state.quiz_started = False
if "quiz_completed" not in st.session_state: st.session_state.quiz_completed = False
if "show_detailed_feedback" not in st.session_state: st.session_state.show_detailed_feedback = False
if "show_detailed_feedback_on_completion" not in st.session_state: st.session_state.show_detailed_feedback_on_completion = False


# --- Helper Functions ---

# ******************************************************************************
# ***** simulate_query_duckdb function (handles quotes, ILIKE, execution) ****
# ******************************************************************************
def simulate_query_duckdb(sql_query, tables_dict):
    """
    Simulates an SQL query using DuckDB on in-memory pandas DataFrames.
    1. Pre-processes the query to replace double-quoted string literals with single-quoted ones.
    2. Attempts case-insensitive comparison for specific columns by rewriting '=' to 'ILIKE'.
    """
    if not sql_query or not sql_query.strip():
        return "Simulation Error: No query provided."
    if not tables_dict:
        return "Simulation Error: No tables provided for context."

    con = None
    processed_query_for_ilike = sql_query # Start with original

    # --- Step 1: Pre-process to replace double-quoted strings with standard single-quoted strings ---
    try:
        double_quote_pattern = r'"([^"]*)"'
        processed_query_for_ilike = re.sub(double_quote_pattern, r"'\1'", sql_query)
        # if processed_query_for_ilike != sql_query:
        #       print(f"DEBUG: Original query: {sql_query}")
        #       print(f"DEBUG: Query after double->single quote conversion: {processed_query_for_ilike}")
    except Exception as e_quotes:
        print(f"Warning: Failed during double quote replacement: {e_quotes}. Proceeding with original query structure for ILIKE.")
        processed_query_for_ilike = sql_query

    # --- Step 2: Query Modification Attempt (using ILIKE on the potentially quote-corrected query) ---
    modified_sql_query = processed_query_for_ilike
    final_executed_query = modified_sql_query

    case_insensitive_columns = { "orders": ["status"], "users": ["city"] }
    flat_insensitive_columns = [col for cols in case_insensitive_columns.values() for col in cols]

    if flat_insensitive_columns:
        try:
            col_pattern_part = "|".join([r"\b" + re.escape(col) + r"\b" for col in flat_insensitive_columns])
            # Ensure it only matches column = 'string_literal'
            pattern = rf"((?:WHERE|AND|OR)\s+(?:[\w.]+\s*=\s*|{col_pattern_part}\s*=\s*))'([^']+)'"
            pattern_with_alias = rf"((?:WHERE|AND|OR)\s+\w+\.({col_pattern_part})\s*=\s*)'([^']+)'"


            def replace_with_ilike_base(match):
                # print(f"DEBUG ILIKE Rewrite: Matched {match.groups()} for base pattern")
                return f"{match.group(1)} ILIKE '{match.group(2)}'"

            # Apply ILIKE for specific columns: table.column = 'value' or column = 'value'
            # Simplified regex for broader applicability while targeting specific columns for ILIKE
            for table_key, cols_to_make_insensitive in case_insensitive_columns.items():
                for col_name in cols_to_make_insensitive:
                    # Pattern for direct column name: col_name = 'value'
                    direct_col_pattern = rf"(\b{re.escape(col_name)}\b\s*=\s*)'([^']+)'"
                    # Pattern for aliased column name: alias.col_name = 'value'
                    aliased_col_pattern = rf"(\b\w+\.{re.escape(col_name)}\b\s*=\s*)'([^']+)'"

                    modified_sql_query = re.sub(direct_col_pattern, lambda m: f"{m.group(1).replace('=', 'ILIKE ')}'{m.group(2)}'", modified_sql_query, flags=re.IGNORECASE)
                    modified_sql_query = re.sub(aliased_col_pattern, lambda m: f"{m.group(1).replace('=', 'ILIKE ')}'{m.group(2)}'", modified_sql_query, flags=re.IGNORECASE)

            final_executed_query = modified_sql_query
            # if modified_sql_query != processed_query_for_ilike:
            # print(f"DEBUG: Query after ILIKE rewrite: {modified_sql_query}")

        except Exception as e_rewrite:
            print(f"Warning: Failed to rewrite query for case-insensitivity (ILIKE), using quote-converted query. Error: {e_rewrite}")
            final_executed_query = processed_query_for_ilike # Fallback to quote-corrected

    # --- Step 3: Connect and Execute with DuckDB ---
    try:
        con = duckdb.connect(database=':memory:', read_only=False)
        for table_name, df in tables_dict.items():
            if isinstance(df, pd.DataFrame):
                con.register(str(table_name), df)
            else:
                print(f"Warning [simulate_query]: Item '{table_name}' not a DataFrame during registration.")

        # print(f"DEBUG: Executing final query in DuckDB: {final_executed_query}")
        result_df = con.execute(final_executed_query).df()
        con.close()
        return result_df

    except Exception as e:
        error_message = f"Simulation Error: Failed to execute query. Reason: {str(e)}"
        e_str = str(e).lower()
        hint = ""

        if "ILIKE" in str(e).upper() or (modified_sql_query != processed_query_for_ilike and "syntax error" in e_str):
            hint = "\n\n**Hint:** The simulation tried using case-insensitive matching (ILIKE). Check your SQL syntax near the comparison, especially if using complex conditions."
        else:
            catalog_match = re.search(r'catalog error:.*table with name "([^"]+)" does not exist', e_str)
            binder_match = re.search(r'(?:binder error|catalog error):.*column "([^"]+)" not found', e_str)
            syntax_match = re.search(r'parser error: syntax error at or near "([^"]+)"', e_str) \
                            or re.search(r'parser error: syntax error at end of input', e_str) \
                            or re.search(r'parser error: syntax error at:', e_str)
            type_match = re.search(r'conversion error:.*try cast\("([^"]+)"', e_str)

            if catalog_match: hint = f"\n\n**Hint:** Table '{catalog_match.group(1)}' might be misspelled or doesn't exist. Available tables: {list(tables_dict.keys())}."
            elif binder_match: hint = f"\n\n**Hint:** Column '{binder_match.group(1)}' might be misspelled or doesn't exist in the referenced table(s)."
            elif syntax_match:
                problem_area = syntax_match.group(1) if syntax_match.groups() and syntax_match.lastindex == 1 else "the location indicated"
                hint = f"\n\n**Hint:** Check your SQL syntax, especially around `{problem_area}`. Remember standard SQL uses single quotes (') for text values like `'example text'` (though the tool tries to handle double quotes for you)."
            elif type_match: hint = f"\n\n**Hint:** There might be a type mismatch. You tried using '{type_match.group(1)}' in a way that's incompatible with its data type (e.g., comparing text to a number)."
            elif "syntax error" in e_str:
                    hint = "\n\n**Hint:** Double-check your SQL syntax. Ensure all clauses (SELECT, FROM, WHERE, etc.) are correct and in order. Use single quotes (') for string values."

        if not hint:
                hint = "\n\n**Hint:** Double-check your query syntax, table/column names, and data types. Ensure string values are correctly quoted (standard SQL uses single quotes '). Verify function names and usage."

        error_message += hint
        print(f"ERROR [simulate_query_duckdb]: {error_message}\nOriginal Query: {sql_query}\nFinal Attempted Query: {final_executed_query}")
        if con:
            try: con.close()
            except: pass
        return error_message
# ******************************************************************************
# ***** End of simulate_query_duckdb function **********************************
# ******************************************************************************


def get_table_schema(table_name, tables_dict):
    """Gets column names as a list for a given table name from the tables dictionary."""
    if table_name in tables_dict and isinstance(tables_dict[table_name], pd.DataFrame):
        return tables_dict[table_name].columns.astype(str).tolist()
    return []


def evaluate_answer_with_llm(question_data, student_answer, original_tables_dict):
    """
    Evaluates the user's SQL query using the Gemini API for feedback and correctness,
    and also simulates the query using DuckDB.
    """
    if not student_answer or not student_answer.strip():
        return "Please provide an answer.", False, "N/A", "N/A", "No input."

    question = question_data["question"]
    relevant_table_names = question_data["relevant_tables"]
    correct_answer_example = question_data["correct_answer_example"]

    schema_info = ""
    if not relevant_table_names:
        schema_info = "No specific table schema context provided for this question.\n"
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
        **>>> IMPORTANT QUIZ CONTEXT FOR CORRECTNESS <<<**
        For *this specific quiz*, assume that simple equality comparisons (`=`) involving the text columns `'status'` (in `orders`) and `'city'` (in `users`) are effectively **CASE-INSENSITIVE**. The quiz environment simulates this behavior by attempting to use ILIKE.
        Therefore, a query like `WHERE status = 'pending'` **should be considered CORRECT** if the question asks for 'Pending' status, even if the student did not use explicit `LOWER()` or `UPPER()` functions or ILIKE themselves.
        Evaluate the *logic* of the query based on this assumed case-insensitivity for these specific columns (`status`, `city`). Penalize only if the core logic (joins, other conditions, selected columns etc.) is wrong.
        Also, assume the student *can* use **either single quotes (') or double quotes (")** for string literals in their query for this quiz simulation, as the system attempts to convert double to single quotes. Do not mark down for using double quotes if the logic is correct.

    * **Validity:** Is the query syntactically valid standard SQL (ignoring the double quote allowance and case-insensitivity behavior mentioned above)? Briefly mention any *other* syntax errors if the query fails simulation for other reasons.
    * **Logic:** Does the query use appropriate SQL clauses (SELECT, FROM, WHERE, JOIN, GROUP BY, ORDER BY, aggregates, etc.) correctly for the task? Is the logic sound? Are comparisons appropriate for the data types (keeping the case-insensitivity rule for `status`/`city` in mind)?
    * **Alternatives:** Briefly acknowledge if the student used a valid alternative approach (e.g., different JOIN type if appropriate, subquery vs. JOIN). Mentioning `LOWER`/`UPPER` or using single quotes as *generally good practice* for other SQL environments is okay, but don't imply it was *required* for correctness *here*.
    * **Feedback:** Provide clear, constructive feedback in a friendly, encouraging, casual Hindi tone (like a helpful senior or 'bhaiya' talking to a learner).
        * If incorrect (due to reasons *other* than case-sensitivity on `status`/`city` or using double quotes, IF those were handled by simulation): Gently point out the error (e.g., "Arre yaar, yahaan thoda sa check karo..." or "Ek chhoti si galti ho gayi hai..."). Explain *what* is wrong (syntax, logic, columns, joins, other conditions etc.). Suggest how to fix it. **Do NOT mark the query incorrect or suggest using LOWER()/UPPER() or single quotes *solely* because of case differences in `status`/`city` or the use of double quotes if the rest of the logic is correct and the simulation handles it.**
    * **Verdict:** Conclude your entire response with *exactly* one line formatted as: "Verdict: Correct" or "Verdict: Incorrect". This line MUST be the very last line.

    **Begin Evaluation:**
    """

    feedback_llm = "AI feedback generation failed."; is_correct_llm = False; llm_output = "Error: No LLM response received."
    try:
        response = model.generate_content(prompt)
        extracted_text = None
        try:
            if hasattr(response, 'text'):
                extracted_text = response.text
            elif hasattr(response, 'parts') and response.parts:
                extracted_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
            else:
                try:
                    extracted_text = f"AI Response Blocked or Empty. Prompt Feedback: {response.prompt_feedback}"
                except Exception:
                    extracted_text = "Error: Received unexpected or empty response structure from AI."

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
                    st.warning(f"⚠️ Could not parse AI verdict from response.")
                    print(f"WARNING: Could not parse verdict from LLM output:\n---\n{llm_output}\n---")
                    feedback_llm = llm_output + "\n\n_(System Note: AI correctness check might be unreliable as verdict wasn't found.)_"
                    is_correct_llm = False # Default to incorrect if verdict is unparsable
                feedback_llm = feedback_llm.replace("student", "aap")

        except AttributeError as ae:
            llm_output = f"Error: Unexpected response format from AI. Details: {ae}"
            print(f"ERROR: Unexpected response format from AI: {response}")
            feedback_llm = f"AI feedback format error: {ae}"
            is_correct_llm = False
        except Exception as e_resp:
            llm_output = f"Error processing AI response: {e_resp}"
            print(f"ERROR: Processing AI response failed: {e_resp}")
            feedback_llm = f"AI response processing error: {e_resp}"
            is_correct_llm = False

    except Exception as e_call:
        st.error(f"🚨 AI Error during evaluation: {e_call}")
        print(f"ERROR: Gemini API call failed: {e_call}")
        feedback_llm = f"AI feedback generation error: {e_call}"
        is_correct_llm = False
        llm_output = f"Error during AI call: {e_call}"

    actual_result_sim = simulate_query_duckdb(student_answer, original_tables_dict)
    expected_result_sim = simulate_query_duckdb(correct_answer_example, original_tables_dict)
    
    # If LLM says correct, but simulation fails for student query, it's likely incorrect.
    if is_correct_llm and isinstance(actual_result_sim, str) and "Simulation Error" in actual_result_sim:
        is_correct_llm = False
        feedback_llm += f"\n\n**Mentor Note:** AI initially thought this was correct, but your query had a simulation error: {actual_result_sim}. So, marking it as needing a fix."

    # If LLM says incorrect, but student simulation matches expected simulation (and both are dataframes), then it IS correct.
    if not is_correct_llm and isinstance(actual_result_sim, pd.DataFrame) and isinstance(expected_result_sim, pd.DataFrame):
        try:
            # Basic check: same shape and all values equal (handles NaNs correctly)
            if actual_result_sim.shape == expected_result_sim.shape and actual_result_sim.equals(expected_result_sim):
                is_correct_llm = True
                feedback_llm = "Waah! Aapka query bilkul sahi result de raha hai simulation mein, aur AI ke initial assessment se behtar nikla. Badhiya kaam! ✅" + \
                               "\n\nOriginal AI Feedback (for reference, may not be fully applicable now):\n" + feedback_llm
        except Exception as e_comp:
            print(f"Error comparing simulation DataFrames: {e_comp}")


    return feedback_llm, is_correct_llm, expected_result_sim, actual_result_sim, llm_output


def calculate_score(user_answers):
    """Calculates the percentage score based on the list of user answers."""
    if not user_answers: return 0.0
    correct_count = sum(1 for ans in user_answers if ans.get("is_correct", False))
    total_questions_answered = len(user_answers) # Considers skipped as answered (and incorrect)
    score = (correct_count / len(sql_questions)) * 100 if len(sql_questions) > 0 else 0.0 # Score out of total questions
    return score


def analyze_performance(user_answers):
    """
    Analyzes the user's overall performance using the Gemini API based on all answers.
    Provides strengths, weaknesses, and overall feedback.
    """
    performance_data = {
        "strengths": [], "weaknesses": [],
        "overall_feedback": "Performance analysis could not be completed."
    }
    if not user_answers and len(sql_questions) > 0 : # if user_answers is empty but quiz started
        all_questions_skipped = True
        for q_idx in range(len(sql_questions)):
            found = False
            for ans in user_answers:
                if ans["question_index"] == q_idx:
                    found = True
                    break
            if not found: # Question not in user_answers, implies it wasn't even skipped via button
                # This case should ideally be handled by how user_answers is populated
                # Assuming if a question is not in user_answers, it wasn't attempted
                 pass # Or treat as skipped

    # If user_answers is truly empty (e.g. quiz started and immediately quit or error)
    if not user_answers and not st.session_state.quiz_completed: # Check if quiz was even completed
         performance_data["overall_feedback"] = "Aapne abhi tak koi sawaal attempt nahi kiya. Analysis ke liye kuch jawaab toh do!"
         return performance_data
    elif not user_answers and st.session_state.quiz_completed: # Quiz completed but no answers (e.g. all skipped implicitly)
         performance_data["overall_feedback"] = "Aisa lagta hai aapne saare sawaal skip kar diye. Thoda try toh banta hai! Analysis abhi possible nahi."
         return performance_data


    try:
        correct_q_details = [{"question": sql_questions[ans["question_index"]]["question"], "answer": ans["student_answer"]} for ans in user_answers if ans.get("is_correct")]
        incorrect_ans = [
            {"question_index": ans["question_index"],
             "question": sql_questions[ans["question_index"]]["question"],
             "your_answer": ans["student_answer"],
             "feedback_received": ans.get("feedback", "N/A")}
            for ans in user_answers if not ans.get("is_correct")
        ]
        performance_data["strengths"] = [item["question"] for item in correct_q_details]
        performance_data["weaknesses"] = [item["question"] for item in incorrect_ans]
        
        total_attempted_or_skipped = len(user_answers)
        total_questions_in_quiz = len(sql_questions)
        correct_c = len(correct_q_details)
        score = calculate_score(user_answers) # Uses the main score function

        incorrect_summary = ""
        if incorrect_ans:
            incorrect_summary = "In sawaalon mein thodi galti hui ya skip kiya:\n"
            for idx, item in enumerate(incorrect_ans):
                feedback_snippet = item['feedback_received'][:150].strip() + ('...' if len(item['feedback_received']) > 150 else '')
                answer_display = f"`{item['your_answer']}`" if item['your_answer'] != "SKIPPED" else "_SKIPPED_"
                incorrect_summary += f"  {idx+1}. Sawaal: {item['question']}\n     Aapka Jawaab: {answer_display}\n     Feedback Mila: {feedback_snippet}\n"
            incorrect_summary = incorrect_summary.strip()
        else:
            incorrect_summary = "Koi galat jawaab nahi! Bahut badhiya!"

        correct_summary = ""
        if correct_q_details:
            correct_summary = "Yeh sawaal bilkul sahi kiye:\n"
            for idx, item in enumerate(correct_q_details):
                correct_summary += f"  - {item['question']}\n" #  (Aapka Sahi Jawaab: `{item['answer']}`)\n"
            correct_summary = correct_summary.strip()
        else:
            correct_summary = "Is baar koi jawaab sahi nahi hua."

        prompt = f"""
        Ek SQL learner ne ek practice quiz complete kiya hai. Unki performance ka analysis karke ek friendly, motivating summary feedback casual Hindi mein (jaise ek senior/mentor deta hai) provide karo.

        **Quiz Performance Summary:**
        - Total Questions in Quiz: {total_questions_in_quiz}
        - Questions Attempted/Skipped: {total_attempted_or_skipped}
        - Correct Answers: {correct_c}
        - Final Score: {score:.2f}%

        **Correctly Answered Questions & Your Answers:**
        {correct_summary if correct_q_details else '(Koi nahi)'}

        **Incorrectly Answered/Skipped Questions & Feedback Snippets:**
        {incorrect_summary if incorrect_ans else '(Koi galat ya skip kiya hua sawaal nahi! Kamaal hai!)'}

        **Quiz Context Reminder (for your AI analysis, not for student):**
        - Case-insensitivity was simulated for '=' comparisons on 'status' and 'city' columns.
        - Both single (') and double (") quotes were acceptable for string literals in this quiz simulation.

        **Task:**
        Ab, neeche diye gaye structure mein overall performance ka ek summary feedback do. Student ko "aap" kehkar address karna:
        1.  **Overall Impression:** Score aur general performance pe ek positive ya encouraging comment (e.g., "Overall, aapki performance kaafi achhi rahi!", "Thodi aur practice lagegi, but potential hai!"). Be realistic but motivating. Agar score kam hai, toh bhi positive raho.
        2.  **Strengths (Kya Achha Kiya):** Agar kuch specific concepts sahi kiye hain (jo correct answers se pata chale), unko highlight karo (e.g., "SELECT aur WHERE clause ka use aapne aache se samajha hai.", "JOINs wale sawaal sahi kiye, yeh achhi baat hai!"). General rakho agar specific pattern na dikhe. Agar sab galat the, to isko skip kar sakte ho ya keh sakte ho ki "Abhi shuruat hai, seekh jayenge!"
        3.  **Areas for Improvement (Kahaan Dhyaan Dena Hai):** Jo concepts galat hue (incorrect answers se related), unko gently point out karo. Focus on concepts, not just specific mistakes (e.g., "JOIN ka logic thoda aur clear karna hoga shayad.", "Aggregate functions (COUNT, AVG) pe dhyaan dena.", "Syntax ki chhoti-moti galtiyan ho rahi hain."). Briefly mention standard practices (like single quotes for strings in real DBs, or using `LOWER`/`UPPER` for case control) as a learning point for *general SQL knowledge*, without implying it was wrong *in this specific quiz*.
        4.  **Next Steps / Encouragement (Aage Kya?):** Kuch encouraging words aur aage kya karna chahiye (e.g., "Keep practicing!", "Concept X ko revise kar lena.", "Aise hi lage raho, SQL aa jayega! Real-world databases ke liye standard SQL practices (jaise hamesha single quotes use karna, aur case sensitivity ka dhyaan rakhna) bhi important hain, toh unhe bhi dekhte rehna.").

        Bas plain text mein feedback generate karna hai. Casual, friendly, and motivating tone rakhna. Sidhe feedback se shuru karo (e.g., "Chalo dekhte hain aapki SQL quiz performance kaisi rahi..."). Avoid repeating the score and stats unless it's naturally part of the flow.
        """
    except Exception as data_prep_error:
        print(f"Error preparing data for performance analysis: {data_prep_error}")
        performance_data["overall_feedback"] = f"Analysis data preparation failed: {data_prep_error}"
        return performance_data

    try:
        response = model.generate_content(prompt)
        generated_feedback = None
        if hasattr(response, 'text'):
            generated_feedback = response.text.strip()
        elif hasattr(response, 'parts') and response.parts:
                generated_feedback = "".join(part.text for part in response.parts if hasattr(part, 'text')).strip()
        else:
                try:
                    generated_feedback = f"AI Response Blocked or Empty. Prompt Feedback: {response.prompt_feedback}"
                except Exception:
                    generated_feedback = "Error: Received unexpected or empty response from AI for summary."

        if generated_feedback:
            performance_data["overall_feedback"] = generated_feedback
        else:
            performance_data["overall_feedback"] = "AI response format unclear or empty for summary analysis."
            print(f"Warning: Unexpected LLM response for performance summary.")
    except Exception as e:
        print(f"Error generating performance summary using LLM: {e}")
        performance_data["overall_feedback"] = f"Summary generation error from AI: {e}"

    return performance_data


def get_emoji(is_correct):
    """Returns a check or cross emoji based on correctness."""
    return "✅" if is_correct else "❌"


def display_simulation(title, result_data):
    """
    Helper function to display simulation results (DataFrame or error string)
    in the Streamlit app.
    """
    st.write(f"**{title}:**")
    if isinstance(result_data, pd.DataFrame):
        if result_data.empty:
            st.info("_(Simulation resulted in an empty table)_")
        else:
            st.dataframe(result_data.reset_index(drop=True), hide_index=True, use_container_width=True)
    elif isinstance(result_data, str) and "Simulation Error" in result_data:
        st.warning(result_data, icon="⚠️")
    elif result_data is None or result_data == "N/A": # Handles None or "N/A"
        st.info("_(Simulation not applicable, not run, or no data to show)_")
    elif isinstance(result_data, str):
        st.info(f"_{result_data}_") # Display other string messages if any
    else:
        st.error(f"_(Unexpected simulation result type: {type(result_data)})_")
        print(f"DEBUG: Unexpected simulation data type: {type(result_data)}, value: {result_data}")


# --- Streamlit App UI ---

# --- Start Screen ---
if not st.session_state.quiz_started:
    st.title("🚀 SQL Mentor - Interactive SQL Practice")
    st.markdown("### Apne SQL Skills Ko Test Aur Improve Karein!")
    st.markdown("""
        **📌 Important Notes:**
        - This quiz uses standard **SQL syntax** (similar to MySQL/PostgreSQL).
        - String comparisons (like `WHERE city = 'new york'` or `WHERE status = "pending"`) are simulated to be **case-insensitive** for specific text columns (`status` in `orders`, `city` in `users`). The system tries to use `ILIKE` or similar for this.
        - **Both single quotes (') and double quotes (") are accepted** for string literals in this simulation (the system attempts to convert double to single quotes for the backend).
        - Your queries are evaluated by an AI for correctness and logic.
        - Query simulation is powered by DuckDB to show results on sample data.
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

    st.write("### 🔍 Table Previews")
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
        - String literals can be enclosed in single quotes (`'...'`) or double quotes (`"..."`).
        """)

    if st.button("🚀 Start SQL Challenge!", type="primary"):
        st.session_state.quiz_started = True
        st.session_state.current_question = 0
        st.session_state.user_answers = []
        st.session_state.quiz_completed = False
        st.session_state.show_detailed_feedback = False
        st.session_state.show_detailed_feedback_on_completion = False
        # Clear any previous dynamic states
        for key in list(st.session_state.keys()):
            if key.startswith("query_input_") or key.startswith("answer_feedback_"):
                del st.session_state[key]
        st.rerun()

# --- Quiz In Progress or Completed ---
elif st.session_state.quiz_started:

    # --- Quiz Completed Screen ---
    if st.session_state.quiz_completed:
        st.title("🎉 SQL Challenge Completed! 🎉")
        st.balloons()

        final_score = calculate_score(st.session_state.user_answers)
        st.subheader(f"🏆 Your Final Score: {final_score:.2f}%")

        if st.checkbox("Show Detailed Feedback for All Questions", value=st.session_state.get("show_detailed_feedback_on_completion", False)):
            st.markdown("---")
            st.header("📜 Detailed Feedback per Question:")
            if not st.session_state.user_answers:
                st.info("You did not attempt or submit any questions.")
            else:
                for i, ans_data in enumerate(st.session_state.user_answers):
                    # Find the original question data using question_index
                    q_data = sql_questions[ans_data["question_index"]]
                    with st.expander(f"{get_emoji(ans_data['is_correct'])} Question {ans_data['question_index']+1}: {q_data['question']}", expanded=not ans_data['is_correct']):
                        st.markdown(f"**Your Answer:**\n```sql\n{ans_data['student_answer']}\n```")
                        st.markdown(f"**AI Mentor's Feedback:**\n{ans_data.get('feedback', 'No feedback available.')}")
                        
                        if "actual_result_sim" in ans_data:
                            display_simulation("Your Query's Result (Simulation)", ans_data["actual_result_sim"])
                        if "expected_result_sim" in ans_data and not ans_data['is_correct'] and not isinstance(ans_data["expected_result_sim"], str):
                            display_simulation("Expected Result (Simulation for Correct Answer)", ans_data["expected_result_sim"])
            st.session_state.show_detailed_feedback_on_completion = True # Keep it true if checkbox is checked
        else:
            st.session_state.show_detailed_feedback_on_completion = False


        st.markdown("---")
        st.header("📊 Overall Performance Analysis")
        with st.spinner("Guru ji aapki performance analyze kar rahe hain..."):
            performance_summary = analyze_performance(st.session_state.user_answers)
        
        st.markdown(performance_summary.get("overall_feedback", "Could not load performance feedback."))
        
        st.markdown("---") 
        if final_score >= 80:
            st.link_button("🏆 Generate Certificate!", "https://superprofile.bio/vp/corporate-bhaiya-sql-page", use_container_width=True, type="primary")
            st.success("Congratulations on scoring 80% or above! Click the button above to generate your certificate.")
        else:
            st.link_button("📚 Book a Mentor Session with Corporate Bhaiya", "https://topmate.io/corporate_bhaiya", use_container_width=True, type="primary") # Replace with actual link if different
            st.info("Keep practicing! You can book a mentor session to improve your skills by clicking the button above.")

        st.markdown("---")
        if st.button("🔄 Restart Quiz Now"):
            st.session_state.quiz_started = False
            st.session_state.quiz_completed = False
            st.session_state.current_question = 0
            st.session_state.user_answers = []
            st.session_state.show_detailed_feedback = False
            st.session_state.show_detailed_feedback_on_completion = False
            for key in list(st.session_state.keys()):
                if key.startswith("query_input_") or key.startswith("answer_feedback_"):
                    del st.session_state[key]
            st.rerun()

    # --- Quiz Questions ---
    else: 
        current_q_index = st.session_state.current_question
        
        if current_q_index < len(sql_questions):
            question_data = sql_questions[current_q_index]
            st.header(f"🧠 Question {current_q_index + 1} of {len(sql_questions)}")
            st.info(question_data["question"])

            st.subheader("Relevant Table Schema(s) & Sample Data:")
            tab_titles = []
            tab_contents = []

            for table_name in question_data["relevant_tables"]:
                df_schema = original_tables.get(table_name)
                if df_schema is not None:
                    tab_titles.append(f"📜 {table_name}")
                    # Create content for this tab
                    with st.container(): # Use a container to group elements for a tab
                        md_content = f"**Table: `{table_name}`**\n"
                        schema_df = pd.DataFrame({
                            'Column': df_schema.columns,
                            'Data Type': [str(dtype) for dtype in df_schema.dtypes]
                        })
                        # md_content += schema_df.to_markdown(index=False) + "\n\n" # Using dataframe directly
                        # md_content += f"**Sample Data (first 3 rows of `{table_name}`):**\n"
                        # md_content += df_schema.head(3).to_markdown(index=False)
                        tab_contents.append((md_content, schema_df, df_schema.head(3)))
                else:
                    tab_titles.append(f"⚠️ {table_name}")
                    tab_contents.append((f"Schema for table '{table_name}' not found.", None, None))
            
            if tab_titles:
                tabs = st.tabs(tab_titles)
                for i, tab_widget in enumerate(tabs):
                    with tab_widget:
                        md_c, schema_d, sample_d = tab_contents[i]
                        st.markdown(md_c)
                        if schema_d is not None:
                             st.dataframe(schema_d, hide_index=True, use_container_width=True)
                             st.markdown(f"**Sample Data (first 3 rows):**")
                             st.dataframe(sample_d, hide_index=True, use_container_width=True)
            
            st.markdown("---")
            user_query = st.text_area("📝 Your SQL Query:", height=150, key=f"query_input_{current_q_index}")

            current_answer_key = f"answer_feedback_{current_q_index}"
            if current_answer_key not in st.session_state:
                st.session_state[current_answer_key] = {}

            col_submit, col_skip = st.columns(2)
            with col_submit:
                if st.button("✅ Submit Answer", key=f"submit_{current_q_index}", use_container_width=True, type="primary"):
                    if user_query.strip():
                        with st.spinner("AI Mentor is evaluating your answer... 🤔"):
                            feedback, is_correct, expected_sim, actual_sim, llm_raw_output = evaluate_answer_with_llm(
                                question_data,
                                user_query,
                                original_tables
                            )
                        
                        # Check if this question was already answered/skipped
                        # If so, update it; otherwise, append.
                        answer_updated = False
                        for i, ans in enumerate(st.session_state.user_answers):
                            if ans["question_index"] == current_q_index:
                                st.session_state.user_answers[i] = {
                                    "question_index": current_q_index, "question": question_data["question"],
                                    "student_answer": user_query, "feedback": feedback, "is_correct": is_correct,
                                    "expected_result_sim": expected_sim, "actual_result_sim": actual_sim,
                                    "llm_raw_output": llm_raw_output
                                }
                                answer_updated = True
                                break
                        if not answer_updated:
                             st.session_state.user_answers.append({
                                "question_index": current_q_index, "question": question_data["question"],
                                "student_answer": user_query, "feedback": feedback, "is_correct": is_correct,
                                "expected_result_sim": expected_sim, "actual_result_sim": actual_sim,
                                "llm_raw_output": llm_raw_output
                            })
                        
                        st.session_state[current_answer_key] = {
                            "submitted": True, "feedback": feedback, "is_correct": is_correct,
                            "actual_sim": actual_sim, "expected_sim": expected_sim, "student_answer": user_query
                        }
                        st.session_state.show_detailed_feedback = True 
                        st.rerun() 
                    else:
                        st.warning("Please enter your SQL query before submitting.")
            
            with col_skip:
                 if st.button("➡️ Skip Question", key=f"skip_{current_q_index}", use_container_width=True):
                    answer_updated = False
                    for i, ans in enumerate(st.session_state.user_answers):
                        if ans["question_index"] == current_q_index:
                            st.session_state.user_answers[i] = {
                                "question_index": current_q_index, "question": question_data["question"],
                                "student_answer": "SKIPPED", "feedback": "Question skipped by user.", "is_correct": False,
                                "expected_result_sim": "N/A", "actual_result_sim": "N/A", "llm_raw_output": "N/A"
                            }
                            answer_updated = True
                            break
                    if not answer_updated:
                        st.session_state.user_answers.append({
                            "question_index": current_q_index, "question": question_data["question"],
                            "student_answer": "SKIPPED", "feedback": "Question skipped by user.", "is_correct": False,
                            "expected_result_sim": "N/A", "actual_result_sim": "N/A", "llm_raw_output": "N/A"
                        })

                    st.session_state[current_answer_key] = {} 
                    st.session_state.show_detailed_feedback = False 

                    if st.session_state.current_question + 1 < len(sql_questions):
                        st.session_state.current_question += 1
                    else:
                        st.session_state.quiz_completed = True
                        st.session_state.show_detailed_feedback_on_completion = True 
                    st.rerun()

            if st.session_state.show_detailed_feedback and st.session_state[current_answer_key].get("submitted"):
                feedback_data = st.session_state[current_answer_key]
                st.markdown("---")
                st.subheader("🔍 AI Mentor's Feedback:")
                
                if feedback_data["is_correct"]:
                    st.success(f"**{get_emoji(True)} Correct!** {feedback_data['feedback']}")
                else:
                    st.error(f"**{get_emoji(False)} Needs Improvement.** {feedback_data['feedback']}")

                display_simulation("Your Query's Result (Simulation)", feedback_data["actual_sim"])
                if not feedback_data["is_correct"] and not isinstance(feedback_data["expected_sim"], str) and feedback_data["expected_sim"] is not None :
                     display_simulation("Expected Result (Simulation for Correct Answer)", feedback_data["expected_sim"])
                elif isinstance(feedback_data["expected_sim"], str) and "Error" in feedback_data["expected_sim"] and not feedback_data["is_correct"]:
                     st.warning(f"Note: Could not simulate the expected correct answer for comparison: {feedback_data['expected_sim']}")

                st.markdown("---")
                if st.session_state.current_question + 1 < len(sql_questions):
                    if st.button("➡️ Next Question", key=f"next_q_{current_q_index}", use_container_width=True):
                        st.session_state.current_question += 1
                        st.session_state.show_detailed_feedback = False 
                        # st.session_state[current_answer_key]["submitted"] = False # Reset for current q
                        st.rerun()
                else:
                    if st.button("🏁 Finish Quiz & See Results", key=f"finish_{current_q_index}", use_container_width=True, type="primary"):
                        st.session_state.quiz_completed = True
                        st.session_state.show_detailed_feedback = False 
                        st.session_state.show_detailed_feedback_on_completion = True 
                        st.rerun()
            
            st.sidebar.markdown("---")
            st.sidebar.subheader("Quiz Progress:")
            # Count how many unique questions have an entry in user_answers
            processed_q_indices = {ans["question_index"] for ans in st.session_state.user_answers}
            questions_processed_count = len(processed_q_indices)

            st.sidebar.progress(questions_processed_count / len(sql_questions))
            st.sidebar.write(f"{questions_processed_count} / {len(sql_questions)} questions processed.")
            st.sidebar.markdown("---")
            if st.sidebar.button("🔙 Restart Quiz (Progress will be lost)"):
                st.session_state.quiz_started = False
                st.session_state.quiz_completed = False
                st.session_state.current_question = 0
                st.session_state.user_answers = []
                st.session_state.show_detailed_feedback = False
                st.session_state.show_detailed_feedback_on_completion = False
                for key in list(st.session_state.keys()):
                    if key.startswith("query_input_") or key.startswith("answer_feedback_"):
                        del st.session_state[key]
                st.rerun()

        else: 
            st.session_state.quiz_completed = True
            st.session_state.show_detailed_feedback_on_completion = True
            st.rerun() 
else:
    st.session_state.quiz_started = False # Fallback to reset to start screen
    st.rerun()
    
