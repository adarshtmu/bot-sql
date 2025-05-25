import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import duckdb

# --- Custom CSS ---
# Updated to increase font sizes globally and for specific elements
# --- Custom CSS ---
hide_streamlit_style = """
    <style>
        /* Apply zoom-out effect to the entire app */
        html, body, .stApp {
            zoom: 1.15 !important; /* Adjust this value to control zoom level (e.g., 0.85 = 85% zoom) */
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
sql_questions = [    {"question": "Write a SQL query to get all details about users from the 'users' table.", "correct_answer_example": "SELECT * FROM users;", "sample_table": users_table, "relevant_tables": ["users"]},
  #   {"question": "Write a SQL query to count the total number of users in the 'users' table.", "correct_answer_example": "SELECT COUNT(*) AS user_count FROM users;", "sample_table": users_table, "relevant_tables": ["users"]},
  #   {"question": "Write a SQL query to get all users older than 30 from the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE age > 30;", "sample_table": users_table, "relevant_tables": ["users"]},
  #   {"question": "Write a SQL query to find all orders with a status of 'Pending' from the 'orders' table.", "correct_answer_example": "SELECT * FROM orders WHERE status = 'Pending';", "sample_table": orders_table, "relevant_tables": ["orders"]},
  #   {"question": "Write a SQL query to find users from 'chicago' in the 'users' table (test case-insensitivity).", "correct_answer_example": "SELECT * FROM users WHERE city = 'Chicago';", "sample_table": users_table, "relevant_tables": ["users"]},
  #   {"question": "Write a SQL query to find the most recent order from the 'orders' table by order date.", "correct_answer_example": "SELECT * FROM orders ORDER BY order_date DESC LIMIT 1;", "sample_table": orders_table, "relevant_tables": ["orders"]},
  #   {"question": "Write a SQL query to find the average order amount from the 'orders' table.", "correct_answer_example": "SELECT AVG(amount) AS average_amount FROM orders;", "sample_table": orders_table, "relevant_tables": ["orders"]},
  #   {"question": "Write a SQL query to find users from 'New York' or 'Chicago' in the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE city IN ('New York', 'Chicago');", "sample_table": users_table, "relevant_tables": ["users"]},
  # {
  #   "question": "Write a SQL query to list all users who have never placed any orders. Use the 'users' and 'orders' tables.",
  #   "correct_answer_example": "SELECT u.* FROM users u LEFT JOIN orders o ON u.user_id = o.user_id WHERE o.user_id IS NULL;",
  #   "sample_table": "users_table",
  #   "relevant_tables": ["users", "orders"]
  # },
  #   {"question": "Write a SQL query to calculate the total amount spent by each user by joining the 'users' and 'orders' tables.", "correct_answer_example": "SELECT u.name, SUM(o.amount) AS total_spent FROM users u JOIN orders o ON u.user_id = o.user_id GROUP BY u.name ORDER BY u.name;", "sample_table": users_table, "relevant_tables": ["users", "orders"]}

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
                correct_summary += f"  - {q_text}\n"
            correct_summary = correct_summary.strip()
        else:
            correct_summary = "Is baar koi jawaab sahi nahi hua."
        
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

# --- Start Screen ---
# --- Start Screen ---
if not st.session_state.quiz_started:
    st.title("🚀 SQL Mentor - Interactive SQL Practice")
    st.markdown("### Finish the Quiz Successfully to Unlock Your SQL Certificate")
    st.markdown("""
        **📌 Important Notes:**
        - To be eligible for a certificate, you must achieve a score of at least 80%.
        - This quiz uses standard **SQL syntax** (similar to MySQL/PostgreSQL).
        - String comparisons (like `WHERE city = 'new york'` or `WHERE status = "pending"`) are simulated to be **case-insensitive** for common text columns (`status`, `city`).
        - **Both single quotes (') and double quotes (") are accepted** for string literals in this simulation.
        - Your queries are evaluated by an AI for correctness and logic.
        - Query simulation is powered by DuckDB to show results on sample data.
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
        try:
            table_overview_data = {"Table": list(original_tables.keys()),
                                   "Rows": [len(df) for df in original_tables.values()],
                                   "Columns": [len(df.columns) for df in original_tables.values()]}
            st.dataframe(pd.DataFrame(table_overview_data), hide_index=True)
        except Exception as e:
            st.error(f"Error displaying table overview: {e}")
    
    st.write("### 🔍 Table Previews")
    try:
        tab1, tab2 = st.tabs(["Users Table", "Orders Table"])
        with tab1: st.dataframe(users_table, hide_index=True, use_container_width=False)
        with tab2: st.dataframe(orders_table, hide_index=True, use_container_width=False)
    except Exception as e:
        st.error(f"Error displaying table previews: {e}")
    
    with st.expander("📝 Quiz Ke Baare Mein"):
        st.write(f"""
        - Aapko {len(sql_questions)} SQL query challenges solve karne honge.
        - Har jawaab ke baad AI Mentor se immediate feedback milega.
        - **SQL Dialect Focus:** Standard SQL (MySQL/PostgreSQL like).
        - Case-insensitivity for `status` and `city` columns in `WHERE =` clauses is simulated.
        - String literals can be enclosed in single quotes (`'...'`) or double quotes (`"..."`).
        """)
    
    if st.button("🚀 Start SQL Challenge!", type="primary"):
        st.session_state.quiz_started = True
        st.session_state.user_answers = []
        st.session_state.current_question = 0
        st.session_state.quiz_completed = False

# --- Quiz In Progress Screen ---
elif st.session_state.quiz_started and not st.session_state.quiz_completed:
    st.title("✍️ SQL Query Challenge")
    
    if st.session_state.user_answers:
        st.markdown("---")
        st.subheader("📖 Ab Tak Ke Jawaab Aur Feedback")
        for i, ans_data in enumerate(st.session_state.user_answers):
            q_num = i + 1
            is_correct = ans_data.get('is_correct', False)
            with st.expander(f"Question {q_num}: {ans_data['question']} {get_emoji(is_correct)}", expanded=False):
                st.write(f"**Aapka Jawaab:**")
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
    
    user_query = st.text_area("Apna SQL Query Yahan Likhein:", height=150, key=f"query_input_{current_q_index}")
    
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

# --- Quiz Completed Screen ---
# --- Quiz Completed Screen ---
elif st.session_state.quiz_completed:


    # --- 1. Answer/Feedback Summary first ---
    st.markdown("---")
    st.subheader("📝 Aapke Jawaab Aur Feedback Ka Summary")
    for i, ans_data in enumerate(st.session_state.user_answers):
        q_num = i + 1
        is_correct = ans_data.get('is_correct', False)
        with st.expander(f"Question {q_num}: {ans_data['question']} {get_emoji(is_correct)}", expanded=False):
            st.write(f"**Aapka Jawaab:**")
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
    st.subheader("💡 AI Mentor Se Detailed Performance Analysis")
    if st.button("📊 Show Detailed Analysis", key="show_analysis"):
        st.session_state.show_detailed_feedback = not st.session_state.show_detailed_feedback
    if st.session_state.show_detailed_feedback:
        with st.spinner("🧠 Performance analysis generate ho raha hai..."):
            performance_summary = analyze_performance(st.session_state.user_answers)
            feedback_text = performance_summary.get("overall_feedback", "Analysis available nahi hai.")
            with st.container():
                st.markdown('<div class="feedback-container">', unsafe_allow_html=True)
                st.markdown('<div class="feedback-header">📈 Aapki Performance Ka Vistaar Se Analysis</div>', unsafe_allow_html=True)
                try:
                    sections = re.split(r'(Overall Impression:|Strengths:|Areas for Improvement:|Next Steps / Encouragement:)', feedback_text)
                    section_dict = {}
                    for i in range(1, len(sections), 2):
                        section_dict[sections[i].strip(':')] = sections[i+1].strip()
                except:
                    section_dict = {"Full Feedback": feedback_text}
                if "Overall Impression" in section_dict:
                    st.markdown("### 🌟 Overall Impression")
                    st.markdown(section_dict["Overall Impression"])
                st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
                st.markdown("### ✅ Strengths")
                if "Strengths" in section_dict:
                    strengths = section_dict["Strengths"].split('\n')
                    for strength in strengths:
                        if strength.strip():
                            st.markdown(f'<div class="strength-item">✔ {strength.strip()}</div>', unsafe_allow_html=True)
                elif performance_summary.get("strengths"):
                    for strength in performance_summary["strengths"]:
                        st.markdown(f'<div class="strength-item">✔ {strength}</div>', unsafe_allow_html=True)
                else:
                    st.markdown("Koi specific strengths identify nahi hue. Aur practice karo!")
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('<div class="feedback-section">', unsafe_allow_html=True)
                st.markdown("### 📝 Areas for Improvement")
                if "Areas for Improvement" in section_dict:
                    weaknesses = section_dict["Areas for Improvement"].split('\n')
                    for weakness in weaknesses:
                        if weakness.strip():
                            st.markdown(f'<div class="weakness-item">➡ {weakness.strip()}</div>', unsafe_allow_html=True)
                elif performance_summary.get("weaknesses"):
                    for weakness in performance_summary["weaknesses"]:
                        st.markdown(f'<div class="weakness-item">➡ {weakness}</div>', unsafe_allow_html=True)
                else:
                    st.markdown("Koi major weaknesses nahi! Bas practice jari rakho.")
                st.markdown('</div>', unsafe_allow_html=True)
                if "Next Steps / Encouragement" in section_dict:
                    st.markdown("### 🚀 Next Steps")
                    st.markdown(section_dict["Next Steps / Encouragement"])
                if "Full Feedback" in section_dict:
                    st.markdown("### 📋 Complete Feedback")
                    st.markdown(section_dict["Full Feedback"])
                st.markdown('</div>', unsafe_allow_html=True)

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
    st.markdown("---")
final_score = calculate_score(st.session_state.user_answers)

# Enhanced scoring logic with more granular feedback
def get_score_details(score):
    if score >= 95:
        return {
            "grade": "A+", "color": "#00c851", "bg_gradient": "linear-gradient(135deg, #00c851, #007E33)",
            "message": "Exceptional Mastery! 🌟", "emoji": "🏆", "title": "OUTSTANDING",
            "description": "You've demonstrated exceptional understanding of the material!"
        }
    elif score >= 85:
        return {
            "grade": "A", "color": "#28a745", "bg_gradient": "linear-gradient(135deg, #28a745, #20c997)",
            "message": "Excellent Performance! ⭐", "emoji": "🎯", "title": "EXCELLENT",
            "description": "Great job! You have a strong grasp of the concepts."
        }
    elif score >= 75:
        return {
            "grade": "B+", "color": "#17a2b8", "bg_gradient": "linear-gradient(135deg, #17a2b8, #007bff)",
            "message": "Very Good Work! 💪", "emoji": "👍", "title": "VERY GOOD",
            "description": "Well done! You're on the right track."
        }
    elif score >= 65:
        return {
            "grade": "B", "color": "#007bff", "bg_gradient": "linear-gradient(135deg, #007bff, #6610f2)",
            "message": "Good Effort! 📈", "emoji": "👌", "title": "GOOD",
            "description": "Nice work! Keep building on this foundation."
        }
    elif score >= 50:
        return {
            "grade": "C", "color": "#ffc107", "bg_gradient": "linear-gradient(135deg, #ffc107, #e0a800)",
            "message": "Keep Going! 🔥", "emoji": "💡", "title": "FAIR",
            "description": "You're making progress! Review and try again."
        }
    else:
        return {
            "grade": "D", "color": "#dc3545", "bg_gradient": "linear-gradient(135deg, #dc3545, #c82333)",
            "message": "More Practice Needed 📚", "emoji": "📖", "title": "NEEDS WORK",
            "description": "Don't give up! Learning takes time and practice."
        }

score_details = get_score_details(final_score)

# Advanced Scorecard with glassmorphism, 3D effects, and micro-animations
st.markdown(
    f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
        
        @keyframes scoreReveal {{
            0% {{ 
                opacity: 0; 
                transform: scale(0.8) rotateY(-15deg); 
                filter: blur(10px);
            }}
            50% {{
                opacity: 0.7;
                transform: scale(1.05) rotateY(5deg);
                filter: blur(2px);
            }}
            100% {{ 
                opacity: 1; 
                transform: scale(1) rotateY(0deg); 
                filter: blur(0px);
            }}
        }}
        
        @keyframes progressFill {{
            0% {{ stroke-dasharray: 0 314; }}
            100% {{ stroke-dasharray: {final_score * 3.14} 314; }}
        }}
        
        @keyframes pulseGlow {{
            0%, 100% {{ box-shadow: 0 0 20px rgba(0,123,255,0.3), 0 15px 40px rgba(0,0,0,0.1); }}
            50% {{ box-shadow: 0 0 40px rgba(0,123,255,0.5), 0 20px 60px rgba(0,0,0,0.15); }}
        }}
        
        @keyframes floatBadge {{
            0%, 100% {{ transform: translateY(0px) rotate(0deg); }}
            25% {{ transform: translateY(-5px) rotate(1deg); }}
            75% {{ transform: translateY(-2px) rotate(-1deg); }}
        }}
        
        @keyframes shimmer {{
            0% {{ background-position: -200% 0; }}
            100% {{ background-position: 200% 0; }}
        }}
        
        .scorecard-main {{
            background: linear-gradient(145deg, rgba(255,255,255,0.95), rgba(255,255,255,0.85));
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 24px;
            padding: 40px;
            margin: 40px auto;
            max-width: 600px;
            position: relative;
            overflow: hidden;
            animation: scoreReveal 1.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            box-shadow: 
                0 20px 60px rgba(0,0,0,0.1),
                0 0 0 1px rgba(255,255,255,0.5) inset;
        }}
        
        .scorecard-main::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent);
            animation: shimmer 2s infinite;
        }}
        
        .score-header {{
            text-align: center;
            margin-bottom: 30px;
            position: relative;
            z-index: 2;
        }}
        
        .score-title {{
            font-family: 'Inter', sans-serif;
            font-size: 1.8rem;
            font-weight: 800;
            background: {score_details['bg_gradient']};
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
            letter-spacing: 1px;
        }}
        
        .score-subtitle {{
            font-family: 'Inter', sans-serif;
            font-size: 1rem;
            color: #6c757d;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        
        .score-display {{
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 40px;
            margin: 40px 0;
            position: relative;
            z-index: 2;
        }}
        
        .circular-progress {{
            position: relative;
            width: 180px;
            height: 180px;
        }}
        
        .circular-progress svg {{
            width: 100%;
            height: 100%;
            transform: rotate(-90deg);
            filter: drop-shadow(0 5px 15px rgba(0,0,0,0.1));
        }}
        
        .progress-bg {{
            fill: none;
            stroke: #e9ecef;
            stroke-width: 12;
        }}
        
        .progress-bar {{
            fill: none;
            stroke: {score_details['color']};
            stroke-width: 12;
            stroke-linecap: round;
            stroke-dasharray: 0 314;
            animation: progressFill 2s ease-out 0.5s forwards;
            filter: drop-shadow(0 0 8px {score_details['color']}40);
        }}
        
        .score-center {{
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            text-align: center;
        }}
        
        .score-percentage {{
            font-family: 'Inter', sans-serif;
            font-size: 2.5rem;
            font-weight: 900;
            color: {score_details['color']};
            line-height: 1;
            margin-bottom: 5px;
        }}
        
        .score-grade {{
            font-family: 'Inter', sans-serif;
            font-size: 1.2rem;
            font-weight: 700;
            color: {score_details['color']};
            opacity: 0.8;
        }}
        
        .score-details {{
            text-align: center;
            flex: 1;
        }}
        
        .performance-badge {{
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: {score_details['bg_gradient']};
            color: white;
            padding: 12px 24px;
            border-radius: 50px;
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 1.1rem;
            margin-bottom: 20px;
            animation: floatBadge 3s ease-in-out infinite;
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }}
        
        .performance-message {{
            font-family: 'Inter', sans-serif;
            font-size: 1.4rem;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 12px;
        }}
        
        .performance-description {{
            font-family: 'Inter', sans-serif;
            font-size: 1rem;
            color: #6c757d;
            line-height: 1.6;
            max-width: 300px;
            margin: 0 auto;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 20px;
            margin-top: 30px;
            position: relative;
            z-index: 2;
        }}
        
        .stat-item {{
            background: rgba(255,255,255,0.8);
            border: 1px solid rgba(255,255,255,0.3);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            backdrop-filter: blur(10px);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .stat-item:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        .stat-value {{
            font-family: 'Inter', sans-serif;
            font-size: 1.8rem;
            font-weight: 800;
            color: {score_details['color']};
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-family: 'Inter', sans-serif;
            font-size: 0.9rem;
            color: #6c757d;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .decoration-elements {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            pointer-events: none;
            z-index: 1;
        }}
        
        .decoration-circle {{
            position: absolute;
            border-radius: 50%;
            background: rgba(0,123,255,0.05);
        }}
        
        .decoration-circle:nth-child(1) {{
            width: 100px;
            height: 100px;
            top: 20px;
            right: 30px;
            animation: floatBadge 4s ease-in-out infinite;
        }}
        
        .decoration-circle:nth-child(2) {{
            width: 60px;
            height: 60px;
            bottom: 40px;
            left: 40px;
            animation: floatBadge 3s ease-in-out infinite reverse;
        }}
        
        .decoration-circle:nth-child(3) {{
            width: 80px;
            height: 80px;
            top: 50%;
            left: 20px;
            animation: floatBadge 5s ease-in-out infinite;
        }}
    </style>
    
    <div class="scorecard-main">
        <div class="decoration-elements">
            <div class="decoration-circle"></div>
            <div class="decoration-circle"></div>
            <div class="decoration-circle"></div>
        </div>
        
        <div class="score-header">
            <div class="score-title">QUIZ RESULTS</div>
            <div class="score-subtitle">Performance Assessment</div>
        </div>
        
        <div class="score-display">
            <div class="circular-progress">
                <svg viewBox="0 0 120 120">
                    <circle class="progress-bg" cx="60" cy="60" r="50"/>
                    <circle class="progress-bar" cx="60" cy="60" r="50"/>
                </svg>
                <div class="score-center">
                    <div class="score-percentage">{final_score:.0f}%</div>
                    <div class="score-grade">{score_details['grade']}</div>
                </div>
            </div>
            
            <div class="score-details">
                <div class="performance-badge">
                    <span>{score_details['emoji']}</span>
                    <span>{score_details['title']}</span>
                </div>
                <div class="performance-message">{score_details['message']}</div>
                <div class="performance-description">{score_details['description']}</div>
            </div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value">{final_score:.1f}</div>
                <div class="stat-label">Score</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{len([a for a in st.session_state.user_answers if a['is_correct']])}</div>
                <div class="stat-label">Correct</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{len(st.session_state.user_answers)}</div>
                <div class="stat-label">Total</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{score_details['grade']}</div>
                <div class="stat-label">Grade</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Certificate eligibility and action buttons
if final_score >= 80:
    st.markdown(
        f"""
        <div style='text-align: center; margin: 30px 0;'>
            <div style='
                background: linear-gradient(135deg, #28a745, #20c997);
                color: white;
                padding: 25px;
                border-radius: 20px;
                margin-bottom: 25px;
                box-shadow: 0 10px 30px rgba(40, 167, 69, 0.3);
                animation: pulseGlow 2s ease-in-out infinite;
            '>
                <h2 style='margin: 0; font-family: Inter, sans-serif; font-weight: 700;'>
                    🎉 Congratulations! You've Earned a Certificate! 🎉
                </h2>
                <p style='margin: 10px 0 0 0; font-size: 1.1rem; opacity: 0.9;'>
                    Outstanding performance! You've demonstrated mastery of the material.
                </p>
            </div>
            
            <a href="https://superprofile.bio/vp/corporate-bhaiya-sql-page" target="_blank" style="
                display: inline-flex;
                align-items: center;
                gap: 12px;
                background: linear-gradient(135deg, #ffc107, #e0a800);
                color: #212529;
                font-family: 'Inter', sans-serif;
                font-size: 1.3rem;
                font-weight: 700;
                padding: 18px 36px;
                border-radius: 50px;
                text-decoration: none;
                box-shadow: 0 8px 25px rgba(255, 193, 7, 0.4);
                transition: all 0.3s ease;
                text-transform: uppercase;
                letter-spacing: 1px;
            " onmouseover="this.style.transform='translateY(-3px) scale(1.05)'; this.style.boxShadow='0 12px 35px rgba(255, 193, 7, 0.6)';" 
               onmouseout="this.style.transform='translateY(0) scale(1)'; this.style.boxShadow='0 8px 25px rgba(255, 193, 7, 0.4)';">
                <span style="font-size: 1.5rem;">🏆</span>
                <span>Claim Your Certificate</span>
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )
else:
    st.markdown(
        f"""
        <div style='text-align: center; margin: 30px 0;'>
            <div style='
                background: linear-gradient(135deg, #6c757d, #5a6268);
                color: white;
                padding: 25px;
                border-radius: 20px;
                margin-bottom: 25px;
                box-shadow: 0 10px 30px rgba(108, 117, 125, 0.3);
            '>
                <h3 style='margin: 0; font-family: Inter, sans-serif; font-weight: 600;'>
                    📚 Keep Learning to Earn Your Certificate!
                </h3>
                <p style='margin: 10px 0 0 0; font-size: 1rem; opacity: 0.9;'>
                    You need 80% or higher to qualify for certification. Don't give up!
                </p>
            </div>
            
            <div style='display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;'>
                <a href="https://www.corporatebhaiya.com/" target="_blank" style="
                    display: inline-flex;
                    align-items: center;
                    gap: 10px;
                    background: linear-gradient(135deg, #007bff, #0056b3);
                    color: white;
                    font-family: 'Inter', sans-serif;
                    font-size: 1.1rem;
                    font-weight: 600;
                    padding: 14px 28px;
                    border-radius: 25px;
                    text-decoration: none;
                    box-shadow: 0 6px 20px rgba(0, 123, 255, 0.3);
                    transition: all 0.3s ease;
                " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 25px rgba(0, 123, 255, 0.4)';" 
                   onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 6px 20px rgba(0, 123, 255, 0.3)';">
                    <span>🚀</span>
                    <span>Book Mentor Session</span>
                </a>
                
                <a href="#" onclick="document.querySelector('[data-testid=\\\"stButton\\\"] button').click(); return false;" style="
                    display: inline-flex;
                    align-items: center;
                    gap: 10px;
                    background: linear-gradient(135deg, #17a2b8, #138496);
                    color: white;
                    font-family: 'Inter', sans-serif;
                    font-size: 1.1rem;
                    font-weight: 600;
                    padding: 14px 28px;
                    border-radius: 25px;
                    text-decoration: none;
                    box-shadow: 0 6px 20px rgba(23, 162, 184, 0.3);
                    transition: all 0.3s ease;
                " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 8px 25px rgba(23, 162, 184, 0.4)';" 
                   onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 6px 20px rgba(23, 162, 184, 0.3)';">
                    <span>📚</span>
                    <span>Study & Retry</span>
                </a>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

# Try Again Button with enhanced styling
st.markdown("<br>", unsafe_allow_html=True)
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🔄 Try Again", use_container_width=True, type="primary"):
        st.session_state.user_answers = []
        st.session_state.current_question = 0
        st.session_state.quiz_started = False
        st.session_state.quiz_completed = False
        st.session_state.show_detailed_feedback = False
        st.rerun()
