'问题：1.更新长宽无法实现 2.连接数据库 3.纠偏 4.抠图'
import os
import cv2
from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtGui import QFont, QPen, QPixmap, QIcon
from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsLineItem, QMessageBox, \
    QInputDialog, QGraphicsItem, QApplication
import mysql.connector


class LabelInterface(QtWidgets.QMainWindow):

    def __init__(self, img_path: str, image_list=None, current_index=None, parent=None):
        super().__init__(parent)
        self.img_path = img_path  # 当前图片路径
        self.lines = []  # 存储测量线
        self.init_database()
        if image_list is None:
            # 未传入图片列表时，根据当前图片所在目录扫描
            self.image_list = []
            self.current_index = 0
            self.update_image_list()
        else:
            self.image_list = image_list
            try:
                self.current_index = current_index if current_index is not None else self.image_list.index(img_path)
            except ValueError:
                self.current_index = 0
        try:
            self.setupUi(self)
        except Exception as e:
            print(f"Error in LabelInterface: {e}")

    def setupUi(self, Form):
        Form.setObjectName("LabelWindow")
        Form.resize(1280, 1000)
        Form.move(200, 0)
        Form.setWindowIcon(QIcon('app/resource/images/logo.png'))

        # 禁止窗口最大化
        Form.setWindowFlags(QtCore.Qt.WindowType.WindowCloseButtonHint | QtCore.Qt.WindowType.WindowMinimizeButtonHint)

        # 设置窗口背景为渐变色
        Form.setStyleSheet("""
            QMainWindow {
                background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:0, y2:1, stop:0 #51dbb8, stop:1 #41b7cb);
            }
        """)

        # 简号
        self.IDLabel = QtWidgets.QLabel(parent=Form)
        self.IDLabel.setGeometry(QtCore.QRect(70, 30, 71, 31))
        font = QtGui.QFont()
        font.setPointSize(15)
        self.IDLabel.setFont(font)
        self.IDLabel.setObjectName("IDLabel")

        self.IDLineEdit = QtWidgets.QLineEdit(parent=Form)
        self.IDLineEdit.setGeometry(QtCore.QRect(200, 25, 200, 40))
        self.IDLineEdit.setObjectName("LengthLineEdit")
        self.IDLineEdit.setReadOnly(True)

        # 左侧滚动区域，显示图片
        self.scrollArea_showPic = QtWidgets.QScrollArea(parent=Form)
        self.scrollArea_showPic.setGeometry(QtCore.QRect(60, 80, 531, 851))
        self.scrollArea_showPic.setWidgetResizable(True)
        self.scrollArea_showPic.setObjectName("scrollArea_showPic")
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 529, 919))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        self.scrollArea_showPic.setWidget(self.scrollAreaWidgetContents)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene, self.scrollAreaWidgetContents)
        self.view.setGeometry(0, 0, 531, 921)
        self.view.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        self.view.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)  # 缩放以鼠标为中心
        self.view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)  # 启用拖动模式

        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)

        self.lines = []  # 存储测量线
        self.pixel_to_cm_ratio = None  # 像素到 cm 转换比例

        # 测量长宽计算结果显示
        self.LengthLineEdit = QtWidgets.QLineEdit(parent=Form)
        self.LengthLineEdit.setGeometry(QtCore.QRect(830, 205, 120, 40))
        self.LengthLineEdit.setObjectName("LengthLineEdit")
        self.LengthLineEdit.setReadOnly(True)

        # 测量按钮
        self.measureButton = QtWidgets.QPushButton(parent=Form)
        self.measureButton.setGeometry(QtCore.QRect(970, 205, 100, 40))
        self.measureButton.setText("测量长宽")
        self.measureButton.setObjectName("measureButton")
        self.measureButton.clicked.connect(self.start_measurement)

        self.measureButton2 = QtWidgets.QPushButton(parent=Form)
        self.measureButton2.setGeometry(QtCore.QRect(1090, 205, 100, 40))
        self.measureButton2.setText("手动测量")
        self.measureButton2.setObjectName("measureButton2")
        self.measureButton2.clicked.connect(self.restart_measurement)

        # 加载图片
        self.load_image()

        # 上一枚、下一枚、返回列表
        self.prevButton = QtWidgets.QPushButton(parent=Form)
        self.prevButton.setGeometry(QtCore.QRect(90, 937, 150, 40))
        self.prevButton.setText("上一枚")
        self.prevButton.setObjectName("prevButton")

        self.nextButton = QtWidgets.QPushButton(parent=Form)
        self.nextButton.setGeometry(QtCore.QRect(250, 937, 150, 40))
        self.nextButton.setText("下一枚")
        self.nextButton.setObjectName("nextButton")

        self.backButton = QtWidgets.QPushButton(parent=Form)
        self.backButton.setGeometry(QtCore.QRect(410, 937, 150, 40))
        self.backButton.setText("返回列表")
        self.backButton.setObjectName("backButton")

        self.prevButton.clicked.connect(self.on_prev_button_clicked)
        self.nextButton.clicked.connect(self.on_next_button_clicked)
        self.backButton.clicked.connect(self.on_back_button_clicked)

        # 右侧区域
        self.BianShengLabel = QtWidgets.QLabel(parent=Form)
        self.BianShengLabel.setGeometry(QtCore.QRect(650, 255, 111, 41))
        self.BianShengLabel.setObjectName("BianShengLabel")
        self.NotHaveBianSheng = QtWidgets.QRadioButton(parent=Form)
        self.NotHaveBianSheng.setGeometry(QtCore.QRect(830, 260, 101, 21))
        self.NotHaveBianSheng.setFont(font)
        self.NotHaveBianSheng.setObjectName("NotHaveBianSheng")
        self.HaveBianSheng = QtWidgets.QRadioButton(parent=Form)
        self.HaveBianSheng.setGeometry(QtCore.QRect(830, 300, 101, 21))
        self.HaveBianSheng.setObjectName("HaveBianSheng")

        self.MoJiLabel = QtWidgets.QLabel(parent=Form)
        self.MoJiLabel.setGeometry(QtCore.QRect(650, 337, 91, 31))
        self.MoJiLabel.setObjectName("MoJiLabel")
        self.HaveMoJi = QtWidgets.QRadioButton(parent=Form)
        self.HaveMoJi.setGeometry(QtCore.QRect(830, 372, 101, 31))
        self.HaveMoJi.setObjectName("HaveMoJi")
        self.NotHaveMoJi = QtWidgets.QRadioButton(parent=Form)
        self.NotHaveMoJi.setGeometry(QtCore.QRect(830, 335, 101, 31))
        self.NotHaveMoJi.setObjectName("NotHaveMoJi")

        self.DirectionLabel = QtWidgets.QLabel(parent=Form)
        self.DirectionLabel.setGeometry(QtCore.QRect(650, 418, 131, 31))
        self.DirectionLabel.setObjectName("DirectionLabel")

        self.upperZhuiHe = QtWidgets.QRadioButton(parent=Form)
        self.upperZhuiHe.setGeometry(QtCore.QRect(830, 415, 101, 31))
        self.upperZhuiHe.setObjectName("upperZhuiHe")

        self.middleZhuiHe = QtWidgets.QRadioButton(parent=Form)
        self.middleZhuiHe.setGeometry(QtCore.QRect(830, 451, 101, 31))
        self.middleZhuiHe.setObjectName("middleZhuiHe")

        self.downZhuiHe = QtWidgets.QRadioButton(parent=Form)
        self.downZhuiHe.setGeometry(QtCore.QRect(830, 485, 101, 31))
        self.downZhuiHe.setObjectName("downZhuiHe")

        self.horizontalLayoutWidget_2 = QtWidgets.QWidget(parent=Form)
        self.horizontalLayoutWidget_2.setGeometry(QtCore.QRect(930, 290, 301, 41))
        self.horizontalLayoutWidget_2.setObjectName("horizontalLayoutWidget_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_2)
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.UpperBianSheng = QtWidgets.QRadioButton(parent=self.horizontalLayoutWidget_2)

        self.UpperBianSheng.setObjectName("UpperBianSheng")
        self.horizontalLayout_2.addWidget(self.UpperBianSheng)
        self.MiddleBianSheng = QtWidgets.QRadioButton(parent=self.horizontalLayoutWidget_2)
        self.MiddleBianSheng.setObjectName("MiddleBianSheng")
        self.DownBianSheng = QtWidgets.QRadioButton(parent=self.horizontalLayoutWidget_2)
        self.DownBianSheng.setObjectName("DownBianSheng")
        self.horizontalLayout_2.addWidget(self.MiddleBianSheng)
        self.horizontalLayout_2.addWidget(self.DownBianSheng)
        self.NotClearBianSheng = QtWidgets.QRadioButton(parent=self.horizontalLayoutWidget_2)
        self.NotClearBianSheng.setObjectName("NotClearBianSheng")
        self.horizontalLayout_2.addWidget(self.NotClearBianSheng)

        self.horizontalLayoutWidget_3 = QtWidgets.QWidget(parent=Form)
        self.horizontalLayoutWidget_3.setGeometry(QtCore.QRect(930, 367, 301, 41))
        self.horizontalLayoutWidget_3.setObjectName("horizontalLayoutWidget_3")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout(self.horizontalLayoutWidget_3)
        self.horizontalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")

        self.UpperMoji = QtWidgets.QRadioButton(parent=self.horizontalLayoutWidget_3)
        self.UpperMoji.setObjectName("UpperMoji")
        self.horizontalLayout_3.addWidget(self.UpperMoji)
        self.DownMoji = QtWidgets.QRadioButton(parent=self.horizontalLayoutWidget_3)
        self.DownMoji.setObjectName("DownMoji")
        self.horizontalLayout_3.addWidget(self.DownMoji)
        self.LeftMoji = QtWidgets.QRadioButton(parent=self.horizontalLayoutWidget_3)
        self.LeftMoji.setObjectName("LeftMoji")
        self.horizontalLayout_3.addWidget(self.LeftMoji)
        self.RightMoji = QtWidgets.QRadioButton(parent=self.horizontalLayoutWidget_3)
        self.RightMoji.setObjectName("RightMoji")
        self.horizontalLayout_3.addWidget(self.RightMoji)

        self.RotateLabel = QtWidgets.QLabel(parent=Form)
        self.RotateLabel.setGeometry(QtCore.QRect(650, 543, 51, 31))
        self.RotateLabel.setObjectName("RotateLabel")

        self.RotatePushButton = QtWidgets.QPushButton(parent=Form)
        self.RotatePushButton.setGeometry(QtCore.QRect(830, 540, 281, 41))
        self.RotatePushButton.setObjectName("RotatePushButton")
        self.RotatePushButton.clicked.connect(self.rotate_image)

        self.CorrectLabel = QtWidgets.QLabel(parent=Form)
        self.CorrectLabel.setGeometry(QtCore.QRect(650, 600, 51, 41))
        self.CorrectLabel.setObjectName("CorrectLabel")
        self.CorrectPushButton = QtWidgets.QPushButton(parent=Form)
        self.CorrectPushButton.setGeometry(QtCore.QRect(830, 600, 281, 41))
        self.CorrectPushButton.setObjectName("CorrectPushButton")
        self.SpecialLabel = QtWidgets.QLabel(parent=Form)
        self.SpecialLabel.setGeometry(QtCore.QRect(650, 660, 81, 41))
        self.SpecialLabel.setObjectName("SpecialLabel")

        self.SpecialComboBox = QtWidgets.QComboBox(parent=Form)
        self.SpecialComboBox.setGeometry(QtCore.QRect(830, 660, 281, 41))
        self.SpecialComboBox.setObjectName("SpecialComboBox")
        Special_list = ["墨点", "刻齿", "涂黑", "图画", "习字", "火烧", "刮削", "自定义"]
        self.SpecialComboBox.setStyleSheet("font-family: SimSun;font-size: 15px;")
        self.SpecialComboBox.addItems(Special_list)
        # 自定义
        self.SpecialComboBox.currentIndexChanged.connect(self.on_special_combo_changed)
        self.SpecialComboBox.setStyleSheet(
            "QComboBox { text-align: center; font-family: SimSun; font-size: 15px; }"
        )

        self.TextLabel = QtWidgets.QLabel(parent=Form)
        self.TextLabel.setGeometry(QtCore.QRect(650, 750, 71, 31))
        self.TextLabel.setObjectName("TextLabel")
        self.TextEdit = QtWidgets.QTextEdit(parent=Form)
        self.TextEdit.setGeometry(QtCore.QRect(830, 718, 361, 91))
        self.TextEdit.setObjectName("TextEdit")
        self.ElseLabel = QtWidgets.QLabel(parent=Form)
        self.ElseLabel.setGeometry(QtCore.QRect(650, 850, 61, 31))
        self.ElseLabel.setObjectName("ElseLabel")
        self.ElseTextEdit = QtWidgets.QTextEdit(parent=Form)
        self.ElseTextEdit.setGeometry(QtCore.QRect(830, 825, 361, 91))
        self.ElseTextEdit.setObjectName("ElseTextEdit")
        self.PSLabel = QtWidgets.QLabel(parent=Form)
        self.PSLabel.setGeometry(QtCore.QRect(650, 935, 71, 31))
        self.PSLabel.setObjectName("PSLabel")
        self.PSPushButton = QtWidgets.QPushButton(parent=Form)
        self.PSPushButton.setGeometry(QtCore.QRect(830, 930, 281, 41))
        self.PSPushButton.setObjectName("PSPushButton")

        self.MaterialComboBox = QtWidgets.QComboBox(parent=Form)
        self.MaterialComboBox.setGeometry(QtCore.QRect(830, 25, 281, 41))
        self.MaterialComboBox.setObjectName("MaterialComboBox")
        Material_list = ["竹", "木", "帛", "纸", "石"]
        self.MaterialComboBox.setStyleSheet("font-family: SimSun;font-size: 15px;")
        self.MaterialComboBox.addItems(Material_list)

        self.XingZhiComboBox = QtWidgets.QComboBox(parent=Form)
        self.XingZhiComboBox.setGeometry(QtCore.QRect(830, 85, 281, 41))
        self.XingZhiComboBox.setObjectName("XingZhiComboBox")
        XingZhi_list = ["简", "两行", "牍", "觚", "署", "楬", "检", "刺", "束", "券", "自定义"]
        self.XingZhiComboBox.setStyleSheet("font-family: SimSun;font-size: 15px;")
        self.XingZhiComboBox.addItems(XingZhi_list)
        # 自定义
        self.XingZhiComboBox.currentIndexChanged.connect(self.on_xingzhi_combo_changed)

        self.ContentComboBox = QtWidgets.QComboBox(parent=Form)
        self.ContentComboBox.setGeometry(QtCore.QRect(830, 145, 281, 41))
        self.ContentComboBox.setObjectName("ContentComboBox")
        Content_list = ["质日", "日书", "书籍", "文书", "律令", "自定义"]
        self.ContentComboBox.setStyleSheet("font-family: SimSun;font-size: 15px;")
        self.ContentComboBox.addItems(Content_list)
        # 自定义
        self.ContentComboBox.currentIndexChanged.connect(self.on_content_combo_changed)

        self.MaterialLabel = QtWidgets.QLabel(parent=Form)
        self.MaterialLabel.setGeometry(QtCore.QRect(650, 20, 158, 50))
        self.MaterialLabel.setObjectName("MaterialLabel")

        self.ContentLabel = QtWidgets.QLabel(parent=Form)
        self.ContentLabel.setGeometry(QtCore.QRect(650, 135, 158, 67))
        self.ContentLabel.setObjectName("ContentLabel")

        self.LengthLabel = QtWidgets.QLabel(parent=Form)
        self.LengthLabel.setGeometry(QtCore.QRect(650, 185, 158, 81))
        self.LengthLabel.setObjectName("LengthLabel")

        self.XingZhiLabel = QtWidgets.QLabel(parent=Form)
        self.XingZhiLabel.setGeometry(QtCore.QRect(650, 75, 158, 61))
        self.XingZhiLabel.setObjectName("XingZhiLabel")

        # 缀合面网格布局
        self.gridLayoutWidget = QtWidgets.QWidget(parent=Form)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(920, 413, 320, 111))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setHorizontalSpacing(3)
        self.gridLayout.setVerticalSpacing(4)
        self.gridLayout.setObjectName("gridLayout")
        self.upperLeftDirection = QtWidgets.QRadioButton(parent=self.gridLayoutWidget)
        self.upperLeftDirection.setObjectName("upperLeftDirection")
        self.gridLayout.addWidget(self.upperLeftDirection, 1, 0, 1, 1)
        self.dowmRightDirection = QtWidgets.QRadioButton(parent=self.gridLayoutWidget)
        self.dowmRightDirection.setObjectName("dowmRightDirection")
        self.gridLayout.addWidget(self.dowmRightDirection, 3, 2, 1, 1)
        self.middleLeftDirection = QtWidgets.QRadioButton(parent=self.gridLayoutWidget)
        self.middleLeftDirection.setObjectName("middleLeftDirection")
        self.gridLayout.addWidget(self.middleLeftDirection, 2, 0, 1, 1)
        self.downMiddleDirection = QtWidgets.QRadioButton(parent=self.gridLayoutWidget)
        self.downMiddleDirection.setObjectName("downMiddleDirection")
        self.gridLayout.addWidget(self.downMiddleDirection, 3, 1, 1, 1)
        self.downLeftDirection = QtWidgets.QRadioButton(parent=self.gridLayoutWidget)
        self.downLeftDirection.setObjectName("downLeftDirection")
        self.gridLayout.addWidget(self.downLeftDirection, 3, 0, 1, 1)
        self.middleMiddleDirection = QtWidgets.QRadioButton(parent=self.gridLayoutWidget)
        self.middleMiddleDirection.setObjectName("middleMiddleDirection")
        self.gridLayout.addWidget(self.middleMiddleDirection, 2, 1, 1, 1)
        self.upperRightDirection = QtWidgets.QRadioButton(parent=self.gridLayoutWidget)
        self.upperRightDirection.setObjectName("upperRightDirection")
        self.gridLayout.addWidget(self.upperRightDirection, 1, 2, 1, 1)
        self.upperMiddleDirection = QtWidgets.QRadioButton(parent=self.gridLayoutWidget)
        self.upperMiddleDirection.setObjectName("upperMiddleDirection")
        self.gridLayout.addWidget(self.upperMiddleDirection, 1, 1, 1, 1)
        self.middleRightDirection = QtWidgets.QRadioButton(parent=self.gridLayoutWidget)
        self.middleRightDirection.setObjectName("middleRightDirection")
        self.gridLayout.addWidget(self.middleRightDirection, 2, 2, 1, 1)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

        # 设置所有 QRadioButton 为非互斥
        self.NotHaveBianSheng.setAutoExclusive(False)
        self.HaveBianSheng.setAutoExclusive(False)
        self.HaveMoJi.setAutoExclusive(False)
        self.NotHaveMoJi.setAutoExclusive(False)
        self.UpperMoji.setAutoExclusive(False)
        self.DownMoji.setAutoExclusive(False)
        self.LeftMoji.setAutoExclusive(False)
        self.RightMoji.setAutoExclusive(False)
        self.UpperBianSheng.setAutoExclusive(False)
        self.DownBianSheng.setAutoExclusive(False)
        self.MiddleBianSheng.setAutoExclusive(False)
        self.NotClearBianSheng.setAutoExclusive(False)
        self.upperZhuiHe.setAutoExclusive(False)
        self.middleZhuiHe.setAutoExclusive(False)
        self.downZhuiHe.setAutoExclusive(False)
        self.upperRightDirection.setAutoExclusive(False)
        self.upperLeftDirection.setAutoExclusive(False)
        self.upperMiddleDirection.setAutoExclusive(False)
        self.middleLeftDirection.setAutoExclusive(False)
        self.middleRightDirection.setAutoExclusive(False)
        self.middleMiddleDirection.setAutoExclusive(False)
        self.downLeftDirection.setAutoExclusive(False)
        self.downMiddleDirection.setAutoExclusive(False)
        self.dowmRightDirection.setAutoExclusive(False)

        # 选项之间的关系
        self.NotHaveBianSheng.toggled.connect(self.on_not_have_bian_sheng_toggled)
        self.HaveBianSheng.toggled.connect(self.on_have_bian_sheng_toggled)
        self.UpperBianSheng.toggled.connect(self.on_bian_sheng_toggled)
        self.DownBianSheng.toggled.connect(self.on_bian_sheng_toggled)
        self.MiddleBianSheng.toggled.connect(self.on_bian_sheng_toggled)
        self.NotClearBianSheng.toggled.connect(self.on_bian_sheng_toggled)

        self.NotHaveMoJi.toggled.connect(self.on_not_have_moji_toggled)
        self.HaveMoJi.toggled.connect(self.on_have_moji_toggled)
        self.UpperMoji.toggled.connect(self.on_moji_toggled)
        self.DownMoji.toggled.connect(self.on_moji_toggled)
        self.LeftMoji.toggled.connect(self.on_moji_toggled)
        self.RightMoji.toggled.connect(self.on_moji_toggled)

    def on_not_have_bian_sheng_toggled(self, checked):
        if checked:
            # 如果选择了 NotHaveBianSheng，则禁用其他相关的 BianSheng 按钮
            self.HaveBianSheng.setChecked(False)
            self.HaveBianSheng.setEnabled(False)
            self.UpperBianSheng.setChecked(False)
            self.UpperBianSheng.setEnabled(False)
            self.DownBianSheng.setChecked(False)
            self.DownBianSheng.setEnabled(False)
            self.MiddleBianSheng.setChecked(False)
            self.MiddleBianSheng.setEnabled(False)
            self.NotClearBianSheng.setChecked(False)
            self.NotClearBianSheng.setEnabled(False)
        else:
            # 如果取消了 NotHaveBianSheng，则启用其他相关的 BianSheng 按钮
            self.HaveBianSheng.setEnabled(True)
            self.UpperBianSheng.setEnabled(True)
            self.DownBianSheng.setEnabled(True)
            self.MiddleBianSheng.setEnabled(True)
            self.NotClearBianSheng.setEnabled(True)

    def on_not_have_moji_toggled(self, checked):
        if checked:
            self.HaveMoJi.setChecked(False)
            self.HaveMoJi.setEnabled(False)
            self.UpperMoji.setChecked(False)
            self.UpperMoji.setEnabled(False)
            self.DownMoji.setChecked(False)
            self.DownMoji.setEnabled(False)
            self.LeftMoji.setChecked(False)
            self.LeftMoji.setEnabled(False)
            self.RightMoji.setChecked(False)
            self.RightMoji.setEnabled(False)

        else:
            self.HaveMoJi.setEnabled(True)
            self.UpperMoji.setEnabled(True)
            self.DownMoji.setEnabled(True)
            self.LeftMoji.setEnabled(True)
            self.RightMoji.setEnabled(True)

    def on_have_bian_sheng_toggled(self, checked):
        if checked:
            # 如果选择了 HaveBianSheng，则禁用 NotHaveBianSheng
            self.NotHaveBianSheng.setChecked(False)
            self.NotHaveBianSheng.setEnabled(False)
        else:
            # 如果取消了 HaveBianSheng，则启用 NotHaveBianSheng
            self.NotHaveBianSheng.setEnabled(True)

    def on_have_moji_toggled(self, checked):
        if checked:
            self.NotHaveMoJi.setChecked(False)
            self.NotHaveMoJi.setEnabled(False)
        else:
            self.NotHaveMoJi.setEnabled(True)

    def on_bian_sheng_toggled(self, checked):
        if checked:
            # 如果选择了任何一个 BianSheng 选项，则禁用 NotHaveBianSheng
            self.NotHaveBianSheng.setChecked(False)
            self.NotHaveBianSheng.setEnabled(False)
        else:
            # 如果取消了任何一个 BianSheng 选项，检查是否可以启用 NotHaveBianSheng
            if not (self.UpperBianSheng.isChecked() or self.DownBianSheng.isChecked() or
                    self.MiddleBianSheng.isChecked() or self.NotClearBianSheng.isChecked()):
                self.NotHaveBianSheng.setEnabled(True)

    def on_moji_toggled(self, checked):
        if checked:
            self.NotHaveMoJi.setChecked(False)
            self.NotHaveMoJi.setEnabled(False)
        else:
            if not (self.UpperMoji.isChecked() or self.DownMoji.isChecked() or
                    self.LeftMoji.isChecked() or self.RightMoji.isChecked()):
                self.NotHaveMoJi.setEnabled(True)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "标记页面"))

        font = QFont("SimSun", 15)  # 宋体
        self.BianShengLabel.setFont(font)
        self.NotHaveBianSheng.setFont(font)
        self.HaveBianSheng.setFont(font)
        self.MoJiLabel.setFont(font)
        self.HaveMoJi.setFont(font)
        self.NotHaveMoJi.setFont(font)
        self.DirectionLabel.setFont(font)
        self.UpperBianSheng.setFont(font)
        self.DownBianSheng.setFont(font)
        self.MiddleBianSheng.setFont(font)
        self.NotClearBianSheng.setFont(font)
        self.RotateLabel.setFont(font)
        self.RotatePushButton.setFont(font)
        self.CorrectLabel.setFont(font)
        self.CorrectPushButton.setFont(font)
        self.SpecialLabel.setFont(font)
        self.TextLabel.setFont(font)
        self.ElseLabel.setFont(font)
        self.PSLabel.setFont(font)
        self.PSPushButton.setFont(font)
        self.MaterialLabel.setFont(font)
        self.ContentLabel.setFont(font)
        self.LengthLabel.setFont(font)
        self.XingZhiLabel.setFont(font)
        self.IDLabel.setFont(font)
        self.UpperMoji.setFont(font)
        self.DownMoji.setFont(font)
        self.LeftMoji.setFont(font)
        self.RightMoji.setFont(font)
        self.upperZhuiHe.setFont(font)
        self.middleZhuiHe.setFont(font)
        self.downZhuiHe.setFont(font)
        self.upperLeftDirection.setFont(font)
        self.dowmRightDirection.setFont(font)
        self.middleLeftDirection.setFont(font)
        self.downMiddleDirection.setFont(font)
        self.downLeftDirection.setFont(font)
        self.middleMiddleDirection.setFont(font)
        self.upperRightDirection.setFont(font)
        self.upperMiddleDirection.setFont(font)
        self.middleRightDirection.setFont(font)

        self.BianShengLabel.setText(_translate("Form", "编绳与契口"))
        self.NotHaveBianSheng.setText(_translate("Form", "无"))
        self.HaveBianSheng.setText(_translate("Form", "有"))
        self.MoJiLabel.setText(_translate("Form", "茬口墨迹"))
        self.HaveMoJi.setText(_translate("Form", "有"))
        self.NotHaveMoJi.setText(_translate("Form", "无"))
        self.DirectionLabel.setText(_translate("Form", "缀合面"))
        self.UpperBianSheng.setText(_translate("Form", "上方"))
        self.DownBianSheng.setText(_translate("Form", "下方"))
        self.MiddleBianSheng.setText(_translate("Form", "中间"))
        self.NotClearBianSheng.setText(_translate("Form", "不明"))
        self.RotateLabel.setText(_translate("Form", "正倒"))
        self.RotatePushButton.setText(_translate("Form", "旋转180度"))
        self.CorrectLabel.setText(_translate("Form", "纠偏"))
        self.CorrectPushButton.setText(_translate("Form", "correct"))
        self.SpecialLabel.setText(_translate("Form", "特殊信息"))
        self.TextLabel.setText(_translate("Form", "释文"))
        self.ElseLabel.setText(_translate("Form", "其他"))
        self.PSLabel.setText(_translate("Form", "抠图"))
        self.PSPushButton.setText(_translate("Form", "PS"))
        self.MaterialLabel.setText(_translate("Form", "材质"))
        self.ContentLabel.setText(_translate("Form", "内容"))
        self.LengthLabel.setText(_translate("Form", "长宽"))
        self.XingZhiLabel.setText(_translate("Form", "形制"))
        self.IDLabel.setText(_translate("Form", "简号"))
        self.UpperMoji.setText(_translate("Form", "上"))
        self.DownMoji.setText(_translate("Form", "下"))
        self.LeftMoji.setText(_translate("Form", "左"))
        self.RightMoji.setText(_translate("Form", "右"))
        self.upperZhuiHe.setText(_translate("Form", "上"))
        self.middleZhuiHe.setText(_translate("Form", "中"))
        self.downZhuiHe.setText(_translate("Form", "下"))
        self.upperLeftDirection.setText(_translate("Form", "上左"))
        self.dowmRightDirection.setText(_translate("Form", "下右"))
        self.middleLeftDirection.setText(_translate("Form", "中左"))
        self.downMiddleDirection.setText(_translate("Form", "下中"))
        self.downLeftDirection.setText(_translate("Form", "下左"))
        self.middleMiddleDirection.setText(_translate("Form", "中中"))
        self.upperRightDirection.setText(_translate("Form", "上右"))
        self.upperMiddleDirection.setText(_translate("Form", "上中"))
        self.middleRightDirection.setText(_translate("Form", "中右"))

    def on_special_combo_changed(self, index):
        # 获取当前选中的文本
        selected_text = self.SpecialComboBox.currentText()
        if selected_text == "自定义":
            # 弹出输入框
            custom_text, ok = QtWidgets.QInputDialog.getText(self, "自定义输入", "请输入自定义内容:")
            if ok and custom_text.strip():  # 如果用户点击了“确定”且输入内容不为空
                # 将自定义内容添加到 QComboBox 中
                self.SpecialComboBox.addItem(custom_text.strip())
                self.SpecialComboBox.setCurrentIndex(self.SpecialComboBox.count() - 1)  # 设置为当前选中项

    def on_xingzhi_combo_changed(self, index):
        selected_text = self.XingZhiComboBox.currentText()
        if selected_text == "自定义":
            custom_text, ok = QtWidgets.QInputDialog.getText(self, "自定义输入", "请输入自定义内容:")
            if ok and custom_text.strip():
                self.XingZhiComboBox.addItem(custom_text.strip())
                self.XingZhiComboBox.setCurrentIndex(self.XingZhiComboBox.count() - 1)

    def on_content_combo_changed(self, index):
        selected_text = self.ContentComboBox.currentText()
        if selected_text == "自定义":
            custom_text, ok = QtWidgets.QInputDialog.getText(self, "自定义输入", "请输入自定义内容:")
            if ok and custom_text.strip():
                self.ContentComboBox.addItem(custom_text.strip())
                self.ContentComboBox.setCurrentIndex(self.ContentComboBox.count() - 1)

    def load_image(self):
        """ 加载图片 """
        pixmap = QPixmap(self.img_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "错误", "无法加载图片！")
            return

        # 获取图片文件名并去掉扩展名
        image_file_name = os.path.basename(self.img_path)  # 获取路径中的文件名部分
        image_name_without_extension = os.path.splitext(image_file_name)[0]  # 去掉扩展名

        # 设置去掉扩展名的文件名到 IDLineEdit
        self.IDLineEdit.setText(image_name_without_extension)  # 将文件名显示在 IDLineEdit 中

        # 读取图片
        self.pixmap_item.setPixmap(pixmap)
        self.scene.setSceneRect(0, 0, pixmap.width(), pixmap.height())

    def update_image_list(self):
        """根据当前图片所在目录扫描所有图片（仅在未传入图片列表时调用）"""
        folder = os.path.dirname(self.img_path)
        ext_list = ["png", "jpg", "jpeg", "gif", "bmp", "tif"]
        files = [os.path.join(folder, f) for f in os.listdir(folder)
                 if os.path.isfile(os.path.join(folder, f)) and f.split('.')[-1].lower() in ext_list]
        files.sort()
        self.image_list = files
        try:
            self.current_index = self.image_list.index(self.img_path)
        except ValueError:
            self.current_index = 0

    def reset_right_panel(self):
        """重置右侧所有控件的状态"""
        # 重置 QComboBox 到第一个选项
        self.MaterialComboBox.setCurrentIndex(0)
        self.XingZhiComboBox.setCurrentIndex(0)
        self.ContentComboBox.setCurrentIndex(0)
        self.SpecialComboBox.setCurrentIndex(0)

        # 重置 QRadioButton 为未选中状态
        self.NotHaveBianSheng.setChecked(False)
        self.HaveBianSheng.setChecked(False)
        self.UpperBianSheng.setChecked(False)
        self.MiddleBianSheng.setChecked(False)
        self.DownBianSheng.setChecked(False)
        self.NotClearBianSheng.setChecked(False)

        self.NotHaveMoJi.setChecked(False)
        self.HaveMoJi.setChecked(False)
        self.UpperMoji.setChecked(False)
        self.DownMoji.setChecked(False)
        self.LeftMoji.setChecked(False)
        self.RightMoji.setChecked(False)

        self.upperZhuiHe.setChecked(False)
        self.middleZhuiHe.setChecked(False)
        self.downZhuiHe.setChecked(False)

        self.upperLeftDirection.setChecked(False)
        self.upperMiddleDirection.setChecked(False)
        self.upperRightDirection.setChecked(False)
        self.middleLeftDirection.setChecked(False)
        self.middleMiddleDirection.setChecked(False)
        self.middleRightDirection.setChecked(False)
        self.downLeftDirection.setChecked(False)
        self.downMiddleDirection.setChecked(False)
        self.dowmRightDirection.setChecked(False)

        # 清空 QLineEdit
        self.LengthLineEdit.clear()

        # 清空 QTextEdit
        self.TextEdit.clear()
        self.ElseTextEdit.clear()

    def on_prev_button_clicked(self):
        for line in self.lines:
            self.scene.removeItem(line)
        self.lines.clear()  # 清空线条列表
        # print("on_prev_button_clicked: current_index =", self.current_index)
        if self.current_index > 0:
            self.current_index -= 1
            self.img_path = self.image_list[self.current_index]
            # print("Switching to previous image:", self.img_path)
            self.load_image()
            self.reset_right_panel()  # 重置右侧面板
        else:
            QtWidgets.QMessageBox.information(self, "提示", "已经是第一张了！")

    def on_next_button_clicked(self):
        for line in self.lines:
            self.scene.removeItem(line)
        self.lines.clear()  # 清空线条列表
        # print("on_next_button_clicked: current_index =", self.current_index)
        if self.current_index < len(self.image_list) - 1:
            self.current_index += 1
            self.img_path = self.image_list[self.current_index]
            # print("Switching to next image:", self.img_path)
            self.load_image()
            self.reset_right_panel()  # 重置右侧面板
        else:
            QtWidgets.QMessageBox.information(self, "提示", "已经是最后一张了！")

    def on_back_button_clicked(self):
        self.close()

    def start_measurement(self):
        """ 点击测量按钮后，开始绘制测量线，并弹出单位换算输入框 """
        # 读取图片并检测非白色区域
        image = cv2.imread(self.img_path, cv2.IMREAD_GRAYSCALE)
        _, thresh = cv2.threshold(image, 240, 255, cv2.THRESH_BINARY_INV)  # 反转颜色
        coords = cv2.findNonZero(thresh)  # 找到所有非白色像素
        x, y, w, h = cv2.boundingRect(coords)  # 获取边界框

        # 清除旧的线条
        for line in self.lines:
            self.scene.removeItem(line)
        self.lines.clear()

        # 画四条测量线
        self.create_lines(x, y, w, h)

        # 让用户输入单位换算比例
        self.ask_for_scale()

        # 初始更新一次距离
        self.update_distance()

    def create_lines(self, x, y, w, h):
        """ 创建四根拖动线条 """

        def update_distance():
            """ 计算并显示距离 """
            left_x = self.lines[2].line().x1()  # 左线 X 坐标
            right_x = self.lines[3].line().x1()  # 右线 X 坐标
            top_y = self.lines[0].line().y1()  # 上线 Y 坐标
            bottom_y = self.lines[1].line().y1()  # 下线 Y 坐标

            length_pixels = abs(left_x - right_x)  # 长 = 左右两条线的 X 轴差值
            width_pixels = abs(top_y - bottom_y)  # 宽 = 上下两条线的 Y 轴差值

            if self.pixel_to_cm_ratio:
                length_cm = round(length_pixels * self.pixel_to_cm_ratio, 2)
                width_cm = round(width_pixels * self.pixel_to_cm_ratio, 2)
                self.LengthLineEdit.setText(f"({length_cm}, {width_cm}) cm")
            else:
                self.LengthLineEdit.setText(f"({length_pixels}, {width_pixels}) pixels")

        # ------------- 设定测量线 -------------
        positions = [
            (x, y, x + w, y, "horizontal"),  # 上
            (x, y + h, x + w, y + h, "horizontal"),  # 下
            (x, y, x, y + h, "vertical"),  # 左
            (x + w, y, x + w, y + h, "vertical")  # 右
        ]

        for x1, y1, x2, y2, orientation in positions:
            line = DraggableLine(x1, y1, x2, y2, orientation, update_distance)
            self.scene.addItem(line)
            self.lines.append(line)

    def ask_for_scale(self):
        """ 询问用户输入像素到 cm 的转换比例 """
        text, ok = QInputDialog.getDouble(self, "输入比例", "请输入 1 像素对应的 cm 值:", 0.01, 0.0001, 10, 4)
        if ok:
            self.pixel_to_cm_ratio = text
            self.update_distance()
        else:
            QMessageBox.warning(self, "警告", "未输入比例，测量结果仅显示像素值。")

    def update_distance(self):
        left_x = min(self.lines[2].line().x1(), self.lines[2].line().x2())
        right_x = max(self.lines[3].line().x1(), self.lines[3].line().x2())
        top_y = min(self.lines[0].line().y1(), self.lines[0].line().y2())
        bottom_y = max(self.lines[1].line().y1(), self.lines[1].line().y2())

        # print(f"Left: {left_x}, Right: {right_x}, Top: {top_y}, Bottom: {bottom_y}")

        length_pixels = abs(left_x - right_x)
        width_pixels = abs(top_y - bottom_y)

        # print(f"Length pixels: {length_pixels}, Width pixels: {width_pixels}")

        if self.pixel_to_cm_ratio:
            length_cm = round(length_pixels * self.pixel_to_cm_ratio, 2)
            width_cm = round(width_pixels * self.pixel_to_cm_ratio, 2)
            self.LengthLineEdit.setText(f"({length_cm}, {width_cm}) cm")
            # print(f"Updated LengthLineEdit: ({length_cm}, {width_cm}) cm")
        else:
            self.LengthLineEdit.setText(f"({length_pixels}, {width_pixels}) pixels")
            # print(f"Updated LengthLineEdit: ({length_pixels}, {width_pixels}) pixels")

    def restart_measurement(self):
        """ 重新计算并显示测量结果 """
        if len(self.lines) != 4:
            # print("Lines not properly initialized!")
            return

        # 获取四条线的当前位置
        left_x = self.lines[2].line().x1()  # 左线 X 坐标
        right_x = self.lines[3].line().x1()  # 右线 X 坐标
        top_y = self.lines[0].line().y1()  # 上线 Y 坐标
        bottom_y = self.lines[1].line().y1()  # 下线 Y 坐标

        # print(f"Left: {left_x}, Right: {right_x}, Top: {top_y}, Bottom: {bottom_y}")

        # 计算新的长宽
        length_pixels = abs(left_x - right_x)  # 长 = 左右两条线的 X 轴差值
        width_pixels = abs(top_y - bottom_y)  # 宽 = 上下两条线的 Y 轴差值

        # 如果存在像素到厘米的转换比例，则转换为厘米
        if self.pixel_to_cm_ratio:
            length_cm = round(length_pixels * self.pixel_to_cm_ratio, 2)
            width_cm = round(width_pixels * self.pixel_to_cm_ratio, 2)
            self.LengthLineEdit.setText(f"({length_cm}, {width_cm}) cm")
        else:
            self.LengthLineEdit.setText(f"({length_pixels}, {width_pixels}) pixels")

    def wheelEvent(self, event: QtGui.QWheelEvent):
        """ 处理鼠标滚轮事件，实现按住Ctrl时进行缩放功能 """
        if QApplication.keyboardModifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:  # 检查Ctrl键是否按下
            factor = 1.1 if event.angleDelta().y() > 0 else 0.9  # 放大或缩小
            self.view.scale(factor, factor)  # 缩放视图

    # 旋转图片180度
    def rotate_image(self):
        """ 旋转图片180度并保存为新文件 """
        # 读取原图片
        image = cv2.imread(self.img_path)
        if image is None:
            QMessageBox.warning(self, "错误", "无法加载图片！")
            return

        # 旋转180度
        rotated_image = cv2.rotate(image, cv2.ROTATE_180)
        # 生成新文件名（在原文件名基础上添加 _rotate）
        folder = os.path.dirname(self.img_path)
        base_name = os.path.basename(self.img_path)
        name_without_ext, ext = os.path.splitext(base_name)
        new_name = f"{name_without_ext}_rotate{ext}"
        new_path = os.path.join(folder, new_name)
        # 保存新图片
        cv2.imwrite(new_path, rotated_image)
        if not os.path.exists(new_path):
            QMessageBox.warning(self, "错误", f"新图片保存失败！路径：{new_path}")
            return
        # print(f"原图片路径：{self.img_path}")
        # print(f"旋转后图片路径：{new_path}")
        # 更新文件列表
        self.image_list.append(new_path)  # 添加新图片路径到文件列表
        self.current_index = len(self.image_list) - 1  # 切换到新图片
        # 更新界面
        self.img_path = new_path  # 更新当前图片路径
        self.load_image()  # 加载新图片
        self.reset_right_panel()  # 重置右侧面板
        # 更新简号
        new_id = f"{name_without_ext}_rotate"
        self.IDLineEdit.setText(new_id)
        # 更新数据库

    # 初始化数据库连接
    def init_database(self):
        try:
            # 数据库配置
            self.db_config = {
                'host': 'localhost',  # 数据库主机地址
                'port': 3306,  # 端口号
                'user': 'root',  # 数据库用户名
                'password': 'Seasons0511',  # 数据库密码
                'database': 'zhujian_label'  # 数据库名称
            }
            # 连接到数据库
            self.conn = mysql.connector.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            # 创建表（如果尚未创建）
            self.cursor.execute('''
                    CREATE TABLE IF NOT EXISTS label (
                        id VARCHAR(255) PRIMARY KEY,
                        material TEXT
                    )
                ''')
            self.conn.commit()
            print("Database connection initialized successfully.")
        except mysql.connector.Error as err:
            print(f"Error: {err}")

    # 更新数据库
    def update_database(self, id, material, length, width, bian_sheng, mo_ji, direction, rotate, special, text,
                        else_content):
        try:
            # 构建更新语句
            update_stmt = """
                UPDATE label
                SET material = %s, length = %s, width = %s, BianSheng = %s, MoJi = %s, direction = %s, rotate = %s, special = %s, text = %s, else = %s
                WHERE id = %s
            """
            self.cursor.execute(update_stmt, (
                material, length, width, bian_sheng, mo_ji, direction, rotate, special, text, else_content, id))
            self.conn.commit()
            # print(f"Database updated: ID={id}")
        except mysql.connector.Error as err:
            print(f"Error updating database: {err}")


class DraggableLine(QGraphicsLineItem):
    """ 可拖动的线条 """

    def __init__(self, x1, y1, x2, y2, orientation, callback):
        super().__init__(x1, y1, x2, y2)
        self.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemIsMovable)
        self.setFlag(QGraphicsLineItem.GraphicsItemFlag.ItemSendsScenePositionChanges)
        self.setPen(QPen(QtCore.Qt.GlobalColor.red, 2))  # 线条颜色
        self.orientation = orientation
        self.callback = callback

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            self.setLine(self.line().x1(), self.line().y1(), self.line().x2(), self.line().y2())
            self.callback()  # 每次移动更新距离
        return super().itemChange(change, value)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.callback()  # 每次移动更新距离
