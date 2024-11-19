from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pyodbc
import logging
from datetime import datetime, timedelta
from controller import DBController
import os
import uvicorn

app = FastAPI()
# Подключение папки static для обслуживания статических файлов
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Инициализация базы данных
db_controller = DBController(
    server=os.getenv("DB_SERVER"), 
    database=os.getenv("DB_NAME"), 
    username=os.getenv("DB_USER"), 
    password=os.getenv("DB_PASSWORD")
)

@app.get("/", response_class=HTMLResponse)
async def list_locations(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/locations", response_class=HTMLResponse)
async def list_locations(request: Request):
    query = "SELECT id, name FROM Locations"
    locations = db_controller.execute_query(query)
    return templates.TemplateResponse("locations.html", {"request": request, "locations": locations})


@app.get("/rooms/{location_id}", response_class=HTMLResponse)
async def list_rooms(request: Request, location_id: int):
    query = "SELECT id, name FROM Rooms WHERE location_id = ?"
    rooms = db_controller.execute_query(query, (location_id,))
    return templates.TemplateResponse("rooms.html", {"request": request, "rooms": rooms, "location_id": location_id})

@app.get("/room/{room_id}", response_class=HTMLResponse)
async def room_info(request: Request, room_id: int):
    query = "SELECT name, capacity, hourly_rate FROM Rooms WHERE id = ?"
    room = db_controller.execute_query(query, (room_id,))
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return templates.TemplateResponse("room.html", {"request": request, "room": room[0], "room_id": room_id})

@app.get("/available_times/{room_id}/{date}", response_class=HTMLResponse)
async def available_times(request: Request, room_id: int, date: str):
    date_dt = datetime.strptime(date, '%Y-%m-%d')
    query = "SELECT start_time, duration_hours FROM Schedules WHERE room_id = ? AND CAST(start_time AS DATE) = ?"
    schedules = db_controller.execute_query(query, (room_id, date_dt.date()))

    available_times = []
    for hour in range(10, 22):
        available_times.append(f"{hour:02d}:00")

    for schedule in schedules:
        start_time = schedule[0]
        duration = schedule[1]
        for hour in range(start_time.hour, start_time.hour + duration):
            if f"{hour:02d}:00" in available_times:
                available_times.remove(f"{hour:02d}:00")

    return templates.TemplateResponse("available_times.html", {"request": request, "available_times": available_times})

@app.post("/book/{room_id}", response_class=HTMLResponse)
async def book_room(request: Request, room_id: int, name: str = Form(...), phone: str = Form(...), email: str = Form(None), date: str = Form(...), time: str = Form(...), duration: int = Form(...)):
    # Проверка наличия клиента
    query = "SELECT id FROM Clients WHERE phone_number = ?"
    client = db_controller.execute_query(query, (phone,))
    if client:
        client_id = client[0][0]
        # Проверка наличия штрафов
        query = "SELECT id FROM Penalties WHERE client_id = ? AND written_off IS NULL"
        penalties = db_controller.execute_query(query, (client_id,))
        if penalties:
            raise HTTPException(status_code=400, detail="Client has penalties and cannot book a room")
    else:
        # Добавление нового клиента
        query = "INSERT INTO Clients (name, phone_number, email) VALUES (?, ?, ?)"
        db_controller.execute_query(query, (name, phone, email), transactional=True)
        
        # Получение ID нового клиента
        query = "SELECT id FROM Clients WHERE phone_number = ?"
        client_id = db_controller.execute_query(query, (phone,))[0][0]

    # Добавление записи в расписание
    start_time_dt = datetime.strptime(f"{date} {time}", '%Y-%m-%d %H:%M')
    query = "INSERT INTO Schedules (room_id, client_id, start_time, duration_hours, is_paid, status) VALUES (?, ?, ?, ?, 0, N'Активно')"
    db_controller.execute_query(query, (room_id, client_id, start_time_dt, duration), transactional=True)

    return RedirectResponse(url=f"/room/{room_id}", status_code=303)


if __name__ == "__main__":
    # Запуск FastAPI через uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)