import os
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QStackedWidget

os.environ["FINNHUB_API_KEY"] = "d5f6tt9r01qtf8imrve0d5f6tt9r01qtf8imrveg"

from gui.startpage import StartPage
from gui.mainpage import MainPage
from gui.analysepage import AnalysePage   # NEU


if __name__ == "__main__":
    app = QApplication(sys.argv)

    stack = QStackedWidget()

    start = StartPage(logo_path="images/Aurelic Logo mit Clar Leitmotiv.png")
    main = MainPage()              # Brokerage
    analyse = AnalysePage()        # Analyse

    stack.addWidget(start)    # index 0
    stack.addWidget(main)     # index 1
    stack.addWidget(analyse)  # index 2

    # Start direkt auf Brokerage
    stack.setCurrentWidget(main)

    # Tabs schalten Seiten um
    def on_tab(which: str):
        if which == "brokerage":
            stack.setCurrentWidget(main)
        elif which == "analyse":
            stack.setCurrentWidget(analyse)

    main.tab_changed.connect(on_tab)
    analyse.tab_changed.connect(on_tab)

    # Avatar-Klick kannst du später identisch auf Settings routen:
    # main.avatar_clicked.connect(...)
    # analyse.avatar_clicked.connect(...)

    def on_key(event):
        if event.key() == Qt.Key_F1:
            stack.setCurrentWidget(start)
            return
        if event.key() == Qt.Key_F2:
            stack.setCurrentWidget(main)
            return
        if event.key() == Qt.Key_F3:
            stack.setCurrentWidget(analyse)
            return
        if event.key() == Qt.Key_Escape:
            app.quit()
            return
        QStackedWidget.keyPressEvent(stack, event)

    stack.keyPressEvent = on_key

    stack.showMaximized()
    sys.exit(app.exec())
