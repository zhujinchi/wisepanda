# coding:utf-8
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QHBoxLayout
from qfluentwidgets import ScrollArea

class SettingInterface(ScrollArea):
    """ Setting interface """

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        
        self.setObjectName('settingInterface')