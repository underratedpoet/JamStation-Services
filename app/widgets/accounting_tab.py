from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QComboBox, QPushButton, QLabel,
    QScrollArea, QWidget, QMenu, QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QFrame,QMessageBox
)
from PyQt6.QtCore import Qt
from pydantic import BaseModel

from utils.controller import DBController
from forms.add_record_form import AddRecordDialog

class EquipmentInstrumentsTab(QWidget):
    def __init__(self, db_controller: DBController, employee_id):
        super().__init__()
        self.db_controller = db_controller
        self.employee_id = employee_id
        self.current_view = "Equipment"  # 'equipment' or 'instruments'
        self.current_table = "accounting"
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        tables_layout = QHBoxLayout()
        # Выбор между оборудованием и инструментами
        self.view_selector = QComboBox()
        self.view_selector.addItems(["Оборудование", "Инструменты"])
        self.view_selector.currentTextChanged.connect(self.change_view)
        #layout.addWidget(self.view_selector)
        self.table_selector = QComboBox()
        self.table_selector.addItems(["Учет", "Проверки", "Ремонт"])
        self.table_selector.currentTextChanged.connect(self.change_view)
        #self.table_selector.currentTextChanged.connect(self.change_table)
        #layout.addWidget(self.table_selector)
        tables_layout.addWidget(self.view_selector)
        tables_layout.addWidget(self.table_selector)
        layout.addLayout(tables_layout)

        # Фильтры
        filter_layout = QHBoxLayout()
        self.location_selector = QComboBox()
        self.room_selector = QComboBox()
        self.room_selector.setEnabled(False)  # Включается только для оборудования
        self.load_locations()
        self.location_selector.currentIndexChanged.connect(self.update_filters)
        self.room_selector.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(QLabel("Локация:"))
        filter_layout.addWidget(self.location_selector)
        filter_layout.addWidget(QLabel("Зал:"))
        filter_layout.addWidget(self.room_selector)
        layout.addLayout(filter_layout)

        # Кнопка добавления записи
        self.add_button = QPushButton("Добавить запись")
        self.add_button.clicked.connect(self.add_record)
        layout.addWidget(self.add_button)

        # Область прокрутки для плиток
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

        # Загрузка данных
        self.change_view()

    def load_locations(self):
        query = "SELECT id, name FROM Locations"
        locations = self.db_controller.execute_query(query)
        self.location_selector.clear()
        for location in locations:
            self.location_selector.addItem(location[1], location[0])

    def update_filters(self):
        location_id = self.location_selector.currentData()
        if self.current_view == "Equipment" and location_id is not None:
            query = "SELECT id, name FROM Rooms WHERE location_id = ?"
            rooms = self.db_controller.execute_query(query, (location_id,))
            self.room_selector.clear()
            self.room_selector.addItem("Все залы", None)

            for room in rooms:
                self.room_selector.addItem(room[1], room[0])
        self.load_data()

    def change_view(self):
        #self.table_selector.clear()
        if self.view_selector.currentText() == "Оборудование":
            self.current_view = "Equipment"
            self.room_selector.setEnabled(True)
        else:
            self.current_view = "Instruments"
            self.room_selector.setEnabled(False)
        if self.table_selector.currentText() == "Учет":
            self.current_table = "accounting"
        elif self.table_selector.currentText() == "Проверки":
            self.current_table = "checks"
        else: self.current_table = "repairs"
        #self.current_view = "equipment" if self.view_selector.currentText() == "Оборудование" else "instruments"
        #self.room_selector.setEnabled(self.current_view == "equipment")
        self.load_data()

    def load_data(self):
        location_id = self.location_selector.currentData()
        room_id = self.room_selector.currentData() if self.current_view == "Equipment" else None
        if self.current_table == "accounting":
            records = self.db_controller.load_accounting(self.current_view, location_id, room_id)
        elif self.current_table == "checks":
            records = self.db_controller.load_checks(self.current_view, location_id, room_id)
        else:
            records = self.db_controller.load_repairs(self.current_view, location_id, room_id)

        self.display_records(records)

    def display_records(self, records):
        # Очистка текущих плиток
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()

        # Создание плиток
        for record in records:
            tile = self.create_tile(record)
            self.scroll_layout.addWidget(tile)


    def create_tile(self, record: BaseModel) -> QWidget:
        tile = QWidget()
        tile.setStyleSheet("""
            QWidget {
                border: 2px solid #555;  /* Чёткая тёмная граница */
                border-radius: 5px;
                padding: 10px;
                margin: 5px;
                background-color: #3d3d40;  /* Тёмный фон для контраста */
                color: #ffffff;  /* Белый текст для лучшей читаемости */
            }
            QLabel {
                font-size: 12px;
            }
        """)

        layout = QVBoxLayout(tile)
        for field, value in record.model_dump().items():
            layout.addWidget(QLabel(f"{field.capitalize()}: {value}"))

        tile.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tile.customContextMenuRequested.connect(lambda pos, r=record: self.show_context_menu(r, pos))
        return tile

    def show_context_menu(self, record, pos):
        menu = QMenu()
        menu.addAction("Изменить", lambda: self.edit_record(record))
        menu.addAction("Удалить", lambda: self.delete_record(record))
        menu.exec(self.mapToGlobal(pos))

    def add_record(self):
        # Открытие диалогового окна
        location_id = self.location_selector.currentData()
        room_id = self.room_selector.currentData() if self.current_view == "Equipment" else None
        if self.current_view == "Equipment" and room_id is None:
            QMessageBox.warning(self, "Ошибка", "Для добавления новго оборудования выберите зал.")
            return
        dialog = AddRecordDialog(self.current_view, self.current_table, location_id, room_id, self.db_controller, self.employee_id, self)
        if dialog.exec():
            self.load_data()  # Перезагрузка данных

    def edit_record(self, record):
        print(f"Изменение записи: {record}")

    def delete_record(self, record):
        print(f"Удаление записи: {record}")
