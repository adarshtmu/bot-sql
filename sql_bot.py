import streamlit as st
import google.generativeai as genai
import pandas as pd
import re
import duckdb

# --- Custom CSS ---
# Updated to increase font sizes globally and for specific elements
st.set_page_config(
    page_title="SQL Mentor EdTech",
    layout="wide",
    page_icon=":rocket:",
)

# --- Custom CSS: Website-Like, Not Centered ---
hide_streamlit_style = """
<style>
    /* Hide Streamlit default elements */
    header, #MainMenu, footer,
    .viewerBadge_container__1QSob, .stDeployButton,
    [data-testid="stToolbar"], [data-testid="stDecoration"],
    [data-testid="stDeployButton"], .st-emotion-cache-1r8d6ul,
    .st-emotion-cache-1jicfl2 {
        display: none !important;
    }

    /* Body styles */
    body {
        background: #1a1a2e !important; /* Dark blue background */
        font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif !important;
        color: #e0e6ed !important; /* Light text color for dark theme */
    }

    /* Main app background */
    .stApp {
        background: #1a1a2e !important;
    }

    /* Main content container - constrained width */
    .main .block-container {
        background: #16213e !important; /* Darker blue for content area */
        border-radius: 16px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        padding: 32px 28px;
        margin: 20px auto; /* Center the container */
        max-width: 1000px !important; /* Constrain maximum width */
        width: 95% !important; /* Responsive width */
        border: 1px solid #0f3460;
    }

    /* Headings with better contrast */
    h1, h2, h3, h4, h5, h6 {
        text-align: left !important;
        color: #f8f9fa !important; /* Bright white for headings */
        font-weight: 600;
    }

    h1 { font-size: 2.2rem !important; }
    h2 { font-size: 1.8rem !important; }
    h3 { font-size: 1.5rem !important; }

    /* General text elements styling */
    .stMarkdown, .stText, .stTextArea, .stDataFrame, .stTable, p, div, span {
        font-size: 1.05rem !important;
        color: #e0e6ed !important; /* Light gray text */
        text-align: left !important;
        line-height: 1.6;
    }

    /* Special styling for markdown content */
    .stMarkdown div {
        color: #e0e6ed !important;
    }

    /* Code blocks */
    .stCodeBlock, pre, code {
        background: #0f1419 !important;
        color: #e0e6ed !important;
        border: 1px solid #2d3748 !important;
        border-radius: 8px;
    }

    /* Button styling */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: #ffffff !important;
        font-size: 1.1rem !important;
        font-weight: 600;
        padding: 12px 28px !important;
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        margin-bottom: 1em;
        transition: all 0.3s ease;
        min-height: 48px;
    }

    .stButton button:hover {
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        transform: translateY(-2px);
    }

    /* Tabs styling */
    .stTabs [role="tablist"] {
        background: #0f3460 !important;
        padding: 8px 12px;
        border-radius: 12px;
        box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
        margin-bottom: 2em;
        border: 1px solid #1e4976;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 1rem !important;
        padding: 10px 18px;
        border-radius: 8px;
        transition: all 0.3s ease;
        color: #b0bec5 !important;
        background: transparent;
        border: 1px solid transparent;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #1e4976 !important;
        color: #e0e6ed !important;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        border: 1px solid #667eea;
    }

    /* DataFrame styling */
    .stDataFrame {
        background: #0f1419 !important;
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid #2d3748;
        max-width: 100% !important;
    }

    .stDataFrame table {
        color: #e0e6ed !important;
        background: #0f1419 !important;
    }

    .stDataFrame th {
        background: #1e4976 !important;
        color: #ffffff !important;
        font-weight: 600;
        padding: 12px 8px !important;
        border-bottom: 2px solid #667eea;
    }

    .stDataFrame td {
        background: #16213e !important;
        color: #e0e6ed !important;
        padding: 10px 8px !important;
        border-bottom: 1px solid #2d3748;
    }

    /* Input fields */
    .stTextArea textarea, .stTextInput input {
        background: #0f1419 !important;
        color: #e0e6ed !important;
        border: 1px solid #2d3748 !important;
        border-radius: 8px;
        font-size: 1rem !important;
    }

    .stTextArea textarea:focus, .stTextInput input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important;
    }

    /* Info, warning, success boxes */
    .stInfo {
        background: #0f3460 !important;
        color: #e0e6ed !important;
        border-left: 4px solid #667eea !important;
    }

    .stWarning {
        background: #2d1b14 !important;
        color: #f8d7da !important;
        border-left: 4px solid #ffc107 !important;
    }

    .stSuccess {
        background: #0f2027 !important;
        color: #d4edda !important;
        border-left: 4px solid #28a745 !important;
    }

    .stError {
        background: #2d1b1f !important;
        color: #f8d7da !important;
        border-left: 4px solid #dc3545 !important;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background: #0f3460 !important;
        color: #e0e6ed !important;
        border-radius: 8px;
        padding: 12px 16px !important;
        border: 1px solid #1e4976;
    }

    .streamlit-expanderContent {
        background: #16213e !important;
        color: #e0e6ed !important;
        border: 1px solid #1e4976;
        border-top: none;
        padding: 16px !important;
    }

    /* Progress bar */
    .stProgress .st-bo {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }

    /* Sidebar styling */
    .css-1d391kg {
        background: #0f1419 !important;
        border-right: 1px solid #2d3748;
    }

    .css-1d391kg .stMarkdown {
        color: #e0e6ed !important;
    }

    /* Links */
    a {
        color: #667eea !important;
        text-decoration: none;
    }

    a:hover {
        color: #764ba2 !important;
        text-decoration: underline;
    }

    /* Feedback container styling */
    .feedback-container {
        background: #0f2027 !important;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #28a745;
        box-shadow: 0 4px 15px rgba(40, 167, 69, 0.1);
        font-size: 1.05rem !important;
        margin-bottom: 2em;
        text-align: left !important;
        color: #e0e6ed !important;
    }

    .feedback-header {
        font-size: 1.4rem !important;
        color: #28a745 !important;
        font-weight: 600;
        margin-bottom: 0.8em;
        text-align: left !important;
    }

    .strength-item, .weakness-item {
        font-size: 1.03rem !important;
        margin: 8px 0;
        padding-left: 16px;
        text-align: left !important;
        color: #e0e6ed !important;
    }

    /* Score card styling */
    .score-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 32px;
        border-radius: 16px;
        text-align: center;
        margin: 24px 0;
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
        max-width: 400px;
        margin-left: auto;
        margin-right: auto;
    }

    .score-card h2 {
        color: #ffffff !important;
        margin-bottom: 16px;
    }

    .score {
        font-size: 3rem;
        font-weight: 700;
        color: #ffffff;
        margin: 16px 0;
    }

    /* Responsive design */
    @media (max-width: 768px) {
        .main .block-container {
            padding: 20px 16px;
            margin: 10px 5px;
            width: calc(100% - 10px) !important;
            max-width: none !important;
        }
        
        .stMarkdown, .stText, .stTextArea, .stDataFrame, .stTable {
            font-size: 0.95rem !important;
        }

        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.5rem !important; }
        h3 { font-size: 1.3rem !important; }

        .score {
            font-size: 2.5rem;
        }

        .score-card {
            padding: 24px;
            margin: 16px 0;
        }
    }

    /* Table overflow handling */
    .stDataFrame > div {
        overflow-x: auto;
    }

    /* Ensure consistent spacing */
    .element-container {
        margin-bottom: 1rem;
    }

    /* Custom certificate button styling */
    .certificate-button {
        background: linear-gradient(135deg, #ffc107 0%, #ff8c00 100%) !important;
        color: #000000 !important;
        font-size: 1.3rem !important;
        font-weight: 700 !important;
        padding: 20px 40px !important;
        border-radius: 12px !important;
        text-decoration: none !important;
        box-shadow: 0 6px 20px rgba(255, 193, 7, 0.4) !important;
        display: inline-block !important;
        margin: 20px 0 !important;
        transition: all 0.3s ease !important;
    }

    .certificate-button:hover {
        background: linear-gradient(135deg, #ff8c00 0%, #ffc107 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(255, 193, 7, 0.5) !important;
    }
</style>
"""
st.markdown(hide_streamlit_style, unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2991/2991148.png", width=90)
    st.title("SQL Mentor")
    st.markdown("👋 Welcome to your interactive SQL learning platform!")
    st.markdown("---")
    st.markdown("### 📚 Resources")
    st.markdown("[Khan Academy SQL](https://www.khanacademy.org/computing/computer-programming/sql)")
    st.markdown("[LeetCode SQL Practice](https://leetcode.com/problemset/database/)")
    st.markdown("[SQLBolt](https://sqlbolt.com/)")
    st.markdown("---")
    st.info("Earn a certificate by scoring 80%+ on the quiz!")

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
sql_questions = [    {"question": "Write a SQL query to get all details about users from the 'users' table.", "correct_answer_example": "SELECT * FROM users;", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to count the total number of users in the 'users' table.", "correct_answer_example": "SELECT COUNT(*) AS user_count FROM users;", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to get all users older than 30 from the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE age > 30;", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to find all orders with a status of 'Pending' from the 'orders' table.", "correct_answer_example": "SELECT * FROM orders WHERE status = 'Pending';", "sample_table": orders_table, "relevant_tables": ["orders"]},
    {"question": "Write a SQL query to find users from 'chicago' in the 'users' table (test case-insensitivity).", "correct_answer_example": "SELECT * FROM users WHERE city = 'Chicago';", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to find the most recent order from the 'orders' table by order date.", "correct_answer_example": "SELECT * FROM orders ORDER BY order_date DESC LIMIT 1;", "sample_table": orders_table, "relevant_tables": ["orders"]},
    {"question": "Write a SQL query to find the average order amount from the 'orders' table.", "correct_answer_example": "SELECT AVG(amount) AS average_amount FROM orders;", "sample_table": orders_table, "relevant_tables": ["orders"]},
    {"question": "Write a SQL query to find users from 'New York' or 'Chicago' in the 'users' table.", "correct_answer_example": "SELECT * FROM users WHERE city IN ('New York', 'Chicago');", "sample_table": users_table, "relevant_tables": ["users"]},
    {"question": "Write a SQL query to find users whose orders are still pending. Use the 'users' and 'orders' tables.","correct_answer_example": "SELECT u.* FROM users u JOIN orders o ON u.user_id = o.user_id WHERE o.order_status = 'pending';","sample_table": users_table,"relevant_tables": ["users", "orders"]},
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
# --- Start Screen ---
if not st.session_state.quiz_started:
    st.image("https://cdn-icons-png.flaticon.com/512/2991/2991148.png", width=65)
    st.title("🚀 SQL Mentor - Interactive SQL Practice")
    st.markdown("### Finish the Quiz Successfully to Unlock Your SQL Certificate")
    st.markdown("> 💡 **Tip:** Use `WHERE` to filter data and `JOIN` to combine tables. Try them in the quiz!")
    st.markdown("""
        **📌 Important Notes:**
        - To be eligible for a certificate, you must achieve a score of at least 80%.
        - This quiz uses standard **SQL syntax** (MySQL/PostgreSQL style).
        - String comparisons (like `WHERE city = 'new york'` or `WHERE status = "pending"`) are simulated to be **case-insensitive** for columns `status` and `city`.
        - **Both single quotes (') and double quotes (") are accepted** for string literals in this simulation.
        - Your queries are evaluated by an AI for correctness and logic.
        - Query simulation is powered by DuckDB to show results on sample data.
    """)
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write("""
        In this interactive quiz, you'll work with two sample tables:
        - **Users Table**: User details like ID, name, email, age, and city.
        - **Orders Table**: Order details like ID, user ID, amount, order date, and status.
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
        with tab1: st.dataframe(users_table, hide_index=True, use_container_width=True)
        with tab2: st.dataframe(orders_table, hide_index=True, use_container_width=True)
    except Exception as e:
        st.error(f"Error displaying table previews: {e}")

    st.markdown("---")
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
        st.subheader("📖 Previous Answers & Feedback")
        for i, ans_data in enumerate(st.session_state.user_answers):
            q_num = i + 1
            is_correct = ans_data.get('is_correct', False)
            with st.expander(f"Question {q_num}: {ans_data['question']} {'✅' if is_correct else '❌'}", expanded=False):
                st.write("**Your Answer:**")
                st.code(ans_data.get('student_answer', '(No answer provided)'), language='sql')
                st.write("**SQL Mentor Feedback:**")
                feedback_text = ans_data.get("feedback", "_Feedback not available._")
                st.markdown(feedback_text)
                st.markdown("---")
                # [Display simulation results as in your code]

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
                        st.dataframe(original_tables[table_name], hide_index=True, use_container_width=True)
                    else:
                        st.warning(f"Data for table '{table_name}' not found.")
        elif len(relevant_tables) == 1:
            table_name = relevant_tables[0]
            if table_name in original_tables:
                st.dataframe(original_tables[table_name], hide_index=True, use_container_width=True)
            else:
                st.warning(f"Data for table '{table_name}' not found.")
    else:
        st.info("No specific table context provided for this question.")

    user_query = st.text_area("Write your SQL query here:", height=150, key=f"query_input_{current_q_index}")

    if st.button("✅ Submit Query", key=f"submit_{current_q_index}"):
        if user_query and user_query.strip():
            with st.spinner("🔄 Checking your query... Getting feedback and simulation results from AI Mentor..."):
                # [Call your evaluate_answer_with_llm function and update session state as per your code]
                # st.session_state.user_answers.append(...)
                # st.session_state.current_question += 1 or st.session_state.quiz_completed = True
                st.rerun()
        else:
            st.warning("⚠️ Please enter your SQL query before submitting.")

# --- Quiz Completed Screen ---
elif st.session_state.quiz_completed:
    st.balloons()
    st.markdown("""
        <h1 style='color:#28a745;'>🎉 Congratulations!</h1>
        <h2 style='color:#1f77b4;'>You have completed the SQL Challenge</h2>
    """, unsafe_allow_html=True)
    final_score = 0 # [Calculate score with your helper function]

    st.markdown(
        f"""
        <div class="score-card">
            <h2>📊 Your Final Score</h2>
            <div class="score">{final_score:.2f}%</div>
            <div style='font-size:1.2rem; color:#888;'>Scoreboard</div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.progress(final_score / 100)
    if final_score >= 80:
        st.success("🏆 Great job! You're eligible for a certificate.")
        st.markdown("""
            <a href="https://superprofile.bio/vp/corporate-bhaiya-sql-page" target="_blank" style="
                background-color:#ffc107;
                color:#121212;
                font-size:1.5rem;
                font-weight:600;
                padding:18px 36px;
                border-radius:10px;
                text-decoration:none;
                box-shadow:0 2px 8px rgba(0,0,0,0.11);
                display:inline-block;
                margin-bottom:2em;">🎓 Get Your Certificate</a>
            """, unsafe_allow_html=True)
    else:
        st.info("📚 Keep practicing to earn a certificate!")

    st.markdown("---")
    if st.button("🔄 Try Again?"):
        st.session_state.user_answers = []
        st.session_state.current_question = 0
        st.session_state.quiz_started = False
        st.session_state.quiz_completed = False
        st.session_state.show_detailed_feedback = False
        st.rerun()

    st.subheader("📝 Your Answers & Feedback Summary")
    for i, ans_data in enumerate(st.session_state.user_answers):
        q_num = i + 1
        is_correct = ans_data.get('is_correct', False)
        with st.expander(f"Question {q_num}: {ans_data['question']} {'✅' if is_correct else '❌'}", expanded=False):
            st.write("**Your Answer:**")
            st.code(ans_data.get('student_answer', '(No answer provided)'), language='sql')
            st.write("**SQL Mentor Feedback:**")
            feedback_text = ans_data.get("feedback", "_Feedback not available._")
            st.markdown(feedback_text)
            st.markdown("---")
            # [Display simulation results as in your code]

    st.markdown("---")
    if st.button("🔄 Try Again?"):
        st.session_state.user_answers = []
        st.session_state.current_question = 0
        st.session_state.quiz_started = False
        st.session_state.quiz_completed = False
        st.session_state.show_detailed_feedback = False
        st.rerun()
