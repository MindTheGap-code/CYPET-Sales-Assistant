from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QPushButton, QHBoxLayout


class Sidebar(QFrame):
    def __init__(self):
        super().__init__()

        self.setObjectName("Sidebar")
        self.setFixedWidth(250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 20, 18, 20)
        layout.setSpacing(8)

        logo = QLabel()
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)

        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo_cypet.png"
        pixmap = QPixmap(str(logo_path))

        if not pixmap.isNull():
            logo.setPixmap(
                pixmap.scaledToWidth(
                    180,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            logo_title = QLabel("CYPET")
            logo_title.setObjectName("LogoTitle")
            logo_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

            logo_subtitle = QLabel("Sales Assistant")
            logo_subtitle.setObjectName("LogoSubtitle")
            logo_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

            logo_box = QVBoxLayout()
            logo_box.setSpacing(2)
            logo_box.addWidget(logo_title)
            logo_box.addWidget(logo_subtitle)

            logo_frame = QFrame()
            logo_frame.setLayout(logo_box)
            layout.addWidget(logo_frame)

            layout.addSpacing(20)
        if not pixmap.isNull():
            layout.addWidget(logo)
            layout.addSpacing(20)

        self.buttons = {}

        items = [
            ("dashboard", "Dashboard"),
            ("outlook", "Outlook"),
            ("prospect", "Prospect"),
            ("report", "Report"),
            ("settings", "Settings"),
        ]

        for key, text in items:
            button = QPushButton(text)
            button.setObjectName("MenuButton")
            button.setCheckable(True)
            button.setMinimumHeight(44)
            button.setCursor(Qt.CursorShape.PointingHandCursor)

            self.buttons[key] = button
            layout.addWidget(button)

        layout.addStretch()

        user_frame = QFrame()
        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(4, 10, 4, 0)
        user_layout.setSpacing(10)

        avatar = QLabel("SR")
        avatar.setFixedSize(38, 38)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(
            "background:#00A3E0;"
            "color:white;"
            "border-radius:19px;"
            "font-weight:700;"
        )

        user_info = QVBoxLayout()
        user_info.setSpacing(1)

        name = QLabel("Sandro Rasi")
        name.setStyleSheet("color:white;font-weight:600;")

        role = QLabel("Sales Manager")
        role.setObjectName("LogoSubtitle")

        user_info.addWidget(name)
        user_info.addWidget(role)

        user_layout.addWidget(avatar)
        user_layout.addLayout(user_info)

        layout.addWidget(user_frame)

    def set_active(self, key):
        for name, button in self.buttons.items():
            button.setChecked(name == key)
