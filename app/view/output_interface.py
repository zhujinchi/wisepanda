# coding:utf-8
from PyQt6.QtCore import Qt, QFile, QTextStream, pyqtSignal
from PyQt6.QtWidgets import QFrame, QTreeWidgetItem, QHBoxLayout, QTreeWidgetItemIterator, QTableWidgetItem, QListWidgetItem, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog
from qfluentwidgets import TreeWidget, TableWidget, ListWidget, PushButton, InfoBar, InfoBarIcon, InfoBarPosition
from openpyxl import Workbook

from .gallery_interface import GalleryInterface
from ..common.singleton_output import Singleton_output

class OutputInterface(GalleryInterface):
    """ Output interface """

    def __init__(self, parent=None):
        super().__init__(
            title='导出项',
            parent=parent
        )
        self.setObjectName('outputInterface')

        self.mainView = tableView(self)
        
        
        self.vBoxLayout.addWidget(self.mainView)
    

class tableView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        
        self.initUI()
    
    def initUI(self):
        


        self.layout = QVBoxLayout()
        

        # 构建背景层
        self.mainWidget = QWidget(self)
        self.mainWidget.setMinimumHeight(800)
        self.mainWidget.setStyleSheet("background-color: rgb(32, 32, 32); border: 0.4px solid rgb(29, 29, 29); border-radius: 5px;")
        
        # 构建表格
        self.table_layout = QVBoxLayout()
        self.tableWidget = TableFrame(self)
        self.table_layout.addWidget(self.tableWidget)

    
        self.mainWidget.setLayout(self.table_layout)

        self.download_button = PushButton('列表下载(.xlsx)', self.mainWidget)
        self.download_button.setFixedWidth(180)
        self.download_button.clicked.connect(self.tableWidget.__save_file__) # 文本下载本地按钮连接事件
        self.table_layout.addWidget(self.download_button)
        
        self.layout.addWidget(self.mainWidget)
        self.setLayout(self.layout)

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
        self.data_provider = Singleton_output()
        self.data_provider.list_changed.connect(self.updateTable)

        self.slipMatchList = []

        self.table.verticalHeader().show()
        self.table.setColumnCount(5)
        self.table.setRowCount(len(self.slipMatchList))
        self.table.setHorizontalHeaderLabels([
            self.tr('图片一'), self.tr('图片二'),
            self.tr('附加信息'), self.tr('备注'), self.tr('置入时间')
        ])
        
        for i, listInfo in enumerate(self.slipMatchList):
            for j in range(5):
                self.table.setItem(i, j, QTableWidgetItem(listInfo[j]))

        # self.setFixedSize(800, 440)
        self.table.setColumnWidth(0, 300)
        self.table.setColumnWidth(1, 300)
        self.table.setColumnWidth(2, 200)
        self.table.setColumnWidth(3, 200)
        self.table.setColumnWidth(4, 280)
        # self.table.resizeColumnsToContents()
    
    def updateTable(self, value):
        # 添加新的数据到slipMatchList
        print(value)
        self.slipMatchList.append(value[0])
        print(self.slipMatchList)
        # 增加表格的行数
        self.table.setRowCount(len(self.slipMatchList))

        # 将新的数据更新到表格的对应单元格中
        for i, listInfo in enumerate(self.slipMatchList):
            for j in range(5):
                self.table.setItem(i, j, QTableWidgetItem(listInfo[j]))

        # 调整表格列宽以适应新的数据
        self.table.resizeColumnsToContents()

        # 触发表格的更新
        self.table.update()

    
    def __save_file__(self):
        # 打开文件对话框，让用户选择保存的地址和文件名
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
        file_dialog.setDefaultSuffix("xlsx")

        if file_dialog.exec():
            file_name = file_dialog.selectedFiles()[0]

            # 创建一个新的Excel工作簿
            workbook = Workbook()
            sheet = workbook.active

            # 这里假设要保存的数据是一个二维列表
            data_to_save = self.slipMatchList

            # 将数据写入Excel工作表
            for row_data in data_to_save:
                sheet.append(row_data)

            # 保存Excel文件
            workbook.save(file_name)

            # 打印成功保存的消息
            InfoBar.success(
            title='提示消息',
            content="匹配列表导出到本地。",
            orient=Qt.Orientation.Horizontal,
            isClosable=True,
            position=InfoBarPosition.BOTTOM_RIGHT,
            duration=3000,    # won't disappear automatically
            parent=self
        )