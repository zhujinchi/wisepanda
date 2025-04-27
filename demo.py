# coding:utf-8
import os
import sys
import traceback

from PyQt6.QtCore import Qt, QTranslator, QLocale
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import QApplication
from qfluentwidgets import FluentTranslator

from app.common.config import cfg
from app.view.main_window import MainWindow

from app.common.vector_net import VectorNet


# enable dpi scale
if cfg.get(cfg.dpiScale) != "Auto":
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = str(cfg.get(cfg.dpiScale))


# create main window
if __name__ == '__main__':

    app = QApplication(sys.argv)

    # internationalization
    try:
        locale = cfg.get(cfg.language).value
        if not locale:
            raise ValueError("未设置语言或语言为空")
        print(locale.name())

        # 加载 FluentWidgets 的内置翻译器
        translator = FluentTranslator()
        app.installTranslator(translator)
        # 加载你的自定义翻译文件
        myTranslator = QTranslator()
        file_path=locale.name()+".qm"
        success = myTranslator.load(file_path,"i18n")
        if not success:
            print(f"[警告] 未能加载 Fratcher 的语言文件：{locale}，请检查路径或文件名")
        app.installTranslator(myTranslator)

    except Exception as e:
        print("[错误] 加载翻译器失败：", str(e))
        traceback.print_exc()

    app.setWindowIcon(QIcon("app/resource/images/logo.png"))
    app.setAttribute(Qt.ApplicationAttribute.AA_DontCreateNativeWidgetSiblings)
    w = MainWindow()
    w.show()

    sys.exit(app.exec())
