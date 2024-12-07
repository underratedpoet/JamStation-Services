from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Модель для таблицы Locations
class Location(BaseModel):
    id: int
    name: str
    address: str
    phone_number: str
    email: str | None = None

# Модель для таблицы Rooms
class Room(BaseModel):
    id: int
    location_id: int
    name: str
    capacity: int
    hourly_rate: float

# Модель для таблицы Employees
class Employee(BaseModel):
    id: int
    location_id: int
    first_name: str
    second_name: str | None = None
    last_name: str
    role: str
    phone_number: str
    email: str | None = None
    login: str
    password_hash: str

# Модель для таблицы Consumables
class Consumable(BaseModel):
    id: int
    location_id: int
    name: str
    price: float
    quantity: int | None
    
class Equipment(BaseModel):
    id: int | None
    name: str
    type: str
    room_id: int
    status: str | None = None

class EquipmentRecord(BaseModel):
    id: int
    name: str
    type: str
    status: str

# Модель для таблицы Clients
class Client(BaseModel):
    id: int
    name: str
    phone_number: str
    email: str | None = None

# Модель для таблицы Schedules
class Schedule(BaseModel):
    id: int
    room_id: int
    client_id: int
    start_time: datetime
    duration_hours: int
    is_paid: bool = False
    status: str = 'Активно'

class ScheduleRecord(BaseModel):
    id: int
    room_name: str
    client_name: str
    start_time: datetime
    duration_hours: int
    is_paid: bool
    status: str

# Модель для таблицы Receipts
class Receipt(BaseModel):
    id: int
    employee_id: int
    total_amount: float
    created_at: datetime

class Receipt_Item(BaseModel):
    id: int
    receipt_id: int
    item_table: str
    item_id: int
    quantity: int | None = None
    total: float

# Модель для таблицы Penalties
class Penalty(BaseModel):
    id: int
    client_id: int
    description: str | None = None
    amount: float
    applied_at: datetime
    written_off: datetime | None = None

# Модель для таблицы Instruments
class Instrument(BaseModel):
    id: int | None
    location_id: int
    name: str
    hourly_rate: float

class InstrumentRecord(BaseModel):
    id: int
    name: str
    hourly_rate: float

# Модель для таблицы Rentals
class Rental(BaseModel):
    id: int
    employee_id: int
    instrument_id: int
    schedule_id: int
    rental_start_time: str
    rental_end_time: str | None = None

# Модель для таблицы Checks
class Check(BaseModel):
    id: int | None
    employee_id: int
    item_id: int
    item_table: str
    inspection_date: datetime
    description: str | None = None
    status: str = 'OK'

class CheckRecord(BaseModel):
    id: int
    name: str
    employee: str
    inspection_date: datetime
    description: str
    status: str

# Модель для таблицы KeyTransfers
class KeyTransfer(BaseModel):
    id: int
    employee_id: int
    room_id: int
    schedule_id: int
    rental_start_time: datetime
    rental_end_time: datetime | None = None

# Модель для таблицы Repairs
class Repair(BaseModel):
    id: int | None
    check_id: int
    repair_start_date: datetime
    repair_end_date: datetime | None = None
    repair_status: str = 'В процессе'
    legal_entity: str
    repair_cost: float

class RepairRecord(BaseModel):
    id: int
    name: str
    description: str
    repair_start_date: datetime
    repair_end_date: datetime | None
    repair_status: str
    legal_entity: str
    repair_cost: float
    
