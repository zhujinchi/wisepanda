# coding:utf-8
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, QVBoxLayout, QWidget, QSlider, QHBoxLayout, QGroupBox, QSplitter, QSizePolicy
from PyQt6.QtGui import QPixmap, QImage, QBitmap, QColor
from qfluentwidgets import ScrollArea, HollowHandleStyle, Slider, setTheme, Theme, PushButton, BodyLabel


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
        self.top_widget = QWidget(self)
        self.top_layout = QVBoxLayout(self.top_widget)
        self.top_widget.setStyleSheet("background-color: rgb(50, 50, 50); border: 0.3px solid rgb(29, 29, 29); border-radius: 5px;")
        self.top_widget.setMinimumHeight(100)
        
        self.layout.addWidget(self.top_widget)

        # 下半区
        self.bottom_widget = QWidget(self)
        self.bottom_layout = QHBoxLayout(self.bottom_widget)
        self.bottom_widget.setStyleSheet("background-color: rgb(51, 51, 51); border: 0.4px solid rgb(29, 29, 29); border-radius: 5px;")
        self.bottom_widget.setMinimumHeight(700) 
       

        # 下半区 控制区
        self.control_widget = QWidget(self.bottom_widget) # 左区 控制区
        self.control_widget.setStyleSheet("background-color: rgb(36, 36, 36); border: 0.4px solid rgb(36, 36, 36);border-radius: 5px;")  # 设置背景颜色
        self.control_widget.setFixedWidth(240)  # 设置固定宽度

        # 下半区 图片区
        self.images_widget = QWidget(self.bottom_widget) # 右区 图片区
        self.images_widget.setStyleSheet("background-color: transparent; border: 0px") 
        

        

        # 控制区组件群
        self.control_layout = QVBoxLayout(self.control_widget)
       
        self.load_button1 = PushButton('LoadImg1', self.control_widget)
        self.load_button1.setFixedWidth(180)
        
        # self.load_button1.clicked.connect(self.loadImage())

        self.load_button2 = PushButton('LoadImg2', self.control_widget)
        self.load_button2.setFixedWidth(180)
       
        
        # 图片1透明度控制
        self.slider1 = Slider(Qt.Orientation.Horizontal, self)
        self.slider1.setFixedWidth(180)
        

        # 图片2透明度控制
        self.slider2 = Slider(Qt.Orientation.Horizontal, self)
        self.slider2.setFixedWidth(180)


        # 组件加载到layout
        self.control_layout.addWidget(BodyLabel('导入图片一'))
        self.control_layout.addWidget(self.load_button1, 0, Qt.AlignmentFlag.AlignHCenter)
        
        self.control_layout.addWidget(BodyLabel('导入图片二'))
        self.control_layout.addWidget(self.load_button2, 0, Qt.AlignmentFlag.AlignHCenter)
        
        self.control_layout.addSpacing(20)

        self.control_layout.addWidget(BodyLabel('图片一透明度'))
        self.control_layout.addSpacing(10)
        self.control_layout.addWidget(self.slider1, 0, Qt.AlignmentFlag.AlignHCenter)
        self.control_layout.addSpacing(10)

        self.control_layout.addWidget(BodyLabel('图片二透明度'))
        self.control_layout.addSpacing(10)
        self.control_layout.addWidget(self.slider2, 0, Qt.AlignmentFlag.AlignHCenter)
        self.control_layout.addSpacing(10)
        
        self.control_layout.addStretch(1)

        # 图片区组件群

        # self.lower_left_layout = QVBoxLayout(self.lower_left_widget)
        
        # self.lower_widget.setLayout(self.lower_layout)
        
        # self.lower_right_widget.setLayout(self.control_layout)

        self.control_widget.setLayout(self.control_layout)

        # 下半区加载到layout
        self.bottom_layout.addWidget(self.control_widget)
        self.bottom_layout.addWidget(self.images_widget)
        
        
        self.layout.addWidget(self.bottom_widget)

        self.setLayout(self.layout)

    def loadImage(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Image1", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)")
        
        if file_name:
            pixmap = QPixmap(file_name)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), aspectRatioMode=True))
