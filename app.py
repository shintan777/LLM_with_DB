import os
from dotenv import load_dotenv
from make_db import connect_to_mysql
from sql_bot import execute_valid_sql, text_to_sql, format_result_to_string, sql_to_text, parse_sql_and_message

load_dotenv()
user = os.getenv("user")
password = os.getenv("password")

def run_question_pipeline(question, db_name, conn):
    answer = text_to_sql(question, db_name)
    query, message = parse_sql_and_message(answer)
    result = execute_valid_sql(query, conn)
    result_str = format_result_to_string(result)
    answer = sql_to_text(result_str, question, message)
    return answer, query, result_str

def process_questions(input_file_path, output_file_path, query_output_file_path, db_name, conn):
    with open(input_file_path, 'r') as infile:
        lines = infile.readlines()

    answers = []
    queries_output = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if '.' in line:
            q_num, question = line.split('.', 1)
            question = question.strip()
        else:
            q_num, question = '?', line

        answer, query, res_str = run_question_pipeline(question, db_name, conn)
        answers.append(f"{q_num.strip()}. {answer}\n")
        queries_output.append(f"{q_num.strip()}. SQL Query:\n{query}\n\nOutput:\n{res_str}\n")

    with open(output_file_path, 'w') as outfile:
        for line in answers:
            outfile.write(line + '\n')

    with open(query_output_file_path, 'w') as queryfile:
        for entry in queries_output:
            queryfile.write(entry + '\n')

if __name__ == "__main__":
    conn = connect_to_mysql(user, password)

    input_file = "questions.txt"
    output_file = "answers.txt"
    query_output_file = "queries.txt"
    db_name = "db"

    process_questions(input_file, output_file, query_output_file, db_name, conn)
    conn.close()
