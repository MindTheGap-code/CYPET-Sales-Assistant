from PySide6.QtWidgets import QFrame
from PySide6.QtWidgets import QFrame
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout
)

from PySide6.QtCore import Qt

from guipages.dashboard_page import DashboardPage


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        self.setWindowTitle("CYPET Sales Assistant")

        self.resize(1400, 850)

        self.build_ui()

    # ---------------------------------------------------------

    def build_ui(self):

        central = QWidget()

        self.setCentralWidget(central)

        layout = QHBoxLayout()

        central.setLayout(layout)

        # =====================================================
        # MENU LATERALE
        # =====================================================

        sidebar = QFrame()

        logo = QLabel("CYPET\nSales Assistant")

        logo.setAlignment(Qt.AlignCenter)

        logo.setStyleSheet("""

            font-size:22px;
            font-weight:bold;
            padding:20px;

        """)

        left.addWidget(logo)

        self.btn_sync = QPushButton("🔄 Sincronizza Outlook")

        self.btn_dashboard = QPushButton("📊 Dashboard")

        self.btn_prospect = QPushButton("👥 Prospect")

        self.btn_report = QPushButton("📈 Report")

        self.btn_settings = QPushButton("⚙ Impostazioni")

        self.btn_exit = QPushButton("Esci")

        left.addWidget(self.btn_sync)

        left.addWidget(self.btn_dashboard)

        left.addWidget(self.btn_prospect)

        left.addWidget(self.btn_report)

        left.addWidget(self.btn_settings)

        left.addStretch()

        left.addWidget(self.btn_exit)

        # =====================================================
        # AREA CENTRALE
        # =====================================================

        right = QVBoxLayout()

        title = QLabel("Dashboard")

        title.setStyleSheet("""

            font-size:28px;
            font-weight:bold;

        """)

        right.addWidget(title)

        self.dashboard = DashboardPage()

        right.addWidget(self.dashboard)

        layout.addLayout(left, 1)

        layout.addLayout(right, 4)

        self.btn_exit.clicked.connect(self.close)