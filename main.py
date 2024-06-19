from wsController import PaintWindow
from recentController import RecentWindow
from getStartedController import GetStartedWindow
from debug import *

from PyQt5 import QtWidgets,QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys
import json
import os

#Против хитрых
if not os.path.exists("icons"):
    error("Нарушена целостность программы, не присутствует папка icons! Запуск невозможен")
    sys.exit()
if not os.path.exists("Temp"):
    os.makedirs("Temp")
#Создание скрытых папок =)
os.system("attrib +h " + 'Temp')
os.system("attrib +h " + 'icons')
app = QtWidgets.QApplication(sys.argv)
app.setWindowIcon(QIcon("./icons/icon.ico"))
windows = {"recent":RecentWindow(),"start":GetStartedWindow()}
currentWindow = GetStartedWindow()
def changeWindow(window,canvas_size=QSize(0,0),pixmap=None):
    if window == "ws" :
        if pixmap is not None:
            application = PaintWindow(canvas_size,pixmap)
        else:
            application = PaintWindow(canvas_size)
    else:
        application = windows[window]
    global currentWindow
    currentWindow.hide()
    currentWindow = application
    
    application.show()
def repairRecent():
    file = open("recent.json", "w")
    file.write('{"Recents":[]}')
    file.close()
    warning("Нарушена целостность файла recent.json")
def addRecent(path):
    try:
       with open('recent.json', 'r+') as file:
        text = file.read()
    except FileNotFoundError:
       repairRecent()
       addRecent(path)
    if not text.strip():
        repairRecent()
        addRecent(path)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        repairRecent()
        addRecent()
        return
    recents = data['Recents']
    recents.append(path)
    if len(recents) > 6:
        recents.pop(0)
    with open('recent.json', 'r+') as file:
        text = file.write(json.dumps(data))
changeWindow("start")

sys.exit(app.exec())
