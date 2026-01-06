import sys
from PySide6.QtWidgets import QApplication
from gui.startpage import StartPage

if __name__ == "__main__":
    app = QApplication(sys.argv)

    w = StartPage(logo_path="images/Aurelic Logo mit Clar Leitmotiv.png")
    w.showMaximized()

    sys.exit(app.exec())
