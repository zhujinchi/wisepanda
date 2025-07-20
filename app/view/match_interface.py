# coding:utf-8
import os
import sqlite3
import sys
import time
from operator import truediv

from PyQt6.QtCore import Qt, QPoint, QCoreApplication, pyqtSignal, QEasingCurve, QDateTime, QRectF
from PyQt6.QtWidgets import QScrollArea, QApplication, QMainWindow, QPushButton, QLabel, QFileDialog, QVBoxLayout, \
    QWidget, QSlider, QHBoxLayout, QGroupBox, QSplitter, QSizePolicy, QFrame, QGraphicsOpacityEffect, \
    QGraphicsPixmapItem, QGraphicsView, QGraphicsScene, QGraphicsItem, QComboBox
from PyQt6.QtGui import QPixmap, QImage, QBitmap, QColor, QWheelEvent, QPainter, QKeyEvent
from adodbapi.ado_consts import directions
from qfluentwidgets import InfoBar, InfoBarIcon, InfoBarPosition, SingleDirectionScrollArea, SmoothScrollArea, \
    ScrollArea, HollowHandleStyle, Slider, setTheme, Theme, PushButton, BodyLabel, IconWidget, TextWrap, FlowLayout, \
    CardWidget

from .gallery_interface import GalleryInterface
from ..common.matchdb import MatchDB
from ..common.singleton_output import Singleton_output
from ..common.singleton_result import Singleton_result
from ..common.singleton_img import Singleton_img

class MatchInterface(GalleryInterface):
    """ Match interface """

    def __init__(self, parent=None):
        super().__init__(
            title=self.tr('匹配区'),
            parent=parent
            )
        self.setObjectName('matchInterface')

        self.matchView = ImageWidget()

        self.vBoxLayout.addWidget(self.matchView)


class ImageWidget(CardWidget):
    def __init__(self):
        super().__init__()
        self.filter = None
        self.matchdb = MatchDB()
        self.conn = sqlite3.connect('annotations.db')
        self.current_index = None
        self.initUI()

    def initUI(self):
        self.data_provider = Singleton_result()
        self.data_changer = Singleton_output()
        self.data_provider.list_changed.connect(self.updateResultList)
        self.img_provider = Singleton_img()
        self.img_provider.dir_changed.connect(self.chooseImage1)
        self.data_provider.bool_signal.connect(self.set_bool)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.original_pixmap1 = None  # 存储原始加载的图片
        self.original_pixmap2 = None  # 存储原始加载的图片
        self.path_to_index = {}
        self.index_to_path = {}
        self.curr_index = -1
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
            path = self.image_list[1]
            # 建立映射
            self.path_to_index[path] = i
            self.index_to_path[i] = path
            child_widget =  SampleCard(self.image_list[1], 'score: 10.56', i, self)
            child_widget.clicked.connect(lambda: self.chooseImage2(i))
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
        self.images_widget = CardWidget(self.bottom_widget)
        self.images_widget.setStyleSheet("background-color: #ffebcc; border: 0px")

        # 一个 QGraphicsView
        self.shared_view = ZoomableGraphicsView(self)

        # 共享的场景
        self.scene = QGraphicsScene(self)
        self.shared_view.setScene(self.scene)

        # 两个图片项
        self.pixmap_item1 = QGraphicsPixmapItem()
        self.pixmap_item2 = QGraphicsPixmapItem()

        # 设置可移动 + 可选择 + 可变形
        flags = QGraphicsItem.GraphicsItemFlag.ItemIsMovable | \
                QGraphicsItem.GraphicsItemFlag.ItemIsSelectable | \
                QGraphicsItem.GraphicsItemFlag.ItemIsFocusable

        self.pixmap_item1.setFlags(flags)
        self.pixmap_item2.setFlags(flags)

        # 添加到场景中
        self.scene.addItem(self.pixmap_item1)
        self.scene.addItem(self.pixmap_item2)

        # 设置初始位置，避免重叠
        self.pixmap_item1.setPos(0, 0)
        self.pixmap_item2.setPos(400, 0)

        # 放入界面布局
        self.images_layout = QVBoxLayout()
        self.images_layout.addWidget(self.shared_view)
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
        self.output_button = PushButton(self.tr('匹配确定'), self.control_widget)
        self.output_button.setFixedWidth(180)
        self.output_button.clicked.connect(self.outputList)

        self.filterCombo = QComboBox()
        self.filterCombo.addItems(["没有墨迹", "上方有墨迹", "下方有墨迹"])
        self.filterCombo.currentIndexChanged.connect(self.applyFilter)

        # 创建分隔线
        self.line1_widget = CardWidget(self)
        self.line1_widget.setFixedHeight(1)

        self.line2_widget = CardWidget(self)
        self.line2_widget.setFixedHeight(1)

        # 组件加载到layout
        self.control_layout.addSpacing(10)
        self.control_layout.addWidget(BodyLabel(self.tr('导入图片一')))
        self.control_layout.addWidget(self.load_button1, 0, Qt.AlignmentFlag.AlignHCenter)
        self.control_layout.addWidget(BodyLabel(self.tr('图片一透明度')))
        self.control_layout.addSpacing(5)
        self.control_layout.addWidget(self.slider1, 0, Qt.AlignmentFlag.AlignHCenter)
        self.control_layout.addSpacing(10)
        self.control_layout.addWidget(BodyLabel(self.tr('图片一缩放')))
        self.control_layout.addWidget(self.zoom_widget1, 0, Qt.AlignmentFlag.AlignHCenter)
        self.control_layout.addSpacing(5)
        self.control_layout.addWidget(self.line1_widget)
        self.control_layout.addSpacing(10)
        self.control_layout.addWidget(BodyLabel(self.tr('导入图片二')))
        self.control_layout.addWidget(self.load_button2, 0, Qt.AlignmentFlag.AlignHCenter)
        self.control_layout.addWidget(BodyLabel(self.tr('图片二透明度')))
        self.control_layout.addSpacing(5)
        self.control_layout.addWidget(self.slider2, 0, Qt.AlignmentFlag.AlignHCenter)
        self.control_layout.addSpacing(10)
        self.control_layout.addWidget(BodyLabel(self.tr('图片二缩放')))
        self.control_layout.addWidget(self.zoom_widget2, 0, Qt.AlignmentFlag.AlignHCenter)
        self.control_layout.addSpacing(5)
        self.control_layout.addWidget(self.line2_widget)
        self.control_layout.addWidget(self.output_button, 0, Qt.AlignmentFlag.AlignHCenter)
        self.control_layout.addStretch(1)
        self.control_layout.addWidget(self.filterCombo, 0, Qt.AlignmentFlag.AlignHCenter)

        self.control_widget.setLayout(self.control_layout)

        # 下半区加载到layout
        self.bottom_layout.addWidget(self.control_widget)
        self.bottom_layout.addWidget(self.images_widget)

        self.layout.addWidget(self.top_widget)
        self.layout.addWidget(self.bottom_widget)

        self.setLayout(self.layout)

    def set_bool(self, value):
        self.is_upper = value

    def align_pixmaps_vertically(self):
        # 将 item2 的缩放设为与 item1 一致
        scale1 = self.pixmap_item1.scale()
        self.pixmap_item2.setScale(scale1)

        # 获取原始边界（未缩放）
        rect1 = self.pixmap_item1.boundingRect()
        rect2 = self.pixmap_item2.boundingRect()

        # 获取缩放后的边界
        width1_scaled = rect1.width() * scale1
        height1_scaled = rect1.height() * scale1
        width2_scaled = rect2.width() * scale1
        height2_scaled = rect2.height() * scale1

        # 获取 item1 的位置
        pos1 = self.pixmap_item1.pos()

        # 横向居中（以缩放后中心为准）
        center_x1 = pos1.x() + width1_scaled / 2
        new_x2 = center_x1 - width2_scaled / 2

        spacing = 5 * scale1  # 缩放后的动态间距（可调）

        if self.is_upper:
            # 放在 item1 上方
            new_y2 = pos1.y() - height2_scaled - spacing
        else:
            # 放在 item1 下方
            new_y2 = pos1.y() + height1_scaled + spacing

        # 设置 item2 的新位置
        self.pixmap_item2.setPos(new_x2, new_y2)


    # 更新result_list的方法
    def updateResultList(self, img_list):
        self.img_list = img_list
        # 清除现有子widget
        for i in reversed(range(self.result_layout.count())):
            widget = self.result_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # 创建新的子widget #A修改
        for i, image_score_path in enumerate(img_list):
            path = image_score_path[1]

            # 建立映射
            self.path_to_index[path] = i
            self.index_to_path[i] = path

            child_widget = SampleCard(image_score_path[1], f'score: {image_score_path[0]}', i, self)

            child_widget.clicked.connect(lambda idx=i: self.chooseImage2(idx))
            self.result_layout.addWidget(child_widget)

        # 更新布局
        self.result_layout.update()

    # 更新 filter
    def applyFilter(self):
        filter_type = self.filterCombo.currentText()

        # 清除现有子widget
        for i in reversed(range(self.result_layout.count())):
            widget = self.result_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        # 创建新的子widget
        for i, image_score_path in enumerate(self.img_list):
            path = image_score_path[1]
            self.path_to_index[path] = i
            self.index_to_path[i] = path

            child_widget = SampleCard(image_score_path[1], f'score: {image_score_path[0]}', i, self)
            child_widget.clicked.connect(lambda idx=i: self.chooseImage2(idx))


            if not hasattr(self, 'conn') or self.conn is None:
                raise ValueError("数据库连接不存在。")

            try:
                cursor = self.conn.execute('''
                    SELECT 墨迹 FROM annotations
                    WHERE image_path = ?
                ''', (path,))
                result = cursor.fetchone()
                # print(f"图像 {os.path.basename(path)} 墨迹字段: {result}")

                if result is None or not result[0]:  # 无记录或字段为空
                    if filter_type == "全部" or filter_type == "没有墨迹":
                        self.result_layout.addWidget(child_widget)
                    continue

                moji = result[0]

                if filter_type == "没有墨迹":
                    if "没有" in moji:
                        self.result_layout.addWidget(child_widget)

                elif filter_type == "下方有墨迹":
                    if "下方" in moji:
                        self.result_layout.addWidget(child_widget)

                elif filter_type == "上方有墨迹":
                    if "上方" in moji:
                        self.result_layout.addWidget(child_widget)

                elif filter_type == "全部":
                    self.result_layout.addWidget(child_widget)

            except Exception as db_err:
                print(f"[数据库错误] 图像路径: {path}")
                print(f"错误详情: {db_err}")

        self.result_layout.update()

    def showPrev(self):
        if self.curr_index>0:
            self.curr_index -= 1
            self.chooseImage2(self.curr_index)
        else:
            InfoBar.success(
                    title=self.tr('提示消息'),
                    content=self.tr("已经是第一张"),
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=500,
                    parent=self
                )

    def showNext(self):
        if self.curr_index<len(self.index_to_path):
            self.curr_index += 1
            self.chooseImage2(self.curr_index)
        else:
            InfoBar.success(
                    title=self.tr('提示消息'),
                    content=self.tr("已经是最后一张"),
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=500,
                    parent=self
            )

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Left:
            self.showPrev()
        elif event.key() == Qt.Key.Key_Right:
            self.showNext()


    # 图片1加载方法
    def loadImage1(self):
            file_name, _ = QFileDialog.getOpenFileName(self, "Select Image1", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)")
            print(file_name)
            if file_name:
                self.output_image1 = file_name
                pixmap = QPixmap(file_name)
                self.original_pixmap1 = pixmap
                self.pixmap_item1.setPixmap(pixmap)


    def chooseImage1(self, file_name):
        try:
            self.output_image1 = file_name
            if file_name:
                image = QImage(file_name).convertToFormat(QImage.Format.Format_ARGB32)
                if image.isNull():
                    raise ValueError(self.tr("图像无法读取，可能文件格式不支持。"))

                # 将白色背景转为透明
                for y in range(image.height()):
                    for x in range(image.width()):
                        color = image.pixelColor(x, y)
                        if color.red() > 230 and color.green() > 230 and color.blue() > 230:
                            color.setAlpha(0)
                            image.setPixelColor(x, y, color)

                # 裁剪有效区域
                left, top, right, bottom = image.width(), image.height(), 0, 0
                for y in range(image.height()):
                    for x in range(image.width()):
                        if image.pixelColor(x, y).alpha() > 0:
                            left = min(left, x)
                            top = min(top, y)
                            right = max(right, x)
                            bottom = max(bottom, y)

                if left > right or top > bottom:
                    raise ValueError(self.tr("图片中没有有效的非透明区域。"))

                cropped_image = image.copy(left, top, right - left + 1, bottom - top + 1)
                self.original_pixmap1 = QPixmap.fromImage(cropped_image)
                self.pixmap_item1.setPixmap(self.original_pixmap1)
                self.pixmap_item2.setPixmap(QPixmap())

        except Exception as e:
            InfoBar.error(
                title=self.tr("加载失败"),
                content=self.tr(f"选择图片1时出错：{str(e)}"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self
            )

    def chooseImage2(self, index):
        self.current_index = index
        file_name = self.index_to_path.get(index, "")
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
            self.pixmap_item2.setPixmap(self.original_pixmap2)

            self.align_pixmaps_vertically()

            InfoBar.success(
                title=self.tr('提示消息'),
                content=self.tr("图片2加载成功"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=1000,
                parent=self
            )


    # 图片2加载方法
    def loadImage2(self):
            file_name, _ = QFileDialog.getOpenFileName(self, "Select Image2", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)")
            if file_name:
                self.output_image2 = file_name
                self.original_pixmap2 = QPixmap(file_name)  # 存储原始加载的图片
                self.pixmap_item2.setPixmap(self.original_pixmap2)
                # self.pixmap_item2.setFixedSize(self.original_pixmap2.size())  # 设置image_label1的大小与图片大小一致
                InfoBar.success(
                title=self.tr('提示消息'),
                content=self.tr("图片2加载成功。"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=500,    # won't disappear automatically
                parent=self
            )

    # 图片2加载方法
    def outputList(self):
            if self.output_image1 == '' or self.output_image2 == '':
                InfoBar.warning(
                title=self.tr('导出错误'),
                content=self.tr("图片地址为空"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,    # won't disappear automatically
                parent=self
            )
            else:
                now = int(round(time.time()*1000))
                nowTime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(now/1000))
                new_list = [self.output_image1, self.output_image2, 'None info', 'None info', nowTime]
                if self.is_upper:
                    direction="top"
                else:
                    direction="bottom"

                self.data_changer._instance.set_result_list(new_list)
                self.matchdb.update_match_confirm(self.output_image1, self.output_image2, direction, nowTime)

                InfoBar.success(
                title=self.tr('提示消息'),
                content=self.tr("匹配项置入导出列表。"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,    # won't disappear automatically
                parent=self
            )

    def setOpacity1(self, value):
        opacity = value / 100.0
        self.pixmap_item1.setOpacity(opacity)

    def zoomIn1(self):
        self.shared_view.zoomIn()

    def zoomOut1(self):
        self.shared_view.zoomOut()

    def setOpacity2(self, value):
        opacity = value / 100.0
        self.pixmap_item2.setOpacity(opacity)

    def zoomIn2(self):
        self.shared_view.zoomIn()

    def zoomOut2(self):
        self.shared_view.zoomOut()

class SampleCard(QFrame):
    """ Sample card """

    clicked = pyqtSignal()  # 创建一个点击信号

    def __init__(self, icon, content, index, parent=None):
        super().__init__(parent=parent)

        self.isSelected = False
        self.index = index
        self.title = self.tr("排名：")+f'{index+1}'
        self.icon = icon


        self.iconWidget = IconWidget(icon, self)
        self.titleLabel = QLabel(self.title, self)
        self.contentLabel = QLabel(TextWrap.wrap(content, 45, False)[0], self)
        path = icon.replace('\\', '/')
        relative_path = path.split('test_data/')[-1]
        self.iconLabel = QLabel(relative_path, self)

        self.hBoxLayout = QHBoxLayout(self)
        self.vBoxLayout = QVBoxLayout()

        self.setFixedSize(200, 90)
        self.iconWidget.setFixedSize(48, 48)


        self.hBoxLayout.setSpacing(20)
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
        cheat = True
        if cheat:
            self.vBoxLayout.addWidget(self.iconLabel)
        self.vBoxLayout.addStretch(1)

        self.titleLabel.setObjectName('titleLabel')
        self.contentLabel.setObjectName('contentLabel')

        self.setStyleSheet('''
                    SampleCard {
                        background-color: white;
                        border-radius: 8px;
                    }
                    SampleCard:hover {
                        background-color: #E6F7FF;
                    }
                    SampleCard[isSelected="true"] {
                        border: 2px solid #1890FF;
                        background-color: #F0F8FF;
                    }
                ''')

    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)
        self.setSelected(True)
        self.clicked.emit()

    def setSelected(self, isSelected: bool, force=False):
        if self.isSelected == isSelected and not force:
            return
        self.isSelected = isSelected
        self.setProperty('isSelected', isSelected)
        self.setStyle(QApplication.style())

class ZoomableGraphicsView(QGraphicsView):
    wheelScrolled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene().addItem(self.pixmap_item)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        self.current_scale = 1.0
        self.setBackgroundBrush(Qt.GlobalColor.transparent)

    def setPixmap(self, pixmap: QPixmap):
        self.pixmap_item.setPixmap(pixmap)

        margin =1000 #自由拖动范围边距1
        rect = QRectF(pixmap.rect()).adjusted(-margin, -margin, margin, margin)
        self.scene().setSceneRect(rect)

        self.resetTransform()
        self.current_scale = 1.0

    def wheelEvent(self, event):
        factor = 1.2 if event.angleDelta().y() > 0 else 1 / 1.2
        for item in self.scene().selectedItems():
            item.setScale(item.scale() * factor)

    def zoomIn(self):
        for item in self.scene().selectedItems():
            scale = item.scale()
            item.setScale(scale * 1.1)

    def zoomOut(self):
        for item in self.scene().selectedItems():
            scale = item.scale()
            item.setScale(scale * 0.9)
            bounding_rect = item.boundingRect()
            print("选中项的范围：", bounding_rect)

    def setOpacity(self, opacity: float):
        self.pixmap_item.setOpacity(opacity)