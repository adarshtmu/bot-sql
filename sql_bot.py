import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import duckdb # Import DuckDB

# --- Page Config ---
st.set_page_config(page_title="SQL Mentor", layout="wide", page_icon="🚀")

# --- Custom CSS ---
# (Paste the full dark_theme_css block from above here)
dark_theme_css = """
    <style>
        /* Base Styling */
        body { color: #d4d4d4; }
        .stApp { background-color: #1e1e1e; }
        /* Hide default Streamlit elements */
        header, #MainMenu, footer, .viewerBadge_container__1QSob, .stDeployButton, [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stDeployButton"], .st-emotion-cache-1r8d6ul, .st-emotion-cache-1jicfl2 { visibility: hidden; height: 0%; position: fixed; }
        #root > div:nth-child(1) > div > div > div > div > section > div { padding-top: 1rem; }
        /* Containers and Cards */
        .section-container { background-color: #252526; border: 1px solid #3c3c3c; border-radius: 8px; padding: 25px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.2); }
        .info-container { background-color: #2a2a2b; border: 1px solid #4a4a4a; border-radius: 5px; padding: 15px; margin-bottom: 10px; height: 100%; } /* Added height */
        /* Buttons */
        .stButton > button { border-radius: 5px; padding: 10px 20px; font-weight: bold; border: none; color: white; background-color: #1ebaa5; }
        .stButton > button:hover { background-color: #24cca8; color: white; }
        .stButton > button:active { background-color: #17a891; color: white; }
        .stButton[kind="secondary"] > button { background-color: #555; } /* Secondary button style */
        .stButton[kind="secondary"] > button:hover { background-color: #666; }
        /* DataFrames */
        .stDataFrame { border: 1px solid #3c3c3c; border-radius: 5px; }
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] { gap: 8px; border-bottom: 1px solid #3c3c3c; padding-bottom: 0; }
        .stTabs [data-baseweb="tab"] { height: 45px; border: none !important; background-color: transparent; padding: 10px 15px; margin: 0; border-bottom: 3px solid transparent; color: #a0a0a0; }
        .stTabs [aria-selected="true"] { background-color: transparent; color: #1ebaa5; border-bottom: 3px solid #1ebaa5; }
        /* Expanders */
        .stExpander { border: 1px solid #3c3c3c; border-radius: 5px; background-color: #2a2a2b; margin-bottom: 10px; /* Add space below expanders */ }
        .stExpander header { font-size: 1.05em; /* Slightly smaller */ font-weight: bold; color: #d4d4d4; visibility: visible; }
        .stExpander header:hover { color: #1ebaa5; }
        .stExpander div[data-testid="stExpanderDetails"] { padding-top: 15px; } /* Add padding inside expander */
        /* Code Blocks */
        div[data-testid="stCodeBlock"] > pre { background-color: #252526; border: 1px solid #3c3c3c; border-radius: 5px; padding: 15px; color: #d4d4d4; }
        /* Success/Error/Warning/Info Boxes */
        div[data-testid="stAlert"] { border-radius: 5px; border: none; padding: 15px; margin-top: 10px; margin-bottom: 10px; }
        div[data-testid="stAlert"][kind="success"] { background-color: rgba(46, 200, 166, 0.15); color: #2eca9a; border-left: 5px solid #1ebaa5;}
        div[data-testid="stAlert"][kind="error"] { background-color: rgba(244, 67, 54, 0.15); color: #f8716d; border-left: 5px solid #f44336;}
        div[data-testid="stAlert"][kind="warning"] { background-color: rgba(255, 167, 38, 0.15); color: #ffa726; border-left: 5px solid #ffa726;}
        div[data-testid="stAlert"][kind="info"] { background-color: rgba(41, 182, 246, 0.15); color: #29b6f6; border-left: 5px solid #29b6f6;}
        /* Metric */
        div[data-testid="stMetric"] { background-color: transparent; border: none; border-radius: 5px; padding: 10px 5px 5px 5px; text-align: center;} /* Adjusted padding */
        div[data-testid="stMetricLabel"] { color: #a0a0a0; font-size: 0.9em; margin-bottom: 0; } /* Smaller label */
        div[data-testid="stMetricValue"] { font-size: 2.8em; font-weight: bold; color: #ffffff; line-height: 1; margin:0; padding:0; } /* Tighter value */
        /* Dividers */
        hr { border-top: 1px solid #3c3c3c; }
    </style>
"""
st.markdown(dark_theme_css, unsafe_allow_html=True)

# --- Set up Gemini API ---
gemini_api_key = "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k"
if not gemini_api_key: st.error("🚨 Gemini API Key missing."); st.stop()
try:
    genai.configure(api_key=gemini_api_key); model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e: st.error(f"🚨 Failed to configure Gemini API: {e}"); st.stop()

# --- Sample Data ---
# (Sample Data remains the same)
users_table = pd.DataFrame({ "user_id": [1, 2, 3, 4], "name": ["Alice", "Bob", "Charlie", "David"], "email": ["alice@example.com", "bob@example.com", "charlie@example.com", "david@example.com"], "age": [25, 30, 35, 40], "city": ["New York", "Los Angeles", "Chicago", "Houston"] })
orders_table = pd.DataFrame({ "order_id": [101, 102, 103, 104, 105], "user_id": [1, 2, 3, 1, 4], "amount": [50.00, 75.50, 120.00, 200.00, 35.00], "order_date": pd.to_datetime(["2024-02-01", "2024-02-05", "2024-02-10", "2024-02-15", "2024-02-20"]), "status": ["Completed", "Pending", "Completed", "Shipped", "Cancelled"] })
original_tables = {"users": users_table, "orders": orders_table}

# --- SQL Questions List ---
# (SQL Questions list remains the same)
sql_questions = [ { "question": "SELECT all details from 'users' table.", "correct_answer_example": "SELECT * FROM users;", "sample_table": users_table, "relevant_tables": ["users"] }, { "question": "Count total users.", "correct_answer_example": "SELECT COUNT(*) AS user_count FROM users;", "sample_table": users_table, "relevant_tables": ["users"] }, { "question": "Get users older than 30.", "correct_answer_example": "SELECT * FROM users WHERE age > 30;", "sample_table": users_table, "relevant_tables": ["users"] }, { "question": "Find 'Pending' orders.", "correct_answer_example": "SELECT * FROM orders WHERE status = 'Pending';", "sample_table": orders_table, "relevant_tables": ["orders"] }, { "question": "Find most recent order.", "correct_answer_example": "SELECT * FROM orders ORDER BY order_date DESC LIMIT 1;", "sample_table": orders_table, "relevant_tables": ["orders"] }, { "question": "Find average order amount.", "correct_answer_example": "SELECT AVG(amount) AS average_amount FROM orders;", "sample_table": orders_table, "relevant_tables": ["orders"] }, { "question": "Find users with no orders.", "correct_answer_example": "SELECT u.* FROM users u LEFT JOIN orders o ON u.user_id = o.user_id WHERE o.order_id IS NULL;", "sample_table": users_table, "relevant_tables": ["users", "orders"] }, { "question": "Calculate total spent by each user (JOIN).", "correct_answer_example": "SELECT u.name, SUM(o.amount) AS total_spent FROM users u JOIN orders o ON u.user_id = o.user_id GROUP BY u.name ORDER BY u.name;", "sample_table": users_table, "relevant_tables": ["users", "orders"] }, { "question": "Count orders per user (LEFT JOIN, include 0).", "correct_answer_example": "SELECT u.name, COUNT(o.order_id) AS order_count FROM users u LEFT JOIN orders o ON u.user_id = o.user_id GROUP BY u.name ORDER BY u.name;", "sample_table": users_table, "relevant_tables": ["users", "orders"] }, { "question": "Find users from 'New York' or 'Chicago'.", "correct_answer_example": "SELECT * FROM users WHERE city IN ('New York', 'Chicago');", "sample_table": users_table, "relevant_tables": ["users"] } ]

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
        con = duckdb.connect(database=':memory:', read_only=False); [con.register(str(name), df) for name, df in tables_dict.items() if isinstance(df, pd.DataFrame)]
        result_df = con.execute(sql_query).df(); con.close(); return result_df
    except Exception as e:
        error_message = f"Simulation Error: Failed query. Reason: {str(e)}";
        try: e_str = str(e).lower(); binder_match = re.search(r'(binder error|catalog error|parser error).*referenced column "([^"]+)" not found', e_str); syntax_match = re.search(r'syntax error.*at or near ""([^"]+)""', e_str);
        if binder_match: error_message += f"\n\n**Hint:** Use single quotes (') for text values like `'{binder_match.group(2)}'` instead of double quotes (\")."
        elif syntax_match: error_message += f"\n\n**Hint:** Use single quotes (') for text values like `'{syntax_match.group(1)}'` instead of double quotes (\")."
        except Exception as e_hint: print(f"Hint gen error: {e_hint}")
        print(f"ERROR [sim]: {error_message}\nQuery: {sql_query}");
        if con: try: con.close() except: pass
        return error_message
def get_table_schema(table_name, tables_dict):
    if table_name in tables_dict and isinstance(tables_dict[table_name], pd.DataFrame): return tables_dict[table_name].columns.astype(str).tolist()
    return []
def evaluate_answer_with_llm(question_data, student_answer, original_tables_dict):
    if not student_answer.strip(): return "Please provide an answer.", False, "N/A", "N/A", "No input."
    question = question_data["question"]; relevant_table_names = question_data["relevant_tables"]; correct_answer_example = question_data["correct_answer_example"]
    schema_info = ""; # ... (schema generation logic as before) ...
    if not relevant_table_names: schema_info = "No table schema context.\n"
    else:
        for name in relevant_table_names:
            columns = get_table_schema(name, original_tables_dict)
            if columns:
                try: df = original_tables_dict[name]; dtypes = df.dtypes.to_string() if isinstance(df, pd.DataFrame) else "N/A"; schema_info += f"Table '{name}': Columns {columns}\n DataTypes:\n{dtypes}\n\n"
                except Exception as e_schema: schema_info += f"Table '{name}': Columns {columns} (Schema Error: {e_schema})\n\n"
            else: schema_info += f"Table '{name}': Schema not found.\n"
    prompt = f""" You are an expert SQL evaluator... Your response MUST be in English... Do NOT use Hindi... Feedback: English ONLY... Verdict: Correct / Incorrect... Begin Evaluation (Respond ONLY in English): """ # Using strong English prompt
    feedback_llm = "AI feedback failed."; is_correct_llm = False; llm_output = "Error: No LLM response."
    try:
        response = model.generate_content(prompt); # ... (LLM response parsing logic as before) ...
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
    if not user_answers: return 0; correct = sum(1 for ans in user_answers if ans.get("is_correct", False)); total = len(user_answers); return (correct / total) * 100 if total > 0 else 0
def analyze_performance(user_answers):
    performance_data = { "strengths": [], "weaknesses": [], "overall_feedback": "Analysis could not be completed." }
    if not user_answers: performance_data["overall_feedback"] = "No answers submitted."; return performance_data
    try: #... (Data prep for analysis prompt as before, using English prompt) ...
        correct_q = [ans["question"] for ans in user_answers if ans.get("is_correct")]; incorrect_ans = [{"question": ans["question"], "your_answer": ans["student_answer"], "feedback_received": ans.get("feedback", "N/A")} for ans in user_answers if not ans.get("is_correct")]; performance_data["strengths"] = correct_q; performance_data["weaknesses"] = [item["question"] for item in incorrect_ans]; total_q, correct_c, score = len(user_answers), len(correct_q), calculate_score(user_answers); incorrect_sum = "\n".join([ f"  Q: {item['question']}\n    Your Answer: {item['your_answer']}\n    Feedback: {item['feedback_received']}\n" for item in incorrect_ans]).strip() if incorrect_ans else "  None! Great job!";
        prompt = f""" A student took an SQL quiz... Task: Provide an overall performance summary feedback in English..."""
    except Exception as data_prep_error: print(f"Error preparing analysis data: {data_prep_error}"); performance_data["overall_feedback"] = f"Analysis prep failed: {data_prep_error}"; return performance_data
    try: # Get LLM summary
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
    # Wrap in a main container for overall padding/styling
    with st.container():
        st.title("🚀 SQL Mentor")
        st.subheader("Test and Improve Your SQL Querying Skills")
        st.markdown("---")

        st.markdown("""
        Welcome! This interactive quiz will challenge you with various SQL tasks using sample `users` and `orders` tables.
        Your queries will be evaluated by an AI mentor providing instant feedback. Use the previews below to understand the data structure.
        """)

        st.markdown('<div class="info-container"><strong>📌 Important Note:</strong> Standard SQL syntax (MySQL/PostgreSQL like) is expected. Query simulation uses DuckDB. AI evaluation by Google Gemini.</div>', unsafe_allow_html=True)

        col_info1, col_info2 = st.columns(2)
        with col_info1:
            # Use markdown for a styled container
            st.markdown('<div class="info-container"><h4>📊 Table Overview</h4>', unsafe_allow_html=True)
            table_overview_data = {"Table": [name.capitalize() for name in original_tables.keys()], "Rows": [len(df) for df in original_tables.values()], "Columns": [len(df.columns) for df in original_tables.values()]}
            st.dataframe(pd.DataFrame(table_overview_data), hide_index=True, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True) # Close the div

        with col_info2:
            # Use markdown for a styled container
            st.markdown('<div class="info-container"><h4>📝 About This Quiz</h4>', unsafe_allow_html=True)
            st.markdown(f"""
            * **{len(sql_questions)} Challenges:** Test across various concepts.
            * **Instant Feedback:** AI analysis of your queries.
            * **Query Simulation:** See results on sample data via DuckDB.
            * **Performance Review:** Score & detailed analysis provided.
            * **Dialect:** Standard SQL focus.
            """)
            st.markdown('</div>', unsafe_allow_html=True) # Close the div

        st.markdown("---")

        st.subheader("🔍 Table Previews & Schema")
        tab1, tab2 = st.tabs(["Users Table", "Orders Table"])
        with tab1:
            st.caption("Contains user details.")
            st.dataframe(users_table, hide_index=True, use_container_width=True)
            with st.expander("Show Schema"):
                 st.code(f"""
                 Table: users
                 Columns: {get_table_schema('users', original_tables)}
                 """, language="text")
        with tab2:
            st.caption("Stores order details.")
            st.dataframe(orders_table, hide_index=True, use_container_width=True)
            with st.expander("Show Schema"):
                 st.code(f"""
                 Table: orders
                 Columns: {get_table_schema('orders', original_tables)}
                 """, language="text")

        st.markdown("---")

        _, center_col, _ = st.columns([1.5, 1, 1.5]) # Adjust ratio for button size/centering
        with center_col:
             if st.button("🚀 Start SQL Challenge!", use_container_width=True, type="primary"):
                 st.session_state.quiz_started = True; st.session_state.user_answers = []; st.session_state.current_question = 0; st.session_state.quiz_completed = False; st.session_state.show_detailed_feedback = False; st.rerun()

# --- Quiz In Progress ---
elif st.session_state.quiz_started and not st.session_state.quiz_completed:
    st.title("✍️ SQL Query Challenge")

    # --- Display Past Answers (Chat History) First ---
    if st.session_state.user_answers:
        st.subheader("📖 Answer History & Feedback")
        st.caption("Expand items below to review past answers, feedback, and simulation results.")
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
        st.divider() # Divider after history

    # --- Current Question Area ---
    with st.container(border=True):
        current_q_index = st.session_state.current_question
        if current_q_index < len(sql_questions):
            question_data = sql_questions[current_q_index]
            st.markdown(f"#### Question {current_q_index + 1} / {len(sql_questions)}")
            st.markdown(f"##### **{question_data['question']}**")

            # Show relevant table previews concisely
            rel_tables = question_data.get("relevant_tables", [])
            if rel_tables:
                preview_cols = st.columns(len(rel_tables))
                for idx, table_name in enumerate(rel_tables):
                    with preview_cols[idx]:
                         st.caption(f"{table_name.capitalize()} Preview:")
                         if table_name in original_tables:
                             st.dataframe(original_tables[table_name].head(3), height=150, hide_index=True, use_container_width=True) # Show only first 3 rows
                             with st.popover("Schema", use_container_width=True): # Use popover for schema
                                 st.code(f"Columns: {get_table_schema(table_name, original_tables)}", language="text")
                         else:
                             st.warning(f"No preview.")
            else: st.info("No specific tables associated with this question for preview.")

            st.markdown("---") # Separator before input

            student_answer = st.text_area("Enter Your SQL Query Here:", key=f"answer_{current_q_index}", height=170, label_visibility="collapsed", placeholder="SELECT column FROM table WHERE condition...")

            submit_col, prog_col = st.columns([2,1]) # Give button more space
            with submit_col:
                submit_pressed = st.button("✅ Submit Answer", key=f"submit_{current_q_index}", use_container_width=True, type="primary")
            with prog_col:
                st.progress((current_q_index +1) / len(sql_questions)) # Progress 1-based
                st.caption(f"{current_q_index + 1}/{len(sql_questions)}")

            if submit_pressed:
                if student_answer.strip():
                    with st.spinner("AI Mentor is checking your answer..."):
                         feedback, is_correct, expected_sim, actual_sim, llm_raw = evaluate_answer_with_llm(question_data, student_answer, original_tables)
                    st.session_state.user_answers.append({"question": question_data["question"], "student_answer": student_answer, "feedback": feedback, "is_correct": is_correct, "expected_result": expected_sim, "actual_result": actual_sim, "llm_raw_output": llm_raw})
                    if current_q_index < len(sql_questions) - 1: st.session_state.current_question += 1
                    else: st.session_state.quiz_completed = True
                    st.rerun()
                else: st.warning("Please enter your SQL query.")
        else: st.warning("Quiz state error."); st.session_state.quiz_completed = True; st.rerun()


# --- Quiz Completed Screen --- # ENHANCED UI
elif st.session_state.quiz_completed:
    st.balloons()
    st.title("🎉 Quiz Complete!")
    score = calculate_score(st.session_state.user_answers)

    # Wrap sections in containers
    with st.container(border=True):
        score_col, summary_col = st.columns([1, 2])
        with score_col:
            st.metric(label="Final Score", value=f"{score:.1f}%") # Keep simple label
        with summary_col:
            st.markdown("#### Performance Summary")
            if score >= 80: st.markdown("🏆 **Excellent Work!** You demonstrated a strong understanding.")
            elif score >= 60: st.markdown("👍 **Good Job!** Solid performance. Review the analysis for areas to refine.")
            else: st.markdown("💪 **Keep Practicing!** Every query helps you learn. Check the detailed analysis.")

    st.divider()

    # Detailed Analysis in Tabs within a container
    st.subheader("📈 Detailed Performance Analysis")
    with st.container(border=True):
        analysis_tab1, analysis_tab2, analysis_tab3 = st.tabs(["Overall Summary (AI)", "✅ Strengths", "❌ Areas for Improvement"])
        with st.spinner("Generating AI performance summary..."): # Generate once
            performance_feedback = analyze_performance(st.session_state.user_answers)
        with analysis_tab1:
            st.markdown(performance_feedback.get("overall_feedback", "Summary not available.")) # Use markdown for potential formatting
        with analysis_tab2:
            strengths = performance_feedback.get("strengths", []);
            if strengths:
                st.markdown("**Questions answered correctly:**")
                for i, q in enumerate(strengths): st.markdown(f"<div style='margin: 5px 0; padding: 8px; background-color: rgba(46, 200, 166, 0.1); border-left: 4px solid #1ebaa5; border-radius: 3px;'>{i + 1}. {q}</div>", unsafe_allow_html=True)
            else: st.info("_(None correct this time. Review the feedback below!)_")
        with analysis_tab3:
             weaknesses = performance_feedback.get("weaknesses", []);
             if weaknesses:
                 st.markdown("**Questions to review:**")
                 for i, q in enumerate(weaknesses): st.markdown(f"<div style='margin: 5px 0; padding: 8px; background-color: rgba(244, 67, 54, 0.1); border-left: 4px solid #f44336; border-radius: 3px;'>{i + 1}. {q}</div>", unsafe_allow_html=True)
             else: st.info("_(No incorrect answers! Well done!)_")

    st.divider()

    # Final Review Section (Expanders)
    st.subheader("📝 Review Your Answers")
    st.caption("Expand questions below to see your answer, the AI feedback, and simulation results.")
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
    with cta_col1: st.link_button("🔗 Connect with a Mentor", "https://www.corporatebhaiya.com/", use_container_width=True)
    with cta_col2: st.link_button("🎓 Prepare for Interviews", "https://www.corporatebhaiya.com/mock-interview", use_container_width=True)
    with cta_col3:
        if st.button("🔄 Restart Quiz", use_container_width=True, type="secondary"): # Use secondary style
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
