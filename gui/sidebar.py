from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt


class Sidebar(QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("Sidebar")
        self.setFixedWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 20, 16, 16)
        layout.setSpacing(8)

        self.logo = QLabel("CYPET")
        self.logo.setObjectName("LogoTitle")
        self.logo.setAlignment(Qt.AlignCenter)

        self.subtitle = QLabel("Sales Assistant\nv1.0")
        self.subtitle.setObjectName("LogoSubtitle")
        self.subtitle.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.logo)
        layout.addWidget(self.subtitle)
        layout.addSpacing(20)

        self.buttons = {}

        items = [
            ("dashboard", "📊  Dashboard"),
            ("outlook", "📧  Outlook"),
            ("prospect", "👥  Prospect"),
            ("campaign", "📣  Campaigns"),
            ("report", "📈  Report"),
            ("settings", "⚙  Settings"),
        ]

        for key, text in items:
            button = QPushButton(text)
            button.setObjectName("MenuButton")
            button.setCheckable(True)
            button.setMinimumHeight(42)
            button.setCursor(Qt.PointingHandCursor)
            self.buttons[key] = button
            layout.addWidget(button)

        layout.addStretch()

        self.exit_button = QPushButton("⏻  Exit")
        self.exit_button.setMinimumHeight(42)
        self.exit_button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.exit_button)
        self.exit_button.clicked.connect(self._exit_application)

    def _exit_application(self):
        window = self.window()
        if window:
            window.close()

    def set_active(self, key):
        for name, button in self.buttons.items():
            button.setChecked(name == key)
