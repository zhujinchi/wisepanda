# coding:utf-8
import os
import sqlite3
from typing import Dict, List

import cv2
import numpy as np
from PyQt6.QtCore import Qt, pyqtSignal, QRectF, QTimer
from PyQt6.QtGui import QPainter, QPixmap, QImage, QIcon
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QGroupBox, QCheckBox, QVBoxLayout, QLineEdit, QGraphicsView, \
    QGraphicsScene, QGraphicsPixmapItem, QGraphicsItem, QFrame, QPushButton, QApplication
from qfluentwidgets import (CardWidget, StrongBodyLabel,
                            PushButton, InfoBar, InfoBarPosition, PrimaryPushButton)

from PyQt6.QtWidgets import QWidget, QLabel

from .gallery_interface import GalleryInterface
from .list_interface import ImgWidget
from ..common.config import cfg
from ..common.notch_extractor import NotchExtractor


class LabelInterface(GalleryInterface):
    """ Setting interface """

    def __init__(self, text: str, parent=None):
        super().__init__(
            title=self.tr('标注页'),
            parent=parent
        )
        self.setObjectName('labelInterface')
        self.mainView=LabelWidget()

        self.vBoxLayout.addWidget(self.mainView)

class LabelWidget(CardWidget):
    def __init__(self):
        super().__init__()
        self.db = None
        self.pixmap_item = QGraphicsPixmapItem()
        self.hide_timer = None
        self.right_layout = None
        self.right_widget = None
        self.shared_view = None
        self.infoPanel = None
        self.dirs = []  # type:List[str]
        self.currentIndex = -1
        self.checkboxes = {}  # 存储每组复选框
        self.other_inputs = {}  # 存储每组的 "其他" 输入框
        self.line_edits = {}  # 用于存储 createRow 创建的 QLineEdit
        self.initUI()

    def initUI(self):
        # ----------- 构造右侧控件区域 -----------
        self.right_widget = CardWidget(self)
        self.right_layout = QVBoxLayout()
        self.right_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.infoPanel = ImageInfoPanel(self)
        self.db = AnnotationDatabase()

        self.right_layout.addWidget(self.createRow("简号", [self.infoPanel.imageInfoLabel]))
        self.right_layout.addWidget(
            self.createCheckRow("材质", ["竹", "木", "帛", "纸", "石", "楬", "检", "刺", "束", "券", "其他"]))
        self.right_layout.addWidget(self.createCheckRow("形制", ["简", "两行", "牍", "觚", "札", "封泥", "其他"]))
        self.right_layout.addWidget(self.createCheckRow("内容", ["质日", "日书", "书籍", "文书", "律令", "其他"]))
        self.right_layout.addWidget(self.createCheckRow("正倒", ["不存在可能", "存在可能"]))
        self.right_layout.addWidget(
            self.createCheckRow("特殊信息", ["墨点", "刻痕", "涂墨", "图画", "习字", "火烧", "刮削", "其他"]))

        transcription_edit = QLineEdit()
        transcription_edit.setPlaceholderText("请输入释文")
        transcription_edit.setMinimumWidth(400)
        self.line_edits["释文"] = [transcription_edit]

        self.right_layout.addWidget(
            self.createRow("释文", [transcription_edit]))


        self.right_layout.addWidget(self.infoPanel)

        self.save_button = PrimaryPushButton(self.tr('保存标注'))
        self.save_button.setFixedWidth(300)
        self.save_button.clicked.connect(self.collectAnnotationData)


        # 添加水平布局以实现按钮居中
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()
        self.right_layout.addSpacing(50)
        # 添加到右侧整体布局
        self.right_layout.addLayout(button_layout)

        self.right_widget.setLayout(self.right_layout)
        self.updateImgList()

        # ----------- 构造左侧图像区域 -----------
        self.shared_view = ZoomableGraphicsView(self)
        self.scene = QGraphicsScene(self)
        self.shared_view.setScene(self.scene)

        flags = QGraphicsItem.GraphicsItemFlag.ItemIsMovable | \
                QGraphicsItem.GraphicsItemFlag.ItemIsSelectable | \
                QGraphicsItem.GraphicsItemFlag.ItemIsFocusable

        self.pixmap_item.setFlags(flags)

        self.scene.addItem(self.pixmap_item)

        # 图像容器
        self.images_widget = CardWidget(self)
        self.images_widget.setStyleSheet("background-color: transparent;")
        self.shared_view.setMouseTracking(True)

        self.images_layout = QVBoxLayout()
        self.images_layout.setContentsMargins(0, 0, 0, 0)
        self.images_layout.addWidget(self.shared_view)
        self.images_widget.setLayout(self.images_layout)

        self.shared_view.prev_button.clicked.connect(self.onPrevImage)
        self.shared_view.next_button.clicked.connect(self.onNextImage)

        # 添加进左侧容器
        self.left_widget = CardWidget(self)
        self.left_layout = QVBoxLayout()
        self.left_layout.addWidget(self.images_widget)
        self.left_widget.setLayout(self.left_layout)

        # ----------- 整体布局组装 -----------
        self.layout = QHBoxLayout()
        self.layout.addWidget(self.left_widget)
        self.layout.addWidget(self.right_widget)
        self.setLayout(self.layout)

        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setFocus()
        self.images_widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.images_widget.setFocus()


    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Left:
            self.onPrevImage()  # 调用你已有的上一张函数
        elif event.key() == Qt.Key.Key_Right:
            self.onNextImage()  # 调用你已有的下一张函数

    def onPrevImage(self):
        if self.currentIndex > 0:
            self.currentIndex -= 1
            self.setSelectedImg(self.dirs[self.currentIndex])  # 更新选中图像
        else:
            InfoBar.success(
                title='',
                content=self.tr("已经是第一张"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=16000,
                parent=self
            )

    def onNextImage(self):
        if self.currentIndex < len(self.dirs) - 1:
            self.currentIndex += 1
            self.setSelectedImg(self.dirs[self.currentIndex])  # 更新选中图像
        else:
            InfoBar.success(
                title='',
                content=self.tr("已经是最后一张"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=16000,
                parent=self
            )

    def createCheckRow(self, title: str, options: list[str]) -> QGroupBox:
        groupBox = QGroupBox(title)
        outer_layout = QVBoxLayout()
        row_layout = QHBoxLayout()
        count_in_row = 0

        self.checkboxes[title] = []
        self.other_inputs[title] = []

        for option in options:
            cb = QCheckBox(option)
            self.checkboxes[title].append(cb)

            if "其他" in option:
                other_line_edit = QLineEdit()
                other_line_edit.setPlaceholderText("请输入自定义内容")
                other_line_edit.setFixedWidth(120)
                other_line_edit.setVisible(False)
                self.other_inputs[title].append(other_line_edit)

                cb.stateChanged.connect(
                    lambda state, edit=other_line_edit: edit.setVisible(state == Qt.CheckState.Checked)
                )

                row_layout.addWidget(cb)
                row_layout.addWidget(other_line_edit)
                count_in_row += 2
            else:
                row_layout.addWidget(cb)
                count_in_row += 1

            if count_in_row >= 4:
                outer_layout.addLayout(row_layout)
                row_layout = QHBoxLayout()
                count_in_row = 0

        if count_in_row > 0:
            outer_layout.addLayout(row_layout)

        groupBox.setLayout(outer_layout)
        return groupBox

    def collectAnnotationData(self) -> dict:
        result = {}

        # 处理复选框 + 其他输入
        for title, checkbox_list in self.checkboxes.items():
            selected = []
            for cb in checkbox_list:
                if cb.isChecked():
                    text = cb.text()
                    if "其他" in text:
                        for edit in self.other_inputs.get(title, []):
                            if edit.isVisible() and edit.text().strip():
                                text += f"（{edit.text().strip()}）"
                    selected.append(text)
            result[title] = selected

        # 新增：处理普通 QLineEdit 行
        for title, edits in self.line_edits.items():
            # 如果只允许单行文本，可以直接取第一个
            if len(edits) == 1:
                result[title] = edits[0].text().strip()
            else:
                result[title] = [edit.text().strip() for edit in edits]

        img_dir = self.dirs[self.currentIndex]
        self.db.save_annotation(img_dir, result)
        print(result)
        return result

    def createRow(self, title: str, widgets: list[QWidget]) -> QGroupBox:
        groupBox = QGroupBox(title)
        layout = QHBoxLayout()

        # 新增：记录 QLineEdit 等控件
        self.line_edits[title] = []

        for widget in widgets:
            layout.addWidget(widget)
            if isinstance(widget, QLineEdit):
                self.line_edits[title].append(widget)

        layout.addStretch()  # 可选：让控件左对齐
        groupBox.setLayout(layout)
        return groupBox

    def loadAnnotationForImage(self, image_path: str):
        """从数据库加载标注并应用到 UI 上"""
        data = self.db.get_annotations_by_image(image_path)
        if data:
            self.applyAnnotationToUI(data)
        else:
            # 清空所有复选框和“其他”输入框
            for title, checkbox_list in self.checkboxes.items():
                for cb in checkbox_list:
                    cb.setChecked(False)

            for title, edit_list in self.other_inputs.items():
                for edit in edit_list:
                    edit.clear()

            for title, edits in self.line_edits.items():
                for edit in edits:
                    edit.setText("")


    def applyAnnotationToUI(self, data: dict):
        for title, values in data.items():
            checkbox_list = self.checkboxes.get(title, [])
            other_edits = self.other_inputs.get(title, [])
            line_edits = self.line_edits.get(title, [])

            if line_edits:
                # 如果有文本输入框（如释文），直接设置文本
                if isinstance(values, str):
                    line_edits[0].setText(values)
                else:
                    line_edits[0].setText(','.join(values))  # 兼容万一传进来的是列表
                continue

            # 以下为复选框 + “其他” 的处理逻辑
            for cb in checkbox_list:
                text = cb.text()
                matched = False
                for value in values:
                    if value == text:
                        cb.setChecked(True)
                        matched = True
                        break
                    elif "其他" in text and value.startswith("其他（") and value.endswith("）"):
                        cb.setChecked(True)
                        # 提取括号内内容
                        other_value = value[3:-1]  # 去掉 "其他（" 和 "）"
                        for edit in other_edits:
                            if edit.isVisible():
                                edit.setText(other_value)
                                break
                        matched = True
                        break
                if not matched:
                    cb.setChecked(False)

    def getImageList(self, dirs=cfg.get(cfg.downloadFolder), ext=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tif']):
        fileList = []
        for file in os.listdir(dirs):
            if os.path.isdir(os.path.join(dirs, file)):
                self.getImageList(os.path.join(dirs, file))
            elif os.path.isfile(os.path.join(dirs, file)) and file.split('.')[-1] in ext:
                fileList.append(os.path.join(dirs, file))
            else:
                continue
        return fileList

    def updateImgList(self):
        self.dirs = []
        self.cards = []
        if self.getImageList(cfg.get(cfg.downloadFolder)) != []:
            for img in self.getImageList():
                self.dirs.append(img)
            self.setSelectedImg(self.dirs[0])

    def dir_changed(self, value):
        self.dirs = []
        if self.getImageList(value) != []:
            self.setSelectedImg(self.dirs[0])


    def setSelectedImg(self, img_dir: str):
        """ set selected icon """
        index = self.dirs.index(img_dir)

        self.currentIndex = index
        self.infoPanel.setImage(img_dir)
        self.chooseImage(img_dir)
        self.loadAnnotationForImage(img_dir)

    def chooseImage(self, file_name):
        try:
            self.output_image = file_name
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
                self.original_pixmap = QPixmap.fromImage(cropped_image)
                self.pixmap_item.setPixmap(self.original_pixmap)

        except Exception as e:
            InfoBar.error(
                title=self.tr("加载失败"),
                content=self.tr(f"选择图片时出错：{str(e)}"),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=5000,
                parent=self
            )

class ZoomableGraphicsView(QGraphicsView):
    wheel = pyqtSignal(bool)

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

        # 初始化按钮
        self.prev_button = QPushButton("◀", self)
        self.next_button = QPushButton("▶", self)
        for btn in (self.prev_button, self.next_button):
            btn.setFixedSize(30, 60)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(0, 0, 0, 80);
                    color: white;
                    border: none;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: rgba(0, 0, 0, 160);
                }
            """)
            btn.hide()

        # 设置延迟隐藏定时器
        self.hide_timer = QTimer(self)
        self.hide_timer.setSingleShot(True)
        self.hide_timer.timeout.connect(lambda: self.toggleNavButtons(False, False))

        # 鼠标追踪
        self.setMouseTracking(True)


    def setPixmap(self, pixmap: QPixmap):
        self.pixmap_item.setPixmap(pixmap)
        margin = 1000  # 拖动范围
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

    def setOpacity(self, opacity: float):
        self.pixmap_item.setOpacity(opacity)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateButtonPosition()

    def updateButtonPosition(self):
        w = self.width()
        h = self.height()
        self.prev_button.move(10, h // 2 - self.prev_button.height() // 2)
        self.next_button.move(w - self.next_button.width() - 18, h // 2 - self.next_button.height() // 2)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        x = event.position().x() if hasattr(event, 'position') else event.x()
        w = self.width()
        margin = 100

        show_prev = x <= margin
        show_next = x >= w - margin
        self.toggleNavButtons(show_prev, show_next)

        self.hide_timer.start(1000)  # 鼠标停留后自动隐藏按钮

    def leaveEvent(self, event):
        super().leaveEvent(event)
        self.toggleNavButtons(False, False)

    def toggleNavButtons(self, show_prev: bool, show_next: bool):
        self.prev_button.setVisible(show_prev)
        self.next_button.setVisible(show_next)



class ImageInfoPanel(QFrame):
    """ Image info panel """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.file_list = []
        self.top, self.bottom = None, None

        # 初始选择的图片
        self.choose_img = ''

        self.imageInfoLabel = StrongBodyLabel(self)
        self.imageInfoLabel.setContentsMargins(8, 0, 0, 0)
        self.imageInfoLabel.setStyleSheet("border-left: 0px solid rgb(29, 29, 29);")
        self.originalImage = ImgWidget(self)
        self.originalImage.hide()
        # 创建分隔线
        self.line1_widget = QWidget(self)
        self.line1_widget.setStyleSheet("background-color: rgb(51, 51, 51); border: 0.4px solid rgb(29, 29, 29);")
        self.line1_widget.setFixedSize(140, 1)
        self.line2_widget = QWidget(self)
        self.line2_widget.setStyleSheet("background-color: rgb(51, 51, 51); border: 0.4px solid rgb(29, 29, 29);")
        self.line2_widget.setFixedSize(140, 1)

        # 上半缀区组件
        self.topPartTitleLabel = StrongBodyLabel(self.tr('上半缀区'))
        self.topPartTitleLabel.setStyleSheet("border-left: 0px solid rgb(29, 29, 29);")
        self.top_button = PushButton(self.tr("缀区修改"), self)
        # self.top_button.clicked.connect(lambda: self.getResultList("top"))
        top_horizontal_layout = QHBoxLayout()
        top_horizontal_layout.addWidget(self.topPartTitleLabel)
        top_horizontal_layout.addSpacing(10)
        top_horizontal_layout.addWidget(self.line1_widget)
        # top_horizontal_layout.addSpacing(10)
        top_horizontal_layout.addWidget(self.top_button)

        # 创建一个容器 QWidget，并将水平布局设置为其布局
        top_container_widget = QWidget(self)
        top_container_widget.setStyleSheet("border-left: 0px solid rgb(29, 29, 29);")
        top_container_widget.setLayout(top_horizontal_layout)
        self.imageTop = ImgWidget(self)

        # 下半缀区组件
        self.bottomPartTitleLabel = StrongBodyLabel(self.tr('下半缀区'))
        self.bottom_button = PushButton(self.tr("缀区修改"), self)
        # self.bottom_button.clicked.connect(lambda: self.getResultList("bottom"))
        bottom_horizontal_layout = QHBoxLayout()
        bottom_horizontal_layout.addWidget(self.bottomPartTitleLabel)
        bottom_horizontal_layout.addSpacing(10)
        bottom_horizontal_layout.addWidget(self.line2_widget)
        # bottom_horizontal_layout.addSpacing(0)
        bottom_horizontal_layout.addWidget(self.bottom_button)

        # 创建一个容器 QWidget，并将水平布局设置为其布局
        bottom_container_widget = QWidget(self)
        bottom_container_widget.setStyleSheet("border-left: 0px solid rgb(29, 29, 29);")
        bottom_container_widget.setLayout(bottom_horizontal_layout)
        self.imageBottom = ImgWidget(self)

        self.vBoxLayout = QHBoxLayout(self)
        self.vBoxLayout.setContentsMargins(16, 20, 16, 20)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.vBoxLayout.addWidget(self.imageInfoLabel)
        self.vBoxLayout.addSpacing(16)
        self.vBoxLayout.addWidget(top_container_widget)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.imageTop, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addSpacing(34)
        self.vBoxLayout.addWidget(bottom_container_widget)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.imageBottom, 0, Qt.AlignmentFlag.AlignHCenter)

        self.imageTop.setFixedSize(64, 64)
        self.imageBottom.setFixedSize(64, 64)

        self.imageInfoLabel.setObjectName('imageInfoLabel')


    def setImage(self, img_dir):
        try:
            name = img_dir.split('/')[-1].split('\\')[-1].split('.')[0]
            processed_img = self.originalImage.processImg(img_dir)
            self.originalImage.setImg(processed_img)
            # self.img_changer._instance.set_dir(img_dir)

            self.choose_img = img_dir

            notch_extractor = NotchExtractor(img_dir)
            self.top, self.bottom = notch_extractor.extract_top(), notch_extractor.extract_bottom()
            crop_size_top = (64, int((self.top.shape[0] * 64) / self.top.shape[1]))
            crop_size_bottom = (64, int((self.bottom.shape[0] * 64) / self.bottom.shape[1]))
            top = cv2.resize(self.top, crop_size_top, interpolation=cv2.INTER_AREA)
            bottom = cv2.resize(self.bottom, crop_size_bottom, interpolation=cv2.INTER_AREA)
            self.imageTop.setImg(self.arrayToQIcon(top))
            self.imageBottom.setImg(self.arrayToQIcon(bottom))

            self.imageInfoLabel.setText(name)
        except:
            pass

    def arrayToQIcon(self, ndarray):
        if isinstance(ndarray, np.ndarray):
            # 将ndarray转换为QPixmap
            height, width, channel = ndarray.shape
            bytes_per_line = 3 * width
            qimage = QPixmap.fromImage(QImage(ndarray.data, width, height, bytes_per_line, QImage.Format.Format_RGB888))

            # 将QPixmap转换为QIcon
            qicon = QIcon(qimage)
            return qicon
        else:
            return None

class AnnotationDatabase:
    def __init__(self, db_path: str = 'annotations.db'):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """初始化数据库（若不存在则创建）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT UNIQUE,
                材质 TEXT,
                形制 TEXT,
                内容 TEXT,
                正倒 TEXT,
                特殊信息 TEXT,
                释文 TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def save_annotation(self, image_path: str, data: Dict[str, List[str]]):
        """保存或更新一条标注信息"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO annotations (image_path, 材质, 形制, 内容, 正倒, 特殊信息,释文)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(image_path) DO UPDATE SET
                    材质=excluded.材质,
                    形制=excluded.形制,
                    内容=excluded.内容,
                    正倒=excluded.正倒,
                    特殊信息=excluded.特殊信息,
                    释文=excluded.释文
            ''', (
                image_path,
                ','.join(data.get('材质', [])),
                ','.join(data.get('形制', [])),
                ','.join(data.get('内容', [])),
                ','.join(data.get('正倒', [])),
                ','.join(data.get('特殊信息', [])),
                data.get('释文', '').strip() if isinstance(data.get('释文'), str) else ''
            ))
            conn.commit()
        except sqlite3.Error as e:
            print(f"[数据库错误] 保存或更新标注失败: {e}")
        finally:
            if conn:
                conn.close()

    def get_annotations_by_image(self, image_path: str) -> Dict[str, List[str]]:
        """根据图片路径读取标注信息"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT 材质, 形制, 内容, 正倒, 特殊信息, 释文
            FROM annotations
            WHERE image_path = ?
            ORDER BY id DESC
            LIMIT 1
        ''', (image_path,))
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                '材质': row[0].split(',') if row[0] else [],
                '形制': row[1].split(',') if row[1] else [],
                '内容': row[2].split(',') if row[2] else [],
                '正倒': row[3].split(',') if row[3] else [],
                '特殊信息': row[4].split(',') if row[4] else [],
                '释文': row[5] if row[5] else ''
            }
        return {}