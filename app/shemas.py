from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


# Таблица locations
class Location(BaseModel):
    id: int = Field(..., description="Идентификатор локации")
    name: str = Field(..., max_length=255, description="Название локации")
    address: str = Field(..., max_length=255, description="Адрес локации")


# Таблица rooms
class Room(BaseModel):
    id: int = Field(..., description="Идентификатор комнаты")
    location_id: int = Field(..., description="Идентификатор локации")
    name: str = Field(..., max_length=255, description="Название комнаты")
    hourly_rate: float = Field(..., description="Стоимость аренды за час")


# Таблица instruments
class Instrument(BaseModel):
    id: int = Field(..., description="Идентификатор инструмента")
    location_id: int = Field(..., description="Идентификатор локации")
    name: str = Field(..., max_length=255, description="Название инструмента")
    rental_price: float = Field(..., description="Стоимость аренды за час")


# Таблица employees
class Employee(BaseModel):
    id: int = Field(..., description="Идентификатор сотрудника")
    location_id: Optional[int] = Field(None, description="Идентификатор локации (если привязан)")
    name: str = Field(..., max_length=255, description="Имя сотрудника")
    role: str = Field(..., max_length=255, description="Роль сотрудника")
    username: str = Field(..., max_length=255, description="Имя пользователя")
    password_hash: str = Field(..., max_length=255, description="Хэш пароля")


# Таблица clients
class Client(BaseModel):
    id: int = Field(..., description="Идентификатор клиента")
    name: str = Field(..., max_length=255, description="Имя клиента")
    email: str = Field(..., max_length=255, description="Email клиента")


# Таблица schedules
class Schedule(BaseModel):
    id: int = Field(..., description="Идентификатор записи в расписании")
    room_id: int = Field(..., description="Идентификатор комнаты")
    client_id: int = Field(..., description="Идентификатор клиента")
    start_time: datetime = Field(..., description="Время начала репетиции")
    duration_hours: int = Field(..., description="Продолжительность репетиции (в часах)")


# Таблица rentals
class Rental(BaseModel):
    id: int = Field(..., description="Идентификатор аренды инструмента")
    instrument_id: int = Field(..., description="Идентификатор инструмента")
    client_id: int = Field(..., description="Идентификатор клиента")
    start_time: datetime = Field(..., description="Время начала аренды")
    end_time: Optional[datetime] = Field(None, description="Время окончания аренды")


# Таблица checks
class Check(BaseModel):
    id: int = Field(..., description="Идентификатор проверки")
    item_id: int = Field(..., description="Идентификатор оборудования или инструмента")
    item_type: str = Field(..., max_length=255, description="Тип проверяемого элемента (equipment или instrument)")
    employee_id: int = Field(..., description="Идентификатор сотрудника")
    check_time: datetime = Field(..., description="Время проверки")
    status: str = Field(..., max_length=50, description="Статус проверки ('ок' или 'найдена поломка')")
    description: Optional[str] = Field(None, description="Описание поломки")


# Таблица repairs
class Repair(BaseModel):
    id: int = Field(..., description="Идентификатор ремонта")
    check_id: int = Field(..., description="Идентификатор проверки, связанной с ремонтом")
    legal_entity: str = Field(..., max_length=255, description="Юридическое лицо, выполняющее ремонт")
    repair_cost: float = Field(..., description="Стоимость ремонта")
    repair_date: datetime = Field(..., description="Дата завершения ремонта")
    status: str = Field(..., max_length=255, description="Статус ремонта ('в процессе', 'завершён')")

# Таблица receipts
class Receipt(BaseModel):
    id: int = Field(..., description="Идентификатор чека")
    client_id: int = Field(..., description="Идентификатор клиента")
    employee_id: Optional[int] = Field(None, description="Идентификатор сотрудника, выписавшего чек")
    receipt_time: datetime = Field(..., description="Дата и время чека")


# Таблица receipt_items
class ReceiptItem(BaseModel):
    id: int = Field(..., description="Идентификатор позиции в чеке")
    receipt_id: int = Field(..., description="Идентификатор чека")
    item_type: str = Field(..., max_length=255, description="Тип позиции ('расходники', 'аренда зала', 'аренда инструмента')")
    item_id: Optional[int] = Field(None, description="Идентификатор связанного элемента (если применимо)")
    quantity: int = Field(..., description="Количество")
    total_price: float = Field(..., description="Итоговая стоимость")


# Таблица penalty_reasons
class PenaltyReason(BaseModel):
    id: int = Field(..., description="Идентификатор причины штрафа")
    reason: str = Field(..., max_length=255, description="Описание причины штрафа")


# Таблица penalties
class Penalty(BaseModel):
    id: int = Field(..., description="Идентификатор штрафа")
    client_id: int = Field(..., description="Идентификатор клиента")
    reason_id: int = Field(..., description="Идентификатор причины штрафа")
    penalty_date: datetime = Field(..., description="Дата наложения штрафа")
    amount: float = Field(..., description="Размер штрафа")