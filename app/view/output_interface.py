# coding:utf-8
from PyQt6.QtCore import Qt, QFile, QTextStream, pyqtSignal
from PyQt6.QtWidgets import QFrame, QTreeWidgetItem, QHBoxLayout, QTreeWidgetItemIterator, QTableWidgetItem, \
    QListWidgetItem, QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QHeaderView
from qfluentwidgets import TreeWidget, TableWidget, ListWidget, PushButton, InfoBar, InfoBarIcon, InfoBarPosition, \
    CardWidget, PrimaryPushButton
from openpyxl import Workbook

from .gallery_interface import GalleryInterface
from ..common.singleton_output import Singleton_output
import sqlite3

class OutputInterface(GalleryInterface):
    """ Output interface """

    def __init__(self, parent=None):
        super().__init__(
            title=self.tr('导出项'),
            parent=parent
        )
        self.setObjectName('outputInterface')

        self.mainView = tableView(self)
        
        
        self.vBoxLayout.addWidget(self.mainView)

    def showEvent(self, event):
        super().showEvent(event)
        self.mainView.tableWidget.loadDataFromDB()
    

class tableView(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):

        # 外层布局
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # 使用 CardWidget 作为主背景层（自带圆角+阴影+主题感知）
        self.mainWidget = CardWidget(self)
        self.mainWidget.setMinimumHeight(800)

        # 表格部分布局
        self.table_layout = QVBoxLayout(self.mainWidget)
        self.table_layout.setSpacing(12)
        self.table_layout.setContentsMargins(20, 20, 20, 20)

        # 表格控件（保持原有逻辑）
        self.tableWidget = TableFrame(self)
        self.table_layout.addWidget(self.tableWidget)

        button_layout = QHBoxLayout()

        self.download_button = PrimaryPushButton(self.tr('列表下载 (.xlsx)'), self.mainWidget)
        self.download_button.setFixedWidth(180)
        self.download_button.clicked.connect(self.tableWidget.__save_file__)
        button_layout.addWidget(self.download_button)

        self.delete_button = PushButton(self.tr('删除选中记录'), self.mainWidget)
        self.delete_button.setFixedWidth(180)
        self.delete_button.clicked.connect(self.tableWidget.deleteSelectedRows)
        button_layout.addWidget(self.delete_button)

        # 把按钮水平布局添加到表格主布局
        self.table_layout.addLayout(button_layout)

        # 设置布局
        self.mainWidget.setLayout(self.table_layout)
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

        # 初始化数据库连接
        self.conn = sqlite3.connect("match_result.db")  # 替换为你的实际数据库路径

        self.table.setColumnCount(4)
        # 设置列宽

        self.table.setHorizontalHeaderLabels([
            self.tr('待匹配图片'), self.tr('上半缀区'), self.tr('下半缀区'), self.tr('置入时间')
        ])
        self.table.setMinimumWidth(200)
        self.loadDataFromDB()


    def loadDataFromDB(self):
        try:
            cursor = self.conn.execute('SELECT image1, image2, image3, timestamp FROM match_confirm')
            rows = cursor.fetchall()

            self.table.setRowCount(len(rows))
            for i, row in enumerate(rows):
                for j, cell in enumerate(row):
                    self.table.setItem(i, j, QTableWidgetItem(str(cell)))

            self.table.resizeColumnsToContents()
            self.table.update()

        except sqlite3.Error as e:
            print("数据库读取失败：", e)

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

            # 添加表头
            sheet.append(['待匹配图片', '上半缀区', '下半缀区', '置入时间'])

            # 从数据库中读取数据
            try:
                cursor = self.conn.execute('SELECT image1, image2, image3, timestamp FROM match_confirm')
                rows = cursor.fetchall()

                for row in rows:
                    sheet.append(row)

                # 保存Excel文件
                workbook.save(file_name)

                # 提示成功
                InfoBar.success(
                    title=self.tr('提示消息'),
                    content=self.tr("匹配记录已导出到本地 Excel 文件。"),
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=3000,
                    parent=self
                )

            except sqlite3.Error as e:
                print("导出失败：", e)
                InfoBar.error(
                    title=self.tr('错误'),
                    content=self.tr("数据库读取失败，无法导出。"),
                    orient=Qt.Orientation.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.BOTTOM_RIGHT,
                    duration=3000,
                    parent=self
                )

    def deleteSelectedRows(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            InfoBar.warning(
                title=self.tr('警告'),
                content=self.tr('请先选择要删除的记录！'),
                orient=Qt.Orientation.Horizontal,
                isClosable=True,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self
            )
            return

        # 获取数据库连接，这里假设 self.conn 是数据库连接对象
        # 你需要确保 self.conn 可用，或通过其他方式获得数据库连接

        rows_to_delete = []
        for selection in selected_ranges:
            for row in range(selection.topRow(), selection.bottomRow() + 1):
                rows_to_delete.append(row)

        # 去重并倒序删除（防止删除时行号错乱）
        rows_to_delete = sorted(set(rows_to_delete), reverse=True)

        for row in rows_to_delete:
            # 取出image1唯一标识用于数据库删除
            image1_item = self.table.item(row, 0)
            if image1_item:
                image1 = image1_item.text()
                try:
                    self.conn.execute('DELETE FROM match_confirm WHERE image1 = ?', (image1,))
                    self.conn.commit()
                except Exception as e:
                    print(f'删除数据库记录失败: {e}')
                    InfoBar.error(
                        title=self.tr('错误'),
                        content=self.tr(f'删除数据库记录失败: {e}'),
                        duration=3000,
                        parent=self
                    )
                    continue

            # 从表格中删除行
            self.table.removeRow(row)

        InfoBar.success(
            title=self.tr('提示'),
            content=self.tr('选中记录已删除'),
            duration=3000,
            parent=self
        )
