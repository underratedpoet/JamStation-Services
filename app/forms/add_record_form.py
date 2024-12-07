from datetime import datetime

from PyQt6.QtWidgets import (
    QPushButton, QMessageBox, QLineEdit, 
    QDialog, QFormLayout, QHBoxLayout, 
    QComboBox, QLabel,QDoubleSpinBox, 
    QVBoxLayout, QTextEdit)

from utils.controller import DBController
from utils.shemas import Equipment, Instrument, Check, Repair

class AddRecordDialog(QDialog):
    def __init__(self, type, table, location, room, db_controller: DBController, employee_id, parent=None):
        super().__init__(parent)
        self.db_controller = db_controller
        self.table = table
        self.location = db_controller.select(['id', 'name'], 'Locations', location)
        self.room = room
        self.type = type
        self.employee_id = employee_id

        self.setWindowTitle("Добавить запись")

        # Главный макет
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)  # Отступы от краев
        main_layout.setSpacing(10)  # Расстояние между элементами

        # Фильтры
        filter_layout = QHBoxLayout()
        location_label = QLabel(f"Локация: {self.location[1]}")
        filter_layout.addWidget(location_label)
        if room:
            self.room = db_controller.select(['id', 'name'], 'Rooms', room)
            room_label = QLabel(f"Зал: {self.room[1]}")
            filter_layout.addWidget(room_label)
        main_layout.addLayout(filter_layout)

        # Поля ввода
        input_layout = QFormLayout()
        input_layout.setSpacing(8)  # Расстояние между строками ввода

        if table == "accounting":
            if self.type == "Equipment":
                self.input_name = QLineEdit(self)
                self.input_type = QLineEdit(self)
                input_layout.addRow("Наименование:", self.input_name)
                input_layout.addRow("Тип:", self.input_type)
            else:
                self.input_name = QLineEdit(self)
                self.input_hourly_rate = QDoubleSpinBox(self)
                self.input_hourly_rate.setRange(0.0, 5000.0)
                self.input_hourly_rate.setDecimals(2)
                self.input_hourly_rate.setSingleStep(0.1)
                self.input_hourly_rate.setValue(0.0)
                input_layout.addRow("Наименование:", self.input_name)
                input_layout.addRow("Руб/ч:", self.input_hourly_rate)

        elif table == "checks":
            filters = {}
            if self.room:
                filters['room_id'] = self.room[0]
            else:
                filters['location_id'] = self.location[0]
            self.items = self.db_controller.select(['id', 'name'], self.type, None, filters)
            self.input_name = QComboBox(self)
            self.input_description = QTextEdit(self)
            self.input_status = QComboBox(self)
            self.input_status.addItems(["OK", "Damaged"])
            self.input_name.addItems([item[1] for item in self.items])
            input_layout.addRow("Наименование:", self.input_name)
            input_layout.addRow("Описание:", self.input_description)
            input_layout.addRow("Состояние:", self.input_status)

        else:
            filters = {}
            if self.room:
                filters['room_id'] = self.room[0]
            else:
                filters['location_id'] = self.location[0]
            self.items = self.db_controller.select(['id', 'name'], self.type, None, filters)
            self.input_legal_entity = QLineEdit(self)
            self.input_price = QDoubleSpinBox(self)
            self.input_price.setRange(0.0, 1000000.0)
            self.input_price.setDecimals(2)
            self.input_price.setSingleStep(10)
            self.input_price.setValue(0.0)
            self.input_name = QComboBox(self)
            self.input_name.addItems([item[1] for item in self.items])
            input_layout.addRow("Наименование:", self.input_name)
            input_layout.addRow("Мастерская:", self.input_legal_entity)
            input_layout.addRow("Стоимость:", self.input_price)

        main_layout.addLayout(input_layout)

        # Кнопки сохранения и отмены
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Сохранить", self)
        self.save_button.clicked.connect(self.save_record)
        self.cancel_button = QPushButton("Отмена", self)
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

        # Установить основной макет
        self.setLayout(main_layout)
        self.adjustSize()  # Автоматически подогнать размер окна


    def save_record(self):
        try:
            if self.table == "accounting":
                if self.type == "Equipment":
                    shema = Equipment(
                        id=None,
                        name=self.input_name.text(),
                        type=self.type,
                        room_id=self.room[0],
                        status='OK'
                    )
                else:
                    shema = Instrument(
                        id=None,
                        location_id=self.location[0],
                        name=self.input_name.text(),
                        hourly_rate=self.input_hourly_rate.value()
                    )
                self.db_controller.add_record(self.type, shema)
            elif self.table == "checks":
                shema = Check(
                    id=None,
                    employee_id=self.employee_id,
                    item_id=self.items[self.input_name.currentIndex()][0],
                    item_table=self.type,
                    inspection_date=datetime.now(),
                    description=self.input_description.toPlainText(),
                    status=self.input_status.currentText()
                )
                self.db_controller.add_record("Checks", shema)
            else:
                last_check = self.db_controller.last_check(self.type, self.items[self.input_name.currentIndex()][0])
                if not last_check:
                    QMessageBox.warning(self, "Ошибка", f"Не существует записей о проверках данного оборудования")
                    return
                shema = Repair(
                    id=None,
                    check_id=last_check,
                    repair_start_date=datetime.today(),
                    legal_entity=self.input_legal_entity.text(),
                    repair_cost=self.input_price.value()
                )
                self.db_controller.add_record("Repairs", shema)
            print(shema)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запись: {e}")
