import cv2

def plot_image(image_hwc_bgr, boxes_np, cls_probs):
    prob_num,_ = cls_probs.shape
    box_num,_  = boxes_np.shape
    
    assert(box_num == prob_num)
    
    plot_image = image_hwc_bgr.copy()
    for i in range(box_num):
        box_info_list = boxes_np[i,:].tolist()
        xyxy = box_info_list[:4]
        # conf = box_info_list[4]
        box_prob = cls_probs[i,0]
        
        xyxy = [int(_val) for _val in xyxy]
        x1,y1,x2,y2 = xyxy
        
        c1 = (x1,y1)
        c2 = (x2,y2)
        box_color = [0,120,200]
        cv2.rectangle(plot_image, c1, c2, color=box_color, thickness=5)
        
        label = '{:.2f}'.format(box_prob)
        front_scale = 1
        t_size = cv2.getTextSize(label, 0, fontScale=front_scale, thickness=3)[0]
        c2 = c1[0] + t_size[0], c1[1] - t_size[1] - 3
        cv2.rectangle(plot_image, c1, c2, box_color, -1, cv2.LINE_AA)  # filled
        cv2.putText(plot_image, label, (c1[0], c1[1] - 2), 0, front_scale, [225, 255, 255], thickness=3, lineType=cv2.LINE_AA)
        
    return plot_image