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

class LoginWindow(QWidget):
    def __init__(self, db_controller: DBController):
        super().__init__()
        self.setWindowTitle("Авторизация")
        self.setFixedSize(300, 200)
        self.db_controller = db_controller

        # UI компоненты
        self.login_label = QLabel("Логин:", self)
        self.login_input = QLineEdit(self)
        self.login_input.setPlaceholderText("Введите логин")
        self.login_input.setFixedWidth(250)

        self.password_label = QLabel("Пароль:", self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setFixedWidth(250)

        self.login_button = QPushButton("Войти", self)
        self.login_button.clicked.connect(self.authenticate)

        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.login_label)
        layout.addWidget(self.login_input)
        layout.addWidget(self.password_label)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)
        self.setLayout(layout)

    def authenticate(self):
        login = self.login_input.text()
        password = self.password_input.text()

        try:
            access = self.db_controller.check_password(login, password)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Неизвестная ошибка: {e}")
            return

        if access:
            self.accept_login()
        else:
            QMessageBox.critical(self, "Ошибка", "Неверный email или пароль!")

    def accept_login(self):
        self.hide()  # Скрыть окно авторизации
        self.main_window = MainWindow(self.db_controller)
        self.main_window.show()


class MainWindow(QMainWindow):
    def __init__(self, db_controller: DBController):
        super().__init__()
        self.db_controller = db_controller

        self.current_offset = 0
        self.limit = 10
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Редактирование таблицы")
        self.setGeometry(200, 200, 800, 600)

        # Создание виджета вкладок
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        # Первая вкладка
        self.tab1 = QWidget()
        self.tab_widget.addTab(self.tab1, "Редактирование таблицы")

        # Вторая и третья пустые вкладки
        self.tab2 = QWidget()
        self.tab_widget.addTab(self.tab2, "Вкладка 2")

        self.tab3 = QWidget()
        self.tab_widget.addTab(self.tab3, "Вкладка 3")

        # Выпадающий список для таблиц
        self.table_selector = QComboBox(self.tab1)
        self.table_selector.currentIndexChanged.connect(self.table_changed)

        # Таблица
        self.table = QTableWidget(self.tab1)
        self.table.setColumnCount(0)
        self.table.setRowCount(0)
        self.table.itemChanged.connect(self.item_changed)  # Отслеживание изменений
        self.table.itemSelectionChanged.connect(self.selection_changed)  # Отслеживание выделения

        # Метка для пустой таблицы
        self.no_data_label = QLabel("Нет записей", self.tab1)
        self.no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_data_label.hide()

        # Кнопки
        self.delete_button = QPushButton("Удалить", self.tab1)
        self.delete_button.setEnabled(False)
        self.delete_button.hide()
        self.delete_button.clicked.connect(self.delete_record)

        self.save_button = QPushButton("Сохранить изменения", self.tab1)
        self.save_button.setEnabled(False)
        self.save_button.clicked.connect(self.save_changes)

        self.prev_button = QPushButton("Назад", self.tab1)
        self.prev_button.setEnabled(False)
        self.prev_button.clicked.connect(self.load_previous_page)

        self.next_button = QPushButton("Вперёд", self.tab1)
        self.next_button.setEnabled(False)
        self.next_button.clicked.connect(self.load_next_page)

        self.add_button = QPushButton("Добавить запись", self.tab1)
        self.add_button.clicked.connect(self.add_record)

        # Размещение элементов на первой вкладке
        layout = QVBoxLayout()
        table_controls_layout = QHBoxLayout()
        table_controls_layout.addWidget(QLabel("Таблица:", self.tab1))
        table_controls_layout.addWidget(self.table_selector)

        navigation_layout = QHBoxLayout()
        navigation_layout.addWidget(self.prev_button)
        navigation_layout.addWidget(self.next_button)

        layout.addLayout(table_controls_layout)
        layout.addWidget(self.table)
        layout.addWidget(self.no_data_label)
        layout.addLayout(navigation_layout)
        layout.addWidget(self.delete_button)
        layout.addWidget(self.save_button)
        layout.addWidget(self.add_button)

        self.tab1.setLayout(layout)

        self.load_table_list()

    def load_table_list(self):
        """Загрузка списка таблиц в выпадающий список"""
        try:
            query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
            tables = [row[0] for row in self.db_controller.execute_query(query)]
            self.table_selector.addItems(tables)
            if tables:
                self.current_table = tables[0]
                self.load_data()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить список таблиц: {e}")

    def table_changed(self):
        """Загрузка данных выбранной таблицы"""
        self.current_table = self.table_selector.currentText()
        self.current_offset = 0
        self.load_data()

    def load_data(self):
        """Загрузка данных из БД в таблицу"""
        try:
            if not self.current_table:
                return

            # Получение данных
            data = self.db_controller.paginate_table(self.current_table, self.current_offset, self.limit)
            columns = self.db_controller.get_table_columns(self.current_table)
            if not data:  # Если данных нет, отображаем метку
                self.table.clear()
                self.table.setRowCount(0)
                self.table.setColumnCount(0)
                self.no_data_label.show()
                self.prev_button.setEnabled(self.current_offset > 0)
                self.next_button.setEnabled(False)
                return

            self.no_data_label.hide()

            # Настройка таблицы
            self.table.setColumnCount(len(columns))
            self.table.setHorizontalHeaderLabels(columns)
            self.table.setRowCount(len(data))

            for row_idx, row in enumerate(data):
                for col_idx, col_name in enumerate(columns):
                    item = QTableWidgetItem(str(row[col_name]))
                    if col_idx == 0:  # Первый столбец (ID) неизменяем
                        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)
                    else:  # Остальные столбцы редактируемы
                        item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsEditable)
                    self.table.setItem(row_idx, col_idx, item)

            self.prev_button.setEnabled(self.current_offset > 0)
            self.next_button.setEnabled(len(data) == self.limit)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить данные: {e}")

    def load_previous_page(self):
        """Загрузка предыдущей страницы"""
        if self.current_offset >= self.limit:
            self.current_offset -= self.limit
            self.load_data()

    def load_next_page(self):
        """Загрузка следующей страницы"""
        self.current_offset += self.limit
        self.load_data()

    def selection_changed(self):
        """Показываем кнопку удаления при выделении строки"""
        if self.table.currentItem():
            self.delete_button.show()
            self.delete_button.setEnabled(True)
        else:
            self.delete_button.hide()
            self.delete_button.setEnabled(False)

    def item_changed(self, item):
        """Показываем кнопку сохранения при изменении данных"""
        if item is not None and item.column() > 0:  # Игнорируем первый столбец (ID)
            self.save_button.setEnabled(True)

    def add_record(self):
        """Открыть окно для добавления новой записи."""
        if not self.current_table:
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу для добавления записи.")
            return
    
        # Получение списка колонок таблицы из базы данных
        try:
            columns = self.db_controller.get_table_columns(self.current_table)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить список колонок: {e}")
            return
    
        if not columns:
            QMessageBox.warning(self, "Ошибка", "Таблица не содержит колонок.")
            return
    
        # Открытие диалогового окна
        dialog = AddRecordDialog(columns, self.db_controller, self.current_table, self)
        if dialog.exec():
            self.load_data()  # Перезагрузка данных

    def delete_record(self):
        """Удаление записи из таблицы"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        reply = QMessageBox.question(
            self, "Подтверждение", "Вы уверены, что хотите удалить эту запись?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                id_value = self.table.item(current_row, 0).text()
                delete_query = f"DELETE FROM {self.current_table} WHERE id = ?"
                print(delete_query)
                print(id_value)
                self.db_controller.execute_query(delete_query, (id_value,))
                #self.db_controller.connection.commit()
                self.load_data()  # Обновляем таблицу
                QMessageBox.information(self, "Успех", "Запись успешно удалена.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить запись: {e}")

    def save_changes(self):
        """Сохранение изменений записи"""
        current_row = self.table.currentRow()
        if current_row < 0:
            return

        try:
            columns = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            values = [self.table.item(current_row, i).text() for i in range(self.table.columnCount())]
            id_value = values[0]
            update_query = f"UPDATE {self.current_table} SET " + ", ".join(f"{col} = ?" for col in columns[1:]) + " WHERE id = ?"
            self.db_controller.execute_query(update_query, tuple(values[1:] + [id_value]))
            self.db_controller.connection.commit()
            self.save_button.setEnabled(False)
            QMessageBox.information(self, "Успех", "Изменения успешно сохранены.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить изменения: {e}")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = DBController(server="localhost, 1433", database="JamStation", username="sa", password="YourStrong!Passw0rd")
    login = LoginWindow(controller)
    login.show()
    sys.exit(app.exec())