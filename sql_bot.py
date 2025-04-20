import streamlit as st
import google.generativeai as genai
import pandas as pd
import re # Needed for regex query modification
import duckdb # Import DuckDB
# import copy # No longer needed

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
# Replace "YOUR_API_KEY_HERE" with your actual Gemini API Key
gemini_api_key = "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k" # Your specific API Key
if not gemini_api_key or gemini_api_key == "YOUR_API_KEY_HERE": # Basic check
    st.error("🚨 Gemini API Key is missing or hasn't been replaced. Please add your key in the code.")
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
    "city": ["New York", "Los Angeles", "Chicago", "Houston"] # Mixed case cities
})
orders_table = pd.DataFrame({
    "order_id": [101, 102, 103, 104, 105],
    "user_id": [1, 2, 3, 1, 4],
    "amount": [50.00, 75.50, 120.00, 200.00, 35.00],
    "order_date": pd.to_datetime(["2024-02-01", "2024-02-05", "2024-02-10", "2024-02-15", "2024-02-20"]),
    "status": ["Completed", "Pending", "Completed", "Shipped", "Cancelled"] # Original case data
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
    { "question": "Write a SQL query to find all orders with a status of 'Pending' from the 'orders' table.", "correct_answer_example": "SELECT * FROM orders WHERE status = 'Pending';", "sample_table": orders_table, "relevant_tables": ["orders"] }, # Test case-insensitivity here
    { "question": "Write a SQL query to find users from 'chicago' in the 'users' table (test case-insensitivity).", "correct_answer_example": "SELECT * FROM users WHERE city = 'Chicago';", "sample_table": users_table, "relevant_tables": ["users"] }, # Test case-insensitivity here
    { "question": "Write a SQL query to find the most recent order from the 'orders' table by order date.", "correct_answer_example": "SELECT * FROM orders ORDER BY order_date DESC LIMIT 1;", "sample_table": orders_table, "relevant_tables": ["orders"] },
    { "question": "Write a SQL query to find the average order amount from the 'orders' table.", "correct_answer_example": "SELECT AVG(amount) AS average_amount FROM orders;", "sample_table": orders_table, "relevant_tables": ["orders"] },
    { "question": "Write a SQL query to find users from 'New York' or 'Chicago' in the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE city IN ('New York', 'Chicago');", "sample_table": users_table, "relevant_tables": ["users"] },

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

# ******************************************************************************
# ***** MODIFIED simulate_query_duckdb function starts here *****
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
    # This makes the query syntax valid for DuckDB (and standard SQL) before further processing.
    try:
        # Pattern to find "string content" (non-greedy match for content)
        double_quote_pattern = r'"([^"]*)"' # Finds "content"
        # Replace "content" with 'content'
        processed_query_for_ilike = re.sub(double_quote_pattern, r"'\1'", sql_query)

        if processed_query_for_ilike != sql_query:
             print(f"Original query: {sql_query}")
             print(f"Query after double->single quote conversion: {processed_query_for_ilike}")
    except Exception as e_quotes:
        print(f"Warning: Failed during double quote replacement: {e_quotes}. Proceeding with original query structure for ILIKE.")
        # Fallback: If replacement fails, continue with the original query string for ILIKE processing.
        # This might still lead to parser errors later if double quotes were the issue.
        processed_query_for_ilike = sql_query

    # --- Step 2: Query Modification Attempt (using ILIKE on the potentially quote-corrected query) ---
    modified_sql_query = processed_query_for_ilike # Start ILIKE processing with the potentially modified query
    final_executed_query = modified_sql_query # Keep track of the query actually sent to DuckDB

    # Define columns for which '=' should be treated as case-insensitive (ILIKE)
    case_insensitive_columns = {
        "orders": ["status"],
        "users": ["city"]
    }
    flat_insensitive_columns = [col for cols in case_insensitive_columns.values() for col in cols]

    if flat_insensitive_columns: # Only attempt ILIKE rewrite if there are columns to modify
        try:
            # Regex pattern: finds patterns like `col_name = 'value'` or `col_name='value'` etc.
            # where col_name is one of our target columns. Handles spaces.
            # ASSUMES single quotes after the previous conversion step.
            # (?:...) is a non-capturing group
            # \b ensures we match whole words for column names
            col_pattern_part = "|".join([r"\b" + re.escape(col) + r"\b" for col in flat_insensitive_columns])

            # Pattern Breakdown (Simplified assuming single quotes):
            # (.*?)                         # Capture group 1: Anything before the column name (non-greedy)
            # (\b(?:{col_pattern_part})\b)  # Capture group 2: The specific column name (e.g., status, city)
            # (\s*=\s*)                     # Capture group 3: The equals sign, potentially surrounded by spaces
            # ('[^']+')                     # Capture group 4: The string literal in SINGLE quotes
            pattern = rf"(.*?)({col_pattern_part})(\s*=\s*)('[^']+')"

            def replace_with_ilike(match):
                pre_context = match.group(1)
                col_name = match.group(2)
                # operator = match.group(3) # We know this is '='
                literal = match.group(4) # The single-quoted literal
                print(f"Rewriting query part: Replacing '=' with 'ILIKE' for column '{col_name}'")
                # Add space before ILIKE if needed
                space_prefix = "" if not pre_context or pre_context.endswith(" ") or pre_context.endswith("(") else " "
                return f"{pre_context}{space_prefix}{col_name} ILIKE {literal}" # Replace = with ILIKE

            # Apply the replacement using re.sub with IGNORECASE flag for the pattern matching itself
            modified_sql_query = re.sub(pattern, replace_with_ilike, processed_query_for_ilike, flags=re.IGNORECASE)
            final_executed_query = modified_sql_query # Update the query to be executed

            if modified_sql_query != processed_query_for_ilike:
                  # Only print if ILIKE rewrite happened
                  print(f"Query after ILIKE rewrite: {modified_sql_query}")

        except Exception as e_rewrite:
            print(f"Warning: Failed to rewrite query for case-insensitivity (ILIKE), using quote-converted query. Error: {e_rewrite}")
            # Fallback to the query after quote conversion if ILIKE rewrite fails
            final_executed_query = processed_query_for_ilike

    # --- Step 3: Connect and Execute with DuckDB ---
    try:
        con = duckdb.connect(database=':memory:', read_only=False)
        for table_name, df in tables_dict.items():
            if isinstance(df, pd.DataFrame):
                con.register(str(table_name), df)
            else:
                 print(f"Warning [simulate_query]: Item '{table_name}' not a DataFrame during registration.")

        # Execute the final query (potentially modified for quotes and ILIKE)
        print(f"Executing final query in DuckDB: {final_executed_query}")
        result_df = con.execute(final_executed_query).df()
        con.close()
        return result_df

    except Exception as e:
        error_message = f"Simulation Error: Failed to execute query. Reason: {str(e)}"
        # Add hints based on the error type and the transformations attempted
        e_str = str(e).lower()
        hint = ""

        # Check if the error might be related to the ILIKE rewrite
        if "ILIKE" in str(e).upper() or (modified_sql_query != processed_query_for_ilike and "syntax error" in e_str):
            hint = "\n\n**Hint:** The simulation tried using case-insensitive matching (ILIKE). Check your SQL syntax near the comparison, especially if using complex conditions."
        else:
            # General error parsing hints
            catalog_match = re.search(r'catalog error:.*table with name "([^"]+)" does not exist', e_str)
            binder_match = re.search(r'(?:binder error|catalog error):.*column "([^"]+)" not found', e_str)
            # DuckDB Parser error format
            syntax_match = re.search(r'parser error: syntax error at or near "([^"]+)"', e_str) \
                        or re.search(r'parser error: syntax error at end of input', e_str) # Catch errors at end
            type_match = re.search(r'conversion error:.*try cast\("([^"]+)"', e_str)

            if catalog_match: hint = f"\n\n**Hint:** Table '{catalog_match.group(1)}' might be misspelled or doesn't exist. Available tables: {list(tables_dict.keys())}."
            elif binder_match: hint = f"\n\n**Hint:** Column '{binder_match.group(1)}' might be misspelled or doesn't exist in the referenced table(s)."
            elif syntax_match:
                problem_area = syntax_match.group(1) if syntax_match.lastindex else "the end of your query"
                hint = f"\n\n**Hint:** Check your SQL syntax, especially around `{problem_area}`. Remember standard SQL uses single quotes (') for text values like `'example text'` (though the tool tries to handle double quotes)."
            elif type_match: hint = f"\n\n**Hint:** There might be a type mismatch. You tried using '{type_match.group(1)}' in a way that's incompatible with its data type (e.g., comparing text to a number)."
            elif "syntax error" in e_str: # Generic syntax hint if specific pattern not matched
                 hint = "\n\n**Hint:** Double-check your SQL syntax. Ensure all clauses (SELECT, FROM, WHERE, etc.) are correct and in order. Use single quotes (') for string values."

        if not hint: # Fallback generic hint
             hint = "\n\n**Hint:** Double-check your query syntax, table/column names, and data types. Use single quotes (') for string values in standard SQL."

        error_message += hint

        print(f"ERROR [simulate_query_duckdb]: {error_message}\nOriginal Query: {sql_query}\nFinal Attempted Query: {final_executed_query}")
        if con:
            try: con.close()
            except: pass
        return error_message

# ******************************************************************************
# ***** MODIFIED simulate_query_duckdb function ends here *****
# ******************************************************************************


def get_table_schema(table_name, tables_dict):
    """Gets column names for a given table name."""
    if table_name in tables_dict and isinstance(tables_dict[table_name], pd.DataFrame):
        return tables_dict[table_name].columns.astype(str).tolist()
    return []

def evaluate_answer_with_llm(question_data, student_answer, original_tables_dict):
    """Evaluate the user's answer using Gemini API and simulate using DuckDB."""
    if not student_answer.strip(): return "Please provide an answer.", False, "N/A", "N/A", "No input."
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

    # ***** MODIFIED PROMPT START (No change needed here, LLM evaluates based on question/schema) *****
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
        For *this specific quiz*, assume that simple equality comparisons (`=`) involving the text columns `'status'` (in `orders`) and `'city'` (in `users`) are effectively **CASE-INSENSITIVE**. The quiz environment simulates this behavior.
        Therefore, a query like `WHERE status = 'pending'` **should be considered CORRECT** if the question asks for 'Pending' status, even if the student did not use explicit `LOWER()` or `UPPER()` functions.
        Evaluate the *logic* of the query based on this assumed case-insensitivity for these specific columns (`status`, `city`). Penalize only if the core logic (joins, other conditions, selected columns etc.) is wrong.
        Also, assume the student *can* use **either single quotes (') or double quotes (")** for string literals in their query for this quiz simulation, even though single quotes are standard SQL. Do not mark down for using double quotes if the logic is correct.

    * **Validity:** Is the query syntactically valid standard SQL (ignoring the double quote allowance above)? Briefly mention any *other* syntax errors.
    * **Logic:** Does the query use appropriate SQL clauses (SELECT, FROM, WHERE, JOIN, GROUP BY, ORDER BY, aggregates, etc.) correctly for the task? Is the logic sound? Are comparisons appropriate for the data types (keeping the case-insensitivity rule for `status`/`city` in mind)?
    * **Alternatives:** Briefly acknowledge if the student used a valid alternative approach (e.g., different JOIN type if appropriate, subquery vs. JOIN). Mentioning `LOWER`/`UPPER` or using single quotes as *generally good practice* is okay, but don't imply it was *required* for correctness *here*.
    * **Feedback:** Provide clear, constructive feedback in a friendly, encouraging, casual Hindi tone (like a helpful senior or 'bhaiya' talking to a learner).
        * If correct (considering the case-insensitivity rule and quote flexibility): Praise the student (e.g., "Wah yaar, zabardast query likhi hai! Bilkul sahi logic lagaya.") and briefly explain *why* it's correct. You can optionally add a small note like "Aur haan, yaad rakhna ki asal databases mein case ka dhyaan rakhna padta hai aur string ke liye single quotes (') use karna standard hai, par yahaan is quiz ke liye yeh bilkul sahi hai!".
        * If incorrect (due to reasons *other* than case-sensitivity on `status`/`city` or using double quotes): Gently point out the error (e.g., "Arre yaar, yahaan thoda sa check karo..." or "Ek chhoti si galti ho gayi hai..."). Explain *what* is wrong (syntax, logic, columns, joins, other conditions etc.). Suggest how to fix it. **Do NOT mark the query incorrect or suggest using LOWER()/UPPER() or single quotes *solely* because of case differences in `status`/`city` or the use of double quotes if the rest of the logic is correct.**
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

    # Simulate student's query (using the modified function that handles quotes)
    actual_result_sim = simulate_query_duckdb(student_answer, original_tables_dict)
    # Simulate correct query (using the modified function for consistency)
    expected_result_sim = simulate_query_duckdb(correct_answer_example, original_tables_dict)

    return feedback_llm, is_correct_llm, expected_result_sim, actual_result_sim, llm_output

# --- Remaining Helper Functions (calculate_score, analyze_performance, get_emoji, display_simulation) ---
# Keep these functions exactly as they were in your original code.
# ... (calculate_score) ...
def calculate_score(user_answers):
    """Calculate the score based on correct answers."""
    if not user_answers: return 0
    correct = sum(1 for ans in user_answers if ans.get("is_correct", False))
    total = len(user_answers)
    return (correct / total) * 100 if total > 0 else 0

# ... (analyze_performance - Minor prompt tweak to mention quote flexibility if needed) ...
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

        incorrect_summary = ""
        if incorrect_ans:
            incorrect_summary = "In sawaalon mein thodi galti hui:\n"
            for idx, item in enumerate(incorrect_ans):
                incorrect_summary += f"  {idx+1}. Sawaal: {item['question']}\n     Aapka Jawaab: `{item['your_answer']}`\n     Feedback Mila: {item['feedback_received'][:150]}...\n" # Limit feedback length
            incorrect_summary = incorrect_summary.strip()
        else:
            incorrect_summary = "Koi galat jawaab nahi! Bahut badhiya!"

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

        **Quiz Context Reminder:**
        - Case-insensitivity was assumed for '=' comparisons on 'status' and 'city' columns.
        - Both single (') and double (") quotes were acceptable for string literals in this quiz.

        **Task:**
        Ab, neeche diye gaye structure mein overall performance ka ek summary feedback do:
        1.  **Overall Impression:** Score aur general performance pe ek positive ya encouraging comment (e.g., "Overall performance kaafi achhi rahi!", "Thodi aur practice lagegi, but potential hai!").
        2.  **Strengths:** Agar kuch specific concepts sahi kiye hain (jo correct answers se pata chale), unko highlight karo (e.g., "SELECT aur WHERE clause ka use aache se samajh aa gaya hai.", "JOINs wale sawaal sahi kiye, yeh achhi baat hai!"). General rakho agar specific pattern na dikhe.
        3.  **Areas for Improvement:** Jo concepts galat hue (incorrect answers se related), unko gently point out karo. Focus on concepts, not just specific mistakes (e.g., "JOIN ka logic thoda aur clear karna hoga shayad.", "Aggregate functions (COUNT, AVG) pe dhyaan dena.", "Syntax ki chhoti-moti galtiyan ho rahi hain."). Specific examples quote mat karo, general areas batao. Remind them gently about standard practices (like single quotes for strings) if needed, but don't frame it as an error *in this quiz*.
        4.  **Next Steps / Encouragement:** Kuch encouraging words aur aage kya karna chahiye (e.g., "Keep practicing!", "Concept X ko revise kar lena.", "Aise hi lage raho, SQL aa jayega! Standard SQL practices (jaise single quotes) seekhte raho real-world ke liye.").

        Bas plain text mein feedback generate karna hai. Casual tone rakhna.
        """
    except Exception as data_prep_error:
        print(f"Error preparing data for analysis: {data_prep_error}")
        performance_data["overall_feedback"] = f"Analysis data preparation failed: {data_prep_error}"; return performance_data

    try:
        response = model.generate_content(prompt); generated_feedback = None
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

# ... (get_emoji) ...
def get_emoji(is_correct):
    return "✅" if is_correct else "❌"

# ... (display_simulation) ...
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
        # Display the error message from simulate_query_duckdb directly
        st.warning(result_data, icon="⚠️") # Changed to warning for simulation errors
    elif result_data == "N/A":
        st.info("_(Simulation not applicable or not run)_")
    elif isinstance(result_data, str): # Catch other string messages if any
         st.info(f"_{result_data}_")
    else:
        # Fallback for unexpected types
        st.error(f"_(Unexpected simulation result type: {type(result_data)})_")
        print(f"DEBUG: Unexpected simulation data type: {type(result_data)}, value: {result_data}")


# --- Streamlit App UI ---
# Keep the UI code exactly as it was in your original code.
# The changes are internal to the helper functions.

# --- Start Screen ---
if not st.session_state.quiz_started:
    st.title("🚀 SQL Mentor - Interactive SQL Practice")
    st.markdown("### Apne SQL Skills Ko Test Aur Improve Karein!")
    st.markdown("""
        **📌 Important Notes:**
        - This quiz uses standard **SQL syntax** (similar to MySQL/PostgreSQL).
        - String comparisons (like `WHERE city = 'new york'` or `WHERE status = "pending"`) are simulated to be **case-insensitive** for common text columns (`status`, `city`). **Both single (') and double (") quotes are accepted for strings in this simulation.**
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
        - String literals can be enclosed in single quotes (`'...'`) or double quotes (`"..."`).
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
                feedback_text = ans_data.get("feedback", "_Feedback not available._")
                # Use markdown to render potential formatting from LLM
                st.markdown(feedback_text)

                # --- Simulation Results for Previous Question ---
                st.markdown("---") # Separator inside expander
                display_simulation("Simulated Result (Your Query Output)", ans_data.get("actual_result", "N/A"))
                # Only show expected if it's different or if the answer was incorrect
                if not is_correct or not (isinstance(ans_data.get("actual_result"), pd.DataFrame) and isinstance(ans_data.get("expected_result"), pd.DataFrame) and ans_data["actual_result"].equals(ans_data["expected_result"])):
                     display_simulation("Simulated Result (Correct Query Output)", ans_data.get("expected_result", "N/A"))

    st.markdown("---")

    # --- Current Question ---
    current_q_index = st.session_state.current_question
    question_data = sql_questions[current_q_index]

    st.subheader(f"Sawaal {current_q_index + 1} of {len(sql_questions)}")
    st.markdown(f"**{question_data['question']}**")

    # Display relevant schemas
    relevant_tables = question_data["relevant_tables"]
    if relevant_tables:
        st.markdown("**Relevant Table Schema(s):**")
        schema_cols = st.columns(len(relevant_tables))
        for i, table_name in enumerate(relevant_tables):
            cols = get_table_schema(table_name, original_tables)
            if cols:
                 with schema_cols[i]:
                     st.code(f"Table: {table_name}\nColumns: {', '.join(cols)}", language='text')
            else:
                 with schema_cols[i]:
                     st.warning(f"Schema for '{table_name}' not found.")
    else:
         st.info("No specific table context provided for this question.")

    user_query = st.text_area("Apna SQL Query Yahan Likhein:", height=150, key=f"query_input_{current_q_index}")

    # Submit Button Logic
    if st.button("✅ Submit Query", key=f"submit_{current_q_index}"):
        if user_query.strip():
            with st.spinner("🔄 Query ko check kiya ja raha hai... AI Mentor se feedback aur simulation results generate ho rahe hain..."):
                # Evaluate Answer
                feedback, is_correct, expected_res, actual_res, raw_llm = evaluate_answer_with_llm(
                    question_data,
                    user_query,
                    original_tables # Pass the original tables
                )

                # Store result
                st.session_state.user_answers.append({
                    "question_number": current_q_index + 1,
                    "question": question_data["question"],
                    "student_answer": user_query,
                    "feedback": feedback,
                    "is_correct": is_correct,
                    "expected_result": expected_res,
                    "actual_result": actual_res,
                    "raw_llm_output": raw_llm # Store for debugging if needed
                })

                # Move to next question or finish quiz
                if current_q_index + 1 < len(sql_questions):
                    st.session_state.current_question += 1
                else:
                    st.session_state.quiz_completed = True

                st.rerun() # Rerun to display updated previous answers and the next question/results screen
        else:
            st.warning("⚠️ Please enter your SQL query before submitting.")


# --- Quiz Completed Screen ---
elif st.session_state.quiz_completed:
    st.balloons()
    st.title("🎉 Badhai Ho! Aapne SQL Challenge Poora Kar Liya!")
    final_score = calculate_score(st.session_state.user_answers)
    st.metric("Aapka Final Score:", f"{final_score:.2f}%")

    st.markdown("---")
    st.subheader("📝 Aapke Jawaab Aur Feedback Ka Summary")

    # Display all answers and feedback from the completed quiz
    for i, ans_data in enumerate(st.session_state.user_answers):
        q_num = i + 1
        is_correct = ans_data.get('is_correct', False)
        with st.expander(f"Question {q_num}: {ans_data['question']} {get_emoji(is_correct)}", expanded=False): # Start collapsed
            st.write(f"**Aapka Jawaab:**"); st.code(ans_data.get('student_answer', '(No answer provided)'), language='sql');
            st.write(f"**SQL Mentor Feedback:**");
            feedback_text = ans_data.get("feedback", "_Feedback not available._")
            st.markdown(feedback_text) # Use markdown for better rendering
            st.markdown("---") # Separator inside expander
            display_simulation("Simulated Result (Your Query Output)", ans_data.get("actual_result", "N/A"))
            # Only show expected if needed
            if not is_correct or not (isinstance(ans_data.get("actual_result"), pd.DataFrame) and isinstance(ans_data.get("expected_result"), pd.DataFrame) and ans_data["actual_result"].equals(ans_data["expected_result"])):
                 display_simulation("Simulated Result (Correct Query Output)", ans_data.get("expected_result", "N/A"))


    st.markdown("---")
    st.subheader("💡 AI Mentor Se Detailed Performance Analysis")

    # Toggle button for showing detailed feedback
    if st.button("Show Detailed Analysis", key="show_analysis"):
        st.session_state.show_detailed_feedback = not st.session_state.show_detailed_feedback # Toggle visibility

    if st.session_state.show_detailed_feedback:
        with st.spinner("🧠 Performance analysis generate ho raha hai..."):
            performance_summary = analyze_performance(st.session_state.user_answers)
            st.markdown(performance_summary.get("overall_feedback", "Analysis available nahi hai."))
            # Optionally display strengths/weaknesses lists if needed
            # st.write("Strengths identified in questions about:", performance_summary.get("strengths"))
            # st.write("Areas for improvement based on questions about:", performance_summary.get("weaknesses"))


    st.markdown("---")
    if st.button("🔄 Dobara Try Karein?"):
        # Reset state for a new quiz attempt
        st.session_state.user_answers = []
        st.session_state.current_question = 0
        st.session_state.quiz_started = False # Go back to start screen
        st.session_state.quiz_completed = False
        st.session_state.show_detailed_feedback = False
        st.rerun()

# --- Fallback (Should not be reached in normal flow) ---
else:
    st.error("🚨 Kuch unexpected hua hai. Application ko restart karein.")
    # You might want to add a button here to reset state as well
    if st.button("Reset App State"):
         # Clear all session state keys related to the quiz
         for key in list(st.session_state.keys()):
              if key in ["user_answers", "current_question", "quiz_started", "quiz_completed", "show_detailed_feedback"]:
                   del st.session_state[key]
         st.rerun()
