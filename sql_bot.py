import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import duckdb # Import DuckDB

# --- Page Config ---
st.set_page_config(page_title="SQL Mentor", layout="wide", page_icon="🚀")

# --- Custom CSS ---
# (Keep existing CSS for hiding elements)
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
        /* Add custom styling for containers */
        .info-container {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
            background-color: #f9f9f9;
        }
        .quiz-container {
             border: 1px solid #e0e0e0;
             border-radius: 8px;
             padding: 20px;
             margin-bottom: 20px;
             background-color: #ffffff;
             box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
         .stTabs [data-baseweb="tab-list"] {
		gap: 24px;
        }
        .stTabs [data-baseweb="tab"] {
		height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        margin: 0;
        background-color: #F0F2F6; /* Default tab color */
		border-radius: 4px 4px 0 0;
		gap: 1px;
        border-bottom: none !important; /* Remove default bottom border */
	    }
        .stTabs [aria-selected="true"] {
  		background-color: #FFFFFF; /* Selected tab color */
        border-bottom: none !important; /* Remove border for selected */
	    }


    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Set up Gemini API ---
# WARNING: Hardcoding API keys is insecure.
gemini_api_key = "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k" # Your specific API Key
if not gemini_api_key: st.error("🚨 Gemini API Key missing."); st.stop()
try:
    genai.configure(api_key=gemini_api_key); model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e: st.error(f"🚨 Failed to configure Gemini API: {e}"); st.stop()

# --- Sample Data ---
users_table = pd.DataFrame({ "user_id": [1, 2, 3, 4], "name": ["Alice", "Bob", "Charlie", "David"], "email": ["alice@example.com", "bob@example.com", "charlie@example.com", "david@example.com"], "age": [25, 30, 35, 40], "city": ["New York", "Los Angeles", "Chicago", "Houston"] })
orders_table = pd.DataFrame({ "order_id": [101, 102, 103, 104, 105], "user_id": [1, 2, 3, 1, 4], "amount": [50.00, 75.50, 120.00, 200.00, 35.00], "order_date": pd.to_datetime(["2024-02-01", "2024-02-05", "2024-02-10", "2024-02-15", "2024-02-20"]), "status": ["Completed", "Pending", "Completed", "Shipped", "Cancelled"] })
original_tables = {"users": users_table, "orders": orders_table}

# --- SQL Questions List ---
sql_questions = [
    { "question": "Write a SQL query to get all details about users from the 'users' table.", "correct_answer_example": "SELECT * FROM users;", "sample_table": users_table, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to count the total number of users in the 'users' table.", "correct_answer_example": "SELECT COUNT(*) AS user_count FROM users;", "sample_table": users_table, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to get all users older than 30 from the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE age > 30;", "sample_table": users_table, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to find all orders with a status of 'Pending' from the 'orders' table.", "correct_answer_example": "SELECT * FROM orders WHERE status = 'Pending';", "sample_table": orders_table, "relevant_tables": ["orders"] },
    { "question": "Write a SQL query to find the most recent order from the 'orders' table by order date.", "correct_answer_example": "SELECT * FROM orders ORDER BY order_date DESC LIMIT 1;", "sample_table": orders_table, "relevant_tables": ["orders"] },
    { "question": "Write a SQL query to find the average order amount from the 'orders' table.", "correct_answer_example": "SELECT AVG(amount) AS average_amount FROM orders;", "sample_table": orders_table, "relevant_tables": ["orders"] },
    { "question": "Write a SQL query to find users who have not placed any orders. Use the 'users' and 'orders' tables.", "correct_answer_example": "SELECT u.* FROM users u LEFT JOIN orders o ON u.user_id = o.user_id WHERE o.order_id IS NULL;", "sample_table": users_table, "relevant_tables": ["users", "orders"] },
    { "question": "Write a SQL query to calculate the total amount spent by each user by joining the 'users' and 'orders' tables.", "correct_answer_example": "SELECT u.name, SUM(o.amount) AS total_spent FROM users u JOIN orders o ON u.user_id = o.user_id GROUP BY u.name ORDER BY u.name;", "sample_table": users_table, "relevant_tables": ["users", "orders"] },
    { "question": "Write a SQL query to count how many orders each user has placed using a LEFT JOIN between 'users' and 'orders'. Include users with zero orders.", "correct_answer_example": "SELECT u.name, COUNT(o.order_id) AS order_count FROM users u LEFT JOIN orders o ON u.user_id = o.user_id GROUP BY u.name ORDER BY u.name;", "sample_table": users_table, "relevant_tables": ["users", "orders"] },
    { "question": "Write a SQL query to find users from 'New York' or 'Chicago' in the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE city IN ('New York', 'Chicago');", "sample_table": users_table, "relevant_tables": ["users"] }
]

# --- Session State Initialization ---
# (No changes needed)
if "user_answers" not in st.session_state: st.session_state.user_answers = []
if "current_question" not in st.session_state: st.session_state.current_question = 0
if "quiz_started" not in st.session_state: st.session_state.quiz_started = False
if "quiz_completed" not in st.session_state: st.session_state.quiz_completed = False
if "show_detailed_feedback" not in st.session_state: st.session_state.show_detailed_feedback = False

# --- Helper Functions ---
# (No changes needed in backend functions: simulate_query_duckdb, get_table_schema, evaluate_answer_with_llm, calculate_score, analyze_performance, get_emoji)

def simulate_query_duckdb(sql_query, tables_dict):
    if not sql_query or not sql_query.strip(): return "Simulation Error: No query provided."
    if not tables_dict: return "Simulation Error: No tables provided."
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
        try: # Add hint for double quote errors
            e_str = str(e).lower(); binder_match = re.search(r'(binder error|catalog error|parser error).*referenced column "([^"]+)" not found', e_str); syntax_match = re.search(r'syntax error.*at or near ""([^"]+)""', e_str)
            if binder_match: error_message += f"\n\n**Hint:** Use single quotes (') for text values like `'{binder_match.group(2)}'` instead of double quotes (\")."
            elif syntax_match: error_message += f"\n\n**Hint:** Use single quotes (') for text values like `'{syntax_match.group(1)}'` instead of double quotes (\")."
        except Exception as e_hint: print(f"Error generating hint: {e_hint}")
        print(f"ERROR [simulate_query_duckdb]: {error_message}\nQuery: {sql_query}");
        if con:
            try: con.close()
            except: pass
        return error_message

def get_table_schema(table_name, tables_dict):
    if table_name in tables_dict and isinstance(tables_dict[table_name], pd.DataFrame): return tables_dict[table_name].columns.astype(str).tolist()
    return []

def evaluate_answer_with_llm(question_data, student_answer, original_tables_dict):
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
    prompt = f"""
    You are an expert SQL evaluator acting as a friendly SQL mentor. Your response MUST be in **English**. Analyze the student's SQL query based on the question asked and the provided table schemas (including data types). Assume standard SQL syntax (like MySQL/PostgreSQL). **Do NOT use Hindi.**
    **Evaluation Task:** ... [Rest of prompt as defined before] ...
    **Begin Evaluation (Respond ONLY in English):**
    """
    feedback_llm = "AI feedback failed."; is_correct_llm = False; llm_output = "Error: No LLM response."
    try:
        response = model.generate_content(prompt);
        if response.parts: llm_output = "".join(part.text for part in response.parts)
        else: llm_output = response.text
        llm_output = llm_output.strip(); verdict_match = re.search(r'^Verdict:\s*(Correct|Incorrect)\s*$', llm_output, re.M | re.I)
        if verdict_match: is_correct_llm = (verdict_match.group(1).lower() == "correct"); feedback_llm = llm_output[:verdict_match.start()].strip()
        else: st.warning(f"⚠️ Could not parse AI verdict."); print(f"WARNING: Could not parse verdict:\n{llm_output}"); feedback_llm = llm_output + "\n\n_(System Note: Correctness check failed.)_"; is_correct_llm = False
    except Exception as e: st.error(f"🚨 AI Error: {e}"); print(f"ERROR: Gemini call: {e}"); feedback_llm = f"AI feedback error: {e}"; is_correct_llm = False; llm_output = f"Error: {e}"
    actual_result_sim = simulate_query_duckdb(student_answer, original_tables)
    expected_result_sim = simulate_query_duckdb(correct_answer_example, original_tables)
    return feedback_llm, is_correct_llm, expected_result_sim, actual_result_sim, llm_output

def calculate_score(user_answers):
    if not user_answers: return 0
    correct = sum(1 for ans in user_answers if ans.get("is_correct", False))
    total = len(user_answers)
    return (correct / total) * 100 if total > 0 else 0

def analyze_performance(user_answers):
    performance_data = { "strengths": [], "weaknesses": [], "overall_feedback": "Analysis could not be completed." }
    if not user_answers: performance_data["overall_feedback"] = "No answers were submitted."; return performance_data
    try:
        correct_q = [ans["question"] for ans in user_answers if ans.get("is_correct")]
        incorrect_ans = [{"question": ans["question"], "your_answer": ans["student_answer"], "feedback_received": ans.get("feedback", "N/A")} for ans in user_answers if not ans.get("is_correct")]
        performance_data["strengths"] = correct_q; performance_data["weaknesses"] = [item["question"] for item in incorrect_ans]
        total_q, correct_c, score = len(user_answers), len(correct_q), calculate_score(user_answers)
        incorrect_sum = "\n".join([ f"  Q: {item['question']}\n    Your Answer: {item['your_answer']}\n    Feedback: {item['feedback_received']}\n" for item in incorrect_ans]).strip() if incorrect_ans else "  None! Great job!"
        prompt = f"""
        A student took an SQL quiz. Here's their performance summary: ... [Rest of prompt as defined before] ...
        Task: Provide an overall performance summary feedback in **English**...
        """
    except Exception as data_prep_error: print(f"Error preparing data for analysis: {data_prep_error}"); performance_data["overall_feedback"] = f"Analysis prep failed: {data_prep_error}"; return performance_data
    try:
        response = model.generate_content(prompt); generated_feedback = None
        if response.parts: generated_feedback = "".join(part.text for part in response.parts).strip()
        elif hasattr(response, 'text'): generated_feedback = response.text.strip()
        if generated_feedback: performance_data["overall_feedback"] = generated_feedback
        else: performance_data["overall_feedback"] = "AI response format unclear."; print(f"Warning: Unexpected LLM response.")
    except Exception as e: print(f"Error generating performance summary: {e}"); performance_data["overall_feedback"] = f"Could not generate performance summary: {e}"
    return performance_data

def get_emoji(is_correct): return "✅" if is_correct else "❌"

def display_simulation(title, result_data):
    st.write(f"**{title}:**")
    if isinstance(result_data, pd.DataFrame):
        if result_data.empty: st.info("_(Simulation resulted in an empty table)_")
        else: st.dataframe(result_data.reset_index(drop=True), hide_index=True, use_container_width=True)
    elif isinstance(result_data, str) and "Simulation Error" in result_data: st.warning(result_data, icon="⚠️")
    elif result_data == "N/A": st.info("_(Simulation not applicable)_")
    else: st.error(f"_(Unexpected simulation result type: {type(result_data)})_")

# --- Streamlit App ---

# --- Start Screen --- # ENHANCED UI
if not st.session_state.quiz_started:
    st.title("🚀 SQL Mentor")
    st.subheader("Test and Improve Your SQL Querying Skills")

    st.markdown("---") # Divider

    st.markdown("""
    Welcome! This interactive quiz will challenge you with various SQL tasks using sample `users` and `orders` tables.
    Your queries will be evaluated by an AI mentor providing instant feedback.
    """)

    # Use markdown with HTML for bordered containers
    st.markdown('<div class="info-container"><strong>📌 Important Note:</strong> Standard SQL syntax (MySQL/PostgreSQL like) is expected. Query simulation uses DuckDB.</div>', unsafe_allow_html=True)

    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.markdown('<div class="info-container"><h4>📊 Table Overview</h4></div>', unsafe_allow_html=True)
        table_overview_data = {"Table": list(original_tables.keys()), "Rows": [len(df) for df in original_tables.values()], "Columns": [len(df.columns) for df in original_tables.values()]}
        st.dataframe(pd.DataFrame(table_overview_data), hide_index=True, use_container_width=True)

    with col_info2:
        st.markdown('<div class="info-container"><h4>📝 About This Quiz</h4></div>', unsafe_allow_html=True)
        st.markdown(f"""
        * Solve {len(sql_questions)} SQL challenges.
        * Test different concepts.
        * Get instant AI feedback.
        * View score & analysis at the end.
        """)

    st.markdown("---") # Divider

    st.subheader("🔍 Table Previews")
    tab1, tab2 = st.tabs(["Users Table", "Orders Table"])
    with tab1:
        st.caption("Contains user details like ID, name, email, age, and city.")
        st.dataframe(users_table, hide_index=True, use_container_width=True)
    with tab2:
        st.caption("Stores order details including ID, user ID, amount, order date, and status.")
        st.dataframe(orders_table, hide_index=True, use_container_width=True)

    st.markdown("---") # Divider

    # Centered Start Button
    _, center_col, _ = st.columns([1, 1.5, 1]) # Adjust ratio as needed
    with center_col:
        if st.button("🚀 Start SQL Challenge!", use_container_width=True, type="primary"):
            st.session_state.quiz_started = True; st.session_state.user_answers = []; st.session_state.current_question = 0; st.session_state.quiz_completed = False; st.session_state.show_detailed_feedback = False; st.rerun()


# --- Quiz In Progress ---
elif st.session_state.quiz_started and not st.session_state.quiz_completed:
    st.title("✍️ SQL Query Challenge")

    # Wrap current question/input in a container
    with st.container(border=True): # Use border=True for newer Streamlit versions
        current_q_index = st.session_state.current_question
        if current_q_index < len(sql_questions):
            question_data = sql_questions[current_q_index]
            st.subheader(f"Question {current_q_index + 1} / {len(sql_questions)}")
            st.markdown(f"**{question_data['question']}**")
            st.write("**Relevant Table(s) Preview:**")
            rel_tables = question_data.get("relevant_tables", []);
            if rel_tables:
                tabs = st.tabs([f"{name.capitalize()} Table" for name in rel_tables]);
                for i, table_name in enumerate(rel_tables):
                    with tabs[i]:
                        if table_name in original_tables: st.dataframe(original_tables[table_name], hide_index=True, use_container_width=True)
                        else: st.warning(f"Schema/Preview error '{table_name}'.")
            else: st.info("No specific tables for preview.")

            student_answer = st.text_area("Enter Your SQL Query Here:", key=f"answer_{current_q_index}", height=150, label_visibility="collapsed", placeholder="SELECT column FROM table WHERE condition...")
            # Submit button aligned below text area
            submit_col, _, prog_col = st.columns([1,2,1])
            with submit_col:
                submit_pressed = st.button("✅ Submit Answer", key=f"submit_{current_q_index}", use_container_width=True)

            if submit_pressed:
                if student_answer.strip():
                    # Using st.status for a cleaner loading indicator
                    with st.spinner("AI Mentor is checking your answer..."): # Keep spinner for immediate feedback
                         feedback, is_correct, expected_sim, actual_sim, llm_raw = evaluate_answer_with_llm(question_data, student_answer, original_tables)
                    st.session_state.user_answers.append({"question": question_data["question"], "student_answer": student_answer, "feedback": feedback, "is_correct": is_correct, "expected_result": expected_sim, "actual_result": actual_sim, "llm_raw_output": llm_raw})
                    if current_q_index < len(sql_questions) - 1: st.session_state.current_question += 1
                    else: st.session_state.quiz_completed = True
                    st.rerun() # Rerun to show updated history/feedback/next question
                else: st.warning("Please enter your SQL query.")

            # Progress Bar aligned
            with prog_col:
                 st.progress((current_q_index) / len(sql_questions))
                 st.caption(f"Question {current_q_index + 1} of {len(sql_questions)}")

        else: st.warning("Quiz state error."); st.session_state.quiz_completed = True; st.rerun()

    st.divider() # Divider before history

    # --- Display Past Answers (Chat History) ---
    if st.session_state.user_answers:
        st.subheader("📖 Answer History & Feedback")
        for i, ans_data in enumerate(reversed(st.session_state.user_answers)):
            q_num = len(st.session_state.user_answers) - i;
            with st.expander(f"Question {q_num}: {ans_data['question']} {get_emoji(ans_data.get('is_correct', False))}", expanded=(i==0)): # Expand most recent
                st.write(f"**Your Answer:**"); st.code(ans_data.get('student_answer', '(No answer)'), language='sql'); st.write(f"**SQL Mentor Feedback:**");
                if ans_data.get("is_correct", False): st.success(ans_data.get('feedback', 'N/A'))
                else: st.error(ans_data.get('feedback', 'N/A'));
                st.markdown("---")
                display_simulation("Simulated Result (Your Query)", ans_data.get("actual_result"))
                st.divider()
                display_simulation("Simulated Result (Example Query)", ans_data.get("expected_result"))
        st.markdown("---")


# --- Quiz Completed Screen --- # ENHANCED UI
elif st.session_state.quiz_completed:
    st.balloons(); st.title("🎉 Quiz Complete!")
    score = calculate_score(st.session_state.user_answers)

    # Score and Summary Message Side-by-side
    score_col, summary_col = st.columns([1, 2])
    with score_col:
        st.metric(label="Your Final Score", value=f"{score:.1f}%") # Format score within metric for consistency

    with summary_col:
        if score >= 80:
            st.markdown("🏆 **Excellent Work!** You have a strong grasp of SQL concepts.")
        elif score >= 60:
            st.markdown("👍 **Good Job!** You're doing well, keep practicing the tricky areas.")
        else:
            st.markdown("💪 **Keep Practicing!** Every attempt helps you learn. Check the analysis below.")

    st.divider()

    # Detailed Analysis in Tabs
    st.subheader("📈 Detailed Performance Analysis")
    analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs(["Overall Summary", "✅ Strengths", "❌ Areas for Improvement"])

    # Generate analysis data once
    with st.spinner("Generating AI performance summary..."):
        performance_feedback = analyze_performance(st.session_state.user_answers)

    with analysis_tab1:
        st.info(performance_feedback.get("overall_feedback", "Summary not available."))

    with analysis_tab2:
        strengths = performance_feedback.get("strengths", []);
        if strengths:
             st.markdown("Questions you answered correctly:")
             for i, q in enumerate(strengths): st.markdown(f"<div style='margin: 5px 0; padding: 8px; background-color: #e8f5e9; border-left: 5px solid #4CAF50;'>{i + 1}. {q}</div>", unsafe_allow_html=True)
        else: st.write("_(None correct this time. Review the feedback below!)_")

    with analysis_tab3:
         weaknesses = performance_feedback.get("weaknesses", []);
         if weaknesses:
             st.markdown("Questions you might want to review:")
             for i, q in enumerate(weaknesses): st.markdown(f"<div style='margin: 5px 0; padding: 8px; background-color: #ffebee; border-left: 5px solid #f44336;'>{i + 1}. {q}</div>", unsafe_allow_html=True)
         else: st.write("_(No incorrect answers! Well done!)_")

    st.divider()

    # Final Review Section (Expanders)
    st.subheader("📝 Final Review: Your Answers & Feedback")
    for i, ans_data in enumerate(st.session_state.user_answers):
        with st.expander(f"Question {i + 1}: {ans_data['question']} {get_emoji(ans_data.get('is_correct', False))}", expanded=False):
             st.write(f"**Your Answer:**"); st.code(ans_data.get('student_answer', '(No answer)'), language='sql'); st.write(f"**SQL Mentor Feedback:**");
             if ans_data.get("is_correct", False): st.success(ans_data.get('feedback', 'N/A'))
             else: st.error(ans_data.get('feedback', 'N/A'));
             st.markdown("---")
             display_simulation("Simulated Result (Your Query)", ans_data.get("actual_result"))
             st.divider()
             display_simulation("Simulated Result (Example Query)", ans_data.get("expected_result"))

    st.divider()

    # CTA and Restart
    st.subheader("Next Steps")
    cta_col1, cta_col2, cta_col3 = st.columns([1.5, 1.5, 1])
    with cta_col1:
        st.link_button("🔗 Need Help? Connect with a Mentor", "https://www.corporatebhaiya.com/", use_container_width=True)
    with cta_col2:
        st.link_button("🎓 Prepare for Interviews", "https://www.corporatebhaiya.com/mock-interview", use_container_width=True)
    with cta_col3:
        if st.button("🔄 Restart Quiz", use_container_width=True):
            keys_to_reset = ["user_answers", "current_question", "quiz_started","quiz_completed", "show_detailed_feedback"]
            for key in keys_to_reset:
                if key in st.session_state: del st.session_state[key]
            st.session_state.current_question = 0; st.session_state.quiz_started = False; st.rerun()


# Fallback if state is somehow invalid
else:
    st.error("An unexpected error occurred. Please restart.")
    if st.button("Force Restart App State"):
         keys_to_reset = ["user_answers", "current_question", "quiz_started","quiz_completed", "show_detailed_feedback"]
         for key in keys_to_reset:
             if key in st.session_state: del st.session_state[key]
         st.session_state.current_question = 0; st.session_state.quiz_started = False; st.rerun()
