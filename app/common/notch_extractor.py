import cv2
import numpy as np
import matplotlib.pyplot as plt


class NotchExtractor:
    def __init__(self, img_dir:str=None):
        self.image = cv2.imread(img_dir) if img_dir else None
        if self.image is not None:
            self.height, self.width, self.channel = self.image.shape
            self.top_notch, self.bottom_notch = self.__extract()
        else:
            self.height, self.width, self.channel = 0, 0, 0
            self.top_notch, self.bottom_notch = None, None

    def __extract(self):
        gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        norm_image = cv2.normalize(255-gray_image, None, 0, 1.0, cv2.NORM_MINMAX, cv2.CV_32F)
        top, bottom = self._get_notch(norm_image)
        top_notch, bottom_notch = self.image[top[0]:top[1]], self.image[bottom[0]:bottom[1]]
        return top_notch, bottom_notch
    
    def _get_notch(self, image):
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
        counts = np.delete(counts, 0, axis=0)
        y = [i if i != (np.argmax(counts)+1) else 0 for i in y]
        counts = np.delete(counts, 0, axis=0)
        y = [i if i != (np.argmax(counts)+2) else 0 for i in y]

        top = [0]*2
        bottom = [0]*2

        for i in range(self.height//2):
            if top[0] == 0 and y[i] > 0:
                top[0] = i
        for i in range(self.height//2, -1, -1):
            if top[1] == 0 and y[i] > 0:
                top[1] = i
        for i in range(self.height//2, self.height):
            if bottom[0] == 0 and y[i] > 0:
                bottom[0] = i
        for i in range(self.height-1, self.height//2, -1):
            if bottom[1] == 0 and y[i] > 0:
                bottom[1] = i
        
        top[1] = top[1]+5
        bottom[0] = bottom[0]-5

        return top, bottom
    
    def generate_image(self):
        #  差一个保存截取到的图片的功能
        if self.top_notch is not None:
            cv2.imwrite("top_notch.png", self.top_notch)