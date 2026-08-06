
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class Card(QFrame):
    def __init__(self, title="", value="", footer=""):
        super().__init__()

        self.setObjectName("Card")
        self.setMinimumHeight(110)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 14, 18, 14)

        self.title = QLabel(title)
        self.title.setObjectName("Secondary")

        self.value = QLabel(value)
        self.value.setObjectName("PageTitle")

        self.footer = QLabel(footer)
        self.footer.setObjectName("Secondary")

        layout.addWidget(self.title)
        layout.addStretch()
        layout.addWidget(self.value)
        layout.addWidget(self.footer)


class Panel(QFrame):
    def __init__(self, title=""):
        super().__init__()

        self.setObjectName("Panel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)

        self.title = QLabel(title)
        self.title.setObjectName("PageTitle")

        self.body = QVBoxLayout()

        layout.addWidget(self.title)
        layout.addSpacing(10)
        layout.addLayout(self.body)

    def add_widget(self, widget):
        self.body.addWidget(widget)

    def add_stretch(self):
        self.body.addStretch()
