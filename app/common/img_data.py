from app.common.notch_extractor import NotchExtractor
from app.common.score_calculator import ScoreCalculator


class ImageData:
    def __init__(self, dir_str, file_list):
        self._dir = dir_str  # 保存dir字符串
        self._top_edge = None  # 初始化top edge为空
        self._bottom_edge = None  # 初始化bottom edge为空
        self._top_edge_match_list = []  # 初始化top_edge_match_list为空列表
        self._bottom_edge_match_list = []  # 初始化bottom_edge_match_list为空列表
        if dir_str is not None:
            notch_extractor = NotchExtractor(dir_str)
            top_part_img, bottom_part_img = notch_extractor.extract_top(), notch_extractor.extract_bottom()
            # 上截区的计算结果list
            self._top_edge_match_list = ScoreCalculator.get_score('bottom', top_part_img, file_list)
            # 下截区的计算结果list
            self._bottom_edge_match_list = ScoreCalculator.get_score('top', bottom_part_img, file_list)


    def get_dir(self):
        return self._dir

    def get_top_edge_match_list(self):
        return self._top_edge_match_list

    def get_bottom_edge_match_list(self):
        return self._bottom_edge_match_list
