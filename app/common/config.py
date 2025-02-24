# coding:utf-8
from enum import Enum

from PyQt6.QtCore import QLocale
from qfluentwidgets import (qconfig, QConfig, ConfigItem, OptionsConfigItem, BoolValidator,
                            OptionsValidator, RangeConfigItem, RangeValidator,
                            FolderListValidator, EnumSerializer, FolderValidator, ConfigSerializer, __version__)


class Language(Enum):  # 用于切换和设置应用程序的语言界面
    """ Language enumeration """

    CHINESE_SIMPLIFIED = QLocale(QLocale.Language.Chinese, QLocale.Country.China)
    CHINESE_TRADITIONAL = QLocale(QLocale.Language.Chinese, QLocale.Country.HongKong)
    ENGLISH = QLocale(QLocale.Language.English)
    AUTO = QLocale()


class LanguageSerializer(ConfigSerializer):  # 用于将应用的语言配置持久化存储或从存储中恢复语言配置
    """ Language serializer """

    def serialize(self, language):  # 将 Language 枚举对象转为字符串形式
        return language.value.name() if language != Language.AUTO else "Auto"

    def deserialize(self, value: str):  # 将字符串形式的语言值转换为 Language 枚举对象
        return Language(QLocale(value)) if value != "Auto" else Language.AUTO


class Config(QConfig):
    """ Config of application """

    # folders
    slipFolders = ConfigItem(  # 存储 “Slips” 文件夹的路径
        "Folders", "Slips", [], FolderListValidator())
    downloadFolder = ConfigItem(  # 存储下载文件夹的路径
        "Folders", "Download", "app/download", FolderValidator())
    modelFolder = ConfigItem(  # 存储模型文件夹的路径
        "Folders", "Model", "app/model", FolderValidator())

    # main window
    dpiScale = OptionsConfigItem(
        "MainWindow", "DpiScale", "Auto", OptionsValidator([1, 1.25, 1.5, 1.75, 2, "Auto"]), restart=True)
    language = OptionsConfigItem(
        "MainWindow", "Language", Language.AUTO, OptionsValidator(Language), LanguageSerializer(), restart=True)

    # Material
    blurRadius = RangeConfigItem("Material", "AcrylicBlurRadius", 15, RangeValidator(0, 40))

    # software update
    checkUpdateAtStartUp = ConfigItem("Update", "CheckUpdateAtStartUp", True, BoolValidator())


YEAR = 2023
AUTHOR = "Angzeng"
VERSION = "1.0.0"

cfg = Config()
qconfig.load('app/config/config.json', cfg)
