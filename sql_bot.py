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
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Set up Gemini API ---
# WARNING: Hardcoding API keys is insecure.
# For production, use Streamlit Secrets or environment variables.
# Replace "YOUR_API_KEY_HERE" with your actual Gemini API Key below.
gemini_api_key = "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k" # Your specific API Key
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
    { "question": "Write a SQL query to count how many orders each user has placed using a LEFT JOIN between 'users' and 'orders'. Include users with zero orders.", "correct_answer_example": "SELECT u.name, COUNT(o.order_id) AS order_count FROM users u LEFT JOIN orders o ON u.user_id = o.user_id GROUP BY u.name ORDER BY u.name;", "sample_table": users_table, "relevant_tables": ["users", "orders"] }
]

# --- Session State Initialization ---
# Using Streamlit's session state to keep track of the quiz progress and user answers
# across reruns.
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
             # Print to console/terminal for debugging
             print(f"DEBUG: Original query: {sql_query}")
             print(f"DEBUG: Query after double->single quote conversion: {processed_query_for_ilike}")
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
    # Flatten the list for easier regex matching
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
            # Use re.IGNORECASE for the column name matching itself
            pattern = rf"(.*?)({col_pattern_part})(\s*=\s*)('[^']+')"

            def replace_with_ilike(match):
                """Internal function to replace = with ILIKE"""
                pre_context = match.group(1)
                col_name = match.group(2)
                # operator = match.group(3) # We know this is '='
                literal = match.group(4) # The single-quoted literal
                print(f"DEBUG: Rewriting query part: Replacing '=' with 'ILIKE' for column '{col_name}'")
                # Add space before ILIKE if needed for valid syntax
                space_prefix = "" if not pre_context or pre_context.endswith(" ") or pre_context.endswith("(") else " "
                return f"{pre_context}{space_prefix}{col_name} ILIKE {literal}" # Replace = with ILIKE

            # Apply the replacement using re.sub with IGNORECASE flag for the pattern matching itself
            modified_sql_query = re.sub(pattern, replace_with_ilike, processed_query_for_ilike, flags=re.IGNORECASE)
            final_executed_query = modified_sql_query # Update the query to be executed

            if modified_sql_query != processed_query_for_ilike:
                  # Only print if ILIKE rewrite happened
                  print(f"DEBUG: Query after ILIKE rewrite: {modified_sql_query}")

        except Exception as e_rewrite:
            print(f"Warning: Failed to rewrite query for case-insensitivity (ILIKE), using quote-converted query. Error: {e_rewrite}")
            # Fallback to the query after quote conversion if ILIKE rewrite fails
            final_executed_query = processed_query_for_ilike

    # --- Step 3: Connect and Execute with DuckDB ---
    try:
        # Connect to an in-memory DuckDB database
        con = duckdb.connect(database=':memory:', read_only=False)
        # Register pandas DataFrames as virtual tables in DuckDB
        for table_name, df in tables_dict.items():
            if isinstance(df, pd.DataFrame):
                con.register(str(table_name), df) # Register the DataFrame
            else:
                 # This condition should ideally not be hit if input is validated
                 print(f"Warning [simulate_query]: Item '{table_name}' not a DataFrame during registration.")

        # Execute the final query (potentially modified for quotes and ILIKE)
        print(f"DEBUG: Executing final query in DuckDB: {final_executed_query}")
        result_df = con.execute(final_executed_query).df() # Execute and fetch results as DataFrame
        con.close() # Close the database connection
        return result_df # Return the resulting DataFrame

    except Exception as e:
        # Handle potential errors during DuckDB execution
        error_message = f"Simulation Error: Failed to execute query. Reason: {str(e)}"
        e_str = str(e).lower() # Lowercase error message for easier matching
        hint = "" # Initialize hint message

        # Check if the error might be related to the ILIKE rewrite attempt
        if "ILIKE" in str(e).upper() or (modified_sql_query != processed_query_for_ilike and "syntax error" in e_str):
            hint = "\n\n**Hint:** The simulation tried using case-insensitive matching (ILIKE). Check your SQL syntax near the comparison, especially if using complex conditions."
        else:
            # Provide more specific hints based on common DuckDB error messages
            catalog_match = re.search(r'catalog error:.*table with name "([^"]+)" does not exist', e_str)
            binder_match = re.search(r'(?:binder error|catalog error):.*column "([^"]+)" not found', e_str)
            # DuckDB Parser error format can vary slightly
            syntax_match = re.search(r'parser error: syntax error at or near "([^"]+)"', e_str) \
                        or re.search(r'parser error: syntax error at end of input', e_str) \
                        or re.search(r'parser error: syntax error at:', e_str) # More general catch
            type_match = re.search(r'conversion error:.*try cast\("([^"]+)"', e_str) # Type mismatch errors

            # Construct hint based on matched error pattern
            if catalog_match: hint = f"\n\n**Hint:** Table '{catalog_match.group(1)}' might be misspelled or doesn't exist. Available tables: {list(tables_dict.keys())}."
            elif binder_match: hint = f"\n\n**Hint:** Column '{binder_match.group(1)}' might be misspelled or doesn't exist in the referenced table(s)."
            elif syntax_match:
                # Extract the problematic part if possible, otherwise provide general syntax hint
                problem_area = syntax_match.group(1) if syntax_match.groups() and syntax_match.lastindex == 1 else "the location indicated"
                hint = f"\n\n**Hint:** Check your SQL syntax, especially around `{problem_area}`. Remember standard SQL uses single quotes (') for text values like `'example text'` (though the tool tries to handle double quotes for you)."
            elif type_match: hint = f"\n\n**Hint:** There might be a type mismatch. You tried using '{type_match.group(1)}' in a way that's incompatible with its data type (e.g., comparing text to a number)."
            elif "syntax error" in e_str: # Generic syntax hint if specific pattern not matched but error contains "syntax error"
                 hint = "\n\n**Hint:** Double-check your SQL syntax. Ensure all clauses (SELECT, FROM, WHERE, etc.) are correct and in order. Use single quotes (') for string values."

        if not hint: # Fallback generic hint if no specific pattern was matched
             hint = "\n\n**Hint:** Double-check your query syntax, table/column names, and data types. Ensure string values are correctly quoted (standard SQL uses single quotes '). Verify function names and usage."

        error_message += hint # Append the generated hint to the error message

        # Print detailed error info to the console for debugging
        print(f"ERROR [simulate_query_duckdb]: {error_message}\nOriginal Query: {sql_query}\nFinal Attempted Query: {final_executed_query}")
        if con: # Ensure connection is closed even if error occurred after opening
            try: con.close()
            except: pass # Ignore errors during close after another error
        return error_message # Return the error string

# ******************************************************************************
# ***** MODIFIED simulate_query_duckdb function ends here *****
# ******************************************************************************


def get_table_schema(table_name, tables_dict):
    """Gets column names as a list for a given table name from the tables dictionary."""
    if table_name in tables_dict and isinstance(tables_dict[table_name], pd.DataFrame):
        return tables_dict[table_name].columns.astype(str).tolist()
    return [] # Return empty list if table not found or not a DataFrame

def evaluate_answer_with_llm(question_data, student_answer, original_tables_dict):
    """
    Evaluates the user's SQL query using the Gemini API for feedback and correctness,
    and also simulates the query using DuckDB.
    """
    if not student_answer or not student_answer.strip():
        # Handle empty input without calling API or simulation
        return "Please provide an answer.", False, "N/A", "N/A", "No input."

    question = question_data["question"]
    relevant_table_names = question_data["relevant_tables"]
    correct_answer_example = question_data["correct_answer_example"]

    # Prepare schema information string for the prompt
    schema_info = ""
    if not relevant_table_names:
        schema_info = "No specific table schema context provided for this question.\n"
    else:
        for name in relevant_table_names:
            columns = get_table_schema(name, original_tables_dict)
            if columns:
                try:
                    # Include column names and data types in the schema info
                    df = original_tables_dict[name]
                    dtypes_str = df.dtypes.to_string() if isinstance(df, pd.DataFrame) else "N/A"
                    schema_info += f"Table '{name}':\n  Columns: {columns}\n  DataTypes:\n{dtypes_str}\n\n"
                except Exception as e_schema:
                    schema_info += f"Table '{name}': Columns {columns} (Error getting schema details: {e_schema})\n\n"
            else:
                schema_info += f"Table '{name}': Schema information not found.\n"

    # Construct the prompt for the Gemini API
    # The prompt asks the AI to act as a SQL mentor, evaluate correctness, validity, and logic,
    # provide feedback in Hindi, and consider the specific quiz rules (case-insensitivity, quote flexibility).
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

    # Initialize return variables
    feedback_llm = "AI feedback generation failed."; is_correct_llm = False; llm_output = "Error: No LLM response received."
    try:
        # Call the Gemini API
        response = model.generate_content(prompt)

        # --- Safely extract text from response ---
        extracted_text = None
        try:
            # Check common attributes/methods for accessing response text
            if hasattr(response, 'text'):
                extracted_text = response.text
            elif hasattr(response, 'parts') and response.parts:
                 # Handle potential multi-part responses
                 extracted_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
            else:
                 # Attempt to handle potential blocking/errors reported in response structure
                 try:
                     extracted_text = f"AI Response Blocked or Empty. Prompt Feedback: {response.prompt_feedback}"
                 except Exception:
                     extracted_text = "Error: Received unexpected or empty response structure from AI."

            if not extracted_text or not extracted_text.strip():
                 llm_output = "Error: Received empty response from AI."
                 # Keep default feedback/correctness values
            else:
                 llm_output = extracted_text.strip() # Store the raw stripped output

                 # --- Parse Verdict from LLM Output ---
                 # Look for "Verdict: Correct" or "Verdict: Incorrect" at the end of the response, case-insensitive
                 verdict_match = re.search(r'^Verdict:\s*(Correct|Incorrect)\s*$', llm_output, re.MULTILINE | re.IGNORECASE)
                 if verdict_match:
                     # Extract verdict and the feedback text preceding it
                     is_correct_llm = (verdict_match.group(1).lower() == "correct")
                     # Get feedback text before the verdict line
                     feedback_llm = llm_output[:verdict_match.start()].strip()
                     # Clean up any residual verdict lines just in case
                     feedback_llm = re.sub(r'\s*Verdict:\s*(Correct|Incorrect)?\s*$', '', feedback_llm, flags=re.MULTILINE | re.IGNORECASE).strip()
                 else:
                     # If verdict line is not found, report a warning and default to incorrect
                     st.warning(f"⚠️ Could not parse AI verdict from response.")
                     print(f"WARNING: Could not parse verdict from LLM output:\n---\n{llm_output}\n---")
                     feedback_llm = llm_output + "\n\n_(System Note: AI correctness check might be unreliable as verdict wasn't found.)_"
                     is_correct_llm = False # Default to incorrect if verdict unclear

                 # Replace "student" with "aap" for a more direct tone in Hindi feedback
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
        # Handle errors during the API call itself
        st.error(f"🚨 AI Error during evaluation: {e_call}")
        print(f"ERROR: Gemini API call failed: {e_call}")
        feedback_llm = f"AI feedback generation error: {e_call}"
        is_correct_llm = False
        llm_output = f"Error during AI call: {e_call}"

    # --- Simulate Queries using the modified function ---
    # Simulate the student's query (handles quotes and ILIKE)
    actual_result_sim = simulate_query_duckdb(student_answer, original_tables_dict)
    # Simulate the correct example query (using the same function for consistent behavior)
    expected_result_sim = simulate_query_duckdb(correct_answer_example, original_tables_dict)

    # Return all results
    return feedback_llm, is_correct_llm, expected_result_sim, actual_result_sim, llm_output


def calculate_score(user_answers):
    """Calculates the percentage score based on the list of user answers."""
    if not user_answers: return 0.0
    # Count answers marked as correct by the LLM
    correct_count = sum(1 for ans in user_answers if ans.get("is_correct", False))
    total_questions_answered = len(user_answers)
    # Calculate percentage
    score = (correct_count / total_questions_answered) * 100 if total_questions_answered > 0 else 0.0
    return score

def analyze_performance(user_answers):
    """
    Analyzes the user's overall performance using the Gemini API based on all answers.
    Provides strengths, weaknesses, and overall feedback.
    """
    performance_data = {
        "strengths": [],
        "weaknesses": [],
        "overall_feedback": "Performance analysis could not be completed."
    }
    if not user_answers:
        performance_data["overall_feedback"] = "Koi jawaab nahi diya gaya. Analysis possible nahi hai."
        return performance_data

    try:
        # Separate correct and incorrect answers/questions
        correct_q = [ans["question"] for ans in user_answers if ans.get("is_correct")]
        incorrect_ans = [
            {"question": ans["question"],
             "your_answer": ans["student_answer"],
             "feedback_received": ans.get("feedback", "N/A")
            } for ans in user_answers if not ans.get("is_correct")
        ]
        performance_data["strengths"] = correct_q # List of correctly answered questions
        performance_data["weaknesses"] = [item["question"] for item in incorrect_ans] # List of incorrectly answered questions
        total_q = len(user_answers)
        correct_c = len(correct_q)
        score = calculate_score(user_answers)

        # --- Prepare summaries for the analysis prompt ---
        incorrect_summary = ""
        if incorrect_ans:
            incorrect_summary = "In sawaalon mein thodi galti hui:\n"
            for idx, item in enumerate(incorrect_ans):
                # Limit length of feedback shown in summary to keep prompt concise
                feedback_snippet = item['feedback_received'][:150].strip() + ('...' if len(item['feedback_received']) > 150 else '')
                incorrect_summary += f"  {idx+1}. Sawaal: {item['question']}\n     Aapka Jawaab: `{item['your_answer']}`\n     Feedback Mila: {feedback_snippet}\n"
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

        # --- Construct the prompt for Gemini API performance analysis ---
        prompt = f"""
        Ek SQL learner ne ek practice quiz complete kiya hai. Unki performance ka analysis karke ek friendly, motivating summary feedback casual Hindi mein (jaise ek senior/mentor deta hai) provide karo.

        **Quiz Performance Summary:**
        - Total Questions Attempted: {total_q}
        - Correct Answers: {correct_c}
        - Final Score: {score:.2f}%

        **Correctly Answered Questions:**
        {correct_summary if correct_q else '(Koi nahi)'}

        **Incorrectly Answered Questions & Feedback Snippets:**
        {incorrect_summary if incorrect_ans else '(Koi nahi)'}

        **Quiz Context Reminder:**
        - Case-insensitivity was assumed for '=' comparisons on 'status' and 'city' columns.
        - Both single (') and double (") quotes were acceptable for string literals in this quiz simulation.

        **Task:**
        Ab, neeche diye gaye structure mein overall performance ka ek summary feedback do:
        1.  **Overall Impression:** Score aur general performance pe ek positive ya encouraging comment (e.g., "Overall performance kaafi achhi rahi!", "Thodi aur practice lagegi, but potential hai!"). Be realistic but motivating.
        2.  **Strengths:** Agar kuch specific concepts sahi kiye hain (jo correct answers se pata chale), unko highlight karo (e.g., "SELECT aur WHERE clause ka use aache se samajh aa gaya hai.", "JOINs wale sawaal sahi kiye, yeh achhi baat hai!"). General rakho agar specific pattern na dikhe.
        3.  **Areas for Improvement:** Jo concepts galat hue (incorrect answers se related), unko gently point out karo. Focus on concepts, not just specific mistakes (e.g., "JOIN ka logic thoda aur clear karna hoga shayad.", "Aggregate functions (COUNT, AVG) pe dhyaan dena.", "Syntax ki chhoti-moti galtiyan ho rahi hain."). Briefly mention standard practices (like single quotes for strings in real DBs) as a learning point, without implying it was wrong *in this quiz*.
        4.  **Next Steps / Encouragement:** Kuch encouraging words aur aage kya karna chahiye (e.g., "Keep practicing!", "Concept X ko revise kar lena.", "Aise hi lage raho, SQL aa jayega! Real-world ke liye standard SQL practices (jaise single quotes) seekhte rehna important hai.").

        Bas plain text mein feedback generate karna hai. Casual tone rakhna. Sidhe feedback se shuru karo.
        """
    except Exception as data_prep_error:
        print(f"Error preparing data for performance analysis: {data_prep_error}")
        performance_data["overall_feedback"] = f"Analysis data preparation failed: {data_prep_error}"
        return performance_data

    # --- Call Gemini API for the analysis ---
    try:
        response = model.generate_content(prompt)
        generated_feedback = None
        # Safely extract text from response (similar pattern as in evaluation)
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
    st.write(f"**{title}:**") # Display the title (e.g., "Your Query Output")
    if isinstance(result_data, pd.DataFrame):
        if result_data.empty:
            st.info("_(Simulation resulted in an empty table)_") # Message for empty results
        else:
            # Display the DataFrame, allow it to use container width
            st.dataframe(result_data.reset_index(drop=True), hide_index=True, use_container_width=True)
    elif isinstance(result_data, str) and "Simulation Error" in result_data:
        # Display simulation errors using Streamlit's warning box
        st.warning(result_data, icon="⚠️")
    elif result_data == "N/A":
        # Indicate when simulation wasn't applicable or run
        st.info("_(Simulation not applicable or not run)_")
    elif isinstance(result_data, str):
         # Display any other string messages (e.g., "No input")
         st.info(f"_{result_data}_")
    else:
        # Fallback for unexpected data types, show an error and log details
        st.error(f"_(Unexpected simulation result type: {type(result_data)})_")
        print(f"DEBUG: Unexpected simulation data type: {type(result_data)}, value: {result_data}")


# --- Streamlit App UI ---

# --- Start Screen ---
# Shown only if the quiz hasn't started yet.
if not st.session_state.quiz_started:
    st.title("🚀 SQL Mentor - Interactive SQL Practice")
    st.markdown("### Apne SQL Skills Ko Test Aur Improve Karein!")
    # Important notes about the quiz environment
    st.markdown("""
        **📌 Important Notes:**
        - This quiz uses standard **SQL syntax** (similar to MySQL/PostgreSQL).
        - String comparisons (like `WHERE city = 'new york'` or `WHERE status = "pending"`) are simulated to be **case-insensitive** for common text columns (`status`, `city`).
        - **Both single quotes (') and double quotes (") are accepted** for string literals in this simulation.
        - Your queries are evaluated by an AI for correctness and logic.
        - Query simulation is powered by DuckDB to show results on sample data.
        """)

    # Display overview and previews of the sample tables
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
            # Create a small DataFrame summarizing the tables
            table_overview_data = {"Table": list(original_tables.keys()),
                                   "Rows": [len(df) for df in original_tables.values()],
                                   "Columns": [len(df.columns) for df in original_tables.values()]}
            st.dataframe(pd.DataFrame(table_overview_data), hide_index=True)
        except Exception as e:
            st.error(f"Error displaying table overview: {e}")

    st.write("### 🔍 Table Previews")
    try:
        # Use tabs to show previews of the full tables
        tab1, tab2 = st.tabs(["Users Table", "Orders Table"])
        with tab1: st.dataframe(users_table, hide_index=True, use_container_width=True)
        with tab2: st.dataframe(orders_table, hide_index=True, use_container_width=True)
    except Exception as e:
         st.error(f"Error displaying table previews: {e}")

    # Expander with more quiz details
    with st.expander("📝 Quiz Ke Baare Mein"):
        st.write(f"""
        - Aapko {len(sql_questions)} SQL query challenges solve karne honge.
        - Har jawaab ke baad AI Mentor se immediate feedback milega.
        - **SQL Dialect Focus:** Standard SQL (MySQL/PostgreSQL like).
        - Case-insensitivity for `status` and `city` columns in `WHERE =` clauses is simulated.
        - String literals can be enclosed in single quotes (`'...'`) or double quotes (`"..."`).
        """)

    # Button to start the quiz
    if st.button("🚀 Start SQL Challenge!"):
        # Set session state flags to start the quiz and reset progress
        st.session_state.quiz_started = True
        st.session_state.user_answers = []
        st.session_state.current_question = 0
        st.session_state.quiz_completed = False
        st.session_state.show_detailed_feedback = False
        st.rerun() # Rerun the script to move to the quiz screen

# --- Quiz In Progress Screen ---
# Shown when the quiz has started but not yet completed.
elif st.session_state.quiz_started and not st.session_state.quiz_completed:
    st.title("✍️ SQL Query Challenge")

    # --- Display Previous Answers and Feedback ---
    # Show feedback for previously answered questions in reverse order (newest first)
    if st.session_state.user_answers:
        st.markdown("---")
        st.subheader("📖 Ab Tak Ke Jawaab Aur Feedback")
        # Loop through answers in reverse to show the latest first
        for i, ans_data in enumerate(reversed(st.session_state.user_answers)):
            q_num = len(st.session_state.user_answers) - i # Get original question number
            is_correct = ans_data.get('is_correct', False) # Check if marked correct
            # Use an expander for each previous question's details
            with st.expander(f"Question {q_num}: {ans_data['question']} {get_emoji(is_correct)}", expanded=False): # Start collapsed
                st.write(f"**Aapka Jawaab:**")
                st.code(ans_data.get('student_answer', '(No answer provided)'), language='sql')
                st.write(f"**SQL Mentor Feedback:**")
                feedback_text = ans_data.get("feedback", "_Feedback not available._")
                st.markdown(feedback_text) # Render feedback using markdown

                # --- Simulation Results for Previous Question ---
                st.markdown("---") # Separator inside the expander
                # Display the simulation result for the user's query
                display_simulation("Simulated Result (Your Query Output)", ans_data.get("actual_result", "N/A"))
                # Optionally, show the expected result if the answer was incorrect or if results differ
                # (Avoid showing identical expected result if answer was correct)
                show_expected = False
                if not is_correct:
                    show_expected = True
                elif isinstance(ans_data.get("actual_result"), pd.DataFrame) and \
                     isinstance(ans_data.get("expected_result"), pd.DataFrame) and \
                     not ans_data["actual_result"].equals(ans_data["expected_result"]):
                     show_expected = True
                elif isinstance(ans_data.get("actual_result"), str) and \
                     ans_data.get("actual_result") != ans_data.get("expected_result"):
                     show_expected = True


                if show_expected:
                     display_simulation("Simulated Result (Correct Query Output)", ans_data.get("expected_result", "N/A"))

    st.markdown("---") # Separator before the current question

    # --- Current Question ---
    current_q_index = st.session_state.current_question
    question_data = sql_questions[current_q_index] # Get data for the current question

    st.subheader(f"Sawaal {current_q_index + 1} of {len(sql_questions)}") # Display question number
    st.markdown(f"**{question_data['question']}**") # Display the question text

    # Display relevant schemas for the current question
    relevant_tables = question_data["relevant_tables"]
    if relevant_tables:
        st.markdown("**Relevant Table Schema(s):**")
        # Use columns for layout if multiple tables are relevant
        schema_cols = st.columns(len(relevant_tables))
        for i, table_name in enumerate(relevant_tables):
            cols = get_table_schema(table_name, original_tables) # Get column names
            if cols:
                 with schema_cols[i]: # Place schema in its column
                     # Display table name and columns using st.code
                     st.code(f"Table: {table_name}\nColumns: {', '.join(cols)}", language='text')
            else:
                 with schema_cols[i]:
                     st.warning(f"Schema for '{table_name}' not found.") # Show warning if schema missing
    else:
         st.info("No specific table context provided for this question.") # Message if no tables listed

    # Text area for user to input their SQL query
    # Using a unique key based on question index prevents input loss on reruns
    user_query = st.text_area("Apna SQL Query Yahan Likhein:", height=150, key=f"query_input_{current_q_index}")

    # Submit Button Logic
    if st.button("✅ Submit Query", key=f"submit_{current_q_index}"):
        if user_query and user_query.strip(): # Check if query is not empty
            # Show a spinner while processing the query
            with st.spinner("🔄 Query ko check kiya ja raha hai... AI Mentor se feedback aur simulation results generate ho rahe hain..."):
                # Call the evaluation function
                feedback, is_correct, expected_res, actual_res, raw_llm = evaluate_answer_with_llm(
                    question_data,
                    user_query,
                    original_tables # Pass the original tables dictionary for simulation context
                )

                # Store the results in session state
                st.session_state.user_answers.append({
                    "question_number": current_q_index + 1,
                    "question": question_data["question"],
                    "student_answer": user_query,
                    "feedback": feedback,
                    "is_correct": is_correct, # Store the LLM's verdict
                    "expected_result": expected_res, # Store simulation of correct query
                    "actual_result": actual_res, # Store simulation of user's query
                    "raw_llm_output": raw_llm # Store raw LLM output for debugging if needed
                })

                # Move to the next question or finish the quiz
                if current_q_index + 1 < len(sql_questions):
                    st.session_state.current_question += 1 # Increment question index
                else:
                    st.session_state.quiz_completed = True # Mark quiz as completed

                st.rerun() # Rerun to display the updated feedback/next question or completion screen
        else:
            st.warning("⚠️ Please enter your SQL query before submitting.") # Warning for empty submission


# --- Quiz Completed Screen ---
# Shown when all questions have been answered.
elif st.session_state.quiz_completed:
    st.balloons() # Fun celebration effect
    st.title("🎉 Badhai Ho! Aapne SQL Challenge Poora Kar Liya!")
    final_score = calculate_score(st.session_state.user_answers) # Calculate final score
    st.metric("Aapka Final Score:", f"{final_score:.2f}%") # Display score using st.metric

    st.markdown("---")
    st.subheader("📝 Aapke Jawaab Aur Feedback Ka Summary")

    # Display all answers and feedback again on the final screen for review
    for i, ans_data in enumerate(st.session_state.user_answers):
        q_num = i + 1
        is_correct = ans_data.get('is_correct', False)
        # Use expanders, initially collapsed, for each question's full details
        with st.expander(f"Question {q_num}: {ans_data['question']} {get_emoji(is_correct)}", expanded=False):
            st.write(f"**Aapka Jawaab:**")
            st.code(ans_data.get('student_answer', '(No answer provided)'), language='sql')
            st.write(f"**SQL Mentor Feedback:**")
            feedback_text = ans_data.get("feedback", "_Feedback not available._")
            st.markdown(feedback_text) # Render feedback using markdown
            st.markdown("---") # Separator inside expander
            # Display simulation results again
            display_simulation("Simulated Result (Your Query Output)", ans_data.get("actual_result", "N/A"))
            # Optionally show expected result if needed (same logic as on quiz screen)
            show_expected_final = False
            if not is_correct:
                show_expected_final = True
            elif isinstance(ans_data.get("actual_result"), pd.DataFrame) and \
                 isinstance(ans_data.get("expected_result"), pd.DataFrame) and \
                 not ans_data["actual_result"].equals(ans_data["expected_result"]):
                 show_expected_final = True
            elif isinstance(ans_data.get("actual_result"), str) and \
                 ans_data.get("actual_result") != ans_data.get("expected_result"):
                 show_expected_final = True

            if show_expected_final:
                 display_simulation("Simulated Result (Correct Query Output)", ans_data.get("expected_result", "N/A"))


    st.markdown("---")
    st.subheader("💡 AI Mentor Se Detailed Performance Analysis")

    # Toggle button for showing/hiding the detailed AI performance analysis
    if st.button("Show Detailed Analysis", key="show_analysis"):
        # Toggle the visibility state
        st.session_state.show_detailed_feedback = not st.session_state.show_detailed_feedback

    # If the toggle is True, generate and display the analysis
    if st.session_state.show_detailed_feedback:
        with st.spinner("🧠 Performance analysis generate ho raha hai..."):
            # Call the analysis function
            performance_summary = analyze_performance(st.session_state.user_answers)
            # Display the overall feedback from the analysis
            st.markdown(performance_summary.get("overall_feedback", "Analysis available nahi hai."))


    st.markdown("---")
    # Button to allow the user to restart the quiz
    if st.button("🔄 Dobara Try Karein?"):
        # Reset all relevant session state variables to their initial values
        st.session_state.user_answers = []
        st.session_state.current_question = 0
        st.session_state.quiz_started = False # Go back to start screen
        st.session_state.quiz_completed = False
        st.session_state.show_detailed_feedback = False
        st.rerun() # Rerun the script to show the start screen again

# --- Fallback (Should not normally be reached) ---
# Handles any unexpected state where the app is neither starting, in progress, nor completed.
else:
    st.error("🚨 Kuch unexpected state issue hai. Application ko restart karne ki koshish karein.")
    # Provide a button to manually reset the state as a recovery mechanism
    if st.button("Reset App State"):
         # Clear all session state keys used by the quiz
         for key in list(st.session_state.keys()):
              if key in ["user_answers", "current_question", "quiz_started", "quiz_completed", "show_detailed_feedback"]:
                   del st.session_state[key]
         st.rerun() # Rerun after clearing state
