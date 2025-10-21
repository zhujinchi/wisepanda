import sqlite3
import json

class MatchDB:
    def __init__(self, db_path="match_result.db"):
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self):
        self.conn.execute('''
        CREATE TABLE IF NOT EXISTS match_result (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_path TEXT NOT NULL,
            direction TEXT NOT NULL CHECK (direction IN ('top', 'bottom')),
            match_list TEXT NOT NULL,
            UNIQUE(image_path, direction)
        )
        ''')

        self.conn.execute('''
                CREATE TABLE IF NOT EXISTS match_confirm (
                    image1 TEXT PRIMARY KEY,
                    image2 TEXT,
                    image3 TEXT,
                    timestamp TEXT NOT NULL
                )
            ''')
        self.conn.commit()

    def save_match(self, image_path: str, direction: str, match_list: list):
        match_list_json = json.dumps(match_list, ensure_ascii=False)
        try:
            self.conn.execute('''
            INSERT OR REPLACE INTO match_result (image_path, direction, match_list)
            VALUES (?, ?, ?)
            ''', (image_path, direction, match_list_json))
            self.conn.commit()
        except sqlite3.Error as e:
            print("数据库保存失败：", e)

    def update_match_confirm(self, image1: str, match_path: str, direction: str,timestamp):
        """
        更新 match_confirm 表中的 image2 或 image3
        :param image1: 原图路径
        :param match_path: 匹配的图片路径
        :param direction: 'top' 或 'bottom'
        """

        try:
            # 查询已有数据
            cursor = self.conn.execute('''
                SELECT image2, image3 FROM match_confirm WHERE image1 = ?
            ''', (image1,))
            row = cursor.fetchone()

            if row:
                image2, image3 = row
            else:
                image2, image3 = None, None

            # 根据方向更新对应字段
            if direction == 'top':
                image2 = match_path
            elif direction == 'bottom':
                image3 = match_path
            else:
                print("非法方向参数：应为 'top' 或 'bottom'")
                return

            # 插入或更新
            self.conn.execute('''
                INSERT OR REPLACE INTO match_confirm (image1, image2, image3, timestamp)
                VALUES (?, ?, ?, ?)
            ''', (image1, image2, image3, timestamp))
            self.conn.commit()
        except sqlite3.Error as e:
            print("数据库更新失败：", e)

    def get_match(self, image_path: str, direction: str):
        cursor = self.conn.execute('''
        SELECT match_list FROM match_result
        WHERE image_path=? AND direction=?
        ''', (image_path, direction))
        row = cursor.fetchone()
        if row:
            return json.loads(row[0])
        return None