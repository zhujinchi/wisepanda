import sys
from PyQt6.QtCore import Qt, QObject, pyqtSignal

class Singleton_output(QObject):
    _instance = None
    list_changed = pyqtSignal(list)
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Singleton_output, cls).__new__(cls)
            cls._instance.result_list = []

        return cls._instance
    
    def set_result_list(self, value):
        self.result_list = value
        self.list_changed.emit(value)

    @property
    def get_result_list(self):
        return self.result_list

