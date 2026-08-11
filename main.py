import sys

from pathlib import Path

from PySide6.QtGui import QPixmap

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QStackedWidget,
)

from PySide6.QtCore import Qt

from guipages.dashboard_page import DashboardPage
from guipages.actions_page import ActionsPage
from guipages.prospect_page import ProspectPage
from guipages.report_page import ReportPage
from guipages.settings_page import SettingsPage


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("CYPET Sales Assistant")
        self.resize(1400, 850)

        self.build_ui()

    def build_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setFixedWidth(260)

        sidebar.setStyleSheet("""
            QFrame {
                background: #1F2937;
                border: none;
            }

            QPushButton {
                background: transparent;
                color: #E5E7EB;
                border: none;
                border-radius: 8px;
                padding: 11px 14px;
                text-align: left;
                font-size: 10pt;
            }

            QPushButton:hover {
                background: #374151;
            }

            QPushButton:checked {
                background: #00A3E0;
                color: white;
                font-weight: 600;
            }
        """)

        left = QVBoxLayout(sidebar)
        left.setContentsMargins(15, 20, 15, 20)
        left.setSpacing(8)

        # Official CYPET logo from the project assets folder.
        # We deliberately use the original asset instead of recreating the
        # logo with text/CSS.
        logo = QLabel()
        logo.setObjectName("CypetLogo")
        logo.setAlignment(Qt.AlignCenter)
        logo.setMinimumHeight(82)
        logo.setMaximumHeight(115)
        logo.setStyleSheet("""
            QLabel#CypetLogo {
                padding: 8px 4px 12px 4px;
                background: transparent;
            }
        """)

        assets_dir = Path(__file__).resolve().parent / "assets"
        logo_candidates = sorted(
            assets_dir.glob("logo_cypet.*")
        )

        if logo_candidates:
            pixmap = QPixmap(str(logo_candidates[0]))
            if not pixmap.isNull():
                logo.setPixmap(
                    pixmap.scaled(
                        205,
                        95,
                        Qt.KeepAspectRatio,
                        Qt.SmoothTransformation,
                    )
                )
                logo.setToolTip("CYPET")
            else:
                logo.setText("CYPET")
        else:
            # Safe fallback only if the official asset is missing.
            logo.setText("CYPET")
            logo.setStyleSheet("""
                QLabel#CypetLogo {
                    color: white;
                    font-size: 22px;
                    font-weight: bold;
                    padding: 20px;
                    background: transparent;
                }
            """)

        left.addWidget(logo)

        self.btn_sync = QPushButton("🔄  Sincronizza Outlook")
        self.btn_dashboard = QPushButton("📊  Dashboard")
        self.btn_actions = QPushButton("⚡  Actions")
        self.btn_prospect = QPushButton("👥  Prospect")
        self.btn_report = QPushButton("📈  Report")
        self.btn_settings = QPushButton("⚙  Impostazioni")
        self.btn_exit = QPushButton("Esci")

        buttons = [
            self.btn_dashboard,
            self.btn_actions,
            self.btn_prospect,
            self.btn_report,
            self.btn_settings,
        ]

        self.btn_sync.setCursor(Qt.PointingHandCursor)
        left.addWidget(self.btn_sync)

        for button in buttons:
            button.setCursor(Qt.PointingHandCursor)
            button.setCheckable(True)
            left.addWidget(button)

        left.addStretch()

        self.btn_exit.setCursor(Qt.PointingHandCursor)
        left.addWidget(self.btn_exit)

        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(70)
        header.setStyleSheet("""
            QFrame {
                background: white;
                border-bottom: 1px solid #DCE3EA;
            }

            QLabel {
                color: #1F2937;
                font-size: 22px;
                font-weight: 700;
            }
        """)

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)

        self.page_title = QLabel("Dashboard")
        header_layout.addWidget(self.page_title)
        header_layout.addStretch()

        right.addWidget(header)

        self.pages = QStackedWidget()

        self.dashboard = DashboardPage()
        self.actions = ActionsPage()
        self.prospect = ProspectPage()
        self.report = ReportPage()
        self.settings = SettingsPage()

        self.pages.addWidget(self.dashboard)
        self.pages.addWidget(self.actions)
        self.pages.addWidget(self.prospect)
        self.pages.addWidget(self.report)
        self.pages.addWidget(self.settings)

        right.addWidget(self.pages, 1)

        layout.addWidget(sidebar)
        layout.addLayout(right, 1)

        self.btn_dashboard.clicked.connect(
            lambda: self.show_page(0, "Dashboard", self.btn_dashboard)
        )
        self.btn_actions.clicked.connect(
            lambda: self.show_page(1, "Actions", self.btn_actions)
        )
        self.btn_prospect.clicked.connect(
            lambda: self.show_page(2, "Prospect", self.btn_prospect)
        )
        self.btn_report.clicked.connect(
            lambda: self.show_page(3, "Report", self.btn_report)
        )
        self.btn_settings.clicked.connect(
            lambda: self.show_page(4, "Impostazioni", self.btn_settings)
        )

        self.btn_exit.clicked.connect(self.close)
        self.btn_sync.clicked.connect(self.sync_outlook)

        self.show_page(0, "Dashboard", self.btn_dashboard)

        # Run the campaign scheduler once at application startup.
        # This is independent from Outlook synchronization and never sends
        # an email. It only creates due campaign actions.
        self.run_campaign_execution_startup()

    def run_campaign_execution_startup(self):
        print("CAMPAIGN EXECUTION START")

        try:
            from modules.database import Database
            from modules.campaign_execution_engine import CampaignExecutionEngine

            db = Database()
            engine = CampaignExecutionEngine(db)
            result = engine.run()

            print(
                f"Campaign execution completed. "
                f"Due communications: {result['checked']} | "
                f"New campaign actions: {result['actions_generated']}"
            )

            self.actions.refresh_data()
            self.dashboard.refresh_data()

        except Exception as exc:
            print("CAMPAIGN EXECUTION ERROR")
            print(exc)

    def show_page(self, index, title, button):

        self.pages.setCurrentIndex(index)
        self.page_title.setText(title)

        buttons = [
            self.btn_dashboard,
            self.btn_actions,
            self.btn_prospect,
            self.btn_report,
            self.btn_settings,
        ]

        for item in buttons:
            item.setChecked(item is button)

        current_page = self.pages.currentWidget()

        if hasattr(current_page, "refresh_data"):
            current_page.refresh_data()

    def sync_outlook(self):

        print("OUTLOOK SYNC START")

        try:
            from modules.database import Database
            from modules.outlook_inbox import OutlookInboxReader
            from modules.automation_engine import AutomationEngine
            from modules.campaign_execution_engine import CampaignExecutionEngine

            db = Database()

            imported = OutlookInboxReader.sync_sent_to_database(
                db,
                number=100
            )

            print(f"Sent emails imported: {imported}")

            engine = AutomationEngine(db)

            result = engine.run(inbox_limit=100)

            print(
                f"Automation completed. "
                f"New actions: {result['actions_generated']}"
            )

            campaign_engine = CampaignExecutionEngine(db)
            campaign_result = campaign_engine.run()

            print(
                f"Campaign execution completed. "
                f"Due communications: {campaign_result['checked']} | "
                f"New campaign actions: {campaign_result['actions_generated']}"
            )

            self.dashboard.refresh_data()
            self.actions.refresh_data()
            self.prospect.refresh_data()
            self.report.refresh_data()

            print("OUTLOOK SYNC COMPLETE")

        except Exception as exc:
            print("OUTLOOK SYNC ERROR")
            print(exc)


# ---------------------------------------------------------
# APPLICATION ENTRY POINT
# ---------------------------------------------------------

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
