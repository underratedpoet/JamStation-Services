from datetime import datetime

from PyQt6.QtWidgets import (
    QPushButton, QMessageBox, QLineEdit, 
    QDialog, QFormLayout, QHBoxLayout, 
    QComboBox, QLabel, QDoubleSpinBox, 
    QVBoxLayout, QDateEdit, QWidget, QScrollArea
)
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QSize, QDate

from utils.controller import DBController
from utils.shemas import Equipment, Instrument, Check, Repair

class AddReceiptDialog(QDialog):
    def __init__(self, location_id, employee_id, db_controller: DBController, parent=None):
        super().__init__(parent)
        self.location_id = location_id
        self.employee_id = employee_id
        self.db_controller = db_controller

        self.setWindowTitle("Выписать чек")

        # Главный макет
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # Прокручиваемая область для добавляемых позиций
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_area.setWidget(self.scroll_widget)
        self.main_layout.addWidget(self.scroll_area)

        # Кнопка "Добавить позицию"
        self.add_button = QPushButton("Добавить позицию")
        self.add_button.setIconSize(QSize(24, 24))
        self.add_button.clicked.connect(self.add_item)
        self.main_layout.addWidget(self.add_button)

        # Кнопки сохранения и отмены
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Сохранить")
        self.save_button.clicked.connect(self.save_receipt)
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        self.main_layout.addLayout(button_layout)

        # Переменные для хранения значений каждой позиции
        self.items_data = []

    def add_item(self):
        item_widget = QWidget()
        item_layout = QVBoxLayout(item_widget)

        # Выпадающий список для выбора типа позиции
        type_combo = QComboBox()
        type_combo.addItems(["Репетиция", "Товар", "Аренда"])
        item_layout.addWidget(QLabel("Тип позиции:"))
        item_layout.addWidget(type_combo)

        # Контейнер для динамического содержимого
        details_widget = QWidget()
        details_layout = QFormLayout(details_widget)
        item_layout.addWidget(details_widget)

        def update_details(index):
            # Очистка текущего содержимого
            while details_layout.count():
                widget = details_layout.takeAt(0).widget()
                if widget:
                    widget.deleteLater()

            if index == 0:  # Репетиция
                room_combo = QComboBox()
                room_combo.setObjectName("roomCombo")  # Уникальное имя для выбора зала
                # Получение списка залов для текущей локации
                rooms = self.db_controller.select(columns=["id", "name"], table="Rooms", filters={"location_id": self.location_id})
                if rooms:
                    room_combo.addItems([room[1] for room in rooms])  # Индекс 1 соответствует "name"

                date_picker = QDateEdit()
                date_picker.setObjectName("datePicker")  # Уникальное имя для выбора даты
                date_picker.setCalendarPopup(True)
                date_picker.setDate(QDate.currentDate())

                rehearsal_combo = QComboBox()
                rehearsal_combo.setObjectName("rehearsalCombo")  # Уникальное имя для выбора репетиции
                # Обновление списка репетиций при выборе зала и даты
                def update_rehearsals():
                    selected_room = room_combo.currentText()
                    room_id = next((room[0] for room in rooms if room[1] == selected_room), None)  # Индекс 0 соответствует "id"
                    selected_date = date_picker.date().toString("yyyy-MM-dd")  # Получаем выбранную дату в формате 'YYYY-MM-DD'
                    if room_id:
                        rehearsals = self.db_controller.execute_query(
                            """
                            SELECT start_time FROM Schedules 
                            WHERE room_id = ? AND status = N'Активно' 
                            AND CAST(start_time AS DATE) = ?  -- Добавляем фильтрацию по дате
                            """,
                            (room_id, selected_date)
                        )
                        rehearsal_combo.clear()
                        if rehearsals:
                            rehearsal_combo.addItems([datetime.strftime(r[0], "%H:%M") for r in rehearsals])  # Индекс 0 соответствует "start_time"
                        else:
                            rehearsal_combo.addItem("Нет доступных репетиций")

                room_combo.currentTextChanged.connect(update_rehearsals)
                date_picker.dateChanged.connect(update_rehearsals)  # Обработчик для изменения даты
                update_rehearsals()

                details_layout.addRow("Зал:", room_combo)
                details_layout.addRow("Дата:", date_picker)
                details_layout.addRow("Репетиция:", rehearsal_combo)

            elif index == 1:  # Товар
                product_combo = QComboBox()
                product_combo.setObjectName("productCombo")  # Уникальное имя для выбора товара
                # Получение списка товаров для текущей локации
                products = self.db_controller.select(columns=["id", "name"], table="Consumables", filters={"location_id": self.location_id})
                if products:
                    product_combo.addItems([product[1] for product in products])  # Индекс 1 соответствует "name"

                quantity_spin = QDoubleSpinBox()
                quantity_spin.setObjectName("quantitySpin")  # Уникальное имя для выбора количества
                quantity_spin.setMinimum(1)

                details_layout.addRow("Товар:", product_combo)
                details_layout.addRow("Количество:", quantity_spin)

            elif index == 2:  # Аренда
                instrument_combo = QComboBox()
                instrument_combo.setObjectName("instrumentCombo")  # Уникальное имя для выбора инструмента
                # Получение списка инструментов для текущей локации
                instruments = self.db_controller.select(columns=["id", "name"], table="Instruments", filters={"location_id": self.location_id})
                if instruments:
                    instrument_combo.addItems([instrument[1] for instrument in instruments])  # Индекс 1 соответствует "name"

                details_layout.addRow("Инструмент:", instrument_combo)

        type_combo.currentIndexChanged.connect(update_details)
        update_details(0)

        # Добавление данных в self.items_data
        self.items_data.append({
            'type_combo': type_combo,
            'details_widget': details_widget
        })

        self.scroll_layout.addWidget(item_widget)


    def save_receipt(self):
        # Сбор всех позиций чека
        items = []
        total_amount = 0
        print("Начинаем обработку позиций...")

        # Перебор элементов layout для получения позиций
        for i, item_data in enumerate(self.items_data):
            item_widget = self.scroll_layout.itemAt(i).widget()
            if item_widget:
                item_layout = item_widget.layout()
                type_combo = item_data['type_combo']
                details_widget = item_data['details_widget']

                if isinstance(type_combo, QComboBox):  # Убедитесь, что это QComboBox
                    # Получение выбранного типа позиции
                    item_type = type_combo.currentText()
                    print(f"Тип позиции для элемента {i + 1}: {item_type}")

                    if item_type == "Репетиция":
                        room_combo = details_widget.findChild(QComboBox, "roomCombo")  # Используем уникальное имя
                        date_picker = details_widget.findChild(QDateEdit, "datePicker")  # Используем уникальное имя
                        rehearsal_combo = details_widget.findChild(QComboBox, "rehearsalCombo")  # Используем уникальное имя

                        if room_combo and date_picker and rehearsal_combo:
                            print(room_combo.currentText(), date_picker.date(), rehearsal_combo.currentText())
                            room_name = room_combo.currentText()
                            room_id = self.db_controller.select(
                                columns=["id"], table="Rooms", filters={"location_id": self.location_id, "name": room_name}
                            )
                            if not room_id:
                                print(f"Комната {room_name} не найдена!")
                                continue
                            room_id = room_id[0][0]

                            rehearsal_time = rehearsal_combo.currentText()
                            rehearsal_start_time = f"{date_picker.date().toString('yyyy-MM-dd')} {rehearsal_time}:00"
                            print(rehearsal_start_time)

                            # Получаем цену аренды зала
                            room_price = self.db_controller.select(
                                columns=["hourly_rate"], table="Rooms", filters={"id": room_id}
                            )[0][0]

                            # Получаем продолжительность репетиции из расписания
                            schedule = self.db_controller.select(
                                columns=["duration_hours", "id"], table="Schedules", filters={"room_id": room_id, "start_time": rehearsal_start_time}
                            )

                            self.db_controller.update_record("Schedules", {"status": "Оплачено"}, {"id": schedule[0][1]})
                            if schedule:
                                duration = schedule[0][0]
                                total_cost = room_price * duration
                                total_amount += total_cost

                                # Добавляем позицию чека
                                items.append({
                                    "item_table": "Schedule",
                                    "item_id": schedule[0][1],
                                    "quantity": None,
                                    "total": total_cost
                                })
                        else:
                            print(f"Не все элементы для репетиции найдены.")
                    elif item_type == "Товар":
                        product_combo = details_widget.findChild(QComboBox, "productCombo")  # Используем уникальное имя
                        quantity_spin = details_widget.findChild(QDoubleSpinBox, "quantitySpin")  # Используем уникальное имя

                        if product_combo and quantity_spin:
                            product_name = product_combo.currentText()
                            product_id = self.db_controller.select(
                                columns=["id"], table="Consumables", filters={"location_id": self.location_id, "name": product_name}
                            )
                            if not product_id:
                                print(f"Продукт {product_name} не найден!")
                                continue
                            product_id = product_id[0][0]
                            quantity = quantity_spin.value()

                            product = self.db_controller.select(
                                columns=["price", "quantity"], table="Consumables", filters={"id": product_id}
                            )
                            # Получаем цену товара
                            product_price = product[0][0]

                            self.db_controller.update_record("Consumables", {"quantity": product[0][1]-quantity}, {"id": product_id})

                            total_cost = float(product_price) * quantity
                            total_amount = float(total_amount)
                            total_amount += total_cost

                            # Добавляем позицию чека
                            items.append({
                                "item_table": "Consumables",
                                "item_id": product_id,
                                "quantity": quantity,
                                "total": total_cost
                            })
                        else:
                            print("Не все элементы для товара найдены.")
                    elif item_type == "Аренда":
                        instrument_combo = details_widget.findChild(QComboBox, "instrumentCombo")  # Используем уникальное имя

                        if instrument_combo:
                            instrument_name = instrument_combo.currentText()
                            instrument_id = self.db_controller.select(
                                columns=["id"], table="Instruments", filters={"location_id": self.location_id, "name": instrument_name}
                            )
                            if not instrument_id:
                                print(f"Инструмент {instrument_name} не найден!")
                                continue
                            instrument_id = instrument_id[0][0]

                            # Получаем цену аренды инструмента
                            instrument_price = self.db_controller.select(
                                columns=["hourly_rate"], table="Instruments", filters={"id": instrument_id}
                            )[0][0]

                            total_cost = instrument_price
                            total_amount += total_cost

                            # Добавляем позицию чека
                            items.append({
                                "item_table": "Instruments",
                                "item_id": instrument_id,
                                "quantity": None,
                                "total": total_cost
                            })
                        else:
                            print("Не все элементы для аренды инструмента найдены.")

        # Сохранение чека в таблице Receipts
        if items:
            receipt_data = {
                "employee_id": self.employee_id,
                "total_amount": total_amount,
                "created_at": datetime.now()
            }
            try:
                receipt_id = self.db_controller.insert(table="Receipts", data=receipt_data)
                if not receipt_id:
                    raise ValueError("Ошибка: Не удалось получить receipt_id")
                print(receipt_id)

                # Сохранение позиций чека в таблице Receipt_Items
                for item in items:
                    item_data = {
                        "receipt_id": receipt_id,
                        "item_table": item["item_table"],
                        "item_id": item["item_id"],
                        "quantity": item["quantity"],
                        "total": item["total"]
                    }
                    self.db_controller.insert(table="Receipt_Items", data=item_data)

                print("Чек успешно сохранен.")
                QMessageBox.information(self, "Успех", "Чек успешно сохранен.")
                self.accept()
            except Exception as e:
                print(f"Ошибка при сохранении чека: {e}")
                QMessageBox.warning(self, "Ошибка", f"Ошибка при сохранении чека: {e}")
        else:
            print("Не выбраны позиции для чека.")
            QMessageBox.warning(self, "Ошибка", "Не выбраны позиции для чека.")
