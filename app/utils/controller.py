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

    def paginate_table(self, table_name: str, offset: int, limit: int, order_column: str | None = None, filters: dict = None, join_clause: str = ""):
        # Добавляем ORDER BY для корректного запроса в SQL Server
        if order_column is None:
            order_column = 'NULL'
        
        # Формируем условия фильтрации
        filter_conditions = ""
        if filters:
            filter_conditions = " AND ".join([f"{col} LIKE '%{val}%'" for col, val in filters.items()])
            filter_conditions = f"WHERE {filter_conditions}"
        
        query = f"""
        SELECT * 
        FROM {table_name}
        {join_clause}
        {filter_conditions}
        ORDER BY (SELECT {order_column}) DESC
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

    def select(self, columns: list[str] | None, table: str, id: int | None = None, filters: dict | None = None) -> list:
        if not columns:
            query = f"SELECT * FROM {table}"
        else:
            selected_columns = ", ".join(columns)
            query = f"SELECT {selected_columns} FROM {table}"
        
        if filters:
            filter_conditions = " AND ".join([f"{col} = ?" for col in filters.keys()])
            query += f" WHERE {filter_conditions}"
            
        if id:
            if filters:
                query += f" AND id = ?"
            else:
                query += f" WHERE id = ?"

        # Преобразуем словарь значений в кортеж
        params = tuple(filters.values()) if filters else ()

        # Добавляем id в параметры, если оно есть
        if id:
            params += (id,)

        rows = self.execute_query(query, params)
        if id:
            return rows[0]
        return rows
    
    def delete_by_id(self, table: str, id: int) -> int:
        query = f'DELETE FROM {table} WHERE id = {id}'
        result = self.execute_query(query)
        if result == 0: return 0
        else: return 1

    def insert(self, table: str, data: dict):
        """
        Выполняет вставку данных в указанную таблицу и возвращает ID вставленной записи.
        
        :param table: имя таблицы, куда вставлять данные.
        :param data: словарь данных для вставки, где ключи - это имена столбцов, а значения - данные для вставки.
        :return: ID вставленной записи.
        """
        columns = ', '.join(data.keys())
        values = ', '.join(['?' for _ in data])
        output_clause = "OUTPUT INSERTED.id"  # Предполагается, что идентификатор называется "id"
        query = f"INSERT INTO {table} ({columns}) {output_clause} VALUES ({values})"

        cursor = self.connection.cursor()
        
        try:
            cursor.execute(query, tuple(data.values()))
            result = cursor.fetchone()
            self.connection.commit()
            if result:
                return result[0]
            else:
                raise ValueError("Не удалось получить ID вставленной записи.")
        except Exception as e:
            self.connection.rollback()
            print(f"Ошибка при выполнении вставки: {e}")
            raise
        finally:
            cursor.close()

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

        try:
            # Выполняем запрос с параметрами
            self.execute_query(query, params=values)
            self.connection.commit()
            self.logger.info(f"Record updated in {table_name}. SET: {record}, WHERE: {filters}")
        except Exception as e:
            self.logger.error(f"Failed to update record in {table_name}: {e}")
            raise

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

    def select_all_receipts(self, location_id: int, offset: int = 0, limit: int = 10) -> list[ReceiptRecord]:
        # Получение чеков с пагинацией и фильтрацией по локации через связь с таблицей Employees
        join_clause = """
        JOIN Employees e ON Receipts.employee_id = e.id
        """
        filters = {"e.location_id": location_id}
        receipts_data = self.paginate_table("Receipts", offset, limit, "Receipts.created_at", filters, join_clause)

        receipt_records = []
        for receipt_data in receipts_data:
            receipt = Receipt(
                id=receipt_data["id"],
                employee_id=receipt_data["employee_id"],
                total_amount=receipt_data["total_amount"],
                created_at=receipt_data["created_at"]
            )

            # Получение позиций для каждого чека
            query_items = """
            SELECT id, receipt_id, item_table, item_id, quantity, total
            FROM Receipt_Items
            WHERE receipt_id = ?
            """
            items_data = self.execute_query(query_items, (receipt.id,))
            items = [Receipt_Item(
                id=item[0],
                receipt_id=item[1],
                item_table=item[2],
                item_id=item[3],
                quantity=item[4],
                total=item[5]
            ) for item in items_data]

            receipt_record = ReceiptRecord(receipt=receipt, items=items)
            receipt_records.append(receipt_record)

        return receipt_records

    def get_clients_by_location(self, location_id: int) -> list[ClientRecord]:
        """
        Получает список клиентов, связанных с указанной локацией через расписание и комнаты.

        :param location_id: ID локации.
        :return: Список объектов ClientRecord.
        """
        query = """
        SELECT DISTINCT 
            c.id AS client_id,
            c.name AS client_name,
            c.phone_number AS client_phone,
            c.email AS client_email,
            CASE 
                WHEN EXISTS (
                    SELECT 1 
                    FROM Penalties p 
                    WHERE p.client_id = c.id AND p.written_off IS NULL
                ) THEN 1
                ELSE 0
            END AS has_penalties
        FROM Clients c
        INNER JOIN Schedules s ON s.client_id = c.id
        INNER JOIN Rooms r ON s.room_id = r.id
        WHERE r.location_id = ?
        """
        
        try:
            rows = self.execute_query(query, (location_id,))
            clients = [
                ClientRecord(
                    id=row[0],
                    name=row[1],
                    phone_number=row[2],
                    email=row[3],
                    has_penalties=bool(row[4])
                )
                for row in rows
            ]
            return clients
        except Exception as e:
            self.logger.error(f"Error fetching clients by location: {e}")
            raise

    def get_penalties_by_client(self, client_id: int) -> list[Penalty]:
        """
        Получает список штрафов для указанного клиента.

        :param client_id: ID клиента.
        :return: Список объектов Penalty.
        """
        query = """
        SELECT 
            id,
            client_id,
            description,
            amount,
            applied_at,
            written_off
        FROM Penalties
        WHERE client_id = ?
        """
        
        try:
            rows = self.execute_query(query, (client_id,))
            penalties = [
                Penalty(
                    id=row[0],
                    client_id=row[1],
                    description=row[2],
                    amount=row[3],
                    applied_at=row[4],
                    written_off=row[5]
                )
                for row in rows
            ]
            return penalties
        except Exception as e:
            self.logger.error(f"Error fetching penalties for client {client_id}: {e}")
            raise

    def write_off_penalty(self, penalty_id: int) -> None:
        """
        Списывает штраф по его ID, если он ещё не списан.

        :param penalty_id: ID штрафа.
        """
        query_check = """
        SELECT written_off
        FROM Penalties
        WHERE id = ?
        """

        query_update = """
        UPDATE Penalties
        SET written_off = CURRENT_TIMESTAMP
        WHERE id = ? AND written_off IS NULL
        """

        try:
            # Проверяем, есть ли уже дата списания
            result = self.execute_query(query_check, (penalty_id,))
            if not result:
                raise ValueError(f"Penalty with ID {penalty_id} not found.")

            written_off = result[0][0]
            if written_off is not None:
                raise ValueError(f"Penalty with ID {penalty_id} is already written off.")

            # Обновляем поле written_off текущим временем
            current_time = datetime.now()
            self.execute_query(query_update, (penalty_id), transactional=True)
            self.logger.info(f"Penalty with ID {penalty_id} successfully written off at {current_time}.")

            return 0
        except Exception as e:
            self.logger.error(f"Error writing off penalty with ID {penalty_id}: {e}")
            raise

    def add_penalty_for_client(self, client_id: int, description: str, amount: float) -> bool:
        """
        Добавляет штраф клиенту.
        :param client_id: ID клиента.
        :param description: Описание штрафа.
        :param amount: Сумма штрафа.
        :return: True, если штраф успешно добавлен, иначе False.
        """
        query = """
            INSERT INTO Penalties (client_id, description, amount, applied_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
        """
        try:
            self.execute_query(query, (client_id, description, amount))
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Ошибка при добавлении штрафа: {e}")
            return False
        
    def get_consumables_by_location(self, location_id: int) -> list[Consumable]:
        rows = self.select(["id", "location_id", "name", "price", "quantity"], "Consumables", filters={"location_id": location_id})
        result = [Consumable(
            id=row[0],
            location_id=row[1],
            name=row[2],
            price=row[3],
            quantity=row[4]
        ) for row in rows]
        return result
    def add_consumable_quantity(self, consumable_id: int, quantity_to_add: int):
        """
        Увеличить количество расходников на указанное значение.
        :param consumable_id: ID расходника.
        :param quantity_to_add: Количество для добавления.
        """
        query = """
            UPDATE Consumables
            SET quantity = quantity + ?
            WHERE id = ? AND quantity + ? >= 0
        """
        self.execute_query(query, (quantity_to_add, consumable_id, quantity_to_add))
        self.connection.commit()

    def delete_zero_quantity_consumables(self, location_id: int):
        query = "DELETE FROM Consumables WHERE location_id = ? AND quantity = 0"
        self.execute_query(query, (location_id,))
        self.connection.commit()

    def get_keys_status(self, location_id: int) -> list[dict]:
        query = """
        SELECT r.id AS room_id, r.name AS room_name, kt.id AS key_id,
            CASE WHEN kt.id IS NOT NULL OR kt.rental_end_time IS NOT NULL THEN 0 ELSE 1 END AS is_returned
        FROM Rooms r
        LEFT JOIN Keys_Transfers kt ON r.id = kt.room_id AND kt.rental_end_time IS NULL
        WHERE r.location_id = ?
        """
        columns = ["room_id", "room_name", "key_id", "is_returned"]
        return [dict(zip(columns, row)) for row in self.execute_query(query, (location_id,))]
    
    def get_today_schedules_by_room(self, room_id: int, location_id: int) -> list[dict]:
        query = """
        SELECT s.id, s.start_time, c.name AS client_name
        FROM Schedules s
        JOIN Clients c ON s.client_id = c.id
        JOIN Rooms r ON s.room_id = r.id
        WHERE r.location_id = ? AND s.room_id = ? 
            AND s.start_time >= CONVERT(DATE, GETDATE())
            AND s.status = N'Активно'
        """
        columns = ["id", "start_time", "client_name"]
        return [dict(zip(columns, row)) for row in self.execute_query(query, (location_id, room_id))]

    def get_keys_history(self, location_id: int) -> list[dict]:
        query = """
        SELECT kt.rental_start_time AS timestamp, r.name AS room_name,
            CASE WHEN kt.rental_end_time IS NULL THEN N'Сдан' ELSE N'Возвращён' END AS action,
            e.id AS employee_id, e.last_name AS employee_name
        FROM Keys_Transfers kt
        JOIN Rooms r ON kt.room_id = r.id
        JOIN Employees e ON kt.employee_id = e.id
        WHERE r.location_id = ?
        ORDER BY kt.rental_start_time
        """
        columns = ["timestamp", "room_name", "action", "employee_id", "employee_name"]
        return [dict(zip(columns, row)) for row in self.execute_query(query, (location_id,))]

    def create_key_transfer(self, key_id: int, schedule_id: int, employee_id: int) -> bool:
        query = """
        INSERT INTO Keys_Transfers (room_id, schedule_id, employee_id, rental_start_time)
        SELECT r.id, ?, ?, GETDATE()
        FROM Rooms r
        WHERE r.id = (SELECT room_id FROM Schedules WHERE id = ?)
        """
        result = self.execute_query(query, (schedule_id, employee_id, schedule_id))
        self.connection.commit()

    def get_instruments_status(self, location_id: int) -> list[dict]:
        query = """
        SELECT i.id AS instrument_id, i.name AS instrument_name,
            CASE 
                WHEN r.id IS NULL THEN 0  -- Если записи в Rentals нет, инструмент не в аренде
                WHEN r.rental_end_time IS NULL THEN 1  -- Если запись есть, но время возврата NULL, инструмент в аренде
                ELSE 0  -- В других случаях инструмент не в аренде
            END AS is_rented
        FROM Instruments i
        LEFT JOIN Rentals r ON i.id = r.instrument_id AND r.rental_end_time IS NULL
        WHERE i.location_id = ?
        """
        columns = ["instrument_id", "instrument_name", "is_rented"]
        return [dict(zip(columns, row)) for row in self.execute_query(query, (location_id,))]


    def add_rental(self, employee_id: int, instrument_id: int, schedule_id: int):
        query = """
        INSERT INTO Rentals (employee_id, instrument_id, schedule_id, rental_start_time)
        VALUES (?, ?, ?, GETDATE())
        """
        self.execute_query(query, (employee_id, instrument_id, schedule_id))

    def return_instrument(self, instrument_id: int):
        query = """
        UPDATE Rentals
        SET rental_end_time = GETDATE()
        WHERE instrument_id = ? AND rental_end_time IS NULL
        """
        self.execute_query(query, (instrument_id,))

    def get_today_schedules(self, location_id: int) -> list[dict]:
        query = """
        SELECT s.id AS schedule_id, r.name AS room_name, c.name AS client_name, s.start_time
        FROM Schedules s
        JOIN Rooms r ON s.room_id = r.id
        JOIN Clients c ON s.client_id = c.id
        WHERE r.location_id = ? AND s.start_time >= CAST(GETDATE() AS DATE) AND s.status = N'Активно'
        ORDER BY s.start_time
        """
        columns = ["schedule_id", "room_name", "client_name", "start_time"]
        return [dict(zip(columns, row)) for row in self.execute_query(query, (location_id,))]
