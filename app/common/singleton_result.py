import sys
from PyQt6.QtCore import Qt, QObject, pyqtSignal

class Singleton_result(QObject):
    _instance = None
    dir_changed = pyqtSignal(str)
    list_changed = pyqtSignal(list)
    bool_signal = pyqtSignal(bool)

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Singleton_result, cls).__new__(cls)
            cls._instance.workspace_dir = ""
            cls._instance.result_list = []
            cls._instance.is_upper = True
        return cls._instance

    def set_dir(self, value):
        self.workspace_dir = value
        self.dir_changed.emit(value)

    @property
    def get_dir(self):
        return self.workspace_dir
    
    def set_result_list(self, value):
        self.result_list = value
        self.list_changed.emit(value)

    @property
    def get_result_list(self):
        return self.result_list

    def set_bool(self, value):
        self.is_upper = value
        self.bool_signal.emit(value)

    @property
    def get_bool(self):
        return self.is_upper
    

