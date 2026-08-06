from PySide6.QtWidgets import QFrame,QLabel,QVBoxLayout,QGraphicsDropShadowEffect
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt


class _Shadow:
    @staticmethod
    def apply(widget):
        shadow=QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(18)
        shadow.setOffset(0,3)
        shadow.setColor(QColor(0,0,0,35))
        widget.setGraphicsEffect(shadow)


class Card(QFrame):

    def __init__(self,title="",value="",footer=""):
        super().__init__()

        self.setObjectName("Card")
        self.setFixedHeight(118)
        _Shadow.apply(self)

        layout=QVBoxLayout(self)
        layout.setContentsMargins(16,12,16,12)
        layout.setSpacing(4)

        self.lbl_title=QLabel(title)
        self.lbl_title.setObjectName("Secondary")

        self.lbl_value=QLabel(value)
        self.lbl_value.setAlignment(Qt.AlignCenter)
        self.lbl_value.setStyleSheet(
            "font-size:28px;font-weight:700;color:#1f2937;"
        )

        self.lbl_footer=QLabel(footer)
        self.lbl_footer.setAlignment(Qt.AlignCenter)
        self.lbl_footer.setObjectName("Secondary")

        layout.addWidget(self.lbl_title)
        layout.addStretch()
        layout.addWidget(self.lbl_value)
        layout.addStretch()
        layout.addWidget(self.lbl_footer)

    def set_value(self,value):
        self.lbl_value.setText(str(value))


class Panel(QFrame):

    def __init__(self,title=""):
        super().__init__()

        self.setObjectName("Panel")
        _Shadow.apply(self)

        layout=QVBoxLayout(self)
        layout.setContentsMargins(18,16,18,16)
        layout.setSpacing(12)

        self.header=QLabel(title)
        self.header.setStyleSheet(
            "font-size:16px;font-weight:700;color:#1f2937;"
        )

        self.body=QVBoxLayout()
        self.body.setSpacing(8)

        layout.addWidget(self.header)
        layout.addLayout(self.body)

    def add_widget(self,widget):
        self.body.addWidget(widget)

    def add_stretch(self):
        self.body.addStretch()
