from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QScrollArea, QWidget, QLabel, QPushButton, 
    QDialog, QFormLayout, QDialogButtonBox, QVBoxLayout, QMessageBox, QLineEdit
)
from PyQt6.QtCore import Qt
from pydantic import BaseModel
from datetime import datetime

from utils.controller import DBController
from utils.shemas import ClientRecord, Penalty

class ClientPenaltiesTab(QDialog):
    def __init__(self, location_id: int, db_controller: DBController):
        super().__init__()
        self.location_id = location_id
        self.db_controller = db_controller
        self.setWindowTitle("Клиенты и штрафы")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Загрузка данных о клиентах
        clients = self.db_controller.get_clients_by_location(self.location_id)

        if not clients:
            layout.addWidget(QLabel("Нет клиентов для данной локации."))
        else:
            # Прокручиваемый список клиентов
            scroll_area = QScrollArea()
            scroll_area.setWidgetResizable(True)
            scroll_content = QWidget()
            scroll_layout = QVBoxLayout(scroll_content)
            scroll_area.setWidget(scroll_content)

            for client in clients:
                client_tile = self.create_client_tile(client)
                scroll_layout.addWidget(client_tile)

            layout.addWidget(scroll_area)

        self.setLayout(layout)

    def create_client_tile(self, client: ClientRecord) -> QWidget:
        """Создаёт плитку клиента с кнопками для просмотра и добавления штрафов."""
        tile = QWidget()
        tile_layout = QVBoxLayout(tile)

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

        tile_layout.addWidget(QLabel(f"ID: {client.id}"))
        tile_layout.addWidget(QLabel(f"Имя: {client.name}"))
        tile_layout.addWidget(QLabel(f"Email: {client.email or 'Не указано'}"))
        tile_layout.addWidget(QLabel(f"Телефон: {client.phone_number or 'Не указан'}"))

        # Кнопки для управления штрафами
        penalty_buttons_layout = QHBoxLayout()

        view_penalty_button = QPushButton("Посмотреть штрафы")
        view_penalty_button.clicked.connect(lambda: self.show_penalties(client))
        penalty_buttons_layout.addWidget(view_penalty_button)

        add_penalty_button = QPushButton("Добавить штраф")
        add_penalty_button.clicked.connect(lambda: self.add_penalty(client))
        penalty_buttons_layout.addWidget(add_penalty_button)

        tile_layout.addLayout(penalty_buttons_layout)

        return tile


    def show_penalties(self, client: ClientRecord):
        """Отображает штрафы клиента."""
        penalties = self.db_controller.get_penalties_by_client(client.id)
        if not penalties:
            QMessageBox.information(self, "Штрафы", f"У клиента {client.name} нет штрафов.")
            return

        # Создание нового окна для отображения штрафов
        penalties_dialog = QDialog(self)
        penalties_dialog.setWindowTitle(f"Штрафы клиента: {client.name}")

        main_layout = QVBoxLayout()

        # Прокручиваемая область для штрафов
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_area.setWidget(scroll_content)

        for penalty in penalties:
            penalty_layout = QVBoxLayout()
            penalty_widget = QWidget()
            penalty_widget.setLayout(penalty_layout)

            penalty_widget.setStyleSheet("""
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

            penalty_layout.addWidget(QLabel(f"Описание: {penalty.description or 'Нет описания'}"))
            penalty_layout.addWidget(QLabel(f"Сумма: {penalty.amount}"))
            penalty_layout.addWidget(QLabel(f"Применён: {penalty.applied_at}"))
            penalty_layout.addWidget(QLabel(f"Списан: {'Да' if penalty.written_off else 'Нет'}"))

            # Кнопка для списания штрафа
            if not penalty.written_off:
                write_off_button = QPushButton("Списать штраф")
                write_off_button.clicked.connect(lambda _, p_id=penalty.id: self.write_off_penalty(p_id, penalties_dialog))
                penalty_layout.addWidget(write_off_button)

            scroll_layout.addWidget(penalty_widget)

        main_layout.addWidget(scroll_area)

        # Кнопка закрытия
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(penalties_dialog.reject)
        main_layout.addWidget(button_box)

        penalties_dialog.setLayout(main_layout)
        penalties_dialog.exec()


    def add_penalty(self, client: ClientRecord):
        """Открывает форму для добавления штрафа клиенту."""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Добавить штраф клиенту: {client.name}")

        layout = QFormLayout()

        # Поля для ввода данных штрафа
        description_label = QLabel("Описание:")
        description_input = QLineEdit()
        amount_label = QLabel("Сумма:")
        amount_input = QLineEdit()

        # Добавление полей в форму
        layout.addRow(description_label, description_input)
        layout.addRow(amount_label, amount_input)

        # Кнопки "Добавить" и "Отмена"
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(lambda: self.confirm_add_penalty(client, description_input.text(), amount_input.text(), dialog))
        button_box.rejected.connect(dialog.reject)

        layout.addWidget(button_box)
        dialog.setLayout(layout)
        dialog.exec()

    def confirm_add_penalty(self, client: ClientRecord, description: str, amount: str, dialog: QDialog):
        """Подтверждает добавление штрафа."""
        try:
            amount_value = float(amount)
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректную сумму штрафа.")
            return

        success = self.db_controller.add_penalty_for_client(client.id, description, amount_value)
        if success:
            QMessageBox.information(self, "Успех", f"Штраф для клиента {client.name} успешно добавлен.")
            dialog.accept()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось добавить штраф.")


    def write_off_penalty(self, penalty_id: int, dialog: QDialog):
        """Списывает штраф."""
        success = self.db_controller.write_off_penalty(penalty_id)
        if success == 0:
            QMessageBox.information(self, "Успех", "Штраф успешно списан.")
            dialog.accept()  # Закрываем окно штрафов, чтобы обновить список
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось списать штраф.")