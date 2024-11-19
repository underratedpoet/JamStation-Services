import time
import os
import logging

import pyodbc

# Настройка логгера
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def wait_for_db():
    while True:
        try:
            connection = pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server};'
                f'SERVER={os.getenv("DB_SERVER")};'
                'DATABASE=master;'  # Подключаемся к системной базе данных
                f'UID={os.getenv("DB_USER")};'
                f'PWD={os.getenv("DB_PASSWORD")}'
            )
            connection.close()
            logger.info(f"Database is ready")
            break
        except pyodbc.Error as e:
            logger.info(f"Waiting for the database to be ready... {e}")
            time.sleep(5)

if __name__ == "__main__":
    wait_for_db()