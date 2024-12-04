from PyQt6.QtWidgets import QMainWindow, QTabWidget

from utils.controller import DBController
from widgets.edit_tab import EditTab
from widgets.report_tab import ReportTab
from widgets.schedule_tab import ScheduleTab


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

        self.edit_tab = EditTab(self.db_controller)
        self.tab_widget.addTab(self.edit_tab, "Прямое редактирование")

        self.report_tab = ReportTab(self.db_controller)
        self.tab_widget.addTab(self.report_tab, "Отчеты")
        
        self.report_tab = ScheduleTab(self.db_controller)
        self.tab_widget.addTab(self.report_tab, "Расписание")

