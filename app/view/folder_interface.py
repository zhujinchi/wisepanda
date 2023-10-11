import os
import numpy as np
import cv2
import torch
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

        # 竹帛计算model
        app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.vector_model = torch.load(os.path.join(app_path, 'model/model_of_best'))
     
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
        top_vector_list = []
        bottom_vector_list = []
        dir =  cfg.get(cfg.downloadFolder)
        # 获取所有图片地址
        fileList = self.getImgList(dir)
        total_num = len(fileList)
        for i, filedir in enumerate(fileList):
            print((i+1)/total_num)
            # self.calculateData = '进度：' + str(round(((i+1)/total_num)*100,2)) + '%'
            # self.addcalculateCard.setContent(self.calculateData)
            # image_data = ImageData(filedir, fileList)
            # self.img_data_instance.add_imgData_element(image_data)

            # 数组保存上下截取区的特征
            top_vector_list.append(self.getVector(filedir,'top')) #修改成新的截取算法
            bottom_vector_list.append(self.getVector(filedir,'bottom')) 
        # 计算上下两两特征的分数，并保存
        score_list = []
        for i in top_vector_list:
            for j in bottom_vector_list:
                # 计算分数
                score_list.append(self.getScore(i, j)) #计算分数的
        
        # 现在得到的是一个长列表，假如你的total_num是100，那么这个列表的长度就是10000，这时如果你100，100这样取样，那你会得到bottom_edge_match_list(按照fileList文件名索引)
        # 但是如果你每隔100取样，你就会得到bottom_edge_match_list(按照fileList文件名索引)：：[1::100]
        for i, filedir in enumerate(fileList):
            bottom_edge_list = score_list[i::total_num]
            top_edge_list = score_list[i*total_num:(i+1)*total_num]

            top_edge_match_list, bottom_edge_match_list = self.getEdgeListWithFiledirList(top_edge_list, bottom_edge_list, fileList)
            image_data = ImageData(filedir, fileList, top_edge_match_list, bottom_edge_match_list)
            self.img_data_instance.add_imgData_element(image_data)

    # 给定list，计算上下截区特征
    def getVector(src_dir, direction="bottom"):
        src_img = cv2.imread(src_dir)
        gray_img = cv2.cvtColor(src_img, cv2.COLOR_BGR2GRAY)
        height, width = gray_img.shape[0], gray_img.shape[1]
        norm_img = cv2.normalize(255-gray_img, None, 0, 1.0, cv2.NORM_MINMAX, dtype=cv2.CV_32F)
        
        row_counts = [0]*height
        count = 0
        
        for r in range(height):
            for c in range(width):
                if norm_img[r][c] - 0 > 0.001:
                    count += 1
            row_counts[r] = count
            count = 0
        
        symbol_vector = [abs(row_counts[i]-row_counts[i-1]) for i in range(1, height)]
        # count_vector = np.delete(counts, [:2])
        # 直接去掉非0的1 和 2 , 他们算作微小扰动
        symbol_vector = [i if i > 2 else 0 for i in symbol_vector]

        print(symbol_vector)
        
        if direction == "top":
            top_mark = [0, height//2]
            for i in range(height//2):
                if symbol_vector[i] > 0:
                    top_mark[0] = i
                    break
            for i in range(height//2, 0, -1):
                if symbol_vector[i] > 0:
                    top_mark[1] = i
                    break
        else:
            bottom_mark = [height//2, height-1]
            for i in range(height-1, height//2, -1):
                if symbol_vector[i] > 0:
                    bottom_mark[1] = i
                    break
            for i in range(height//2, height):
                if symbol_vector[i] > 0:
                    bottom_mark[0] = i
                    break

        # 处理上下边界相等导致的图片无效问题
        # min_gap = 3
        if direction == "top":
            if (top_mark[1]-top_mark[0])*64 < width:
                top_mark = [0, height//2]
            notch_img = src_img[top_mark[0]: top_mark[1], :, :]
        else:
            if (bottom_mark[1]-bottom_mark[0])*64 < width:
                bottom_mark = [height//2, height-1]
            notch_img = src_img[bottom_mark[0]: bottom_mark[1], :, :]
            
        print(notch_img.shape)
        
        gray_img = cv2.cvtColor(notch_img, cv2.COLOR_BGR2GRAY)
        print(gray_img.shape)
        
        crop_size = (64, int(gray_img.shape[0]*64/gray_img.shape[1]))
        print(crop_size)
        cropped_img = cv2.resize(gray_img, crop_size, interpolation=cv2.INTER_AREA)
        print(cropped_img.shape)
        
        height, width = cropped_img.shape[0], cropped_img.shape[1]
        symbol_vector = []
        symbol_sum = 0
        
        for c in range(width):
            for r in range(height):
                if direction == "top":
                    if cropped_img[r][c] < 230:
                        symbol_sum += 1
                else:
                    if cropped_img[r][c] >= 230:
                        symbol_sum += 1
            symbol_vector.append(symbol_sum)
            symbol_sum = 0
        symbol_vector = [item - min(symbol_vector) for item in symbol_vector]
        return symbol_vector


    # 计算分数的方法
    def getScore(self, direction, top_vector, bottom_vector):
        zero_array = np.zeros(64)
        vector_texture_top = zero_array
        vector_texture_bottom = zero_array
        model = self.vector_model
       
        data_list = [vector_texture_top, vector_texture_bottom, top_vector, bottom_vector]
        input_data = np.array(data_list)
        pred_data = input_data.astype(np.float32)
        
        model.eval()
        y_pred = model(torch.tensor(pred_data))
        score = round(y_pred.item(), 4)
            
        return score

    # 获取某一个地址图片列表顺序的，这里应该去除掉自己本身的匹配，但我没有写，因为一趟遍历会造成加时。
    def getEdgeListWithFiledirList(top_list, bottom_list, filedir_list):
        top_temp_list = []
        bottom_temp_list = []
        for i in range(filedir_list):
            top_temp_list.append(top_list[i], filedir_list[i])
            bottom_temp_list.append(bottom_list[i], filedir_list[i])
            
        top_temp_list.sort(key=lambda x: x[0], reverse=True)
        bottom_temp_list.sort(key=lambda x: x[0], reverse=True)

        if len(filedir_list) > 50:
            return top_temp_list[:50], bottom_temp_list[:50]
        else:
            return top_temp_list, bottom_temp_list
        

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
