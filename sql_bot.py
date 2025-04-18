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
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Set up Gemini API ---
gemini_api_key = "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k"

if not gemini_api_key:
    st.error("🚨 Gemini API Key is missing in the code.")
    st.stop()

try:
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"🚨 Failed to configure Gemini API or access the model: {e}")
    st.stop()

# --- Sample Data (All Lowercase) ---
users_table = pd.DataFrame({
    "user_id": [1, 2, 3, 4],
    "name": ["alice", "bob", "charlie", "david"],  # Lowercase
    "email": ["alice@example.com", "bob@example.com", "charlie@example.com", "david@example.com"],
    "age": [25, 30, 35, 40],
    "city": ["new york", "los angeles", "chicago", "houston"]
})

orders_table = pd.DataFrame({
    "order_id": [101, 102, 103, 104, 105],
    "user_id": [1, 2, 3, 1, 4],
    "amount": [50.00, 75.50, 120.00, 200.00, 35.00],
    "order_date": pd.to_datetime(["2024-02-01", "2024-02-05", "2024-02-10", "2024-02-15", "2024-02-20"]),
    "status": ["completed", "pending", "completed", "shipped", "cancelled"]
})

original_tables = {
    "users": users_table,
    "orders": orders_table
}

# --- SQL Questions List ---
# --- SQL Questions List ---
sql_questions = [
    { "question": "Write a SQL query to get all details about users from the 'users' table.", "correct_answer_example": "SELECT * FROM users;", "sample_table": users_table, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to count the total number of users in the 'users' table.", "correct_answer_example": "SELECT COUNT(*) AS user_count FROM users;", "sample_table": users_table, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to get all users older than 30 from the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE age > 30;", "sample_table": users_table, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to find all orders with a status of 'Pending' from the 'orders' table.", "correct_answer_example": "SELECT * FROM orders WHERE status = 'Pending';", "sample_table": orders_table, "relevant_tables": ["orders"] },
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




# --- Helper Functions (Updated) ---
def normalize_sql_case(sql_query):
    """Normalize SQL case for case-insensitive execution"""
    # Convert string literals to lowercase
    sql_query = re.sub(r"'((?:[^']|'')*)'", 
                     lambda m: f"'{m.group(1).lower()}'", 
                     sql_query, 
                     flags=re.IGNORECASE)
    
    # Convert column/table names to lowercase (basic handling)
    sql_query = re.sub(r'\b([A-Z_]+)\b(?=(?:[^"]*"[^"]*")*[^"]*$)', 
                     lambda m: m.group(1).lower(), 
                     sql_query, 
                     flags=re.IGNORECASE)
    
    return sql_query

def prepare_case_insensitive_data(tables_dict):
    """Prepare lowercase version of all data"""
    lower_tables = {}
    for name, df in tables_dict.items():
        if isinstance(df, pd.DataFrame):
            # Lowercase column names
            df_lower = df.rename(columns=str.lower)
            # Lowercase string columns
            for col in df_lower.select_dtypes(include=['object']).columns:
                df_lower[col] = df_lower[col].str.lower()
            lower_tables[name] = df_lower
    return lower_tables

def simulate_query_duckdb(sql_query, tables_dict):
    """Case-insensitive SQL execution with proper data handling"""
    if not sql_query.strip():
        return "Simulation Error: Empty query"
    
    try:
        # Normalize query case
        modified_query = normalize_sql_case(sql_query)
        
        # Prepare case-insensitive data
        lower_tables = prepare_case_insensitive_data(tables_dict)
        
        # Execute query
        con = duckdb.connect(database=':memory:')
        for table_name, df in lower_tables.items():
            con.register(table_name, df)
            
        result_df = con.execute(modified_query).df()
        con.close()
        return result_df
        
    except Exception as e:
        return f"Simulation Error: {str(e)}"

# --- Rest of the Functions ---
# ... (keep evaluate_answer_with_llm, analyze_performance, 
#      display_simulation etc. same as previous version)

# --- Streamlit UI Components ---
# ... (keep all UI code the same as before)

def get_table_schema(table_name, tables_dict):
    """Gets column names for a given table name."""
    if table_name in tables_dict and isinstance(tables_dict[table_name], pd.DataFrame):
        return tables_dict[table_name].columns.astype(str).tolist()
    return []

def evaluate_answer_with_llm(question_data, student_answer, original_tables_dict):
    """Evaluate the user's answer using Gemini API and simulate using DuckDB."""
    if not student_answer.strip(): return "Please provide an answer.", False, "N/A", "N/A", "No input."
    
    question = question_data["question"]
    relevant_table_names = question_data["relevant_tables"]
    correct_answer_example = question_data["correct_answer_example"]
    
    schema_info = ""
    for name in relevant_table_names:
        columns = get_table_schema(name, original_tables_dict)
        if columns:
            try: 
                df = original_tables_dict[name]
                dtypes = df.dtypes.to_string() if isinstance(df, pd.DataFrame) else "N/A"
                schema_info += f"Table '{name}': Columns {columns}\nData Types:\n{dtypes}\n\n"
            except Exception as e_schema: 
                schema_info += f"Table '{name}': Columns {columns} (Schema Error: {e_schema})\n\n"
        else: 
            schema_info += f"Table '{name}': Schema not found.\n"

    prompt = f"""
    You are an expert SQL evaluator acting as a friendly SQL mentor. Analyze the student's SQL query based on the question asked and the provided table schemas. Assume standard SQL syntax.

    **Evaluation Task:**
    1. **Question:** {question}
    2. **Relevant Table Schemas:**\n{schema_info.strip()}
    3. **Student's SQL Query:**\n```sql\n{student_answer}\n```

    **Analysis Instructions:**
    * Consider case-insensitive string comparisons as valid
    * Allow different but equivalent syntax (e.g., JOIN vs WHERE clause joins)
    * Focus on logical correctness rather than exact syntax matching
    * Provide feedback in casual Hindi
    * End with "Verdict: Correct" or "Verdict: Incorrect"
    """

    feedback_llm = "AI feedback failed."
    is_correct_llm = False
    try:
        response = model.generate_content(prompt)
        llm_output = response.text.strip()
        verdict_match = re.search(r'Verdict:\s*(Correct|Incorrect)', llm_output, re.IGNORECASE)
        
        if verdict_match:
            is_correct_llm = verdict_match.group(1).lower() == 'correct'
            feedback_llm = llm_output[:verdict_match.start()].strip()
        else:
            feedback_llm = llm_output + "\n\n(Sistem Note: Could not determine correctness)"
            
    except Exception as e:
        feedback_llm = f"AI feedback error: {e}"
    
    actual_result_sim = simulate_query_duckdb(student_answer, original_tables)
    expected_result_sim = simulate_query_duckdb(correct_answer_example, original_tables)
    
    return feedback_llm, is_correct_llm, expected_result_sim, actual_result_sim, llm_output

# ... (Rest of the code remains the same from the original version, including UI components and display functions)

# --- Streamlit App Components (Unchanged UI Code) ---
# [Keep all the remaining code from the original version including:
# - calculate_score()
# - analyze_performance()
# - get_emoji()
# - display_simulation()
# - All the Streamlit UI components
# - State management
# - Progress tracking
# - Result display logic]

# Note: The rest of the code (UI components and display functions) remains exactly the same as in the original version provided.

def calculate_score(user_answers):
    """Calculate the score based on correct answers."""
    if not user_answers: return 0
    correct = sum(1 for ans in user_answers if ans.get("is_correct", False))
    total = len(user_answers)
    return (correct / total) * 100 if total > 0 else 0

def analyze_performance(user_answers):
    """Analyze the user's performance and provide detailed feedback via LLM."""
    # [analyze_performance function remains the same as the last working version]
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
        st.warning(result_data, icon="⚠️")
    elif result_data == "N/A":
        st.info("_(Simulation not applicable)_")
    else:
        st.error(f"_(Unexpected simulation result type: {type(result_data)})_")

# --- Streamlit App ---

# --- Start Screen --- # CORRECTED FORMATTING
if not st.session_state.quiz_started:
    st.title("🚀 SQL Mentor - Interactive SQL Practice")
    st.markdown("### Apne SQL Skills Ko Test Aur Improve Karein!")
    st.markdown("""
        **📌 Important Note:**
        - This quiz assumes standard **SQL syntax** (similar to MySQL/PostgreSQL).
        - Your queries will be evaluated by an AI for correctness and logic.
        - Query simulation is powered by DuckDB to show results based on sample data.
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
        table_overview_data = {"Table": list(original_tables.keys()), "Rows": [len(df) for df in original_tables.values()], "Columns": [len(df.columns) for df in original_tables.values()]}
        st.dataframe(pd.DataFrame(table_overview_data), hide_index=True)
    st.write("### 🔍 Table Previews"); tab1, tab2 = st.tabs(["Users Table", "Orders Table"])
    with tab1: st.dataframe(users_table, hide_index=True, use_container_width=True) # Added use_container_width
    with tab2: st.dataframe(orders_table, hide_index=True, use_container_width=True) # Added use_container_width
    with st.expander("📝 Quiz Ke Baare Mein"):
        st.write(f"""
        - Aapko {len(sql_questions)} SQL query challenges solve karne honge...
        - Har jawaab ke baad AI Mentor se immediate feedback milega...
        - **SQL Dialect Focus:** Standard SQL (MySQL/PostgreSQL like)
        """)
    if st.button("🚀 Start SQL Challenge!"):
        st.session_state.quiz_started = True; st.session_state.user_answers = []; st.session_state.current_question = 0; st.session_state.quiz_completed = False; st.session_state.show_detailed_feedback = False; st.rerun()

# --- Quiz In Progress ---
elif st.session_state.quiz_started and not st.session_state.quiz_completed:
    st.title("✍️ SQL Query Challenge")
    if st.session_state.user_answers:
        st.markdown("---"); st.subheader("📖 Ab Tak Ke Jawaab Aur Feedback")
        for i, ans_data in enumerate(reversed(st.session_state.user_answers)):
            q_num = len(st.session_state.user_answers) - i;
            with st.expander(f"Question {q_num}: {ans_data['question']} {get_emoji(ans_data.get('is_correct', False))}", expanded=False):
                st.write(f"**Aapka Jawaab:**"); st.code(ans_data.get('student_answer', '(No answer)'), language='sql'); st.write(f"**SQL Mentor Feedback:**");
                if ans_data.get("is_correct", False): st.success(ans_data.get('feedback', 'N/A'))
                else: st.error(ans_data.get('feedback', 'N/A'));

                # --- CORRECTED: Display tables vertically ---
                st.markdown("---") # Separator before tables
                display_simulation("Simulated Result (User Output)", ans_data.get("actual_result"))
                st.divider() # Optional: Add a visual divider between the two tables
                display_simulation("Simulated Result (Expected Output)", ans_data.get("expected_result"))
                # --- END CORRECTION ---
        st.markdown("---")
    # --- Current Question ---
    current_q_index = st.session_state.current_question
    if current_q_index < len(sql_questions):
        question_data = sql_questions[current_q_index]; st.subheader(f"Question {current_q_index + 1} / {len(sql_questions)}"); st.markdown(f"**{question_data['question']}**"); st.write("****");
        rel_tables = question_data.get("relevant_tables", []);
        if rel_tables:
            tabs = st.tabs([f"{name.capitalize()} Table" for name in rel_tables]);
            for i, table_name in enumerate(rel_tables):
                with tabs[i]:
                    if table_name in original_tables: st.dataframe(original_tables[table_name], hide_index=True, use_container_width=True) # Added use_container_width
                    else: st.warning(f"Schema/Preview error '{table_name}'.")
        else: st.info("No specific tables for preview.")
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
elif st.session_state.quiz_completed:
    st.balloons(); st.title("🎉 Quiz Complete!")
    score = calculate_score(st.session_state.user_answers)
    st.metric(label="Your Final Score (%)", value=score)
    st.subheader("📝 Final Review: Aapke Jawaab Aur Feedback")
    for i, ans_data in enumerate(st.session_state.user_answers):
        with st.expander(f"Question {i + 1}: {ans_data['question']} {get_emoji(ans_data.get('is_correct', False))}", expanded=False):
             st.write(f"**Aapka Jawaab:**"); st.code(ans_data.get('student_answer', '(No answer)'), language='sql'); st.write(f"**SQL Mentor Feedback:**");
             if ans_data.get("is_correct", False): st.success(ans_data.get('feedback', 'N/A'))
             else: st.error(ans_data.get('feedback', 'N/A'));

             # --- CORRECTED: Display tables vertically ---
             st.markdown("---") # Separator before tables
             display_simulation("Simulated Result (Aapka Query)", ans_data.get("actual_result"))
             st.divider() # Optional: Add a visual divider between the two tables
             display_simulation("Simulated Result (Example Query)", ans_data.get("expected_result"))
             # --- END CORRECTION ---
    st.markdown("---")
    col_cta_1, col_cta_2 = st.columns(2)
    with col_cta_1:
        if st.button("📊 Detailed Performance Analysis"): st.session_state.show_detailed_feedback = not st.session_state.show_detailed_feedback; st.rerun()
    with col_cta_2:
        if score < 60: st.error("Score thoda kam hai..."); st.link_button("Need Help? Connect with a Mentor", "https://www.corporatebhaiya.com/", use_container_width=True)
        else: st.success("Bahut badhiya score! 👍"); st.link_button("Next Steps? Mock Interview Practice", "https://www.corporatebhaiya.com/mock-interview", use_container_width=True)

    # --- Detailed Feedback Section --- # CORRECTED LOOPS
    if st.session_state.show_detailed_feedback:
        st.markdown("---"); st.subheader("📈 Detailed Performance Analysis (AI Generated)")
        with st.spinner("AI performance summary generate kar raha hai..."):
            performance_feedback = analyze_performance(st.session_state.user_answers)
        st.write("**Overall Feedback:**"); st.info(performance_feedback.get("overall_feedback", "Summary N/A."))
        st.write("**Strengths (Questions answered correctly):**");
        strengths = performance_feedback.get("strengths", []);
        if strengths:
            for i, q in enumerate(strengths): st.success(f"{i + 1}. {q} ✅") # Use standard loop
        else: st.write("_(None correct this time.)_")
        st.write("**Areas for Improvement (Questions answered incorrectly):**");
        weaknesses = performance_feedback.get("weaknesses", []);
        if weaknesses:
            for i, q in enumerate(weaknesses): st.error(f"{i + 1}. {q} ❌") # Use standard loop
        else: st.write("_(No incorrect answers!)_")
    st.markdown("---")
    if st.button("🔄 Restart Quiz"):
        keys_to_reset = ["user_answers", "current_question", "quiz_started","quiz_completed", "show_detailed_feedback"]
        for key in keys_to_reset:
            if key in st.session_state: del st.session_state[key]
        st.session_state.current_question = 0; st.session_state.quiz_started = False; st.rerun()

# Fallback if state is somehow invalid
else:
    st.error("An unexpected error occurred with the application state. Please restart.")
    if st.button("Force Restart App State"):
         keys_to_reset = ["user_answers", "current_question", "quiz_started","quiz_completed", "show_detailed_feedback"]
         for key in keys_to_reset:
             if key in st.session_state: del st.session_state[key]
         st.session_state.current_question = 0; st.session_state.quiz_started = False; st.rerun()



