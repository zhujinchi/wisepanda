# coding:utf-8
import os
import re
import cv2
import numpy as np
from functools import singledispatchmethod
from typing import List, Union

from PyQt6.QtCore import Qt, pyqtSignal, pyqtProperty, QRect, QRectF, QCoreApplication
from PyQt6.QtGui import QIcon, QPainter, QPixmap, QImage, QMouseEvent
from qfluentwidgets import (SubtitleLabel, SearchLineEdit, SmoothScrollArea, FlowLayout, StrongBodyLabel, FluentIcon,
                            IconWidget, Theme, PushButton, PushButton, InfoBar, InfoBarPosition)
from PyQt6.QtWidgets import QApplication, QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, \
    QSizePolicy

from app.common.singleton_imgData_list import Singleton_imgData_list

from .gallery_interface import GalleryInterface
from ..common.config import cfg
from ..common.trie import Trie
from ..common.style_sheet import StyleSheet
from ..common.notch_extractor import NotchExtractor
from ..common.singleton_dir import Singleton_dir
from ..common.singleton_result import Singleton_result
from ..common.singleton_img import Singleton_img
from ..common.score_calculator import ScoreCalculator
from .label_interface import LabelInterface

global app_path

app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class MarkInterface(GalleryInterface):
    """ List interface """

    def __init__(self, parent=None):
        super().__init__(
            title='竹简标记',
            parent=parent
        )
        self.setObjectName('iconInterface')
        self.iconView = IconCardView(self)

        self.vBoxLayout.addWidget(self.iconView)


class IconCardView(QWidget):
    """ Icon card view """
    filelistChanged = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.data_provider = Singleton_dir()
        self.data_provider.dir_changed.connect(self.dir_changed)

        self.trie = Trie()
        self.iconLibraryLabel = StrongBodyLabel(self.tr('搜索'), self)
        self.searchLineEdit = LineEdit(self)

        self.view = QFrame(self)
        self.scrollArea = SmoothScrollArea(self.view)
        self.scrollWidget = QWidget(self.scrollArea)

        self.vBoxLayout = QVBoxLayout(self)
        self.hBoxLayout = QHBoxLayout(self.view)
        self.flowLayout = FlowLayout(self.scrollWidget, isTight=True)

        self.cards = []  # type:List[PreviewCard]
        self.dirs = []  # type:List[str]
        self.currentIndex = -1

        self.__initWidget()

    def __initWidget(self):
        self.updateImgList()

        if self.currentIndex >= 0:
            self.cards[self.currentIndex].setSelected(True, True)

        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setViewportMargins(0, 5, 0, 5)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(12)
        self.vBoxLayout.addWidget(self.iconLibraryLabel)
        self.vBoxLayout.addWidget(self.searchLineEdit)
        self.vBoxLayout.addWidget(self.view)

        # initialize style sheet
        self.view.setObjectName('preview')
        self.scrollWidget.setObjectName('scrollWidget')
        StyleSheet.LIST_INTERFACE.apply(self)
        StyleSheet.LIST_INTERFACE.apply(self.scrollWidget)

        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.searchLineEdit.setPlaceholderText(self.tr("搜索"))
        self.searchLineEdit.setFixedWidth(720)

        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.scrollArea)

        self.flowLayout.setVerticalSpacing(8)
        self.flowLayout.setHorizontalSpacing(8)
        self.flowLayout.setContentsMargins(8, 3, 8, 8)

    def __connectSignalToSlot(self):
        self.searchLineEdit.clearSignal.connect(self.showAllImgs)
        self.searchLineEdit.searchSignal.connect(self.search)

    def search(self, keyWord: str):
        """ search icons """
        regex = "\d*(" + keyWord + "+)\d*_*\d*"
        target_pattern = re.compile(regex)

        results = [card for card in self.cards if re.search(target_pattern, card.name)]

        for card in self.cards:
            card.setVisible(False)
        for card in results:
            card.setVisible(True)
        self.flowLayout.update()

    def dir_changed(self, value):
        self.dirs = []
        self.cards = []
        self.flowLayout.takeAllWidgets()
        if self.getImgList(value) != []:
            for img in self.getImgList(value):
                self.addImg(img)
        self.flowLayout.update()

    def getImgList(self, dirs=cfg.get(cfg.downloadFolder), ext=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tif']):
        fileList = []
        for file in os.listdir(dirs):
            path = os.path.join(dirs, file)
            if os.path.isdir(path):
                # 递归获取子目录中的图片，并将结果累加
                fileList.extend(self.getImgList(path, ext))
            elif os.path.isfile(path) and file.split('.')[-1].lower() in ext:
                fileList.append(path)
            else:
                continue
        self.filelistChanged.emit(fileList)
        return fileList

    def updateImgList(self):
        self.dirs = []
        self.cards = []
        if self.getImgList(cfg.get(cfg.downloadFolder)) != []:
            for img in self.getImgList():
                self.addImg(img)

    def showAllImgs(self):
        self.flowLayout.removeAllWidgets()
        for card in self.cards:
            card.show()
            self.flowLayout.addWidget(card)

    def addImg(self, img_dir: str):
        """ add icon to view """
        card = PreviewCard(img_dir, self)
        card.imgWidget.setImg(img_dir)  # 设置为实际图像路径
        self.cards.append(card)
        self.dirs.append(img_dir)
        # 将当前图片列表保存到卡片对象中
        card.image_list = self.dirs.copy()
        self.flowLayout.addWidget(card)


class PreviewCard(QFrame):  # 每个卡片显示一个图标和图标的名称
    """ Preview card """

    def __init__(self, img_dir: str, parent=None):
        super().__init__(parent=parent)
        self.name = img_dir.split('/')[-1].split('\\')[-1].split('.')[0]
        self.dir = img_dir
        self.isSelected = False

        self.imgWidget = ImgWidget(img_dir, self)
        self.nameLabel = QLabel(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.setFixedSize(128, 128)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(8, 28, 8, 0)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.imgWidget.setFixedSize(75, 75)
        self.vBoxLayout.addWidget(self.imgWidget, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addSpacing(14)
        self.vBoxLayout.addWidget(self.nameLabel, 0, Qt.AlignmentFlag.AlignHCenter)

        text = self.nameLabel.fontMetrics().elidedText(self.name, Qt.TextElideMode.ElideRight, 120)
        self.nameLabel.setText(text)

    def setSelected(self, isSelected: bool, force=False):
        if isSelected == self.isSelected and not force:
            return
        self.isSelected = isSelected
        self.setProperty('isSelected', isSelected)
        self.setStyle(QApplication.style())

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_new_page()

    def open_new_page(self):
        # 从当前控件开始，沿着父控件链查找包含属性 "dirs" 的控件
        icon_view = self.parentWidget()
        while icon_view is not None and not hasattr(icon_view, "dirs"):
            icon_view = icon_view.parentWidget()
        if icon_view is not None and hasattr(icon_view, "dirs"):
            image_list = icon_view.dirs.copy()
        else:
            image_list = []
        # 调试输出，检查获取的图片列表
        # print("PreviewCard.open_new_page - image_list:", image_list)
        # print("PreviewCard.open_new_page - current card dir:", self.dir)
        try:
            current_index = image_list.index(self.dir)
        except ValueError:
            current_index = 0
            # print("Warning: 当前图片路径在列表中未找到！")
        # print("PreviewCard.open_new_page - current_index:", current_index)
        # 传递完整的图片列表和当前索引给页面2
        self.new_page = LabelInterface(self.dir, image_list, current_index)
        self.new_page.show()


class ImgWidget(QWidget):  # 用于显示图像
    """ Image widget """

    @singledispatchmethod
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setImg(QIcon())

    @__init__.register
    def _(self, img: QIcon, parent: QWidget = None):
        self.__init__(parent)
        self.setImg(img)

    @__init__.register
    def _(self, img: str, parent: QWidget = None):
        self.__init__(parent)
        self.setImg(img)

    def getImg(self):
        return self.toQIcon(self._img)

    def setImg(self, img: Union[str, QIcon]):
        self._img = img
        self.update()

    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHints(QPainter.RenderHint.Antialiasing |
                               QPainter.RenderHint.SmoothPixmapTransform)
        self.drawImg(self._img, painter, self.rect())

    def toQIcon(self, img: Union[str, QIcon]):
        """ convet `str` to `QIcon` """
        if isinstance(img, QIcon):
            return img
        elif isinstance(img, str):
            pixmap = QPixmap(img)
            pixmap = pixmap.scaled(QRectF(self.rect()).toRect().size(), Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            return QIcon(pixmap)
        else:
            raise TypeError("img must be QIcon or str")

    def drawImg(self, img: Union[str, QIcon], painter: QPainter, rect, state=QIcon.State.Off):
        """ draw icon """
        if isinstance(img, QIcon):
            img.paint(painter, QRectF(rect).toRect(), Qt.AlignmentFlag.AlignCenter, state=state)
        elif isinstance(img, str):
            pixmap = QPixmap(img)
            pixmap = pixmap.scaled(QRectF(rect).toRect().size(), Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)
            icon = QIcon(pixmap)
            icon.paint(painter, QRectF(rect).toRect(), Qt.AlignmentFlag.AlignCenter, state=state)
        else:
            raise TypeError("img must be QIcon or str")

    img = pyqtProperty(QIcon, getImg, setImg)


class LineEdit(SearchLineEdit):
    """ Search line edit """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText(self.tr('搜索'))
        self.setFixedWidth(304)
        self.textChanged.connect(self.search)
