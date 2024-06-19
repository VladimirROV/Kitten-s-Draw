# Импорт локальных
from ws import Ui_MainWindow
from debug import *
# Импорт Pip репозиториев
from vcolorpicker import getColor
from PIL import Image
from PIL import ImageFilter
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtGui
import os

import sys
import numpy as np
import random


class Settings():
    selectedcolor = "primary"
    brushSize = 28
    opacity = 100
    primarycolor = QColor(196, 46, 233)
    secondcolor = QColor(61, 61, 61)
    tool = "Brush"
    selection_css = "border: 2px solid blue;"
    ps_colors_css = "background-color: {};"
    figure_thickness = 12
    canvas_size = QSize(800, 600)


config = Settings()


class Canvas(QtWidgets.QWidget):
    def __init__(self, btn,canvas_frame):
        super().__init__()
        self.image = QImage(config.canvas_size, QImage.Format_RGB32)
        self.image.fill(Qt.GlobalColor.white)
        self.drawing = False
        self.btn = btn
        self.frame = canvas_frame
        self.frame.setMinimumSize(config.canvas_size)
        self.color = config.primarycolor
        self.lastPoint = QPoint()
        self.begin, self.destination = QPoint(), QPoint()
        self.points = []
        self.tempPath = QPainterPath()
        self.path = QPainterPath()

        self.undo_stack = []
        self.redo_stack = []
        self.saveState()

    def saveState(self):
        self.undo_stack.append(self.image.copy())
        if len(self.undo_stack) > 10:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(self.image.copy())
            self.image = self.undo_stack.pop()
            self.update()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(self.image.copy())
            self.image = self.redo_stack.pop()
            self.update()

    def mousePressEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.saveState()
            if config.tool in ["Rectangle", "RoundedRect", "Ellipse", "Line", "Hexagon"]:
                self.begin = event.pos()
                self.destination = self.begin
                self.update()
            elif config.tool == "Picker":
                self.setcolor_forPicker(self.picker(event.pos()))
                self.update()
            elif config.tool == "Pen":
                self.points.append(event.pos())
                if len(self.points) == 1:
                    self.path.moveTo(self.points[0])
                self.update()
            elif config.tool == "Bucket":
                self.floodFill(event.pos(), self.color)
                self.update()
            elif config.tool == "Text":
                self.addText(event.pos())
            elif config.tool == "Spray":
                self.drawing = True
                self.lastPoint = event.pos()
                self.spray(event.pos())
            else:
                self.drawing = True
                self.lastPoint = event.pos()
        if event.button() == Qt.RightButton:
            self.drawing = False
            if self.color != config.primarycolor:
                self.color = config.primarycolor
                self.btn[0].setStyleSheet(
                    config.selection_css + config.ps_colors_css.format(config.primarycolor.name()))
                self.btn[1].setStyleSheet(
                    config.ps_colors_css.format(config.secondcolor.name()))
                config.selectedcolor = "primary"
                return
            self.color = config.secondcolor
            self.btn[1].setStyleSheet(
                config.selection_css + config.ps_colors_css.format(config.secondcolor.name()))
            self.btn[0].setStyleSheet(
                config.ps_colors_css.format(config.primarycolor.name()))
            config.selectedcolor = "second"

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            if self.drawing:
                painter = QPainter(self.image)
                color = self.color
                if config.tool in ["Eraser", "Brush"]:
                    if config.tool == "Eraser":
                        color = Qt.GlobalColor.white
                    painter.setPen(QPen(color, config.brushSize,
                                        Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                    painter.drawLine(self.lastPoint, event.pos())
                    self.lastPoint = event.pos()
                    self.update()
                elif config.tool == "Spray":
                    self.spray(event.pos())
                painter.end()
            if config.tool in ["Rectangle", "RoundedRect", "Ellipse", "Line", "Hexagon"]:
                self.destination = event.pos()
                self.update()
            if config.tool == "Pen" and len(self.points) == 3:
                self.updateTempBezierCurve(event.pos())
                self.saveState()
                self.update()

    def mouseReleaseEvent(self, event):
        p = QPainter(self.image)
        p.setPen(QPen(self.color, config.figure_thickness,
                 Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        if event.button() == Qt.LeftButton:
            if config.tool in ["Rectangle", "RoundedRect", "Ellipse", "Line", "Hexagon"]:
                rect = QRectF(self.begin, self.destination)
                if config.tool == "RoundedRect":
                    p.drawRoundedRect(rect.normalized(), 100, 100)
                    self.begin, self.destination = QPoint(), QPoint()
                    self.update()
                if config.tool == "Ellipse":
                    p.drawEllipse(QRect(self.begin, self.destination))
                    self.begin, self.destination = QPoint(), QPoint()
                    self.update()
                if config.tool == "Line":
                    p.drawLine(self.begin, self.destination)
                    self.begin, self.destination = QPoint(), QPoint()
                    self.update()
                if config.tool == "Rectangle":
                    p.drawRect(rect.normalized())
                    self.begin, self.destination = QPoint(), QPoint()
                    self.update()
                if config.tool == "Hexagon":
                    self.drawHexagon(p, self.begin, self.destination)
                    self.begin, self.destination = QPoint(), QPoint()
                    self.update()
            elif config.tool == "Pen" and len(self.points) == 4:
                self.addBezierCurve()
                self.tempPath = QPainterPath()
                self.saveState()
                self.update()
            else:
                self.drawing = False
        p.end()

    def spray(self, pos):
        painter = QPainter(self.image)
        painter.setPen(QPen(self.color, 1))
        for _ in range(1000):
            dx = int(random.gauss(0, config.brushSize/1))
            dy = int(random.gauss(0, config.brushSize/1))
            painter.drawPoint(pos.x() + dx, pos.y() + dy)
        self.update()

    def updateTempBezierCurve(self, endPoint):
        self.tempPath = QPainterPath()
        self.tempPath.moveTo(self.points[0])
        self.tempPath.cubicTo(self.points[1], self.points[2], endPoint)

    def addBezierCurve(self):
        if len(self.points) == 4:
            self.path.cubicTo(self.points[1], self.points[2], self.points[3])
            p = QPainter(self.image)
            p.setPen(QPen(self.color, config.figure_thickness,
                     Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawPath(self.path)
            self.update()
            p.end()
            self.points = []

    def setcolor_forPicker(self, color):
        if config.selectedcolor == "primary":
            self.btn[0].setStyleSheet(
                config.selection_css + "background-color: {};".format(color.name()))
            config.primarycolor = color
            self.color = color
        if config.selectedcolor == "second":
            self.btn[1].setStyleSheet(
                config.selection_css + "background-color: {};".format(color.name()))
            config.secondcolor = color
            self.color = color

    def drawHexagon(self, painter, start_point, end_point):
        rect = QRectF(start_point, end_point).normalized()
        center = rect.center()
        radius = min(rect.width(), rect.height()) / 2
        hexagon = QPolygonF()
        for i in range(6):
            angle = 2 * np.pi / 6 * i
            x = center.x() + radius * np.cos(angle)
            y = center.y() + radius * np.sin(angle)
            hexagon.append(QPointF(x, y))
        painter.drawPolygon(hexagon)

    def floodFill(self, start_point, new_color):
        width = self.image.width()
        height = self.image.height()
        target_color = self.image.pixelColor(start_point)

        if target_color == new_color:
            return

        buffer = self.image.constBits()
        buffer.setsize(self.image.byteCount())
        pixels = np.array(buffer).reshape((height, width, 4)).copy()

        def color_match(c1, c2):
            return (c1.red() == c2.red() and c1.green() == c2.green() and c1.blue() == c2.blue() and c1.alpha() == c2.alpha())

        mask = np.zeros((height, width), dtype=bool)
        queue = [(start_point.x(), start_point.y())]
        while queue:
            x, y = queue.pop(0)
            if not (0 <= x < width and 0 <= y < height):
                continue
            if mask[y, x]:
                continue
            current_color = QColor(*pixels[y, x])
            if not color_match(current_color, target_color):
                continue

            pixels[y, x] = [new_color.red(), new_color.green(),
                            new_color.blue(), new_color.alpha()]
            mask[y, x] = True

            queue.extend([(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)])

        for y in range(height):
            for x in range(width):
                if mask[y, x]:
                    self.image.setPixelColor(x, y, QColor(*pixels[y, x]))

        self.update()
    def paintEvent(self, event):
        p = QPainter(self)
        p.drawImage(QPoint(), self.image)
        if config.tool in ["Rectangle", "RoundedRect", "Ellipse", "Line", "Hexagon"]:
            p.setPen(QPen(self.color, config.figure_thickness,
                     Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawImage(QPoint(), self.image)
            if not self.begin.isNull() and not self.destination.isNull():
                rect = QRect(self.begin, self.destination)
                if config.tool == "Ellipse":
                    p.drawEllipse(rect)
                if config.tool == "Rectangle":
                    p.drawRect(rect.normalized())
                if config.tool == "RoundedRect":
                    p.drawRoundedRect(rect.normalized(), 100, 100)
                if config.tool == "Line":
                    p.drawLine(self.begin, self.destination)
                if config.tool == "Hexagon":
                    self.drawHexagon(p, self.begin, self.destination)
        if config.tool == "Pen":
            p.setPen(QPen(self.color, config.figure_thickness,
                     Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            p.drawPath(self.path)
            if len(self.points) == 3:
                p.setPen(QPen(Qt.red, config.figure_thickness,
                         Qt.DashLine, Qt.RoundCap, Qt.RoundJoin))
                p.drawPath(self.tempPath)
            for point in self.points:
                p.setPen(QPen(Qt.blue, config.figure_thickness,
                         Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                p.drawEllipse(point, 5, 5)
                p.setPen(QPen(Qt.black, 1, Qt.SolidLine,
                         Qt.RoundCap, Qt.RoundJoin))
                if point != self.points[0]:
                    p.drawLine(point, self.points[0])
            self.update()
        p.end()

    def picker(self, pos):
        color = self.image.pixelColor(pos)
        return color

    def saveImage(self):
        filePath, _ = QFileDialog.getSaveFileName(
            self, "Сохранить изображение", "", "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;All Files (*)")
        if filePath == "":
            return
        import main
        main.addRecent(filePath)
        self.image.save(filePath)
    def openImage(self):
        filePath, _ = QFileDialog.getOpenFileName(
            self, "Открыть изображение", "", "PNG Files (*.png);;JPEG Files (*.jpg *.jpeg);;All Files (*)")
        if filePath == "":
            return
        pix_map = QtGui.QPixmap(filePath)
        config.canvas_size = pix_map.size()
        self.image = QImage(pix_map)
        self.image.size = config.canvas_size
        self.frame.setMinimumSize(config.canvas_size)
        import main
        main.addRecent(filePath)
        self.update()

    def clear(self):
        self.image.fill(Qt.GlobalColor.white)
        self.path = QPainterPath()
        self.points = []
        self.update()

    def addText(self, position):
        
        text, ok = QInputDialog.getText(self, 'Input Text', 'Enter your text:')
        if ok and text:
            (font, okay) = QFontDialog.getFont(QFont("Helvetica [Cronyx]", 10), self)
            if okay:
                p = QPainter(self.image)
                p.setPen(QPen(self.color))
                p.setFont(font)
                p.drawText(position, text)
                self.update()
                self.saveState()
            else:
                return

class PaintWindow(QtWidgets.QMainWindow):
    # Инициализация
    def __init__(self,size,pixmap=None):
        super(PaintWindow, self).__init__()
        config.canvas_size = size
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        # Добавление холста(Canvas)
        colorbtns = [self.ui.primaryColor, self.ui.secondColor]
        self.canvas = Canvas(colorbtns,self.ui.frame)
        if pixmap is not None:
            config.canvas_size = pixmap.size()
            self.canvas.image = QImage(pixmap)
            self.canvas.size = config.canvas_size
            self.ui.frame.setMinimumSize(config.canvas_size)
            self.canvas.update()
        self.ui.verticalLayout_3.addWidget(self.canvas)
        # Привязка кнопок к ассоциативному массиву для удобства
        self.tools = {"Brush": self.ui.brush, "Eraser": self.ui.eraser, "Bucket": self.ui.bucket, "Picker": self.ui.picker,
                      "Spray": self.ui.spray, "Rectangle": self.ui.rectangle, "Hexagon": self.ui.hexagon,
                      "RoundedRect": self.ui.roundedrect, "Ellipse": self.ui.ellipse, "Line": self.ui.line_2, "Pen": self.ui.curve,
                      "Text": self.ui.text}
        self.filters = {"Blur": self.ui.action_4,"Grayscale": self.ui.action_5,"Rotate": self.ui.action_6,"Border-detection": self.ui.action_7,"Embossing": self.ui.action_9,"CMYK":self.ui.action_CMYK,"RGB": self.ui.action_8}
        # Установка стандартных значений
        self.change_opacity(config.opacity - 1)
        self.ui.brushSize.setValue(config.brushSize)
        config.selectedcolor = "primary"
        self.ui.primaryColor.setStyleSheet(
            config.selection_css + config.ps_colors_css.format(config.primarycolor.name()))
        self.ui.secondColor.setStyleSheet(
            config.ps_colors_css.format(config.secondcolor.name()))
        # Привязка к кнопкам
        for i in self.tools:
            self.tools[i].clicked.connect(lambda _, name=i: select_tool(name))
            good("Инициализация инструмента {}".format(i))
        for i in self.filters:
            good("Инициализация фильтра {}".format(i))
            self.filters[i].triggered.connect(lambda _, name=i: setfilters(self,name))
        self.ui.clear.clicked.connect(self.canvas.clear)
        self.ui.action_10.triggered.connect(lambda: sys.exit())
        self.ui.undo.clicked.connect(self.canvas.undo)
        self.ui.action_2.triggered.connect(self.canvas.saveImage)
        self.ui.action_3.triggered.connect(self.canvas.openImage)
        self.ui.un_undo.clicked.connect(self.canvas.redo)
        colorbtns[0].clicked.connect(
            lambda: request_color(self.ui.primaryColor, "primary"))
        colorbtns[1].clicked.connect(
            lambda: request_color(self.ui.secondColor, "second"))
        # Привязка слайдера
        self.ui.opacity.valueChanged.connect(self.change_opacity)
        # Привязка выбора размера кисти
        self.ui.brushSize.valueChanged.connect(self.change_brushSize)
        # Привязка горячих клавиш
        undo_shortcut = QShortcut(QKeySequence("Ctrl+Z"), self)
        undo_shortcut.activated.connect(self.canvas.undo)
        redo_shortcut = QShortcut(QKeySequence("Ctrl+Y"), self)
        redo_shortcut.activated.connect(self.canvas.redo)

        # Методы для кнопок
        def request_color(btn, typecolor):
            color = getColor()
            selected_color = QColor(
                int(color[0]), int(color[1]), int(color[2]), config.opacity)
            style = "background-color: rgb{};"
            if typecolor == config.selectedcolor:
                style += config.selection_css
                self.canvas.color = selected_color
            btn.setStyleSheet(style.format(color))
            if typecolor == "second":
                config.secondcolor = selected_color
                return
            config.primarycolor = selected_color
                

        def select_tool(tool):
            self.tools[config.tool].setStyleSheet(
                "background-color: white;border-radius: 2.5px;")
            config.tool = tool
            self.tools[config.tool].setStyleSheet(
                "background-color: white;border-radius: 2.5px;border: 2px solid blue;")
            if config.tool in ["Pen", "Rectangle", "Hexagon", "Line", "Ellipse", "RoundedRect"]:
                self.ui.brushSize.setValue(config.figure_thickness)
                self.ui.label.setText("Толщина фигур")
                self.update()
            elif config.tool in ["Brush", "Eraser"]:
                self.ui.brushSize.setValue(config.brushSize)
                self.ui.label.setText("Размер кисти")
                self.update()
        def setfilters(self, filter):
                #Совмещение с библиотекой pillow через папку временных изображений
                self.canvas.image.save('./Temp/img.png')
                Img = Image.open('./Temp/img.png')
                if filter == "Blur":
                    Img.filter(ImageFilter.BoxBlur(5)).save("./Temp/img.png")
                if filter == "Grayscale":
                    Img.convert("L").save("./Temp/img.png")
                if filter == "Rotate":
                    Img.rotate(90,expand=True).save("./Temp/img.png")
                if filter == "Border_detection":
                    Img.filter(ImageFilter.FIND_EDGES).save("./Temp/img.png")
                if filter == "Embossing":
                    Img.filter(ImageFilter.EMBOSS).save("./Temp/img.png")
                if filter == "CMYK":
                    Img.convert("CMYK").save("./Temp/img.png")
                if filter == "RGB":
                    Img.convert("RGB").save("./Temp/img.png")
                pix_map = QtGui.QPixmap('./Temp/img.png')
                config.canvas_size = pix_map.size()
                self.canvas.size = config.canvas_size
                self.ui.frame.setMinimumSize(config.canvas_size)
                self.canvas.update()
                self.canvas.image = QImage(pix_map)
    def change_opacity(self, value):
        config.opacity = value
        self.ui.opacity.setValue(value)
        self.canvas.color.setAlpha(value)
        self.ui.opacity_percentage.setText("{}%".format(value + 1))

    def change_brushSize(self, value):
        if config.tool == "Brush":
            config.brushSize = value
            return
        config.figure_thickness = value



