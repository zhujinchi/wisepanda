import cv2
import numpy as np
import sqlite3
import os


class NotchExtractor:
    def __init__(self, img_dir: str = None, db_path: str = "annotations.db"):

        self.image_path = os.path.normpath(img_dir).replace("\\", "/")
        self.image = cv2.imread(img_dir) if img_dir else None
        if self.image is not None:
            self.height, self.width, self.channel = self.image.shape
        else:
            self.height, self.width, self.channel = 0, 0, 0
        self.top_notch, self.bottom_notch = None, None
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notch_info (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image_path TEXT UNIQUE,
                top_start INTEGER,
                top_end INTEGER,
                bottom_start INTEGER,
                bottom_end INTEGER
            )
        ''')
        conn.commit()
        conn.close()

    def _save_slice(self, direction: str, slice: list):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        self.image_path = os.path.normpath(self.image_path).replace("\\", "/")

        # 判断是否已存在记录
        cursor.execute('SELECT id FROM notch_info WHERE image_path=?', (self.image_path,))
        row = cursor.fetchone()

        if row is None:
            # 新增记录，部分字段为 NULL
            if direction == "top":
                cursor.execute('''
                    INSERT INTO notch_info (image_path, top_start, top_end)
                    VALUES (?, ?, ?)
                ''', (self.image_path, slice[0], slice[1]))
            else:  # bottom
                cursor.execute('''
                    INSERT INTO notch_info (image_path, bottom_start, bottom_end)
                    VALUES (?, ?, ?)
                ''', (self.image_path, slice[0], slice[1]))
        else:
            # 更新对应字段
            if direction == "top":
                cursor.execute('''
                    UPDATE notch_info SET top_start=?, top_end=?
                    WHERE image_path=?
                ''', (slice[0], slice[1], self.image_path))
            else:
                cursor.execute('''
                    UPDATE notch_info SET bottom_start=?, bottom_end=?
                    WHERE image_path=?
                ''', (slice[0], slice[1], self.image_path))

        conn.commit()
        conn.close()


    def _extract(self, direction):
        slice_from_db = self.get_slice_from_db(direction)
        if slice_from_db:
            slice = list(slice_from_db)
        else:
            gray_image = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
            norm_image = cv2.normalize(255 - gray_image, None, 0, 1.0, cv2.NORM_MINMAX, cv2.CV_32F)
            slice = self._get_notch(norm_image, direction)
            self._save_slice(direction, slice)  # 新提取则存储到数据库
        notch = self.image[slice[0]:slice[1]]
        return notch

    def _get_notch(self, image, direction):
        x = [i for i in range(self.height)]
        row_count = [0] * self.height
        count = 0

        for r in range(self.height):
            for c in range(self.width):
                if image[r][c] - 0 > 0.001:
                    count += 1
            row_count[r] = count
            count = 0

        y = [abs(row_count[x[i]] - row_count[x[i - 1]]) for i in range(1, len(x))]
        y.append(y[-1])

        counts = np.bincount(y)
        counts = np.delete(counts, 0, axis=0)
        y = [i if i != (np.argmax(counts) + 1) else 0 for i in y]
        counts = np.delete(counts, 0, axis=0)
        y = [i if i != (np.argmax(counts) + 2) else 0 for i in y]

        slice = [0] * 2
        if direction == "top":
            for i in range(self.height // 2):
                if slice[0] == 0 and y[i] > 0:
                    slice[0] = i
            for i in range(self.height // 2, -1, -1):
                if slice[1] == 0 and y[i] > 0:
                    slice[1] = i
            slice[1] = slice[1] + 5
        else:
            for i in range(self.height // 2, self.height):
                if slice[0] == 0 and y[i] > 0:
                    slice[0] = i
            for i in range(self.height - 1, self.height // 2, -1):
                if slice[1] == 0 and y[i] > 0:
                    slice[1] = i
            slice[0] = slice[0] - 5

        return slice

    def extract_top(self):
        self.top_notch = self._extract("top")
        return self.top_notch

    def extract_bottom(self):
        self.bottom_notch = self._extract("bottom")
        return self.bottom_notch

    def get_slice_from_db(self, direction: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if direction == "top":
            cursor.execute('''
                SELECT top_start, top_end FROM notch_info WHERE image_path=?
            ''', (self.image_path,))
        else:
            cursor.execute('''
                SELECT bottom_start, bottom_end FROM notch_info WHERE image_path=?
            ''', (self.image_path,))
        result = cursor.fetchone()
        conn.close()
        if result is None or result[0] is None or result[1] is None:
            return None
        return result