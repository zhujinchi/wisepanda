# coding: utf-8
from enum import Enum

from qfluentwidgets import StyleSheetBase, Theme, isDarkTheme, qconfig


class StyleSheet(StyleSheetBase, Enum):
    """ Style sheet  """

    LINK_CARD = "link_card"
    SAMPLE_CARD = "sample_card"

    FOLDER_INTERFACE = "folder_interface"
    LIST_INTERFACE = "list_interface"
    MATCH_INTERFACE = "match_interface"
    OUTPUT_INTERFACE = "output_interface"
    SETTING_INTERFACE = "setting_interface"

    def path(self, theme=Theme.AUTO):
        theme = qconfig.theme if theme == Theme.AUTO else theme
        return f"app/resource/qss/{theme.value.lower()}/{self.value}.qss"
