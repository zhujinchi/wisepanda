# coding: utf-8
from PyQt6.QtCore import QObject


class Translator(QObject):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.folder = self.tr('导入文件')
        self.list = self.tr('竹帛列表')
        self.match = self.tr('匹配项')
        self.output = self.tr('导出')
        self.label = self.tr('标注')
        self.setting = self.tr('设置')
        