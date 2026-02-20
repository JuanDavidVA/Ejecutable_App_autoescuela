from PyQt6.QtWidgets import QMainWindow, QTableWidget, QTabWidget, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt


class MainWindowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Driving Exams")
        self.resize(900, 600)

        self.table = QTableWidget()
        self.tabs = QTabWidget()

        table_page = QWidget()
        table_layout = QVBoxLayout(table_page)
        table_layout.addWidget(self.table)
        self.tabs.addTab(table_page, "Tabla")

        self.chart_page = QWidget()
        self.chart_layout = QVBoxLayout(self.chart_page)
        self.chart_placeholder = QLabel("Aplica filtros para ver el gráfico")
        self.chart_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.chart_layout.addWidget(self.chart_placeholder)
        self.tabs.addTab(self.chart_page, "Gráfico")

        self.setCentralWidget(self.tabs)
