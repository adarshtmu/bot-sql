import streamlit as st
import google.generativeai as genai
import pandas as pd
import re # Needed for regex query modification
import duckdb # Import DuckDB
# import copy # No longer needed as we don't modify data copies this way

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
    Simulates an SQL query using DuckDB on in-memory pandas DataFrames,
    attempting case-insensitive comparison for specific columns by rewriting
    '=' to 'ILIKE' before execution.
    """
    if not sql_query or not sql_query.strip():
        return "Simulation Error: No query provided."
    if not tables_dict:
        return "Simulation Error: No tables provided for context."

    con = None
    modified_sql_query = sql_query # Start with the original query
    # Define columns for which '=' should be treated as case-insensitive (ILIKE)
    # Add more columns as needed: e.g., "users": ["name", "email", "city"]
    case_insensitive_columns = {
        "orders": ["status"],
        "users": ["city"]
    }
    # Flatten the list of column names for easier regex matching
    flat_insensitive_columns = [col for cols in case_insensitive_columns.values() for col in cols]

    try:
        # --- Query Modification Attempt (using ILIKE) ---
        if flat_insensitive_columns: # Only attempt if there are columns to modify
            try:
                # Regex pattern: finds patterns like `col_name = 'value'` or `col_name='value'` etc.
                # where col_name is one of our target columns. Handles spaces and single/double quotes.
                # It captures the part before the operator, the operator itself (=), and the literal.
                # Using word boundaries (\b) around column names to avoid matching substrings.
                col_pattern_part = "|".join([r"\b" + re.escape(col) + r"\b" for col in flat_insensitive_columns])
                # Updated pattern to capture pre-column context (like table alias), column name, operator, and literal
                # Pattern Breakdown:
                # (.*?)                     # Capture group 1: Anything before the column name (non-greedy)
                # (\b(?:{col_pattern_part})\b) # Capture group 2: The specific column name (e.g., status, city) with word boundaries
                # (\s*=\s*)                 # Capture group 3: The equals sign, potentially surrounded by spaces
                # ('[^']+'|\"[^\"]+\")       # Capture group 4: The string literal in single or double quotes
                pattern = rf"(.*?)({col_pattern_part})(\s*=\s*)('[^']+'|\"[^\"]+\")"

                def replace_with_ilike(match):
                    # Reconstruct the matched string replacing '=' with ' ILIKE '
                    # Ensure spaces around ILIKE for valid syntax
                    pre_context = match.group(1)
                    col_name = match.group(2)
                    operator = match.group(3)
                    literal = match.group(4)
                    print(f"Rewriting query part: Replacing '=' with 'ILIKE' for column '{col_name}'")
                    # Add space before ILIKE if pre_context doesn't end with space
                    space_prefix = "" if pre_context.endswith(" ") else " "
                    return f"{pre_context}{space_prefix}{col_name} ILIKE {literal}" # Replace = with ILIKE

                # Apply the replacement using re.sub with IGNORECASE flag
                modified_sql_query = re.sub(pattern, replace_with_ilike, sql_query, flags=re.IGNORECASE)

                if modified_sql_query != sql_query:
                     print(f"Original query: {sql_query}")
                     print(f"Modified query for simulation: {modified_sql_query}")

            except Exception as e_rewrite:
                print(f"Warning: Failed to rewrite query for case-insensitivity, using original. Error: {e_rewrite}")
                modified_sql_query = sql_query # Fallback to original if rewrite fails

        # --- Connect and Register ORIGINAL Data ---
        con = duckdb.connect(database=':memory:', read_only=False)
        for table_name, df in tables_dict.items():
             if isinstance(df, pd.DataFrame):
                 # Register the original DataFrame
                 con.register(str(table_name), df)
             else:
                 # This condition should ideally not be hit if input is validated
                 print(f"Warning [simulate_query]: Item '{table_name}' not a DataFrame during registration.")

        # Execute the potentially modified query (using ILIKE) against the ORIGINAL data
        result_df = con.execute(modified_sql_query).df()
        con.close()
        return result_df

    except Exception as e:
        error_message = f"Simulation Error: Failed to execute query. Reason: {str(e)}"
        # Add specific hint for ILIKE related errors if they occur
        if "ILIKE" in str(e).upper() or (modified_sql_query != sql_query and "syntax error" in str(e).lower()):
             error_message += "\n\n**Hint:** The simulation tried using case-insensitive matching (ILIKE). Check your SQL syntax near the comparison, especially if using complex conditions."
        else:
            # Your existing hint generation logic
            try:
                e_str = str(e).lower()
                # Enhanced error parsing for common DuckDB errors
                catalog_match = re.search(r'catalog error:.*table with name "([^"]+)" does not exist', e_str)
                binder_match = re.search(r'(?:binder error|catalog error):.*column "([^"]+)" not found', e_str)
                syntax_match = re.search(r'parser error: syntax error at or near "([^"]+)"', e_str) # DuckDB Parser error format
                type_match = re.search(r'conversion error:.*try cast\("([^"]+)"', e_str) # Type mismatch errors

                if catalog_match: error_message += f"\n\n**Hint:** Table '{catalog_match.group(1)}' might be misspelled or doesn't exist. Available tables: {list(tables_dict.keys())}."
                elif binder_match: error_message += f"\n\n**Hint:** Column '{binder_match.group(1)}' might be misspelled or doesn't exist in the referenced table(s)."
                elif syntax_match: error_message += f"\n\n**Hint:** Check your SQL syntax, especially around `{syntax_match.group(1)}`. Remember to use single quotes (') for text values like `'example text'`."
                elif type_match: error_message += f"\n\n**Hint:** There might be a type mismatch. You tried using '{type_match.group(1)}' in a way that's incompatible with its data type (e.g., comparing text to a number)."
                # Generic hint for unparsed errors
                elif not any([catalog_match, binder_match, syntax_match, type_match]): error_message += "\n\n**Hint:** Double-check your syntax, table/column names, and use single quotes (') for string values."

            except Exception as e_hint: print(f"Error generating hint: {e_hint}")

        print(f"ERROR [simulate_query_duckdb]: {error_message}\nOriginal Query: {sql_query}\nAttempted Query: {modified_sql_query}")
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

# Keep all other imports and functions the same as the previous complete code block
# ... (imports: streamlit, genai, pandas, re, duckdb) ...
# ... (CSS, API Key setup, Sample Data, SQL Questions List, Session State) ...
# ... (simulate_query_duckdb - use the one from the previous answer with ILIKE rewrite) ...
# ... (get_table_schema) ...

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

    # ***** MODIFIED PROMPT START *****
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

    * **Validity:** Is the query syntactically valid SQL? Briefly mention any syntax errors unrelated to the case-insensitivity rule above.
    * **Logic:** Does the query use appropriate SQL clauses (SELECT, FROM, WHERE, JOIN, GROUP BY, ORDER BY, aggregates, etc.) correctly for the task? Is the logic sound? Are comparisons appropriate for the data types (keeping the case-insensitivity rule for `status`/`city` in mind)?
    * **Alternatives:** Briefly acknowledge if the student used a valid alternative approach (e.g., different JOIN type if appropriate, subquery vs. JOIN). Mentioning `LOWER`/`UPPER` as a *generally good practice* is okay, but don't imply it was *required* for correctness *here*.
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
    actual_result_sim = simulate_query_duckdb(student_answer, original_tables_dict)
    # Simulate correct query (using the modified function for consistency)
    expected_result_sim = simulate_query_duckdb(correct_answer_example, original_tables_dict)

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

    st.markdown("---") # Separator before the current question

    # --- Current Question ---
    current_q_index = st.session_state.current_question
    if current_q_index < len(sql_questions):
        question_data = sql_questions[current_q_index]
        st.subheader(f"Question {current_q_index + 1} / {len(sql_questions)}")
        st.markdown(f"**{question_data['question']}**")
        st.write("****"); # Visual separator

        # Display relevant table previews for the current question
        rel_tables = question_data.get("relevant_tables", []);
        if rel_tables:
            tabs = st.tabs([f"{name.capitalize()} Table Preview" for name in rel_tables]);
            for i, table_name in enumerate(rel_tables):
                with tabs[i]:
                    if table_name in original_tables:
                        st.dataframe(original_tables[table_name], hide_index=True, use_container_width=True)
                    else: st.warning(f"Schema/Preview error for table '{table_name}'.")
        else: st.info("No specific tables linked for preview for this question.")

        # User input area
        student_answer = st.text_area("Apna SQL Query Yahaan Likhein:", key=f"answer_{current_q_index}", height=150, placeholder="SELECT column_name FROM table_name WHERE condition;")

        # Submit button
        if st.button("✅ Submit Answer", key=f"submit_{current_q_index}"):
            if student_answer.strip():
                with st.spinner("AI Mentor aapka jawaab check kar raha hai... Intezaar kijiye..."):
                    try:
                        feedback, is_correct, expected_sim, actual_sim, llm_raw = evaluate_answer_with_llm(question_data, student_answer, original_tables)
                        st.session_state.user_answers.append({
                            "question": question_data["question"],
                            "student_answer": student_answer,
                            "feedback": feedback,
                            "is_correct": is_correct,
                            "expected_result": expected_sim,
                            "actual_result": actual_sim,
                            "llm_raw_output": llm_raw # Store raw LLM output for debugging if needed
                        })
                    except Exception as eval_error:
                         st.error(f"Evaluation failed: {eval_error}")
                         # Append error state to answers
                         st.session_state.user_answers.append({
                            "question": question_data["question"],
                            "student_answer": student_answer,
                            "feedback": f"Error during evaluation: {eval_error}",
                            "is_correct": False,
                            "expected_result": "N/A",
                            "actual_result": "N/A",
                            "llm_raw_output": f"Error: {eval_error}"
                         })

                # Move to next question or complete quiz
                if current_q_index < len(sql_questions) - 1:
                    st.session_state.current_question += 1
                else:
                    st.session_state.quiz_completed = True
                st.rerun() # Rerun to display updated feedback/next question
            else:
                st.warning("Please enter your SQL query before submitting.")

        # Progress bar
        progress = (current_q_index) / len(sql_questions) # Progress before submitting current question
        st.progress(progress)
        st.caption(f"Question {current_q_index + 1} of {len(sql_questions)}")
    else:
        # Should not happen in normal flow, but handle state error
        st.warning("Reached end of questions unexpectedly or quiz state error.")
        st.session_state.quiz_completed = True; st.rerun()

# --- Quiz Completed Screen ---
elif st.session_state.quiz_completed:
    st.balloons(); st.title("🎉 Quiz Complete!")
    score = calculate_score(st.session_state.user_answers)
    st.metric(label="Your Final Score", value=f"{score:.2f}%")

    st.subheader("📝 Final Review: Aapke Jawaab Aur Feedback")
    for i, ans_data in enumerate(st.session_state.user_answers):
         is_correct = ans_data.get('is_correct', False)
         with st.expander(f"Question {i + 1}: {ans_data['question']} {get_emoji(is_correct)}", expanded=False):
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

                # --- Optional: Show Raw LLM Output for Debugging ---
                # with st.popover("Debug: Raw AI Output"):
                #    st.text_area("LLM Raw Response", ans_data.get('llm_raw_output', 'N/A'), height=150, disabled=True)

    st.markdown("---")

    # --- Call to Action Buttons ---
    col_cta_1, col_cta_2 = st.columns(2)
    with col_cta_1:
        # Toggle button for detailed feedback
        button_text = "📊 Hide Detailed Analysis" if st.session_state.show_detailed_feedback else "📊 Show Detailed Analysis"
        if st.button(button_text):
             st.session_state.show_detailed_feedback = not st.session_state.show_detailed_feedback; st.rerun()
    with col_cta_2:
        # Conditional Link Button based on score
        if score < 60:
            st.error("Score thoda kam hai... Aur practice kijiye!")
            st.link_button("Need Help? Connect with a Mentor", "https://www.corporatebhaiya.com/", use_container_width=True)
        else:
            st.success("Bahut badhiya score! 👍 Keep it up!")
            st.link_button("Next Steps? Mock Interview Practice", "https://www.corporatebhaiya.com/mock-interview", use_container_width=True)


    # --- Detailed Feedback Section (Conditional Display) ---
    if st.session_state.show_detailed_feedback:
        st.markdown("---"); st.subheader("📈 Detailed Performance Analysis (AI Generated)")
        with st.spinner("AI performance summary generate kar raha hai..."):
            performance_feedback = analyze_performance(st.session_state.user_answers)

        st.write("**Overall AI Mentor Feedback:**"); st.info(performance_feedback.get("overall_feedback", "Summary not available."))

        st.write("**Strengths (Questions answered correctly):**");
        strengths = performance_feedback.get("strengths", []);
        if strengths:
            for i, q in enumerate(strengths): st.success(f"{i + 1}. {q} ✅")
        else: st.write("_(No questions were answered correctly this time.)_")

        st.write("**Areas for Improvement (Based on incorrect answers):**");
        weaknesses = performance_feedback.get("weaknesses", []);
        if weaknesses:
            for i, q in enumerate(weaknesses): st.error(f"{i + 1}. {q} ❌")
        else: st.write("_(Great job! No incorrect answers!)_")

    st.markdown("---")
    # --- Restart Button ---
    if st.button("🔄 Restart Quiz"):
        # Clear specific session state keys related to the quiz progress
        keys_to_reset = ["user_answers", "current_question", "quiz_started","quiz_completed", "show_detailed_feedback"]
        for key in keys_to_reset:
            if key in st.session_state: del st.session_state[key]
        # Explicitly set starting state (optional but good practice)
        st.session_state.current_question = 0; st.session_state.quiz_started = False;
        st.rerun() # Rerun to go back to the start screen

# Fallback if state is somehow invalid (e.g., started=True, completed=True but current_question exists)
else:
    st.error("An unexpected error occurred with the application state. Please restart.")
    if st.button("Force Restart App State"):
        keys_to_reset = list(st.session_state.keys()) # Get all keys
        for key in keys_to_reset:
            del st.session_state[key] # Clear everything
        st.rerun()
