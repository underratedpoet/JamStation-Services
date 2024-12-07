from PyQt6.QtWidgets import (
    QPushButton, QMessageBox, QLineEdit, 
    QDialog, QFormLayout, QHBoxLayout, 
    QComboBox, QLabel,QDoubleSpinBox, 
    QVBoxLayout, QTextEdit)

from utils.controller import DBController

class AddRecordDialog(QDialog):
    def __init__(self, type, table, location, room, db_controller: DBController, parent=None):
        super().__init__(parent)
        self.db_controller = db_controller
        self.table = table
        self.location = location
        self.room = room

        self.setWindowTitle("Добавить запись")

        # Главный макет
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)  # Отступы от краев
        main_layout.setSpacing(10)  # Расстояние между элементами

        # Фильтры
        filter_layout = QHBoxLayout()
        location_label = QLabel(f"Локация: {location}")
        filter_layout.addWidget(location_label)
        if room:
            room_label = QLabel(f"Зал: {room}")
            filter_layout.addWidget(room_label)
        main_layout.addLayout(filter_layout)

        # Поля ввода
        input_layout = QFormLayout()
        input_layout.setSpacing(8)  # Расстояние между строками ввода

        if table == "accounting":
            if type == "Equipment":
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
            self.input_name = QLineEdit(self)
            self.input_description = QTextEdit(self)
            self.input_status = QComboBox(self)
            self.input_status.addItems(["OK", "Damaged"])
            input_layout.addRow("Наименование:", self.input_name)
            input_layout.addRow("Описание:", self.input_description)
            input_layout.addRow("Состояние:", self.input_status)

        else:
            self.input_name = QLineEdit(self)
            self.input_legal_entity = QLineEdit(self)
            self.input_price = QDoubleSpinBox(self)
            self.input_price.setRange(0.0, 1000000.0)
            self.input_price.setDecimals(2)
            self.input_price.setSingleStep(10)
            self.input_price.setValue(0.0)
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
            print('add')
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запись: {e}")
