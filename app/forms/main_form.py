from PyQt6.QtWidgets import QMainWindow, QTabWidget, QMessageBox
from PyQt6.QtGui import QAction

from utils.controller import DBController
from widgets.edit_tab import EditTab
from widgets.report_tab import ReportTab
from widgets.schedule_tab import ScheduleTab
from widgets.accounting_tab import EquipmentInstrumentsTab
from widgets.receipt_tab import ReceiptTab
from widgets.clients_tab import ClientPenaltiesTab

class MainWindow(QMainWindow):
    def __init__(self, db_controller: DBController, employee_id):
        super().__init__()
        self.db_controller = db_controller
        self.employee_id = employee_id
        self.location_id = self.db_controller.select(["location_id"], "Employees", employee_id)[0]
        self.current_offset = 0
        self.limit = 10
        self.column_filters = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("JamStation")
        self.setGeometry(200, 200, 800, 600)

        # Добавление панели инструментов
        toolbar = self.addToolBar("Основные действия")
        refresh_action = QAction("Обновить", self)
        refresh_action.triggered.connect(self.refresh_tabs)
        toolbar.addAction(refresh_action)

        # Создание виджета вкладок
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        self.load_tabs()

    def load_tabs(self):
        """Загружает вкладки в виджет."""
        self.tab_widget.clear()  # Очищаем все текущие вкладки

        emp_role: str = self.db_controller.select(["role"], "Employees", self.employee_id)[0]
        print(emp_role)
        if emp_role.lower() == "manager":
            self.edit_tab = EditTab(self.db_controller)
            self.tab_widget.addTab(self.edit_tab, "Прямое редактирование")

        else:
            self.accounting_tab = EquipmentInstrumentsTab(self.db_controller, self.employee_id, self.location_id)
            self.tab_widget.addTab(self.accounting_tab, "Оборудование и инструменты")

            self.schedule_tab = ScheduleTab(self.db_controller, self.location_id)
            self.tab_widget.addTab(self.schedule_tab, "Расписание")

            self.receipt_tab = ReceiptTab(self.db_controller, self.employee_id)
            self.tab_widget.addTab(self.receipt_tab, "Чеки")

            self.clients_tab = ClientPenaltiesTab(location_id=self.location_id, db_controller=self.db_controller)
            self.tab_widget.addTab(self.clients_tab, "Клиенты")

            self.report_tab = ReportTab(self.db_controller, self.employee_id)
            self.tab_widget.addTab(self.report_tab, "Отчеты")

    def refresh_tabs(self):
        """Метод для обновления всех вкладок."""
        self.load_tabs()
        QMessageBox.information(self, "Обновление", "Вкладки обновлены.")

