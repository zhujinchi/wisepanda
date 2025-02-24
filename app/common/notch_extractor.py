import cv2
import numpy as np


class NotchExtractor:  # 用于图像中的“缺口”提取，特别是在图像分析和处理过程中需要分割图像的上下部分
    def __init__(self, img_dir:str=None):
        self.image = cv2.imread(img_dir) if img_dir else None
        if self.image is not None:
            self.height, self.width, self.channel = self.image.shape
        else:
            self.height, self.width, self.channel = 0, 0, 0
        self.top_notch, self.bottom_notch = None, None

    def _extract(self, direction):  # 将图像转化为灰度图像并进行归一化处理。根据该图像，提取上下“缺口”区域
        gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        norm_image = cv2.normalize(255-gray_image, None, 0, 1.0, cv2.NORM_MINMAX, cv2.CV_32F)
        slice = self._get_notch(norm_image, direction)
        notch = self.image[slice[0]:slice[1]]
        return notch
    
    def _get_notch(self, image, direction):
        x = [i for i in range(self.height)]
        row_count = [0]*self.height
        count = 0

        for r in range(self.height):
            for c in range(self.width):
                if image[r][c]-0 > 0.001:
                    count += 1
            row_count[r] = count
            count = 0

        y = [abs(row_count[x[i]]-row_count[x[i-1]]) for i in range(1, len(x))]
        y.append(y[-1])
        counts = np.bincount(y)
        # bincount统计众数之后数量最多的值0, 其次是1, 再次为2
        # 去除统计到的值0, 这样argmax返回的是值1
        counts = np.delete(counts, 0, axis=0)
        # 再将1的值置为0
        y = [i if i != (np.argmax(counts)+1) else 0 for i in y]
        # 去除统计到的1值
        counts = np.delete(counts, 0, axis=0)
        # 再将2的值置为0
        y = [i if i != (np.argmax(counts)+2) else 0 for i in y]

        slice = [0]*2

        if direction == "top":
            for i in range(self.height//2):
                if slice[0] == 0 and y[i] > 0:
                    slice[0] = i
            for i in range(self.height//2, -1, -1):
                if slice[1] == 0 and y[i] > 0:
                    slice[1] = i
            slice[1] = slice[1]+5
        else:
            for i in range(self.height//2, self.height):
                if slice[0] == 0 and y[i] > 0:
                    slice[0] = i
            for i in range(self.height-1, self.height//2, -1):
                if slice[1] == 0 and y[i] > 0:
                    slice[1] = i
            slice[0] = slice[0]-5

        return slice
    
    def extract_top(self):  # 提取图像的上半部分区域
        self.top_notch = self._extract("top")
        return self.top_notch
    
    def extract_bottom(self):
        self.bottom_notch = self._extract("bottom")
        return self.bottom_notch