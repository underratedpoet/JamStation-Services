from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ScheduleRecord(BaseModel):
    id: int
    room_name: str
    client_name: str
    start_time: datetime
    duration_hours: int
    is_paid: bool
    status: str