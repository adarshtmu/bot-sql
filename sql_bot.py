import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import duckdb

# --- Custom CSS for EdTech feel ---
edtech_css = """
    <style>
        header, #MainMenu, footer, .viewerBadge_container__1QSob, .stDeployButton,
        [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stDeployButton"],
        .st-emotion-cache-1r8d6ul, .st-emotion-cache-1jicfl2 {
            display: none !important;
        }
        body, .stMarkdown, .stText, .stTextArea, .stButton button, .stLinkButton a {
            font-size: 18px !important;
        }
        h1 {font-size: 36px !important;}
        h2 {font-size: 28px !important;}
        h3 {font-size: 24px !important;}
        .ed-card {
            background: #f7fbff;
            border-radius: 16px;
            box-shadow: 0 2px 12px #0001;
            padding: 24px 28px;
            margin-bottom: 32px;
        }
        .ed-btn-main {
            font-size: 22px !important;
            padding: 15px 34px !important;
            color: white !important;
            background-color: #ec407a;
            border-radius: 12px;
            margin-bottom: 10px;
        }
        .ed-btn-sec {
            font-size: 18px !important;
            padding: 8px 18px !important;
            border-radius: 8px;
            background: #d1e7fd !important;
            color: #1f77b4 !important;
        }
        .ed-feedback {
            background: #fef6e4;
            border-radius: 12px;
            padding: 18px 22px;
            margin: 12px 0;
            font-size: 18px !important;
        }
        .ed-hint {
            background: #e0f7fa;
            border-radius: 10px;
            padding: 10px 18px;
            margin: 10px 0;
            font-size: 16px;
        }
        .ed-progress-label {
            font-size: 18px;
            font-weight: 500;
            color: #333;
            margin-bottom: -18px;
        }
    </style>
"""
st.markdown(edtech_css, unsafe_allow_html=True)

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

# --- SQL Questions List with Hints and Concepts ---
sql_questions = [
    {
        "question": "Write a SQL query to get all details about users from the 'users' table.",
        "correct_answer_example": "SELECT * FROM users;",
        "sample_table": users_table,
        "relevant_tables": ["users"],
        "hint": "Use SELECT * to get all columns. The table name is users.",
        "concept": "The SELECT statement retrieves data from a table. SELECT * FROM users returns all columns for all records in the users table."
    },
    # You can add more questions with "hint" and "concept" fields for each.
]

# --- Session State Initialization ---
if "user_answers" not in st.session_state: st.session_state.user_answers = []
if "current_question" not in st.session_state: st.session_state.current_question = 0
if "quiz_started" not in st.session_state: st.session_state.quiz_started = False
if "quiz_completed" not in st.session_state: st.session_state.quiz_completed = False
if "show_detailed_feedback" not in st.session_state: st.session_state.show_detailed_feedback = False
if "show_hint" not in st.session_state: st.session_state.show_hint = False


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
            st.dataframe(result_data.reset_index(drop=True), hide_index=True, use_container_width=True)
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
if not st.session_state.quiz_started:
    st.title("🚀 SQL Mentor - Interactive SQL Practice")
    st.markdown("""
        <div class='ed-card'>
            <h2>Apne SQL Skills Ko Test Aur Improve Karein!</h2>
            <ul>
                <li><b>AI Mentor:</b> Har sawaal ke baad instant feedback!</li>
                <li><b>Hints &amp; Concepts:</b> Doubt ho toh hint aur concept samjho!</li>
                <li><b>Progress Bar:</b> Dekhein kitna aagey badhe!</li>
                <li><b>Certificate:</b> 80%+ score pe certificate milega!</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("### 🔍 Table Previews")
    tab1, tab2 = st.tabs(["Users Table", "Orders Table"])
    with tab1: st.dataframe(users_table, hide_index=True, use_container_width=True)
    with tab2: st.dataframe(orders_table, hide_index=True, use_container_width=True)
    if st.button("🚀 Start SQL Challenge!", key="start_btn", help="Start the quiz!", type="primary"):
        st.session_state.quiz_started = True
        st.session_state.user_answers = []
        st.session_state.current_question = 0
        st.session_state.quiz_completed = False
        st.session_state.show_detailed_feedback = False
        st.rerun()

# --- Quiz In Progress Screen ---
elif st.session_state.quiz_started and not st.session_state.quiz_completed:
    current_q_index = st.session_state.current_question
    question_data = sql_questions[current_q_index]
    total_questions = len(sql_questions)

    # Top progress bar & counter
    st.markdown(f"<div class='ed-progress-label'>Question {current_q_index+1} of {total_questions}</div>", unsafe_allow_html=True)
    st.progress((current_q_index + 1) / total_questions)

    # Card-style question UI
    st.markdown(f"""
        <div class='ed-card'>
            <h3>🔍 Challenge</h3>
            <div style='font-size:20px; margin-bottom:12px;'>{question_data['question']}</div>
        </div>
    """, unsafe_allow_html=True)

    # Sample Table Preview(s)
    st.markdown("**Sample Table Preview(s):**")
    for table_name in question_data["relevant_tables"]:
        st.dataframe(original_tables[table_name], hide_index=True, use_container_width=True)

    # Hint section
    if st.button("💡 Need a Hint?", key="hint_btn"):
        st.session_state.show_hint = True
    if st.session_state.show_hint:
        st.markdown(f"<div class='ed-hint'>Hint: {question_data.get('hint','No hint available.')}</div>", unsafe_allow_html=True)

    # Concept section
    with st.expander("📚 Learn the Concept"):
        st.write(question_data.get("concept", "No concept summary available for this question."))

    user_query = st.text_area("Apna SQL Query Yahan Likhein:", height=150, key=f"query_input_{current_q_index}")

    if st.button("✅ Submit Query", key=f"submit_{current_q_index}", help="Submit your answer!"):
        if user_query and user_query.strip():
            with st.spinner("🔄 AI Mentor is checking your answer..."):
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
                st.session_state.show_hint = False  # Reset hint for next q
                # Balloons/confetti for correct answers
                if is_correct:
                    st.balloons()
                else:
                    st.snow()
                # Next question or finish
                if current_q_index + 1 < total_questions:
                    st.session_state.current_question += 1
                else:
                    st.session_state.quiz_completed = True
                st.rerun()
        else:
            st.warning("⚠️ Please enter your SQL query before submitting.")

    # Show answer history
    if st.session_state.user_answers:
        st.markdown("---")
        st.subheader("📖 Previous Answers & Feedback")
        for i, ans_data in enumerate(reversed(st.session_state.user_answers)):
            q_num = len(st.session_state.user_answers) - i
            is_correct = ans_data.get('is_correct', False)
            with st.expander(f"Question {q_num}: {ans_data['question']} {'✅' if is_correct else '❌'}", expanded=False):
                st.write("**Your Answer:**")
                st.code(ans_data.get('student_answer', '(No answer provided)'), language='sql')
                st.markdown(f"<div class='ed-feedback'>{ans_data.get('feedback', '_Feedback not available._')}</div>", unsafe_allow_html=True)
                display_simulation("Simulated Result (Your Query Output)", ans_data.get("actual_result", "N/A"))
                if not is_correct:
                    display_simulation("Simulated Result (Correct Query Output)", ans_data.get("expected_result", "N/A"))

# --- Quiz Completed Screen ---
elif st.session_state.quiz_completed:
    st.balloons()
    final_score = calculate_score(st.session_state.user_answers)
    st.markdown(
        f"""
        <div style='background:#e6faed;border-radius:18px;box-shadow:0 2px 10px #0002;padding:30px;margin:30px 0;text-align:center;'>
            <h1 style='color:#28a745;'>🎉 Congratulations!</h1>
            <h2 style='color:#1f77b4;'>You've completed the SQL Challenge!</h2>
            <div style='font-size:2.5rem;font-weight:bold;color:#28a745;'>{final_score:.2f}%</div>
            <div style='font-size:1.2rem;color:#888;'>Final Score</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.progress(final_score / 100)
    if final_score >= 80:
        st.markdown(
            """
            <div style='text-align:center; margin-top: 20px;'>
                <h3 style='color:#007bff;'>🏆 Great job! You're eligible for a certificate.</h3>
                <a href="https://superprofile.bio/vp/corporate-bhaiya-sql-page" target="_blank" class="ed-btn-main">🎓 Get Your Certificate</a>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div style='text-align:center; margin-top: 20px;'>
                <h3 style='color:#e74c3c;'>📚 Keep practicing to earn a certificate!</h3>
                <a href="https://www.corporatebhaiya.com/" target="_blank" class="ed-btn-sec">🚀 Book a Mentor Session</a>
            </div>
            """,
            unsafe_allow_html=True
        )
    if st.button("🔄 Try Again?", key="try_again_btn"):
        st.session_state.user_answers = []
        st.session_state.current_question = 0
        st.session_state.quiz_started = False
        st.session_state.quiz_completed = False
        st.session_state.show_detailed_feedback = False
        st.session_state.show_hint = False
        st.rerun()
    st.markdown("---")
    st.subheader("📝 Your Answers & Feedback Summary")
    for i, ans_data in enumerate(st.session_state.user_answers):
        q_num = i + 1
        is_correct = ans_data.get('is_correct', False)
        with st.expander(f"Question {q_num}: {ans_data['question']} {'✅' if is_correct else '❌'}", expanded=False):
            st.write("**Your Answer:**")
            st.code(ans_data.get('student_answer', '(No answer provided)'), language='sql')
            st.markdown(f"<div class='ed-feedback'>{ans_data.get('feedback', '_Feedback not available._')}</div>", unsafe_allow_html=True)
            display_simulation("Simulated Result (Your Query Output)", ans_data.get("actual_result", "N/A"))
            if not is_correct:
                display_simulation("Simulated Result (Correct Query Output)", ans_data.get("expected_result", "N/A"))
    st.markdown("---")
    st.subheader("💡 AI Mentor Detailed Performance Analysis")
    if st.button("📊 Show Detailed Analysis", key="show_analysis"):
        st.session_state.show_detailed_feedback = not st.session_state.show_detailed_feedback
    if st.session_state.show_detailed_feedback:
        with st.spinner("🧠 Analyzing your performance..."):
            performance_summary = analyze_performance(st.session_state.user_answers)
            feedback_text = performance_summary.get("overall_feedback", "No analysis available.")
            st.markdown(f"<div class='ed-card'>{feedback_text}</div>", unsafe_allow_html=True)
    if st.button("🔄 Dobara Try Karein?", key="try_again_btn2"):
        st.session_state.user_answers = []
        st.session_state.current_question = 0
        st.session_state.quiz_started = False
        st.session_state.quiz_completed = False
        st.session_state.show_detailed_feedback = False
        st.session_state.show_hint = False
        st.rerun()
