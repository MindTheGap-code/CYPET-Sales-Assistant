from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QGridLayout,
)

from modules.database import Database


class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        self.db = Database()

        self.setStyleSheet("""
            QFrame#Card,
            QFrame#Panel {
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

            QLabel#ItemTitle {
                color: #1F2937;
                font-size: 10pt;
                font-weight: 600;
            }

            QLabel#ItemMeta {
                color: #6B7280;
                font-size: 9pt;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(18)

        cards = QHBoxLayout()
        cards.setSpacing(16)

        self.email_card = self.card(
            "Emails",
            str(self.db.total_emails()),
            "Imported messages",
        )

        self.domain_card = self.card(
            "Companies",
            str(self.db.total_domains()),
            "Known domains",
        )

        last_email = self.db.last_email()

        self.last_card = self.card(
            "Last contact",
            str(last_email)[:10] if last_email else "-",
            "Latest email",
        )

        self.status_card = self.card(
            "Status",
            "READY",
            "CYPET Sales Assistant",
        )

        cards.addWidget(self.email_card)
        cards.addWidget(self.domain_card)
        cards.addWidget(self.last_card)
        cards.addWidget(self.status_card)

        root.addLayout(cards)

        grid = QGridLayout()
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)

        self.recent_panel = self.panel("Recent emails")
        self.companies_panel = self.panel("Latest companies")
        self.activity_panel = self.panel("Activity")

        grid.addWidget(self.recent_panel, 0, 0)
        grid.addWidget(self.companies_panel, 0, 1)
        grid.addWidget(self.activity_panel, 1, 0, 1, 2)

        root.addLayout(grid)

        self.refresh()

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

        frame.value_label = value_label

        return frame

    def panel(self, title):
        frame = QFrame()
        frame.setObjectName("Panel")
        frame.setMinimumHeight(170)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        title_label = QLabel(title)
        title_label.setObjectName("PanelTitle")

        body = QVBoxLayout()
        body.setSpacing(6)

        layout.addWidget(title_label)
        layout.addLayout(body)
        layout.addStretch()

        frame.body = body

        return frame

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)

            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

            child_layout = item.layout()
            if child_layout is not None:
                self._clear_layout(child_layout)

    def _add_item(self, layout, title, meta):
        item = QFrame()
        item_layout = QVBoxLayout(item)
        item_layout.setContentsMargins(0, 0, 0, 0)
        item_layout.setSpacing(1)

        title_label = QLabel(title)
        title_label.setObjectName("ItemTitle")

        meta_label = QLabel(meta)
        meta_label.setObjectName("ItemMeta")

        item_layout.addWidget(title_label)
        item_layout.addWidget(meta_label)

        layout.addWidget(item)

    def refresh(self):
        total_emails = self.db.total_emails()
        total_domains = self.db.total_domains()
        last_email = self.db.last_email()

        self.email_card.value_label.setText(str(total_emails))
        self.domain_card.value_label.setText(str(total_domains))
        self.last_card.value_label.setText(
            str(last_email)[:10] if last_email else "-"
        )

        self._clear_layout(self.recent_panel.body)

        recent = self.db.get_recent_emails(5)

        if recent:
            for row in recent:
                subject = row["subject"] or "(No subject)"
                recipient = row["recipient_email"] or row["recipient_name"] or "-"
                self._add_item(
                    self.recent_panel.body,
                    subject,
                    f"{recipient} · {str(row['sent_date'])[:16]}",
                )
        else:
            self._add_item(
                self.recent_panel.body,
                "No recent emails",
                "No email data available",
            )

        self._clear_layout(self.companies_panel.body)

        companies = self.db.get_domains(5)

        if companies:
            for row in companies:
                self._add_item(
                    self.companies_panel.body,
                    row["domain"],
                    f"{row['total']} contacts · last {str(row['last_contact'])[:10]}",
                )
        else:
            self._add_item(
                self.companies_panel.body,
                "No companies",
                "No company data available",
            )

        self._clear_layout(self.activity_panel.body)

        self._add_item(
            self.activity_panel.body,
            f"{total_emails} emails indexed",
            f"{total_domains} companies identified",
        )

    def refresh_data(self):
        self.refresh()
