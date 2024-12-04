from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox

from utils.controller import DBController
from forms.report_form import ReportWindow

class ReportTab(QWidget):
    def __init__(self, db_controller: DBController):
        super().__init__()
        self.db_controller = db_controller

        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        self.setLayout(layout)        

        self.status_report_button = QPushButton("Отчет о состоянии оборудования")
        self.status_report_button.clicked.connect(self.open_report)

        layout.addWidget(self.status_report_button)

    def open_report(self):
        # Открытие диалогового окна
        dialog = ReportWindow(self.db_controller, self)
        if dialog.exec():
            QMessageBox.information(self, "Успех", "Сохранено")