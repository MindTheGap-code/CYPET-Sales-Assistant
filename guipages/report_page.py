from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QPushButton


class ReportPage(QWidget):
    def __init__(self):
        super().__init__()

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

            QPushButton#Secondary {
                background: #EEF4F8;
                color: #374151;
                border: none;
                border-radius: 8px;
                padding: 9px 18px;
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

        export_button = QPushButton("Export")
        export_button.setObjectName("Secondary")
        export_button.setCursor(Qt.PointingHandCursor)

        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("Primary")
        refresh_button.setCursor(Qt.PointingHandCursor)

        header_layout.addWidget(export_button)
        header_layout.addWidget(refresh_button)

        root.addWidget(header)

        summary = QFrame()
        summary.setObjectName("Summary")

        summary_layout = QHBoxLayout(summary)
        summary_layout.setContentsMargins(20, 18, 20, 18)
        summary_layout.setSpacing(40)

        metrics = [
            ("Emails", "0"),
            ("Companies", "0"),
            ("Prospects", "0"),
            ("Activities", "0"),
        ]

        for title_text, value_text in metrics:
            metric = QVBoxLayout()
            metric.setSpacing(3)

            metric_title = QLabel(title_text)
            metric_title.setObjectName("MetricTitle")

            metric_value = QLabel(value_text)
            metric_value.setObjectName("MetricValue")

            metric.addWidget(metric_title)
            metric.addWidget(metric_value)
            summary_layout.addLayout(metric)

        summary_layout.addStretch()
        root.addWidget(summary)

        report = QFrame()
        report.setObjectName("Report")

        report_layout = QVBoxLayout(report)
        report_layout.setContentsMargins(20, 18, 20, 18)
        report_layout.setSpacing(12)

        report_title = QLabel("Sales report")
        report_title.setObjectName("Title")

        report_text = QLabel(
            "No report data available yet."
        )
        report_text.setObjectName("Caption")
        report_text.setAlignment(Qt.AlignCenter)

        report_layout.addWidget(report_title)
        report_layout.addStretch()
        report_layout.addWidget(report_text)
        report_layout.addStretch()

        root.addWidget(report, 1)
