# coding:utf-8
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QHBoxLayout
from qfluentwidgets import ScrollArea

class ListInterface(ScrollArea):
    """ List interface """

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.setFixedHeight(0)
        self.setObjectName('listInterface')