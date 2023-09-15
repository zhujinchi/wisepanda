import sys
from PyQt6.QtCore import Qt, QObject, pyqtSignal

class Singleton_img(QObject):
    _instance = None
    dir_changed = pyqtSignal(str)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Singleton_img, cls).__new__(cls)
            cls._instance.img_dir = ""
        return cls._instance

    def set_dir(self, value):
        self.img_dir = value
        self.dir_changed.emit(value)

    @property
    def get_dir(self):
        return self.img_dir
    