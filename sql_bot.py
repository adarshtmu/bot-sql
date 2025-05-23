import streamlit as st
import google.generativeai as genai
import pandas as pd
import re # Needed for regex query modification
import duckdb # Import DuckDB

# --- Page Configuration (Set it as the first Streamlit command) ---
st.set_page_config(layout="wide", page_title="SQL Mentor", page_icon="🚀")

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
        
        /* Style for the main Start SQL Challenge! button */
        button[kind="primary"].stButton > button { /* Be more specific to target Streamlit's button */
            font-size: 30px !important; /* Adjusted for better proportion */
            padding: 18px 24px !important;
            color: white !important;
            background-color: #FF4B4B !important; /* Streamlit's red */
            border-radius: 10px !important;
            border: none !important;
        }
        button[kind="primary"].stButton > button:hover {
            background-color: #FF6B6B !important;
        }

        /* Add some padding to containers with border */
        .st-emotion-cache-1ih91yr, [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > .element-container > .stMarkdown, .stApp [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] > .stDeck > [data-testid="stVerticalBlock"] {
             padding: 0.5rem; /* Add some padding around elements in horizontal blocks */
        }
        div[data-testid="stExpander"] div[role="button"] > div { /* Style expander header */
            font-size: 1.1rem;
            font-weight: bold;
        }

    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Set up Gemini API ---
gemini_api_key = "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k" # <--- IMPORTANT: PASTE YOUR GEMINI API KEY HERE

if not gemini_api_key or gemini_api_key == "YOUR_API_KEY_HERE":
    st.error("🚨 Gemini API Key is missing. Please add your key in the code.")
    st.stop()

try:
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"🚨 Failed to configure Gemini API or access the model: {e}")
    st.stop()

# --- Sample Data ---
users_table = pd.DataFrame({
    "user_id": [1, 2, 3, 4], "name": ["Alice", "Bob", "Charlie", "David"],
    "email": ["alice@example.com", "bob@example.com", "charlie@example.com", "david@example.com"],
    "age": [25, 30, 35, 40], "city": ["New York", "Los Angeles", "Chicago", "Houston"]
})
orders_table = pd.DataFrame({
    "order_id": [101, 102, 103, 104, 105], "user_id": [1, 2, 3, 1, 4],
    "amount": [50.00, 75.50, 120.00, 200.00, 35.00],
    "order_date": pd.to_datetime(["2024-02-01", "2024-02-05", "2024-02-10", "2024-02-15", "2024-02-20"]),
    "status": ["Completed", "Pending", "Completed", "Shipped", "Cancelled"]
})
original_tables = {"users": users_table, "orders": orders_table}

# --- SQL Questions List ---
sql_questions = [
    { "question": "Write a SQL query to get all details about users from the 'users' table.", "correct_answer_example": "SELECT * FROM users;", "sample_table": users_table, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to count the total number of users in the 'users' table.", "correct_answer_example": "SELECT COUNT(*) AS user_count FROM users;", "sample_table": users_table, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to get all users older than 30 from the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE age > 30;", "sample_table": users_table, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to find all orders with a status of 'Pending' from the 'orders' table.", "correct_answer_example": "SELECT * FROM orders WHERE status = 'Pending';", "sample_table": orders_table, "relevant_tables": ["orders"] },
    { "question": "Write a SQL query to find users from 'chicago' in the 'users' table (test case-insensitivity).", "correct_answer_example": "SELECT * FROM users WHERE city = 'Chicago';", "sample_table": users_table, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to find the most recent order from the 'orders' table by order date.", "correct_answer_example": "SELECT * FROM orders ORDER BY order_date DESC LIMIT 1;", "sample_table": orders_table, "relevant_tables": ["orders"] },
    { "question": "Write a SQL query to find the average order amount from the 'orders' table.", "correct_answer_example": "SELECT AVG(amount) AS average_amount FROM orders;", "sample_table": orders_table, "relevant_tables": ["orders"] },
    { "question": "Write a SQL query to find users from 'New York' or 'Chicago' in the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE city IN ('New York', 'Chicago');", "sample_table": users_table, "relevant_tables": ["users"] },
    { "question": "Write a SQL query to find users who have not placed any orders. Use the 'users' and 'orders' tables.", "correct_answer_example": "SELECT u.* FROM users u LEFT JOIN orders o ON u.user_id = o.user_id WHERE o.order_id IS NULL;", "sample_table": users_table, "relevant_tables": ["users", "orders"] },
    { "question": "Write a SQL query to calculate the total amount spent by each user by joining the 'users' and 'orders' tables.", "correct_answer_example": "SELECT u.name, SUM(o.amount) AS total_spent FROM users u JOIN orders o ON u.user_id = o.user_id GROUP BY u.name ORDER BY u.name;", "sample_table": users_table, "relevant_tables": ["users", "orders"] },
]

# --- Session State Initialization ---
default_session_state = {
    "user_answers": [], "current_question": 0, "quiz_started": False,
    "quiz_completed": False, "show_detailed_feedback": False,
    "show_detailed_feedback_on_completion": False
}
for key, value in default_session_state.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- Helper Functions (simulate_query_duckdb, get_table_schema, evaluate_answer_with_llm, calculate_score, analyze_performance, get_emoji, display_simulation) ---
# These functions remain largely the same as in your provided code. I'm assuming they are correct and complete.
# For brevity, I will paste them collapsed, make sure you have your full versions.

def simulate_query_duckdb(sql_query, tables_dict):
    if not sql_query or not sql_query.strip(): return "Simulation Error: No query provided."
    if not tables_dict: return "Simulation Error: No tables provided for context."
    con = None
    processed_query_for_ilike = sql_query
    try:
        double_quote_pattern = r'"([^"]*)"'
        processed_query_for_ilike = re.sub(double_quote_pattern, r"'\1'", sql_query)
    except Exception as e_quotes:
        print(f"Warning: Failed during double quote replacement: {e_quotes}.")
        processed_query_for_ilike = sql_query
    modified_sql_query = processed_query_for_ilike
    final_executed_query = modified_sql_query
    case_insensitive_columns = { "orders": ["status"], "users": ["city"] }
    try:
        for table_key, cols_to_make_insensitive in case_insensitive_columns.items():
            for col_name in cols_to_make_insensitive:
                direct_col_pattern = rf"(\b{re.escape(col_name)}\b\s*=\s*)'([^']+)'"
                aliased_col_pattern = rf"(\b\w+\.{re.escape(col_name)}\b\s*=\s*)'([^']+)'"
                modified_sql_query = re.sub(direct_col_pattern, lambda m: f"{m.group(1).replace('=', 'ILIKE ')}'{m.group(2)}'", modified_sql_query, flags=re.IGNORECASE)
                modified_sql_query = re.sub(aliased_col_pattern, lambda m: f"{m.group(1).replace('=', 'ILIKE ')}'{m.group(2)}'", modified_sql_query, flags=re.IGNORECASE)
        final_executed_query = modified_sql_query
    except Exception as e_rewrite:
        print(f"Warning: Failed to rewrite query for ILIKE: {e_rewrite}")
        final_executed_query = processed_query_for_ilike
    try:
        con = duckdb.connect(database=':memory:', read_only=False)
        for table_name, df in tables_dict.items():
            if isinstance(df, pd.DataFrame): con.register(str(table_name), df)
        result_df = con.execute(final_executed_query).df()
        con.close()
        return result_df
    except Exception as e:
        error_message = f"Simulation Error: Failed to execute query. Reason: {str(e)}"
        e_str = str(e).lower(); hint = ""
        if "ILIKE" in str(e).upper() or (modified_sql_query != processed_query_for_ilike and "syntax error" in e_str):
            hint = "\n\n**Hint:** The simulation tried using case-insensitive matching (ILIKE). Check your SQL syntax near the comparison."
        else:
            catalog_match = re.search(r'table with name "([^"]+)" does not exist', e_str)
            binder_match = re.search(r'column "([^"]+)" not found', e_str)
            syntax_match = re.search(r'syntax error at or near "([^"]+)"', e_str) or re.search(r'syntax error at end of input', e_str) or re.search(r'syntax error at:', e_str)
            if catalog_match: hint = f"\n\n**Hint:** Table '{catalog_match.group(1)}' might be misspelled. Available: {list(tables_dict.keys())}."
            elif binder_match: hint = f"\n\n**Hint:** Column '{binder_match.group(1)}' might be misspelled."
            elif syntax_match: problem_area = syntax_match.group(1) if syntax_match.groups() and syntax_match.lastindex == 1 else "indicated location"
            hint = f"\n\n**Hint:** Check SQL syntax near `{problem_area}`. Use single quotes for text (e.g., `'text'`)."
        error_message += hint if hint else "\n\n**Hint:** Double-check syntax, names, and types. Use single quotes for strings."
        if con: con.close()
        return error_message

def get_table_schema(table_name, tables_dict):
    if table_name in tables_dict and isinstance(tables_dict[table_name], pd.DataFrame):
        return tables_dict[table_name].columns.astype(str).tolist()
    return []

def evaluate_answer_with_llm(question_data, student_answer, original_tables_dict):
    if not student_answer or not student_answer.strip(): return "Please provide an answer.", False, "N/A", "N/A", "No input."
    question, relevant_table_names, correct_answer_example = question_data["question"], question_data["relevant_tables"], question_data["correct_answer_example"]
    schema_info = ""
    for name in relevant_table_names:
        columns = get_table_schema(name, original_tables_dict)
        if columns:
            try: schema_info += f"Table '{name}':\n  Columns: {columns}\n  DataTypes:\n{original_tables_dict[name].dtypes.to_string()}\n\n"
            except: schema_info += f"Table '{name}': Columns {columns} (Error getting schema details)\n\n"
        else: schema_info += f"Table '{name}': Schema not found.\n"
    prompt = f"""
    You are an expert SQL evaluator acting as a friendly SQL mentor. Analyze the student's SQL query.
    Question: {question}
    Relevant Table Schemas:\n{schema_info.strip()}
    Student's SQL Query:\n```sql\n{student_answer}\n```
    Analysis Instructions:
    * Correctness: Does the query answer the Question based on Schemas? Assume CASE-INSENSITIVE comparison for 'status' (orders) and 'city' (users) and that single or double quotes for strings are okay for this quiz. Focus on logic.
    * Validity: Is it valid SQL otherwise?
    * Logic: Correct use of clauses, joins, aggregates?
    * Feedback: Friendly, casual Hindi tone. If incorrect (for reasons other than case/quotes if logic is fine), explain gently.
    * Verdict: End with "Verdict: Correct" or "Verdict: Incorrect" on a new line.
    Begin Evaluation:
    """
    feedback_llm, is_correct_llm, llm_output = "AI feedback generation failed.", False, "Error: No LLM response."
    try:
        response = model.generate_content(prompt)
        extracted_text = getattr(response, 'text', "".join(part.text for part in getattr(response, 'parts', []) if hasattr(part, 'text')))
        if not extracted_text and hasattr(response, 'prompt_feedback'): extracted_text = f"AI Response Blocked/Empty. Prompt Feedback: {response.prompt_feedback}"
        if extracted_text:
            llm_output = extracted_text.strip()
            verdict_match = re.search(r'^Verdict:\s*(Correct|Incorrect)\s*$', llm_output, re.MULTILINE | re.IGNORECASE)
            if verdict_match:
                is_correct_llm = (verdict_match.group(1).lower() == "correct")
                feedback_llm = re.sub(r'\s*Verdict:\s*(Correct|Incorrect)?\s*$', '', llm_output[:verdict_match.start()].strip(), flags=re.MULTILINE | re.IGNORECASE).strip()
            else:
                feedback_llm = llm_output + "\n\n_(System Note: AI verdict unparsable.)_"
            feedback_llm = feedback_llm.replace("student", "aap")
    except Exception as e_call:
        feedback_llm, llm_output = f"AI feedback generation error: {e_call}", f"Error during AI call: {e_call}"
    actual_result_sim = simulate_query_duckdb(student_answer, original_tables_dict)
    expected_result_sim = simulate_query_duckdb(correct_answer_example, original_tables_dict)
    if is_correct_llm and isinstance(actual_result_sim, str) and "Simulation Error" in actual_result_sim:
        is_correct_llm = False
        feedback_llm += f"\n\n**Mentor Note:** AI initially marked correct, but your query had a simulation error: {actual_result_sim}. So, needs a fix."
    if not is_correct_llm and isinstance(actual_result_sim, pd.DataFrame) and isinstance(expected_result_sim, pd.DataFrame):
        if actual_result_sim.equals(expected_result_sim):
            is_correct_llm = True
            feedback_llm = "Waah! Aapka query bilkul sahi result de raha hai simulation mein! ✅\n\nOriginal AI Feedback (for ref):\n" + feedback_llm
    return feedback_llm, is_correct_llm, expected_result_sim, actual_result_sim, llm_output

def calculate_score(user_answers):
    if not user_answers: return 0.0
    correct_count = sum(1 for ans in user_answers if ans.get("is_correct", False))
    return (correct_count / len(sql_questions)) * 100 if sql_questions else 0.0

def analyze_performance(user_answers):
    if not user_answers and not st.session_state.quiz_completed : return {"overall_feedback": "Aapne abhi tak koi sawaal attempt nahi kiya."}
    if not user_answers and st.session_state.quiz_completed : return {"overall_feedback": "Aisa lagta hai aapne saare sawaal skip kar diye. Analysis abhi possible nahi."}
    try:
        correct_q_details = [{"question": sql_questions[ans["question_index"]]["question"]} for ans in user_answers if ans.get("is_correct")]
        incorrect_ans = [{"question": sql_questions[ans["question_index"]]["question"], "your_answer": ans["student_answer"], "feedback_received": ans.get("feedback", "N/A")} for ans in user_answers if not ans.get("is_correct")]
        total_q, correct_c, score = len(sql_questions), len(correct_q_details), calculate_score(user_answers)
        incorrect_summary = "In sawaalon mein thodi galti hui ya skip kiya:\n" + "\n".join([f"  {idx+1}. Sawaal: {item['question']}\n     Aapka Jawaab: {f'`{item["your_answer"]}`' if item['your_answer'] != 'SKIPPED' else '_SKIPPED_'}\n     Feedback: {item['feedback_received'][:100]}..." for idx, item in enumerate(incorrect_ans)]) if incorrect_ans else "Koi galat jawaab nahi! Bahut badhiya!"
        correct_summary = "Yeh sawaal bilkul sahi kiye:\n" + "\n".join([f"  - {item['question']}" for item in correct_q_details]) if correct_q_details else "Is baar koi jawaab sahi nahi hua."
        prompt = f"""
        SQL learner quiz performance analysis. Provide friendly, motivating summary in casual Hindi.
        Stats: Total Questions: {total_q}, Correct: {correct_c}, Score: {score:.2f}%
        Correctly Answered:\n{correct_summary if correct_q_details else '(Koi nahi)'}
        Incorrect/Skipped:\n{incorrect_summary if incorrect_ans else '(Koi nahi)'}
        Task: Provide overall feedback:
        1. Overall Impression: Positive/encouraging comment on score and performance.
        2. Strengths: Highlight concepts done well.
        3. Areas for Improvement: Gently point out concepts needing work. Suggest standard practices (single quotes, LOWER/UPPER) as general learning.
        4. Next Steps/Encouragement: Motivate for practice.
        Address student as "aap". Start feedback directly.
        """
        response = model.generate_content(prompt)
        generated_feedback = getattr(response, 'text', "".join(part.text for part in getattr(response, 'parts', []) if hasattr(part, 'text')))
        if not generated_feedback and hasattr(response, 'prompt_feedback'): generated_feedback = f"AI Response Blocked/Empty. Prompt Feedback: {response.prompt_feedback}"
        return {"overall_feedback": generated_feedback if generated_feedback else "AI summary generation error."}
    except Exception as e: return {"overall_feedback": f"Performance analysis error: {e}"}

def get_emoji(is_correct): return "✅" if is_correct else "❌"

def display_simulation(title, result_data):
    st.write(f"**{title}:**")
    if isinstance(result_data, pd.DataFrame):
        if result_data.empty: st.info("_(Simulation resulted in an empty table)_")
        else: st.dataframe(result_data.reset_index(drop=True), hide_index=True, use_container_width=True)
    elif isinstance(result_data, str) and "Simulation Error" in result_data: st.warning(result_data, icon="⚠️")
    elif result_data is None or result_data == "N/A": st.info("_(Simulation not applicable or no data)_")
    elif isinstance(result_data, str): st.info(f"_{result_data}_")
    else: st.error(f"_(Unexpected simulation result type: {type(result_data)})_")


# --- Streamlit App UI ---
st.sidebar.title("SQL Mentor Controls")
st.sidebar.markdown("---")

if not st.session_state.quiz_started:
    st.title("🚀 SQL Mentor - Interactive SQL Practice")
    st.markdown("### Apne SQL Skills Ko Test Aur Improve Karein!")

    with st.container(border=True):
        st.subheader("📌 Important Notes")
        st.markdown("""
        - This quiz uses **standard SQL syntax** (similar to MySQL/PostgreSQL).
        - String comparisons for `status` (in `orders`) and `city` (in `users`) are simulated to be **case-insensitive**.
        - Both **single quotes (') and double quotes (")** are accepted for string literals in this simulation.
        - Your queries are evaluated by an AI for correctness and logic.
        - Query simulation is powered by DuckDB.
        """)

    cols_info = st.columns(2)
    with cols_info[0]:
        with st.container(border=True):
            st.subheader("📝 Quiz Overview")
            st.write(f"""
            Is interactive quiz mein, aap **{len(sql_questions)} SQL challenges** solve karenge using two sample tables:
            - **Users Table**: User details.
            - **Orders Table**: Order details.
            Har jawaab ke baad AI Mentor se immediate feedback milega.
            """)
    with cols_info[1]:
        with st.container(border=True):
            st.subheader("📊 Tables at a Glance")
            col1, col2 = st.columns(2)
            col1.metric("Users Table Rows", len(users_table))
            col1.metric("Users Table Columns", len(users_table.columns))
            col2.metric("Orders Table Rows", len(orders_table))
            col2.metric("Orders Table Columns", len(orders_table.columns))
            
    with st.expander("🔍 View Table Previews", expanded=False):
        tab1, tab2 = st.tabs(["Users Table Sample", "Orders Table Sample"])
        with tab1: st.dataframe(users_table.head(), hide_index=True, use_container_width=True)
        with tab2: st.dataframe(orders_table.head(), hide_index=True, use_container_width=True)

    st.markdown("---")
    if st.button("🚀 Start SQL Challenge!", type="primary", use_container_width=True):
        st.session_state.quiz_started = True
        st.session_state.current_question = 0
        st.session_state.user_answers = []
        st.session_state.quiz_completed = False
        st.session_state.show_detailed_feedback = False
        st.session_state.show_detailed_feedback_on_completion = False
        for key in list(st.session_state.keys()): # Clear dynamic states
            if key.startswith("query_input_") or key.startswith("answer_feedback_"):
                del st.session_state[key]
        st.rerun()

elif st.session_state.quiz_started:
    if st.session_state.quiz_completed:
        st.title("🎉 SQL Challenge Completed! 🎉")
        st.balloons()

        final_score = calculate_score(st.session_state.user_answers)
        score_emoji = "🏆" if final_score >= 80 else ("👍" if final_score >= 50 else "💪")
        st.metric(label=f"{score_emoji} Your Final Score", value=f"{final_score:.2f}%")
        
        with st.container(border=True):
            st.subheader("📊 Overall Performance Analysis")
            with st.spinner("Guru ji aapki performance analyze kar rahe hain..."):
                performance_summary = analyze_performance(st.session_state.user_answers)
            st.markdown(performance_summary.get("overall_feedback", "Could not load performance feedback."))

        st.markdown("---")
        if st.checkbox("🧐 Show Detailed Feedback for All Questions", 
                        value=st.session_state.get("show_detailed_feedback_on_completion", False),
                        key="toggle_detailed_feedback_completion"):
            st.session_state.show_detailed_feedback_on_completion = st.session_state.toggle_detailed_feedback_completion
            with st.container(border=True):
                st.subheader("📜 Detailed Feedback per Question:")
                if not st.session_state.user_answers:
                    st.info("You did not attempt or submit any questions.")
                else:
                    for ans_data in st.session_state.user_answers:
                        q_data = sql_questions[ans_data["question_index"]]
                        with st.expander(f"{get_emoji(ans_data['is_correct'])} Question {ans_data['question_index']+1}: {q_data['question']}", expanded=not ans_data['is_correct']):
                            st.markdown(f"**Your Answer:**\n```sql\n{ans_data['student_answer']}\n```")
                            st.markdown(f"**AI Mentor's Feedback:**\n{ans_data.get('feedback', 'No feedback.')}")
                            if "actual_result_sim" in ans_data: display_simulation("Your Query's Result (Sim)", ans_data["actual_result_sim"])
                            if "expected_result_sim" in ans_data and not ans_data['is_correct'] and not isinstance(ans_data["expected_result_sim"], str):
                                display_simulation("Expected Result (Sim)", ans_data["expected_result_sim"])
        
        st.markdown("---")
        cta_col1, cta_col2 = st.columns(2)
        with cta_col1:
            if final_score >= 80:
                st.link_button("🏆 Generate Certificate!", "https://superprofile.bio/vp/corporate-bhaiya-sql-page", use_container_width=True, type="primary")
                st.success("Congratulations! Click above for your certificate.")
            else:
                st.link_button("📚 Book a Mentor Session", "https://topmate.io/corporate_bhaiya", use_container_width=True, type="primary") # Replace if different
                st.info("Keep practicing! Book a session to improve.")
        
        with cta_col2:
             if st.button("🔄 Restart Quiz", use_container_width=True):
                st.session_state.quiz_started = False # This will trigger rerun to start screen
                # Reset all relevant states
                for key in default_session_state.keys():
                    st.session_state[key] = default_session_state[key]
                for key in list(st.session_state.keys()):
                    if key.startswith("query_input_") or key.startswith("answer_feedback_") or key == "toggle_detailed_feedback_completion":
                        del st.session_state[key]
                st.rerun()

    else: # Quiz in progress
        current_q_index = st.session_state.current_question
        if current_q_index < len(sql_questions):
            question_data = sql_questions[current_q_index]
            
            st.header(f"🧠 Question {current_q_index + 1} of {len(sql_questions)}")
            st.info(f"**{question_data['question']}**")

            with st.expander("🔍 View Table Schemas & Sample Data", expanded=False):
                for table_name in question_data["relevant_tables"]:
                    df_schema = original_tables.get(table_name)
                    if df_schema is not None:
                        st.markdown(f"**Table: `{table_name}`**")
                        schema_view = pd.DataFrame({'Column': df_schema.columns, 'Data Type': [str(dtype) for dtype in df_schema.dtypes]})
                        st.dataframe(schema_view, hide_index=True, use_container_width=True)
                        st.markdown(f"*Sample Data (first 3 rows of `{table_name}`):*")
                        st.dataframe(df_schema.head(3), hide_index=True, use_container_width=True)
                        st.markdown("---")
                    else: st.warning(f"Schema for table '{table_name}' not found.")
            
            user_query = st.text_area("📝 Your SQL Query:", height=150, key=f"query_input_{current_q_index}", placeholder="SELECT * FROM ...")
            
            current_answer_key = f"answer_feedback_{current_q_index}"
            if current_answer_key not in st.session_state: st.session_state[current_answer_key] = {}

            submit_cols = st.columns((2,1))
            with submit_cols[0]:
                if st.button("✅ Submit Answer", key=f"submit_{current_q_index}", use_container_width=True, type="primary"):
                    if user_query.strip():
                        st.toast("Submitting your answer... 🤔", icon="🤔")
                        with st.spinner("AI Mentor is evaluating..."):
                            feedback, is_correct, expected_sim, actual_sim, llm_output = evaluate_answer_with_llm(question_data, user_query, original_tables)
                        
                        answer_updated = False # To update if re-answering
                        for i, ans in enumerate(st.session_state.user_answers):
                            if ans["question_index"] == current_q_index:
                                st.session_state.user_answers[i] = {"question_index": current_q_index, "question": question_data["question"], "student_answer": user_query, "feedback": feedback, "is_correct": is_correct, "expected_result_sim": expected_sim, "actual_result_sim": actual_sim, "llm_raw_output": llm_output}
                                answer_updated = True; break
                        if not answer_updated: st.session_state.user_answers.append({"question_index": current_q_index, "question": question_data["question"], "student_answer": user_query, "feedback": feedback, "is_correct": is_correct, "expected_result_sim": expected_sim, "actual_result_sim": actual_sim, "llm_raw_output": llm_output})
                        
                        st.session_state[current_answer_key] = {"submitted": True, "feedback": feedback, "is_correct": is_correct, "actual_sim": actual_sim, "expected_sim": expected_sim}
                        st.session_state.show_detailed_feedback = True
                        st.toast("💡 Feedback received!", icon="💡")
                        st.rerun()
                    else: st.warning("Please enter your SQL query before submitting.", icon="⚠️")
            with submit_cols[1]:
                if st.button("➡️ Skip Question", key=f"skip_{current_q_index}", use_container_width=True):
                    st.toast("Skipping question...", icon="➡️")
                    # Logic for skipping (similar to submit but with SKIPPED values)
                    answer_updated = False
                    for i, ans in enumerate(st.session_state.user_answers):
                        if ans["question_index"] == current_q_index:
                            st.session_state.user_answers[i] = {"question_index": current_q_index, "question": question_data["question"], "student_answer": "SKIPPED", "feedback": "Question skipped.", "is_correct": False, "expected_result_sim": "N/A", "actual_result_sim": "N/A", "llm_raw_output": "N/A"}
                            answer_updated = True; break
                    if not answer_updated: st.session_state.user_answers.append({"question_index": current_q_index, "question": question_data["question"], "student_answer": "SKIPPED", "feedback": "Question skipped.", "is_correct": False, "expected_result_sim": "N/A", "actual_result_sim": "N/A", "llm_raw_output": "N/A"})
                    
                    st.session_state[current_answer_key] = {} # Clear feedback for this q
                    st.session_state.show_detailed_feedback = False
                    if st.session_state.current_question + 1 < len(sql_questions): st.session_state.current_question += 1
                    else: 
                        st.session_state.quiz_completed = True
                        st.session_state.show_detailed_feedback_on_completion = True # Show full feedback list on completion
                    st.rerun()

            if st.session_state.show_detailed_feedback and st.session_state[current_answer_key].get("submitted"):
                with st.container(border=True):
                    st.subheader("🔍 AI Mentor's Feedback")
                    feedback_data = st.session_state[current_answer_key]
                    if feedback_data["is_correct"]: st.success(f"**{get_emoji(True)} Correct!** {feedback_data['feedback']}")
                    else: st.error(f"**{get_emoji(False)} Needs Improvement.** {feedback_data['feedback']}")
                    display_simulation("Your Query's Result (Sim)", feedback_data["actual_sim"])
                    if not feedback_data["is_correct"] and not isinstance(feedback_data["expected_sim"], str) and feedback_data["expected_sim"] is not None:
                        display_simulation("Expected Result (Sim)", feedback_data["expected_sim"])
                
                st.markdown("---")
                if st.session_state.current_question + 1 < len(sql_questions):
                    if st.button("➡️ Next Question", key=f"next_q_{current_q_index}", use_container_width=True, type="primary"):
                        st.session_state.current_question += 1
                        st.session_state.show_detailed_feedback = False
                        st.rerun()
                else:
                    if st.button("🏁 Finish Quiz & See Results", key=f"finish_{current_q_index}", use_container_width=True, type="primary"):
                        st.session_state.quiz_completed = True
                        st.session_state.show_detailed_feedback = False
                        st.session_state.show_detailed_feedback_on_completion = True
                        st.rerun()
        else: # Should not be reached if logic is correct
            st.session_state.quiz_completed = True
            st.rerun()
            
    # Sidebar content (Progress and Restart)
    st.sidebar.header("🧭 Quiz Navigation")
    processed_q_indices = {ans["question_index"] for ans in st.session_state.user_answers}
    questions_processed_count = len(processed_q_indices)
    
    if not st.session_state.quiz_completed:
      st.sidebar.progress(questions_processed_count / len(sql_questions) if sql_questions else 0)
      st.sidebar.caption(f"{questions_processed_count} / {len(sql_questions)} questions processed.")
    else:
      st.sidebar.success("Quiz Completed!")

    st.sidebar.markdown("---")
    if st.sidebar.button("🔙 Restart Quiz Now", use_container_width=True):
        st.session_state.quiz_started = False # This will trigger rerun to start screen
        # Reset all relevant states
        for key in default_session_state.keys():
            st.session_state[key] = default_session_state[key]
        # Clear any dynamic keys used during the quiz
        for key in list(st.session_state.keys()):
            if key.startswith("query_input_") or key.startswith("answer_feedback_") or key == "toggle_detailed_feedback_completion":
                del st.session_state[key]
        st.rerun()
else: # Fallback if quiz_started is False but not caught by the first if block
    st.session_state.quiz_started = False
    st.rerun()
