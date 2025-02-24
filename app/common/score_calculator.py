import os
import numpy as np
import cv2
import torch

from .notch_extractor import NotchExtractor


class ScoreCalculator:  # 用于根据图像的特征计算评分，通常用于图像匹配和评估图像相似性

    @staticmethod
    def get_score(direction, src_image, dir_list):  # 使用图像的边缘特征和纹理特征进行评分，并返回匹配度最高的图像路径及其评分
        zero_array = np.zeros(64)
        vector_texture_top = zero_array
        vector_texture_bottom = zero_array
        app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        vector_model = torch.load(os.path.join(app_path, 'model/model_of_best'))
        if direction == 'bottom':
            #源图片是上半截区的
            vector_edge_top = np.array(ScoreCalculator._get_edge(src_image, 'top'))
            scores_bottom_edge = []
            for dir_aim in dir_list:
                extractor = NotchExtractor(dir_aim)
                notch_bottom = extractor.extract_bottom()
                vector_edge_bottom = np.array(ScoreCalculator._get_edge(notch_bottom, 'bottom'))
                
                data_list = [vector_texture_top, vector_texture_bottom, vector_edge_top, vector_edge_bottom]
                input_data = np.array(data_list)
                pred_data = input_data.astype(np.float32)
                vector_model.eval()
                y_pred = vector_model(torch.tensor(pred_data))
                scores_bottom_edge.append((round(y_pred.item(), 4), dir_aim))

            scores_bottom_edge.sort(key=lambda x: x[0], reverse=True)

            if len(scores_bottom_edge) > 50:
                return scores_bottom_edge[:50]
            else:
                return scores_bottom_edge

        else:
            # 源片是上半截区的
            vector_edge_bottom = np.array(ScoreCalculator._get_edge(src_image, 'bottom'))
            scores_top_edge = []
            for dir_aim in dir_list:
                extractor = NotchExtractor(dir_aim)
                notch_top = extractor.extract_top()
                vector_edge_top = np.array(ScoreCalculator._get_edge(notch_top, 'top'))

                data_list = [vector_texture_top, vector_texture_bottom, vector_edge_top, vector_edge_bottom]
                input_data = np.array(data_list)
                pred_data = input_data.astype(np.float32)
                vector_model.eval()
                y_pred = vector_model(torch.tensor(pred_data))
                scores_top_edge.append([round(y_pred.item(), 4), dir_aim])

            scores_top_edge.sort(key=lambda x: x[0], reverse=True)

            return scores_top_edge[:50]

    @staticmethod
    def _get_edge(src_image, direction):  # 提取图像的边缘特征
        gray_image = cv2.cvtColor(src_image, cv2.COLOR_BGR2GRAY)
        # print(gray_image.shape)
        crop_size = (64,int((gray_image.shape[0]*64)/gray_image.shape[1]))
        new_image = cv2.resize(gray_image, crop_size, interpolation = cv2.INTER_AREA)
        # print(new_image.shape)

        height = new_image.shape[0] # 3
        width = new_image.shape[1] # 64
        symbol_vector = []
        symbol_sum = 0

        for c in range(width):
            for r in range(height):
                if direction == 'bottom':
                    if new_image[r][c] < 250:
                        symbol_sum += 1
                else:
                    if new_image[r][c] >= 250:
                        symbol_sum += 1
            symbol_vector.append(symbol_sum)
            symbol_sum = 0
            symbol_vector = [item - min(symbol_vector) for item in symbol_vector]
            # print(symbol_vector)
        return symbol_vector