from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox

from utils.controller import DBController
from forms.report_form import ReportWindow, StandartReportWindow

class ReportTab(QWidget):
    def __init__(self, db_controller: DBController, emp_id):
        super().__init__()
        self.db_controller = db_controller
        self.emp_id = emp_id

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)        

        self.status_report_button = QPushButton("Отчет о состоянии оборудования")
        self.status_report_button.clicked.connect(self.open_report)

        layout.addWidget(self.status_report_button)

        self.standart_report_button = QPushButton("Стандартный отчет")
        self.standart_report_button.clicked.connect(self.open_standart_report)

        layout.addWidget(self.standart_report_button)

    def open_report(self):
        # Открытие диалогового окна
        try:
            self.db_controller.select(["id"], "Checks")
            dialog = ReportWindow(self.db_controller, self)
            if dialog.exec():
                QMessageBox.information(self, "Успех", "Сохранено")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить данные: {e}")

    def open_standart_report(self):
        # Открытие диалогового окна
        try:
            #self.db_controller.select(["id"], "Checks")
            dialog = StandartReportWindow(self.db_controller, self, self.emp_id)
        except Exception as e:
            #QMessageBox.critical(self, "Ошибка", f"Не удалось получить данные: {e}")
            return
        if dialog.exec():
            QMessageBox.information(self, "Успех", "Сохранено")