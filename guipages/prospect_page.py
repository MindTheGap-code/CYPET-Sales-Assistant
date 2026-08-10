from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFrame,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
)


class ProspectPage(QWidget):
    def __init__(self):
        super().__init__()

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

            QLineEdit,
            QComboBox {
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

        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)
        header_layout.setSpacing(4)

        title = QLabel("Prospect")
        title.setObjectName("Title")

        subtitle = QLabel(
            "Manage companies and contacts identified as potential customers."
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
        self.search.setPlaceholderText("Search company or contact...")
        self.search.setFixedHeight(38)

        self.industry = QComboBox()
        self.industry.addItems([
            "All industries",
            "PET Packaging",
            "Beverage",
            "Pharma",
            "Cosmetics",
            "Home Care",
        ])
        self.industry.setFixedWidth(160)

        self.status = QComboBox()
        self.status.addItems([
            "All statuses",
            "New",
            "Contacted",
            "Qualified",
            "Customer",
        ])
        self.status.setFixedWidth(150)

        search_button = QPushButton("Search")
        search_button.setObjectName("Primary")
        search_button.setCursor(Qt.PointingHandCursor)

        clear_button = QPushButton("Clear")
        clear_button.setObjectName("Secondary")
        clear_button.setCursor(Qt.PointingHandCursor)

        filters_layout.addWidget(self.search, 1)
        filters_layout.addWidget(self.industry)
        filters_layout.addWidget(self.status)
        filters_layout.addWidget(search_button)
        filters_layout.addWidget(clear_button)

        root.addWidget(filters)

        results = QFrame()
        results.setObjectName("Results")

        results_layout = QVBoxLayout(results)
        results_layout.setContentsMargins(20, 16, 20, 16)

        top = QHBoxLayout()

        result_title = QLabel("Prospects")
        result_title.setObjectName("Title")

        self.count = QLabel("0 prospects")
        self.count.setObjectName("Count")

        top.addWidget(result_title)
        top.addStretch()
        top.addWidget(self.count)

        empty = QLabel(
            "No prospects available yet.\n"
            "Use the search and filters above to find potential customers."
        )
        empty.setObjectName("Caption")
        empty.setAlignment(Qt.AlignCenter)

        results_layout.addLayout(top)
        results_layout.addStretch()
        results_layout.addWidget(empty)
        results_layout.addStretch()

        root.addWidget(results, 1)

        clear_button.clicked.connect(self.clear_filters)

    def clear_filters(self):
        self.search.clear()
        self.industry.setCurrentIndex(0)
        self.status.setCurrentIndex(0)
