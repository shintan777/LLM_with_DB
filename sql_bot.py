import os
import sqlparse
import re
from typing import Dict
from dotenv import load_dotenv
from openai import OpenAI
from sqlparse.tokens import Keyword, DML

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
bot_name = os.getenv("BOT_NAME")
client = OpenAI(api_key=api_key)

def text_to_sql(question: str, db_name) -> str:

    with open("prompt_text_to_sql.txt", "r", encoding='utf-8') as f:
        prompt = f.read()

    system_prompt = (
          f"{prompt}"
    )
    user_prompt = (
        f"Give the needed SQL query for the following question"
        f"Add the database name {db_name} before the table names for a valid query"
        f"Include the valid query in the block ```sql ```. Also provide additional relevant information from the database or your knowledge \n\n"
        f"{question}"
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.00001
    )

    return response.choices[0].message.content.strip()

def verify_sql(query_string, conn):
    try:
        parsed = sqlparse.parse(query_string)
        if not parsed or not parsed[0].tokens:
            return (False, "Invalid query")

        first_token = next((t for t in parsed[0].tokens if not t.is_whitespace), None)
        if not first_token or first_token.ttype is not DML or first_token.value.upper() != 'SELECT':
            return (False, "Not a SELECT query")

        cursor = conn.cursor(dictionary=True)
        cursor.execute(f"EXPLAIN {query_string}")
        cursor.fetchall()

        return (True, "")

    except Exception as e:
        return (False, f"Failed to execute query: {str(e)}")

def execute_valid_sql(query_string, conn):
    success, msg = verify_sql(query_string, conn)
    if not success:
        return {
            "success": False,
            "row_count": 0,
            "rows": [],
            "message": msg
        }
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query_string)
        rows = cursor.fetchall()
        return {
            "success": True,
            "row_count": len(rows),
            "rows": rows,
            "message": "Query executed successfully."
        }
    except Exception as e:
        return {
            "success": False,
            "row_count": 0,
            "rows": [],
            "message": f"Failed to execute query: {str(e)}"
        }

def format_result_to_string(result_dict):
    if not result_dict.get("success"):
        return f"Success: False\nMessage: {result_dict.get('message')}"

    lines = [
        f"Success: True",
        f"Row Count: {result_dict['row_count']}",
        "Rows:"
    ]

    for idx, row in enumerate(result_dict['rows'], start=1):
        row_str = ', '.join(f"{k}: {v}" for k, v in row.items())
        lines.append(f"{idx}. {row_str}")

    return '\n'.join(lines)

def sql_to_text(query_res: str, question:str, message_query) -> str:

    with open("prompt_sql_to_text.txt", "r", encoding='utf-8') as f:
        prompt = f.read()

    system_prompt = (
          f"{prompt}"
    )

    user_prompt = (
        f"Answer the question based on the query description and output provided. Keep the language direct and human like, just like a natural conversation. The question is\n\n"
        f"{question}\n\n"
        f"{message_query}"
        f"The query result is\n"
        f"{query_res}"
    )

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.00001
    )

    return response.choices[0].message.content.strip()

def parse_sql_and_message(input_text: str) -> Dict[str, str]:
    sql_match = re.search(r"```sql\s*(.*?)\s*```", input_text, re.DOTALL)

    if not sql_match:
        raise ValueError("No SQL query block found in input.")

    sql_query = sql_match.group(1).strip()
    cleaned_query = sql_query.replace('\n', ' ').strip()
    message = re.sub(r"```sql\s*.*?\s*```", "", input_text, flags=re.DOTALL).strip()

    return (cleaned_query, message)


if __name__ == "__main__":
    db_name = "employee_db"
    question = "Which employees in the company were hired during a time of industry recession (requires external knowledge)?"
    q = "What was the sales revenue of 'Todd Garcia' for the week starting on '2024-09-30'?"
    q2 = "Who are the employees that faced challenges with heuristic, and what solutions did they propose?"
    ans = text_to_sql(q2, db_name)
    print(parse_sql_and_message(ans))
