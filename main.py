# main.py
#!/usr/bin/env python3
import sys
from PySide6.QtWidgets import QApplication
from gui.startpage import StartPage

if __name__ == "__main__":
    app = QApplication(sys.argv)

    w = StartPage()
    w.showMaximized()  # fills the screen

    sys.exit(app.exec())
