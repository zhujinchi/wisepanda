import cv2
import numpy as np
import matplotlib.pyplot as plt


class NotchExtractor:
    # 静态方法，不用实例化
    @staticmethod
    def _get_notch(dir):
        image = cv2.imread(dir) if dir else None
        if image is not None:
            gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            norm_image = cv2.normalize(255-gray_image, None, 0, 1.0, cv2.NORM_MINMAX, cv2.CV_32F)
            height, width, channel = image.shape


            x = [i for i in range(height)]
            row_count = [0]*height
            count = 0

            for r in range(height):
                for c in range(width):
                    if (image[r][c] - 0 > 0.001).any():
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

            for i in range(height//2):
                if top[0] == 0 and y[i] > 0:
                    top[0] = i
            for i in range(height//2, -1, -1):
                if top[1] == 0 and y[i] > 0:
                    top[1] = i
            for i in range(height//2, height):
                if bottom[0] == 0 and y[i] > 0:
                    bottom[0] = i
            for i in range(height-1, height//2, -1):
                if bottom[1] == 0 and y[i] > 0:
                    bottom[1] = i
            
            top[1] = top[1]+5
            bottom[0] = bottom[0]-5

            top_notch, bottom_notch = image[top[0]:top[1]], image[bottom[0]:bottom[1]]
        else:
            top_notch, bottom_notch = None, None
        return top_notch, bottom_notch