# coding:utf-8
import os
import re
import json
import csv
import sqlite3
from typing import Optional, Tuple, Dict, List

DB_PATH = os.path.join(os.path.dirname(__file__), 'match_result.db')
ANNOTATIONS_DB_PATH = os.path.join(os.path.dirname(__file__), 'annotations.db')


def normalize_path(p: str) -> str:
    if not p:
        return p
    # 统一为正斜杠，便于字符串比较
    return os.path.normpath(p).replace('\\', '/')


def counterpart_of(path: str) -> Optional[str]:
    """
    根据命名规则：xxx_1.png <-> xxx_2.png 切换对应匹配目标。
    若不符合规则，返回 None。
    """
    filename = os.path.basename(path)
    # 捕获最后一个 "_<digit>.png" 的数字
    m = re.search(r"(.*)_([12])\.png$", filename, re.IGNORECASE)
    if not m:
        return None

    prefix, d = m.group(1), m.group(2)
    other = '2' if d == '1' else '1'
    counterpart_name = f"{prefix}_{other}.png"
    # 用同目录替换文件名以得到完整路径
    dir_ = os.path.dirname(path)
    return normalize_path(os.path.join(dir_, counterpart_name))


def get_ink_annotation(conn: sqlite3.Connection, image_path: str) -> str:
    """
    从 annotations.db 获取图像的墨迹标注。
    不在数据库中的视为"没有墨迹"。
    """
    try:
        cursor = conn.execute("SELECT 墨迹 FROM annotations WHERE image_path = ?", (image_path,))
        result = cursor.fetchone()
        if result and result[0]:
            return result[0]
    except Exception:
        pass
    return "没有墨迹"


def filter_by_ink_direction(match_list_json: str, direction: str, ink_annotations: Dict[str, str]) -> List:
    """
    根据墨迹方向和标注过滤匹配列表：
    - 如果是 top_rank 且当前图片"下方有墨迹"，则只保留"上方有墨迹"的候选
    - 如果是 bottom_rank 且当前图片"上方有墨迹"，则只保留"下方有墨迹"的候选
    - 其他情况保留所有候选
    """
    try:
        items = json.loads(match_list_json)
    except Exception:
        return []
    
    if not items:
        return []
    
    # 获取当前图片的墨迹标注（从第一个item中提取）
    current_image = None
    if isinstance(items[0], (list, tuple)) and len(items[0]) >= 2:
        current_image = normalize_path(str(items[0][1]))
    elif isinstance(items[0], str):
        current_image = normalize_path(items[0])
    
    if not current_image:
        return items
    
    current_ink = ink_annotations.get(current_image, "没有墨迹")
    
    filtered_items = []
    for item in items:
        # 提取候选图片路径
        candidate_path = None
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            candidate_path = normalize_path(str(item[1]))
        elif isinstance(item, str):
            candidate_path = normalize_path(item)
        
        if not candidate_path:
            continue
            
        candidate_ink = ink_annotations.get(candidate_path, "没有墨迹")
        
        # 过滤逻辑
        should_include = True
        if direction == "top" and "下方" in current_ink and "上方" not in candidate_ink:
            should_include = False
        elif direction == "bottom" and "上方" in current_ink and "下方" not in candidate_ink:
            should_include = False
            
        if should_include:
            filtered_items.append(item)
    
    return filtered_items


def find_rank(match_list_json: str, target_path: str, direction: str = None, ink_annotations: Dict[str, str] = None) -> Optional[int]:
    """
    在 match_list（JSON，形如 [[score, path], ...]，按分数降序）中查找 target_path 的名次（1-based）。
    如果提供了 direction 和 ink_annotations，会先根据墨迹方向过滤列表再查找排名。
    找不到返回 None。
    """
    items = match_list_json
    
    # 如果提供了墨迹标注信息，先过滤列表
    if direction and ink_annotations:
        items = filter_by_ink_direction(match_list_json, direction, ink_annotations)
        # 将过滤后的列表转换为JSON字符串格式
        items = json.dumps(items) if items else "[]"
    
    try:
        items = json.loads(items)
    except Exception:
        return None

    target_norm = normalize_path(target_path)

    for idx, item in enumerate(items):
        # item 通常是 [score, path]
        if isinstance(item, (list, tuple)) and len(item) >= 2:
            path = normalize_path(str(item[1]))
            if path == target_norm:
                return idx + 1
        # 兼容异常结构：若直接存 path
        elif isinstance(item, str) and normalize_path(item) == target_norm:
            return idx + 1

    return None


def main():
    if not os.path.exists(DB_PATH):
        print(f"未找到数据库：{DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # 读取墨迹标注信息
    ink_annotations = {}
    if os.path.exists(ANNOTATIONS_DB_PATH):
        try:
            ann_conn = sqlite3.connect(ANNOTATIONS_DB_PATH)
            ann_cursor = ann_conn.execute("SELECT image_path, 墨迹 FROM annotations")
            for row in ann_cursor.fetchall():
                ink_annotations[normalize_path(row[0])] = row[1] if row[1] else "没有墨迹"
            ann_conn.close()
            print(f"已加载 {len(ink_annotations)} 条墨迹标注")
        except Exception as e:
            print(f"读取墨迹标注失败：{e}")
    else:
        print(f"未找到墨迹标注数据库：{ANNOTATIONS_DB_PATH}")

    # 读取所有记录
    rows = conn.execute("SELECT image_path, direction, match_list FROM match_result").fetchall()

    # 聚合：每个 image_path 分别可能有 top/bottom 两条
    data: Dict[Tuple[str, str], str] = {}
    images = set()
    for r in rows:
        img = normalize_path(r['image_path'])
        direction = r['direction']
        match_list = r['match_list']
        data[(img, direction)] = match_list
        images.add(img)

    # 计算每张 png 的对应对手排名
    results = []
    total_pairs = 0
    cnt_lt50 = 0
    cnt_lt100 = 0
    cnt_lt300 = 0
    for img in sorted(images):
        if not img.lower().endswith('.png'):
            continue

        target = counterpart_of(img)
        if not target:
            # 不符合 _1/_2 规则的图片，跳过或记录为空
            results.append({
                'image': os.path.basename(img),
                'counterpart': '',
                'current_ink': ink_annotations.get(img, "没有墨迹"),
                'target_ink': '',
                'top_rank': '',
                'bottom_rank': '',
                'any_lt50': '',
                'any_lt100': '',
                'any_lt300': ''
            })
            continue

        # top 方向（根据墨迹标注过滤）
        top_json = data.get((img, 'top'))
        top_rank = find_rank(top_json, target, 'top', ink_annotations) if top_json else None

        # bottom 方向（根据墨迹标注过滤）
        bottom_json = data.get((img, 'bottom'))
        bottom_rank = find_rank(bottom_json, target, 'bottom', ink_annotations) if bottom_json else None

        # 阈值判断（任一方向满足即可）
        def hit(threshold: int) -> bool:
            return (top_rank is not None and top_rank <= threshold) or (bottom_rank is not None and bottom_rank <= threshold)

        any50 = hit(50)
        any100 = hit(100)
        any300 = hit(300)

        total_pairs += 1
        if any50:
            cnt_lt50 += 1
        if any100:
            cnt_lt100 += 1
        if any300:
            cnt_lt300 += 1

        # 获取墨迹标注信息用于显示
        current_ink = ink_annotations.get(img, "没有墨迹")
        target_ink = ink_annotations.get(target, "没有墨迹")
        
        results.append({
            'image': os.path.basename(img),
            'counterpart': os.path.basename(target),
            'current_ink': current_ink,
            'target_ink': target_ink,
            'top_rank': top_rank if top_rank is not None else '',
            'bottom_rank': bottom_rank if bottom_rank is not None else '',
            'any_lt50': 'Y' if any50 else 'N',
            'any_lt100': 'Y' if any100 else 'N',
            'any_lt300': 'Y' if any300 else 'N'
        })

    # 导出 CSV
    out_path = os.path.join(os.path.dirname(DB_PATH), 'ranking_report.csv')
    with open(out_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=['image', 'counterpart', 'current_ink', 'target_ink', 'top_rank', 'bottom_rank', 'any_lt50', 'any_lt100', 'any_lt300'])
        writer.writeheader()
        for row in results:
            writer.writerow(row)

    print(f"已生成排名报告：{out_path}")
    print("注意：排名已根据墨迹标注进行过滤优化")
    # 统计信息
    if total_pairs > 0:
        print(f"总对数: {total_pairs}")
        print(f"rank <= 50 的对数: {cnt_lt50}  (占比 {cnt_lt50/total_pairs:.2%})")
        print(f"rank <= 100 的对数: {cnt_lt100} (占比 {cnt_lt100/total_pairs:.2%})")
        print(f"rank <= 300 的对数: {cnt_lt300} (占比 {cnt_lt300/total_pairs:.2%})")


if __name__ == '__main__':
    main()


