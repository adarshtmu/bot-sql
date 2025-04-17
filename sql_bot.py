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
# WARNING: Hardcoding API keys is insecure. Consider environment variables or Streamlit secrets for deployment.
gemini_api_key = "YOUR_GEMINI_API_KEY" # <-- IMPORTANT: Replace with your actual key

if not gemini_api_key or gemini_api_key == "YOUR_GEMINI_API_KEY": # Basic check if the key is empty or default
    st.error("🚨 Gemini API Key is missing or is the default placeholder in the code. Please replace 'YOUR_GEMINI_API_KEY' with your actual key.")
    st.stop()

try:
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash') # Or your preferred model
except Exception as e:
    st.error(f"🚨 Failed to configure Gemini API or access the model: {e}")
    st.stop()


# --- Sample Data ---
# Keep original data for display
users_table_display = pd.DataFrame({
    "user_id": [1, 2, 3, 4],
    "name": ["Alice", "Bob", "Charlie", "David"],
    "email": ["alice@example.com", "bob@example.com", "charlie@example.com", "david@example.com"],
    "age": [25, 30, 35, 40],
    "city": ["New York", "Los Angeles", "Chicago", "Houston"]
})
orders_table_display = pd.DataFrame({
    "order_id": [101, 102, 103, 104, 105],
    "user_id": [1, 2, 3, 1, 4],
    "amount": [50.00, 75.50, 120.00, 200.00, 35.00],
    "order_date": pd.to_datetime(["2024-02-01", "2024-02-05", "2024-02-10", "2024-02-15", "2024-02-20"]),
    "status": ["Completed", "Pending", "Completed", "Shipped", "Cancelled"]
})

# Create copies for simulation with lowercase strings
users_table_sim = users_table_display.copy()
orders_table_sim = orders_table_display.copy()

# Convert relevant string columns to lowercase for simulation
for col in ["name", "email", "city"]:
    if col in users_table_sim.columns:
        users_table_sim[col] = users_table_sim[col].str.lower()
for col in ["status"]:
     if col in orders_table_sim.columns:
        orders_table_sim[col] = orders_table_sim[col].str.lower()

# Dictionary for simulation uses lowercase data
tables_for_simulation = {
    "users": users_table_sim,
    "orders": orders_table_sim
}

# Dictionary for display uses original data
original_tables_for_display = {
    "users": users_table_display,
    "orders": orders_table_display
}

# --- SQL Questions List ---
# Ensure examples use lowercase for string literals where comparisons happen,
# and sample_table uses the display version for context.
sql_questions = [
    { "question": "Write a SQL query to get all details about users from the 'users' table.", "correct_answer_example": "SELECT * FROM users;", "sample_table": users_table_display, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to count the total number of users in the 'users' table.", "correct_answer_example": "SELECT COUNT(*) AS user_count FROM users;", "sample_table": users_table_display, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to get all users older than 30 from the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE age > 30;", "sample_table": users_table_display, "relevant_tables": ["users"] },
    # --- UPDATED EXAMPLE QUERIES with lowercase strings for comparison ---
    { "question": "Write a SQL query to find all orders with a status of 'Pending' from the 'orders' table.", "correct_answer_example": "SELECT * FROM orders WHERE status = 'pending';", "sample_table": orders_table_display, "relevant_tables": ["orders"] },
    { "question": "Write a SQL query to find the most recent order from the 'orders' table by order date.", "correct_answer_example": "SELECT * FROM orders ORDER BY order_date DESC LIMIT 1;", "sample_table": orders_table_display, "relevant_tables": ["orders"] },
    { "question": "Write a SQL query to find the average order amount from the 'orders' table.", "correct_answer_example": "SELECT AVG(amount) AS average_amount FROM orders;", "sample_table": orders_table_display, "relevant_tables": ["orders"] },
    { "question": "Write a SQL query to find users from 'New York' or 'Chicago' in the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE city IN ('new york', 'chicago');", "sample_table": users_table_display, "relevant_tables": ["users"] },
    # --- JOIN examples focus on logic ---
    { "question": "Write a SQL query to find users who have not placed any orders. Use the 'users' and 'orders' tables.", "correct_answer_example": "SELECT u.* FROM users u LEFT JOIN orders o ON u.user_id = o.user_id WHERE o.order_id IS NULL;", "sample_table": users_table_display, "relevant_tables": ["users", "orders"] },
    { "question": "Write a SQL query to calculate the total amount spent by each user by joining the 'users' and 'orders' tables.", "correct_answer_example": "SELECT u.name, SUM(o.amount) AS total_spent FROM users u JOIN orders o ON u.user_id = o.user_id GROUP BY u.name ORDER BY u.name;", "sample_table": users_table_display, "relevant_tables": ["users", "orders"] },
    { "question": "Write a SQL query to count how many orders each user has placed using a LEFT JOIN between 'users' and 'orders'. Include users with zero orders.", "correct_answer_example": "SELECT u.name, COUNT(o.order_id) AS order_count FROM users u LEFT JOIN orders o ON u.user_id = o.user_id GROUP BY u.name ORDER BY u.name;", "sample_table": users_table_display, "relevant_tables": ["users", "orders"] }
]

# --- Session State Initialization ---
if "user_answers" not in st.session_state: st.session_state.user_answers = []
if "current_question" not in st.session_state: st.session_state.current_question = 0
if "quiz_started" not in st.session_state: st.session_state.quiz_started = False
if "quiz_completed" not in st.session_state: st.session_state.quiz_completed = False
if "show_detailed_feedback" not in st.session_state: st.session_state.show_detailed_feedback = False

# --- Helper Functions ---

def simulate_query_duckdb(sql_query, tables_dict_sim):
    """Simulates an SQL query using DuckDB on in-memory pandas DataFrames (using lowercase string data)."""
    if not sql_query or not sql_query.strip():
        return "Simulation Error: No query provided."
    if not tables_dict_sim:
        return "Simulation Error: No tables provided for context."
    con = None
    try:
        con = duckdb.connect(database=':memory:', read_only=False)
        # Register tables from the simulation dictionary
        for table_name, df in tables_dict_sim.items():
            if isinstance(df, pd.DataFrame):
                 con.register(str(table_name), df)
            else:
                 # This case should ideally not happen if setup is correct
                 print(f"Warning [simulate_query]: Item '{table_name}' not a DataFrame.")
                 return f"Simulation Error: Table '{table_name}' is not a valid DataFrame."

        result_df = con.execute(sql_query).df()
        con.close()
        return result_df
    except Exception as e:
        error_message = f"Simulation Error: Failed to execute query. Reason: {str(e)}"
        # Add hints for common errors like using double quotes for strings
        try:
            e_str = str(e).lower()
            # DuckDB error for invalid input syntax for type varchar often means wrong quotes
            if 'binder error' in e_str and 'referenced column' in e_str and 'not found' in e_str:
                 # Try to extract the problematic identifier if possible
                 match = re.search(r'column "([^"]+)" not found', e_str)
                 column_hint = f" `{match.group(1)}`" if match else ""
                 error_message += f"\n\n**Hint:** Check if column{column_hint} exists or if you used double quotes (\") for a string value instead of single quotes (')."
            elif 'parser error: syntax error at or near' in e_str or 'invalid input syntax for type' in e_str:
                 # Check if the error points near a double quote
                 if '"""' in e_str or '"' in sql_query:
                      error_message += "\n\n**Hint:** MySQL (and standard SQL) uses single quotes (') for string literals (e.g., `WHERE city = 'Chicago'`), not double quotes (\"). Double quotes are sometimes used for identifiers."
                 else:
                     error_message += "\n\n**Hint:** Check your SQL syntax carefully near the point mentioned in the error."

        except Exception as e_hint: print(f"Error generating hint: {e_hint}")

        print(f"ERROR [simulate_query_duckdb]: {error_message}\nQuery: {sql_query}")
        if con:
            try: con.close()
            except: pass # Ignore errors during close if connection failed
        return error_message # Return the detailed error message string

def get_table_schema(table_name, tables_dict_display):
    """Gets column names and data types for a given table name from original display data."""
    if table_name in tables_dict_display and isinstance(tables_dict_display[table_name], pd.DataFrame):
        df = tables_dict_display[table_name]
        # Get columns and pandas dtypes as strings
        schema_dict = {col: str(dtype) for col, dtype in df.dtypes.items()}
        return schema_dict # Return a dictionary {column_name: dtype_string}
    return {}

def evaluate_answer_with_llm(question_data, student_answer, tables_sim, tables_display):
    """Evaluate the user's answer using Gemini API (MySQL focus) and simulate using DuckDB (on lowercase data)."""
    if not student_answer.strip(): return "Please provide an answer.", False, "N/A", "N/A", "No input."
    question = question_data["question"]; relevant_table_names = question_data["relevant_tables"]; correct_answer_example = question_data["correct_answer_example"]

    # Generate Schema Info from Display Tables (original casing) for the prompt
    schema_info_str = ""
    if not relevant_table_names: schema_info_str = "No table schema context provided.\n"
    else:
        for name in relevant_table_names:
            schema_dict = get_table_schema(name, tables_display) # Use display tables for schema context
            if schema_dict:
                 # Format schema nicely for the prompt
                 schema_lines = [f"    - {col} ({dtype})" for col, dtype in schema_dict.items()]
                 schema_info_str += f"Table '{name}':\n" + "\n".join(schema_lines) + "\n\n"
            else: schema_info_str += f"Table '{name}': Schema not found.\n"

    prompt = f"""
    You are an expert SQL evaluator acting as a friendly SQL mentor, focusing ONLY on MySQL syntax and logic.

    **Evaluation Task:**

    1.  **Question:** {question}
    2.  **Relevant Table Schemas (Original Case & Types):**
        {schema_info_str.strip()}
    3.  **Student's SQL Query:**
        ```sql
        {student_answer}
        ```
    4.  **Important Context:**
        * **Target Dialect:** Evaluate strictly based on **MySQL syntax**. For example, strings MUST use single quotes (e.g., 'New York'), not double quotes. Column and table names might or might not be quoted with backticks (`), but standard keywords (SELECT, FROM, WHERE, etc.) should be correct. Check for common MySQL functions if used.
        * **Case-Insensitivity Simulation:** Although the schema shows mixed-case data, the query simulation environment automatically handles string comparisons case-insensitively (similar to default MySQL behavior). Therefore, a query like `WHERE city = 'new york'` will correctly match 'New York' in the simulation. **Focus your evaluation on the logical correctness and MySQL syntax, assuming case-insensitivity for string comparisons.** Do NOT penalize the student if their query uses different casing in string literals (e.g., 'pending' vs 'Pending') as long as the logic is correct, because the simulation handles it. Penalize incorrect syntax like using double quotes for strings.

    **Analysis Instructions:**

    * **MySQL Syntax:** Is the query valid **MySQL** syntax? Pay close attention to quote usage (single quotes for strings REQUIRED), keywords, clauses, and function names. Mention *specific* MySQL syntax errors if found (e.g., "MySQL mein strings ke liye single quotes (') use karte hain, double quotes (\") nahi.").
    * **Correctness & Logic:** Does the student's query accurately answer the **Question** based on the **Schemas**, assuming case-insensitive string comparisons? Does it use appropriate clauses (SELECT, FROM, WHERE, JOIN, GROUP BY, ORDER BY, aggregates, etc.) correctly for the task? Is the logic sound?
    * **Feedback (Hindi):** Provide clear, constructive feedback in a friendly, encouraging, casual Hindi tone (like a helpful senior).
        * If correct (both logic and MySQL syntax): Praise the student (e.g., "Wah bhai! Ekdum sahi MySQL query hai ye. Logic bhi perfect aur syntax bhi MySQL ke hisaab se bilkul theek.").
        * If incorrect syntax: Gently point out the specific MySQL syntax error (e.g., "Arre yaar, query ka logic toh theek lag raha hai, lekin MySQL mein string values ke liye single quotes (') use karna hota hai, double quotes (\") nahi. Double quotes (\") identifiers ke liye use ho sakte hain (jaise `column name`), par strings ke liye hamesha single quotes (') hi aate hain. Isko theek karke try karo!").
        * If incorrect logic: Explain the logical flaw clearly (e.g., "Hmm, lagta hai JOIN condition mein thodi गड़बड़ hai..." or "Is sawaal ke liye COUNT ke saath GROUP BY use karna padega na?"). Suggest the correct approach conceptually.
        * If both are incorrect: Prioritize explaining the most fundamental error (often syntax first, like wrong quotes).
    * **Verdict:** Conclude your entire response with *exactly* one line formatted as: "Verdict: Correct" or "Verdict: Incorrect". This line MUST be the very last line.

    **Begin Evaluation:**
    """

    feedback_llm = "AI feedback could not be generated."; is_correct_llm = False; llm_output = "Error: No LLM response generated."
    try:
        response = model.generate_content(prompt)
        # Handle potential API response variations
        if hasattr(response, 'parts') and response.parts:
             llm_output = "".join(part.text for part in response.parts)
        elif hasattr(response, 'text'):
             llm_output = response.text
        else:
             # Attempt to get text if structure is unexpected, or default to error
             llm_output = str(response) # Or handle specific structures if known

        llm_output = llm_output.strip()
        # More robust verdict parsing
        verdict_match = re.search(r'Verdict:\s*(Correct|Incorrect)\s*$', llm_output, re.M | re.I)
        if verdict_match:
            is_correct_llm = (verdict_match.group(1).strip().lower() == "correct")
            # Extract feedback part before the verdict line
            feedback_llm = llm_output[:verdict_match.start()].strip()
            if not feedback_llm: # Handle case where feedback might be missing before verdict
                feedback_llm = f"Evaluation complete. Verdict: {verdict_match.group(1).strip()}"
        else:
            st.warning(f"⚠️ Could not parse AI verdict from the response.")
            print(f"WARNING: Could not parse verdict from LLM output:\n---\n{llm_output}\n---")
            # Use the full output as feedback, but mark as incorrect since verdict is unclear
            feedback_llm = llm_output + "\n\n_(System Note: AI verdict parsing failed. Assuming incorrect.)_"
            is_correct_llm = False

        # Replace "student" with "aap" for politeness
        feedback_llm = feedback_llm.replace("student", "aap")

    except Exception as e:
        st.error(f"🚨 AI Error during evaluation: {e}")
        print(f"ERROR: Gemini call or processing failed: {e}\nPrompt:\n{prompt[:500]}...") # Log part of the prompt
        feedback_llm = f"AI feedback generation failed: {e}"
        is_correct_llm = False
        llm_output = f"Error: {e}"

    # Simulate queries using the lowercase data (tables_sim)
    actual_result_sim = simulate_query_duckdb(student_answer, tables_sim)
    # Simulate the corrected example query (which should also work on lowercase data)
    expected_result_sim = simulate_query_duckdb(correct_answer_example, tables_sim)

    # Refine correctness: LLM must say correct AND simulation must not return an error string
    final_correctness = is_correct_llm and not isinstance(actual_result_sim, str)

    # If LLM said correct but simulation failed, add a note to feedback
    if is_correct_llm and isinstance(actual_result_sim, str):
        feedback_llm += f"\n\n**Mentor Note:** AI ko laga ki logic sahi hai, lekin query simulation mein error aa gaya: `{actual_result_sim}`. Syntax dobara check karein, khaas kar ke quotes aur column/table names."
        final_correctness = False # Override LLM verdict if simulation fails

    # If LLM said incorrect but simulation produced a result (maybe syntax was ok but logic wrong)
    # No change needed, LLM feedback should explain the logic error.

    return feedback_llm, final_correctness, expected_result_sim, actual_result_sim, llm_output


def calculate_score(user_answers):
    """Calculate the score based on correct answers."""
    if not user_answers: return 0
    correct = sum(1 for ans in user_answers if ans.get("is_correct", False))
    total = len(user_answers)
    return (correct / total) * 100 if total > 0 else 0

def analyze_performance(user_answers):
    """Analyze the user's performance and provide detailed feedback via LLM (MySQL focus)."""
    performance_data = { "strengths": [], "weaknesses": [], "overall_feedback": "Analysis could not be completed." }
    if not user_answers: performance_data["overall_feedback"] = "Koi jawab nahi diya gaya isliye analysis nahi ho sakta."; return performance_data

    try:
        correct_q = [ans["question"] for ans in user_answers if ans.get("is_correct")]
        incorrect_ans = [{"question": ans["question"], "your_answer": ans["student_answer"], "feedback_received": ans.get("feedback", "N/A")} for ans in user_answers if not ans.get("is_correct")]
        performance_data["strengths"] = correct_q
        performance_data["weaknesses"] = [item["question"] for item in incorrect_ans] # Store only question text
        total_q, correct_c, score = len(user_answers), len(correct_q), calculate_score(user_answers)

        incorrect_sum = "\n".join([
            f"  Q: {item['question']}\n    Aapka Jawaab:\n    ```sql\n    {item['your_answer']}\n    ```\n    Feedback Mila:\n    {item['feedback_received']}\n"
            for item in incorrect_ans
        ]).strip() if incorrect_ans else "Koi nahi! Sab sahi the!"

        prompt = f"""Ek student ne MySQL SQL quiz diya hai. String comparisons case-insensitive assume kiye gaye the simulation mein. Unka performance yeh hai:
Total Questions: {total_q} | Correct Answers (Logic & MySQL Syntax): {correct_c} | Score: {score:.2f}%

Correctly Answered Questions:
{chr(10).join(f'  - {q}' for q in correct_q) if correct_q else '  (Koi nahi)'}

Incorrectly Answered Questions (Logic ya MySQL Syntax mein galti):
{incorrect_sum}

Task: Ab ek dost ki tarah, casual Hindi mein overall performance ka ek summary feedback do. MySQL syntax (jaise single quotes for strings) aur logical correctness par focus karo. Batao kahaan achha kiya aur kahaan improvement chahiye specifically MySQL ke context mein. Agar syntax errors (jaise double quotes for strings) baar baar aa rahe hain toh uspe emphasize karo. Overall encouragement bhi do.
"""
    except Exception as data_prep_error:
        print(f"Error preparing data for analysis: {data_prep_error}")
        performance_data["overall_feedback"] = f"Analysis data preparation failed: {data_prep_error}"
        return performance_data

    try:
        response = model.generate_content(prompt)
        generated_feedback = None
        # Handle potential API response variations
        if hasattr(response, 'parts') and response.parts:
             generated_feedback = "".join(part.text for part in response.parts).strip()
        elif hasattr(response, 'text'):
             generated_feedback = response.text.strip()
        else:
             generated_feedback = str(response).strip() # Fallback

        if generated_feedback:
             performance_data["overall_feedback"] = generated_feedback
        else:
             performance_data["overall_feedback"] = "AI response format unclear or empty."
             print(f"Warning: Unexpected or empty LLM response for performance summary.")

    except Exception as e:
        print(f"Error generating performance summary: {e}")
        performance_data["overall_feedback"] = f"Summary generation error: {e}"

    return performance_data


def get_emoji(is_correct):
    """Return ✅ for correct, ❌ for incorrect."""
    return "✅" if is_correct else "❌"

def display_simulation(title, result_data):
    """Helper function to display simulation results (DataFrame or error string)."""
    st.write(f"**{title}:**")
    if isinstance(result_data, pd.DataFrame):
        if result_data.empty:
            st.info("_(Simulation resulted in an empty table)_")
        else:
            # Reset index for cleaner display, allow container width
            st.dataframe(result_data.reset_index(drop=True), hide_index=True, use_container_width=True)
    elif isinstance(result_data, str) and "Simulation Error" in result_data:
        # Display simulation errors clearly using st.error or st.warning
        st.error(result_data, icon="⚠️") # Use error for simulation failures
    elif result_data == "N/A":
        st.info("_(Simulation not applicable or not run)_")
    elif isinstance(result_data, str): # Catch other potential string messages?
         st.info(f"_(Simulation note: {result_data})_")
    else:
        st.error(f"_(Unexpected simulation result type: {type(result_data)})_")


# --- Streamlit App ---

# --- Start Screen ---
if not st.session_state.quiz_started:
    st.title("🚀 SQL Mentor - Interactive MySQL Practice")
    st.markdown("### Apne MySQL Skills Ko Test Aur Improve Karein!")
    st.markdown("""
        **📌 Important Notes:**
        - This quiz focuses on standard **MySQL syntax**. Pay close attention to details like using **single quotes (')** for string values (e.g., `'New York'`).
        - Queries are simulated against sample data. String comparisons (like in `WHERE` clauses) are treated as **case-insensitive**, similar to default MySQL behavior (so `'new york'` will match `'New York'`).
        - Your queries will be evaluated by an AI for correctness (logic) and valid MySQL syntax.
        """)
    col1, col2 = st.columns([2, 1])
    with col1:
         st.write("""
         Is interactive quiz mein, aap do sample tables ke saath kaam karenge (Data original case mein dikhaya gaya hai):
         - **Users Table**: User details (ID, naam, email, umar, sheher).
         - **Orders Table**: Order details (ID, user ID, amount, date, status).
         """)
    with col2:
         st.markdown("#### Tables Overview")
         # Use display tables for overview
         table_overview_data = {
             "Table": list(original_tables_for_display.keys()),
             "Rows": [len(df) for df in original_tables_for_display.values()],
             "Columns": [len(df.columns) for df in original_tables_for_display.values()]
         }
         st.dataframe(pd.DataFrame(table_overview_data), hide_index=True)

    st.write("### 🔍 Table Previews (Original Data)");
    tab1, tab2 = st.tabs(["Users Table", "Orders Table"])
    with tab1: st.dataframe(users_table_display, hide_index=True, use_container_width=True) # Show original
    with tab2: st.dataframe(orders_table_display, hide_index=True, use_container_width=True) # Show original

    with st.expander("📝 Quiz Ke Baare Mein"):
        st.write(f"""
        - Aapko {len(sql_questions)} MySQL query challenges solve karne honge.
        - Har jawaab ke baad AI Mentor se immediate feedback milega (MySQL syntax aur logic par focus).
        - **SQL Dialect Focus:** MySQL
        - **String Comparison:** Case-Insensitive (like MySQL defaults)
        - **Tip:** Strings ko hamesha **single quotes** mein likhein (e.g., `WHERE city = 'Chicago'`). Double quotes (`"`) strings ke liye **nahi** chalenge.
        """)
    if st.button("🚀 Start MySQL Challenge!"):
        st.session_state.quiz_started = True
        st.session_state.user_answers = []
        st.session_state.current_question = 0
        st.session_state.quiz_completed = False
        st.session_state.show_detailed_feedback = False
        st.rerun()

# --- Quiz In Progress ---
elif st.session_state.quiz_started and not st.session_state.quiz_completed:
    st.title("✍️ MySQL Query Challenge")

    # --- Display Previous Answers ---
    if st.session_state.user_answers:
        st.markdown("---")
        st.subheader("📖 Ab Tak Ke Jawaab Aur Feedback")
        # Show most recent answer first
        for i, ans_data in enumerate(reversed(st.session_state.user_answers)):
            q_num = len(st.session_state.user_answers) - i
            is_correct = ans_data.get('is_correct', False)
            with st.expander(f"Question {q_num}: {ans_data['question']} {get_emoji(is_correct)}", expanded=(i == 0)): # Expand the latest one
                st.write(f"**Aapka Jawaab:**")
                st.code(ans_data.get('student_answer', '(No answer provided)'), language='sql')
                st.write(f"**SQL Mentor Feedback:**")
                if is_correct:
                    st.success(ans_data.get('feedback', 'N/A'))
                else:
                    st.error(ans_data.get('feedback', 'N/A')) # Use error for incorrect feedback

                # Display simulation results vertically
                st.markdown("---") # Separator before tables
                display_simulation("Simulated Result (Aapka Query Output)", ans_data.get("actual_result"))
                st.divider() # Visual divider
                display_simulation("Simulated Result (Expected Example Output)", ans_data.get("expected_result"))
        st.markdown("---")

    # --- Current Question ---
    current_q_index = st.session_state.current_question
    if current_q_index < len(sql_questions):
        question_data = sql_questions[current_q_index]
        st.subheader(f"Question {current_q_index + 1} / {len(sql_questions)}")
        st.markdown(f"**{question_data['question']}**")
        st.markdown("---")
        st.markdown("_**Note:** Yaad rakhein, MySQL syntax use karein (strings ke liye **single quotes** jaise `'Mumbai'`). String comparisons case-insensitive honge._")

        # Display relevant table previews using original data
        rel_tables = question_data.get("relevant_tables", [])
        if rel_tables:
            st.write("**Relevant Tables (Original Data):**")
            tabs = st.tabs([f"{name.capitalize()} Table" for name in rel_tables])
            for i, table_name in enumerate(rel_tables):
                with tabs[i]:
                    if table_name in original_tables_for_display:
                        st.dataframe(original_tables_for_display[table_name], hide_index=True, use_container_width=True)
                    else:
                        st.warning(f"Schema/Preview error for table '{table_name}'.")
        else:
            st.info("Is sawaal ke liye specific table preview nahi hai.")

        student_answer = st.text_area("Apna MySQL Query Yahaan Likhein:", key=f"answer_{current_q_index}", height=150)

        if st.button("✅ Submit Answer", key=f"submit_{current_q_index}"):
            if student_answer and student_answer.strip():
                with st.spinner("🤖 AI Mentor aapka jawaab check kar raha hai..."):
                    # Pass both simulation and display tables to evaluator
                    feedback, is_correct, expected_sim, actual_sim, llm_raw = evaluate_answer_with_llm(
                        question_data,
                        student_answer,
                        tables_for_simulation,    # Use lowercase data for simulation
                        original_tables_for_display # Use original data for schema context
                    )
                # Store results in session state
                st.session_state.user_answers.append({
                    "question": question_data["question"],
                    "student_answer": student_answer,
                    "feedback": feedback,
                    "is_correct": is_correct,
                    "expected_result": expected_sim,
                    "actual_result": actual_sim,
                    "llm_raw_output": llm_raw # Store raw LLM output for debugging if needed
                })

                # Move to next question or complete quiz
                if current_q_index < len(sql_questions) - 1:
                    st.session_state.current_question += 1
                else:
                    st.session_state.quiz_completed = True
                st.rerun() # Rerun to display feedback and next question/completion screen
            else:
                st.warning("Please enter your SQL query before submitting.")

        # Progress bar
        progress = (current_q_index) / len(sql_questions)
        st.progress(progress)
        st.caption(f"Question {current_q_index + 1} of {len(sql_questions)}")
    else:
        # Should not happen if logic is correct, but handle defensively
        st.warning("Quiz state error: No more questions found, but quiz not marked as completed.")
        st.session_state.quiz_completed = True
        st.rerun()

# --- Quiz Completed Screen ---
elif st.session_state.quiz_completed:
    st.balloons()
    st.title("🎉 Quiz Complete!")
    score = calculate_score(st.session_state.user_answers)
    # Display score with color based on pass/fail
    if score >= 60:
         st.metric(label="Your Final Score (%) - MySQL", value=f"{score:.2f}", delta="Passed!")
    else:
         st.metric(label="Your Final Score (%) - MySQL", value=f"{score:.2f}", delta="Needs Improvement", delta_color="inverse")


    st.subheader("📝 Final Review: Aapke Jawaab Aur Feedback")
    for i, ans_data in enumerate(st.session_state.user_answers):
         is_correct = ans_data.get('is_correct', False)
         with st.expander(f"Question {i + 1}: {ans_data['question']} {get_emoji(is_correct)}", expanded=False):
              st.write(f"**Aapka Jawaab:**")
              st.code(ans_data.get('student_answer', '(No answer)'), language='sql')
              st.write(f"**SQL Mentor Feedback:**")
              if is_correct:
                   st.success(ans_data.get('feedback', 'N/A'))
              else:
                   st.error(ans_data.get('feedback', 'N/A')) # Use error styling

              # Display simulation results vertically
              st.markdown("---") # Separator before tables
              display_simulation("Simulated Result (Aapka Query)", ans_data.get("actual_result"))
              st.divider() # Visual divider
              display_simulation("Simulated Result (Example Query)", ans_data.get("expected_result"))

    st.markdown("---")
    col_cta_1, col_cta_2 = st.columns(2)
    with col_cta_1:
        if st.button("📊 Detailed Performance Analysis"):
            st.session_state.show_detailed_feedback = not st.session_state.show_detailed_feedback # Toggle visibility
            st.rerun() # Rerun to update the view
    with col_cta_2:
         # Example CTAs - replace with relevant links
         if score < 60:
              st.error("Score thoda kam hai... Keep practicing!")
              # st.link_button("Need Help? SQL Resources", "https://example.com/sqlhelp", use_container_width=True)
         else:
              st.success("Bahut badhiya score! Keep it up! 👍")
              # st.link_button("Next Steps? Advanced SQL", "https://example.com/advancedsql", use_container_width=True)

    # --- Detailed Feedback Section ---
    if st.session_state.show_detailed_feedback:
        st.markdown("---")
        st.subheader("📈 Detailed Performance Analysis (AI Generated)")
        with st.spinner("🤖 AI performance summary generate kar raha hai..."):
            performance_feedback = analyze_performance(st.session_state.user_answers)

        st.write("**Overall Feedback (MySQL Focus):**")
        st.info(performance_feedback.get("overall_feedback", "Summary N/A."))

        st.write("**Strengths (Questions answered correctly - Logic & MySQL Syntax):**")
        strengths = performance_feedback.get("strengths", [])
        if strengths:
            for i, q in enumerate(strengths):
                 st.success(f"{i + 1}. {q} ✅")
        else:
            st.write("_(Is baar koi jawaab sahi nahi tha. Practice karte rahein!)_")

        st.write("**Areas for Improvement (Questions answered incorrectly - Check Feedback):**")
        weaknesses = performance_feedback.get("weaknesses", [])
        if weaknesses:
             for i, q in enumerate(weaknesses):
                  st.error(f"{i + 1}. {q} ❌") # Use error styling
        else:
             st.write("_(Koi galat jawaab nahi! Zabardast!)_")

    st.markdown("---")
    if st.button("🔄 Restart Quiz"):
        # Clear relevant session state keys to restart
        keys_to_reset = ["user_answers", "current_question", "quiz_started", "quiz_completed", "show_detailed_feedback"]
        for key in keys_to_reset:
            if key in st.session_state:
                 del st.session_state[key]
        # Explicitly set defaults needed for restart
        st.session_state.quiz_started = False
        st.session_state.current_question = 0
        st.rerun()

# Fallback for any unexpected state
else:
    st.error("An unexpected error occurred with the application state. Please try restarting.")
    if st.button("Force Restart App State"):
         keys_to_reset = ["user_answers", "current_question", "quiz_started", "quiz_completed", "show_detailed_feedback"]
         for key in keys_to_reset:
             if key in st.session_state:
                 del st.session_state[key]
         # Explicitly set defaults needed for restart
         st.session_state.quiz_started = False
         st.session_state.current_question = 0
         st.rerun()
