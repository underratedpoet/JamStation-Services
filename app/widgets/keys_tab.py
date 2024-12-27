from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, 
    QDialog, QLabel, QMessageBox, QComboBox, QDateTimeEdit, QHeaderView
)
from PyQt6.QtCore import Qt, QDateTime
from utils.controller import DBController
from datetime import datetime


class KeysTransfersTab(QDialog):
    def __init__(self, db_controller: DBController, location_id: int, employee_id: int):
        super().__init__()
        self.db_controller = db_controller
        self.location_id = location_id
        self.employee_id = employee_id
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Таблица текущих состояний ключей
        self.keys_table = QTableWidget()
        self.keys_table.setColumnCount(3)
        self.keys_table.setHorizontalHeaderLabels(["Комната", "Ключ", "Действие"])
        self.keys_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.keys_table)

        # Кнопка для просмотра истории
        history_button = QPushButton("Посмотреть историю")
        history_button.clicked.connect(self.show_history)
        layout.addWidget(history_button)

        self.setLayout(layout)

        # Загрузка данных
        self.load_keys_status()

    def load_keys_status(self):
        """Загружает список всех комнат и текущий статус ключей для заданной локации."""
        rooms_status = self.db_controller.get_keys_status(location_id=self.location_id)
        print(rooms_status)
        self.keys_table.setRowCount(len(rooms_status))
        for row, room in enumerate(rooms_status):
            self.keys_table.setItem(row, 0, QTableWidgetItem(room["room_name"]))
            self.keys_table.setItem(
                row, 1, QTableWidgetItem("На месте" if room["is_returned"] else "Не на месте")
            )

            action_button = QPushButton("Сдать ключ" if room["is_returned"] else "Вернуть ключ")
            action_button.clicked.connect(
                lambda _, r_id=room["room_id"], k_id=room["key_id"], is_ret=room["is_returned"]: 
                self.handle_key_action(r_id, k_id, is_ret)
            )
            self.keys_table.setCellWidget(row, 2, action_button)

    def handle_key_action(self, room_id: int, key_id: int, is_returned: bool):
        """Обрабатывает действие с ключом (сдать или вернуть)."""
        if is_returned:
            schedules = self.db_controller.get_today_schedules_by_room(room_id, self.location_id)
            print(schedules)
            if not schedules:
                QMessageBox.warning(self, "Ошибка", "Нет активных бронирований для этой комнаты сегодня.")
                return

            dialog = QDialog(self)
            dialog.setWindowTitle("Привязать ключ к расписанию")
            layout = QVBoxLayout(dialog)

            combo_box = QComboBox()
            for schedule in schedules:
                combo_box.addItem(
                    f"{schedule['start_time']} - {schedule['client_name']}",
                    schedule["id"]
                )
            layout.addWidget(combo_box)

            submit_button = QPushButton("Сдать ключ")
            submit_button.clicked.connect(
                lambda: self.submit_key_transfer(dialog, key_id, combo_box.currentData())
            )
            layout.addWidget(submit_button)

            dialog.setLayout(layout)
            dialog.exec()
        else:
            try:
                # Вернуть ключ (обновить rental_end_time)
                self.db_controller.update_record("Keys_Transfers", {"rental_end_time":datetime.now()},{"id":key_id})
                QMessageBox.information(self, "Успех", "Ключ возвращён.")
                self.load_keys_status()
            except Exception as e:
                QMessageBox.warning(self, "Ошибка", f"Не удалось вернуть ключ: {e}")

    def submit_key_transfer(self, dialog: QDialog, key_id: int, schedule_id: int):
        """Привязывает ключ к расписанию."""
        try:
            self.db_controller.create_key_transfer(
                key_id, schedule_id, self.employee_id
            )
            QMessageBox.information(self, "Успех", "Ключ сдан.")
            dialog.accept()
            self.load_keys_status()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сдать ключ: {e}")

    def show_history(self):
        """Отображает историю операций с ключами."""
        history = self.db_controller.get_keys_history(self.location_id)
        print(history)

        dialog = QDialog(self)
        dialog.setWindowTitle("История ключей")
        layout = QVBoxLayout(dialog)

        for record in history:
            record_label = QLabel(
                f"{record['timestamp']} - {record['room_name']} - Ключ {record['action']} сотрудником "
                f"{record['employee_id']}, {record['employee_name']}"
            )
            layout.addWidget(record_label)

        close_button = QPushButton("Закрыть")
        close_button.clicked.connect(dialog.accept)
        layout.addWidget(close_button)

        dialog.setLayout(layout)
        dialog.exec()
