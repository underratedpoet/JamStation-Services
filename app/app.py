import sys
from PyQt6.QtWidgets import QApplication
from controller import DBController

from forms.app_login import LoginWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = DBController(server="localhost, 1433", database="JamStation", username="sa", password="YourStrong!Passw0rd")
    login = LoginWindow(controller)
    login.show()
    sys.exit(app.exec())