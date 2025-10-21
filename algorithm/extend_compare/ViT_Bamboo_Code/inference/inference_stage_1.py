import torch
import torch.nn as nn
import numpy as np
import yaml
import cv2
import sys
from torchvision.transforms import Resize
from utils.extern.yolov7_extern import letterbox, non_max_suppression, scale_coords
from utils.box_transform import box_trans,xyxy2xywh
from utils.process import cut_half_image,extract_black_text,extract_angled_horizontal_strokes_tensor,calculate_contribution_value
from DataLoader.FoundationModelInf.BMIFactory import BaseModelFnMap
from model.DecoderFactory import Decoder_map

class PipelineInference(nn.Module):
    def __init__(self, det_cfg="", base_cfg="", decoder_cfg=""):
        super().__init__()
        
        self.cfg_det         = None
        self.cfg_base        = None
        
        self.det_model        = None
        self.recg_pre_process = {}
        self.base_model       = {}
        self.decoder_models   = {}
        self.slips_recog      = {}
            
        #load base jit
        with open(base_cfg,'r') as f:
            self.cfg_base = yaml.load(f,Loader=yaml.FullLoader)
        for model_name in self.cfg_base:
            model_info = self.cfg_base[model_name]
            self.recg_pre_process[model_name]={}
            self.recg_pre_process[model_name]['resize_fn']  = Resize(model_info['input_shape'],antialias=True)
            self.recg_pre_process[model_name]['input_type'] = model_info['input_type']
            self.base_model[model_name] = torch.jit.load(model_info['path']).cuda().half()
        
        #load decoders
        if isinstance(decoder_cfg,str):
            with open(decoder_cfg,'r') as f:
                self.decoder_cfg = yaml.load(f,Loader=yaml.FullLoader)
                for func_name in self.decoder_cfg:
                    model_path = self.decoder_cfg[func_name]['model_path']
                    self.decoder_models[func_name] = torch.jit.load(model_path).cuda().half()
        else:
                for func_name in decoder_cfg:
                    cfg_file, model_path = decoder_cfg[func_name]

                    with open(cfg_file,'r') as f:
                        cfg_decoder = yaml.load(f,Loader=yaml.FullLoader)

                    model_key   = cfg_decoder['model']['decoder_key']
                    decoder_fn  = Decoder_map[model_key]
                    act_decoder = decoder_fn(cfg_decoder)
                    model_params = torch.load(model_path)
                    act_decoder.load_state_dict(model_params)
                    act_decoder.eval()
                    self.decoder_models[func_name] = act_decoder.cuda().half()

    def inference_path(self,image_path, res_norm=False, res_xywh=False):
        image_rgb = cv2.imread(image_path)[:,:,::-1]
        return self.forward(image_rgb, res_norm, res_xywh)
            
    def forward(self, image_rgb, res_norm=False, res_xywh=False):
        with torch.no_grad():
            
            #inference detection model For Slips
            height, width = image_rgb.shape[:2]
            boxes_np = [[0, 0, width, height]]
            boxes_np = np.array(boxes_np)
            
            boxes_num     = boxes_np.shape
            if boxes_num == 0:
                return [{}, boxes_np]
            
            #inference basemodel
            mid_datas  = self.prep_box_img(image_rgb,boxes_np)
            decoder_input = {}
            foundation_model   = {}
            f_model_input_cfg  = []
            base_model_cfg     = self.cfg_base

            for model_name in self.base_model:
                if model_name == 'slips':
                    continue
                cur_cfg                      = base_model_cfg[model_name]
                weight_file_path             = cur_cfg['path']
                base_model_fn                = BaseModelFnMap[model_name](weight_file_path)
                foundation_model[model_name] = base_model_fn
                f_model_input_cfg.append([cur_cfg['decode_idx'],cur_cfg['input_key'],model_name])
            f_model_input_cfg = sorted(f_model_input_cfg, key=lambda cell:cell[0])

            
            # YOLO cropped img data
            with torch.no_grad():
                for cfg_cell in f_model_input_cfg:
                    idx, data_key, model_key  = cfg_cell
                    img_data                  = mid_datas[model_key].cuda().float()
                    f_feature                 = foundation_model[model_key](img_data)
                    decoder_input[model_key]  = f_feature.half()

            image_rgb_left, image_rgb_right = cut_half_image(mid_datas['slips'][0])
            
            grey_left, binary_left  = extract_black_text(image_rgb_left)
            grey_right, binary_right = extract_black_text(image_rgb_right)

            horizontal_strokes_left, angle_vis_left = extract_angled_horizontal_strokes_tensor(binary_left)
            horizontal_strokes_right, angle_vis_right = extract_angled_horizontal_strokes_tensor(binary_right)
            
            C_left, contribution_map_left   = calculate_contribution_value(horizontal_strokes_left, edge_x=96, lambda_value=0.2) 
            C_right, contribution_map_right = calculate_contribution_value(horizontal_strokes_right, edge_x=0, lambda_value=0.2)
            
            contribution_map_left_reshaped  = contribution_map_left[np.newaxis, :, :]
            contribution_map_right_reshaped = contribution_map_right[np.newaxis, :, :]
            
            horizontal_strokes_left_entrophy  = horizontal_strokes_left * contribution_map_left_reshaped
            horizontal_strokes_right_entrophy = horizontal_strokes_right * contribution_map_right_reshaped
            horizontal_strokes_combined_entrophy = torch.cat([horizontal_strokes_left_entrophy, horizontal_strokes_right_entrophy], dim=0)

            horizontal_strokes_left_entrophy_ = torch.cumsum(horizontal_strokes_left_entrophy, dim=-1)
            horizontal_strokes_left_entrophy_sum = horizontal_strokes_left_entrophy_[:, :, -1]
            
            horizontal_strokes_right_entrophy_ = torch.cumsum(horizontal_strokes_right_entrophy.flip(dims=[-1]), dim=-1)  # 先翻转最后一维，再累加
            horizontal_strokes_right_entrophy_sum = horizontal_strokes_right_entrophy_[:, :, -1]  # 取最后一个累加结果，形状 (128, 1, 256)
    
            horizontal_strokes_entrophy_combine_sum = torch.cat([horizontal_strokes_left_entrophy_sum, horizontal_strokes_right_entrophy_sum], dim=0)

            img_256_entorphy = horizontal_strokes_combined_entrophy.unsqueeze(0).half()
            img_256_entorphy_sum = horizontal_strokes_entrophy_combine_sum.unsqueeze(0).half()

            self.slips_recog = {'img_256_entorphy': img_256_entorphy, 'img_256_entorphy_sum': img_256_entorphy_sum}
        
            #inference decoders
            cls_result = {}
            for func_name in self.decoder_models:
                cls_result[func_name] = self.decoder_models[func_name](self.slips_recog['img_256_entorphy'], self.slips_recog['img_256_entorphy_sum'])[1]
            
        #output coordinate adjust    
        if res_norm:
            h,w,_ = image_rgb.shape
            boxes_np[:,0] = boxes_np[:,0] / w
            boxes_np[:,1] = boxes_np[:,1] / h
            boxes_np[:,2] = boxes_np[:,2] / w
            boxes_np[:,3] = boxes_np[:,3] / h
        if res_xywh:
            boxes_np = xyxy2xywh(boxes_np)
            
        return cls_result, boxes_np
    
    def inference_yolov7(self, image_rgb):
        resized_image,resize_ratio,pad_size = letterbox(image_rgb,640,auto=False,stride=32)
        resized_image    = resized_image / 255.
        det_input_tensor = torch.from_numpy(resized_image).half().cuda().permute(2,0,1).unsqueeze(0)
        
        model_pred       = self.det_model(det_input_tensor)[0].detach()
        box_preds        = non_max_suppression(model_pred,classes=self.cfg_det['classes'])

        for box_pred in box_preds:
            det = scale_coords(det_input_tensor.shape[2:], box_pred[:,:4], image_rgb.shape).round()
        boxes_np   = box_preds[0].detach().cpu().numpy()
        return boxes_np

    def prep_box_img(self, image_rgb, boxes_np):
        box_num = boxes_np.shape[0]
        input_img_map = {}
        img_h,img_w,_ = image_rgb.shape
        
        for i in range(box_num):
            box_list = boxes_np[i,:4].tolist()
            box_list = [int(coord) for coord in box_list]
            x1,y1,x2,y2 = box_trans(box_list,img_w,img_h,[0.5,0.3],norm=False)
            box_image = image_rgb[y1:y2,x1:x2,:].copy()
        
            for model_name in self.recg_pre_process:
                model_info = self.recg_pre_process[model_name]
                resize_fn = model_info['resize_fn']
                if model_info['input_type'] == 'MAE':
                    img_tensor = torch.from_numpy(box_image).cuda()
                    img_tensor = img_tensor.permute(2, 0, 1) / 255.
                    img_tensor = resize_fn(img_tensor.half()).unsqueeze(0)
                
                if model_name not in input_img_map:
                    input_img_map[model_name] = []
                input_img_map[model_name].append(img_tensor)
                
        output_map = {}
        for model_name in input_img_map:
            output_map[model_name] = torch.cat(input_img_map[model_name],axis=0)
            
        return output_map
        
if __name__ == '__main__':
    

    pipe = PipelineInference(
        det_cfg  = '../det.yaml',
        base_cfg = '../base.yaml',
        decoder_cfg={'first_recog': ['../train_cfg.yaml', 
                                    '../saved_model/best.pt']})
    
    test_image = '../test.jpg'

    image_rgb = cv2.imread(test_image)[:,:,::-1]
    h,w,_ = image_rgb.shape
    print(image_rgb.shape)
    
    prob_map, box_np = pipe.inference_path(test_image)
    print(prob_map)