from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)

from modules.database import Database


class ProspectPage(QWidget):
    def __init__(self):
        super().__init__()

        self.db = Database()
        self.all_domains = []

        self.setStyleSheet("""
            QFrame#Header,
            QFrame#Filters,
            QFrame#Results {
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

            QLabel#Count {
                color: #00A3E0;
                font-size: 12pt;
                font-weight: 700;
            }

            QLineEdit {
                background: #F7F9FC;
                border: 1px solid #DCE3EA;
                border-radius: 8px;
                padding: 8px 10px;
                min-height: 20px;
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

        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        header_layout.setSpacing(4)

        title = QLabel("Prospect")
        title.setObjectName("Title")

        subtitle = QLabel(
            "Search and explore companies identified from your Outlook contacts."
        )
        subtitle.setObjectName("Subtitle")

        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)

        root.addWidget(header)

        filters = QFrame()
        filters.setObjectName("Filters")

        filters_layout = QHBoxLayout(filters)
        filters_layout.setContentsMargins(16, 14, 16, 14)
        filters_layout.setSpacing(10)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search company or domain...")
        self.search.setFixedHeight(38)

        search_button = QPushButton("Search")
        search_button.setObjectName("Primary")
        search_button.setCursor(Qt.PointingHandCursor)

        clear_button = QPushButton("Clear")
        clear_button.setObjectName("Secondary")
        clear_button.setCursor(Qt.PointingHandCursor)

        filters_layout.addWidget(self.search, 1)
        filters_layout.addWidget(search_button)
        filters_layout.addWidget(clear_button)

        root.addWidget(filters)

        results = QFrame()
        results.setObjectName("Results")

        results_layout = QVBoxLayout(results)
        results_layout.setContentsMargins(20, 16, 20, 16)
        results_layout.setSpacing(12)

        top = QHBoxLayout()

        result_title = QLabel("Prospects")
        result_title.setObjectName("Title")

        self.count = QLabel("0 companies")
        self.count.setObjectName("Count")

        top.addWidget(result_title)
        top.addStretch()
        top.addWidget(self.count)

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

        results_layout.addLayout(top)
        results_layout.addWidget(self.table)

        root.addWidget(results, 1)

        search_button.clicked.connect(self.search_domains)
        clear_button.clicked.connect(self.clear_filters)
        self.search.returnPressed.connect(self.search_domains)

        self.refresh_data()

    def refresh_data(self):
        self.all_domains = self.db.get_domains(5000)
        self.populate_table(self.all_domains)

    def search_domains(self):
        query = self.search.text().strip().lower()

        if not query:
            self.populate_table(self.all_domains)
            return

        filtered = [
            row
            for row in self.all_domains
            if query in str(row["domain"] or "").lower()
        ]

        self.populate_table(filtered)

    def populate_table(self, rows):
        self.table.setRowCount(0)

        for row_data in rows:
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

        self.count.setText(f"{len(rows)} companies")

    def clear_filters(self):
        self.search.clear()
        self.populate_table(self.all_domains)
