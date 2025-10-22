import os
import cv2
from glob import glob

def yolo_to_bbox(yolo_box, img_width, img_height):
    class_id, x_center, y_center, box_width, box_height = yolo_box
    x = int((x_center - box_width / 2) * img_width)
    y = int((y_center - box_height / 2) * img_height)
    w = int(box_width * img_width)
    h = int(box_height * img_height)
    x = max(0, x)
    y = max(0, y)
    w = min(img_width - x, w)
    h = min(img_height - y, h)
    return int(class_id), x, y, w, h

def crop_and_save_images(image_dir, label_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    
    image_files = glob(os.path.join(image_dir, '*.jpg')) + \
                  glob(os.path.join(image_dir, '*.png')) + \
                  glob(os.path.join(image_dir, '*.jpeg'))
    
    total_crops = 0
    
    for image_path in image_files:
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        label_path = os.path.join(label_dir, f"{base_name}.txt")
        
        if not os.path.exists(label_path):
            continue
        
        image = cv2.imread(image_path)
        if image is None:
            continue
        
        img_height, img_width = image.shape[:2]
        
        with open(label_path, 'r') as f:
            lines = f.readlines()
        
        for i, line in enumerate(lines):
            try:
                parts = list(map(float, line.strip().split()))
                if len(parts) < 5:
                    continue
                
                class_id, x, y, w, h = yolo_to_bbox(parts, img_width, img_height)
                crop = image[y:y+h, x:x+w]
                
                if crop.size == 0:
                    continue
                
                class_dir = os.path.join(output_dir, str(class_id))
                os.makedirs(class_dir, exist_ok=True)
                
                crop_name = f"{base_name}_crop{i}.jpg"
                crop_path = os.path.join(class_dir, crop_name)
                cv2.imwrite(crop_path, crop)
                total_crops += 1
                
            except Exception as e:
                continue

    print(f"完成！共保存 {total_crops} 个截图到 {output_dir}")

if __name__ == "__main__":
    image_directory = "./DATA/PDFWords/page_images"  
    label_directory = "./DATA/PDFWords/page_labels"  
    output_directory = "./DATA/PDFWords/Box_images"  
    crop_and_save_images(image_directory, label_directory, output_directory)