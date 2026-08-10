from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QGridLayout
from modules.database import Database


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        self.db = Database()

        self.setStyleSheet("""
            QFrame#Card, QFrame#Panel {
                background: white;
                border: 1px solid #DCE3EA;
                border-radius: 12px;
            }

            QLabel#CardTitle {
                color: #6B7280;
                font-size: 10pt;
            }

            QLabel#Value {
                color: #1F2937;
                font-size: 24px;
                font-weight: 700;
            }

            QLabel#PanelTitle {
                color: #374151;
                font-size: 11pt;
                font-weight: 700;
            }

            QLabel#PanelText {
                color: #6B7280;
                font-size: 10pt;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(18)

        cards = QHBoxLayout()
        cards.setSpacing(16)

        cards.addWidget(self.card(
            "Emails",
            str(self.db.total_emails()),
            "Imported messages"
        ))

        cards.addWidget(self.card(
            "Companies",
            str(self.db.total_domains()),
            "Known domains"
        ))

        last_email = self.db.last_email()
        cards.addWidget(self.card(
            "Last contact",
            str(last_email)[:10] if last_email else "-",
            "Latest email"
        ))

        cards.addWidget(self.card(
            "Status",
            "READY",
            "CYPET Sales Assistant"
        ))

        root.addLayout(cards)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)

        grid.addWidget(
            self.panel("Recent emails", "No recent emails available."),
            0, 0
        )

        grid.addWidget(
            self.panel("Latest companies", "No companies available."),
            0, 1
        )

        grid.addWidget(
            self.panel("Activity", "Activity will appear here."),
            1, 0, 1, 2
        )

        root.addLayout(grid)

    def card(self, title, value, caption):
        frame = QFrame()
        frame.setObjectName("Card")
        frame.setMinimumHeight(118)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)

        title_label = QLabel(title)
        title_label.setObjectName("CardTitle")

        value_label = QLabel(value)
        value_label.setObjectName("Value")
        value_label.setAlignment(Qt.AlignCenter)

        caption_label = QLabel(caption)
        caption_label.setObjectName("PanelText")
        caption_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(value_label)
        layout.addWidget(caption_label)

        return frame

    def panel(self, title, text):
        frame = QFrame()
        frame.setObjectName("Panel")
        frame.setMinimumHeight(170)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(12)

        title_label = QLabel(title)
        title_label.setObjectName("PanelTitle")

        text_label = QLabel(text)
        text_label.setObjectName("PanelText")
        text_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(title_label)
        layout.addStretch()
        layout.addWidget(text_label)
        layout.addStretch()

        return frame
