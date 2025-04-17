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
    "status": ["Completed", "pending", "Completed", "Shipped", "Cancelled"]  # Changed "Pending" to "pending" for consistency
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
    { "question": "Write a SQL query to find all orders with a status of 'pending' from the 'orders' table.", "correct_answer_example": "SELECT * FROM orders WHERE TRIM(LOWER(status)) = 'pending';", "sample_table": orders_table, "relevant_tables": ["orders"] },  # Updated to use LOWER() for case insensitivity
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
if "show_debug_info" not in st.session_state: st.session_state.show_debug_info = False

# --- Data Consistency Check ---
def ensure_data_consistency():
    """Ensures data consistency in tables and returns any issues found"""
    inconsistencies = []
    
    # Check orders table status values
    status_values = original_tables["orders"]["status"].unique().tolist()
    
    # Check if 'Pending' exists but 'pending' doesn't
    if 'Pending' in status_values and 'pending' not in status_values:
        inconsistencies.append("'Pending' is capitalized in database but query examples use lowercase 'pending'")
    
    # Check if both 'Pending' and 'pending' exist (inconsistent data)
    if 'Pending' in status_values and 'pending' in status_values:
        inconsistencies.append("Both 'Pending' and 'pending' exist in the database (inconsistent data)")
    
    return inconsistencies, status_values

# --- Helper Functions ---

def smart_query_evaluator(query, tables_dict):
    """Evaluates SQL query with automatic case sensitivity handling"""
    # Try original query first
    result = simulate_query_duckdb(query, tables_dict)
    
    # If result is empty DataFrame, try case-insensitive alternatives
    if isinstance(result, pd.DataFrame) and result.empty:
        # Check if query contains status comparison with 'Pending'
        if "status = 'Pending'" in query:
            case_insensitive_query = query.replace("status = 'Pending'", "LOWER(status) = 'pending'")
            alt_result = simulate_query_duckdb(case_insensitive_query, tables_dict)
            if isinstance(alt_result, pd.DataFrame) and not alt_result.empty:
                return alt_result, True  # Return result and flag indicating case sensitivity fix
        
        # Check if query contains status comparison with 'PENDING'
        if "status = 'PENDING'" in query:
            alt_query = query.replace("status = 'PENDING'", "LOWER(status) = 'pending'")
            alt_result = simulate_query_duckdb(alt_query, tables_dict)
            if isinstance(alt_result, pd.DataFrame) and not alt_result.empty:
                return alt_result, True  # Return result and flag indicating case sensitivity fix
    
    return result, False  # Return original result and flag indicating no case sensitivity fix

def simulate_query_duckdb(sql_query, tables_dict):
    """Simulates an SQL query using DuckDB on in-memory pandas DataFrames."""
    if not sql_query or not sql_query.strip():
        return "Simulation Error: No query provided."
    if not tables_dict:
        return "Simulation Error: No tables provided for context."
    con = None
    try:
        con = duckdb.connect(database=':memory:', read_only=False)
        for table_name, df in tables_dict.items():
            if isinstance(df, pd.DataFrame): con.register(str(table_name), df)
            else: print(f"Warning [simulate_query]: Item '{table_name}' not a DataFrame.")
        result_df = con.execute(sql_query).df()
        con.close(); return result_df
    except Exception as e:
        error_message = f"Simulation Error: Failed to execute query. Reason: {str(e)}"
        try:
            e_str = str(e).lower()
            binder_match = re.search(r'(binder error|catalog error|parser error).*referenced column "([^"]+)" not found', e_str)
            syntax_match = re.search(r'syntax error.*at or near ""([^"]+)""', e_str)
            if binder_match: error_message += f"\n\n**Hint:** Use single quotes (') for text values like `'{binder_match.group(2)}'` instead of double quotes (\")."
            elif syntax_match: error_message += f"\n\n**Hint:** Use single quotes (') for text values like `'{syntax_match.group(1)}'` instead of double quotes (\")."
        except Exception as e_hint: print(f"Error generating hint: {e_hint}")
        print(f"ERROR [simulate_query_duckdb]: {error_message}\nQuery: {sql_query}")
        if con:
            try: con.close()
            except: pass
        return error_message

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
    actual_result_sim, case_fix_applied = smart_query_evaluator(student_answer, original_tables)
    expected_result_sim, _ = smart_query_evaluator(correct_answer_example, original_tables)
    
    return feedback_llm, is_correct_llm, expected_result_sim, actual_result_sim, llm_output, case_fix_applied

def calculate_score(user_answers):
    """Calculate the score based on correct answers."""
    if not user_answers: return 0
    correct = sum(1 for ans in user_answers if ans.get("is_correct", False))
    total = len(user_answers)
    return (correct / total) * 100 if total > 0 else 0

def analyze_performance(user_answers):
    """Analyze the user's performance and provide detailed feedback via LLM."""
    performance_data = { "strengths": [], "weaknesses": [], "overall_feedback": "Analysis could not be completed." }
    if not user_answers: performance_data["overall_feedback"] = "Koi jawab nahi diya gaya."; return performance_data
    try:
        correct_q = [ans["question"] for ans in user_answers if ans.get("is_correct")]
        incorrect_ans = [{"question": ans["question"], "your_answer": ans["student_answer"], "feedback_received": ans.get("feedback", "N/A")} for ans in user_answers if not ans.get("is_correct")]
        performance_data["strengths"] = correct_q; performance_data["weaknesses"] = [item["question"] for item in incorrect_ans]
        total_q, correct_c, score = len(user_answers), len(correct_q), calculate_score(user_answers)
        incorrect_sum = "\n".join([ f"  Q: {item['question']}\n    Aapka Jawaab: {item['your_answer']}\n    Feedback Mila: {item['feedback_received']}\n" for item in incorrect_ans]).strip() if incorrect_ans else "Koi nahi! Sab sahi the!"
        prompt = f"""Ek student ne SQL quiz diya hai...\nTotal Questions: {total_q} | Correct Answers: {correct_c} | Score: {score:.2f}%\nCorrectly Answered Questions:\n{chr(10).join(f'  - {q}' for q in correct_q) if correct_q else '  (Koi nahi)'}\nIncorrectly Answered Questions:\n{incorrect_sum}\nTask: Ab ek dost ki tarah, casual Hindi mein overall performance ka ek summary feedback do..."""
    except Exception as data_prep_error: print(f"Error preparing data for analysis: {data_prep_error}"); performance_data["overall_feedback"] = f"Analysis prep failed: {data_prep_error}"; return performance_data
    try:
        response = model.generate_content(prompt); generated_feedback = None
        if response.parts: generated_feedback = "".join(part.text for part in response.parts).strip()
        elif hasattr(response, 'text'): generated_feedback = response.text.strip()
        if generated_feedback: performance_data["overall_feedback"] = generated_feedback
        else: performance_data["overall_feedback"] = "AI response format unclear."; print(f"Warning: Unexpected LLM response.")
    except Exception as e: print(f"Error generating performance summary: {e}"); performance_data["overall_feedback"] = f"Summary generation error: {e}"
    return performance_data

def get_emoji(is_correct):
    return "✅" if is_correct else "❌"

def display_simulation(title, result_data, case_fix_applied=False):
    """Helper function to display simulation results (DataFrame or error)."""
    st.write(f"**{title}:**")
    if case_fix_applied:
        st.info("Note: Case-insensitive query was automatically applied to show results.")
        
    if isinstance(result_data, pd.DataFrame):
        if result_data.empty:
            st.info("_(Simulation resulted in an empty table)_")
        else:
            # Use use_container_width to allow table to expand
            st.dataframe(result_data.reset_index(drop=True), hide_index=True, use_container_width=True)
    elif isinstance(result_data, str) and "Simulation Error" in result_data:
        st.warning(result_data, icon="⚠️")
    elif result_data == "N/A":
        st.info("_(Simulation not applicable)_")
    else:
        st.error(f"_(Unexpected simulation result type: {type(result_data)})_")

# --- Streamlit App ---

# --- Start Screen ---
st.title("SQL Practice Quiz")
st.write("Test your SQL knowledge with interactive questions!")

# Run data consistency check
inconsistencies, status_values = ensure_data_consistency()
if inconsistencies:
    st.warning("⚠️ Data Consistency Issues Detected:")
    for issue in inconsistencies:
        st.write(f"- {issue}")
    st.write("These issues may cause unexpected query results.")

# Debug Information Toggle
if st.checkbox("Show Debug Information", value=st.session_state.show_debug_info):
    st.session_state.show_debug_info = True
    with st.expander("Database Content Inspection", expanded=True):
        st.subheader("Database Content")
        
        # Show all distinct status values
        st.write("Status values in database:", status_values)
        
        # Show full orders table
        st.write("Full orders table data:")
        st.dataframe(original_tables["orders"])
        
        # Test specific queries
        st.write("Test query with 'Pending':")
        test1 = simulate_query_duckdb("SELECT * FROM orders WHERE status = 'Pending'", original_tables)
        st.dataframe(test1)
        
        st.write("Test query with 'pending':")
        test2 = simulate_query_duckdb("SELECT * FROM orders WHERE status = 'pending'", original_tables)
        st.dataframe(test2)
        
        st.write("Test query with LOWER function:")
        test3 = simulate_query_duckdb("SELECT * FROM orders WHERE LOWER(status) = 'pending'", original_tables)
        st.dataframe(test3)
else:
    st.session_state.show_debug_info = False

if not st.session_state.quiz_started:
    st.write("This quiz will test your SQL knowledge with questions ranging from basic to intermediate difficulty.")
    st.write("You'll get instant feedback on your answers and see the results of your queries.")
    
    if st.button("Start Quiz"):
        st.session_state.quiz_started = True
        st.experimental_rerun()

# --- Quiz Interface ---
elif not st.session_state.quiz_completed:
    # Display progress
    progress_text = f"Question {st.session_state.current_question + 1} of {len(sql_questions)}"
    st.progress((st.session_state.current_question) / len(sql_questions))
    st.write(progress_text)
    
    # Display current question
    current_q = sql_questions[st.session_state.current_question]
    st.subheader(current_q["question"])
    
    # Display relevant table schemas
    for table_name in current_q["relevant_tables"]:
        if table_name in original_tables:
            st.write(f"**Table: {table_name}**")
            st.dataframe(original_tables[table_name].head(), use_container_width=True)
    
    # User input
    user_answer = st.text_area("Your SQL Query:", height=100, key=f"answer_{st.session_state.current_question}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Submit Answer"):
            if not user_answer.strip():
                st.warning("Please enter a SQL query before submitting.")
            else:
                # Evaluate answer
                feedback, is_correct, expected_result, actual_result, _, case_fix_applied = evaluate_answer_with_llm(
                    current_q, user_answer, original_tables
                )
                
                # Store answer
                st.session_state.user_answers.append({
                    "question": current_q["question"],
                    "student_answer": user_answer,
                    "feedback": feedback,
                    "is_correct": is_correct,
                    "expected_result": expected_result,
                    "actual_result": actual_result,
                    "case_fix_applied": case_fix_applied
                })
                
                # Move to next question or complete quiz
                if st.session_state.current_question < len(sql_questions) - 1:
                    st.session_state.current_question += 1
                    st.experimental_rerun()
                else:
                    st.session_state.quiz_completed = True
                    st.experimental_rerun()
    
    with col2:
        if st.button("Skip Question"):
            if st.session_state.current_question < len(sql_questions) - 1:
                st.session_state.current_question += 1
                st.experimental_rerun()
            else:
                st.session_state.quiz_completed = True
                st.experimental_rerun()

# --- Results Screen ---
else:
    st.subheader("Quiz Results")
    
    # Calculate and display score
    score = calculate_score(st.session_state.user_answers)
    st.write(f"Your score: {score:.2f}%")
    
    # Display answers and feedback
    st.subheader("Your Answers")
    
    for i, answer in enumerate(st.session_state.user_answers):
        with st.expander(f"{get_emoji(answer.get('is_correct', False))} Question {i+1}: {answer['question']}"):
            st.write("**Your Query:**")
            st.code(answer["student_answer"], language="sql")
            
            st.write("**SQL Mentor Feedback:**")
            st.write(answer.get("feedback", "No feedback available."))
            
            # Display simulation results with case sensitivity information
            display_simulation("Simulated Result (Aapka Query Output)", 
                              answer.get("actual_result", "N/A"), 
                              answer.get("case_fix_applied", False))
            
            display_simulation("Simulated Result (Expected Example Output)", 
                              answer.get("expected_result", "N/A"))
    
    # Option to show detailed performance analysis
    if st.button("Show Detailed Performance Analysis" if not st.session_state.show_detailed_feedback else "Hide Detailed Analysis"):
        st.session_state.show_detailed_feedback = not st.session_state.show_detailed_feedback
    
    if st.session_state.show_detailed_feedback:
        st.subheader("Performance Analysis")
        performance = analyze_performance(st.session_state.user_answers)
        
        st.write("**Overall Feedback:**")
        st.write(performance["overall_feedback"])
        
        st.write("**Strengths:**")
        if performance["strengths"]:
            for strength in performance["strengths"]:
                st.write(f"- {strength}")
        else:
            st.write("No specific strengths identified.")
        
        st.write("**Areas for Improvement:**")
        if performance["weaknesses"]:
            for weakness in performance["weaknesses"]:
                st.write(f"- {weakness}")
        else:
            st.write("No specific areas for improvement identified.")
    
    # Restart quiz option
    if st.button("Restart Quiz"):
        st.session_state.user_answers = []
        st.session_state.current_question = 0
        st.session_state.quiz_started = False
        st.session_state.quiz_completed = False
        st.session_state.show_detailed_feedback = False
        st.experimental_rerun()
