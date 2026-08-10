import sys

from PySide6.QtWidgets import QApplication

from gui.main_window import MainWindow
from gui.styles import app_styles


def main():
    app = QApplication(sys.argv)

    app.setStyleSheet(app_styles())

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
