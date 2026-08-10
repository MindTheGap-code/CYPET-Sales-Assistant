from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
)


class _Shadow:
    @staticmethod
    def apply(widget):
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 3)
        shadow.setColor(QColor(0, 0, 0, 35))
        widget.setGraphicsEffect(shadow)


class Card(QFrame):
    def __init__(self, title="", value="", footer=""):
        super().__init__()

        self.setObjectName("Card")
        self.setMinimumHeight(118)
        _Shadow.apply(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)

        self.lbl_title = QLabel(title)
        self.lbl_title.setObjectName("Secondary")

        self.lbl_value = QLabel(value)
        self.lbl_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_value.setStyleSheet(
            "font-size:28px;font-weight:700;color:#1f2937;"
        )

        self.lbl_footer = QLabel(footer)
        self.lbl_footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_footer.setObjectName("Secondary")

        layout.addWidget(self.lbl_title)
        layout.addStretch()
        layout.addWidget(self.lbl_value)
        layout.addStretch()
        layout.addWidget(self.lbl_footer)

    def set_value(self, value):
        self.lbl_value.setText(str(value))

    def set_title(self, title):
        self.lbl_title.setText(title)

    def set_footer(self, footer):
        self.lbl_footer.setText(footer)


class Panel(QFrame):
    def __init__(self, title=""):
        super().__init__()

        self.setObjectName("Panel")
        _Shadow.apply(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        header_row.setSpacing(8)

        self.header = QLabel(title)
        self.header.setStyleSheet(
            "font-size:16px;font-weight:700;color:#1f2937;"
        )

        header_row.addWidget(self.header)
        header_row.addStretch()

        self.body = QVBoxLayout()
        self.body.setSpacing(8)

        layout.addLayout(header_row)
        layout.addLayout(self.body)

    def set_title(self, title):
        self.header.setText(title)

    def add_widget(self, widget):
        self.body.addWidget(widget)

    def add_stretch(self):
        self.body.addStretch()

    def clear(self):
        while self.body.count():
            item = self.body.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
