from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

from modules.scanner import Scanner


class OutlookPage(QWidget):
    def __init__(self):
        super().__init__()

        self.scanner = Scanner()
        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.timeout.connect(self._restore_connected)

        self.setStyleSheet("""
            QFrame#Header,
            QFrame#Stats,
            QFrame#Content {
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

            QLabel#Metric {
                color: #1F2937;
                font-size: 22px;
                font-weight: 700;
            }

            QLabel#MetricCaption {
                color: #6B7280;
                font-size: 9pt;
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

            QPushButton#Action:disabled {
                background: #A9D9E9;
            }

            QTableWidget {
                background: white;
                border: none;
                gridline-color: #EEF1F4;
                selection-background-color: #E8F6FB;
                selection-color: #1F2937;
            }

            QHeaderView::section {
                background: #F7F9FC;
                color: #6B7280;
                border: none;
                border-bottom: 1px solid #DCE3EA;
                padding: 9px;
                font-weight: 600;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(18)

        header = QFrame()
        header.setObjectName("Header")

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        header_layout.setSpacing(12)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        title = QLabel("Outlook")
        title.setObjectName("Title")

        subtitle = QLabel(
            "Email synchronization and imported message overview"
        )
        subtitle.setObjectName("Subtitle")

        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)

        header_layout.addLayout(text_layout)
        header_layout.addStretch()

        self.status = QLabel("● Connected")
        self.status.setObjectName("Status")

        self.sync_button = QPushButton("Sync now")
        self.sync_button.setObjectName("Action")
        self.sync_button.setCursor(Qt.PointingHandCursor)
        self.sync_button.clicked.connect(self.sync_now)

        header_layout.addWidget(self.status)
        header_layout.addWidget(self.sync_button)

        root.addWidget(header)

        stats = QHBoxLayout()
        stats.setSpacing(14)

        self.imported_value = self.metric_card("0", "Imported emails")
        self.companies_value = self.metric_card("0", "Companies identified")
        self.last_value = self.metric_card("-", "Last contact")

        stats.addWidget(self.imported_value)
        stats.addWidget(self.companies_value)
        stats.addWidget(self.last_value)

        root.addLayout(stats)

        content = QFrame()
        content.setObjectName("Content")

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 16, 18, 18)
        content_layout.setSpacing(12)

        content_title = QLabel("Latest imported emails")
        content_title.setObjectName("Title")

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            "Recipient",
            "Email",
            "Subject",
            "Sent",
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.table.verticalHeader().setVisible(False)

        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        header_view.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        header_view.setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        header_view.setSectionResizeMode(
            3, QHeaderView.ResizeMode.ResizeToContents
        )

        content_layout.addWidget(content_title)
        content_layout.addWidget(self.table)

        root.addWidget(content, 1)

        self.refresh_data()

    def metric_card(self, value, caption):
        frame = QFrame()
        frame.setObjectName("Stats")

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(2)

        value_label = QLabel(value)
        value_label.setObjectName("Metric")
        value_label.setAlignment(Qt.AlignCenter)

        caption_label = QLabel(caption)
        caption_label.setObjectName("MetricCaption")
        caption_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(value_label)
        layout.addWidget(caption_label)

        frame.value_label = value_label
        return frame

    def refresh_data(self):
        total = self.scanner.database.total_emails()
        domains = self.scanner.database.total_domains()
        last = self.scanner.database.last_email()

        self.imported_value.value_label.setText(str(total))
        self.companies_value.value_label.setText(str(domains))
        self.last_value.value_label.setText(
            str(last)[:16] if last else "-"
        )

        rows = self.scanner.database.get_recent_emails(10)
        self.table.setRowCount(0)

        for row_data in rows:
            row = self.table.rowCount()
            self.table.insertRow(row)

            values = [
                row_data["recipient_name"] or "-",
                row_data["recipient_email"] or "-",
                row_data["subject"] or "(No subject)",
                str(row_data["sent_date"] or "-")[:16],
            ]

            for column, value in enumerate(values):
                self.table.setItem(
                    row,
                    column,
                    QTableWidgetItem(str(value)),
                )

    def sync_now(self):
        self.sync_button.setEnabled(False)
        self.status.setText("● Synchronizing...")
        self.status.setStyleSheet(
            "color:#D97706;font-weight:600;"
        )

        try:
            imported, skipped = self.scanner.scan(100)
            self.refresh_data()

            self.status.setText(
                f"● Sync complete · {imported} new · {skipped} skipped"
            )
            self.status.setStyleSheet(
                "color:#16A34A;font-weight:600;"
            )

            self._status_timer.start(4000)

        except Exception as exc:
            self.status.setText("● Sync error")
            self.status.setStyleSheet(
                "color:#DC2626;font-weight:600;"
            )
            print(f"Outlook synchronization error: {exc}")
            self._status_timer.start(5000)

        finally:
            self.sync_button.setEnabled(True)

    def _restore_connected(self):
        self.status.setText("● Connected")
        self.status.setStyleSheet(
            "color:#16A34A;font-weight:600;"
        )

    def set_connected(self, connected):
        self._status_timer.stop()

        if connected:
            self._restore_connected()
        else:
            self.status.setText("● Offline")
            self.status.setStyleSheet(
                "color:#DC2626;font-weight:600;"
            )
