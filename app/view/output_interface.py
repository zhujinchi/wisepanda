# coding:utf-8
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QTreeWidgetItem, QHBoxLayout, QTreeWidgetItemIterator, QTableWidgetItem, QListWidgetItem, QWidget, QVBoxLayout, QHBoxLayout
from qfluentwidgets import TreeWidget, TableWidget, ListWidget, PushButton, InfoBar, InfoBarIcon, InfoBarPosition

from .gallery_interface import GalleryInterface

class OutputInterface(GalleryInterface):
    """ Output interface """

    def __init__(self, parent=None):
        super().__init__(
            title='导出项',
            parent=parent
        )
        self.setObjectName('outputInterface')

        self.mainView = testWidget(self)
        
        self.vBoxLayout.addWidget(self.mainView)

class testWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        
        self.initUI()
    
    def initUI(self):
        self.layout = QVBoxLayout()

        # 构建背景层
        self.mainWidget = QWidget(self)
        self.mainWidget.setFixedHeight(800)
        self.mainWidget.setStyleSheet("background-color: rgb(32, 32, 32); border: 0.4px solid rgb(29, 29, 29); border-radius: 5px;")
        
        
        # 构建表格
        self.table_layout = QVBoxLayout()
        self.tableWidget = TableFrame(self)
        self.table_layout.addWidget(self.tableWidget)
        
        self.mainWidget.setLayout(self.table_layout)

        self.download_button = PushButton('列表下载', self.mainWidget)
        self.download_button.setFixedWidth(180)
        self.download_button.clicked.connect(self.downloadList) # 文本下载本地按钮连接事件
        self.table_layout.addWidget(self.download_button)
        
        self.layout.addWidget(self.mainWidget)
        self.setLayout(self.layout)

    # 文本下载到本地方法
    def downloadList(self):
            InfoBar.success(
            title='提示消息',
            content="匹配列表导出到本地。",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=3000,    # won't disappear automatically
            parent=self
        )

class Frame(QFrame):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.hBoxLayout = QHBoxLayout(self)
        self.hBoxLayout.setContentsMargins(0, 8, 0, 0)

        self.setObjectName('frame')
        self.setStyleSheet("border: 1px solid rgba(0, 0, 0, 15); border-radius: 5px; background-color: transparent;")

    def addWidget(self, widget):
        self.hBoxLayout.addWidget(widget)

class TableFrame(Frame):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.table = TableWidget(self)
        self.addWidget(self.table)

        songInfos = [
            ['1      ', '219-08-02.png', '224-10-01.png', '/Users/angzeng/Documents/缀合网络相关/trainval/100', '/Users/angzeng/Documents/缀合网络相关/trainval/100', '2023/09/09/20:34'],
            ['2      ', '219-08-02.png', '224-10-01.png', '/Users/angzeng/Documents/缀合网络相关/trainval/100', '/Users/angzeng/Documents/缀合网络相关/trainval/100', '2023/09/09/20:34'],
            ['3', '219-08-02.png', '224-10-01.png', '/Users/angzeng/Documents/缀合网络相关/trainval/100', '/Users/angzeng/Documents/缀合网络相关/trainval/100', '2023/09/09/20:34'],
            ['4', '219-08-02.png', '224-10-01.png', '/Users/angzeng/Documents/缀合网络相关/trainval/100', '/Users/angzeng/Documents/缀合网络相关/trainval/100', '2023/09/09/20:34'],
            ['5', '219-08-02.png', '224-10-01.png', '/Users/angzeng/Documents/缀合网络相关/trainval/100', '/Users/angzeng/Documents/缀合网络相关/trainval/100', '2023/09/09/20:34'],
            ['6', '219-08-02.png', '224-10-01.png', '/Users/angzeng/Documents/缀合网络相关/trainval/100', '/Users/angzeng/Documents/缀合网络相关/trainval/100', '2023/09/09/20:34'],
        ]

        self.table.verticalHeader().hide()
        self.table.setColumnCount(6)
        self.table.setRowCount(len(songInfos))
        self.table.setHorizontalHeaderLabels([
            self.tr('ID'), self.tr('图片一'), self.tr('图片二'),
            self.tr('图片一路径'), self.tr('图片二路径'), self.tr('置入时间')
        ])
        
        for i, songInfo in enumerate(songInfos):
            for j in range(6):
                self.table.setItem(i, j, QTableWidgetItem(songInfo[j]))

        # self.setFixedSize(800, 440)
        self.table.resizeColumnsToContents()