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
    "status": ["Completed", "Pending", "Completed", "Shipped", "Cancelled"]
})
original_tables = {
    # Use lowercase names matching standard SQL conventions if possible
    "users": users_table,
    "orders": orders_table
}

# --- SQL Questions List ---
sql_questions = [
    {
        "question": "Write a SQL query to get all details about users from the 'users' table.",
        "correct_answer_example": "SELECT * FROM users;",
        "sample_table": users_table,
        "relevant_tables": ["users"]
    },
    {
        "question": "Write a SQL query to count the total number of users in the 'users' table.",
        "correct_answer_example": "SELECT COUNT(*) AS user_count FROM users;",
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
        "correct_answer_example": "SELECT AVG(amount) AS average_amount FROM orders;",
        "sample_table": orders_table,
        "relevant_tables": ["orders"]
    },
    {
        "question": "Write a SQL query to find users who have not placed any orders. Use the 'users' and 'orders' tables.",
        "correct_answer_example": "SELECT u.* FROM users u LEFT JOIN orders o ON u.user_id = o.user_id WHERE o.order_id IS NULL;",
        "sample_table": users_table,
        "relevant_tables": ["users", "orders"]
    },
    {
        "question": "Write a SQL query to calculate the total amount spent by each user by joining the 'users' and 'orders' tables.",
        "correct_answer_example": ("SELECT u.name, SUM(o.amount) AS total_spent FROM users u "
                           "JOIN orders o ON u.user_id = o.user_id GROUP BY u.name ORDER BY u.name;"),
        "sample_table": users_table,
        "relevant_tables": ["users", "orders"]
    },
    {
        "question": "Write a SQL query to count how many orders each user has placed using a LEFT JOIN between 'users' and 'orders'. Include users with zero orders.",
        "correct_answer_example": ("SELECT u.name, COUNT(o.order_id) AS order_count FROM users u "
                           "LEFT JOIN orders o ON u.user_id = o.user_id GROUP BY u.name ORDER BY u.name;"),
        "sample_table": users_table,
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

# --- Helper Functions ---

# --- simulate_query using DuckDB with enhanced error hint ---
def simulate_query_duckdb(sql_query, tables_dict):
    """Simulates an SQL query using DuckDB on in-memory pandas DataFrames."""
    if not sql_query or not sql_query.strip():
        return "Simulation Error: No query provided."
    if not tables_dict:
        return "Simulation Error: No tables provided for context."

    con = None # Initialize con outside try
    try:
        con = duckdb.connect(database=':memory:', read_only=False)
        # Register each DataFrame in the dictionary as a DuckDB virtual table
        for table_name, df in tables_dict.items():
            if isinstance(df, pd.DataFrame): # Check if it's actually a DataFrame
                 # Ensure table names are treated as strings for registration
                 con.register(str(table_name), df)
            else:
                 # Log warning but continue if possible
                 print(f"Warning [simulate_query]: Item '{table_name}' in tables_dict is not a DataFrame.")

        # Execute the query and fetch the result as a Pandas DataFrame
        result_df = con.execute(sql_query).df()
        con.close()
        return result_df

    except Exception as e:
        # Catch DuckDB execution errors (syntax errors, binder errors, etc.)
        # Default error message
        error_message = f"Simulation Error: Failed to execute query. Reason: {str(e)}"

        # --- Add specific hint for double-quote string issue ---
        try:
            e_str = str(e).lower() # Use lowercase for easier matching
            # Check if it's a Binder Error about a referenced column not found
            # Use broader check for different error types that might indicate this issue
            binder_match = re.search(r'(binder error|catalog error|parser error).*referenced column "([^"]+)" not found', e_str)
            # Also check for syntax errors near a double quoted string
            syntax_match = re.search(r'syntax error.*at or near ""([^"]+)""', e_str) # Matches ""Value"" pattern in errors

            if binder_match:
                 double_quoted_value = binder_match.group(2) # Get the problematic value like 'pending'
                 # Add a specific, user-friendly hint
                 error_message += f"\n\n**Hint:** SQL standard uses single quotes (') for text values. Try using `'{double_quoted_value}'` instead of `\"{double_quoted_value}\"` in your `WHERE` clause."
            elif syntax_match:
                 double_quoted_value = syntax_match.group(1)
                 error_message += f"\n\n**Hint:** It looks like double quotes (\") were used for the text value `\"{double_quoted_value}\"`. SQL standard uses single quotes ('). Try `'{double_quoted_value}'` instead."

        except Exception as e_hint:
            # Avoid breaking the app if hint generation fails
            print(f"Error generating hint for simulation error: {e_hint}")
        # --- End of hint ---

        print(f"ERROR [simulate_query_duckdb]: {error_message}\nQuery: {sql_query}") # Log error
        if con:
            try: con.close() # Ensure connection is closed on error
            except: pass
        return error_message # Return the potentially enhanced error message

def get_table_schema(table_name, tables_dict):
    """Gets column names for a given table name."""
    if table_name in tables_dict:
        return tables_dict[table_name].columns.astype(str).tolist()
    return []

def evaluate_answer_with_llm(question_data, student_answer, original_tables_dict):
    """Evaluate the user's answer using Gemini API and simulate using DuckDB."""
    if not student_answer.strip():
        return "Please provide an answer.", False, "N/A", "N/A", "No input."

    question = question_data["question"]
    relevant_table_names = question_data["relevant_tables"]
    correct_answer_example = question_data["correct_answer_example"]

    # --- Schema Information ---
    schema_info = ""
    if not relevant_table_names:
         schema_info = "No specific table schema provided for context.\n"
    else:
        for name in relevant_table_names:
            columns = get_table_schema(name, original_tables_dict)
            if columns:
                # Get dtypes safely, handle potential errors if table doesn't exist
                try:
                    dtypes = original_tables_dict[name].dtypes.to_string()
                    schema_info += f"Table '{name}': Columns {columns}\n DataTypes:\n{dtypes}\n\n"
                except KeyError:
                     schema_info += f"Table '{name}': Columns {columns} (DataTypes unavailable)\n\n"
                except AttributeError:
                     schema_info += f"Table '{name}': Columns {columns} (DataTypes unavailable - not a DataFrame?)\n\n"
            else:
                schema_info += f"Table '{name}': Schema not found.\n"


    # --- LLM Prompt ---
    prompt = f"""
    You are an expert SQL evaluator acting as a friendly SQL mentor... [Rest of prompt unchanged] ...
    **Analysis Instructions:** ...
    * **Feedback:** Provide clear, constructive feedback in a friendly, encouraging, casual Hindi tone...
        * If correct: Praise...
        * If incorrect: Gently point out the error... Explain *what* is wrong (syntax - like using " vs ' for strings, logic, columns, etc.)...
    * **Verdict:** Conclude with "Verdict: Correct" or "Verdict: Incorrect". ...
    **Begin Evaluation:**
    """ # Keep prompt concise for brevity, assuming it's correct from previous steps

    # --- Call Gemini API ---
    feedback_llm = "AI feedback could not be generated." # Default
    is_correct_llm = False # Default
    llm_output = "Error: No response from LLM." # Default
    try:
        response = model.generate_content(prompt)
        if response.parts: llm_output = "".join(part.text for part in response.parts)
        else: llm_output = response.text # Fallback
        llm_output = llm_output.strip()
        verdict_match = re.search(r'^Verdict:\s*(Correct|Incorrect)\s*$', llm_output, re.MULTILINE | re.IGNORECASE)
        if verdict_match:
            verdict = verdict_match.group(1).lower()
            is_correct_llm = (verdict == "correct")
            feedback_llm = llm_output[:verdict_match.start()].strip()
        else:
            st.warning(f"⚠️ System Warning: Could not parse final verdict from AI feedback...")
            print(f"WARNING: Could not parse verdict from LLM output. Full output was:\n{llm_output}")
            feedback_llm = llm_output + "\n\n_(System Note: Automatic correctness check failed...)_"
            is_correct_llm = False
        feedback_llm = feedback_llm.replace("student", "aap")
    except Exception as e:
        st.error(f"🚨 Error communicating with AI model: {e}")
        print(f"ERROR: Exception during Gemini API call: {e}")
        feedback_llm = f"Maaf karna yaar, AI feedback generate karne mein kuch dikkat aa gayi: {e}"
        is_correct_llm = False
        llm_output = f"Error: {e}"

    # --- Simulation using DuckDB ---
    actual_result_sim = simulate_query_duckdb(student_answer, original_tables_dict)
    expected_result_sim = simulate_query_duckdb(correct_answer_example, original_tables_dict)

    return feedback_llm, is_correct_llm, expected_result_sim, actual_result_sim, llm_output


def calculate_score(user_answers):
    """Calculate the score based on correct answers."""
    # (No changes needed)
    if not user_answers: return 0
    correct = sum(1 for ans in user_answers if ans.get("is_correct", False))
    total = len(user_answers)
    return (correct / total) * 100 if total > 0 else 0

def analyze_performance(user_answers):
    """Analyze the user's performance and provide detailed feedback via LLM."""
    # (No changes needed)
    if not user_answers: return {"strengths": [], "weaknesses": [], "overall_feedback": "Koi jawab nahi diya gaya."}
    correct_q = [ans["question"] for ans in user_answers if ans.get("is_correct")]
    incorrect_ans = [{"question": ans["question"], "your_answer": ans["student_answer"], "feedback_received": ans.get("feedback", "N/A")} for ans in user_answers if not ans.get("is_correct")]
    feedback_summary = { "overall_feedback": "Performance summary generation failed." }
    total_q, correct_c, score = len(user_answers), len(correct_q), calculate_score(user_answers)
    incorrect_sum = "\n".join([ f"  Q: {item['question']}\n    Aapka Jawaab: {item['your_answer']}\n    Feedback Mila: {item['feedback_received']}\n" for item in incorrect_ans]).strip() if incorrect_ans else "Koi nahi! Sab sahi the!"
    prompt = f"""Ek student ne SQL quiz diya hai...\nTotal Questions: {total_q}\nCorrect Answers: {correct_c}\nScore: {score:.2f}%\nCorrectly Answered Questions:\n{chr(10).join(f'  - {q}' for q in correct_q) if correct_q else '  (Koi nahi)'}\nIncorrectly Answered Questions:\n{incorrect_sum}\nTask: Ab ek dost ki tarah, casual Hindi mein overall performance ka ek summary feedback do..."""
    try:
        response = model.generate_content(prompt)
        if response.parts: feedback_summary["overall_feedback"] = "".join(part.text for part in response.parts).strip()
        else: feedback_summary["overall_feedback"] = response.text.strip()
    except Exception as e:
        print(f"Error generating performance summary: {e}"); feedback_summary["overall_feedback"] = f"Summary generate karne mein dikkat: {e}"
    feedback_display = {"strengths": correct_q, "weaknesses": [item["question"] for item in incorrect_ans], "overall_feedback": feedback_summary["overall_feedback"]}
    return feedback_display

def get_emoji(is_correct):
    return "✅" if is_correct else "❌"


# --- Streamlit App ---

# --- Start Screen ---
# (No changes needed here)
if not st.session_state.quiz_started:
    st.title("🚀 SQL Mentor - Interactive SQL Practice")
    st.markdown("### Apne SQL Skills Ko Test Aur Improve Karein!")
    st.markdown("""**📌 Important Note:**\n- This quiz assumes standard **SQL syntax**...\n- Query simulation is powered by DuckDB...""")
    col1, col2 = st.columns([2, 1]); #... (rest of layout as before)
    with col1: st.write("""Is interactive quiz mein, aap do sample tables ke saath kaam karenge...""")
    with col2: st.markdown("#### Tables Overview"); table_overview_data = {"Table": list(original_tables.keys()),"Rows": [len(df) for df in original_tables.values()],"Columns": [len(df.columns) for df in original_tables.values()]}; st.dataframe(pd.DataFrame(table_overview_data), hide_index=True)
    st.write("### 🔍 Table Previews"); tab1, tab2 = st.tabs(["Users Table", "Orders Table"])
    with tab1: st.dataframe(users_table, hide_index=True)
    with tab2: st.dataframe(orders_table, hide_index=True)
    with st.expander("📝 Quiz Ke Baare Mein"): st.write(f"""- Aapko {len(sql_questions)} SQL query challenges solve karne honge...""")
    if st.button("🚀 Start SQL Challenge!"): st.session_state.quiz_started = True; st.session_state.user_answers = []; st.session_state.current_question = 0; st.session_state.quiz_completed = False; st.session_state.show_detailed_feedback = False; st.rerun()

# Define display_simulation helper function (can be defined globally)
def display_simulation(title, result_data):
    """Helper function to display simulation results (DataFrame or error)."""
    st.write(f"**{title}:**")
    if isinstance(result_data, pd.DataFrame):
        if result_data.empty:
            st.info("_(Simulation resulted in an empty table)_")
        else:
            st.dataframe(result_data.reset_index(drop=True), hide_index=True)
    elif isinstance(result_data, str) and "Simulation Error" in result_data:
        st.warning(result_data) # Show simulation errors clearly (potentially with hints)
    elif result_data == "N/A":
        st.info("_(Simulation not applicable for this query)_")
    else:
        st.error(f"_(Unexpected simulation result type: {type(result_data)})_") # More specific error

# --- Quiz In Progress ---
if st.session_state.quiz_started and not st.session_state.quiz_completed:
    st.title("✍️ SQL Query Challenge")
    # --- Display Past Answers (Chat History) ---
    if st.session_state.user_answers:
        st.markdown("---"); st.subheader("📖 Ab Tak Ke Jawaab Aur Feedback")
        for i, ans_data in enumerate(reversed(st.session_state.user_answers)):
            q_num = len(st.session_state.user_answers) - i
            with st.expander(f"Question {q_num}: {ans_data['question']} {get_emoji(ans_data.get('is_correct', False))}", expanded=False):
                st.write(f"**Aapka Jawaab:**"); st.code(ans_data.get('student_answer', '(No answer)'), language='sql')
                st.write(f"**SQL Mentor Feedback:**")
                if ans_data.get("is_correct", False): st.success(ans_data.get('feedback', 'N/A'))
                else: st.error(ans_data.get('feedback', 'N/A'))
                st.markdown("---")
                col_sim1, col_sim2 = st.columns(2)
                with col_sim1: display_simulation("Simulated Result (Aapka Query)", ans_data.get("actual_result"))
                with col_sim2: display_simulation("Simulated Result (Example Query)", ans_data.get("expected_result"))
        st.markdown("---")

    # --- Current Question ---
    # (No changes needed in logic here)
    current_q_index = st.session_state.current_question
    if current_q_index < len(sql_questions):
        question_data = sql_questions[current_q_index]; st.subheader(f"Sawaal {current_q_index + 1} / {len(sql_questions)}"); st.markdown(f"**{question_data['question']}**"); st.write("**Relevant Table(s) Preview:**")
        rel_tables = question_data.get("relevant_tables", []); #... (rest of table preview logic) ...
        if rel_tables:
            tabs = st.tabs([f"{name.capitalize()} Table" for name in rel_tables])
            for i, table_name in enumerate(rel_tables):
                with tabs[i]:
                    if table_name in original_tables: st.dataframe(original_tables[table_name], hide_index=True)
                    else: st.warning(f"Schema/Preview for '{table_name}' not found.")
        else: st.info("No specific tables indicated for preview.")
        student_answer = st.text_area("Apna SQL Query Yahaan Likhein:", key=f"answer_{current_q_index}", height=150)
        if st.button("✅ Submit Answer", key=f"submit_{current_q_index}"):
            if student_answer.strip():
                with st.spinner("AI Mentor aapka jawaab check kar raha hai..."): feedback, is_correct, expected_sim, actual_sim, llm_raw = evaluate_answer_with_llm(question_data, student_answer, original_tables)
                st.session_state.user_answers.append({"question": question_data["question"], "student_answer": student_answer, "feedback": feedback, "is_correct": is_correct, "expected_result": expected_sim, "actual_result": actual_sim, "llm_raw_output": llm_raw})
                if current_q_index < len(sql_questions) - 1: st.session_state.current_question += 1
                else: st.session_state.quiz_completed = True
                st.rerun()
            else: st.warning("Please enter your SQL query.")
        progress = (current_q_index) / len(sql_questions); st.progress(progress); st.caption(f"Question {current_q_index + 1} of {len(sql_questions)}")
    else: st.warning("Quiz state error."); st.session_state.quiz_completed = True; st.rerun()

# --- Quiz Completed Screen ---
if st.session_state.quiz_completed:
    st.balloons(); st.title("🎉 Quiz Complete!")
    score = calculate_score(st.session_state.user_answers); st.metric(label="Your Final Score", value=f"{score:.2f}%")
    st.subheader("📝 Final Review: Aapke Jawaab Aur Feedback")
    # (Review loop using display_simulation as defined above)
    for i, ans_data in enumerate(st.session_state.user_answers):
        with st.expander(f"Question {i + 1}: {ans_data['question']} {get_emoji(ans_data.get('is_correct', False))}", expanded=False):
             st.write(f"**Aapka Jawaab:**"); st.code(ans_data.get('student_answer', '(No answer)'), language='sql')
             st.write(f"**SQL Mentor Feedback:**")
             if ans_data.get("is_correct", False): st.success(ans_data.get('feedback', 'N/A'))
             else: st.error(ans_data.get('feedback', 'N/A'))
             st.markdown("---")
             col_sim1, col_sim2 = st.columns(2)
             with col_sim1: display_simulation("Simulated Result (Aapka Query)", ans_data.get("actual_result"))
             with col_sim2: display_simulation("Simulated Result (Example Query)", ans_data.get("expected_result"))
    st.markdown("---")
    # (Rest of CTA buttons and Detailed Feedback display logic remains the same)
    col_cta_1, col_cta_2 = st.columns(2)
    with col_cta_1:
        if st.button("📊 Detailed Performance Analysis"): st.session_state.show_detailed_feedback = not st.session_state.show_detailed_feedback; st.rerun()
    with col_cta_2:
        if score < 60: st.error("Score thoda kam hai..."); st.link_button("Need Help? Connect with a Mentor", "https://www.corporatebhaiya.com/", use_container_width=True)
        else: st.success("Bahut badhiya score! 👍"); st.link_button("Next Steps? Mock Interview Practice", "https://www.corporatebhaiya.com/mock-interview", use_container_width=True)
    if st.session_state.show_detailed_feedback:
        st.markdown("---"); st.subheader("📈 Detailed Performance Analysis (AI Generated)")
        with st.spinner("AI performance summary generate kar raha hai..."): performance_feedback = analyze_performance(st.session_state.user_answers)
        st.write("**Overall Feedback:**"); st.info(performance_feedback.get("overall_feedback", "Summary N/A."))
        st.write("**Strengths:**"); strengths = performance_feedback.get("strengths", [])
        if strengths: [st.success(f"{i + 1}. {q} ✅") for i, q in enumerate(strengths)]
        else: st.write("_(None correct this time.)_")
        st.write("**Areas for Improvement:**"); weaknesses = performance_feedback.get("weaknesses", [])
        if weaknesses: [st.error(f"{i + 1}. {q} ❌") for i, q in enumerate(weaknesses)]
        else: st.write("_(No incorrect answers!)_")
    st.markdown("---")
    if st.button("🔄 Restart Quiz"):
        keys_to_reset = ["user_answers", "current_question", "quiz_started","quiz_completed", "show_detailed_feedback"]
        for key in keys_to_reset:
            if key in st.session_state: del st.session_state[key]
        st.session_state.current_question = 0; st.session_state.quiz_started = False; st.rerun()
