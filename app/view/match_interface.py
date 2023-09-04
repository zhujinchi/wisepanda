# coding:utf-8
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, QVBoxLayout, QWidget, QSlider, QHBoxLayout, QGroupBox, QSplitter, QSizePolicy, QFrame
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

        self.dragging = False
        self.offset = None

        self.layout = QVBoxLayout()

        # 上半区 列表区
        self.top_widget = QWidget(self)
        self.top_layout = QVBoxLayout(self.top_widget)
        self.top_widget.setStyleSheet("background-color: rgb(50, 50, 50); border: 0.3px solid rgb(29, 29, 29); border-radius: 5px;")
        self.top_widget.setMinimumHeight(80)

        # 下半区
        self.bottom_widget = QWidget(self)
        self.bottom_layout = QHBoxLayout(self.bottom_widget)
        self.bottom_widget.setStyleSheet("background-color: rgb(51, 51, 51); border: 0.4px solid rgb(29, 29, 29); border-radius: 5px;")
        self.bottom_widget.setMinimumHeight(660) 
       

        # 下半区 控制区
        self.control_widget = QWidget(self.bottom_widget) # 左区 控制区
        self.control_widget.setStyleSheet("background-color: rgb(36, 36, 36); border: 0.4px solid rgb(36, 36, 36);border-radius: 5px;")  # 设置背景颜色
        self.control_widget.setFixedWidth(240)  # 设置固定宽度
        self.control_widget.setMinimumHeight(660)
        # self.control_widget.setMaximumHeight(680)

        # 下半区 图片区
        self.images_widget = QWidget(self.bottom_widget) # 右区 图片区
        self.images_widget.setStyleSheet("background-color: transparent; border: 0px") 
        
        # 图片区组件群
        self.images_layout = QVBoxLayout()

        # 图片1
        self.image_label1 = QLabel(self)
        self.image_label1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label1.setStyleSheet("background-color: lightblue; border-radius: 0px;") 
        self.image_label1.setFixedSize(600, 200)

        # 图片1连接鼠标事件
        self.image_label1.mousePressEvent = self.mousePressEvent1
        self.image_label1.mouseMoveEvent = self.mouseMoveEvent1

        # 图片2
        self.image_label2 = QLabel(self)
        self.image_label2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label2.setStyleSheet("background-color: lightgreen; border-radius: 0px;") 
        self.image_label2.setFixedSize(600, 200)
        

        # 图片2连接鼠标事件
        self.image_label2.mousePressEvent = self.mousePressEvent2
        self.image_label2.mouseMoveEvent = self.mouseMoveEvent2


        self.images_layout.addWidget(self.image_label1)
        self.images_layout.addWidget(self.image_label2)

        self.images_widget.setLayout(self.images_layout)

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

        # 图片1大小控制
        self.zoom_widget1 = QWidget(self.control_widget)
        self.zoom_widget1_layout = QHBoxLayout(self.control_widget)
        self.zoomIn_button1 = PushButton('-', self.control_widget)
        self.zoomOut_button1 = PushButton('+', self.control_widget)

        zoom_widget1_line = QWidget(self)
        zoom_widget1_line.setStyleSheet("background-color: rgb(51, 51, 51); border: 0.4px solid rgb(29, 29, 29);")
        zoom_widget1_line.setFixedWidth(1) 

        self.zoom_widget1_layout.addWidget(self.zoomIn_button1)
        self.zoom_widget1_layout.addWidget(zoom_widget1_line)
        self.zoom_widget1_layout.addWidget(self.zoomOut_button1)

        self.zoom_widget1.setLayout(self.zoom_widget1_layout)

        # 图片2大小控制
        self.zoom_widget2 = QWidget(self.control_widget)
        self.zoom_widget2_layout = QHBoxLayout(self.control_widget)
        self.zoomIn_button2 = PushButton('-', self.control_widget)
        self.zoomOut_button2 = PushButton('+', self.control_widget)

        zoom_widget2_line = QWidget(self)
        zoom_widget2_line.setStyleSheet("background-color: rgb(51, 51, 51); border: 0.4px solid rgb(29, 29, 29);")
        zoom_widget2_line.setFixedWidth(1) 

        self.zoom_widget2_layout.addWidget(self.zoomIn_button2)
        self.zoom_widget2_layout.addWidget(zoom_widget2_line)
        self.zoom_widget2_layout.addWidget(self.zoomOut_button2)

        self.zoom_widget2.setLayout(self.zoom_widget2_layout)

        # 导出按钮
        self.output_button = PushButton('匹配确定', self.control_widget)
        self.output_button.setFixedWidth(180)


        # 创建分隔线
        self.line1_widget = QWidget(self)
        self.line1_widget.setStyleSheet("background-color: rgb(51, 51, 51); border: 0.4px solid rgb(29, 29, 29);")
        self.line1_widget.setFixedHeight(1) 

        self.line2_widget = QWidget(self)
        self.line2_widget.setStyleSheet("background-color: rgb(51, 51, 51); border: 0.4px solid rgb(29, 29, 29);")
        self.line2_widget.setFixedHeight(1) 

        # 组件加载到layout
        self.control_layout.addSpacing(10)
        self.control_layout.addWidget(BodyLabel('导入图片一'))
        self.control_layout.addWidget(self.load_button1, 0, Qt.AlignmentFlag.AlignHCenter)

        self.control_layout.addWidget(BodyLabel('图片一透明度'))
        self.control_layout.addSpacing(10)
        self.control_layout.addWidget(self.slider1, 0, Qt.AlignmentFlag.AlignHCenter)
        self.control_layout.addSpacing(10)

        self.control_layout.addWidget(BodyLabel('图片一缩放'))
        self.control_layout.addWidget(self.zoom_widget1, 0, Qt.AlignmentFlag.AlignHCenter)

        
        self.control_layout.addSpacing(10)
        self.control_layout.addWidget(self.line1_widget)
        self.control_layout.addSpacing(20)

        self.control_layout.addWidget(BodyLabel('导入图片二'))
        self.control_layout.addWidget(self.load_button2, 0, Qt.AlignmentFlag.AlignHCenter)

        self.control_layout.addWidget(BodyLabel('图片二透明度'))
        self.control_layout.addSpacing(10)
        self.control_layout.addWidget(self.slider2, 0, Qt.AlignmentFlag.AlignHCenter)
        self.control_layout.addSpacing(10)

        self.control_layout.addWidget(BodyLabel('图片二缩放'))
        self.control_layout.addWidget(self.zoom_widget2, 0, Qt.AlignmentFlag.AlignHCenter)

        self.control_layout.addSpacing(10)
        self.control_layout.addWidget(self.line2_widget)
        self.control_layout.addWidget(self.output_button, 0, Qt.AlignmentFlag.AlignHCenter)
        
        self.control_layout.addStretch(1)

        # 图片区组件群

        # self.lower_left_layout = QVBoxLayout(self.lower_left_widget)
        
        # self.lower_widget.setLayout(self.lower_layout)
        
        # self.lower_right_widget.setLayout(self.control_layout)

        self.control_widget.setLayout(self.control_layout)

        # 下半区加载到layout
        self.bottom_layout.addWidget(self.control_widget)
        self.bottom_layout.addWidget(self.images_widget)
        
        self.layout.addWidget(self.top_widget)
        self.layout.addWidget(self.bottom_widget)

        self.setLayout(self.layout)

    def loadImage(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select Image1", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)")
        
        if file_name:
            pixmap = QPixmap(file_name)
            self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), aspectRatioMode=True))
    
    # 图片鼠标拽动事件
    def mousePressEvent1(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position1 = event.globalPosition().toPoint() - self.image_label1.pos()

    def mouseMoveEvent1(self, event):
        if hasattr(self, 'drag_start_position1') and self.drag_start_position1:
            new_position = event.globalPosition().toPoint() - self.drag_start_position1
            self.image_label1.move(new_position)

    def mouseReleaseEvent1(self, event):
        if hasattr(self, 'drag_start_position1'):
            del self.drag_start_position1

    def mousePressEvent2(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position2 = event.globalPosition().toPoint() - self.image_label2.pos()

    def mouseMoveEvent2(self, event):
        if hasattr(self, 'drag_start_position2') and self.drag_start_position2:
            new_position = event.globalPosition().toPoint() - self.drag_start_position2
            self.image_label2.move(new_position)

    def mouseReleaseEvent2(self, event):
        if hasattr(self, 'drag_start_position2'):
            del self.drag_start_position2