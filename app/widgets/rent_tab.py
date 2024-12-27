from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QMessageBox, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt
from datetime import datetime
from utils.controller import DBController

class InstrumentRentalTab(QWidget):
    def __init__(self, db_controller: DBController, location_id: int, employee_id: int):
        super().__init__()
        self.db_controller = db_controller
        self.location_id = location_id
        self.employee_id = employee_id
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.load_instruments_status()

    def load_instruments_status(self):
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.clear_layout(self.layout)

        instruments_status = self.db_controller.get_instruments_status(self.location_id)
        for instrument in instruments_status:
            instrument_widget = QWidget()
            instrument_layout = QVBoxLayout()
            instrument_widget.setLayout(instrument_layout)

            instrument_widget.setStyleSheet("""
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

            instrument_layout.addWidget(QLabel(f"ID: {instrument['instrument_id']}"))
            instrument_layout.addWidget(QLabel(f"Название: {instrument['instrument_name']}"))
            status_text = "В аренде" if instrument["is_rented"] else "На месте"
            instrument_layout.addWidget(QLabel(f"Статус: {status_text}"))

            if instrument["is_rented"]:
                return_button = QPushButton("Вернуть инструмент")
                return_button.clicked.connect(
                    lambda _, inst_id=instrument["instrument_id"]: self.return_instrument(inst_id)
                )
                instrument_layout.addWidget(return_button)
            else:
                rent_button = QPushButton("Сдать в аренду")
                rent_button.clicked.connect(
                    lambda _, inst_id=instrument["instrument_id"]: self.rent_instrument(inst_id)
                )
                instrument_layout.addWidget(rent_button)

            self.layout.addWidget(instrument_widget)

    def rent_instrument(self, instrument_id: int):
        schedules = self.db_controller.get_today_schedules(self.location_id)
        if not schedules:
            QMessageBox.warning(self, "Нет записей", "Нет доступных записей для аренды.")
            return

        dialog = QDialog(self)
        dialog.setWindowTitle("Выберите запись для аренды")
        dialog_layout = QVBoxLayout(dialog)

        schedule_combo = QComboBox()
        for schedule in schedules:
            schedule_combo.addItem(
                f"{schedule['start_time']} - Комната: {schedule['room_name']} - Клиент: {schedule['client_name']}",
                userData=schedule["schedule_id"]
            )
        dialog_layout.addWidget(schedule_combo)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        dialog_layout.addWidget(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_schedule_id = schedule_combo.currentData()
            if selected_schedule_id:
                self.db_controller.add_rental(self.employee_id, instrument_id, selected_schedule_id)
                QMessageBox.information(self, "Успешно", "Инструмент сдан в аренду.")
                self.load_instruments_status()

    def return_instrument(self, instrument_id: int):
        self.db_controller.return_instrument(instrument_id)
        QMessageBox.information(self, "Успешно", "Инструмент возвращён.")
        self.load_instruments_status()

    def clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
