from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QFrame
)

from modules.database import Database


class DashboardPage(QWidget):

    def __init__(self):

        super().__init__()

        self.db = Database()

        self.build_ui()

    # ---------------------------------------------------------

    def build_ui(self):

        main = QVBoxLayout(self)

        title = QLabel("Dashboard")

        title.setStyleSheet("""
            font-size:30px;
            font-weight:bold;
            padding-bottom:15px;
        """)

        main.addWidget(title)

        cards = QHBoxLayout()

        cards.addWidget(
            self.create_card(
                "📧",
                "Email archiviate",
                str(self.db.total_emails())
            )
        )

        cards.addWidget(
            self.create_card(
                "🏢",
                "Aziende",
                str(self.db.total_domains())
            )
        )

        cards.addWidget(
            self.create_card(
                "📅",
                "Ultimo contatto",
                str(self.db.last_email())
            )
        )

        cards.addWidget(
            self.create_card(
                "🔄",
                "Stato",
                "READY"
            )
        )

        main.addLayout(cards)

        placeholder = QFrame()

        placeholder.setMinimumHeight(320)

        placeholder.setStyleSheet("""
            QFrame{
                background:white;
                border:1px solid #d8d8d8;
                border-radius:10px;
            }
        """)

        box = QVBoxLayout()

        lbl = QLabel("Area grafici e statistiche")

        lbl.setStyleSheet("""
            font-size:18px;
            color:#666;
        """)

        box.addWidget(lbl)

        box.addStretch()

        placeholder.setLayout(box)

        main.addWidget(placeholder)

        main.addStretch()

    # ---------------------------------------------------------

    def create_card(self, icon, title, value):

        card = QFrame()

        card.setMinimumHeight(110)

        card.setStyleSheet("""
            QFrame{
                background:white;
                border:1px solid #dcdcdc;
                border-radius:12px;
            }
        """)

        layout = QVBoxLayout(card)

        i = QLabel(icon)
        i.setStyleSheet("font-size:28px;")

        t = QLabel(title)
        t.setStyleSheet("font-size:13px;color:#666;")

        v = QLabel(value)
        v.setStyleSheet("""
            font-size:24px;
            font-weight:bold;
        """)

        layout.addWidget(i)
        layout.addWidget(t)
        layout.addWidget(v)

        return card