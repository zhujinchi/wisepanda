from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, FolderListSettingCard,
                            OptionsSettingCard, PushSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme, CustomColorSettingCard,
                            setTheme, setThemeColor, RangeSettingCard, isDarkTheme)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QStandardPaths
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QWidget, QLabel, QFileDialog

from ..common.config import cfg
from ..common.style_sheet import StyleSheet


class FolderInterface(ScrollArea):
    """ Folder interface """

    checkUpdateSig = pyqtSignal()
    slipFoldersChanged = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

        self.scrollWidget = QWidget()
        self.expandLayout = ExpandLayout(self.scrollWidget)

        # setting label
        self.settingLabel = QLabel(self.tr("项目文件管理"), self)
     

        # folders
        self.slipInThisPCGroup = SettingCardGroup(
            self.tr("文件&项目"), self.scrollWidget)
        self.slipFolderCard = FolderListSettingCard(
            cfg.slipFolders,
            self.tr("导入文件"),
            directory=QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation),
            parent=self.slipInThisPCGroup
        )
        self.downloadFolderCard = PushSettingCard(
            self.tr('选择项目'),
            FIF.DICTIONARY_ADD,
            self.tr("导入项目"),
            cfg.get(cfg.downloadFolder),
            self.slipInThisPCGroup
        )   

        # models
        self.modelGroup = SettingCardGroup(
            self.tr("模型"), self.scrollWidget)    
        self.addmodelCard = PushSettingCard(
            self.tr('选择文件'),
            FIF.ADD,
            self.tr('导入模型'),
            cfg.get(cfg.modelFolder),
            self.modelGroup
        )

        
        self.__initWidget()

    def __initWidget(self):
        self.resize(1000, 800)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setViewportMargins(0, 80, 0, 20)
        self.setWidget(self.scrollWidget)
        self.setWidgetResizable(True)
        self.setObjectName('folderInterface')

        # initialize style sheet
        self.scrollWidget.setObjectName('scrollWidget')
        self.settingLabel.setObjectName('folderLabel')
        StyleSheet.FOLDER_INTERFACE.apply(self)

        # initialize layout
        self.__initLayout()
        self.__connectSignalToSlot()

    def __initLayout(self):
        self.settingLabel.move(36, 30)

        # add cards to group
        self.slipInThisPCGroup.addSettingCard(self.slipFolderCard)
        self.slipInThisPCGroup.addSettingCard(self.downloadFolderCard)

        self.modelGroup.addSettingCard(self.addmodelCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.slipInThisPCGroup)
        self.expandLayout.addWidget(self.modelGroup)

    def __onDownloadFolderCardClicked(self):
        """ download folder card clicked slot """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), "./")
        if not folder or cfg.get(cfg.downloadFolder) == folder:
            return

        cfg.set(cfg.downloadFolder, folder)
        self.downloadFolderCard.setContent(folder)

    def __onAddModelCardClicked(self):
        """ add model folder card clicked slot """
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Select File")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("All Files (*);;Text Files (*.txt)")

        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            file_name = file_dialog.selectedFiles()[0]
            self.addmodelCard.setContent(file_name)


    def __connectSignalToSlot(self):
        """ connect signal to slot """
        cfg.themeChanged.connect(setTheme)

        # music in the pc
        self.slipFolderCard.folderChanged.connect(
            self.slipFoldersChanged)
        self.downloadFolderCard.clicked.connect(
            self.__onDownloadFolderCardClicked)
        self.addmodelCard.clicked.connect(
            self.__onAddModelCardClicked
        )
