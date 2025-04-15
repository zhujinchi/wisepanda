# coding:utf-8
import sys
import time
from PyQt6.QtCore import Qt, QPoint, QCoreApplication, pyqtSignal, QEasingCurve, QDateTime
from PyQt6.QtWidgets import QScrollArea, QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, QVBoxLayout, QWidget, QSlider, QHBoxLayout, QGroupBox, QSplitter, QSizePolicy, QFrame, QGraphicsOpacityEffect
from PyQt6.QtGui import QPixmap, QImage, QBitmap, QColor, QWheelEvent
from qfluentwidgets import InfoBar, InfoBarIcon, InfoBarPosition, SingleDirectionScrollArea, SmoothScrollArea, \
    ScrollArea, HollowHandleStyle, Slider, setTheme, Theme, PushButton, BodyLabel, IconWidget, TextWrap, FlowLayout, \
    CardWidget

from .gallery_interface import GalleryInterface
from ..common.singleton_output import Singleton_output
from ..common.singleton_result import Singleton_result
from ..common.singleton_img import Singleton_img

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


class ImageWidget(CardWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.data_provider = Singleton_result()
        self.data_changer = Singleton_output()
        self.data_provider.list_changed.connect(self.updateResultList)
        self.img_provider = Singleton_img()
        self.img_provider.dir_changed.connect(self.chooseImage1)

        self.original_pixmap1 = None  # 存储原始加载的图片
        self.original_pixmap2 = None  # 存储原始加载的图片
        self.image_label1_position = QPoint(0, 0)  # 记录图片的当前位置
        self.image_label2_position = QPoint(0, 0)  # 记录图片的当前位置

        self.output_image1 = ''
        self.output_image2 = ''


        self.layout = QVBoxLayout()

        # 上半区 列表区
        self.top_widget = CardWidget(self)
        self.top_layout = QVBoxLayout(self.top_widget)
        self.top_widget.setFixedHeight(140)

        # 在 self.top_widget 上创建一个横向滚动的页面
        scroll_area = SingleDirectionScrollArea(self.top_widget, Qt.Orientation.Horizontal)
        scroll_area.setWidgetResizable(True)  # 使滚动区域的内容自适应大小
        # scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)  # 显示水平滚动条

        # 创建一个容器 widget，作为滚动内容的容器
        scroll_content = CardWidget()
        scroll_area.setWidget(scroll_content)

        # 创建一个水平布局来容纳子 widget
        self.result_layout = QHBoxLayout(scroll_content)

        # 创建 widget
        self.image_list = ['/Users/angzeng/GitHub/Defragment-Neural-Network/data/origin_data/0_1.png', '/Users/angzeng/Documents/缀合网络相关/trainval/107/240-05-01.png']

        # 添加一系列的子 widget
        for i in range(0):
            child_widget =  SampleCard(self.image_list[1], 'score: 10.56', i, self)
            child_widget.clicked.connect(lambda: self.chooseImage2(self.image_list[1]))
            self.result_layout.addWidget(child_widget)

        # 设置容器 widget 的布局
        scroll_content.setLayout(self.result_layout)

        # 添加滚动区域到 self.top_layout 中
        self.top_layout.addWidget(scroll_area)

        # 下半区
        self.bottom_widget = CardWidget(self)
        self.bottom_layout = QHBoxLayout(self.bottom_widget)
        self.bottom_widget.setMinimumHeight(655)

        # 下半区 控制区
        self.control_widget = CardWidget(self.bottom_widget) # 左区 控制区
        self.control_widget.setFixedWidth(240)  # 设置固定宽度
        self.control_widget.setMinimumHeight(630)
        # self.control_widget.setMaximumHeight(680)

        # 下半区 图片区
        self.images_widget = CardWidget(self.bottom_widget) # 右区 图片区
        self.images_widget.setStyleSheet("background-color: transparent; border: 0px")

        # 图片区组件群
        self.images_layout = QVBoxLayout()

        # 图片1
        self.image_label1 = ZoomableLabel(self)
        # 图片1连接鼠标事件
        self.image_label1.mousePressEvent = self.mousePressEvent1
        self.image_label1.mouseMoveEvent = self.mouseMoveEvent1
        self.image_label1.wheelScrolled.connect(self.onWheelScrolled1)
        # 图片2
        self.image_label2 = ZoomableLabel(self)

        # 图片2连接鼠标事件
        self.image_label2.mousePressEvent = self.mousePressEvent2
        self.image_label2.mouseMoveEvent = self.mouseMoveEvent2
        self.image_label2.wheelScrolled.connect(self.onWheelScrolled2)

        # 初始化透明度效果
        self.opacityEffect1 = QGraphicsOpacityEffect()
        self.opacityEffect2 = QGraphicsOpacityEffect()
        self.image_label1.setGraphicsEffect(self.opacityEffect1)
        self.image_label2.setGraphicsEffect(self.opacityEffect2)

        # 设置初始透明度
        self.opacityEffect1.setOpacity(1.0)  # 初始透明度为1.0
        self.opacityEffect2.setOpacity(1.0)  # 初始透明度为1.0

        # 设置初始大小
        self.current_scale1 = 1.0
        self.current_scale2 = 1.0


        self.images_layout.addWidget(self.image_label1)
        self.images_layout.addWidget(self.image_label2)

        self.images_widget.setLayout(self.images_layout)


        # 控制区组件群
        self.control_layout = QVBoxLayout(self.control_widget)

        self.load_button1 = PushButton('LoadImg1', self.control_widget)
        self.load_button1.setFixedWidth(180)
        self.load_button1.clicked.connect(self.loadImage1) # 上传按钮连接事件

        self.load_button2 = PushButton('LoadImg2', self.control_widget)
        self.load_button2.setFixedWidth(180)
        self.load_button2.clicked.connect(self.loadImage2) # 上传按钮连接事件

        # 图片1透明度控制
        self.slider1 = Slider(Qt.Orientation.Horizontal, self)
        self.slider1.setFixedWidth(180)
        self.slider1.setValue(100)
        self.slider1.valueChanged.connect(self.setOpacity1) # 连接 slider1 的值变化事件到透明度控制方法

        # 图片2透明度控制
        self.slider2 = Slider(Qt.Orientation.Horizontal, self)
        self.slider2.setFixedWidth(180)
        self.slider2.setValue(100)
        self.slider2.valueChanged.connect(self.setOpacity2) # 连接 slider2 的值变化事件到透明度控制方法

        # 图片1大小控制
        self.zoom_widget1 = CardWidget(self.control_widget)
        self.zoom_widget1_layout = QHBoxLayout(self.control_widget)
        self.zoomOut_button1 = PushButton('-', self.control_widget)
        self.zoomIn_button1 = PushButton('+', self.control_widget)
        # 连接 zoom_widget1 的按钮点击事件到大小控制方法
        self.zoomOut_button1.clicked.connect(self.zoomOut1)
        self.zoomIn_button1.clicked.connect(self.zoomIn1)

        zoom_widget1_line = CardWidget(self)
        zoom_widget1_line.setFixedWidth(1)

        self.zoom_widget1_layout.addWidget(self.zoomOut_button1)
        self.zoom_widget1_layout.addWidget(zoom_widget1_line)
        self.zoom_widget1_layout.addWidget(self.zoomIn_button1)

        self.zoom_widget1.setLayout(self.zoom_widget1_layout)

        # 图片2大小控制
        self.zoom_widget2 = CardWidget(self.control_widget)
        self.zoom_widget2_layout = QHBoxLayout(self.control_widget)
        self.zoomOut_button2 = PushButton('-', self.control_widget)
        self.zoomIn_button2 = PushButton('+', self.control_widget)
         # 连接 zoom_widget1 的按钮点击事件到大小控制方法
        self.zoomOut_button2.clicked.connect(self.zoomOut2)
        self.zoomIn_button2.clicked.connect(self.zoomIn2)

        zoom_widget2_line = CardWidget(self)
        zoom_widget2_line.setFixedWidth(1)

        self.zoom_widget2_layout.addWidget(self.zoomOut_button2)
        self.zoom_widget2_layout.addWidget(zoom_widget2_line)
        self.zoom_widget2_layout.addWidget(self.zoomIn_button2)

        self.zoom_widget2.setLayout(self.zoom_widget2_layout)

        # 导出按钮
        self.output_button = PushButton('匹配确定', self.control_widget)
        self.output_button.setFixedWidth(180)
        self.output_button.clicked.connect(self.outputList)

        # 创建分隔线
        self.line1_widget = CardWidget(self)
        self.line1_widget.setFixedHeight(1)

        self.line2_widget = CardWidget(self)
        self.line2_widget.setFixedHeight(1)

        # 组件加载到layout
        self.control_layout.addSpacing(10)
        self.control_layout.addWidget(BodyLabel('导入图片一'))
        self.control_layout.addWidget(self.load_button1, 0, Qt.AlignmentFlag.AlignHCenter)
        self.control_layout.addWidget(BodyLabel('图片一透明度'))
        self.control_layout.addSpacing(5)
        self.control_layout.addWidget(self.slider1, 0, Qt.AlignmentFlag.AlignHCenter)
        self.control_layout.addSpacing(10)
        self.control_layout.addWidget(BodyLabel('图片一缩放'))
        self.control_layout.addWidget(self.zoom_widget1, 0, Qt.AlignmentFlag.AlignHCenter)
        self.control_layout.addSpacing(5)
        self.control_layout.addWidget(self.line1_widget)
        self.control_layout.addSpacing(10)
        self.control_layout.addWidget(BodyLabel('导入图片二'))
        self.control_layout.addWidget(self.load_button2, 0, Qt.AlignmentFlag.AlignHCenter)
        self.control_layout.addWidget(BodyLabel('图片二透明度'))
        self.control_layout.addSpacing(5)
        self.control_layout.addWidget(self.slider2, 0, Qt.AlignmentFlag.AlignHCenter)
        self.control_layout.addSpacing(10)
        self.control_layout.addWidget(BodyLabel('图片二缩放'))
        self.control_layout.addWidget(self.zoom_widget2, 0, Qt.AlignmentFlag.AlignHCenter)
        self.control_layout.addSpacing(5)
        self.control_layout.addWidget(self.line2_widget)
        self.control_layout.addWidget(self.output_button, 0, Qt.AlignmentFlag.AlignHCenter)
        self.control_layout.addStretch(1)

        self.control_widget.setLayout(self.control_layout)

        # 下半区加载到layout
        self.bottom_layout.addWidget(self.control_widget)
        self.bottom_layout.addWidget(self.images_widget)

        self.layout.addWidget(self.top_widget)
        self.layout.addWidget(self.bottom_widget)

        self.setLayout(self.layout)

    def onWheelScrolled1(self, zoom_in: bool):
        if zoom_in:
            self.zoomIn1()
        else:
            self.zoomOut1()

    def onWheelScrolled2(self, zoom_in: bool):
        if zoom_in:
            self.zoomIn2()
        else:
            self.zoomOut2()

    # 更新result_list的方法
    def updateResultList(self, img_list):
        # 清除现有子widget
        for i in reversed(range(self.result_layout.count())):
            widget = self.result_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # 创建新的子widget #A修改
        for i, image_score_path in enumerate(img_list):
            print(list[0])
            print(image_score_path[1])
            child_widget = SampleCard(image_score_path[1], f'score: {image_score_path[0]}', i, self)
            child_widget.clicked.connect(lambda path=image_score_path[1]: self.chooseImage2(path))
            self.result_layout.addWidget(child_widget)

        # 更新布局
        self.result_layout.update()

    # 图片1加载方法
    def loadImage1(self):
            file_name, _ = QFileDialog.getOpenFileName(self, "Select Image1", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)")
            print(file_name)
            if file_name:
                self.output_image1 = file_name
                self.original_pixmap1 = QPixmap(file_name)  # 存储原始加载的图片
                self.image_label1.setPixmap(self.original_pixmap1)
                self.image_label1.setFixedSize(self.original_pixmap1.size())  # 设置image_label1的大小与图片大小一致
            #     InfoBar.success(
            #     title='提示消息',
            #     content="图片1加载成功。",
            #     orient=Qt.Orientation.Horizontal,
            #     isClosable=True,
            #     position=InfoBarPosition.BOTTOM_RIGHT,
            #     duration=1000,    # won't disappear automatically
            #     parent=self
            # )

    def chooseImage1(self, file_name):
        self.output_image1 = file_name
        if file_name:
            # 加载图像为 QImage，并确保是带 alpha 通道的格式
            image = QImage(file_name).convertToFormat(QImage.Format.Format_ARGB32)

            # 遍历每个像素，将白色背景改为透明
            for y in range(image.height()):
                for x in range(image.width()):
                    color = image.pixelColor(x, y)
                    # 判断是否为接近白色，可以调节容差（下面是 RGB > 240 判定为白）
                    if color.red() > 230 and color.green() > 230 and color.blue() > 230:
                        color.setAlpha(0)
                        image.setPixelColor(x, y, color)

            left, top, right, bottom = image.width(), image.height(), 0, 0
            for y in range(image.height()):
                for x in range(image.width()):
                    if image.pixelColor(x, y).alpha() > 0:  # 非透明区域
                        left = min(left, x)
                        top = min(top, y)
                        right = max(right, x)
                        bottom = max(bottom, y)

                # 截取有效区域（去除透明边缘）
            cropped_image = image.copy(left, top, right - left + 1, bottom - top + 1)

            # 转换为 QPixmap
            self.original_pixmap1 = QPixmap.fromImage(cropped_image)
            self.image_label1.setPixmap(self.original_pixmap1)
            self.image_label1.setFixedSize(self.original_pixmap1.size())
            self.image_label1.repaint()

            InfoBar.success(
                title='提示消息',
                content="图片1加载成功",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1000,
                parent=self
            )

    def chooseImage2(self, file_name):
        self.output_image2 = file_name
        if file_name:
            # 加载图像为 QImage，并确保是带 alpha 通道的格式
            image = QImage(file_name).convertToFormat(QImage.Format.Format_ARGB32)

            # 遍历每个像素，将白色背景变成透明
            for y in range(image.height()):
                for x in range(image.width()):
                    color = image.pixelColor(x, y)
                    if color.red() > 240 and color.green() > 240 and color.blue() > 240:
                        color.setAlpha(0)
                        image.setPixelColor(x, y, color)

            left, top, right, bottom = image.width(), image.height(), 0, 0
            for y in range(image.height()):
                for x in range(image.width()):
                    if image.pixelColor(x, y).alpha() > 0:  # 非透明区域
                        left = min(left, x)
                        top = min(top, y)
                        right = max(right, x)
                        bottom = max(bottom, y)

                # 截取有效区域（去除透明边缘）
            cropped_image = image.copy(left, top, right - left + 1, bottom - top + 1)

            # 转换为 QPixmap 显示
            self.original_pixmap2 = QPixmap.fromImage(cropped_image)
            self.image_label2.setPixmap(self.original_pixmap2)
            self.image_label2.setFixedSize(self.original_pixmap2.size())
            self.image_label2.repaint()

            InfoBar.success(
                title='提示消息',
                content="图片2加载成功，白色背景已设为透明。",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self
            )


    # 图片2加载方法
    def loadImage2(self):
            file_name, _ = QFileDialog.getOpenFileName(self, "Select Image2", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)")
            if file_name:
                self.output_image2 = file_name
                self.original_pixmap2 = QPixmap(file_name)  # 存储原始加载的图片
                self.image_label2.setPixmap(self.original_pixmap2)
                self.image_label2.setFixedSize(self.original_pixmap2.size())  # 设置image_label1的大小与图片大小一致
                InfoBar.success(
                title='提示消息',
                content="图片2加载成功。",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,    # won't disappear automatically
                parent=self
            )

    # 图片2加载方法
    def outputList(self):
            #old_list = self.data_provider._instance.get_output_list()
            # sample ['219-08-02.png', '224-10-01.png', '/Users/angzeng/Documents/缀合网络相关/trainval/100', '/Users/angzeng/Documents/缀合网络相关/trainval/100', '2023/09/09/20:34'],
            if self.output_image1 == '' or self.output_image2 == '':
                InfoBar.warning(
                title='导出错误',
                content="图片地址为空",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,    # won't disappear automatically
                parent=self
            )
            else:
                now = int(round(time.time()*1000))
                nowTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(now/1000))
                new_list = [self.output_image1, self.output_image2, 'None info', 'None info', nowTime],

                self.data_changer._instance.set_result_list(new_list)

                InfoBar.success(
                title='提示消息',
                content="匹配项置入导出列表。",
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,    # won't disappear automatically
                parent=self
            )

    # 图片1透明度方法
    def setOpacity1(self, value):
        opacity = value / 100.0  # 将 slider1 的值映射到透明度范围 0.0 - 1.0
        self.opacityEffect1.setOpacity(opacity)
        self.image_label1.setGraphicsEffect(self.opacityEffect1)

    # 图片2透明度方法
    def setOpacity2(self, value):
        opacity = value / 100.0  # 将 slider1 的值映射到透明度范围 0.0 - 1.0
        self.opacityEffect2.setOpacity(opacity)
        self.image_label2.setGraphicsEffect(self.opacityEffect2)

    # 图片1缩放方法
    def zoomIn1(self):
        if self.original_pixmap1 is not None:
            self.current_scale1 += 0.1  # 增加0.1倍
            pixmap = self.original_pixmap1
            scaled_pixmap = pixmap.scaled(pixmap.size() * self.current_scale1, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
            self.image_label1.setPixmap(scaled_pixmap)
            self.image_label1.setFixedSize(scaled_pixmap.size())
            # 等待setFixedSize执行完成
            QCoreApplication.processEvents()
            # 设置图片的位置为记录的位置
            self.image_label1.move(self.image_label1_position)
            self.image_label2.move(self.image_label2_position)

    def zoomOut1(self):
        if self.original_pixmap1 is not None:
            self.current_scale1 -= 0.1  # 减小0.1倍
            pixmap = self.original_pixmap1
            scaled_pixmap = pixmap.scaled(pixmap.size() * self.current_scale1, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
            self.image_label1.setPixmap(scaled_pixmap)
            self.image_label1.setFixedSize(scaled_pixmap.size())
            # 等待setFixedSize执行完成
            QCoreApplication.processEvents()
            # 设置图片的位置为记录的位置
            self.image_label1.move(self.image_label1_position)
            self.image_label2.move(self.image_label2_position)

    # 图片2缩放方法
    def zoomIn2(self):
        if self.original_pixmap2 is not None:
            self.current_scale2 += 0.1  # 增加0.1倍
            pixmap = self.original_pixmap2
            scaled_pixmap = pixmap.scaled(pixmap.size() * self.current_scale2, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
            self.image_label2.setPixmap(scaled_pixmap)
            self.image_label2.setFixedSize(scaled_pixmap.size())
            # 等待setFixedSize执行完成
            QCoreApplication.processEvents()
            # 设置图片的位置为记录的位置
            self.image_label1.move(self.image_label1_position)
            self.image_label2.move(self.image_label2_position)

    def zoomOut2(self):
        if self.original_pixmap2 is not None:
            self.current_scale2 -= 0.1  # 减小0.1倍
            pixmap = self.original_pixmap2
            scaled_pixmap = pixmap.scaled(pixmap.size() * self.current_scale2, aspectRatioMode=Qt.AspectRatioMode.KeepAspectRatio)
            self.image_label2.setPixmap(scaled_pixmap)
            self.image_label2.setFixedSize(scaled_pixmap.size())
            # 等待setFixedSize执行完成
            QCoreApplication.processEvents()
            # 设置图片的位置为记录的位置
            self.image_label1.move(self.image_label1_position)
            self.image_label2.move(self.image_label2_position)

    # 图片鼠标拽动事件
    def mousePressEvent1(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_start_position1 = event.globalPosition().toPoint() - self.image_label1.pos()

    def mouseMoveEvent1(self, event):
        if hasattr(self, 'drag_start_position1') and self.drag_start_position1:
            new_position = event.globalPosition().toPoint() - self.drag_start_position1
            self.image_label1.move(new_position)

            # 更新 self.image_label1_position
            self.image_label1_position = self.image_label1.pos()

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

            # 更新 self.image_label2_position
            self.image_label2_position = self.image_label2.pos()

    def mouseReleaseEvent2(self, event):
        if hasattr(self, 'drag_start_position2'):
            del self.drag_start_position2

class SampleCard(QFrame):
    """ Sample card """

    clicked = pyqtSignal()  # 创建一个点击信号

    def __init__(self, icon, content, index, parent=None):
        super().__init__(parent=parent)

        self.index = index
        self.title = f"排名: {index+1}"
        self.icon = icon

        self.iconWidget = IconWidget(icon, self)
        self.titleLabel = QLabel(self.title, self)
        self.contentLabel = QLabel(TextWrap.wrap(content, 45, False)[0], self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.setFixedSize(200, 90)
        self.iconWidget.setFixedSize(48, 48)


        self.hBoxLayout.setSpacing(28)
        self.hBoxLayout.setContentsMargins(20, 0, 0, 0)
        self.vBoxLayout.setSpacing(2)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        self.hBoxLayout.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.hBoxLayout.addWidget(self.iconWidget)
        self.hBoxLayout.addLayout(self.vBoxLayout)
        self.vBoxLayout.addStretch(1)
        self.vBoxLayout.addWidget(self.titleLabel)
        self.vBoxLayout.addWidget(self.contentLabel)
        self.vBoxLayout.addStretch(1)

        self.titleLabel.setObjectName('titleLabel')
        self.contentLabel.setObjectName('contentLabel')

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.clicked.emit()

class ZoomableLabel(QLabel):
    wheelScrolled = pyqtSignal(bool)  # True = 放大，False = 缩小

    def __init__(self, parent=None):
        super().__init__(parent)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(True)
        self.image_label.setStyleSheet("background-color: transparent; border-radius: 0px;")
        self.image_label.setMinimumSize(600, 200)


    def wheelEvent(self, event: QWheelEvent):
        if event.angleDelta().y() > 0:
            self.wheelScrolled.emit(True)   # 向上滚动 = 放大
        else:
            self.wheelScrolled.emit(False)  # 向下滚动 = 缩小


