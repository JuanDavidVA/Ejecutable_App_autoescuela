# main.py
import sys
from PyQt6.QtWidgets import QApplication
from driving_statistics.mainc import MainController  # si MainController está en otro archivo
from driving_statistics.services.database import init_database

def main():
    init_database()
    app = QApplication(sys.argv)
    win = MainController()
    win.show()
    sys.exit(app.exec())

# Permite ejecutar directamente con python main.py
if __name__ == "__main__":
    main()