import os

import numpy as np
import torch
from PIL import Image, ImageFilter
from torch.utils import data
import random
from torchvision.transforms import transforms

import sys
sys.path.append('./')
from utils.box_transform import xywh2xyxy,box_trans,cal_iou
from utils.process import cut_half_image,extract_black_text,extract_angled_horizontal_strokes_tensor,calculate_contribution_value,slips_kmeans

image_format = set(['png','jpg','jpeg'])

class BoxDataSet_v1(data.Dataset):
    def __init__(self, cfg, datatype='train'):
        print("BoxDataSet_v1 For Slips Stage1 (KMeans)")
        self.cache = True
        
        self.cfg  = cfg.copy()
        data_set_list = cfg['data'][datatype]
        
        # Add middle blur parameters
        self.middle_blur = cfg['middle_blur']
        
        self.label_count_map = {}
        self.process_list   = []
                
        for data_set in data_set_list:
            data_path   = data_set['dataset_path']
            image_path  = data_set['images_path']
            label_path  = data_set['labels_path']
            cls_file    = data_set['obj_name']
            list_file   = data_set['list_file']
            relabel_map = data_set['label_remap']
            
            label_idx_map = {}
            with open(os.path.join(data_path,cls_file), 'r') as f:
                label_id = 0
                for line in f:
                    label_name = line.strip('\n')
                    label_idx_map[str(label_id)] = label_name
                    label_id += 1
      
            with open(os.path.join(data_path,list_file),'r') as f:
                for line in f:
                    img_path_ele  = line.strip('\n').split('/')
                    img_full_path = os.path.join(image_path,img_path_ele[-1])
                    image_name = img_path_ele[-1].split('.')
                    label_file_path = os.path.join(label_path, image_name[0] + ".txt")
                    try:
                        assert(os.path.isfile(img_full_path))
                        assert(os.path.isfile(label_file_path))
                    except:
                        print('error:',img_full_path,'file or label not exists')
                        
                    label_full_path = os.path.join(data_path,label_file_path)
                    if not os.path.exists(label_full_path):
                        continue
                                                   
                    with open(os.path.join(data_path,label_file_path),'r') as label_f:
                        
                        all_box_coords = []
                        for label_line in label_f:
                            line_ele = label_line.split(' ')
                            
                            box_label_id, cx, cy, cw, ch = line_ele
                            all_box_coords.append([float(cx), float(cy), float(cw), float(ch)])
                            ori_label_name = label_idx_map[box_label_id]
                            
                            new_label_id = relabel_map['unpair']
                            if ori_label_name in relabel_map:
                                new_label_id = relabel_map[ori_label_name]
                                
                            if new_label_id not in self.label_count_map:
                                self.label_count_map[new_label_id] = 0
                            self.label_count_map[new_label_id] += 1
                            # print(self.label_count_map, new_label_id)
                            
                            line_ele[0] = str(new_label_id)
                            self.process_list.append([img_full_path, line_ele, None])
                            
                        all_box_np = np.array(all_box_coords)
                        cur_box_num  = len(all_box_coords)
                        
                        #random public negtive sample added while training
                        if datatype == 'train' and cfg['data']['public_neg_extend'] and cur_box_num > 0:
                            rand_coord = []
                            p_neg_box_num = min(cur_box_num,2)
                            for r_num in range(p_neg_box_num):
                                r_cx = 0.8 * random.random() + 0.1
                                r_cy = 0.8 * random.random() + 0.1
                                
                                max_w = min(r_cx, 1- r_cx) * 2
                                max_h = min(r_cy, 1- r_cy) * 2
                                
                                r_cw = (0.3 + 0.7 * random.random()) * max_w
                                r_ch = (0.3 + 0.7 * random.random()) * max_h
                                
                                rand_coord.append([r_cx,r_cy,r_cw,r_ch])
                            rand_coord_np = np.array(rand_coord)
                            
                            iou_matrix = cal_iou(rand_coord_np,all_box_np,input_type='xywh')
                            
                            for r_num in range(p_neg_box_num):
                                if iou_matrix[r_num,:].max() < 0.2:
                                    new_label_id = relabel_map['other']
                                    if new_label_id not in self.label_count_map:
                                        self.label_count_map[new_label_id] = 0
                                    self.label_count_map[new_label_id] += 1
                                    add_line_ele   = [str(new_label_id)]
                                    str_line_coord = [str(_num) for _num in rand_coord[r_num]]
                                    add_line_ele.extend(str_line_coord)
                                    self.process_list.append([img_full_path, add_line_ele, None]) 
            
        print(datatype, ':', self.label_count_map)

        transform_cfg = cfg['data']['transforms']

        transforms_list = []
        
        if 'RandomHorizontalFlip' in transform_cfg:
            if transform_cfg['RandomHorizontalFlip']['turn_on']:
                tmp_cfg = transform_cfg['RandomHorizontalFlip']
                transforms_list.append(transforms.RandomHorizontalFlip(p=tmp_cfg['prob']))
        else:
            transforms_list.append(transforms.RandomHorizontalFlip(p=0.5))

        if 'RandomGrayscale' in transform_cfg:
            if transform_cfg['RandomGrayscale']['turn_on']:
                tmp_cfg = transform_cfg['RandomGrayscale']
                transforms_list.append(transforms.RandomGrayscale(p=tmp_cfg['prob']))
        else:
            transforms_list.append(transforms.RandomGrayscale(p=0.1))

        if 'RandomEqualize' in transform_cfg:
            if transform_cfg['RandomEqualize']['turn_on']:
                tmp_cfg = transform_cfg['RandomEqualize']
                transforms_list.append(transforms.RandomEqualize(p=tmp_cfg['prob']))
        else:
            transforms_list.append(transforms.RandomEqualize(p=0.1))

        if 'RandomAffine' in transform_cfg:
            if transform_cfg['RandomAffine']['turn_on']:
                tmp_cfg = transform_cfg['RandomAffine']
                transforms_list.append(transforms.RandomAffine(degrees=tmp_cfg['degrees'], translate=tmp_cfg['translate'],scale=tmp_cfg['scale'],shear=tmp_cfg['shear']))
        else:
            transforms_list.append(transforms.RandomAffine(degrees=10, translate=(0.1,0.),scale=(0.9,1.1),shear=10))

        if 'ColorJitter' in transform_cfg:
            if transform_cfg['ColorJitter']['turn_on']:
                tmp_cfg = transform_cfg['ColorJitter']
                transforms_list.append(transforms.ColorJitter(brightness=tmp_cfg['brightness'], contrast=tmp_cfg['contrast'],saturation=tmp_cfg['saturation'],hue=tmp_cfg['hue']))
        else:
            transforms_list.append(transforms.ColorJitter(brightness=0.5, contrast=0.5,saturation=0.5,hue=0.5))

           
        if 'gaussianblur' in transform_cfg and transform_cfg['gaussianblur']['turn_on']:
            tmp_cfg = transform_cfg['gaussianblur']
            transforms_list.append(transforms.GaussianBlur(kernel_size=tmp_cfg['g_bulr_kernel'],sigma=tmp_cfg['g_bulr_sigma']))
        
        self.data_augment   = transforms.Compose(transforms_list)
        self.resize_224_224 = transforms.Resize((224,224),antialias=False)
        self.resize_256_192 = transforms.Resize((256,192),antialias=False)
        self.to_tensor      = transforms.ToTensor()
        self.datatype       = datatype
        
        self.extend_rate = [0.5,0.3]
        
    def check_img_224(self, image_tensor:torch.Tensor):
        c,h,w = image_tensor.shape
        if c == 3 and h == 224 and w == 224:
            return True
        else:
            return False
        
    def check_img_256(self, image_tensor:torch.Tensor):
        c,h,w = image_tensor.shape
        if c == 3 and h == 256 and w == 192:
            return True
        else:
            return False
    
    def apply_middle_blur(self, image):
        if not self.middle_blur['enable']:
            return image
        
        width, height = image.size
        blur_radius = self.middle_blur['blur_radius']
        min_width = self.middle_blur['min_width']
        max_width = self.middle_blur['max_width']
        
        # Calculate a random blur width within the range
        blur_width = random.randint(min_width, max_width)
        
        # Calculate the middle strip boundaries
        left_boundary = (width - blur_width) // 2
        right_boundary = left_boundary + blur_width
        
        # Create a copy of the image
        result = image.copy()
        
        # Create a mask for the middle part
        mask = Image.new('L', (width, height), 0)
        for y in range(height):
            for x in range(left_boundary, right_boundary):
                mask.putpixel((x, y), 255)
        
        # Apply blur to the middle region
        blurred = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        
        # Paste the blurred region onto the result using the mask
        result.paste(blurred, (0, 0), mask)
        
        return result
        
    def __getitem__(self, index):
        image_path,label_info,_box_image = self.process_list[index]
        
        label, x, y, w, h = label_info
        label    = int(label)
        
        if _box_image is None:
            img = Image.open(image_path)
            img_w, img_h = img.size

            xywh_box = np.array([[float(x), float(y), float(w), float(h)]])
            xyxy_box = xywh2xyxy(xywh_box)[0] #one box only
            xyxy_box = box_trans(xyxy_box, img_w, img_h, self.extend_rate)
            box_image = img.crop(xyxy_box)

            if self.cache:
                self.process_list[index][2] = box_image
        else:
            box_image = _box_image
                
        box_image = box_image.convert('RGB')
        
        if self.datatype == 'train':
            box_image = self.data_augment(box_image)
        
        # Apply middle blur
        box_image = self.apply_middle_blur(box_image)
        
        # Resize and convert to tensors
        box_image_224 = self.to_tensor(self.resize_224_224(box_image))
        box_image_256 = self.to_tensor(self.resize_256_192(box_image))
        
        if not self.check_img_224(box_image_224):
            print(self.process_list[index], index, box_image_224.shape)
            
        if not self.check_img_256(box_image_256):
            print(self.process_list[index], index, box_image_256.shape)
        
        box_image_256_left, box_image_256_right = cut_half_image(box_image_256)

        grey_left, binary_left  = extract_black_text(box_image_256_left)
        grey_right, binary_right = extract_black_text(box_image_256_right)

        horizontal_strokes_left, angle_vis_left = extract_angled_horizontal_strokes_tensor(binary_left)
        horizontal_strokes_right, angle_vis_right = extract_angled_horizontal_strokes_tensor(binary_right)

        horizontal_strokes_kmeans_left  = slips_kmeans(horizontal_strokes_left, n_clusters=2, n_init=10)
        horizontal_strokes_kmeans_right = slips_kmeans(horizontal_strokes_right, n_clusters=2, n_init=10)

        
        C_left, contribution_map_left   = calculate_contribution_value(horizontal_strokes_kmeans_left, edge_x=96, lambda_value=0.2) 
        C_right, contribution_map_right = calculate_contribution_value(horizontal_strokes_kmeans_right, edge_x=0, lambda_value=0.2)
        
        contribution_map_left_reshaped  = contribution_map_left[np.newaxis, :, :]
        contribution_map_right_reshaped = contribution_map_right[np.newaxis, :, :]
        
        horizontal_strokes_left_entrophy  = horizontal_strokes_kmeans_left * contribution_map_left_reshaped
        horizontal_strokes_right_entrophy = horizontal_strokes_kmeans_right * contribution_map_right_reshaped
        horizontal_strokes_combined_entrophy = torch.cat([horizontal_strokes_left_entrophy, horizontal_strokes_right_entrophy], dim=0)

        horizontal_strokes_left_entrophy_ = torch.cumsum(horizontal_strokes_left_entrophy, dim=-1)
        horizontal_strokes_left_entrophy_sum = horizontal_strokes_left_entrophy_[:, :, -1]
        
        horizontal_strokes_right_entrophy_ = torch.cumsum(horizontal_strokes_right_entrophy.flip(dims=[-1]), dim=-1)
        horizontal_strokes_right_entrophy_sum = horizontal_strokes_right_entrophy_[:, :, -1]

        horizontal_strokes_entrophy_combine_sum = torch.cat([horizontal_strokes_left_entrophy_sum, horizontal_strokes_right_entrophy_sum], dim=0)
        
        output_dict = {'img_224': box_image_224, 'img_256': box_image_256, 'img_256_entorphy': horizontal_strokes_combined_entrophy,'img_256_entorphy_sum': horizontal_strokes_entrophy_combine_sum, 'label': label, 'img_path': image_path, 'label_info': label_info}
        
        return output_dict
    
    def __len__(self):
        return len(self.process_list)


if __name__ == '__main__':
    import yaml
    with open('./config/config-v21.yaml','r') as f:
        cfg = yaml.load(f.read(),Loader=yaml.FullLoader)
    
    # Add middle blur configuration to the config if not already present
    if 'middle_blur' not in cfg:
        cfg['middle_blur'] = {
            'enable': True,
            'min_width': 10,
            'max_width': 15,
            'blur_radius': 5
        }
    
    # print(cfg)
    box_Data = BoxDataSet_v1(cfg, datatype='valid')
    
    from torch.utils.data import DataLoader
    from tqdm import tqdm
    box_data_loader = DataLoader(box_Data, batch_size=128, shuffle=True, num_workers=4, pin_memory=False, drop_last=False)
    
    data_num = 0
    
    for data_cell in tqdm(box_data_loader):
        data_num += 1
        # print(data_num)
        # print(data_cell['img_224'].shape)
        print('img_256', data_cell['img_256'].shape)
        print('img_256_entorphy', data_cell['img_256_entorphy'].shape)  #[bs, 2, 256, 96]
        print('img_256_entorphy_sum', data_cell['img_256_entorphy_sum'].shape) #[bs, 2, 256]