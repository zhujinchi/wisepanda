# Train the model and test the model
import os
import random
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import torch
import torch.backends.cudnn as cudnn
import torch.nn as nn
from torch.optim.lr_scheduler import OneCycleLR
from torch.utils.data import DataLoader, Dataset
import matplotlib.pyplot as plt
import seaborn as sns

from model import CompareNet, VectorNet
from dataset import VectorDataset
from utils import get_heat_map, get_top_k_accuracy, inference
from generator import FractureCurveGenerator
import heapq
from sklearn.manifold import TSNE
from matplotlib.colors import LinearSegmentedColormap


from matplotlib.gridspec import GridSpec

pio.renderers.default = "browser"

# set environment
def set_env(deterministic, seed, allow_tf32_on_cudnn, allow_tf32_on_matmul):
    '''Description: This function is used to set the environment for the model'''
    # set deterministic
    if deterministic:
        cudnn.benchmark = False
        # https://docs.nvidia.com/cuda/cublas/index.html#cublasApi_reproducibility
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
        torch.use_deterministic_algorithms(True, warn_only=True)
        # cv2.ocl.setUseOpenCL(False)
        # cv2.setNumThreads(1)
    else:
        cudnn.benchmark = True
        torch.use_deterministic_algorithms(False)

    # set seed
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    # cv2.setRNGSeed(seed)

    # The flag below controls whether to allow TF32 on matmul. This flag defaults to False
    # in PyTorch 1.12 and later.
    torch.backends.cuda.matmul.allow_tf32 = allow_tf32_on_matmul
    # The flag below controls whether to allow TF32 on cuDNN. This flag defaults to True.
    torch.backends.cudnn.allow_tf32 = allow_tf32_on_cudnn

# loss function
def loss_fn(dis_pos, dis_neg):
    '''Description: This function is used to calculate the loss function'''
    loss = torch.mean((dis_pos - 0) ** 2) + torch.mean((dis_neg - 1) ** 2)
    return loss

# train function    
def train(f_model, c_model, dataloader, max_epoch=10, lr=3e-3):
    '''Description: This function is used to train the model'''
    f_model.train()
    c_model.train()
    params = list(f_model.parameters()) + list(c_model.parameters())

    optimizer = torch.optim.Adam(params, lr=lr)

    scheduler_onecycle = OneCycleLR(
        optimizer,
        max_lr=lr,
        steps_per_epoch=len(dataloader),
        epochs=max_epoch,
        pct_start=0.1,
    )

    for epoch in range(max_epoch):
        for batch_idx, (vector, pos_vector, neg_vector) in enumerate(dataloader):
            vector = vector
            pos_vector = pos_vector
            neg_vector = neg_vector

            optimizer.zero_grad()

            feature = f_model(vector)
            feature_pos = f_model(pos_vector)
            feature_neg = f_model(neg_vector)

            dis_pos = c_model(torch.stack((feature, feature_pos), 1))
            dis_neg = c_model(torch.stack((feature, feature_neg), 1))

            loss = loss_fn(dis_pos, dis_neg)
            loss.backward()
            optimizer.step()
            scheduler_onecycle.step()

            if batch_idx % 100 == 0:
                print(
                    "Train Epoch: {} [{}/{} ({:.0f}%)]\tLoss: {:.6f}".format(
                        epoch,
                        batch_idx * len(vector),
                        len(dataloader.dataset),
                        100.0 * batch_idx / len(dataloader),
                        loss.item(),
                    )
                )
         # Save the models
    torch.save(f_model.state_dict(), 'models/f_model.pth')
    torch.save(c_model.state_dict(), 'models/c_model.pth')

def get_tsne_plots(fake_vectors, real_vectors, dis_map):
    """
    Generate t-SNE visualization and matching quality heatmap, 
    save them separately, and export data as Excel
    """
    
    # Create output directory
    os.makedirs('outputs', exist_ok=True)
    
    # Data preprocessing function
    def extract_vectors(vectors, sample_size, indices=(2,3)):
        top = vectors[:, indices[0]:indices[0]+1, :].astype(np.float32)
        bottom = vectors[:, indices[1]:indices[1]+1, :].astype(np.float32)
        return [vec[0] for vec in top[:sample_size]], [vec[0] for vec in bottom[:sample_size]]
    
    # Extract fake and real data
    fake_top, fake_bottom = extract_vectors(fake_vectors, 1000)
    real_top, real_bottom = extract_vectors(real_vectors, 118)
    
    # Combine bottom data for t-SNE
    combined_bottom = np.vstack((fake_bottom, real_bottom))
    
    # t-SNE transformation
    tsne = TSNE(n_components=2, random_state=42)
    data_transformed = tsne.fit_transform(combined_bottom)
    
    # Set standard plotting style
    plt.style.use('seaborn-whitegrid')
    plt.rcParams.update({
        'font.family': 'Arial',
        'font.size': 10,
        'axes.linewidth': 1.0,
        'axes.grid': False,
        'axes.facecolor': 'white',
        'figure.facecolor': 'white',
        'figure.dpi': 300
    })
    
    # Separate data
    synthetic_data = data_transformed[:1000]
    real_data = data_transformed[1000:]
    
    # Save t-SNE data to Excel
    tsne_df = pd.DataFrame({
        'Type': ['Synthetic']*len(synthetic_data) + ['Real']*len(real_data),
        'Dimension_1': np.concatenate([synthetic_data[:, 0], real_data[:, 0]]),
        'Dimension_2': np.concatenate([synthetic_data[:, 1], real_data[:, 1]])
    })
    tsne_df.to_excel('outputs/tsne_data.xlsx', index=False)
    
    # Save heatmap data to Excel
    dis_map_df = pd.DataFrame(dis_map)
    dis_map_df.to_excel('outputs/heatmap_data.xlsx', index=False)
    
    # ============ Save t-SNE plot ============
    plt.figure(figsize=(5, 5))

    # Blue-green color scheme used in the reference
    plt.scatter(
        synthetic_data[:, 0],
        synthetic_data[:, 1],
        c='#1f77b4',  # Blue
        s=20,
        alpha=0.6,
        edgecolors='none',
        label='Synthetic data'
    )

    plt.scatter(
        real_data[:, 0],
        real_data[:, 1],
        c='#2ca02c',  # Green
        s=20,
        alpha=0.6,
        edgecolors='none',
        label='Real data'
    )

    # Complete border
    for spine in plt.gca().spines.values():
        spine.set_visible(True)
        spine.set_linewidth(0.8)

    # Add legend with border
    legend = plt.legend(loc='upper right', markerscale=1, frameon=True)
    legend.get_frame().set_edgecolor('#E3E3E3')  # Add gray border
    legend.get_frame().set_linewidth(0.8)      # Set border width

    # Remove axis labels and title
    plt.xlabel('')
    plt.ylabel('')
    plt.title('')

    # Set ticks but hide labels
    plt.xticks([-60, -30, 0, 30, 60], [])
    plt.yticks([-60, -30, 0, 30, 60], [])

    plt.tight_layout()
    plt.savefig('outputs/tsne_plot.pdf', bbox_inches='tight')
    plt.savefig('outputs/tsne_plot.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # ============ Save heatmap ============
    plt.figure(figsize=(5, 5))

    # Modify color scheme, use gradient from deep blue to white
    cmap = LinearSegmentedColormap.from_list('match_quality', 
                                            ['#053061', '#2166AC', '#4393C3', '#92C5DE', '#F7F7F7'], 
                                            N=100)

    # Draw heatmap
    ax = sns.heatmap(
        dis_map,
        cmap=cmap,
        square=True,
        vmin=0.0,  # Ensure minimum value starts from 0
        vmax=1.0,  # Ensure maximum value ends at 1
        cbar_kws={
            'shrink': 0.8,
            'aspect': 15,
            'label': ''
        },
        xticklabels=False, 
        yticklabels=False
    )

    # Keep clean layout
    plt.tight_layout()
    plt.savefig('outputs/heatmap_plot.pdf', bbox_inches='tight')
    plt.savefig('outputs/heatmap_plot.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("Charts and data have been saved to the 'outputs' directory")

# main function
if __name__ == "__main__":
    set_env(deterministic=True, seed=0, allow_tf32_on_cudnn=True, allow_tf32_on_matmul=True)
    
    
    # Physics engine generates data
    # generator = FractureCurveGenerator(187, 1, 3, 0.001, 1000)
    # vectors = generator.get_fracture_curves(6000)
    
    # Import data (generated by physics engine)
    vectors = np.load("dataset/vector_reallike_6000.npy")

    total_size = len(vectors)
    vectors_train = vectors[0:int(total_size/2), 2:4, :].astype(np.float32)
    vectors_test = vectors[int(total_size/2):total_size, 2:4, :].astype(np.float32)

    dataset_train = VectorDataset(vectors_train)
    dataloader = DataLoader(dataset_train, batch_size=100, shuffle=True)

    f_model = VectorNet()
    c_model = CompareNet()
    train(f_model, c_model, dataloader, max_epoch=150, lr=1e-3)

    real_vectors = np.load("dataset/vector_real_118_patch.npy")
    # real_vectors = np.load("/Users/angzeng/Desktop/data_new/vector_real_335_patch.npy")
    real_vectors = real_vectors[:, 2:4, :].astype(np.float32)

    length = len(real_vectors)
    dis_map = get_heat_map(f_model, c_model, "dataset/vector_real_118_patch.npy", length, True)
    np.save('heatmap/dis_map3.npy', dis_map)


    #dis_map = np.load('heatmap/dis_map.npy')

    fake_vectors = vectors
    real_vectors = np.load("dataset/vector_real_118_patch.npy")
    #calculate the similarity of two data distributions via t-SNE
    # get_tsne_plots(fake_vectors, real_vectors ,dis_map) 

    #calculate the top k accuracy
    data_real_todo = "dataset/vector_real_118_patch.npy"
    k1 = get_top_k_accuracy(1, f_model, c_model, data_real_todo, "longitudinal")
    k5 = get_top_k_accuracy(5, f_model, c_model, data_real_todo, "longitudinal")
    k10 = get_top_k_accuracy(10, f_model, c_model, data_real_todo, "longitudinal")
    k20 = get_top_k_accuracy(20, f_model, c_model, data_real_todo, "longitudinal")
    k50 = get_top_k_accuracy(50, f_model, c_model, data_real_todo, "longitudinal")

    k_list = [1, 5, 10, 20, 50, 100]
    result_list = []
    for i in k_list:
        k = get_top_k_accuracy(i, f_model, c_model, data_real_todo, "longitudinal")
        k_ = get_top_k_accuracy(i, f_model, c_model, data_real_todo, "transverse")
        result_list.append(round((k+k_)/236, 4))
