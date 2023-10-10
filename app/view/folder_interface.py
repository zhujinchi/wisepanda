import os
from qfluentwidgets import (SettingCardGroup, SwitchSettingCard, FolderListSettingCard,
                            OptionsSettingCard, PushSettingCard,
                            HyperlinkCard, PrimaryPushSettingCard, ScrollArea,
                            ComboBoxSettingCard, ExpandLayout, Theme, CustomColorSettingCard,
                            setTheme, setThemeColor, RangeSettingCard, isDarkTheme)
from qfluentwidgets import FluentIcon as FIF
from qfluentwidgets import InfoBar, InfoBar, InfoBarPosition
from PyQt6.QtCore import Qt, pyqtSignal, QUrl, QStandardPaths
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QWidget, QLabel, QFileDialog

from app.common.img_data import ImageData
from app.common.singleton_imgData_list import Singleton_imgData_list

from ..common.config import cfg
from ..common.style_sheet import StyleSheet
from ..common.singleton_dir import Singleton_dir


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

        self.singleton_instance = Singleton_dir()
        self.img_data_instance = Singleton_imgData_list()
     

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

        self.calculateData = ' '

        # calculate
        self.calculator = SettingCardGroup(
            self.tr("运算"), self.scrollWidget)  
        self.addcalculateCard = PushSettingCard(
            self.tr('开始计算'),
            FIF.ADD,
            self.tr('计算'),
            self.calculateData,
            self.calculator
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
        self.calculator.addSettingCard(self.addcalculateCard)

        # add setting card group to layout
        self.expandLayout.setSpacing(28)
        self.expandLayout.setContentsMargins(36, 10, 36, 0)
        self.expandLayout.addWidget(self.slipInThisPCGroup)
        self.expandLayout.addWidget(self.modelGroup)
        self.expandLayout.addWidget(self.calculator)

    def __onDownloadFolderCardClicked(self):
        """ download folder card clicked slot """
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Choose folder"), "./")
        if not folder or cfg.get(cfg.downloadFolder) == folder:
            return
        
        cfg.set(cfg.downloadFolder, folder)
        self.downloadFolderCard.setContent(folder)
        # 修改单例文件地址
        self.singleton_instance._instance.set_dir(folder)

    def __onAddModelCardClicked(self):
        """ add model folder card clicked slot """
        file_dialog = QFileDialog(self)
        file_dialog.setWindowTitle("Select File")
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("All Files (*);;Text Files (*.txt)")

        if file_dialog.exec() == QFileDialog.DialogCode.Accepted:
            file_name = file_dialog.selectedFiles()[0]
            self.addmodelCard.setContent(file_name)

    def __onAddCalculateCardClicked(self):
        """ 
        input: dir 
        save: a list
        1. 先获得文件地址filelist
        2. 每个文件获得上截区和下截区的特征，并保存
        """
        dir =  cfg.get(cfg.downloadFolder)
        # 获取所有图片地址
        fileList = self.getImgList(dir)
        total_num = len(fileList)
        for i, filedir in enumerate(fileList):
            print((i+1)/total_num)
            self.calculateData = '进度：' + str(round(((i+1)/total_num)*100,2)) + '%'
            self.addcalculateCard.setContent(self.calculateData)
            image_data = ImageData(filedir, fileList)
            self.img_data_instance.add_imgData_element(image_data)



    def getImgList(self, dirs, ext='png'):
        fileList = []
        for file in os.listdir(dirs):
            if os.path.isdir(os.path.join(dirs, file)):
                self.getImgList(os.path.join(dirs, file))
            elif os.path.isfile(os.path.join(dirs, file)) and file.split('.')[-1] == ext:
                fileList.append(os.path.join(dirs, file))
            else:
                continue
        return fileList
        


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
        self.addcalculateCard.clicked.connect(
            self.__onAddCalculateCardClicked
        )
