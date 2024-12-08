import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from utils.controller import DBController

from forms.login_form import LoginWindow
from forms.main_form import MainWindow


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("static/icons8-music-band-16.png"))
    controller = DBController(server="localhost, 1433", database="JamStation", username="sa", password="YourStrong!Passw0rd")
    main = MainWindow(controller, 2)
    main.show()
    #login = LoginWindow(controller)
    #login.show()
    sys.exit(app.exec())