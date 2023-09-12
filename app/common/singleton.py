import sys
from PyQt6.QtCore import Qt, QObject, pyqtSignal

class Singleton(QObject):
    _instance = None
    data_changed = pyqtSignal(str)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Singleton, cls).__new__(cls)
            cls._instance.workspace_dir = ""
        return cls._instance

    def set_dir(self, value):
        self.workspace_dir = value
        self.data_changed.emit(value)

    @property
    def get_dir(self):
        return self.workspace_dir

