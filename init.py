import time
import os
import logging
import pyodbc

# Настройка логгера
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DB_NAME = "JamStation"
SQL_TABLES_PATH = os.path.join("Scripts", "JamStationTables.sql")
SQL_PROCS_ADDEM_PATH = os.path.join("Scripts", "AddEmployee.sql")
SQL_PROCS_CHECKEMP_PATH = os.path.join("Scripts", "CheckEmployeePassword.sql")
PROC_ADDEMP_NAME = "AddEmployee"
PROC_CHECKEMP_NAME = "CheckEmployeePassword"

logger.info(f"Current working directory: {os.getcwd()}")
logger.info(f"Available files: {os.listdir(os.path.join(os.getcwd(), 'Scripts'))}")

def wait_for_db():
    while True:
        try:
            connection = pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server};'
                f'SERVER={os.getenv("DB_SERVER")};'
                'DATABASE=master;'
                f'UID={os.getenv("DB_USER")};'
                f'PWD={os.getenv("DB_PASSWORD")}'
            )
            connection.close()
            logger.info("Database server is ready")
            break
        except pyodbc.Error as e:
            logger.info(f"Waiting for the database server to be ready... {e}")
            time.sleep(5)

def ensure_database_and_tables():
    try:
        connection = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            f'SERVER={os.getenv("DB_SERVER")};'
            f'UID={os.getenv("DB_USER")};'
            f'PWD={os.getenv("DB_PASSWORD")}',
            autocommit=True
        )
        cursor = connection.cursor()

        # Проверка существования базы данных
        cursor.execute("SELECT name FROM sys.databases WHERE name = ?", DB_NAME)
        db_exists = cursor.fetchone()

        if not db_exists:
            logger.info(f"Database '{DB_NAME}' does not exist. Creating it...")
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            #connection.commit()
            logger.info(f"Database '{DB_NAME}' created successfully.")

        # Подключаемся к новой базе данных
        connection.close()
        
        connection = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            f'SERVER={os.getenv("DB_SERVER")};'
            f'UID={os.getenv("DB_USER")};'
            f'PWD={os.getenv("DB_PASSWORD")}',
            autocommit=True
        )
        cursor = connection.cursor()

        cursor.execute(f"USE {DB_NAME}")
        # Проверка существования базы данных
        cursor.execute("SELECT * FROM sys.procedures WHERE name = ? or name = ?;", PROC_ADDEMP_NAME, PROC_CHECKEMP_NAME)
        proc_exists = cursor.fetchone()
        logger.info(f"{proc_exists}")
        if not proc_exists:
            logger.info(f"Procedures do not exist. Creating them...")
            with open(SQL_PROCS_ADDEM_PATH, "r", encoding="utf-8") as sql_file:
                cursor.execute(f'use {DB_NAME}')
                cursor.commit()
                sql_script = sql_file.read()
                statements = sql_script.split("GO")
                for statement in statements:
                    if statement.strip():
                        cursor.execute(statement)
            connection.commit()
            with open(SQL_PROCS_CHECKEMP_PATH, "r", encoding="utf-8") as sql_file:
                cursor.execute(f'use {DB_NAME}')
                cursor.commit()
                sql_script = sql_file.read()
                statements = sql_script.split("GO")
                for statement in statements:
                    if statement.strip():
                        cursor.execute(statement)
            connection.commit()
            logger.info("Procedures created successfully from the script.")

        # Подключаемся к новой базе данных
        connection.close()
        
        connection = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            f'SERVER={os.getenv("DB_SERVER")};'
            f'DATABASE={DB_NAME};'
            f'UID={os.getenv("DB_USER")};'
            f'PWD={os.getenv("DB_PASSWORD")}',
            autocommit=False
        )
        cursor = connection.cursor()
        


        # Проверка существования таблиц
        cursor.execute("""
        SELECT COUNT(*) FROM information_schema.tables WHERE table_type = 'BASE TABLE' AND table_catalog = ?
        """, DB_NAME)
        table_count = cursor.fetchone()[0]

        if table_count == 0:
            logger.info("No tables found in the database. Executing the SQL script to create tables...")
            with open(SQL_TABLES_PATH, "r", encoding="utf-8") as sql_file:
                sql_script = sql_file.read()
                statements = sql_script.split("GO")
                for statement in statements:
                    if statement.strip():
                        cursor.execute(statement)
            connection.commit()
            logger.info("Tables created successfully from the script.")

        connection.close()

    except pyodbc.Error as e:
        logger.error(f"An error occurred while ensuring database or tables: {e}")
        raise
    except FileNotFoundError:
        logger.error(f"SQL script file '{SQL_TABLES_PATH}' not found.")
        raise

if __name__ == "__main__":
    wait_for_db()
    ensure_database_and_tables()
