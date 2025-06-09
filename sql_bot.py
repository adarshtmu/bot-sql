import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import duckdb

# --- Custom CSS ---
# Updated to increase font sizes globally and for specific elements
hide_streamlit_style = """
    <style>
        /* Apply zoom-out effect to the entire app */
        html, body, .stApp {
            zoom: 1.0 !important; /* Adjust this value to control zoom level (e.g., 0.85 = 85% zoom) */
        }
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
        /* Increase global font size */
        body, .stMarkdown, .stText, .stTextArea, .stButton button, .stLinkButton a {
            font-size: 18px !important;
        }
        h1 {font-size: 48px !important;}
        h2 {font-size: 36px !important;}
        h3 {font-size: 30px !important;}
        /* Style for Start SQL Challenge! button */
        button[kind="primary"] {
            font-size: 24px !important;
            padding: 15px 30px !important;
            color: white !important;
            background-color: red;
            border-radius: 10px;
        }
        /* Style for other buttons (Submit, Analysis, Retry) */
        .stButton button:not([kind="primary"]), .stLinkButton a {
            font-size: 20px !important;
            padding: 12px 24px !important;
            border-radius: 8px;
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

extra_user = {
    "user_id": 5,
    "name": "Eve",
    "email": "eve@example.com",
    "age": 28,
    "city": "Seattle"
}
users_table = pd.concat([users_table, pd.DataFrame([extra_user])], ignore_index=True)

original_tables = {
    "users": users_table,
    "orders": orders_table
}

# --- SQL Questions List ---
sql_questions = [
    {"question": "Write a SQL query to get all details about users from the 'users' table.", "correct_answer_example": "SELECT * FROM users;", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to count the total number of users in the 'users' table.", "correct_answer_example": "SELECT COUNT(*) AS user_count FROM users;", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to get all users older than 30 from the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE age > 30;", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to find the average order amount from the 'orders' table.", "correct_answer_example": "SELECT AVG(amount) AS average_amount FROM orders;", "sample_table": orders_table, "relevant_tables": ["orders"]},
    {"question": "Write a SQL query to calculate the total amount spent by each user by joining the 'users' and 'orders' tables.", "correct_answer_example": "SELECT u.name, SUM(o.amount) AS total_spent FROM users u JOIN orders o ON u.user_id = o.user_id GROUP BY u.name ORDER BY u.name;", "sample_table": users_table, "relevant_tables": ["users", "orders"]}
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
    * **Feedback:** Provide clear, constructive feedback in a friendly, encouraging, and casual English tone (like a helpful senior or mentor talking to a learner).
        * If incorrect (due to reasons *other* than case-sensitivity on `status`/`city` or using double quotes): Gently point out the error (e.g., "Hey, you might want to double-check this part..." or "Looks like there's a small mistake here..."). Explain *what* is wrong (syntax, logic, columns, joins, other conditions etc.). Suggest how to fix it. **Do NOT mark the query incorrect or suggest using LOWER()/UPPER() or single quotes *solely* because of case differences in `status`/`city` or the use of double quotes if the rest of the logic is correct.**
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
    if not user_answers or len(user_answers) == 0:
        return 0.0
    correct_count = sum(1 for ans in user_answers if ans.get("is_correct", False))
    total_attempted = len(user_answers)
    return (correct_count / total_attempted) * 100

def analyze_performance(user_answers):
    performance_data = {
        "strengths": [], "weaknesses": [],
        "overall_feedback": "Performance analysis could not be completed."
    }
    if not user_answers:
        performance_data["overall_feedback"] = "No answers were submitted. Analysis is not possible."
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
            incorrect_summary = "There were some mistakes in these questions:\n"
            for idx, item in enumerate(incorrect_ans):
                feedback_snippet = item['feedback_received'][:150].strip() + ('...' if len(item['feedback_received']) > 150 else '')
                incorrect_summary += f"  {idx+1}. Question: {item['question']}\n     Your Answer: `{item['your_answer']}`\n     Feedback Received: {feedback_snippet}\n"
            incorrect_summary = incorrect_summary.strip()
        else:
            incorrect_summary = "No incorrect answers! Great job!"

        correct_summary = ""
        if correct_q:
            correct_summary = "These questions were answered correctly:\n"
            for idx, q_text in enumerate(correct_q):
                correct_summary += f"  - {q_text}\n"
            correct_summary = correct_summary.strip()
        else:
            correct_summary = "No questions were answered correctly this time."

        prompt = f"""
        An SQL learner has just completed a practice quiz. Please analyze their performance and provide a friendly, motivating summary and feedback in casual English, like a mentor would.

        **Quiz Performance Summary:**
        - Total Questions Attempted: {total_q}
        - Correct Answers: {correct_c}
        - Final Score: {score:.2f}%

        **Correctly Answered Questions:**
        {correct_summary if correct_q else '(None)'}

        **Incorrectly Answered Questions & Feedback Snippets:**
        {incorrect_summary if incorrect_ans else '(None)'}

        **Quiz Context Reminder:**
        - Case-insensitivity was assumed for '=' comparisons on 'status' and 'city' columns.
        - Both single (') and double (") quotes were acceptable for string literals in this quiz simulation.

        **Task:**
        Now, provide an overall performance summary in the structure below:
        1.  **Overall Impression:** Give a positive or encouraging comment on the score and general performance (e.g., "Overall, this was a strong performance!", "You're on the right track, a little more practice will make a big difference!"). Be realistic but motivating.
        2.  **Strengths:** If any specific concepts were handled well (judging from the correct answers), highlight them (e.g., "You have a good grasp of using the SELECT and WHERE clauses.", "You handled the JOIN question correctly, which is excellent!"). Keep it general if no specific pattern is clear.
        3.  **Areas for Improvement:** Gently point out the concepts that were challenging (related to the incorrect answers). Focus on the concepts, not just the mistakes (e.g., "It looks like the logic for JOINs could be reviewed.", "Pay close attention to aggregate functions (like COUNT, AVG).", "There were some minor syntax errors."). Briefly mention standard practices (like using single quotes for strings in real databases) as a learning point, without implying it was wrong *in this quiz*.
        4.  **Next Steps / Encouragement:** Offer some encouraging words and suggest what to do next (e.g., "Keep practicing!", "It might be helpful to revise concept X.", "Keep up the great work, you'll master SQL in no time! It's also important to keep learning standard SQL practices (like using single quotes) for real-world scenarios.").

        Please generate the feedback in plain text. Keep the tone casual and start directly with the feedback.
        """
    except Exception as data_prep_error:
        print(f"Error preparing data for performance analysis: {data_prep_error}")
        performance_data["overall_feedback"] = f"Analysis data preparation failed: {data_prep_error}"
        return performance_data

    try:
        response = model.generate_content(prompt)
        generated_feedback = None
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
    return "✅" if is_correct else "❌"

def display_simulation(title, result_data):
    st.write(f"**{title}:**")
    if isinstance(result_data, pd.DataFrame):
        if result_data.empty:
            st.info("_(Simulation resulted in an empty table)_")
        else:
            st.dataframe(result_data.reset_index(drop=True), hide_index=False, use_container_width=False)
    elif isinstance(result_data, str) and "Simulation Error" in result_data:
        st.warning(result_data, icon="⚠️")
    elif result_data == "N/A":
        st.info("_(Simulation not applicable or not run)_")
    elif isinstance(result_data, str):
        st.info(f"_{result_data}_")
    else:
        st.error(f"_(Unexpected simulation result type: {type(result_data)})_")
        print(f"DEBUG: Unexpected simulation data type: {type(result_data)}, value: {result_data}")

# --- Streamlit App UI ---

# --- Advanced Start Screen ---
# --- Minimal Advanced Start Screen ---
# --- Advanced EdTech Learning Platform UI ---
# --- Advanced EdTech Learning Platform UI ---
# --- Advanced EdTech Learning Platform UI ---
# --- Advanced EdTech Learning Platform UI ---
if not st.session_state.quiz_started:
    # Advanced CSS for modern EdTech platform
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .main-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        min-height: 100vh;
        padding: 2rem 0;
        position: relative;
    }
    
    .floating-shapes {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100vh;
        overflow: hidden;
        pointer-events: none;
        z-index: -1;
    }
    
    .shape {
        position: absolute;
        background: rgba(255,255,255,0.1);
        border-radius: 50%;
        animation: float 6s ease-in-out infinite;
    }
    
    .shape:nth-child(1) {
        width: 80px;
        height: 80px;
        top: 10%;
        left: 10%;
        animation-delay: 0s;
    }
    
    .shape:nth-child(2) {
        width: 120px;
        height: 120px;
        top: 20%;
        right: 15%;
        animation-delay: 2s;
    }
    
    .shape:nth-child(3) {
        width: 60px;
        height: 60px;
        bottom: 20%;
        left: 20%;
        animation-delay: 4s;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-20px) rotate(180deg); }
    }
    
    .hero-container {
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255,255,255,0.2);
        padding: 3rem;
        border-radius: 24px;
        margin: 2rem auto;
        max-width: 1000px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.1);
        position: relative;
        overflow: hidden;
    }
    
    .hero-badge {
        display: inline-block;
        background: linear-gradient(135deg, #667eea, #764ba2);
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 50px;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .hero-title {
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 1rem;
        background: linear-gradient(135deg, #2d3748, #4a5568);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        line-height: 1.2;
    }
    
    .hero-subtitle {
        font-size: 1.4rem;
        color: #6b7280;
        margin-bottom: 2.5rem;
        font-weight: 400;
        max-width: 600px;
        margin-left: auto;
        margin-right: auto;
        line-height: 1.6;
    }
    
    .stats-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin: 2.5rem 0;
    }
    
    .stat-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 1.5rem;
        border-radius: 16px;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.5);
        box-shadow: 0 4px 20px rgba(0,0,0,0.08);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        position: relative;
        overflow: hidden;
        min-height: 180px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    
    .stat-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 40px rgba(0,0,0,0.15);
    }
    
    .stat-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #667eea, #764ba2);
    }
    
    .stat-icon {
        font-size: 2.5rem;
        margin-bottom: 0.8rem;
        display: block;
    }
    
    .stat-number {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1e293b;
        display: block;
        margin-bottom: 0.5rem;
        line-height: 1.2;
        word-wrap: break-word;
        hyphens: auto;
    }
    
    .stat-label {
        color: #64748b;
        font-weight: 500;
        font-size: 0.9rem;
        line-height: 1.3;
    }
    
    .start-button-container {
        margin: 3rem 0;
        text-align: center;
    }
    
    .cta-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 1.2rem 3rem;
        border-radius: 50px;
        font-size: 1.2rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        position: relative;
        overflow: hidden;
    }
    
    .cta-button::before {
        content: '';
        position: absolute;
        top: 0;
        left: -100%;
        width: 100%;
        height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    
    .cta-button:hover::before {
        left: 100%;
    }
    
    .cta-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 35px rgba(102, 126, 234, 0.4);
    }
    
    .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 2rem;
        margin: 3rem 0;
    }
    
    .feature-card {
        background: white;
        padding: 2.5rem;
        border-radius: 20px;
        box-shadow: 0 8px 30px rgba(0,0,0,0.1);
        border: 1px solid rgba(255,255,255,0.5);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        position: relative;
    }
    
    .feature-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 60px rgba(0,0,0,0.15);
    }
    
    .feature-icon {
        width: 60px;
        height: 60px;
        background: linear-gradient(135deg, #667eea, #764ba2);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.8rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        color: white;
    }
    
    .feature-title {
        font-size: 1.4rem;
        font-weight: 600;
        margin-bottom: 1rem;
        color: #1e293b !important;
    }
    
    .feature-description {
        color: #64748b !important;
        line-height: 1.6;
        font-size: 1rem;
    }
    
    .learning-path {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 3rem;
        border-radius: 20px;
        margin: 3rem 0;
        border: 1px solid rgba(255,255,255,0.5);
    }
    
    .learning-path h3 {
        text-align: center;
        font-size: 2rem;
        font-weight: 700;
        margin-bottom: 2rem;
        color: #1e293b;
    }
    
    .steps-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        position: relative;
        margin: 2rem 0;
    }
    
    .steps-container::before {
        content: '';
        position: absolute;
        top: 50%;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #667eea, #764ba2);
        z-index: 1;
    }
    
    .step {
        background: white;
        width: 120px;
        height: 120px;
        border-radius: 50%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        border: 3px solid #667eea;
        position: relative;
        z-index: 2;
        transition: transform 0.3s ease;
    }
    
    .step:hover {
        transform: scale(1.05);
    }
    
    .step-number {
        font-size: 1.5rem;
        font-weight: 700;
        color: #667eea;
        margin-bottom: 0.5rem;
    }
    
    .step-text {
        font-size: 0.8rem;
        font-weight: 600;
        text-align: center;
        color: #64748b;
    }
    
    .testimonial {
        background: white;
        padding: 2.5rem;
        border-radius: 20px;
        margin: 3rem 0;
        box-shadow: 0 8px 30px rgba(0,0,0,0.1);
        text-align: center;
        border: 1px solid rgba(255,255,255,0.5);
    }
    
    .testimonial-text {
        font-size: 1.2rem;
        font-style: italic;
        color: #4a5568;
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }
    
    .testimonial-author {
        font-weight: 600;
        color: #1e293b;
    }
    
    .pulse {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.02); }
        100% { transform: scale(1); }
    }
    
    @media (max-width: 768px) {
        .hero-title { font-size: 2.5rem; }
        .hero-subtitle { font-size: 1.2rem; }
        .stats-container { 
            grid-template-columns: repeat(2, 1fr); 
            gap: 1rem;
        }
        .stat-card {
            min-height: 160px;
            padding: 1.2rem;
        }
        .stat-number {
            font-size: 1.5rem;
        }
        .stat-label {
            font-size: 0.8rem;
        }
        .features-grid { grid-template-columns: 1fr; }
        .steps-container { flex-direction: column; gap: 2rem; }
        .steps-container::before { display: none; }
    }
    
    @media (max-width: 480px) {
        .stats-container {
            grid-template-columns: 1fr;
        }
        .stat-card {
            min-height: 140px;
        }
        .stat-number {
            font-size: 1.3rem;
        }
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Floating background shapes - Fixed positioning
    st.markdown("""
    <div class="floating-shapes">
        <div class="shape"></div>
        <div class="shape"></div>
        <div class="shape"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main Hero Section
    st.markdown("""
    <div class="hero-container">
        <div class="hero-badge">🚀 AI-Powered Learning Experience</div>
        <h1 class="hero-title">Master SQL Like a Pro</h1>
        <p class="hero-subtitle">Join 50,000+ developers who've accelerated their careers with our AI-powered SQL mastery program. Get personalized feedback, earn industry-recognized certificates, and land your dream job.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats Section using Streamlit columns (Alternative approach)
    st.markdown('<div class="stats-container">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)

        # Start Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 Start Your SQL Journey", type="primary", use_container_width=True, key="start_quiz"):
            st.session_state.quiz_started = True
            st.session_state.user_answers = []
            st.session_state.current_question = 0
            st.session_state.quiz_completed = False
            st.success("🎉 Welcome to your SQL mastery journey!")
            st.balloons()
            st.rerun()
    
    with col1:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-icon">📊</div>
            <span class="stat-number">5</span>
            <div class="stat-label">Expert Questions</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-icon">⚡</div>
            <span class="stat-number">15-20</span>
            <div class="stat-label">Minutes</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-icon">🎯</div>
            <span class="stat-number">50%</span>
            <div class="stat-label">Pass Rate</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="stat-card">
            <div class="stat-icon">🏆</div>
            <span class="stat-number">Pro</span>
            <div class="stat-label">Certificate</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    

    
    # Features Section
    st.markdown("""
    <div class="features-grid">
        <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <h3 class="feature-title">AI-Powered Feedback</h3>
            <p class="feature-description">Get instant, personalized feedback on your SQL queries with suggestions for optimization and best practices from our advanced AI tutor.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">🎯</div>
            <h3 class="feature-title">Real-World Scenarios</h3>
            <p class="feature-description">Practice with authentic business problems and datasets that mirror what you'll encounter in your professional career.</p>
        </div>
        <div class="feature-card">
            <div class="feature-icon">📈</div>
            <h3 class="feature-title">Progress Tracking</h3>
            <p class="feature-description">Monitor your learning journey with detailed analytics, performance insights, and skill progression tracking.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Learning Path
    st.markdown("""
    <div class="learning-path">
        <h3>Your Learning Journey</h3>
        <div class="steps-container">
            <div class="step">
                <div class="step-number">1</div>
                <div class="step-text">Take Assessment</div>
            </div>
            <div class="step">
                <div class="step-number">2</div>
                <div class="step-text">Get AI Feedback</div>
            </div>
            <div class="step">
                <div class="step-number">3</div>
                <div class="step-text">Earn Certificate</div>
            </div>
            <div class="step">
                <div class="step-number">4</div>
                <div class="step-text">Advance Career</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Testimonial
    st.markdown("""
    <div class="testimonial pulse">
        <p class="testimonial-text">"This platform transformed my SQL skills in just 2 weeks. The AI feedback was incredibly detailed and helped me land my dream data analyst role!"</p>
        <div class="testimonial-author">— Sarah Chen, Senior Data Analyst at Tech Corp</div>
    </div>
    """, unsafe_allow_html=True)
# --- Quiz In Progress Screen ---
elif st.session_state.quiz_started and not st.session_state.quiz_completed:
    st.title("✍️ SQL Query Challenge")
    
    if st.session_state.user_answers:
        st.markdown("---")
        st.subheader("📖 Your Answers and Feedback So Far")
        for i, ans_data in enumerate(st.session_state.user_answers):
            q_num = i + 1
            is_correct = ans_data.get('is_correct', False)
            with st.expander(f"Question {q_num}: {ans_data['question']} {get_emoji(is_correct)}", expanded=False):
                st.write(f"**Your Answere:**")
                st.code(ans_data.get('student_answer', '(No answer provided)'), language='sql')
                st.write(f"**SQL Mentor Feedback:**")
                feedback_text = ans_data.get("feedback", "_Feedback not available._")
                st.markdown(feedback_text)
                
                st.markdown("---")
                display_simulation("Simulated Result (Your Query Output)", ans_data.get("actual_result", "N/A"))
                
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


    st.markdown("---")
    
    current_q_index = st.session_state.current_question
    question_data = sql_questions[current_q_index]
    
    st.subheader(f"Question {current_q_index + 1} of {len(sql_questions)}")
    st.markdown(f"**{question_data['question']}**")
    
    relevant_tables = question_data["relevant_tables"]
    if relevant_tables:
        st.markdown("**Sample Table Preview(s):**")
        if len(relevant_tables) > 1:
            tabs = st.tabs([f"{name} Preview" for name in relevant_tables])
            for i, table_name in enumerate(relevant_tables):
                with tabs[i]:
                    if table_name in original_tables:
                        st.dataframe(original_tables[table_name], hide_index=True, use_container_width=False)
                    else:
                        st.warning(f"Data for table '{table_name}' not found.")
        elif len(relevant_tables) == 1:
            table_name = relevant_tables[0]
            if table_name in original_tables:
                st.dataframe(original_tables[table_name], hide_index=True, use_container_width=False)
            else:
                st.warning(f"Data for table '{table_name}' not found.")
    else:
        st.info("No specific table context provided for this question.")
    
    user_query = st.text_area("Write your SQL query here:", height=150, key=f"query_input_{current_q_index}")
    
    if st.button("✅ Submit Query", key=f"submit_{current_q_index}"):
        if user_query and user_query.strip():
            with st.spinner("🔄 Query ko check kiya ja raha hai... AI Mentor se feedback aur simulation results generate ho rahe hain..."):
                feedback, is_correct, expected_res, actual_res, raw_llm = evaluate_answer_with_llm(
                    question_data,
                    user_query,
                    original_tables
                )
                
                st.session_state.user_answers.append({
                    "question_number": current_q_index + 1,
                    "question": question_data["question"],
                    "student_answer": user_query,
                    "feedback": feedback,
                    "is_correct": is_correct,
                    "expected_result": expected_res,
                    "actual_result": actual_res,
                    "raw_llm_output": raw_llm
                })
                
                if current_q_index + 1 < len(sql_questions):
                    st.session_state.current_question += 1
                else:
                    st.session_state.quiz_completed = True
                
                st.rerun()
        else:
            st.warning("⚠️ Please enter your SQL query before submitting.")
    st.markdown("<div style='height: 220px;'></div>", unsafe_allow_html=True)        
    footer_html = """
    <div style='text-align: center; margin-top: 2rem; padding: 1.2rem; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 16px; color: white;'>
        <h3>🎓 Corporate Bhaiya Learning Platform</h3>
        <p>Empowering careers through expert mentorship</p>
        <p style='opacity: 0.8; font-size: 0.9rem;'>© 2025 All rights reserved</p>
    </div>
    """
    st.markdown(footer_html, unsafe_allow_html=True)
# --- Quiz Completed Screen ---
# --- Quiz Completed Screen ---
elif st.session_state.quiz_completed:

    # --- 1. Answer/Feedback Summary first ---
    st.markdown("---")
    st.subheader("📝 Your Answers and Feedback So Far")
    for i, ans_data in enumerate(st.session_state.user_answers):
        q_num = i + 1
        is_correct = ans_data.get('is_correct', False)
        with st.expander(f"Question {q_num}: {ans_data['question']} {get_emoji(is_correct)}", expanded=False):
            st.write(f"**Your Answere:**")
            st.code(ans_data.get('student_answer', '(No answer provided)'), language='sql')
            st.write(f"**SQL Mentor Feedback:**")
            feedback_text = ans_data.get("feedback", "_Feedback not available._")
            st.markdown(feedback_text)
            st.markdown("---")
            display_simulation("Simulated Result (Your Query Output)", ans_data.get("actual_result", "N/A"))
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

    # --- 2. Analysis Section ---
    st.markdown("---")
    # st.subheader("💡 AI Mentor Se Detailed Performance Analysis")
    # if st.button("📊 Show Detailed Analysis", key="show_analysis"):
    #     st.session_state.show_detailed_feedback = not st.session_state.show_detailed_feedback
    # if st.session_state.show_detailed_feedback:
    #     with st.spinner("🧠 Performance analysis generate ho raha hai..."):
    #         performance_summary = analyze_performance(st.session_state.user_answers)
    #         feedback_text = performance_summary.get("overall_feedback", "Analysis available nahi hai.")
    #         with st.container():
    #             st.markdown('<div class="feedback-container">', unsafe_allow_html=True)
    #             st.markdown('<div class="feedback-header">📈 Aapki Performance Ka Vistaar Se Analysis</div>', unsafe_allow_html=True)
    #             try:
    #                 sections = re.split(r'(Overall Impression:|Strengths:|Areas for Improvement:|Next Steps / Encouragement:)', feedback_text)
    #                 section_dict = {}
    #                 for i in range(1, len(sections), 2):
    #                     section_dict[sections[i].strip(':')] = sections[i+1].strip()
    #             except:
    #                 section_dict = {"Full Feedback": feedback_text}
    #             if "Overall Impression" in section_dict:
    #                 st.markdown("### 🌟 Overall Impression")
    #                 st.markdown(section_dict["Overall Impression"])
    #             st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
    #             st.markdown("### ✅ Strengths")
    #             if "Strengths" in section_dict:
    #                 strengths = section_dict["Strengths"].split('\n')
    #                 for strength in strengths:
    #                     if strength.strip():
    #                         st.markdown(f'<div class="strength-item">✔ {strength.strip()}</div>', unsafe_allow_html=True)
    #             elif performance_summary.get("strengths"):
    #                 for strength in performance_summary["strengths"]:
    #                     st.markdown(f'<div class="strength-item">✔ {strength}</div>', unsafe_allow_html=True)
    #             else:
    #                 st.markdown("Koi specific strengths identify nahi hue. Aur practice karo!")
    #             st.markdown('</div>', unsafe_allow_html=True)
    #             st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
    #             st.markdown("### 📝 Areas for Improvement")
    #             if "Areas for Improvement" in section_dict:
    #                 weaknesses = section_dict["Areas for Improvement"].split('\n')
    #                 for weakness in weaknesses:
    #                     if weakness.strip():
    #                         st.markdown(f'<div class="weakness-item">➡ {weakness.strip()}</div>', unsafe_allow_html=True)
    #             elif performance_summary.get("weaknesses"):
    #                 for weakness in performance_summary["weaknesses"]:
    #                     st.markdown(f'<div class="weakness-item">➡ {weakness}</div>', unsafe_allow_html=True)
    #             else:
    #                 st.markdown("Koi major weaknesses nahi! Bas practice jari rakho.")
    #             st.markdown('</div>', unsafe_allow_html=True)
    #             if "Next Steps / Encouragement" in section_dict:
    #                 st.markdown("### 🚀 Next Steps")
    #                 st.markdown(section_dict["Next Steps / Encouragement"])
    #             if "Full Feedback" in section_dict:
    #                 st.markdown("### 📋 Complete Feedback")
    #                 st.markdown(section_dict["Full Feedback"])
    #             st.markdown('</div>', unsafe_allow_html=True)

    # --- 3. Advanced Scorecard & Buttons LAST ---
    st.balloons()
    # Optional: Show congratulations at top
    st.markdown(
        """
        <div style='text-align:center; margin-top: 30px;'>
            <h1 style='color:#28a745;'>🎉 Congratulations!</h1>
            <h2 style='color:#1f77b4;'>You have completed the SQL Challenge</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")
    final_score = calculate_score(st.session_state.user_answers)


    # Determine dynamic colors and messages based on score
    score_color = "#28a745" if final_score >= 80 else "#ff9800" if final_score >= 50 else "#e74c3c"
    score_message = "Outstanding Performance! 🌟" if final_score >= 80 else "Good Effort! Keep Going! 💪" if final_score >= 50 else "Needs Improvement! 📚"
    border_gradient = "linear-gradient(45deg, #28a745, #1f77b4)" if final_score >= 80 else "linear-gradient(45deg, #ff9800, #e74c3c)"

    # Advanced Scorecard with animations, gradient border, and progress circle
    import streamlit as st
    import pandas as pd
    import re
    from datetime import datetime
    
    def inject_custom_css():
        """Inject advanced CSS styles for the learning platform"""
        st.markdown("""
        <style>
        /* Import Google Fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        /* Global Styles */
        .main .block-container {
            padding-top: 2rem;
            font-family: 'Inter', sans-serif;
        }
        
        /* Advanced Score Card */
        .score-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 24px;
            padding: 0;
            margin: 2rem auto;           /* This centers the card horizontally */
            box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3);
            position: relative;
            overflow: hidden;
            animation: scoreCardFloat 6s ease-in-out infinite;
            width: 690px;                /* Set your preferred width */
            height: 350px;               /* Set your preferred height */
            max-width: 95vw;             /* Responsive: not larger than viewport */
            max-height: 60vh;            /* Responsive: not taller than viewport */
            min-width: 220px;            /* Optional, for small screens */
            min-height: 140px;           /* Optional, for small screens */
        }
                
        .score-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 24px;
        }
        
        .score-content {
            position: relative;
            z-index: 2;
            padding: 3rem 2rem;
            text-align: center;
            color: white;
        }
        
        .score-title {
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 1rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .score-value {
            font-size: 4rem;
            font-weight: 800;
            margin: 1rem 0;
            text-shadow: 0 4px 8px rgba(0,0,0,0.3);
            animation: scoreCountUp 2s ease-out;
        }
        
        .score-label {
            font-size: 1.2rem;
            opacity: 0.9;
            font-weight: 400;
        }
        
        .score-progress {
            margin: 2rem 0;
            background: rgba(255, 255, 255, 0.2);
            border-radius: 50px;
            height: 12px;
            overflow: hidden;
        }
        
        .score-progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #ffd700, #ffed4e);
            border-radius: 50px;
            animation: progressFill 2s ease-out;
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.5);
        }
        
        /* Certificate Section */
       .certificate-section {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        border-radius: 20px;
        padding: 2.5rem;
        margin: 2rem 0;
        text-align: center;
        box-shadow: 0 15px 35px rgba(252, 182, 159, 0.3);
        position: relative;
        overflow: hidden;
        width: 690px;
        height: 350px;
        max-width: 95vw;
        max-height: 60vh;
        min-width: 220px;
        min-height: 140px;
        margin-left: auto;
        margin-right: auto;
    }
        
        .certificate-section::before {
            content: '🎉';
            position: absolute;
            top: -10px;
            left: -10px;
            font-size: 3rem;
            animation: celebrate 2s ease-in-out infinite;
        }
        
        .certificate-section::after {
            content: '🏆';
            position: absolute;
            top: -10px;
            right: -10px;
            font-size: 3rem;
            animation: celebrate 2s ease-in-out infinite reverse;
        }
        
        .certificate-btn {
            background: linear-gradient(135deg, #ffd700, #ffed4e) !important;
            color: #1a1a1a !important;
            font-size: 1.3rem !important;
            font-weight: 700 !important;
            padding: 1rem 2.5rem !important;
            border-radius: 15px !important;
            text-decoration: none !important;
            display: inline-block !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 10px 25px rgba(255, 215, 0, 0.4) !important;
            border: none !important;
        }
        
        .certificate-btn:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 15px 35px rgba(255, 215, 0, 0.6) !important;
        }
        
        /* Retry Section */
        .retry-section {
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
            border-radius: 20px;
            padding: 2rem;
            text-align: center;
            margin: 2rem 0;
            box-shadow: 0 12px 28px rgba(255, 154, 158, 0.3);
            width: 690px;
            height: 350px;
            max-width: 95vw;
            max-height: 60vh;
            min-width: 220px;
            min-height: 140px;
            margin-left: auto;
            margin-right: auto;
        }
                
        .mentor-btn {
            background: linear-gradient(135deg, #667eea, #764ba2) !important;
            color: white !important;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            padding: 0.8rem 2rem !important;
            border-radius: 12px !important;
            text-decoration: none !important;
            display: inline-block !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4) !important;
            border: none !important;
        }
        
        .mentor-btn:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 12px 30px rgba(102, 126, 234, 0.6) !important;
        }
        
        /* Question Cards */
        .question-card {
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 16px;
            margin: 1rem 0;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        
        .question-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 28px rgba(0, 0, 0, 0.15);
        }
        
        .question-header {
            padding: 1.5rem;
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            color: white;
            font-weight: 600;
            font-size: 1.1rem;
        }
        
        .question-content {
            padding: 2rem;
            background: white;
        }
        
        /* Code Display */
        .code-container {
            background: #1e1e1e;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.3);
            position: relative;
        }
        
        .code-container::before {
            content: 'SQL';
            position: absolute;
            top: 0.5rem;
            right: 1rem;
            background: #4CAF50;
            color: white;
            padding: 0.2rem 0.8rem;
            border-radius: 8px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        
        /* Feedback Section */
        .feedback-container {
            background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            border-radius: 20px;
            padding: 2.5rem;
            margin: 2rem 0;
            box-shadow: 0 15px 35px rgba(168, 237, 234, 0.3);
        }
        
        .feedback-header {
            font-size: 1.5rem;
            font-weight: 700;
            color: #2c3e50;
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .feedback-section {
            background: rgba(255, 255, 255, 0.7);
            border-radius: 12px;
            padding: 1.5rem;
            margin: 1rem 0;
            backdrop-filter: blur(5px);
        }
        
        .strength-item {
            background: linear-gradient(135deg, #d4fc79 0%, #96e6a1 100%);
            padding: 0.8rem 1.2rem;
            margin: 0.5rem 0;
            border-radius: 10px;
            color: #2d5016;
            font-weight: 500;
        }
        
        .weakness-item {
            background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
            padding: 0.8rem 1.2rem;
            margin: 0.5rem 0;
            border-radius: 10px;
            color: #8b4513;
            font-weight: 500;
        }
        
        /* Animations */
        @keyframes scoreCardFloat {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }
        
        @keyframes scoreCountUp {
            0% { transform: scale(0.5); opacity: 0; }
            100% { transform: scale(1); opacity: 1; }
        }
        
        @keyframes progressFill {
            0% { width: 0%; }
            100% { width: var(--progress-width, 0%); }
        }
        
        @keyframes celebrate {
            0%, 100% { transform: rotate(0deg) scale(1); }
            25% { transform: rotate(-10deg) scale(1.1); }
            75% { transform: rotate(10deg) scale(1.1); }
        }
        
        /* Button Styles */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 12px;
            border: none;
            padding: 0.75rem 2rem;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.5);
        }
        
        /* Responsive Design */
        @media (max-width: 768px) {
            .score-value {
                font-size: 3rem;
            }
            
            .score-content {
                padding: 2rem 1rem;
            }
            
            .certificate-section, .feedback-container {
                padding: 1.5rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
    def get_correct_wrong_counts(user_answers):
        correct = sum(1 for ans in user_answers if ans.get("is_correct", False))
        wrong = len(user_answers) - correct
        return correct, wrong
    correct_count, wrong_count = get_correct_wrong_counts(st.session_state.user_answers)
    
    def display_advanced_scorecard(final_score, correct_count, wrong_count):
        progress_width = min(final_score, 100)
        st.markdown(f"""
        <div class="score-card">
            <div class="score-content">
                <div class="score-title">📊 Your Final Score</div>
                <div class="score-value">{final_score:.1f}%</div>
                <div class="score-label">Performance Rating</div>
                <div style='font-size:1.35rem; margin: 14px 0 0 0;'><b>Questions Correct:</b> {correct_count} &nbsp; | &nbsp; <b>Wrong:</b> {wrong_count}</div>
                <div class="score-progress">
                    <div class="score-progress-fill" style="--progress-width: {progress_width}%; width: {progress_width}%;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    def display_certificate_section(final_score):
        """Display certificate eligibility section"""
        if final_score >= 50:
            st.markdown("""
            <div class="certificate-section">
                <h2 style='color:#2c3e50; margin-bottom: 1rem;'>🏆 Outstanding Performance!</h2>
                <p style='color:#5d6d7e; font-size: 1.1rem; margin-bottom: 2rem;'>
                    Congratulations! You've demonstrated excellent SQL skills and earned your certificate.
                </p>
                <a href="https://superprofile.bio/vp/corporate-bhaiya-sql-page" target="_blank" class="certificate-btn">
                    🎓 Claim Your Certificate
                </a>
            </div>
            """, unsafe_allow_html=True)
        else:
            score_needed = 50 - final_score
            st.markdown(f"""
            <div class="retry-section">
                <h3 style='color:#2c3e50; margin-bottom: 1rem;'>📚 Keep Learning & Growing!</h3>
                <p style='color:#5d6d7e; font-size: 1rem; margin-bottom: 1.5rem;'>
                    You need {score_needed:.1f}% more to earn your certificate. Don't give up!
                </p>
                <a href="https://www.corporatebhaiya.com/" target="_blank" class="mentor-btn">
                    🚀 Book a SQL Mentor To Guide You
                </a>
            </div>
            """, unsafe_allow_html=True)
    
    # def display_question_summary(user_answers):
    #     """Display question summary with advanced styling"""
    #     st.markdown("""
    #     <div style='text-align: center; margin: 3rem 0 2rem 0;'>
    #         <h2 style='background: linear-gradient(135deg, #667eea, #764ba2); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 2rem;'>
    #             📝 Detailed Question Analysis
    #         </h2>
    #         <p style='color: #6c757d; font-size: 1.1rem;'>Review your performance on each question</p>
    #     </div>
    #     """, unsafe_allow_html=True)
        
    #     for i, ans_data in enumerate(user_answers):
    #         q_num = i + 1
    #         is_correct = ans_data.get('is_correct', False)
    #         emoji = "✅" if is_correct else "❌"
            
    #         with st.expander(f"Question {q_num}: {ans_data['question']} {emoji}", expanded=False):
    #             # Question content container
    #             st.markdown('<div class="question-content">', unsafe_allow_html=True)
                
    #             # Student answer
    #             st.markdown("**🧑‍💻 Your Solution:**")
    #             st.code(ans_data.get('student_answer', '(No answer provided)'), language='sql')
                
    #             # Feedback
    #             st.markdown("**🤖 AI Mentor Feedback:**")
    #             feedback_text = ans_data.get("feedback", "_Feedback not available._")
    #             st.markdown(f'<div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #007bff;">{feedback_text}</div>', unsafe_allow_html=True)
                
    #             # Results comparison
    #             col1, col2 = st.columns(2)
                
    #             with col1:
    #                 st.markdown("**📊 Your Query Result:**")
    #                 display_simulation_result(ans_data.get("actual_result", "N/A"))
                
    #             if not is_correct:
    #                 with col2:
    #                     st.markdown("**✅ Expected Result:**")
    #                     display_simulation_result(ans_data.get("expected_result", "N/A"))
                
    #             st.markdown('</div>', unsafe_allow_html=True)
    
    def display_simulation_result(result):
        """Display simulation results with styling"""
        if isinstance(result, pd.DataFrame):
            st.dataframe(result, use_container_width=True)
        elif isinstance(result, str):
            st.markdown(f'<div class="code-container"><pre>{result}</pre></div>', unsafe_allow_html=True)
        else:
            st.write(result)
    
    def display_performance_analysis(user_answers, analyze_performance_func):
        """Display detailed performance analysis"""
        st.markdown("""
        <div style='text-align: center; margin: 3rem 0 2rem 0;'>
            <h2 style='background: linear-gradient(135deg, #f093fb, #f5576c); -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-weight: 800; font-size: 2rem;'>
                🧠 AI-Powered Performance Analysis
            </h2>
            <p style='color: #6c757d; font-size: 1.1rem;'>Get personalized insights to improve your SQL skills</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📊 Generate Detailed Analysis", key="show_analysis_results"):
            st.session_state.show_detailed_feedback = not st.session_state.get('show_detailed_feedback', False)
        
        if st.session_state.get('show_detailed_feedback', False):
            with st.spinner("🔍 Analyzing your performance..."):
                performance_summary = analyze_performance_func(user_answers)
                feedback_text = performance_summary.get("overall_feedback", "Analysis not available.")
                
                st.markdown('<div class="feedback-container">', unsafe_allow_html=True)
                st.markdown('<div class="feedback-header">📈 Your Comprehensive Performance Report</div>', unsafe_allow_html=True)
                
                # Parse feedback sections
                try:
                    sections = re.split(r'(Overall Impression:|Strengths:|Areas for Improvement:|Next Steps / Encouragement:)', feedback_text)
                    section_dict = {}
                    for i in range(1, len(sections), 2):
                        if i+1 < len(sections):
                            section_dict[sections[i].strip(':')] = sections[i+1].strip()
                except:
                    section_dict = {"Full Feedback": feedback_text}
                
                # Overall impression
                if "Overall Impression" in section_dict:
                    st.markdown("### 🌟 Overall Impression")
                    st.markdown(f'<div style="background: rgba(255,255,255,0.8); padding: 1.5rem; border-radius: 12px; margin: 1rem 0;">{section_dict["Overall Impression"]}</div>', unsafe_allow_html=True)
                
                # Strengths
                st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
                st.markdown("### ✨ Your Strengths")
                if "Strengths" in section_dict:
                    strengths = [s.strip() for s in section_dict["Strengths"].split('\n') if s.strip()]
                    for strength in strengths:
                        st.markdown(f'<div class="strength-item">✔ {strength}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="strength-item">✔ Keep practicing to identify your strengths!</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Areas for improvement
                st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
                st.markdown("### 🎯 Areas for Improvement")
                if "Areas for Improvement" in section_dict:
                    improvements = [s.strip() for s in section_dict["Areas for Improvement"].split('\n') if s.strip()]
                    for improvement in improvements:
                        st.markdown(f'<div class="weakness-item">📝 {improvement}</div>', unsafe_allow_html=True)
                else:
                    st.markdown('<div class="weakness-item">📝 Continue practicing to reach the next level!</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Next steps
                if "Next Steps / Encouragement" in section_dict:
                    st.markdown("### 🚀 Recommended Next Steps")
                    st.markdown(f'<div style="background: linear-gradient(135deg, #d299c2, #fef9d7); padding: 1.5rem; border-radius: 12px; margin: 1rem 0; color: #2c3e50;">{section_dict["Next Steps / Encouragement"]}</div>', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    def display_retry_section():
        """Display retry section with advanced styling"""
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔄 Start New Quiz", key="retry_quiz", use_container_width=True):
                # Reset session state
                for key in ['user_answers', 'current_question', 'quiz_started', 'quiz_completed', 'show_detailed_feedback']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    
    # Main function to display the complete results page
    def display_advanced_results_page(final_score, user_answers, analyze_performance_func):
        """Display the complete advanced results page"""
        
        # Inject custom CSS
        inject_custom_css()
        
        # Advanced scorecard
        display_advanced_scorecard(final_score, correct_count, wrong_count)
        
        # Certificate section
        display_certificate_section(final_score)
        
        # Separator
        st.markdown("---")
        
        # Question summary
        # display_question_summary(user_answers)
        
        # Performance analysis
        display_performance_analysis(user_answers, analyze_performance_func)
        
        # Retry section
        display_retry_section()
        
        # Footer
        st.markdown("""
        <div style='text-align: center; margin-top: 4rem; padding: 2rem; background: linear-gradient(135deg, #667eea, #764ba2); border-radius: 16px; color: white;'>
            <h3>🎓 Corporate Bhaiya Learning Platform</h3>
            <p>Empowering careers through expert mentorship</p>
            <p style='opacity: 0.8; font-size: 0.9rem;'>© 2025 All rights reserved</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Usage example:
    final_score = calculate_score(st.session_state.user_answers)

    display_advanced_results_page(final_score , st.session_state.user_answers, analyze_performance)
    
    


