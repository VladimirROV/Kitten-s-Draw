from recent import Ui_Form
from canvasSize import Ui_Dialog
from debug import *

import json
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtGui
from PyQt5.QtCore import *
import os

class RecentWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(RecentWindow, self).__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        
        self.ui.open.clicked.connect(lambda:openImage())
        self.ui.create.clicked.connect(lambda:createImage())
        
        tiles = [self.ui.simg1,self.ui.simg2,self.ui.simg3,self.ui.simg4,self.ui.simg5,self.ui.simg6]
        def repairRecents():
            file = open("recent.json", "w")
            file.write('{"Recents":[]}')
            file.close()
            warning("Нарушена целостность файла recent.json")
        def getRecents():
            try:
                with open('recent.json', 'r+') as file:
                    text = file.read()
            except FileNotFoundError:
                repairRecents()
                getRecents()
            else:
                if not text.strip():
                    repairRecents()
                    getRecents()
                else:
                    try:
                        data = json.loads(text)
                    except json.JSONDecodeError:
                        repairRecents()
                        getRecents()
                        return
                    recents = data['Recents']
                    n = 0
                    #Удаление из списка уже не существующих файлов
                    for i in recents:
                        if not os.path.exists(i):
                            recents.pop(n)
                        n+=1
                    file = open("recent.json", "w")
                    file.write(json.dumps(data))
                    file.close()
                    return recents
                
        
        imgs = getRecents()
        if imgs:
            imgs.reverse()
            for i in range(0,len(tiles)):
                if i==len(imgs):
                    break
                if os.path.exists(imgs[i]):   
                    tiles[i].setIcon(QIcon(imgs[i]))
                    tiles[i].clicked.connect(lambda _, path=imgs[i]: openRecent(path))
        def openRecent(path):
            pixmap = QtGui.QPixmap(path)
            import main
            main.changeWindow("ws",pixmap.size(),pixmap)
            
            
        def createImage():
            self.dialog = QtWidgets.QDialog()
            self.ui = Ui_Dialog()
            self.ui.setupUi(self.dialog)
            self.dialog.accepted.connect(openInCanvas)
            self.dialog.show()
        def openInCanvas():
            width = self.ui.width.value()
            height = self.ui.spinBox_2.value()
            size = QSize(width,height)
            import main
            main.changeWindow("ws",size)
        def openImage():
            filePath, _ = QFileDialog.getOpenFileName(
                self, "Открыть файл", "", "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;All Files (*)")
            if filePath == "":
                return
            pix_map = QtGui.QPixmap(filePath)
            import main
            main.changeWindow("ws",pix_map.size(),pix_map)
            main.addRecent(filePath)
            
               
        