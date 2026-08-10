from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QToolButton


class TopBar(QFrame):
    def __init__(self):
        super().__init__()

        self.setObjectName("TopBar")
        self.setFixedHeight(76)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(12)

        self.title = QLabel("Dashboard")
        self.title.setObjectName("PageTitle")
        layout.addWidget(self.title)

        layout.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search companies, contacts, emails...")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedSize(330, 38)
        self.search.setStyleSheet(
            "QLineEdit {"
            "background:#F7F9FC;"
            "border:1px solid #DCE3EA;"
            "border-radius:19px;"
            "padding:0 14px;"
            "color:#1F2937;"
            "}"
            "QLineEdit:focus {"
            "border:1px solid #00A3E0;"
            "}"
        )
        layout.addWidget(self.search)

        self.notification = QToolButton()
        self.notification.setText("🔔")
        self.notification.setFixedSize(38, 38)
        self.notification.setToolTip("Notifications")
        layout.addWidget(self.notification)

        self.outlook = QLabel("● Outlook")
        self.outlook.setObjectName("Secondary")
        layout.addWidget(self.outlook)

        self.sync = QLabel("Last sync: --:--")
        self.sync.setObjectName("Secondary")
        layout.addWidget(self.sync)

        self.user = QLabel("Sandro Rasi")
        self.user.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.user.setMinimumWidth(110)
        self.user.setFixedHeight(38)
        self.user.setStyleSheet(
            "QLabel {"
            "background:#00A3E0;"
            "color:white;"
            "border-radius:19px;"
            "padding:0 14px;"
            "font-weight:600;"
            "}"
        )
        layout.addWidget(self.user)

    def set_title(self, text):
        self.title.setText(text)

    def set_sync(self, text):
        self.sync.setText(f"Last sync: {text}")

    def set_outlook(self, connected):
        self.outlook.setText("● Outlook")
        self.outlook.setStyleSheet(
            "color:#16A34A;font-weight:600;"
            if connected else
            "color:#DC2626;font-weight:600;"
        )

    def set_user(self, name):
        self.user.setText(name)
