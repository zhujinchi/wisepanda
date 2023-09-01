# coding:utf-8
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, QVBoxLayout, QWidget, QSlider, QHBoxLayout, QGroupBox, QSplitter, QSizePolicy
from PyQt6.QtGui import QPixmap, QImage, QBitmap, QColor
from qfluentwidgets import ScrollArea, HollowHandleStyle, Slider, setTheme, Theme, PushButton


from .gallery_interface import GalleryInterface 

class MatchInterface(GalleryInterface):
    """ Match interface """

    def __init__(self, parent=None):
        super().__init__(
            title='匹配区',
            parent=parent
            )
        self.setObjectName('matchInterface')
       
        self.matchView = ImageWidget()

        self.vBoxLayout.addWidget(self.matchView)
       
        
class ImageWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.layout = QVBoxLayout()

        # 上半区 列表区
        self.upper_widget = QWidget(self)
        self.upper_layout = QVBoxLayout(self.upper_widget)
        self.upper_widget.setStyleSheet("background-color: red;")
        self.image_label = QLabel(self.upper_widget)
        self.upper_layout.addWidget(self.image_label)
        self.layout.addWidget(self.upper_widget)

        # 下半区
        self.lower_widget = QWidget(self)
        self.lower_layout = QHBoxLayout(self.lower_widget)
        self.lower_left_widget = QWidget(self.lower_widget) # 左区 图片区
        self.lower_right_widget = QWidget(self.lower_widget) # 右区 控制区

        self.lower_left_widget.setStyleSheet("background-color: green;") 
        # self.lower_right_widget.setStyleSheet("background-color: blue;")
        
        self.lower_layout.addWidget(self.lower_left_widget)
        self.lower_layout.addWidget(self.lower_right_widget)
        self.layout.addWidget(self.lower_widget)


        # 下半区 图片区
        self.image_area_container = QWidget(self.lower_left_widget)
        self.image_area_container.setStyleSheet("background-color: yellow;")  # 设置按钮容器的背景颜色
        # 设置按钮容器的固定宽度
        self.image_area_container.setFixedWidth(100)  # 这里设置为100像素
        self.lower_left_widget.setLayout(self.image_area_container)

        # 下半区 控制区
        self.control_layout = QVBoxLayout(self.lower_right_widget)
       
        self.load_button1 = PushButton('Load Image1', self.lower_right_widget)
        self.load_button2 = PushButton('Load Image2', self.lower_right_widget)

        self.slider1 = Slider(Qt.Orientation.Horizontal, self)
        self.slider1.setFixedWidth(200)
        self.slider1.move(50, 30)

        # self.load_button1.clicked.connect(self.loadImage())

        self.control_layout.addWidget(self.load_button1)
        self.control_layout.addWidget(self.load_button2)
        self.control_layout.addWidget(self.slider1)

        self.lower_left_layout = QVBoxLayout(self.lower_left_widget)
        
        self.lower_left_layout.addStretch()
        
        self.lower_widget.setLayout(self.lower_layout)
        self.lower_left_widget.setLayout(self.lower_left_layout)
        self.lower_right_widget.setLayout(self.control_layout)

        self.setLayout(self.layout)

    def loadImage(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Image1", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)")
        
        if file_name:
            pixmap = QPixmap(file_name)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), aspectRatioMode=True))
