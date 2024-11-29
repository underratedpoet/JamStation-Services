import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QPushButton, QWidget, QMessageBox, QLabel, QComboBox, QHBoxLayout, QLineEdit, QDialog, QFormLayout, QTabWidget
)
from PyQt6.QtCore import Qt
from controller import DBController

from forms.app_add_row import AddRecordDialog
from forms.app_filter import FindRecordsDialog
from forms.app_report import ReportWindow

class MainWindow(QMainWindow):
    def __init__(self, db_controller: DBController):
        super().__init__()
        self.db_controller = db_controller

        self.current_offset = 0
        self.limit = 10
        self.column_filters = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Редактирование таблицы")
        self.setGeometry(200, 200, 800, 600)

        # Создание виджета вкладок
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        # Первая вкладка
        self.tab1 = QWidget()
        self.tab_widget.addTab(self.tab1, "Учет")

        # Вторая и третья пустые вкладки
        self.tab2 = QWidget()
        self.tab_widget.addTab(self.tab2, "Отчеты")

        #self.tab3 = QWidget()
        #self.tab_widget.addTab(self.tab3, "Вкладка 3")

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

        self.find_button = QPushButton("Фильтры", self.tab1)
        self.find_button.clicked.connect(self.find_records)

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
        layout.addWidget(self.find_button)

        self.tab1.setLayout(layout)

        self.status_report_button = QPushButton("Отчет о состоянии оборудования", self.tab2)
        self.status_report_button.clicked.connect(self.open_report)

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
        self.column_filters = None
        self.load_data()

    def load_data(self):
        """Загрузка данных из БД в таблицу"""
        try:
            if not self.current_table:
                return

            # Получение данных
            data = self.db_controller.paginate_table(self.current_table, self.current_offset, self.limit, filters=self.column_filters)
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

    def find_records(self):
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
        dialog = FindRecordsDialog(columns, self.db_controller, self.current_table, self)
        if dialog.exec():
            print(self.column_filters)
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

    def open_report(self):
        # Открытие диалогового окна
        dialog = ReportWindow(self.db_controller, self)
        if dialog.exec():
            QMessageBox.information(self, "Успех", "Сохранено")
