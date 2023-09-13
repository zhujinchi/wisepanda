# coding:utf-8
import os
import re
import cv2
import numpy as np
from functools import singledispatchmethod
from typing import List, Union

from PyQt6.QtCore import Qt, pyqtSignal, pyqtProperty, QRect, QRectF
from PyQt6.QtGui import QIcon, QPainter, QPixmap, QImage
from qfluentwidgets import (ScrollArea, ExpandLayout, SearchLineEdit, SmoothScrollArea, FlowLayout, StrongBodyLabel, FluentIcon, IconWidget, Theme)
from PyQt6.QtWidgets import QApplication, QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QSizePolicy

from .gallery_interface import GalleryInterface
from ..common.config import cfg
from ..common.trie import Trie
from ..common.style_sheet import StyleSheet
from ..common.notch_extractor import NotchExtractor
from ..common.singleton import Singleton


class ListInterface(GalleryInterface):
    """ List interface """

    def __init__(self, parent=None):
        super().__init__(
            title='竹帛列表',
            parent=parent
        )
        self.setObjectName('iconInterface')

        self.iconView = IconCardView(self)
        
        self.vBoxLayout.addWidget(self.iconView)

class IconCardView(QWidget):
    """ Icon card view """

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.data_provider = Singleton()
        self.data_provider.data_changed.connect(self.dir_changed)

        self.trie = Trie()
        self.iconLibraryLabel = StrongBodyLabel(self.tr('搜索'), self)
        self.searchLineEdit = LineEdit(self)

        self.view = QFrame(self)
        self.scrollArea = SmoothScrollArea(self.view)
        self.scrollWidget = QWidget(self.scrollArea)
        self.infoPanel = ImageInfoPanel(self)

        self.vBoxLayout = QVBoxLayout(self)
        self.hBoxLayout = QHBoxLayout(self.view)
        self.flowLayout = FlowLayout(self.scrollWidget, isTight=True)

        self.cards = []     # type:List[PreviewCard]
        self.dirs = []      # type:List[str]
        self.currentIndex = -1

        self.__initWidget()
    
    def __initWidget(self):
        self.updateImgList()

        print(self.dirs)

        if self.currentIndex >= 0:
            self.cards[self.currentIndex].setSelected(True, True)
        
        #self.infoPanel.setImage(self.dirs[0])

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
        self.infoPanel.setObjectName('infoPanel')
        StyleSheet.LIST_INTERFACE.apply(self)
        StyleSheet.LIST_INTERFACE.apply(self.scrollWidget)

        self.__initLayout()
        self.__connectSignalToSlot()
    
    def __initLayout(self):
        self.searchLineEdit.setPlaceholderText(self.tr("搜索"))
        self.searchLineEdit.setFixedWidth(720)
        # self.searchLineEdit.textChanged.connect(self.search)

        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.scrollArea)
        self.hBoxLayout.addWidget(self.infoPanel, 0, Qt.AlignmentFlag.AlignRight)

        self.flowLayout.setVerticalSpacing(8)
        self.flowLayout.setHorizontalSpacing(8)
        self.flowLayout.setContentsMargins(8, 3, 8, 8)

    def __connectSignalToSlot(self):
        self.searchLineEdit.clearSignal.connect(self.showAllImgs)
        self.searchLineEdit.searchSignal.connect(self.search)

    def search(self, keyWord: str):
        """ search icons """
        regex = "\d*("+ keyWord +"+)\d*_*\d*"
        target_pattern = re.compile(regex)

        results = [card for card in self.cards if re.search(target_pattern, card.name)]

        for card in self.cards:
            card.setVisible(False)
        for card in results:
            card.setVisible(True)
        self.flowLayout.update()
        self.setSelectedImg(results[0].dir)


    def dir_changed(self, value):
        self.dirs = []
        self.cards = []
        self.flowLayout.takeAllWidgets()
        if self.getImgList(value) != []:
            for img in self.getImgList(value):
                self.addImg(img)
            self.setSelectedImg(self.dirs[0])
        self.flowLayout.update()


    def getImgList(self, dirs=cfg.get(cfg.downloadFolder), ext='png'):
        fileList = []
        for file in os.listdir(dirs):
            if os.path.isdir(os.path.join(dirs, file)):
                self.getImgList(os.path.join(dirs, file))
            elif os.path.isfile(os.path.join(dirs, file)) and file.split('.')[-1] == ext:
                fileList.append(os.path.join(dirs, file))
            else:
                continue
        return fileList
    
    def updateImgList(self):
        self.dirs = []
        self.cards = []
        if self.getImgList(cfg.get(cfg.downloadFolder)) != []:
            for img in self.getImgList():
                self.addImg(img)
            self.setSelectedImg(self.dirs[0])
        
    def showAllImgs(self):
        self.flowLayout.removeAllWidgets()
        for card in self.cards:
            card.show()
            self.flowLayout.addWidget(card)

    def addImg(self, img_dir: str):
        """ add icon to view """
        card = PreviewCard(img_dir, self)
        card.clicked.connect(self.setSelectedImg)
        self.cards.append(card)
        self.dirs.append(img_dir)
        self.flowLayout.addWidget(card)

    def setSelectedImg(self, img_dir: str):
        """ set selected icon """
        index = self.dirs.index(img_dir)

        if self.currentIndex >= 0:
            self.cards[self.currentIndex].setSelected(False)
  
        self.currentIndex = index
        self.cards[index].setSelected(True)
        self.infoPanel.setImage(img_dir)

class ImageInfoPanel(QFrame):
    """ Image info panel """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.imageInfoLabel = StrongBodyLabel(self)
        self.originalImage = ImgWidget(self)

        self.topPartTitleLabel = QLabel(self.tr('上半缀区'), self)
        self.imageTop = ImgWidget(self)

        self.bottomPartTitleLabel = QLabel(self.tr('下半缀区'), self)
        self.imageBottom = ImgWidget(self)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(16, 20, 16, 20)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.vBoxLayout.addWidget(self.imageInfoLabel)
        self.vBoxLayout.addSpacing(16)
        self.vBoxLayout.addWidget(self.originalImage)
        self.vBoxLayout.addSpacing(34)
        self.vBoxLayout.addWidget(self.topPartTitleLabel)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.imageTop)
        self.vBoxLayout.addSpacing(34)
        self.vBoxLayout.addWidget(self.bottomPartTitleLabel)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.imageBottom)

        self.originalImage.setFixedSize(96, 96)
        self.imageTop.setFixedSize(96, 96)
        self.imageBottom.setFixedSize(96, 96)
        self.setFixedWidth(432)

        self.imageInfoLabel.setObjectName('imageInfoLabel')

    def setImage(self, img_dir):
        name = img_dir.split('/')[-1].split('\\')[-1].split('.')[0]
        self.originalImage.setImg(img_dir)
        

        # image = cv2.imread(img_dir)
        # s_img_dir = '/Users/angzeng/Documents/Project/缀合网络相关/trainval/100/219-08-02.png'
        # top, bottom = NotchExtractor._get_notch(s_img_dir)
       
        # self.imageTop.setImg(self.arrayToQIcon(top))
        # self.imageBottom.setImg(self.arrayToQIcon(bottom))

        self.imageInfoLabel.setText(name)
    
    def arrayToQIcon(ndarray):
        if isinstance(ndarray, np.ndarray):
            # 将ndarray转换为QPixmap
            height, width, channel = ndarray.shape
            bytes_per_line = 3 * width
            qimage = QPixmap.fromImage(QImage(ndarray.data, width, height, bytes_per_line, QImage.Format_RGB888))
            
            # 将QPixmap转换为QIcon
            qicon = QIcon(qimage)
            return qicon
        else:
            return None


class IconCard(QFrame):
    """ Icon card """ 
    clicked = pyqtSignal(FluentIcon)

    def __init__(self, icon: FluentIcon, parent=None):
        super().__init__(parent=parent)
        self.icon = icon
        self.isSelected = False

        self.iconWidget = IconWidget(icon, self)
        self.nameLabel = QLabel(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.setFixedSize(96, 96)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(8, 28, 8, 0)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.iconWidget.setFixedSize(28, 28)
        self.vBoxLayout.addWidget(self.iconWidget, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addSpacing(14)
        self.vBoxLayout.addWidget(self.nameLabel, 0, Qt.AlignmentFlag.AlignHCenter)

        text = self.nameLabel.fontMetrics().elidedText(icon.value, Qt.TextElideMode.ElideRight, 78)
        self.nameLabel.setText(text)

    def mouseReleaseEvent(self, e):
        if self.isSelected:
            return

        self.clicked.emit(self.icon)

    def setSelected(self, isSelected: bool, force=False):
        if isSelected == self.isSelected and not force:
            return

        self.isSelected = isSelected

        if not isSelected:
            self.iconWidget.setIcon(self.icon)
        else:
            icon = self.icon.icon(Theme.DARK)
            self.iconWidget.setIcon(icon)

        self.setProperty('isSelected', isSelected)
        self.setStyle(QApplication.style())


class PreviewCard(QFrame):
    """ Preview card """
    clicked = pyqtSignal(str)

    def __init__(self, img_dir: str, parent=None):
        super().__init__(parent=parent)
        self.name = img_dir.split('/')[-1].split('\\')[-1].split('.')[0]
        self.dir = img_dir
        self.isSelected = False

        self.imgWidget = ImgWidget(img_dir, self)
        self.nameLabel = QLabel(self)
        self.vBoxLayout = QVBoxLayout(self)

        self.setFixedSize(96, 96)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(8, 28, 8, 0)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.imgWidget.setFixedSize(28, 28)
        self.vBoxLayout.addWidget(self.imgWidget, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addSpacing(14)
        self.vBoxLayout.addWidget(self.nameLabel, 0, Qt.AlignmentFlag.AlignHCenter)

        text = self.nameLabel.fontMetrics().elidedText(self.name, Qt.TextElideMode.ElideRight, 78)
        self.nameLabel.setText(text)

    def mouseReleaseEvent(self, e):
        if self.isSelected:
            return
        
        self.clicked.emit(self.dir)

    def setSelected(self, isSelected: bool, force=False):
        if isSelected == self.isSelected and not force:
            return
        self.isSelected = isSelected
        
        self.imgWidget.setImg(self.dir)
        self.setProperty('isSelected', isSelected)
        self.setStyle(QApplication.style())

class ImgWidget(QWidget):
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
            pixmap = pixmap.scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            return QIcon(pixmap)
        else:
            raise TypeError("img must be QIcon or str")
        
    def drawImg(self, img: Union[str, QIcon], painter: QPainter, rect, state=QIcon.State.Off):
        """ draw icon """
        if isinstance(img, QIcon):
            img.paint(painter, QRectF(rect).toRect(), Qt.AlignmentFlag.AlignCenter, state=state)
        elif isinstance(img, str):
            pixmap = QPixmap(img)
            pixmap = pixmap.scaled(QRectF(rect).toRect().size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
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