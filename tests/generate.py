import pyodbc 
import random 
from faker import Faker 
 
# Инициализация фейковых данных 
faker = Faker() 
 
# Подключение к базе данных 
conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER=AGUYFROMTHOSEPA;DATABASE=JamStation;UID=sa;PWD=YourStrong!Passw0rd')
conn.autocommit = True
cursor = conn.cursor() 
 
def insert_fake_data(): 
    try: 
        # Добавление тестовых данных для таблицы Locations 
        for _ in range(5): 
            cursor.execute( 
                """ 
                INSERT INTO Locations (name, address, phone_number, email) 
                VALUES (?, ?, ?, ?) 
                """, 
                faker.company(), 
                faker.address(), 
                faker.phone_number(), 
                faker.email() 
            ) 
 
        # Добавление тестовых данных для таблицы Employees 
        for _ in range(10): 
            cursor.execute( 
                """ 
                INSERT INTO Employees (location_id, first_name, second_name, last_name, role, phone_number, email, password_hash) 
                VALUES (?, ?, ?, ?, ?, ?) 
                """, 
                random.randint(1, 5), 
                faker.first_name(), 
                faker.name_nonbinary(),
                faker.last_name(),
                random.choice(["Администратор", "Менеджер"]), 
                faker.phone_number(), 
                faker.email(), 
                faker.sha256() 
            ) 
 
        # Добавление тестовых данных для таблицы Clients 
        for _ in range(15): 
            cursor.execute( 
                """ 
                INSERT INTO Clients (name, phone_number, email) 
                VALUES (?, ?, ?) 
                """, 
                faker.name(), 
                faker.phone_number(), 
                faker.email() 
            ) 
 
        # Добавление тестовых данных для таблицы Rooms 
        for _ in range(10): 
            cursor.execute( 
                """ 
                INSERT INTO Rooms (location_id, name, capacity, hourly_rate) 
                VALUES (?, ?, ?, ?) 
                """, 
                random.randint(1, 5), 
                f"Room {faker.random_int(1, 20)}", 
                random.randint(2, 6), 
                round(random.uniform(10.0, 50.0), 2) 
            ) 
 
        # Добавление тестовых данных для таблицы Instruments 
        for _ in range(10): 
            cursor.execute( 
                """ 
                INSERT INTO Instruments (location_id, name, hourly_rate) 
                VALUES (?, ?, ?) 
                """, 
                random.randint(1, 5), 
                faker.word(), 
                round(random.uniform(5.0, 20.0), 2) 
            ) 
 
        # Добавление тестовых данных для таблицы Schedules 
        for _ in range(20): 
            cursor.execute( 
                """ 
                INSERT INTO Schedules (room_id, client_id, start_time, duration_hours, status) 
                VALUES (?, ?, ?, ?, ?) 
                """, 
                random.randint(1, 10), 
                random.randint(1, 15), 
                faker.date_time_this_year(), 
                random.randint(1, 4), 
                random.choice(["booked", "completed", "canceled"]) 
            ) 
 
        # Добавление тестовых данных для таблицы Penalties 
        penalties = ["Late Cancellation", "Equipment Damage", "No Show"] 
        for penalty in penalties: 
            cursor.execute( 
                """ 
                INSERT INTO Penalties (name, description, amount) 
                VALUES (?, ?, ?) 
                """, 
                penalty, 
                f"{penalty} description", 
                round(random.uniform(10.0, 100.0), 2) 
            ) 
 
        # Добавление тестовых данных для таблицы Checks 
        for _ in range(15): 
            cursor.execute( 
                """
                INSERT INTO Checks (item_id, item_type, inspection_date, description, status) 
                VALUES (?, ?, ?, ?, ?) 
                """, 
                random.randint(1, 10), 
                random.choice(["equipment", "instrument"]), 
                faker.date_time_this_year(), 
                faker.sentence(), 
                random.choice(["ok", "broken"]) 
            ) 
 
        conn.commit() 
        print("Тестовые данные успешно добавлены.") 
    except Exception as e: 
        conn.rollback() 
        print(f"Ошибка при добавлении тестовых данных: {e}") 
    finally: 
        cursor.close() 
        conn.close() 
 
# Вызов функции 
insert_fake_data()