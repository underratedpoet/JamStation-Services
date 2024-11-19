import pyodbc
import logging
from typing import List, Any

# Настройка логгера
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DBController:
    def __init__(self, server: str, database: str, username: str, password: str):
        self.connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}"
        self.connection = pyodbc.connect(self.connection_string, autocommit=False)
        self.logger = logging.getLogger(__name__)
        self.cursor = self.connection.cursor()
        self.transaction_active = False

    def execute_query(self, query: str, params: tuple = (), transactional: bool = False):
        """
        Выполняет запрос к базе данных.

        :param query: SQL-запрос.
        :param params: Параметры для запроса.
        :param transactional: Флаг выполнения в рамках транзакции.
        :return: Результаты запроса, если они есть (иначе None).
        """
        try:
            if transactional and not self.transaction_active:
                self.transaction_active = True

            # Выполнение запроса
            result = self.connection.execute(query, params)

            # Если запрос возвращает данные, пытаемся их получить
            if query.strip().upper().startswith("SELECT"):
                return result.fetchall()

            # Для запросов без результата коммитим транзакцию, если необходимо
            if transactional and self.transaction_active:
                self.connection.commit()
                self.transaction_active = False

            return 0  # Для запросов без возвращаемого результата

        except Exception as e:
            self.logger.error(f"Error executing query: {e}")

            # Откат транзакции в случае ошибки
            if transactional and self.transaction_active:
                self.connection.rollback()
                self.transaction_active = False
            raise

    def paginate_table(self, table_name: str, offset: int, limit: int, order_table: str | None = None):
        # Добавляем ORDER BY для корректного запроса в SQL Server
        if order_table is None: order_table = 'NULL'
        query = f"""
        SELECT * 
        FROM {table_name}
        ORDER BY (SELECT {order_table})  -- Используйте реальный столбец для сортировки
        OFFSET {offset} ROWS
        FETCH NEXT {limit} ROWS ONLY;
        """
        rows = self.execute_query(query)
        columns = self.get_table_columns(table_name)
        
        # Преобразование кортежей в словари
        result = [dict(zip(columns, row)) for row in rows]
        
        return result
    
    def get_table_columns(self, table_name: str):
        query = f"""
        SELECT COLUMN_NAME
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = ?
        """
        return [row[0] for row in self.execute_query(query, (table_name,))]

    def commit_transaction(self):
        if self.transaction_active:
            self.connection.commit_transaction()
            self.transaction_active = False

    def rollback_transaction(self):
        if self.transaction_active:
            self.connection.rollback_transaction()
            self.transaction_active = False

    def _execute_sql(self, sql: str, params: List[Any] = None, in_transaction: bool = False):
        """Выполнение SQL-запроса (не хранимой процедуры)."""
        try:
            if in_transaction:
                self.connection.autocommit = False
            self.cursor.execute(sql, params or [])
            if in_transaction:
                self.connection.commit()
        except Exception as e:
            if in_transaction:
                self.connection.rollback()
            self.logger.error(f"Error executing SQL: {e}")
            raise

    def get_procedure_params(self, proc_name: str) -> list[dict[str, str]]: 
        """Получаем параметры хранимой процедуры и их типы из базы данных.""" 
        try: 
            # Получаем параметры хранимой процедуры и их типы из базы данных 
            cursor = self.connection.cursor() 
            cursor.execute(f""" 
                SELECT p.name AS parameter_name, 
                       t.name AS parameter_type 
                FROM sys.parameters p 
                JOIN sys.types t ON p.user_type_id = t.user_type_id 
                WHERE p.object_id = OBJECT_ID('{proc_name}'); 
            """) 

            # Читаем параметры и их типы 
            params_with_types = cursor.fetchall() 
            return [{'parameter_name': param_name, 'parameter_type': param_type} 
                    for param_name, param_type in params_with_types] 
        except Exception as e: 
            self.logger.error(f"Error retrieving procedure parameters: {e}") 
            raise 

    def check_password(self, login: str, password: str) -> bool:
        try:

            # Генерация строки EXEC с плейсхолдерами для параметров
            exec_query = f"EXEC CheckEmployeePassword {login}, {password};"

            # Выполняем запрос
            self.cursor.execute(exec_query)

            # Извлекаем результат — это будет таблица, поэтому fetchall() всегда вернет данные
            result = self.cursor.fetchall()

            # Если нужно, можно извлечь описание колонок
            columns = [desc[0] for desc in self.cursor.description]  # Имена колонок результата

            # Возвращаем результат и описание колонок
            return result[0][0]

        except Exception as e:
            self.logger.error(f"Error executing procedure: {e}")
            raise        

    def execute_procedure(self, proc_name: str, params: List[Any] = None, in_transaction: bool = False) -> dict:
        """
        Выполнение хранимой процедуры с поддержкой входных параметров.
        Предполагается, что результат выполнения — это таблица.

        :param proc_name: Имя хранимой процедуры.
        :param params: Список входных параметров.
        :param in_transaction: Указывает, требуется ли транзакция.
        :return: Словарь с результатами выполнения процедуры (таблицей).
        """
        try:
            if in_transaction:
                self.connection.autocommit = False  # Отключаем автокоммит

            # Получаем параметры и их типы для процедуры
            params_with_types = self.get_procedure_params(proc_name)

            # Генерация SQL-запроса для передачи параметров
            exec_placeholders = []

            # Формируем запрос EXEC
            for param in params_with_types:
                param_name = param['parameter_name']
                exec_placeholders.append(f"@{param_name}")

            # Генерация строки EXEC с плейсхолдерами для параметров
            exec_query = f"EXEC {proc_name} {', '.join(exec_placeholders)};"
            print(exec_query)

            # Выполняем запрос
            self.execute_query(
                f'''
                EXEC {proc_name} 
                
                ''')

            # Извлекаем результат — это будет таблица, поэтому fetchall() всегда вернет данные
            result = self.cursor.fetchall()

            # Если нужно, можно извлечь описание колонок
            columns = [desc[0] for desc in self.cursor.description]  # Имена колонок результата

            if in_transaction:
                self.connection.commit()

            # Возвращаем результат и описание колонок
            return {"result": result, "columns": columns}

        except Exception as e:
            if in_transaction:
                self.connection.rollback()
            self.logger.error(f"Error executing procedure: {e}")
            raise

    def execute_function(self, func_name: str, params: List[Any] = None, in_transaction: bool = False) -> Any:
        """Выполнение функции и возврат результата."""
        try:
            if in_transaction:
                self.connection.autocommit = False
            placeholders = ', '.join(['?'] * len(params)) if params else ''
            query = f"SELECT {func_name}({placeholders})"
            self.cursor.execute(query, params or [])
            result = self.cursor.fetchone()
            if in_transaction:
                self.connection.commit()
            return result[0] if result else None
        except Exception as e:
            if in_transaction:
                self.connection.rollback()
            self.logger.error(f"Error executing function: {e}")
            raise

    def _start_transaction(self, isolation_level: str):
        """Открытие транзакции с указанным уровнем изоляции."""
        try:
            self.connection.autocommit = False
            self.connection.setisolatedlevel(isolation_level)
            self.logger.info(f"Transaction started with isolation level: {isolation_level}")
        except Exception as e:
            self.logger.error(f"Error starting transaction: {e}")
            raise

    def close_connection(self):
        """Закрытие соединения с базой данных."""
        try:
            self.cursor.close()
            self.connection.close()
            self.logger.info("Database connection closed.")
        except Exception as e:
            self.logger.error(f"Error closing connection: {e}")
            raise