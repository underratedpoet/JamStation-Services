import pyodbc
from faker import Faker
from datetime import datetime, timedelta
import random

def fill_schedules(room_id: int):
    # Подключение к базе данных
    conn = pyodbc.connect(f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER=AGUYFROMTHOSEPA;DATABASE=JamStation;UID=sa;PWD=YourStrong!Passw0rd')
    cursor = conn.cursor()
    
    # Инициализация Faker
    fake = Faker()
    
    # Получение существующих client_id из таблицы Clients
    cursor.execute("SELECT id FROM Clients")
    client_ids = [row[0] for row in cursor.fetchall()]
    
    if not client_ids:
        print("No clients found in the database.")
        return
    
    # Временные рамки для бронирования
    start_hour = 10
    end_hour = 22
    
    # Получение текущей даты
    today = datetime.now().date()
    
    # Функция для проверки доступности времени бронирования
    def is_time_available(start_time, duration_hours):
        end_time = start_time + timedelta(hours=duration_hours)
        cursor.execute("""
            SELECT COUNT(*)
            FROM Schedules
            WHERE room_id = ? AND (
                (start_time <= ? AND DATEADD(hour, duration_hours, start_time) > ?) OR
                (start_time < ? AND DATEADD(hour, duration_hours, start_time) >= ?)
            )
        """, room_id, start_time, start_time, end_time, end_time)
        count = cursor.fetchone()[0]
        return count == 0
    
    # Генерация данных для таблицы Schedules
    schedules = []
    for _ in range(10):  # Генерируем 10 записей
        while True:
            start_hour_random = random.randint(start_hour, end_hour - 1)
            duration_hours = random.randint(1, 6)
            start_time = datetime.combine(today, datetime.min.time()) + timedelta(hours=start_hour_random)
            
            if start_time.hour + duration_hours <= end_hour and is_time_available(start_time, duration_hours):
                break
        
        client_id = random.choice(client_ids)
        is_paid = random.choice([0, 1])
        status = random.choice(['Активно', 'Завершено', 'Отменено'])
        
        schedules.append((room_id, client_id, start_time, duration_hours, is_paid, status))
    
    # Вставка данных в таблицу Schedules
    cursor.executemany("""
        INSERT INTO Schedules (room_id, client_id, start_time, duration_hours, is_paid, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, schedules)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Schedules table has been filled.")

# Пример вызова функции
fill_schedules(3)