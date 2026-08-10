from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton


class OutlookPage(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
            QFrame#Header {
                background: white;
                border: 1px solid #DCE3EA;
                border-radius: 12px;
            }

            QLabel#Title {
                color: #1F2937;
                font-size: 20px;
                font-weight: 700;
            }

            QLabel#Subtitle {
                color: #6B7280;
                font-size: 10pt;
            }

            QLabel#Status {
                color: #16A34A;
                font-size: 10pt;
                font-weight: 600;
            }

            QPushButton#Action {
                background: #00A3E0;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 9px 16px;
                font-weight: 600;
            }

            QPushButton#Action:hover {
                background: #008FC4;
            }

            QFrame#Content {
                background: white;
                border: 1px solid #DCE3EA;
                border-radius: 12px;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(18)

        header = QFrame()
        header.setObjectName("Header")

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        title = QLabel("Outlook")
        title.setObjectName("Title")

        subtitle = QLabel("Email synchronization and connection status")
        subtitle.setObjectName("Subtitle")

        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)

        header_layout.addLayout(text_layout)
        header_layout.addStretch()

        self.status = QLabel("● Connected")
        self.status.setObjectName("Status")
        header_layout.addWidget(self.status)

        self.sync_button = QPushButton("Sync now")
        self.sync_button.setObjectName("Action")
        self.sync_button.setCursor(Qt.PointingHandCursor)
        header_layout.addWidget(self.sync_button)

        root.addWidget(header)

        content = QFrame()
        content.setObjectName("Content")

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(24, 24, 24, 24)

        message = QLabel(
            "Outlook synchronization is ready."
        )
        message.setObjectName("Subtitle")
        message.setAlignment(Qt.AlignCenter)

        content_layout.addStretch()
        content_layout.addWidget(message)
        content_layout.addStretch()

        root.addWidget(content)

    def set_connected(self, connected):
        if connected:
            self.status.setText("● Connected")
            self.status.setStyleSheet(
                "color:#16A34A;font-weight:600;"
            )
        else:
            self.status.setText("● Offline")
            self.status.setStyleSheet(
                "color:#DC2626;font-weight:600;"
            )
