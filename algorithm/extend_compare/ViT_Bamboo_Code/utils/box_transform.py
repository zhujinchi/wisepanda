import torch
import numpy as np

def xyxy2xywh(x):
    # Convert nx4 boxes from [x1, y1, x2, y2] to [x, y, w, h] where xy1=top-left, xy2=bottom-right
    y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
    y[:, 0] = (x[:, 0] + x[:, 2]) / 2  # x center
    y[:, 1] = (x[:, 1] + x[:, 3]) / 2  # y center
    y[:, 2] = x[:, 2] - x[:, 0]  # width
    y[:, 3] = x[:, 3] - x[:, 1]  # height
    return y

def xywh2xyxy(x):
    # Convert nx4 boxes from [x, y, w, h] to [x1, y1, x2, y2] where xy1=top-left, xy2=bottom-right
    y = x.clone() if isinstance(x, torch.Tensor) else np.copy(x)
    y[:, 0] = x[:, 0] - x[:, 2] / 2  # top left x
    y[:, 1] = x[:, 1] - x[:, 3] / 2  # top left y
    y[:, 2] = x[:, 0] + x[:, 2] / 2  # bottom right x
    y[:, 3] = x[:, 1] + x[:, 3] / 2  # bottom right y
    return y

def cal_iou(_box1,_box2,input_type='xyxy'):
    
    assert(input_type in set(['xyxy','xywh']))
    
    if input_type == 'xywh':
        box1 = xywh2xyxy(_box1)
        box2 = xywh2xyxy(_box2)
    else:
        box1 = _box1.copy()
        box2 = _box2.copy()
    
    x11, y11, x12, y12 = np.split(box1, 4, axis=1)
    x21, y21, x22, y22 = np.split(box2, 4, axis=1)
    
    xa = np.maximum(x11, np.transpose(x21))
    xb = np.minimum(x12, np.transpose(x22))
    ya = np.maximum(y11, np.transpose(y21))
    yb = np.minimum(y12, np.transpose(y22))
    
    inter_area = np.maximum(0, (xb - xa)) * np.maximum(0, (yb - ya))
    box1_area = (x12 - x11) * (y12 - y11)
    box2_area = (x22 - x21) * (y22 - y21)
    
    union_area = box1_area + np.transpose(box2_area) - inter_area
    iou_metrix = (inter_area + 1e-12) / (union_area + 1e-6)
    return iou_metrix

def box_trans(xyxy, w, h, extend_r_xy, norm=True):
    x1,y1,x2,y2 = xyxy
    
    if norm:
        x1 *= w
        y1 *= h
        x2 *= w
        y2 *= h

    box_width  = x2 - x1 
    box_height = y2 - y1

    extend_r_x, extend_r_y = extend_r_xy
    extend_y = int(box_height * extend_r_y / 2)
    extend_x = int(box_width * extend_r_x / 2)

    y_u = max(0, y1 - extend_y)
    y_d = min(h, y2 + extend_y)
    x_l = max(0, x1 - extend_x)
    x_r = min(w, x2 + extend_x)

    return [x_l, y_u, x_r, y_d]