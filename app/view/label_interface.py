# coding:utf-8
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QGroupBox, QCheckBox, QVBoxLayout, QLineEdit
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, FolderListSettingCard,
                            OptionsSettingCard, PushSettingCard,
                            HyperlinkCard, SettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme, CustomColorSettingCard,
                            setTheme, setThemeColor, RangeSettingCard, isDarkTheme)

from qfluentwidgets import FluentIcon as FIF
from PyQt6.QtWidgets import QWidget, QLabel, QFileDialog

from ..common.config import cfg, AUTHOR, VERSION, YEAR
from ..common.style_sheet import StyleSheet


class LabelInterface(ScrollArea):
    """ Setting interface """

    def __init__(self, text: str, parent=None):
        super().__init__(parent=parent)
        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = QLabel(self.tr("标注"), self)

        self.setObjectName('labelInterface')

        self.initUI()

    def initUI(self):
        mainLayout = QVBoxLayout(self)
        mainLayout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # 示例：简号 + 材质 + 形制
        mainLayout.addWidget(self.createRow("简号", [QLabel("218-09-03")]))
        mainLayout.addWidget(self.createCheckRow("材质", ["竹", "木", "帛", "纸", "石", "楬", "检", "刺", "束", "券", "其他"]))
        mainLayout.addWidget(self.createCheckRow("形制", ["简", "两行", "牍", "觚", "札", "封泥", "其他"]))

        # 示例：内容
        mainLayout.addWidget(self.createCheckRow("内容", ["质日", "日书", "书籍", "文书", "律令", "其他"]))

        # 示例：正倒
        mainLayout.addWidget(self.createCheckRow("正倒", ["不存在可能", "存在可能"]))

        # 示例：特殊信息
        mainLayout.addWidget(
            self.createCheckRow("特殊信息", ["墨点", "刻痕", "涂墨", "图画", "习字", "火烧", "刮削", "其他"]))

        # 示例：备注
        mainLayout.addWidget(
            self.createRow("释文", [QCheckBox("已出"), QCheckBox("庋子"), QLabel("备注:"), QLabel("_____")]))

    def createCheckRow(self, title: str, options: list[str]) -> QGroupBox:
        groupBox = QGroupBox(title)
        outer_layout = QVBoxLayout()
        row_layout = QHBoxLayout()
        count = 0

        for option in options:
            cb = QCheckBox(option)
            count += 1

            if "其他" in option:
                other_line_edit = QLineEdit()
                other_line_edit.setPlaceholderText("请输入自定义内容")
                other_line_edit.setFixedWidth(120)
                other_line_edit.setVisible(False)

                def toggle_input(state, edit=other_line_edit):
                    edit.setVisible(state == Qt.CheckState.Checked)

                cb.stateChanged.connect(toggle_input)
                row_layout.addWidget(cb)
                row_layout.addWidget(other_line_edit)
                count += 1  # 多了一个输入框

            else:
                row_layout.addWidget(cb)

            # 如果超出 4 项或是最后一项就添加一行
            if count >= 4:
                outer_layout.addLayout(row_layout)
                row_layout = QHBoxLayout()
                count = 0

        if count > 0:  # 还有剩下没添加
            outer_layout.addLayout(row_layout)

        groupBox.setLayout(outer_layout)
        return groupBox

    def createRow(self, title: str, widgets: list[QWidget]) -> QGroupBox:
        groupBox = QGroupBox(title)
        layout = QHBoxLayout()
        for w in widgets:
            layout.addWidget(w)
        groupBox.setLayout(layout)
        return groupBox