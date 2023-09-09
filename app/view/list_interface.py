# coding:utf-8
import os
from functools import singledispatchmethod
from typing import List, Union

from PyQt6.QtCore import Qt, pyqtSignal, pyqtProperty, QRect, QRectF
from PyQt6.QtGui import QIcon, QPainter, QPixmap
from qfluentwidgets import (ScrollArea, ExpandLayout, SearchLineEdit, SmoothScrollArea, FlowLayout, StrongBodyLabel, FluentIcon, IconWidget, Theme)
from PyQt6.QtWidgets import QApplication, QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QSizePolicy

from .gallery_interface import GalleryInterface
from ..common.config import cfg
from ..common.trie import Trie
from ..common.style_sheet import StyleSheet


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

class testWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        
        self.initUI()
    
    def initUI(self):
        self.setMinimumSize(800, 600)
        self.setStyleSheet("background-color: red;")

class IconCardView(QWidget):
    """ Icon card view """

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.trie = Trie()
        self.iconLibraryLabel = StrongBodyLabel(self.tr('搜索'), self)
        self.searchLineEdit = SearchLineEdit(self)

        self.view = QFrame(self)
        self.scrollArea = SmoothScrollArea(self.view)
        self.scrollWidget = QWidget(self.scrollArea)
        self.infoPanel = IconInfoPanel(FluentIcon.MENU, self)

        self.vBoxLayout = QVBoxLayout(self)
        self.hBoxLayout = QHBoxLayout(self.view)
        self.flowLayout = FlowLayout(self.scrollWidget, isTight=True)

        self.cards = []     # type:List[PreviewCard]
        self.imgs = []      # type:List[str]
        self.currentIndex = -1

        self.__initWidget()

    def __initWidget(self):
        self.scrollArea.setWidget(self.scrollWidget)
        self.scrollArea.setViewportMargins(0, 5, 0, 5)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.vBoxLayout.setSpacing(12)
        self.vBoxLayout.addWidget(self.iconLibraryLabel)
        self.vBoxLayout.addWidget(self.searchLineEdit)
        self.vBoxLayout.addWidget(self.view)

        self.hBoxLayout.setSpacing(0)
        self.hBoxLayout.setContentsMargins(0, 0, 0, 0)
        self.hBoxLayout.addWidget(self.scrollWidget)
        self.hBoxLayout.addWidget(self.infoPanel, Qt.AlignmentFlag.AlignRight)

        self.flowLayout.setVerticalSpacing(8)
        self.flowLayout.setHorizontalSpacing(8)
        self.flowLayout.setContentsMargins(8, 3, 8, 8)

        # initialize style sheet
        self.view.setObjectName('preview')
        self.scrollWidget.setObjectName('scrollWidget')
        StyleSheet.LIST_INTERFACE.apply(self)
        StyleSheet.LIST_INTERFACE.apply(self.scrollWidget)

        if self.currentIndex >= 0:
            self.cards[self.currentIndex].setSelected(True, True)

        self.updateImgList()

        self.__initLayout()
        self.__connectSignalToSlot()
    
    def __initLayout(self):
        # self.searchLineEdit.move(36, 80)
        self.searchLineEdit.setPlaceholderText(self.tr("搜索"))
        self.searchLineEdit.setFixedWidth(720)
        # self.view.move(36, 130)

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
        items = self.trie.items(keyWord.lower())
        indexes = {i[1] for i in items}
        self.flowLayout.removeAllWidgets()

        for i, card in enumerate(self.cards):
            isVisible = i in indexes
            card.setVisible(isVisible)
            if isVisible:
                self.flowLayout.addWidget(card)

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
        self.imgs = []
        self.cards = []
        if self.getImgList(cfg.get(cfg.downloadFolder)) != []:
            for img in self.getImgList():
                self.addImg(img)
            self.setSelectedImg(self.imgs[0])
        

    def showAllImgs(self):
        self.flowLayout.removeAllWidgets()
        for card in self.cards:
            card.show()
            self.flowLayout.addWidget(card)

    def addImg(self, img: str):
        """ add icon to view """
        card = PreviewCard(img, self)
        card.clicked.connect(self.setSelectedImg)

        self.trie.insert(img.split('/')[-1].split('\\')[-1].split('.')[0], len(self.cards))
        self.cards.append(card)
        self.imgs.append(img)
        self.flowLayout.addWidget(card)

    def setSelectedImg(self, img_dir: str):
        """ set selected icon """
        index = self.imgs.index(img_dir)

        if self.currentIndex >= 0:
            self.cards[self.currentIndex].setSelected(False)

        self.currentIndex = index
        self.cards[index].setSelected(True)

class IconInfoPanel(QFrame):
    """ Icon info panel """

    def __init__(self, icon: FluentIcon, parent=None):
        super().__init__(parent=parent)
        self.nameLabel = QLabel(icon.value, self)
        self.iconWidget = IconWidget(icon, self)
        self.iconNameTitleLabel = QLabel(self.tr('Icon name'), self)
        self.iconNameLabel = QLabel(icon.value, self)
        self.enumNameTitleLabel = QLabel(self.tr('Enum member'), self)
        self.enumNameLabel = QLabel("FluentIcon." + icon.name, self)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(16, 20, 16, 20)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.vBoxLayout.addWidget(self.nameLabel)
        self.vBoxLayout.addSpacing(16)
        self.vBoxLayout.addWidget(self.iconWidget)
        self.vBoxLayout.addSpacing(45)
        self.vBoxLayout.addWidget(self.iconNameTitleLabel)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.iconNameLabel)
        self.vBoxLayout.addSpacing(34)
        self.vBoxLayout.addWidget(self.enumNameTitleLabel)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.enumNameLabel)

        self.iconWidget.setFixedSize(48, 48)
        self.setFixedWidth(216)

        self.nameLabel.setObjectName('nameLabel')
        self.iconNameTitleLabel.setObjectName('subTitleLabel')
        self.enumNameTitleLabel.setObjectName('subTitleLabel')

    def setIcon(self, icon: FluentIcon):
        self.iconWidget.setIcon(icon)
        self.nameLabel.setText(icon.value)
        self.iconNameLabel.setText(icon.value)
        self.enumNameLabel.setText("FluentIcon."+icon.name)



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

    def __init__(self, img: str, parent=None):
        super().__init__(parent=parent)
        self.img = img
        self.isSelected = False

        self.imgWidget = ImgWidget(img, self)
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

        text = self.nameLabel.fontMetrics().elidedText(self.img.split('/')[-1].split('\\')[-1].split('.')[0], Qt.TextElideMode.ElideRight, 78)
        self.nameLabel.setText(text)

    def mouseReleaseEvent(self, e):
        if self.isSelected:
            return
        
        self.clicked.emit(self.img)

    def setSelected(self, isSelected: bool, force=False):
        if isSelected == self.isSelected and not force:
            return
        self.isSelected = isSelected
        
        self.imgWidget.setImg(self.img)
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
