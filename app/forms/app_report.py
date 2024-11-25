import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QWidget, QMessageBox, QLabel, QComboBox, QHBoxLayout, QLineEdit, QDialog, QFormLayout, QTabWidget, QTextEdit, QFileDialog
from PyQt6.QtCore import Qt
from controller import DBController
from forms.documents import save_report_to_docx

class ReportWindow(QDialog):
    def __init__(self, db_controller: DBController, parent=None):
        super().__init__()
        self.setWindowTitle("Отчет о состоянии оборудования")
        self.setFixedSize(400, 300)
        self.db_controller = db_controller

        # UI компоненты
        self.eq_label = QLabel("Оборудование:", self)
        self.eq_data_label = QLabel("", self)

        self.checks_label = QLabel("Проверки:", self)
        self.checks_data_label = QLabel("", self)

        self.stats_label = QLabel("Сводная статистика:", self)
        self.stats_data_label = QLabel("", self)

        self.comments_label = QLabel("Комментарии:", self)
        self.comments_text_edit = QTextEdit(self)

        # Layout
        self.layout = QFormLayout(self)

        self.layout.addRow(self.eq_label)
        self.layout.addRow(self.eq_data_label)
        self.layout.addRow(self.checks_label)
        self.layout.addRow(self.checks_data_label)
        self.layout.addRow(self.stats_label)
        self.layout.addRow(self.stats_data_label)
        self.layout.addRow(self.comments_label)
        self.layout.addRow(self.comments_text_edit)

        # Кнопки сохранения и отмены
        self.save_button = QPushButton("Сохранить отчет", self)
        self.save_button.clicked.connect(self.save_report)
        self.layout.addRow(self.save_button)

        self.cancel_button = QPushButton("Отмена", self)
        self.cancel_button.clicked.connect(self.reject)
        self.layout.addRow(self.cancel_button)

        self.get_data()

    def get_data(self):
        try:
            equipment_data = self.db_controller.execute_query("SELECT * FROM Equipment")
            checks_data = self.db_controller.execute_query("SELECT * FROM Checks")

            self.eq_data_label.setText("\n".join([str(row) for row in equipment_data]))
            self.checks_data_label.setText("\n".join([str(row) for row in checks_data]))

            # Пример сводной статистики
            total_equipment = len(equipment_data)
            total_checks = len(checks_data)
            self.stats_data_label.setText(f"Всего оборудования: {total_equipment}\nВсего проверок: {total_checks}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось получить данные: {e}")

    def save_report(self):
        equipment_data = self.eq_data_label.text()
        checks_data = self.checks_data_label.text()
        stats_data = self.stats_data_label.text()
        comments = self.comments_text_edit.toPlainText()

        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить отчет", "", "Word Documents (*.docx);;All Files (*)")
        if file_path:
            try:
                save_report_to_docx(equipment_data, checks_data, stats_data, comments, file_path)
                QMessageBox.information(self, "Успех", "Отчет успешно сохранен")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить отчет: {e}")