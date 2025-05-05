# This file contains some useful functions for the project.
import numpy as np
import torch
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import seaborn as sns
import random
import math

from scipy import optimize

def inference(f_model, c_model, vector_1, vector_2):
    '''Description: This function is used to calculate the distance between two vectors'''
    f_model.eval()
    c_model.eval()
    feature_1 = f_model(vector_1)
    feature_2 = f_model(vector_2)
    dis = c_model(torch.stack((feature_1, feature_2), 1))
    return dis

def get_heat_map(f_model, c_model, str, length, isshow = False):
    '''Description: This function is used to calculate the heat map of the model'''
    # calculate the heat map
    f_model.eval()
    c_model.eval()

    real_vectors = np.load(str)
    real_vectors = real_vectors[:, 2:4, :].astype(np.float32)

    dis_map = []
    for i in range(length):
        dis_list = []
        for j in range(length):
            v1 = real_vectors[i, 0, :][np.newaxis, np.newaxis, :]
            v2 = real_vectors[j, 1, :][np.newaxis, np.newaxis, :]
            v1[0][0] = [x-v1.min() for x in v1[0][0]]
            v2[0][0] = [x-v2.min() for x in v2[0][0]]
            v1 /= v1.max()+1e-6
            v2 /= v2.max()+1e-6
            v1 = torch.tensor(v1, dtype=torch.float32)
            v2 = torch.tensor(v2, dtype=torch.float32)
            dis = inference(f_model, c_model, v1, v2)
            dis_list.append(dis.item())

        dis_map.append(dis_list)

    return dis_map
    
def get_top_k_accuracy(k, f_model, c_model, str, direction):
    '''Description: This function is used to calculate the top k accuracy of the model'''
    # calculate the top k accuracy
    top_k = 0
    dis_map = get_heat_map(f_model, c_model, str, 118, False)
    length = len(dis_map)
    gather_list_transverse = []
    for i in range(length):
        dis_list = []
        if direction == "longitudinal":
           dis_list = [x[i] for x in dis_map]
        else: 
            dis_list = dis_map[i].copy()
        dis_list.sort()
        top_index = dis_list.index(dis_map[i][i])
        gather_list_transverse.append(top_index+1)

    for j in gather_list_transverse:
        if j <= k:
            top_k += 1
    
    return top_k

def show_fiber_curve(bottom_fiber, top_fiber):
    '''Description: This function is used to show the fiber curve'''

    # Draw line plot
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=np.arange(0, 64),
            y=top_fiber,
            mode="lines",
            name="Patch",
            line=dict(color="red", width=2),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=np.arange(0, 64),
            y=bottom_fiber,
            mode="lines",
            name="Patch",
            line=dict(color="blue", width=2),
        )
    )
    fig.show()
