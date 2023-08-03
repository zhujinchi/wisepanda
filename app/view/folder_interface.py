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
     

        # music folders
        self.slipInThisPCGroup = SettingCardGroup(
            self.tr("文件&项目"), self.scrollWidget)
        self.slipFolderCard = FolderListSettingCard(
            cfg.slipFolders,
            self.tr("文件集合"),
            directory=QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation),
            parent=self.slipInThisPCGroup
        )
        self.downloadFolderCard = PushSettingCard(
            self.tr('选择项目'),
            FIF.DOWNLOAD,
            self.tr("导入项目"),
            cfg.get(cfg.downloadFolder),
            self.slipInThisPCGroup
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

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.slipInThisPCGroup)

    def __showRestartTooltip(self):
        """ show restart tooltip """
        InfoBar.success(
            self.tr('Updated successfully'),
            self.tr('Configuration takes effect after restart'),
            duration=1500,
            parent=self
        )

    def __onDownloadFolderCardClicked(self):
        """ download folder card clicked slot """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), "./")
        if not folder or cfg.get(cfg.downloadFolder) == folder:
            return

        cfg.set(cfg.downloadFolder, folder)
        self.downloadFolderCard.setContent(folder)

    def __connectSignalToSlot(self):
        """ connect signal to slot """
        cfg.appRestartSig.connect(self.__showRestartTooltip)
        cfg.themeChanged.connect(setTheme)

        # music in the pc
        self.slipFolderCard.folderChanged.connect(
            self.slipFoldersChanged)
        self.downloadFolderCard.clicked.connect(
            self.__onDownloadFolderCardClicked)
