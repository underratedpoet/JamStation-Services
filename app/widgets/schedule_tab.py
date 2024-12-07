from datetime import datetime, date as d

from PyQt6.QtWidgets import (
    QVBoxLayout, QWidget, QLabel, 
    QComboBox, QHBoxLayout, 
    QDateEdit, QScrollArea
)
from pydantic import ValidationError

from utils.controller import DBController
from utils.shemas import ScheduleRecord

class ScheduleTab(QWidget):
    def __init__(self, db_controller: DBController, location_id):
        super().__init__()
        self.db_controller = db_controller
        self.location = self.db_controller.select(["id", "name"], "Locations", location_id)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout) 

        # Выбор локации
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Локация:"))
        location_layout.addWidget(QLabel(f"{self.location[1]}"))

        # Выбор зала
        room_layout = QHBoxLayout()
        room_layout.addWidget(QLabel("Зал:"))
        self.room_selector = QComboBox()
        self.room_selector.currentIndexChanged.connect(self.load_schedule)
        room_layout.addWidget(self.room_selector)

        # Выбор даты
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Дата:"))
        self.date_selector = QDateEdit()
        self.date_selector.setCalendarPopup(True)
        self.date_selector.setDate(datetime.now())
        self.date_selector.dateChanged.connect(self.load_schedule)
        date_layout.addWidget(self.date_selector)

        # Область прокрутки для плиток расписания
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)

        layout.addLayout(location_layout)
        layout.addLayout(room_layout)
        layout.addLayout(date_layout)
        layout.addWidget(self.scroll_area)

        self.load_rooms()

    def load_rooms(self):
        location_id = self.location[0]
        if location_id is not None:
            query = "SELECT id, name FROM Rooms WHERE location_id = ?"
            rooms = self.db_controller.execute_query(query, (location_id,))
            self.room_selector.clear()
            self.room_selector.addItem("Все залы", None)  # Опция для выбора всех залов
            for room in rooms:
                self.room_selector.addItem(room[1], room[0])
            self.load_schedule()  # Обновить расписание при изменении зала

    def load_schedule(self):
        location_id = self.location[0]
        room_id = self.room_selector.currentData()
        qdate = self.date_selector.date()
        date = d(qdate.year(), qdate.month(), qdate.day())
        if location_id is not None:
            schedule = self.db_controller.load_schedule(location_id, date, room_id)
            self.display_schedule(schedule)

    def display_schedule(self, schedule):
        # Очистка текущих плиток
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Создание плиток для каждой записи
        for record in schedule:
            self.add_schedule_tile(record)

    def add_schedule_tile(self, record: ScheduleRecord):
        tile = QWidget()
        tile_layout = QVBoxLayout(tile)

        fields = [
            ("ID", record.id),
            ("Зал", record.room_name),
            ("Клиент", record.client_name),
            ("Начало", record.start_time.strftime("%Y-%m-%d %H:%M:%S")),
            ("Длительность", record.duration_hours),
            ("Оплачено", "Да" if record.is_paid else "Нет"),
            ("Статус", record.status)
        ]

        for field_name, field_value in fields:
            label = QLabel(f"{field_name}: {field_value}")
            tile_layout.addWidget(label)

        self.scroll_layout.addWidget(tile)