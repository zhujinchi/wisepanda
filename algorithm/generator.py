# 断裂曲线生成相关
import matplotlib.pyplot as plt
import numpy as np
import random
import torch
import math

from scipy import optimize

class FractureCurveGenerator:
    def __init__(self, count_fiber, K_Ⅲ, len_x, ce_rate, erosion_epoch):
        self.count_fiber = count_fiber
        self.K_Ⅲ = K_Ⅲ
        self.len_x = len_x
        self.ce_rate = ce_rate
        self.erosion_epoch = erosion_epoch

    def p(self, theta_i, x):
        '''Description: This function is used to calculate the probability density function'''
        return self.K_Ⅲ*math.cos(x/2)/math.sqrt(2*math.pi*(self.len_x/math.cos(theta_i+x)))

    def angle_from_pdf(self, theta_i):
        '''Description: This function is used to generate the angle from the probability density function'''
        while True:
            # Generate a random sample from uniform distribution
            x = np.random.uniform(math.pi/2-theta_i, -math.pi/2-theta_i)
            # Generate a random y from uniform distribution (0, 1)
            maximum = optimize.fminbound(lambda x:-self.p(theta_i, x), -math.pi/2-theta_i, math.pi/2-theta_i) # 获取函数最大值，用于生成概率密度函数的上界
            y = np.random.uniform(0, maximum)
            # Check if y <= p(x) (our PDF: y = p(x))
            if y <= self.p(theta_i, x):
                return x + theta_i # x+theta_i = theta_i+1

    def creat_fiber_line(self): 
        '''Description: This function is used to generate the fracture curve'''
        theta_0 = random.uniform(-math.pi/2, math.pi/2)
        theta_list = [theta_0]
        for i in range(self.count_fiber):
            theta_current = self.angle_from_pdf(theta_list[-1])
            theta_list.append(theta_current)

        y_diff_list = [math.tan(theta)*(1/self.len_x) for theta in theta_list]
        y_list = [sum(y_diff_list[:i]) for i in range(self.count_fiber)]

        min_y = min(y_list)
        for i in range(self.count_fiber):
            y_list[i] += -min_y
            
        return y_list

    def relu(self, x):
        '''Description: This function is used to calculate the ReLU function'''
        return np.maximum(0, x)

    def erosion_new(self, list):
        '''Description: This function is used to generate the erosion curve'''
        new_list = []
        for i in range(len(list)):
            if i == 0:
                left_fiber = list[i]
                if len(list) == 1:
                    right_fiber = list[i]
                else:
                    right_fiber = list[i+1]
            elif i == len(list)-1:
                left_fiber = list[i-1]
                right_fiber = list[i]
            else:
                left_fiber = list[i-1]
                right_fiber = list[i+1]
            
            # 对每一个竹简计算腐蚀
            structural_area = self.relu(list[i]-left_fiber)+self.relu(list[i]-right_fiber) # 计算结构面积
            erosion_fiber = list[i]-structural_area*self.ce_rate
            new_list.append(erosion_fiber)

        return new_list

    def erosion_with_epoch(self, list, epoch): 
        '''Description: This function is used to generate the erosion curve'''
        for i in range(epoch):
            list = self.erosion_new(list)
        return list

    def floor_list(self, list, floor):
        '''Description: This function is used to adjust the list to the floor'''
        min_value = min(list) + floor
        adjusted_list = [x - min_value for x in list]
        return adjusted_list

    def revers_list(self, list, floor): 
        '''Description: This function is used to reverse the list'''
        inverted_list = [-x for x in list]
        return self.floor_list(inverted_list, floor)

    def get_top_erosion_fiber(self, list, epoch, floor): 
        '''Description: This function is used to get the top erosion fiber'''
        reversed_list = self.revers_list(list, 0)
        erosioned_list = self.erosion_with_epoch(reversed_list, epoch)
        adjusted_list = self.revers_list(erosioned_list, -floor)
        return adjusted_list

    def fibers_resize(self, list, num):
        '''Description: This function is used to resize the fibers'''
        # 创建一个长度为64的新索引
        new_indices = np.linspace(0, len(list) - 1, num=num)
        # 使用线性插值
        resampled_list = np.interp(new_indices, np.arange(len(list)), list)
        resampled_list = [64*x/self.count_fiber for x in resampled_list]
        resampled_list = [round(x, 4) for x in resampled_list]
        return resampled_list

    def get_pair_fibers(self):
        '''Description: This function is used to generate the pair of fibers'''
        fracture_list = self.creat_fiber_line() 
        erosion_list = self.erosion_with_epoch(fracture_list, self.erosion_epoch)
        erosion_list = self.floor_list(erosion_list, 0)
        top_erosion_list = self.get_top_erosion_fiber(fracture_list, self.erosion_epoch, 0)
        return self.fibers_resize(erosion_list, 64), self.fibers_resize(top_erosion_list, 64)


    def get_fracture_curves(self, data_amount):
        '''Description: This function is used to generate the fracture curve'''
        data_list = []
        array_zero = np.zeros(64)
        for i in range(data_amount):
            a, b = self.get_pair_fibers()
            vector_edge_top = np.array(a)
            vector_edge_bottom = np.array(b)
            list_top_bottom = [array_zero, array_zero, vector_edge_top, vector_edge_bottom]
            data_list.append(list_top_bottom)

        for i in range(int(data_amount/2)):
            a, b = self.get_pair_fibers()
            c, d = self.get_pair_fibers()
            vector_edge_top = np.array(a)
            vector_edge_bottom = np.array(d)
            list_top_bottom = [array_zero, array_zero, vector_edge_top, vector_edge_bottom]
            data_list.append(list_top_bottom)
            vector_edge_top = np.array(c)
            vector_edge_bottom = np.array(b)
            list_top_bottom = [array_zero, array_zero, vector_edge_top, vector_edge_bottom]
            data_list.append(list_top_bottom)

        all_data_list = np.array(data_list)
        np.save('slips/train_data', all_data_list)
        # torch.save(data_list, 'slips/valid_data.pt')
        return all_data_list


# main function
if __name__ == "__main__":
    generator = FractureCurveGenerator(80, 1, 10, 0.01, 1000)
    vectors = generator.get_fracture_curves(1000)
