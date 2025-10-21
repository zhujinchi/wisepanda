import sys
from PyQt6.QtCore import Qt, QObject, pyqtSignal

class Singleton_imgData_list(QObject):
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Singleton_imgData_list, cls).__new__(cls)
            cls._instance.img_list = []
        return cls._instance
 
    def add_imgData_element(self, value):
        self.img_list.append(value)

    def get_result_list(self):
        return self.img_list
    
    def get_result_with_name(self, name):
        for i in self.img_list:
            if i.get_dir() == name:
                return i