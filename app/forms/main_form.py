from PyQt6.QtWidgets import QMainWindow, QTabWidget

from utils.controller import DBController
from widgets.edit_tab import EditTab
from widgets.report_tab import ReportTab
from widgets.schedule_tab import ScheduleTab
from widgets.accounting_tab import EquipmentInstrumentsTab
from widgets.receipt_tab import ReceiptTab


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

        # Создание виджета вкладок
        self.tab_widget = QTabWidget(self)
        self.setCentralWidget(self.tab_widget)

        self.edit_tab = EditTab(self.db_controller)
        self.tab_widget.addTab(self.edit_tab, "Прямое редактирование")

        self.report_tab = ReportTab(self.db_controller)
        self.tab_widget.addTab(self.report_tab, "Отчеты")

        self.accounting_tab = EquipmentInstrumentsTab(self.db_controller, self.employee_id, self.location_id)
        self.tab_widget.addTab(self.accounting_tab, "Оборудование и инструменты")
        
        self.report_tab = ScheduleTab(self.db_controller, self.location_id)
        self.tab_widget.addTab(self.report_tab, "Расписание")

        self.receipt_tab = ReceiptTab(self.db_controller, self.employee_id)
        self.tab_widget.addTab(self.receipt_tab, "Чеки")

