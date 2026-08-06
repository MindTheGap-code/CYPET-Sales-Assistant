from PySide6.QtWidgets import (
    QMainWindow, QWidget, QFrame, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QStackedWidget
)
from PySide6.QtCore import Qt

from guipages.dashboard_page import DashboardPage
from guipages.outlook_page import OutlookPage
from guipages.prospect_page import ProspectPage
from guipages.report_page import ReportPage
from guipages.settings_page import SettingsPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CYPET Sales Assistant")
        self.resize(1400, 850)

        self.setStyleSheet("""
        QMainWindow{background:#f3f5f7;}
        QFrame#Sidebar{background:#1f2937;}
        QLabel#Logo{color:white;font-size:24px;font-weight:bold;padding:20px;}
        QLabel#Header{font-size:28px;font-weight:bold;padding:20px;color:#222;}
        QPushButton{
            background:transparent;
            color:white;
            border:none;
            text-align:left;
            padding:14px 20px;
            font-size:15px;
        }
        QPushButton:hover{background:#374151;}
        QPushButton:checked{
            background:#2563eb;
            font-weight:bold;
        }
        """)

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(240)

        left = QVBoxLayout(sidebar)
        left.setContentsMargins(0, 0, 0, 15)
        left.setSpacing(0)

        logo = QLabel("CYPET\nSales Assistant")
        logo.setObjectName("Logo")
        logo.setAlignment(Qt.AlignCenter)
        left.addWidget(logo)

        self.buttons = {}

        self.btn_dashboard = self._menu_button("📊 Dashboard")
        self.btn_outlook = self._menu_button("📧 Outlook")
        self.btn_prospect = self._menu_button("👥 Prospect")
        self.btn_report = self._menu_button("📈 Report")
        self.btn_settings = self._menu_button("⚙ Settings")

        for b in (
            self.btn_dashboard,
            self.btn_outlook,
            self.btn_prospect,
            self.btn_report,
            self.btn_settings,
        ):
            left.addWidget(b)

        left.addStretch()

        self.btn_exit = QPushButton("⏻ Exit")
        self.btn_exit.clicked.connect(self.close)
        left.addWidget(self.btn_exit)

        content = QWidget()
        right = QVBoxLayout(content)
        right.setContentsMargins(20, 10, 20, 20)

        self.header = QLabel("Dashboard")
        self.header.setObjectName("Header")
        right.addWidget(self.header)

        self.stack = QStackedWidget()
        self.stack.addWidget(DashboardPage())
        self.stack.addWidget(OutlookPage())
        self.stack.addWidget(ProspectPage())
        self.stack.addWidget(ReportPage())
        self.stack.addWidget(SettingsPage())

        right.addWidget(self.stack)

        root.addWidget(sidebar)
        root.addWidget(content)

        self.btn_dashboard.clicked.connect(lambda: self.show_page(0, "Dashboard", self.btn_dashboard))
        self.btn_outlook.clicked.connect(lambda: self.show_page(1, "Outlook", self.btn_outlook))
        self.btn_prospect.clicked.connect(lambda: self.show_page(2, "Prospect", self.btn_prospect))
        self.btn_report.clicked.connect(lambda: self.show_page(3, "Report", self.btn_report))
        self.btn_settings.clicked.connect(lambda: self.show_page(4, "Settings", self.btn_settings))

        self.show_page(0, "Dashboard", self.btn_dashboard)

    def _menu_button(self, text):
        button = QPushButton(text)
        button.setCheckable(True)
        self.buttons[text] = button
        return button

    def show_page(self, index, title, active_button):
        self.stack.setCurrentIndex(index)
        self.header.setText(title)
        for button in self.buttons.values():
            button.setChecked(button is active_button)
