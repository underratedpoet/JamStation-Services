import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QPushButton, QWidget, QMessageBox, QLabel, QComboBox, QHBoxLayout, QLineEdit, QDialog, QFormLayout, QTabWidget
)
from PyQt6.QtCore import Qt
from controller import DBController

from forms.app_main import MainWindow

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