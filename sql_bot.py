import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import duckdb

# --- Custom CSS ---
# Updated to include professional scoreboard styling
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
        
        /* Global font size */
        body, .stMarkdown, .stText, .stTextArea, .stButton button, .stLinkButton a {
            font-size: 18px !important;
        }
        h1 {font-size: 36px !important;}
        h2 {font-size: 28px !important;}
        h3 {font-size: 24px !important;}
        
        /* Start SQL Challenge button */
        button[kind="primary"] {
            font-size: 24px !important;
            padding: 15px 30px !important;
            color: white !important;
            background-color: red;
            border-radius: 10px;
        }
        
        /* Other buttons */
        .stButton button:not([kind="primary"]), .stLinkButton a {
            font-size: 20px !important;
            padding: 12px 24px !important;
            border-radius: 8px;
        }
        
        /* Professional Scoreboard Styles */
        .scoreboard-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
            margin: 30px 0;
            color: white;
        }
        
        .scoreboard-title {
            font-size: 48px !important;
            font-weight: bold;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .score-display {
            font-size: 80px !important;
            font-weight: bold;
            margin: 30px 0;
            text-shadow: 3px 3px 6px rgba(0,0,0,0.4);
            background: linear-gradient(45deg, #FFD700, #FFA500);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.3));
        }
        
        .performance-badge {
            display: inline-block;
            padding: 15px 30px;
            border-radius: 50px;
            font-size: 24px !important;
            font-weight: bold;
            margin: 20px 0;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .badge-excellent {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            box-shadow: 0 8px 20px rgba(76, 175, 80, 0.4);
        }
        
        .badge-good {
            background: linear-gradient(45deg, #2196F3, #1976D2);
            box-shadow: 0 8px 20px rgba(33, 150, 243, 0.4);
        }
        
        .badge-needs-improvement {
            background: linear-gradient(45deg, #FF9800, #F57C00);
            box-shadow: 0 8px 20px rgba(255, 152, 0, 0.4);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }
        
        .stat-number {
            font-size: 36px !important;
            font-weight: bold;
            display: block;
            margin-bottom: 10px;
        }
        
        .stat-label {
            font-size: 16px !important;
            opacity: 0.8;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        /* Certificate Button */
        .certificate-button {
            background: linear-gradient(45deg, #FFD700, #FFA500) !important;
            color: #000 !important;
            font-size: 24px !important;
            font-weight: bold !important;
            padding: 20px 40px !important;
            border-radius: 50px !important;
            text-decoration: none !important;
            display: inline-block !important;
            margin: 20px 0 !important;
            box-shadow: 0 10px 30px rgba(255, 215, 0, 0.4) !important;
            transition: all 0.3s ease !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            border: none !important;
        }
        
        .certificate-button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 15px 40px rgba(255, 215, 0, 0.6) !important;
        }
        
        /* Mentor Button */
        .mentor-button {
            background: linear-gradient(45deg, #6B73FF, #000DFF) !important;
            color: white !important;
            font-size: 22px !important;
            font-weight: bold !important;
            padding: 18px 36px !important;
            border-radius: 50px !important;
            text-decoration: none !important;
            display: inline-block !important;
            margin: 20px 0 !important;
            box-shadow: 0 10px 30px rgba(107, 115, 255, 0.4) !important;
            transition: all 0.3s ease !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
            border: none !important;
        }
        
        .mentor-button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 15px 40px rgba(107, 115, 255, 0.6) !important;
        }
        
        /* Achievement Icons */
        .achievement-icon {
            font-size: 60px;
            margin: 20px 0;
            display: block;
        }
        
        /* Progress Ring */
        .progress-ring {
            width: 200px;
            height: 200px;
            margin: 20px auto;
        }
        
        .progress-ring circle {
            fill: none;
            stroke-width: 8;
            stroke-linecap: round;
        }
        
        .progress-ring .background {
            stroke: rgba(255, 255, 255, 0.2);
        }
        
        .progress-ring .progress {
            stroke: #FFD700;
            stroke-dasharray: 628;
            stroke-dashoffset: 628;
            animation: progress-animation 2s ease-out forwards;
        }
        
        @keyframes progress-animation {
            to {
                stroke-dashoffset: calc(628 - (628 * var(--progress)) / 100);
            }
        }
        
        /* Feedback container styling */
        .feedback-container {
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            font-size: 18px !important;
        }
        .feedback-header {
            font-size: 24px !important;
            color: #1f77b4;
            margin-bottom: 10px;
        }
        .feedback-section {
            margin-top: 15px;
        }
        .strength-item, .weakness-item {
            font-size: 18px !important;
            margin: 5px 0;
        }
        
        /* Celebration animation */
        @keyframes celebrate {
            0% { transform: scale(1) rotate(0deg); }
            25% { transform: scale(1.1) rotate(5deg); }
            50% { transform: scale(1.2) rotate(-5deg); }
            75% { transform: scale(1.1) rotate(3deg); }
            100% { transform: scale(1) rotate(0deg); }
        }
        
        .celebrate {
            animation: celebrate 2s ease-in-out;
        }
    </style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Set up Gemini API ---
gemini_api_key = "AIzaSyAfzl_66GZsgaYjAM7cT2djVCBCAr86t2k"  # Replace with your Gemini API Key

if not gemini_api_key or gemini_api_key == "YOUR_API_KEY_HERE":
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
    "users": users_table,
    "orders": orders_table
}

# --- SQL Questions List ---
sql_questions = [
    {"question": "Write a SQL query to get all details about users from the 'users' table.", "correct_answer_example": "SELECT * FROM users;", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to count the total number of users in the 'users' table.", "correct_answer_example": "SELECT COUNT(*) AS user_count FROM users;", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to get all users older than 30 from the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE age > 30;", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to find all orders with a status of 'Pending' from the 'orders' table.", "correct_answer_example": "SELECT * FROM orders WHERE status = 'Pending';", "sample_table": orders_table, "relevant_tables": ["orders"]},
    {"question": "Write a SQL query to find users from 'chicago' in the 'users' table (test case-insensitivity).", "correct_answer_example": "SELECT * FROM users WHERE city = 'Chicago';", "sample_table": users_table, "relevant_tables": ["users"]},
]

# --- Session State Initialization ---
if "user_answers" not in st.session_state: st.session_state.user_answers = []
if "current_question" not in st.session_state: st.session_state.current_question = 0
if "quiz_started" not in st.session_state: st.session_state.quiz_started = False
if "quiz_completed" not in st.session_state: st.session_state.quiz_completed = False
if "show_detailed_feedback" not in st.session_state: st.session_state.show_detailed_feedback = False

# --- Helper Functions ---
def simulate_query_duckdb(sql_query, tables_dict):
    if not sql_query or not sql_query.strip():
        return "Simulation Error: No query provided."
    if not tables_dict:
        return "Simulation Error: No tables provided for context."
    
    con = None
    processed_query_for_ilike = sql_query
    
    # Replace double-quoted strings with single-quoted strings
    try:
        double_quote_pattern = r'"([^"]*)"'
        processed_query_for_ilike = re.sub(double_quote_pattern, r"'\1'", sql_query)
        if processed_query_for_ilike != sql_query:
            print(f"DEBUG: Original query: {sql_query}")
            print(f"DEBUG: Query after double->single quote conversion: {processed_query_for_ilike}")
    except Exception as e_quotes:
        print(f"Warning: Failed during double quote replacement: {e_quotes}. Proceeding with original query structure for ILIKE.")
        processed_query_for_ilike = sql_query
    
    # Query Modification for case-insensitive comparison
    modified_sql_query = processed_query_for_ilike
    final_executed_query = modified_sql_query
    case_insensitive_columns = {"orders": ["status"], "users": ["city"]}
    flat_insensitive_columns = [col for cols in case_insensitive_columns.values() for col in cols]
    
    if flat_insensitive_columns:
        try:
            col_pattern_part = "|".join([r"\b" + re.escape(col) + r"\b" for col in flat_insensitive_columns])
            pattern = rf"(.*?)({col_pattern_part})(\s*=\s*)('[^']+')"
            def replace_with_ilike(match):
                pre_context = match.group(1)
                col_name = match.group(2)
                literal = match.group(4)
                print(f"DEBUG: Rewriting query part: Replacing '=' with 'ILIKE' for column '{col_name}'")
                space_prefix = "" if not pre_context or pre_context.endswith(" ") or pre_context.endswith("(") else " "
                return f"{pre_context}{space_prefix}{col_name} ILIKE {literal}"
            
            modified_sql_query = re.sub(pattern, replace_with_ilike, processed_query_for_ilike, flags=re.IGNORECASE)
            final_executed_query = modified_sql_query
            if modified_sql_query != processed_query_for_ilike:
                print(f"DEBUG: Query after ILIKE rewrite: {modified_sql_query}")
        except Exception as e_rewrite:
            print(f"Warning: Failed to rewrite query for case-insensitivity (ILIKE), using quote-converted query. Error: {e_rewrite}")
            final_executed_query = processed_query_for_ilike
    
    # Execute with DuckDB
    try:
        con = duckdb.connect(database=':memory:', read_only=False)
        for table_name, df in tables_dict.items():
            if isinstance(df, pd.DataFrame):
                con.register(str(table_name), df)
            else:
                print(f"Warning [simulate_query]: Item '{table_name}' not a DataFrame during registration.")
        
        print(f"DEBUG: Executing final query in DuckDB: {final_executed_query}")
        result_df = con.execute(final_executed_query).df()
        con.close()
        return result_df
    except Exception as e:
        error_message = f"Simulation Error: Failed to execute query. Reason: {str(e)}"
        e_str = str(e).lower()
        hint = ""
        
        if "ILIKE" in str(e).upper() or (modified_sql_query != processed_query_for_ilike and "syntax error" in e_str):
            hint = "\n\n**Hint:** The simulation tried using case-insensitive matching (ILIKE). Check your SQL syntax near the comparison, especially if using complex conditions."
        else:
            catalog_match = re.search(r'catalog error:.*table with name "([^"]+)" does not exist', e_str)
            binder_match = re.search(r'(?:binder error|catalog error):.*column "([^"]+)" not found', e_str)
            syntax_match = re.search(r'parser error: syntax error at or near "([^"]+)"', e_str) \
                        or re.search(r'parser error: syntax error at end of input', e_str) \
                        or re.search(r'parser error: syntax error at:', e_str)
            type_match = re.search(r'conversion error:.*try cast\("([^"]+)"', e_str)
            
            if catalog_match: hint = f"\n\n**Hint:** Table '{catalog_match.group(1)}' might be misspelled or doesn't exist. Available tables: {list(tables_dict.keys())}."
            elif binder_match: hint = f"\n\n**Hint:** Column '{binder_match.group(1)}' might be misspelled or doesn't exist in the referenced table(s)."
            elif syntax_match:
                problem_area = syntax_match.group(1) if syntax_match.groups() and syntax_match.lastindex == 1 else "the location indicated"
                hint = f"\n\n**Hint:** Check your SQL syntax, especially around `{problem_area}`. Remember standard SQL uses single quotes (') for text values like `'example text'` (though the tool tries to handle double quotes for you)."
            elif type_match: hint = f"\n\n**Hint:** There might be a type mismatch. You tried using '{type_match.group(1)}' in a way that's incompatible with its data type (e.g., comparing text to a number)."
            elif "syntax error" in e_str:
                hint = "\n\n**Hint:** Double-check your SQL syntax. Ensure all clauses (SELECT, FROM, WHERE, etc.) are correct and in order. Use single quotes (') for string values."
        
        if not hint:
            hint = "\n\n**Hint:** Double-check your query syntax, table/column names, and data types. Ensure string values are correctly quoted (standard SQL uses single quotes '). Verify function names and usage."
        
        error_message += hint
        print(f"ERROR [simulate_query_duckdb]: {error_message}\nOriginal Query: {sql_query}\nFinal Attempted Query: {final_executed_query}")
        if con:
            try: con.close()
            except: pass
        return error_message

def get_table_schema(table_name, tables_dict):
    if table_name in tables_dict and isinstance(tables_dict[table_name], pd.DataFrame):
        return tables_dict[table_name].columns.astype(str).tolist()
    return []

def evaluate_answer_with_llm(question_data, student_answer, original_tables_dict):
    if not student_answer or not student_answer.strip():
        return "Please provide an answer.", False, "N/A", "N/A", "No input."
    
    question = question_data["question"]
    relevant_table_names = question_data["relevant_tables"]
    correct_answer_example = question_data["correct_answer_example"]
    
    schema_info = ""
    if not relevant_table_names:
        schema_info = "No specific table schema context provided for this question.\n"
    else:
        for name in relevant_table_names:
            columns = get_table_schema(name, original_tables_dict)
            if columns:
                try:
                    df = original_tables_dict[name]
                    dtypes_str = df.dtypes.to_string() if isinstance(df, pd.DataFrame) else "N/A"
                    schema_info += f"Table '{name}':\n  Columns: {columns}\n  DataTypes:\n{dtypes_str}\n\n"
                except Exception as e_schema:
                    schema_info += f"Table '{name}': Columns {columns} (Error getting schema details: {e_schema})\n\n"
            else:
                schema_info += f"Table '{name}': Schema information not found.\n"
    
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
        * If incorrect (due to reasons *other* than case-sensitivity on `status`/`city` or using double quotes): Gently point out the error (e.g., "Arre yaar, yahaan thoda sa check karo..." or "Ek chhoti si galti ho gayi hai..."). Explain *what* is wrong (syntax, logic, columns, joins, other conditions etc.). Suggest how to fix it. **Do NOT mark the query incorrect or suggest using LOWER()/UPPER() or single quotes *solely* because of case differences in `status`/`city` or the use of double quotes if the rest of the logic is correct.**
    * **Verdict:** Conclude your entire response with *exactly* one line formatted as: "Verdict: Correct" or "Verdict: Incorrect". This line MUST be the very last line.

    **Begin Evaluation:**
    """
    
    feedback_llm = "AI feedback generation failed."; is_correct_llm = False; llm_output = "Error: No LLM response received."
    try:
        response = model.generate_content(prompt)
        extracted_text = None
        try:
            if hasattr(response, 'text'):
                extracted_text = response.text
            elif hasattr(response, 'parts') and response.parts:
                extracted_text = "".join(part.text for part in response.parts if hasattr(part, 'text'))
            else:
                try:
                    extracted_text = f"AI Response Blocked or Empty. Prompt Feedback: {response.prompt_feedback}"
                except Exception:
                    extracted_text = "Error: Received unexpected or empty response structure from AI."
            
            if not extracted_text or not extracted_text.strip():
                llm_output = "Error: Received empty response from AI."
            else:
                llm_output = extracted_text.strip()
                verdict_match = re.search(r'^Verdict:\s*(Correct|Incorrect)\s*$', llm_output, re.MULTILINE | re.IGNORECASE)
                if verdict_match:
                    is_correct_llm = (verdict_match.group(1).lower() == "correct")
                    feedback_llm = llm_output[:verdict_match.start()].strip()
                    feedback_llm = re.sub(r'\s*Verdict:\s*(Correct|Incorrect)?\s*$', '', feedback_llm, flags=re.MULTILINE | re.IGNORECASE).strip()
                else:
                    st.warning(f"⚠️ Could not parse AI verdict from response.")
                    print(f"WARNING: Could not parse verdict from LLM output:\n---\n{llm_output}\n---")
                    feedback_llm = llm_output + "\n\n_(System Note: AI correctness check might be unreliable as verdict wasn't found.)_"
                    is_correct_llm = False
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
        st.error(f"🚨 AI Error during evaluation: {e_call}")
        print(f"ERROR: Gemini API call failed: {e_call}")
        feedback_llm = f"AI feedback generation error: {e_call}"
        is_correct_llm = False
        llm_output = f"Error during AI call: {e_call}"
    
    actual_result_sim = simulate_query_duckdb(student_answer, original_tables_dict)
    expected_result_sim = simulate_query_duckdb(correct_answer_example, original_tables_dict)
    
    return feedback_llm, is_correct_llm, expected_result_sim, actual_result_sim, llm_output

def calculate_score(user_answers):
    if not user_answers: return 0.0
    correct_count = sum(1 for ans in user_answers if ans.get("is_correct", False))
    total_questions_answered = len(user_answers)
    score = (correct_count / total_questions_answered) * 100 if total_questions_answered > 0 else 0.0
    return score

def get_performance_level(score):
    if score >= 90:
        return "excellent", "🏆", "OUTSTANDING PERFORMANCE"
    elif score >= 80:
        return "good", "🥇", "EXCELLENT PERFORMANCE"
    elif score >= 70:
        return "good", "🥈", "GOOD PERFORMANCE"
    elif score >= 60:
        return "needs-improvement", "🥉", "FAIR PERFORMANCE"
    else:
        return "needs-improvement", "📚", "NEEDS IMPROVEMENT"

def analyze_performance(user_answers):
    performance_data = {
        "strengths": [], "weaknesses": [],
        "overall_feedback": "Performance analysis could not be completed."
    }
    if not user_answers:
        performance_data["overall_feedback"] = "Koi jawaab nahi diya gaya. Analysis possible nahi hai."
        return performance_data
    
    try:
        correct_q = [ans["question"] for ans in user_answers if ans.get("is_correct")]
        incorrect_ans = [
            {"question": ans["question"], "your_answer": ans["student_answer"],
             "feedback_received": ans.get("feedback", "N/A")}
            for ans in user_answers if not ans.get("is_correct")
        ]
        performance_data["strengths"] = correct_q
        performance_data["weaknesses"] = [item["question"] for item in incorrect_ans]
        total_q, correct_c, score = len(user_answers), len(correct_q), calculate_score(user_answers)
        
        incorrect_summary = ""
        if incorrect_ans:
            incorrect_summary = "In sawaalon mein thodi galti hui:\n"
            for idx, item in enumerate(incorrect_ans):
                feedback_snippet = item['feedback_received'][:150].strip() + ('...' if len(item['feedback_received']) > 150 else '')
                incorrect_summary += f"  {idx+1}. Sawaal: {item['question']}\n     Aapka Jawaab: `{item['your_answer']}`\n     Feedback Mila: {feedback_snippet}\n"
            incorrect_summary = incorrect_summary.strip()
        else:
            incorrect_summary = "Koi galat jawaab nahi! Bahut badhiya!"
        
        correct_summary = ""
        if correct_q:
                    correct_summary = "Yeh sawaal bilkul sahi kiye:\n"
                    for idx, q_text in enumerate(correct_q):
                        correct_summary += f"  {idx+1}. {q_text}\n"
                else:
                    correct_summary = "Koi sahi jawaab nahi mila is baar."
        
                overall = f"{correct_summary}\n\n{incorrect_summary}\n\nTotal Questions: {total_q}\nSahi Jawaab: {correct_c}\nScore: {score:.2f}%"
                performance_data["overall_feedback"] = overall
            except Exception as e:
                performance_data["overall_feedback"] = f"Analysis failed: {e}"
            return performance_data
        
        # --- Streamlit UI ---
        st.title("🔥 SQL Quiz Challenge")
        st.markdown("""
        Welcome to the **SQL Quiz Challenge**!  
        Test your SQL skills on real tables, get instant feedback, and see how you did on our pro-style scoreboard.
        """)
        
        if not st.session_state.quiz_started:
            if st.button("🚦 Start SQL Challenge", type="primary"):
                st.session_state.quiz_started = True
                st.session_state.current_question = 0
                st.session_state.user_answers = []
                st.session_state.quiz_completed = False
                st.experimental_rerun()
            st.markdown("#### Sample Tables Available")
            st.dataframe(users_table, use_container_width=True)
            st.dataframe(orders_table, use_container_width=True)
            st.stop()
        
        if st.session_state.quiz_started and not st.session_state.quiz_completed:
            q_idx = st.session_state.current_question
            q_total = len(sql_questions)
            question_data = sql_questions[q_idx]
            st.markdown(f"### Question {q_idx+1} of {q_total}")
            st.info(question_data["question"])
            example_exp = st.expander("Show sample table(s)", expanded=False)
            for tname in question_data["relevant_tables"]:
                if tname in original_tables:
                    example_exp.dataframe(original_tables[tname], use_container_width=True)
            st.markdown("Write your SQL answer below:")
            user_sql = st.text_area("Enter your SQL query", value="", height=120, key=f"answer_{q_idx}")
        
            if st.button("Submit Answer", key=f"submit_{q_idx}"):
                feedback, is_correct, expected_result, actual_result, llm_output = evaluate_answer_with_llm(
                    question_data, user_sql, original_tables)
                st.session_state.user_answers.append({
                    "question": question_data["question"],
                    "student_answer": user_sql,
                    "is_correct": is_correct,
                    "feedback": feedback,
                    "llm_output": llm_output,
                    "expected_result": expected_result,
                    "actual_result": actual_result
                })
                if q_idx + 1 >= q_total:
                    st.session_state.quiz_completed = True
                else:
                    st.session_state.current_question += 1
                st.experimental_rerun()
        
            if q_idx > 0 and st.button("⬅️ Previous Question"):
                st.session_state.current_question -= 1
                st.experimental_rerun()
        
        if st.session_state.quiz_completed:
            score = calculate_score(st.session_state.user_answers)
            perf_key, trophy, perf_title = get_performance_level(score)
            st.markdown(f"""
            <div class="scoreboard-container">
                <div class="scoreboard-title">{trophy} Your Scoreboard</div>
                <div class="score-display">{score:.2f}%</div>
                <span class="performance-badge badge-{perf_key}">{perf_title}</span>
                <div class="stats-grid">
                    <div class="stat-card"><span class="stat-number">{len(st.session_state.user_answers)}</span><span class="stat-label">Total Questions</span></div>
                    <div class="stat-card"><span class="stat-number">{sum(1 for a in st.session_state.user_answers if a.get('is_correct'))}</span><span class="stat-label">Correct</span></div>
                    <div class="stat-card"><span class="stat-number">{sum(1 for a in st.session_state.user_answers if not a.get('is_correct'))}</span><span class="stat-label">Incorrect</span></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.success("Quiz complete! Dekhiye apna detailed feedback aur performance analysis niche.")
        
            st.markdown("## 📝 Detailed Feedback")
            for idx, ans in enumerate(st.session_state.user_answers):
                with st.expander(f"Question {idx+1}: {ans['question']}", expanded=(idx == 0)):
                    st.markdown(f"**Your Answer:**\n```sql\n{ans['student_answer']}\n```")
                    st.markdown(f"**Feedback:**\n{ans['feedback']}")
                    if isinstance(ans["expected_result"], pd.DataFrame):
                        st.markdown("**Expected Result:**")
                        st.dataframe(ans["expected_result"], use_container_width=True)
                    else:
                        st.markdown(f"**Expected Result:** {ans['expected_result']}")
                    if isinstance(ans["actual_result"], pd.DataFrame):
                        st.markdown("**Your Query Result:**")
                        st.dataframe(ans["actual_result"], use_container_width=True)
                    else:
                        st.markdown(f"**Your Query Result:** {ans['actual_result']}")
                    with st.expander("Show Full AI Evaluation Output"):
                        st.markdown(f"```\n{ans['llm_output']}\n```")
            # Performance Analysis
            st.markdown("## 📊 Performance Analysis")
            perf = analyze_performance(st.session_state.user_answers)
            st.markdown(f"""
            <div class="feedback-container">
                <div class="feedback-header">Aapki Performance Summary</div>
                <div class="feedback-section">
                    <strong>Strengths:</strong>
                    <ul>
                        {''.join(f"<li class='strength-item'>{q}</li>" for q in perf['strengths']) or "<li>Koi khas strength nahi dikh rahi hai abhi.</li>"}
                    </ul>
                </div>
                <div class="feedback-section">
                    <strong>Weaknesses:</strong>
                    <ul>
                        {''.join(f"<li class='weakness-item'>{q}</li>" for q in perf['weaknesses']) or "<li>Kamjori nahi dikh rahi abhi!</li>"}
                    </ul>
                </div>
                <div class="feedback-section">
                    <strong>Overall Feedback:</strong><br>
                    {perf['overall_feedback']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔁 Retake Quiz"):
                st.session_state.quiz_started = False
                st.session_state.current_question = 0
                st.session_state.user_answers = []
                st.session_state.quiz_completed = False
                st.experimental_rerun()
