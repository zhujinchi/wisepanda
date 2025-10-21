import os
import argparse
import numpy as np
import yaml
from tqdm import tqdm
from inference.inference_stage_1 import PipelineInference
from inference.inference_stage_3 import PipelineInference_v21
from utils.preprocess import stitch_bamboo_slips, extract_black_text_stitched, find_text_regions_and_boundaries, extract_single_words_region, calculate_top_k_accuracy

parser = argparse.ArgumentParser()
parser.add_argument('--stage_one_path',type=str,default='./config/Stage-1.yaml')
parser.add_argument('--stage_three_path',type=str,default='./config/Stage-3.yaml')
parser.add_argument('--val_path',type=str,default='./test/Val_datasets')
parser.add_argument('--output_path',type=str,default='./result')
cfg = parser.parse_args()

def collect_left_right_image_paths(root_directory):
    left_image_paths = []
    right_image_paths = []
    image_extensions = ['.tif', '.jpg', '.png']
    
    for dirpath, dirnames, filenames in os.walk(root_directory):
        for filename in filenames:
            if any(filename.endswith(ext) for ext in image_extensions):
                full_path = os.path.join(dirpath, filename)
                if '_left.' in filename:
                    left_image_paths.append(full_path)
                elif '_right.' in filename:
                    right_image_paths.append(full_path)
    left_image_paths.sort()
    right_image_paths.sort()
    
    return left_image_paths, right_image_paths

def main():
    with open(cfg.stage_one_path,'r') as f:
        opt_stage_1 = yaml.load(f.read(), Loader=yaml.FullLoader)
    
    with open(cfg.stage_three_path,'r') as f:
        opt_stage_2 = yaml.load(f.read(), Loader=yaml.FullLoader)
    
    base_cfg_1    = opt_stage_1['base_cfg']
    det_cfg_1     = opt_stage_1['det_cfg']
    decoder_cfg_1 = opt_stage_1['decoder_cfg']
    
    save_folder_path = decoder_cfg_1['first_recog'][0].split('/')[-2]
    save_full_path = os.path.join(cfg.output_path, save_folder_path)
    
    base_cfg_2    = opt_stage_2['base_cfg']
    det_cfg_2     = opt_stage_2['det_cfg']
    decoder_cfg_2 = opt_stage_2['decoder_cfg']
    
    pipe = PipelineInference(det_cfg = det_cfg_1, base_cfg = base_cfg_1, decoder_cfg=decoder_cfg_1)
    pipe_2_batch = PipelineInference_v21(det_cfg = det_cfg_2, base_cfg = base_cfg_2, decoder_cfg = decoder_cfg_2)
    
    root_dir = cfg.val_path
    left_image_list, right_image_list = collect_left_right_image_paths(root_dir)
    print(f"Found {len(left_image_list)} left images and {len(right_image_list)} right images")
    
    heatmap = []
    words_list_all = []
    
    for l in tqdm(range(len(left_image_list)), desc="Processing left images", unit="image"):
        row = []
        words_list_row = []
        for r in tqdm(range(len(right_image_list)), desc=f"Processing right images for left image {l}", unit="image", leave=False):
            stitched_image = stitch_bamboo_slips(left_image_list[l], right_image_list[r], threshold=50)
            prob_map, box_np = pipe.forward(stitched_image)
            stage_1_pair_flag = prob_map['first_recog'][0][0] > 0.4   
            if stage_1_pair_flag:
                original, binary_text = extract_black_text_stitched(stitched_image, threshold=50)
                text_regions, gap_regions, projection = find_text_regions_and_boundaries(
                    binary_text, 
                    min_text_height=20,    
                    min_gap_height=8,  
                    peak_proximity_threshold=0.3  
                )
            
                words_list = extract_single_words_region(original, binary_text, text_regions)
                if words_list is not None and len(words_list) > 0:
                    words_list_row.append(words_list)
                else:
                    words_list_row.append([])
            else:
                words_list_row.append([])
        words_list_all.append(words_list_row)
    
    heatmap = pipe_2_batch.forward(words_list_all)
    np.save(save_full_path, heatmap)
    
    # Topk result
    heatmap_np = np.array(heatmap)
    accuracies = calculate_top_k_accuracy(heatmap_np, k_values=[1, 5, 10, 15, 20, 50]) 
    for k, acc in accuracies.items():
        print("Top-{:d} Accuracy: {:.4f}%".format(k, acc * 100))
    
    print('Done')

if __name__ == "__main__":
    main()