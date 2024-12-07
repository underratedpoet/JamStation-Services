import pyodbc
import logging
from typing import List, Any

from utils.shemas import *

# Настройка логгера
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DBController:
    def __init__(self, server: str, database: str, username: str, password: str):
        self.connection_string = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};CHARSET=UTF8"
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

                    # Обработка параметров: если параметр строковый, добавляем префикс N
            #processed_params = []
            #for param in params:
            #    if isinstance(param, str):
            #        processed_params.append(f"N'{param}'")  # Добавляем N перед строками
            #    else:
            #        processed_params.append(param)

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

    def paginate_table(self, table_name: str, offset: int, limit: int, order_table: str | None = None, filters: dict = None):
        # Добавляем ORDER BY для корректного запроса в SQL Server
        if order_table is None:
            order_table = 'NULL'
        
        # Формируем условия фильтрации
        filter_conditions = ""
        if filters:
            filter_conditions = " AND ".join([f"{col} LIKE '%{val}%'" for col, val in filters.items()])
            filter_conditions = f"WHERE {filter_conditions}"
        
        query = f"""
        SELECT * 
        FROM {table_name}
        {filter_conditions}
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
            exec_query = f"EXEC CheckEmployeePassword N'{login}', N'{password}';"

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

    def select(self, columns: list[str] | None, table: str, id: int | None, filters: dict | None = None) -> list:
        if not columns:
            query = f"SELECT * FROM {table}"
        else:
            selected_columns = ", ".join(columns)
            query = f"SELECT {selected_columns} FROM {table}"
        if filters:
            filter_conditions = " AND ".join([f"{col} LIKE '%{val}%'" for col, val in filters.items()])
            query += f" WHERE {filter_conditions}"
        if id:
            if filters: query += f" AND id = {id}"
            else: query += f" WHERE id = {id}"
        print(query)
        rows = self.execute_query(query)
        if id: return rows[0]
        return rows        
    
    def delete_by_id(self, table: str, id: int) -> int:
        query = f'DELETE FROM {table} WHERE id = {id}'
        result = self.execute_query(query)
        if result == 0: return 0
        else: return 1

    def load_schedule(self, location_id, date, room_id) -> list[ScheduleRecord]:
        query = """
        SELECT S.id, R.name, C.name, S.start_time, S.duration_hours, S.is_paid, S.status
        FROM Schedules S
        JOIN Rooms R ON S.room_id = R.id
        JOIN Clients C ON S.client_id = C.id
        WHERE R.location_id = ? AND CONVERT(date, S.start_time) = ?
        """
        params = [location_id, date]
        if room_id is not None:
            query += " AND R.id = ?"
            params.append(room_id)
        schedule = self.execute_query(query, tuple(params))
        record_shemas = []
        for record in schedule:
            schedule_record = ScheduleRecord(
                id=record[0],
                room_name=record[1],
                client_name=record[2],
                start_time=record[3],
                duration_hours=record[4],
                is_paid=record[5],
                status=record[6]
            )
            record_shemas.append(schedule_record)
        return record_shemas
    
    def load_accounting(self, type, location_id, room_id) -> list[EquipmentRecord] | list [InstrumentRecord]:
        if type == "Equipment":
            query = "SELECT id, name, type, status FROM Equipment WHERE room_id IN (SELECT id FROM Rooms WHERE location_id = ?)"
            params = [location_id]
            if room_id is not None:
                query += " AND room_id = ?"
                params.append(room_id)
        else:
            query = "SELECT id, name, hourly_rate FROM Instruments WHERE location_id = ?"
            params = [location_id]

        records = self.execute_query(query, tuple(params))

        record_shemas = []
        for record in records:
            if type == "Equipment":
                record_data = EquipmentRecord.model_validate({
                    "id": record[0],
                    "name": record[1],
                    "type": record[2],
                    "status": record[3],
                })
            else:
                record_data = InstrumentRecord.model_validate({
                    "id": record[0],
                    "name": record[1],
                    "hourly_rate": record[2],
                })
            record_shemas.append(record_data)
        
        return record_shemas


    def load_checks(self, type, location_id, room_id, status = None) -> list[CheckRecord]:
        query = f"""
            SELECT 
            	C.id, T.name, E.first_name, E.last_name, C.inspection_date, C.description, C.status
            FROM 
            	Checks C, Employees E, {type} T, Locations L{', Rooms R' if type=='Equipment' else ''}
            WHERE 
            	C.item_table = '{type}' 
            	AND C.item_id = T.id
            	AND E.id = C.employee_id
            	{'AND T.room_id = R.id' if type=='Equipment' else ''}
                {'AND R.location_id = L.id' if type=='Equipment' else 'AND T.location_id = L.id'}
            	AND L.id = ?
        """
        params = [location_id]
        if room_id is not None:
            query += " AND R.id = ?"
            params.append(room_id) 
        if status is not None:
            query += " AND C.status = ?"
            params.append(status)    
        records = self.execute_query(query, tuple(params))
        record_shemas = []
        for record in records:
            schedule_record = CheckRecord(
                id=record[0],
                name=record[1],
                employee=f"{record[2]} {record[3]}",
                inspection_date=record[4],
                description=record[5],
                status=record[6]
            )
            record_shemas.append(schedule_record)
        return record_shemas     
    
    def load_repairs(self, type, location_id, room_id, status = None) -> list[RepairRecord]:
        query = f"""
            SELECT 
            	Rep.id, 
                T.name, 
                C.description, 
                Rep.repair_start_date, 
                Rep.repair_end_date, 
                Rep.repair_status, 
                Rep.legal_entity,
                Rep.repair_cost
            FROM 
            	Repairs Rep, Checks C, {type} T, Locations L{', Rooms R' if type=='Equipment' else ''}
            WHERE 
            	item_table = '{type}' 
                AND Rep.check_id = C.id
            	AND C.item_id = T.id
            	{'AND T.room_id = R.id' if type=='Equipment' else ''}
            	{'AND R.location_id = L.id' if type=='Equipment' else 'AND T.location_id = L.id'}
            	AND L.id = ?
        """
        params = [location_id]
        if room_id is not None:
            query += " AND R.id = ?"
            params.append(room_id) 
        if status is not None:
            query += " AND R.repair_status = ?"
            params.append(status)    
        records = self.execute_query(query, tuple(params))
        record_shemas = []
        for record in records:
            schedule_record = RepairRecord(
                id=record[0],
                name=record[1],
                description=record[2],
                repair_start_date=record[3],
                repair_end_date=record[4],
                repair_status=record[5],
                legal_entity=record[6],
                repair_cost=record[7],
            )
            record_shemas.append(schedule_record)
        return record_shemas       
    
    def last_check(self, item_table, item_id):
        last_check = self.execute_query(
                    f"""
                    SELECT TOP 1 id
                    FROM Checks
                    WHERE item_table = ? AND item_id = ?
                    ORDER BY inspection_date DESC
                    """,
                    (item_table, item_id)
                )
        if len(last_check) == 0:
            return None
        return last_check[0][0]
    
    def add_record(self, table_name: str, record: BaseModel):
        """
        Добавляет запись в указанную таблицу на основе экземпляра класса BaseModel.

        :param table_name: Название таблицы.
        :param record: Экземпляр класса, наследующегося от BaseModel.
        :raises Exception: Если добавление не удалось.
        """
        # Получаем словарь значений, исключая id, если он есть
        record_dict = record.dict(exclude_unset=True)
        
        # Если столбец 'id' существует, удаляем его из данных для вставки
        if 'id' in record_dict:
            del record_dict['id']
        
        # Получаем список столбцов и значений для запроса
        columns = ", ".join(record_dict.keys())
        placeholders = ", ".join("?" for _ in record_dict.values())
        values = tuple(record_dict.values())
        
        # Формируем SQL-запрос
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders});"

        try:
            # Выполняем запрос с параметрами
            self.execute_query(query, params=values)
            self.connection.commit()
            self.logger.info(f"Record added to {table_name}: {record}")
        except Exception as e:
            self.logger.error(f"Failed to add record to {table_name}: {e}")
            raise

    def update_record(self, table_name: str, record: dict, filters: dict):
        """
        Обновляет запись в указанной таблице на основе переданного словаря и фильтров.

        :param table_name: Название таблицы.
        :param record: Словарь со столбцами и значениями для обновления.
        :param filters: Словарь с фильтрами для идентификации записей, которые нужно обновить.
        :raises Exception: Если обновление не удалось.
        """
        if not record:
            raise ValueError("Record dictionary cannot be empty.")
        if not filters:
            raise ValueError("Filters dictionary cannot be empty to prevent updating all rows.")

        # Формируем строки для SET и WHERE частей запроса
        set_clause = ", ".join([f"{key} = ?" for key in record.keys()])
        where_clause = " AND ".join([f"{key} = ?" for key in filters.keys()])

        # Объединяем значения для SET и WHERE
        values = tuple(record.values()) + tuple(filters.values())

        # Формируем SQL-запрос
        query = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause};"
        print(query, values)
        try:
            # Выполняем запрос с параметрами
            self.execute_query(query, params=values)
            self.connection.commit()
            self.logger.info(f"Record updated in {table_name}. SET: {record}, WHERE: {filters}")
        except Exception as e:
            self.logger.error(f"Failed to update record in {table_name}: {e}")
            raise
