from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QStackedWidget,
)
from gui.sidebar import Sidebar
from gui.topbar import TopBar
from guipages.dashboard_page import DashboardPage
from guipages.outlook_page import OutlookPage
from guipages.prospect_page import ProspectPage
from guipages.report_page import ReportPage
from guipages.settings_page import SettingsPage
from guipages.campaign_page import CampaignPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CYPET Sales Assistant")
        self.resize(1400, 850)
        self.setMinimumSize(1100, 700)
        self.build_ui()

    def build_ui(self):
        central = QWidget()
        central.setObjectName("CentralWidget")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.sidebar = Sidebar()
        main_layout.addWidget(self.sidebar)

        content = QWidget()
        content.setObjectName("ContentArea")

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.topbar = TopBar()
        content_layout.addWidget(self.topbar)

        self.pages = QStackedWidget()
        content_layout.addWidget(self.pages, 1)

        self.dashboard = DashboardPage()
        self.outlook = OutlookPage()
        self.prospect = ProspectPage()
        self.campaign = CampaignPage()
        self.report = ReportPage()
        self.settings = SettingsPage()

        self.pages.addWidget(self.dashboard)
        self.pages.addWidget(self.outlook)
        self.pages.addWidget(self.prospect)
        self.pages.addWidget(self.campaign)
        self.pages.addWidget(self.report)
        self.pages.addWidget(self.settings)

        main_layout.addWidget(content, 1)

        self._connect_navigation()
        self.show_page("dashboard")

    def _connect_navigation(self):
        self.sidebar.buttons["dashboard"].clicked.connect(
            lambda: self.show_page("dashboard")
        )
        self.sidebar.buttons["outlook"].clicked.connect(
            lambda: self.show_page("outlook")
        )
        self.sidebar.buttons["prospect"].clicked.connect(
            lambda: self.show_page("prospect")
        )
        self.sidebar.buttons["campaign"].clicked.connect(
            lambda: self.show_page("campaign")
        )
        self.sidebar.buttons["report"].clicked.connect(
            lambda: self.show_page("report")
        )
        self.sidebar.buttons["settings"].clicked.connect(
            lambda: self.show_page("settings")
        )

    def show_page(self, page_name):
        pages = {
            "dashboard": (self.dashboard, "Dashboard"),
            "outlook": (self.outlook, "Outlook"),
            "prospect": (self.prospect, "Prospect"),
            "campaign": (self.campaign, "Campaigns"),
            "report": (self.report, "Report"),
            "settings": (self.settings, "Settings"),
        }

        page, title = pages[page_name]
        self.pages.setCurrentWidget(page)
        self.topbar.set_title(title)
        self.sidebar.set_active(page_name)
