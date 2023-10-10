import sys
from PyQt6.QtCore import Qt, QObject, pyqtSignal

class Singleton_dir(QObject):
    _instance = None
    dir_changed = pyqtSignal(str)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Singleton_dir, cls).__new__(cls)
            cls._instance.workspace_dir = ""
        return cls._instance

    # 全局的目录地址
    def set_dir(self, value):
        self.workspace_dir = value
        self.dir_changed.emit(value)

    @property
    def get_dir(self):
        return self.workspace_dir
    

