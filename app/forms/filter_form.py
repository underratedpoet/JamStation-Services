from PyQt6.QtWidgets import QPushButton, QMessageBox, QLineEdit, QDialog, QFormLayout

from utils.controller import DBController

class FindRecordsDialog(QDialog):
    def __init__(self, table_columns, db_controller: DBController, table_name, parent=None):
        super().__init__(parent)
        self.db_controller = db_controller
        self.table_name = table_name
        self.table_columns = table_columns  # Исключаем столбец ID
        self._parent = parent

        self.setWindowTitle("Найти")
        self.setFixedSize(400, 300)

        # Layout для формы ввода данных
        self.layout = QFormLayout(self)

        # Поля ввода для каждой колонки
        self.inputs = {}
        for column in self.table_columns:
            input_field = QLineEdit(self)
            input_field.textChanged.connect(self.find)
            self.inputs[column] = input_field
            self.layout.addRow(f"{column}:", input_field)

        # Кнопки сохранения и отмены
        self.save_button = QPushButton("Применить фильтры", self)
        self.save_button.clicked.connect(self.save_filters)
        self.layout.addRow(self.save_button)

        self.cancel_button = QPushButton("Сбросить", self)
        self.cancel_button.clicked.connect(self.drop_filters)
        self.layout.addRow(self.cancel_button)

    def find(self):
        try:
            # Получаем значения из полей
            values = [self.inputs[column].text() for column in self.table_columns]
            self._parent.column_filters = {}
            for column, value in zip(self.table_columns, values):
                self._parent.column_filters[column] = value

            self._parent.load_data()
            #self._parent.column_filters = None
            #self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить запись: {e}")

    def drop_filters(self):
        self._parent.column_filters = None
        self.accept()

    def save_filters(self):
        self.accept()