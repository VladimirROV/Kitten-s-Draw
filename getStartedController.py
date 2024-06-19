from getStarted import Ui_MainWindow
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

class GetStartedWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(GetStartedWindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        import main
        self.ui.startbtn.clicked.connect(lambda: main.changeWindow("recent"))
        