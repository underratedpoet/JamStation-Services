import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QPushButton, QWidget, QMessageBox, QLabel, QComboBox, QHBoxLayout, QLineEdit, QDialog, QFormLayout, QTabWidget
)
from PyQt6.QtCore import Qt
from controller import DBController

class AddRecordDialog(QDialog):
    def __init__(self, table_columns, db_controller, table_name, parent=None):
        super().__init__(parent)
        self.db_controller = db_controller
        self.table_name = table_name
        self.table_columns = table_columns[1:]  # Исключаем столбец ID

        self.setWindowTitle("Добавить запись")
        self.setFixedSize(400, 300)

        # Layout для формы ввода данных
        self.layout = QFormLayout(self)

        # Поля ввода для каждой колонки
        self.inputs = {}
        for column in self.table_columns:
            input_field = QLineEdit(self)
            self.inputs[column] = input_field
            self.layout.addRow(f"{column}:", input_field)

        # Кнопки сохранения и отмены
        self.save_button = QPushButton("Сохранить", self)
        self.save_button.clicked.connect(self.save_record)
        self.layout.addRow(self.save_button)

        self.cancel_button = QPushButton("Отмена", self)
        self.cancel_button.clicked.connect(self.reject)
        self.layout.addRow(self.cancel_button)

    def save_record(self):
        try:
            # Получаем значения из полей
            values = [self.inputs[column].text() for column in self.table_columns]

            # Формируем запрос INSERT
            columns_str = ", ".join(self.table_columns)
            placeholders = ", ".join("?" for _ in self.table_columns)
            query = f"INSERT INTO {self.table_name} ({columns_str}) VALUES ({placeholders})"

            # Выполняем запрос
            self.db_controller.execute_query(query, tuple(values))
            self.db_controller.connection.commit()

            QMessageBox.information(self, "Успех", "Запись успешно добавлена.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запись: {e}")