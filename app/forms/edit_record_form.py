from datetime import datetime

from PyQt6.QtWidgets import (
    QPushButton, QMessageBox, QLineEdit, 
    QDialog, QFormLayout, QHBoxLayout, 
    QComboBox, QCheckBox, QDoubleSpinBox, 
    QVBoxLayout, QTextEdit)

from utils.controller import DBController
from utils.shemas import EquipmentRecord, RepairRecord, InstrumentRecord, CheckRecord

class EditRecordDialog(QDialog):
    def __init__(self, record, db_controller: DBController, parent=None):
        super().__init__(parent)
        self.db_controller = db_controller
        self.type = type
        self.record = record
        

        # Главный макет
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)  # Отступы от краев
        main_layout.setSpacing(10)  # Расстояние между элементами

        # Поля ввода
        input_layout = QFormLayout()
        input_layout.setSpacing(8)  # Расстояние между строками ввода

        if isinstance(record, EquipmentRecord):
            self.setWindowTitle("Редактировать запись: Оборудование")
            self.input_name = QLineEdit(self)
            self.input_name.setText(record.name)
            self.input_type = QLineEdit(self)
            self.input_type.setText(record.type)
            self.input_status = QLineEdit(self)
            self.input_status.setText(record.status)
            input_layout.addRow("Наименование:", self.input_name)
            input_layout.addRow("Тип:", self.input_type)
            input_layout.addRow("Состояние:", self.input_status)
        elif isinstance(record, InstrumentRecord):
            self.setWindowTitle("Редактировать запись: Инструменты")
            self.input_name = QLineEdit(self)
            self.input_name.setText(record.name)
            self.input_hourly_rate = QDoubleSpinBox(self)
            self.input_hourly_rate.setRange(0.0, 5000.0)
            self.input_hourly_rate.setDecimals(2)
            self.input_hourly_rate.setSingleStep(0.1)
            self.input_hourly_rate.setValue(record.hourly_rate)
            input_layout.addRow("Наименование:", self.input_name)
            input_layout.addRow("Руб/ч:", self.input_hourly_rate)
        elif isinstance(record, CheckRecord):
            self.setWindowTitle("Редактировать запись: Проверки")
            self.input_description = QTextEdit(self)
            self.input_description.setPlainText(record.description)
            input_layout.addRow("Описание:", self.input_description)
        else:
            self.setWindowTitle("Редактировать запись: Ремонт")
            self.input_legal_entity = QLineEdit(self)
            self.input_legal_entity.setText(record.legal_entity)
            self.input_price = QDoubleSpinBox(self)
            self.input_status = QLineEdit(self)
            self.input_status.setText(record.repair_status)
            self.checkbox = QCheckBox("Ремонт завершен", self)
            self.input_price.setRange(0.0, 1000000.0)
            self.input_price.setDecimals(2)
            self.input_price.setSingleStep(10)
            self.input_price.setValue(record.repair_cost)
            input_layout.addRow("Мастерская:", self.input_legal_entity)
            input_layout.addRow("Стоимость:", self.input_price)
            input_layout.addRow("Статус ремонта:", self.input_status)
            if not record.repair_end_date:
                input_layout.addRow(self.checkbox)
            else:
                self.checkbox.hide()

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
            if isinstance(self.record, EquipmentRecord):
                values = {
                    'name': self.input_name.text(),
                    'type': self.input_type.text(),
                    'status': self.input_status.text()
                }
                self.db_controller.update_record("Equipment", values, {"id":self.record.id})
            elif isinstance(self.record, InstrumentRecord): 
                values = {
                    'name': self.input_name.text(),
                    'hourly_rate': self.input_hourly_rate.value(),
                }
                self.db_controller.update_record("Instruments", values, {"id":self.record.id})                
            elif isinstance(self.record, CheckRecord):   
                values = {
                    'description': self.input_description.toPlainText(),
                }
                self.db_controller.update_record("Checks", values, {"id":self.record.id})  
            else:
                values = {
                    'legal_entity': self.input_legal_entity.text(),
                    'repair_cost': self.input_price.value(),
                    'repair_status': self.input_status.text(),
                }
                if self.checkbox.isChecked() and not self.record.repair_end_date:
                    values['repair_status'] = 'Завершено'
                    values['repair_end_date'] = datetime.today()
                self.db_controller.update_record("Repairs", values, {"id":self.record.id})
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запись: {e}")
