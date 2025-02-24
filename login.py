from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QMessageBox

from app.common.config import cfg
from app.view.main_window import MainWindow
from app.view.main_window2 import MainWindow2  # 引入新窗口
from app.common.vector_net import VectorNet


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(900, 510)

        # 设置背景图片
        self.set_background(Form, "rain-drops-1144448_1280.jpg")

        # 设置窗口图标
        Form.setWindowIcon(QIcon('app/resource/images/logo.png'))

        self.textBrowser = QtWidgets.QTextBrowser(parent=Form)
        self.textBrowser.setGeometry(QtCore.QRect(120, 70, 641, 131))
        self.textBrowser.setObjectName("textBrowser")
        self.textBrowser.setStyleSheet("background: transparent; border: none;")

        self.UserNameLabel = QtWidgets.QLabel(parent=Form)
        self.UserNameLabel.setGeometry(QtCore.QRect(210, 240, 81, 31))
        font = QtGui.QFont()
        font.setPointSize(15)
        self.UserNameLabel.setFont(font)
        self.UserNameLabel.setObjectName("UserNameLabel")
        self.passwordLabel = QtWidgets.QLabel(parent=Form)
        self.passwordLabel.setGeometry(QtCore.QRect(210, 310, 81, 31))
        font = QtGui.QFont()
        font.setPointSize(15)
        self.passwordLabel.setFont(font)
        self.passwordLabel.setObjectName("UpasswordLabel")
        self.pushButton = QtWidgets.QPushButton(parent=Form)
        self.pushButton.setGeometry(QtCore.QRect(400, 380, 131, 41))
        font = QtGui.QFont()
        font.setPointSize(12)
        self.pushButton.setFont(font)
        self.pushButton.setObjectName("pushButton")
        self.lineEdit = QtWidgets.QLineEdit(parent=Form)
        self.lineEdit.setGeometry(QtCore.QRect(310, 239, 351, 31))
        self.lineEdit.setObjectName("lineEdit")
        self.lineEdit_2 = QtWidgets.QLineEdit(parent=Form)
        self.lineEdit_2.setGeometry(QtCore.QRect(310, 310, 351, 31))
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.lineEdit_2.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)  # 设置密码隐藏

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

        # 绑定登录按钮的点击事件
        self.pushButton.clicked.connect(self.login)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "login"))
        self.textBrowser.setHtml(_translate("Form",
                                            "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
                                            "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
                                            "p, li { white-space: pre-wrap; }\n"
                                            "</style></head><body style=\" font-family:\'SimSun\'; font-size:9pt; font-weight:400; font-style:normal;\">\n"
                                            "<p style=\"-qt-paragraph-type:empty; margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p>\n"
                                            "<p align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'黑体\'; font-size:24pt; font-weight:600; color:#000000;\">武汉大学</span></p>\n"
                                            "<p align=\"center\" style=\" margin-top:12px; margin-bottom:12px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-family:\'黑体\'; font-size:24pt; font-weight:600; color:#000000;\">简牍残片缀合智能辅助系统</span></p></body></html>"))
        self.UserNameLabel.setText(_translate("Form", "用户名:"))
        self.passwordLabel.setText(_translate("Form", "密  码:"))
        self.pushButton.setText(_translate("Form", "登录"))

    def set_background(self, widget, image_path):
        palette = widget.palette()
        palette.setBrush(QtGui.QPalette.ColorRole.Window, QtGui.QBrush(QtGui.QPixmap(image_path)))
        widget.setPalette(palette)

    def login(self):
        username = self.lineEdit.text()
        password = self.lineEdit_2.text()

        # 如果用户名或密码为空，则显示警告框
        if not username or not password:
            QMessageBox.warning(self.lineEdit, "错误", "用户名或密码不能为空！")
            return

        # 如果用户名和密码正确，跳转到 MainWindow
        if username == "zhanghu" and password == "mima":
            self.open_main_window()
        else:
            # 否则跳转到 MainWindow2
            self.open_main_window2()

    def open_main_window(self):
        self.Form.close()  # 关闭登录窗口
        self.main_window = MainWindow()  # 打开主窗口
        self.main_window.show()

    def open_main_window2(self):
        self.Form.close()  # 关闭登录窗口
        self.main_window2 = MainWindow2()  # 打开错误窗口
        self.main_window2.show()


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.Form = Form
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec())
