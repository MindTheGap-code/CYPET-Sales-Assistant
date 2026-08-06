from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel
from PySide6.QtCore import Qt


class TopBar(QFrame):
    def __init__(self):
        super().__init__()

        self.setObjectName("TopBar")
        self.setFixedHeight(72)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(24, 12, 24, 12)
        layout.setSpacing(16)

        self.title = QLabel("Dashboard")
        self.title.setObjectName("PageTitle")

        layout.addWidget(self.title)
        layout.addStretch()

        self.outlook = QLabel("● Outlook Connected")
        self.outlook.setObjectName("Secondary")
        self.outlook.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.sync = QLabel("Last Sync: --:--")
        self.sync.setObjectName("Secondary")
        self.sync.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        self.user = QLabel("User")
        self.user.setObjectName("Secondary")
        self.user.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(self.outlook)
        layout.addSpacing(20)
        layout.addWidget(self.sync)
        layout.addSpacing(20)
        layout.addWidget(self.user)

    def set_title(self, text):
        self.title.setText(text)

    def set_user(self, text):
        self.user.setText(text)

    def set_sync(self, text):
        self.sync.setText(f"Last Sync: {text}")

    def set_outlook(self, connected):
        if connected:
            self.outlook.setText("● Outlook Connected")
        else:
            self.outlook.setText("● Outlook Disconnected")
