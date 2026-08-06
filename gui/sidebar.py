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

        self.subtitle = QLabel("Sales Assistant
v1.0")
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
            ("report", "📈  Report"),
            ("settings", "⚙  Settings"),
        ]

        for key, text in items:
            b = QPushButton(text)
            b.setObjectName("MenuButton")
            b.setCheckable(True)
            b.setMinimumHeight(42)
            self.buttons[key] = b
            layout.addWidget(b)

        layout.addStretch()

        self.exit_button = QPushButton("⏻  Exit")
        self.exit_button.setMinimumHeight(42)
        layout.addWidget(self.exit_button)

    def set_active(self, key):
        for name, button in self.buttons.items():
            button.setChecked(name == key)
