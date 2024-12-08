from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QScrollArea, QFrame, QLabel, QVBoxLayout, QHBoxLayout
from PyQt6.QtCore import Qt
from datetime import datetime

from utils.controller import DBController
from utils.shemas import Receipt, Receipt_Item, ReceiptRecord

class ReceiptTab(QWidget):
    def __init__(self, db_controller: DBController, employee_id):
        super().__init__()
        self.db_controller = db_controller
        self.employee = self.db_controller.select(["id", "location_id", "first_name", "last_name"], "Employees", employee_id)
        self.init_ui()

    def init_ui(self):
        # Основной вертикальный лейаут
        layout = QVBoxLayout()

        # Кнопка "Выписать чек"
        self.new_receipt_button = QPushButton("Выписать чек")
        self.new_receipt_button.clicked.connect(self.new_receipt)
        layout.addWidget(self.new_receipt_button)

        # Прокручиваемая область для списка чеков
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

        # Загрузка данных из БД и создание плиток
        self.load_receipts()

        self.setLayout(layout)

    def load_receipts(self, offset=0, limit=10):
        # Получение данных из БД
        location_id = self.employee[1]
        receipts = self.db_controller.select_all_receipts(location_id, offset, limit)

        for receipt_record in receipts:
            self.add_receipt_tile(receipt_record)

    def add_receipt_tile(self, receipt_record: ReceiptRecord):
        # Создание плитки для чека
        tile = QFrame()
        tile.setFrameShape(QFrame.Shape.Panel)
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

        tile_layout = QVBoxLayout()

        # Данные о чеке
        receipt_info = QLabel(f"Чек ID: {receipt_record.receipt.id}\n"
                              f"Сотрудник ID: {receipt_record.receipt.employee_id}\n"
                              f"Сумма: {receipt_record.receipt.total_amount}\n"
                              f"Создан: {receipt_record.receipt.created_at}")
        tile_layout.addWidget(receipt_info)

        # Кнопка для раскрытия позиций чека
        self.toggle_button = QPushButton("Показать позиции")
        self.toggle_button.setCheckable(True)
        self.toggle_button.toggled.connect(lambda checked, r=receipt_record: self.toggle_items(checked, r, tile_layout))
        tile_layout.addWidget(self.toggle_button)

        tile.setLayout(tile_layout)
        self.scroll_layout.addWidget(tile)

    def toggle_items(self, checked, receipt_record: ReceiptRecord, layout):
        if checked:
            self.toggle_button.setText("Скрыть позиции")
            for item in receipt_record.items:
                item_info = QLabel(f"Позиция ID: {item.id}\n"
                                   f"Таблица: {item.item_table}\n"
                                   f"ID товара: {item.item_id}\n"
                                   f"Количество: {item.quantity}\n"
                                   f"Сумма: {item.total}")
                layout.addWidget(item_info)
        else:
            self.toggle_button.setText("Показать позиции")
            # Удаление всех виджетов, кроме первых двух (информация о чеке и кнопка)
            while layout.count() > 2:
                child = layout.takeAt(2)
                if child.widget():
                    child.widget().deleteLater()

    def new_receipt(self):
        # Метод для создания нового чека (пока пустой)
        pass