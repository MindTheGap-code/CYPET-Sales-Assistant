from PySide6.QtCore import Qt
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
    QFileDialog,
)

from modules.database import Database


class ReportPage(QWidget):
    def __init__(self):
        super().__init__()

        self.db = Database()

        self.setStyleSheet("""
            QFrame#Header,
            QFrame#Summary,
            QFrame#Report {
                background: white;
                border: 1px solid #DCE3EA;
                border-radius: 12px;
            }

            QLabel#Title {
                color: #1F2937;
                font-size: 20px;
                font-weight: 700;
            }

            QLabel#Subtitle,
            QLabel#Caption {
                color: #6B7280;
                font-size: 10pt;
            }

            QLabel#MetricTitle {
                color: #6B7280;
                font-size: 9pt;
            }

            QLabel#MetricValue {
                color: #1F2937;
                font-size: 22px;
                font-weight: 700;
            }

            QPushButton#Primary {
                background: #00A3E0;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 9px 18px;
                font-weight: 600;
            }

            QPushButton#Primary:hover {
                background: #008FC4;
            }

            QPushButton#Secondary {
                background: #EEF4F8;
                color: #374151;
                border: none;
                border-radius: 8px;
                padding: 9px 18px;
                font-weight: 600;
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

        text_layout = QVBoxLayout()
        text_layout.setSpacing(3)

        title = QLabel("Report")
        title.setObjectName("Title")

        subtitle = QLabel(
            "Sales activity, prospecting and Outlook synchronization overview."
        )
        subtitle.setObjectName("Subtitle")

        text_layout.addWidget(title)
        text_layout.addWidget(subtitle)

        header_layout.addLayout(text_layout)
        header_layout.addStretch()

        self.export_button = QPushButton("Export")
        self.export_button.setObjectName("Secondary")
        self.export_button.setCursor(Qt.PointingHandCursor)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.setObjectName("Primary")
        self.refresh_button.setCursor(Qt.PointingHandCursor)

        header_layout.addWidget(self.export_button)
        header_layout.addWidget(self.refresh_button)

        root.addWidget(header)

        summary = QFrame()
        summary.setObjectName("Summary")

        summary_layout = QHBoxLayout(summary)
        summary_layout.setContentsMargins(20, 18, 20, 18)
        summary_layout.setSpacing(40)

        self.email_value = self._metric(summary_layout, "Emails")
        self.company_value = self._metric(summary_layout, "Companies")
        self.prospect_value = self._metric(summary_layout, "Prospects")
        self.activity_value = self._metric(summary_layout, "Activities")

        summary_layout.addStretch()
        root.addWidget(summary)

        report = QFrame()
        report.setObjectName("Report")

        report_layout = QVBoxLayout(report)
        report_layout.setContentsMargins(20, 18, 20, 18)
        report_layout.setSpacing(12)

        report_title = QLabel("Company activity")
        report_title.setObjectName("Title")

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels([
            "Company / Domain",
            "Contacts",
            "Last contact",
        ])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.table.verticalHeader().setVisible(False)

        table_header = self.table.horizontalHeader()
        table_header.setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        table_header.setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents
        )
        table_header.setSectionResizeMode(
            2, QHeaderView.ResizeMode.ResizeToContents
        )

        report_layout.addWidget(report_title)
        report_layout.addWidget(self.table)

        root.addWidget(report, 1)

        self.refresh_button.clicked.connect(self.refresh_data)
        self.export_button.clicked.connect(self.export_report)

        self.refresh_data()

    def _metric(self, layout, title):
        metric = QVBoxLayout()
        metric.setSpacing(3)

        metric_title = QLabel(title)
        metric_title.setObjectName("MetricTitle")

        metric_value = QLabel("0")
        metric_value.setObjectName("MetricValue")

        metric.addWidget(metric_title)
        metric.addWidget(metric_value)
        layout.addLayout(metric)

        return metric_value

    def refresh_data(self):
        emails = self.db.total_emails()
        companies = self.db.total_domains()
        domains = self.db.get_domains(5000)

        self.email_value.setText(str(emails))
        self.company_value.setText(str(companies))
        self.prospect_value.setText(str(companies))
        self.activity_value.setText(str(emails))

        self.table.setRowCount(0)

        for row_data in domains:
            row = self.table.rowCount()
            self.table.insertRow(row)

            values = [
                row_data["domain"] or "-",
                str(row_data["total"]),
                str(row_data["last_contact"] or "-")[:16],
            ]

            for column, value in enumerate(values):
                self.table.setItem(
                    row,
                    column,
                    QTableWidgetItem(str(value)),
                )

    def export_report(self):
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export report",
            "cypet_sales_report.csv",
            "CSV files (*.csv)",
        )

        if not path:
            return

        import csv

        with open(path, "w", newline="", encoding="utf-8-sig") as file:
            writer = csv.writer(file, delimiter=";")
            writer.writerow([
                "Company / Domain",
                "Contacts",
                "Last contact",
            ])

            for row in range(self.table.rowCount()):
                writer.writerow([
                    self.table.item(row, 0).text(),
                    self.table.item(row, 1).text(),
                    self.table.item(row, 2).text(),
                ])
