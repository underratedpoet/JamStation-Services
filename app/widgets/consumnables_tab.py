from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QScrollArea, QWidget, QLabel, QPushButton, 
    QDialog, QFormLayout, QLineEdit, QSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt
from utils.controller import DBController
from utils.shemas import Consumable

class ConsumablesTab(QDialog):
    def __init__(self, location_id: int, db_controller: DBController):
        super().__init__()
        self.location_id = location_id
        self.db_controller = db_controller
        self.setWindowTitle("Управление расходниками")
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Список расходников
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)

        layout.addWidget(self.scroll_area)

        # Кнопки для управления
        buttons_layout = QHBoxLayout()

        add_new_button = QPushButton("Добавить новый")
        add_new_button.clicked.connect(self.add_new_consumable)
        buttons_layout.addWidget(add_new_button)

        delete_zero_button = QPushButton("Удалить с количеством 0")
        delete_zero_button.clicked.connect(self.delete_zero_consumables)
        buttons_layout.addWidget(delete_zero_button)

        layout.addLayout(buttons_layout)

        self.setLayout(layout)

        # Загрузка данных
        self.load_consumables()

    def load_consumables(self):
        """Загружает и отображает список расходников."""
        # Очищаем текущий список
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        consumables = self.db_controller.get_consumables_by_location(self.location_id)

        if not consumables:
            self.scroll_layout.addWidget(QLabel("Расходники отсутствуют."))
        else:
            for consumable in consumables:
                self.scroll_layout.addWidget(self.create_consumable_tile(consumable))

    def create_consumable_tile(self, consumable: Consumable) -> QWidget:
        """Создаёт виджет для расходника."""
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
        print(consumable)
        tile_layout.addWidget(QLabel(f"ID: {consumable.id}"))
        tile_layout.addWidget(QLabel(f"Название: {consumable.name}"))
        tile_layout.addWidget(QLabel(f"Цена: {consumable.price} руб."))
        tile_layout.addWidget(QLabel(f"Количество: {consumable.quantity}"))

        # Поле для изменения количества
        quantity_layout = QHBoxLayout()
        quantity_spin = QSpinBox()
        quantity_spin.setMinimum(-consumable.quantity)
        quantity_spin.setMaximum(10000)
        quantity_layout.addWidget(QLabel("Изменить количество:"))
        quantity_layout.addWidget(quantity_spin)

        change_quantity_button = QPushButton("Обновить")
        change_quantity_button.clicked.connect(lambda: self.change_quantity(consumable.id, quantity_spin.value()))
        quantity_layout.addWidget(change_quantity_button)
        tile_layout.addLayout(quantity_layout)

        # Поле для изменения цены
        price_layout = QHBoxLayout()
        price_input = QLineEdit()
        price_input.setPlaceholderText(f"Текущая цена: {consumable.price}")
        price_layout.addWidget(QLabel("Новая цена:"))
        price_layout.addWidget(price_input)

        change_price_button = QPushButton("Обновить")
        change_price_button.clicked.connect(lambda: self.change_price(consumable.id, price_input.text()))
        price_layout.addWidget(change_price_button)
        tile_layout.addLayout(price_layout)

        return tile

    def add_new_consumable(self):
        """Открывает окно для добавления нового расходника."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить новый расходник")
        form = QFormLayout(dialog)

        name_input = QLineEdit()
        form.addRow("Название:", name_input)

        price_input = QLineEdit()
        form.addRow("Цена:", price_input)

        quantity_input = QSpinBox()
        quantity_input.setMinimum(0)
        form.addRow("Количество:", quantity_input)

        add_button = QPushButton("Добавить")
        add_button.clicked.connect(
            lambda: self.add_consumable_action(dialog, name_input.text(), price_input.text(), quantity_input.value())
        )
        form.addWidget(add_button)

        dialog.setLayout(form)
        dialog.exec()

    def add_consumable_action(self, dialog: QDialog, name: str, price: str, quantity: int):
        """Обрабатывает добавление нового расходника."""
        try:
            price = float(price)
            self.db_controller.insert("Consumables", {"location_id":self.location_id, "name":name, "price":price, "quantity":quantity})
            QMessageBox.information(self, "Успех", "Расходник добавлен успешно.")
            dialog.accept()
            self.load_consumables()
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректное значение цены.")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", "Не удалось добавить расходник.")

    def change_quantity(self, consumable_id: int, quantity: int):
        """Изменяет количество расходника."""
        try:
            self.db_controller.add_consumable_quantity(consumable_id, quantity)
            QMessageBox.information(self, "Успех", "Количество обновлено успешно.")
            self.load_consumables()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось обновить количество: {e}")

    def change_price(self, consumable_id: int, price: str):
        """Изменяет цену расходника."""
        try:
            price = float(price)
            self.db_controller.update_record("Consumables", {"price":price}, {"id":consumable_id})
            QMessageBox.information(self, "Успех", "Цена обновлена успешно.")
            self.load_consumables() 
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите корректное значение цены.")
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось обновить цену: {e}")

    def delete_zero_consumables(self):
        """Удаляет все расходники с количеством 0."""
        try:
            success = self.db_controller.delete_zero_quantity_consumables(self.location_id)
            QMessageBox.information(self, "Успех", "Удалены все расходники с количеством 0.")
            self.load_consumables()
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось удалить расходники с количеством 0: {e}")
