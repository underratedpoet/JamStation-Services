import sys
from PyQt6.QtWidgets import QApplication
from utils.controller import DBController

from forms.login_form import LoginWindow
#from forms.main_form import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    controller = DBController(server="localhost, 1433", database="JamStation", username="sa", password="YourStrong!Passw0rd")
    #main = MainWindow(controller)
    #main.show()
    login = LoginWindow(controller)
    login.show()
    sys.exit(app.exec())