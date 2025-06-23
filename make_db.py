import mysql.connector
import random
import os
import datetime

from dotenv import load_dotenv

load_dotenv()

def connect_to_mysql(user, password):
    conn = mysql.connector.connect(
        host='localhost',
        user=user,
        password=password
    )
    print('Connected')
    return conn

def create_db(conn, db_name):
    cursor = conn.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS {db_name}")
    cursor.execute(f"CREATE DATABASE {db_name}")
    cursor.execute(f"USE {db_name}")

    # Normalized tables
    cursor.execute("""
    CREATE TABLE Employees (
        EmployeeID INT PRIMARY KEY,
        FirstName VARCHAR(20),
        LastName VARCHAR(20),
        Department VARCHAR(50),
        HireDate DATE,
        EmailAddress VARCHAR(100),
        JobTitle VARCHAR(100)
    )
    """)

    cursor.execute("""
    CREATE TABLE EmployeeWeeklyData (
        EmployeeID INT,
        WeekNumber INT,
        WeekStartDate DATE,
        NumberOfMeetings INT,
        TotalSales DECIMAL(10, 2),
        HoursWorked DECIMAL(5, 2),
        Activities TEXT,
        PRIMARY KEY (EmployeeID, WeekNumber),
        FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
    )
    """)
    conn.commit()
    cursor.close()


def generate_synthetic_data():
    first_names = ["Wei", "Na", "Tao", "Emma", "John", "Olivia", "James", "Sophia", "Michael", "Emily"]
    last_names = ["Zhang", "Li", "Huang", "Smith", "Doe", "Brown", "Johnson", "Lee", "Davis", "Taylor"]
    departments = ["Sales", "Finance", "IT", "Product Development", "Business Development"]
    job_titles = [
        "Sales Manager", "Financial Analyst", "IT Specialist", "Product Designer",
        "Business Analyst", "Software Engineer", "Marketing Manager", "Data Analyst",
        "Customer Success Manager", "DevOps Engineer"
    ]
    activities_pool = [
        "Worked on feature rollout", "Client meetings", "Internal training",
        "Resolved infrastructure issues", "Faced challenges with heuristic approach",
        "Struggled with customer retention, proposed loyalty program",
        "Analyzed financial reports", "Prepared sales forecasts",
        "Implemented dashboard reporting", "Conducted market research"
    ]

    employees = []
    weekly_data = []
    base_date = datetime.date(2024, 8, 26)

    for i in range(10):
        emp_id = i + 1
        fn, ln = first_names[i], last_names[i]
        dept = departments[i % len(departments)]
        title = job_titles[i % len(job_titles)]
        hire_date = datetime.date(2020, 1, 1) + datetime.timedelta(days=random.randint(0, 365 * 5))
        email = f"{fn.lower()}.{ln.lower()}@company.com"

        employees.append((emp_id, fn, ln, dept, hire_date, email, title))

        for wk in range(1, 11):
            start_date = base_date + datetime.timedelta(weeks=wk - 1)
            meetings = random.randint(1, 10)
            sales = round(random.uniform(1000, 10000) if dept == "Sales" else 0, 2)
            hours = round(random.uniform(35, 50), 2)
            activities = random.choice(activities_pool)

            weekly_data.append((emp_id, wk, start_date, meetings, sales, hours, activities))

    return employees, weekly_data

def generate_insert_statements(employees, weekly_data):
    emp_inserts = [
        f"INSERT INTO Employees (EmployeeID, FirstName, LastName, Department, HireDate, EmailAddress, JobTitle) VALUES ({eid}, '{fn}', '{ln}', '{dept}', '{hd}', '{email}', '{title}');"
        for eid, fn, ln, dept, hd, email, title in employees
    ]

    data_inserts = [
        f"INSERT INTO EmployeeWeeklyData (EmployeeID, WeekNumber, WeekStartDate, NumberOfMeetings, TotalSales, HoursWorked, Activities) VALUES ({eid}, {wk}, '{wsd}', {meetings}, {sales}, {hours}, '{activities.replace("'", "''")}');"
        for eid, wk, wsd, meetings, sales, hours, activities in weekly_data
    ]

    return emp_inserts, data_inserts

def insert_into_mysql(conn, emp_inserts, data_inserts):
    cursor = conn.cursor()
    try:
        for stmt in emp_inserts:
            cursor.execute(stmt)
        for stmt in data_inserts:
            cursor.execute(stmt)
        conn.commit()
    except mysql.connector.Error as err:
        conn.rollback()
        raise err
    finally:
        cursor.close()


if __name__ == "__main__":
    user = os.getenv("user")
    password = os.getenv("password")
    conn = connect_to_mysql(user, password)
    create_db(conn, "db")
    e, wd = generate_synthetic_data()
    ei, wdi = generate_insert_statements(e, wd)
    insert_into_mysql(conn, ei, wdi)
    conn.close()
