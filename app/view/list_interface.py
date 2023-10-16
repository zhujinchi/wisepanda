# coding:utf-8
import os
import re
import cv2
import numpy as np
from functools import singledispatchmethod
from typing import List, Union

from PyQt6.QtCore import Qt, pyqtSignal, pyqtProperty, QRect, QRectF, QCoreApplication
from PyQt6.QtGui import QIcon, QPainter, QPixmap, QImage
from qfluentwidgets import (SubtitleLabel, SearchLineEdit, SmoothScrollArea, FlowLayout, StrongBodyLabel, FluentIcon, IconWidget, Theme, PushButton, PushButton, InfoBar, InfoBarPosition)
from PyQt6.QtWidgets import QApplication, QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QSizePolicy

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

global app_path

app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
        self.filelistChanged.emit(fileList)
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
        # 新加入的代码 By Clay
        new_dir = os.path.join(app_path, 'resource', 'images', 'pixel.png')
        card.imgWidget.setImg(new_dir)
        
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

        self.img_changer = Singleton_img()
        self.singleton_instance = Singleton_result()
        self.img_data_instance = Singleton_imgData_list()

        self.file_list = []
        self.top, self.bottom = None, None
        parent.filelistChanged.connect(self.onFileListChanged)

        # 初始选择的图片
        self.choose_img = ''

        self.imageInfoLabel = StrongBodyLabel(self)
        self.imageInfoLabel.setContentsMargins(8, 0, 0, 0)
        self.imageInfoLabel.setStyleSheet("border-left: 0px solid rgb(29, 29, 29);")
        self.originalImage = ImgWidget(self)

        # 创建分隔线
        self.line1_widget = QWidget(self)
        self.line1_widget.setStyleSheet("background-color: rgb(51, 51, 51); border: 0.4px solid rgb(29, 29, 29);")
        self.line1_widget.setFixedSize(140,1) 
        self.line2_widget = QWidget(self)
        self.line2_widget.setStyleSheet("background-color: rgb(51, 51, 51); border: 0.4px solid rgb(29, 29, 29);")
        self.line2_widget.setFixedSize(140,1) 

        #上半缀区组件
        self.topPartTitleLabel = StrongBodyLabel('上半缀区')
        self.topPartTitleLabel.setStyleSheet("border-left: 0px solid rgb(29, 29, 29);")
        self.top_button = PushButton("缀区开始匹配", self)
        self.top_button.clicked.connect(lambda: self.getResultList("top"))
        top_horizontal_layout = QHBoxLayout()
        top_horizontal_layout.addWidget(self.topPartTitleLabel)
        top_horizontal_layout.addSpacing(40)
        top_horizontal_layout.addWidget(self.line1_widget)
        top_horizontal_layout.addSpacing(30)
        top_horizontal_layout.addWidget(self.top_button)

        # 创建一个容器 QWidget，并将水平布局设置为其布局
        top_container_widget = QWidget(self)
        top_container_widget.setStyleSheet("border-left: 0px solid rgb(29, 29, 29);")
        top_container_widget.setLayout(top_horizontal_layout)
        self.imageTop = ImgWidget(self)

        #下半缀区组件
        self.bottomPartTitleLabel = StrongBodyLabel('下半缀区')
        self.bottom_button = PushButton("缀区开始匹配", self)
        self.bottom_button.clicked.connect(lambda: self.getResultList("bottom"))
        bottom_horizontal_layout = QHBoxLayout()
        bottom_horizontal_layout.addWidget(self.bottomPartTitleLabel)
        bottom_horizontal_layout.addSpacing(40)
        bottom_horizontal_layout.addWidget(self.line2_widget)
        bottom_horizontal_layout.addSpacing(30)
        bottom_horizontal_layout.addWidget(self.bottom_button)

        # 创建一个容器 QWidget，并将水平布局设置为其布局
        bottom_container_widget = QWidget(self)
        bottom_container_widget.setStyleSheet("border-left: 0px solid rgb(29, 29, 29);")
        bottom_container_widget.setLayout(bottom_horizontal_layout)
        self.imageBottom = ImgWidget(self)

        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(16, 20, 16, 20)
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.vBoxLayout.addWidget(self.imageInfoLabel)
        self.vBoxLayout.addSpacing(16)
        self.vBoxLayout.addWidget(self.originalImage, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addSpacing(34)
        self.vBoxLayout.addWidget(top_container_widget)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.imageTop, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vBoxLayout.addSpacing(34)
        self.vBoxLayout.addWidget(bottom_container_widget)
        self.vBoxLayout.addSpacing(5)
        self.vBoxLayout.addWidget(self.imageBottom, 0, Qt.AlignmentFlag.AlignHCenter)

        self.originalImage.setFixedSize(96, 96)
        self.imageTop.setFixedSize(96, 96)
        self.imageBottom.setFixedSize(96, 96)
        self.setFixedWidth(432)

        self.imageInfoLabel.setObjectName('imageInfoLabel')
        self.setStyleSheet("background-color: rgb(43, 43, 43); border-left: 1px solid rgb(29, 29, 29); border-top-right-radius: 10px; border-bottom-right-radius: 10px;"
                           "Qframe")

    def onFileListChanged(self, filelist):
        self.file_list = filelist
        self.choose_img = filelist[0]


    def getResultList(self, direction):
        dir = self.choose_img
        print(dir)
        try:
            if direction == 'top':
                imgData = self.img_data_instance._instance.get_result_with_name(dir)
                result_list = imgData.get_top_edge_match_list()
            else:
                imgData = self.img_data_instance._instance.get_result_with_name(dir)
                result_list = imgData.get_bottom_edge_match_list()
        except:
            pass

        # 修改单例文件地址
        self.singleton_instance._instance.set_result_list(result_list)
        InfoBar.success(
            title=self.tr('计算完成'),
            content=self.tr("匹配结果计算完毕"),
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=16000,
            parent=self
        )

    def setImage(self, img_dir):
        name = img_dir.split('/')[-1].split('\\')[-1].split('.')[0]
        self.originalImage.setImg(img_dir)
        self.img_changer._instance.set_dir(img_dir)

        self.choose_img = img_dir

        notch_extractor = NotchExtractor(img_dir)
        self.top, self.bottom = notch_extractor.extract_top(), notch_extractor.extract_bottom()
        # print(type(top), type(bottom))
        crop_size_top = (64,int((self.top.shape[0]*64)/self.top.shape[1]))
        crop_size_bottom = (64,int((self.bottom.shape[0]*64)/self.bottom.shape[1]))
        top = cv2.resize(self.top, crop_size_top, interpolation=cv2.INTER_AREA)
        bottom = cv2.resize(self.bottom, crop_size_bottom, interpolation=cv2.INTER_AREA)
        self.imageTop.setImg(self.arrayToQIcon(top))
        self.imageBottom.setImg(self.arrayToQIcon(bottom))

        self.imageInfoLabel.setText("文件名："+ name)
    
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
        
        #self.imgWidget.setImg(self.dir)
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
            pixmap = pixmap.scaled(QRectF(self.rect()).toRect().size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
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