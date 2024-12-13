import os
from datetime import datetime, timedelta

from fastapi import FastAPI, Request, HTTPException, Form, UploadFile, File, WebSocket
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn

from utils.controller import DBController

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

@app.get("/available_durations/{room_id}/{date}/{time}", response_model=list[int])
async def available_durations(room_id: int, date: str, time: str):
    start_time_dt = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    query = """
        SELECT start_time, duration_hours 
        FROM Schedules 
        WHERE room_id = ? AND CAST(start_time AS DATE) = ?
    """
    schedules = db_controller.execute_query(query, (room_id, start_time_dt.date()))

    # Максимальная продолжительность для бронирования
    max_duration = 6
    available_durations = []

    # Проверяем доступность каждого часа
    for duration in range(1, max_duration + 1):
        end_time = start_time_dt + timedelta(hours=duration)
        if end_time.hour > 22:
            break  # Не разрешаем бронирование позже 22:00

        conflict = any(
            schedule_start <= start_time_dt < schedule_start + timedelta(hours=schedule_duration) or
            schedule_start < end_time <= schedule_start + timedelta(hours=schedule_duration)
            for schedule_start, schedule_duration in schedules
        )
        if conflict:
            break
        available_durations.append(duration)

    return available_durations

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

    return JSONResponse(
        content={"message": "Бронирование прошло успешно!", "redirect_url": f"/room/{room_id}"},
        status_code=200
    )


messages = []
active_connections = []

@app.get("/chat/admin", response_class=HTMLResponse)
async def get_admin_chat(request: Request):
    return templates.TemplateResponse("admin_chat.html", {"request": request, "messages": messages})

@app.post("/chat/admin/send_file")
async def send_file(request: Request, file: UploadFile = File(...)):
    file_location = f"static/uploads/{file.filename}"
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
    messages.append({"username": "admin", "message": None, "file": file.filename})
    await notify_clients()
    return templates.TemplateResponse("admin_chat.html", {"request": request, "messages": messages})

@app.get("/chat/mngr", response_class=HTMLResponse)
async def get_mngr_chat(request: Request):
    return templates.TemplateResponse("mngr_chat.html", {"request": request, "messages": messages})

@app.post("/chat/mngr/send_message")
async def send_message(request: Request, message: str = Form(...)):
    messages.append({"username": "mngr", "message": message, "file": None})
    await notify_clients()
    return templates.TemplateResponse("mngr_chat.html", {"request": request, "messages": messages})

@app.get("/download/{file_name}")
async def download_file(file_name: str):
    file_path = f"static/uploads/{file_name}"
    return FileResponse(path=file_path, filename=file_name)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception as e:
        print(f"Connection error: {e}")
    finally:
        active_connections.remove(websocket)

async def notify_clients():
    for connection in active_connections:
        await connection.send_json(messages)

if __name__ == "__main__":
    # Запуск FastAPI через uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)