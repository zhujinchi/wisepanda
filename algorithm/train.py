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
import math
import torch.nn.functional as F

from model import CompareNet, VectorNet, PositionalEncoding, TransformerVectorNet, VectorNet2
from dataset import VectorDataset
from utils import get_heat_map, get_top_k_accuracy, inference
from generator import FractureCurveGenerator
import heapq
from sklearn.manifold import TSNE
from matplotlib.colors import LinearSegmentedColormap
from sklearn.model_selection import KFold

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

def contrastive_loss(distances, labels, margin=1.0):
    distances = distances.squeeze()

    similar_loss = labels * torch.pow(distances, 2)
    dissimilar_loss = (1 - labels) * torch.pow(torch.clamp(margin - distances, min=0.0), 2)
    
    loss = torch.mean(similar_loss + dissimilar_loss)
    return loss

def bce_loss(predictions, labels):

    return F.binary_cross_entropy(predictions, labels)

# train function    
def train(f_model, c_model, dataloader, max_epoch=10, lr=3e-3, f_model_path='models/f_model.pth', c_model_path='models/c_model.pth'):
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



            # dis_pos = c_model(torch.stack((feature, feature_pos), 1))
            # dis_neg = c_model(torch.stack((feature, feature_neg), 1))

            # loss = loss_fn(dis_pos, dis_neg)


            #triplet loss
            triplet_loss = nn.TripletMarginLoss(margin=1.0, p=2)
            loss = triplet_loss(feature, feature_pos, feature_neg)
            
            #contrastive loss
            # dist_pos = torch.norm(feature - feature_pos, dim=1)
            # dist_neg = torch.norm(feature - feature_neg, dim=1)

            # pos_labels = torch.ones(dist_pos.size(0), device=dist_pos.device)
            # neg_labels = torch.zeros(dist_neg.size(0), device=dist_neg.device)

            # distances = torch.cat([dist_pos, dist_neg], dim=0)
            # labels = torch.cat([pos_labels, neg_labels], dim=0)

            # loss = contrastive_loss(distances, labels)

            # BCE loss
            # dist_pos = torch.norm(feature - feature_pos, dim=1)  # Distance to positive sample
            # dist_neg = torch.norm(feature - feature_neg, dim=1)  # Distance to negative sample
            
            # prob_pos = torch.exp(-dist_pos)  # High probability for small distances (similar pairs)
            # prob_neg = torch.exp(-dist_neg)  # Low probability for large distances (dissimilar pairs)
            
            #  # Create labels for BCE loss
            # pos_labels = torch.ones_like(prob_pos)   # Label 1 for similar pairs
            # neg_labels = torch.zeros_like(prob_neg)  # Label 0 for dissimilar pairs
            
            # # Concatenate predictions and labels
            # predictions = torch.cat([prob_pos, prob_neg], dim=0)
            # labels = torch.cat([pos_labels, neg_labels], dim=0)
            
            # # Compute Binary Cross Entropy loss
            # loss = F.binary_cross_entropy(predictions, labels)


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
    torch.save(f_model.state_dict(), f_model_path)
    torch.save(c_model.state_dict(), c_model_path)

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

def train_without_cross_validation(vectors, fpath='models/f_model.pth', cpath='models/c_model.pth'):
    '''Description: This function is used to train the model without cross validation'''
    total_size = len(vectors)
    vectors_train = vectors[0:int(total_size/2), 2:4, :].astype(np.float32)


    dataset_train = VectorDataset(vectors_train)
    dataloader = DataLoader(dataset_train, batch_size=300, shuffle=True)

    f_model = VectorNet2()
    c_model = CompareNet()
    train(f_model, c_model, dataloader, max_epoch=30, lr=1e-3, f_model_path=fpath, c_model_path=cpath)

    real_vectors = np.load("dataset/vector_real_118_patch.npy")
    real_vectors = real_vectors[:, 2:4, :].astype(np.float32)

    real_vectors = np.load("dataset/vector_real_118_patch.npy")

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
    print(result_list)

def calculate_position_stats_numpy(list1, list2, list3):
    # transform to numpy array
    arrays = np.array([list1, list2, list3])
    
    # calculate mean and standard deviation
    means = np.mean(arrays, axis=0)
    stds = np.std(arrays, axis=0, ddof=1)  

    means = np.round(means, 2)
    stds = np.round(stds, 2)
    
    return means.tolist(), stds.tolist()

# main function
if __name__ == "__main__":
    #默认2
    set_env(deterministic=True, seed=0, allow_tf32_on_cudnn=True, allow_tf32_on_matmul=True)
    
    # Physics engine generates data
    # parameters (187, 1, 3, 0.02, 500)
    # generator = FractureCurveGenerator(187, 1, 3, 0.02, 500)
    # vectors = generator.get_fracture_curves(6000)
    # Save the generated data
    # np.save("dataset/vector_reallike_6000_0904.npy", vectors)

    
    # Import data (generated by physics engine)
    vectors = np.load("dataset/vector_reallike_6000.npy") #150
    #vectors = np.load("dataset/vector_reallike_6000_0826.npy") #153
    #vectors = np.load("dataset/vector_reallike_6000_0904.npy") #150
    #train_without_cross_validation(vectors, fpath='models/extend-data/f_model_wisepanda(tripletnet_loss)3.pth', cpath='models/extend-data/c_model_wisepanda(tripletnet_loss)3.pth')
    

    # GAN
    #vectors = np.load('extend_compare/GANs/GAN/generated_vectors_GAN_0.01_6000.npy') #150
    #vectors = np.load('extend_compare/GANs/GAN/generated_vectors_GAN_0.02_6000.npy') #80
    #vectors = np.load('extend_compare/GANs/GAN/generated_vectors_GAN_perturbed_0.02_6000.npy') #200
    # seriesGan 
    #vectors = np.load('extend_compare/GANs/SeriesGAN/generated_vectors_seriesgan_0.01_6000.npy') #150
    #vectors = np.load('extend_compare/GANs/SeriesGAN/generated_vectors_seriesgan_0.02_6000.npy') #150
    #vectors = np.load('extend_compare/GANs/SeriesGAN/generated_vectors_seriesgan_perturbed_0.02_6000.npy') #150
    # diffusion
    #vectors = np.load('extend_compare/Diffusion/Diffusion_1d/generated_vectors_diffusion_0.01_6000.npy') #100
    #vectors = np.load('extend_compare/Diffusion/Diffusion_1d/generated_vectors_diffusion_0.02_6000.npy') #100
    #vectors = np.load('extend_compare/Diffusion/Diffusion_1d/generated_vectors_diffusion_perturbed_0.02_6000.npy') #100
    # diffusion-TS
    #vectors = np.load('extend_compare/Diffusion/Diffusion-TS/generated_vectors_diffusion-TS_0.01_6000.npy') #150
    #vectors = np.load('extend_compare/Diffusion/Diffusion-TS/generated_vectors_diffusion-TS_0.02_6000.npy') #150
    #vectors = np.load('extend_compare/Diffusion/Diffusion-TS/generated_vectors_diffusion-TS_perturbed_0.02_6000.npy') #150

    # extract the 3rd and 4th channels for training and testing
    selected_vectors = vectors[:int(vectors.shape[0]/2), 2:4, :].astype(np.float32)
    #selected_vectors = vectors[:, 2:4, :].astype(np.float32)

    # create 3-fold cross-validation
    kf = KFold(n_splits=3, shuffle=False)
    train_test_splits = []

    for i, (train_idx, test_idx) in enumerate(kf.split(selected_vectors)):
        vectors_train = selected_vectors[train_idx]
        vectors_test = selected_vectors[test_idx]
        
        train_test_splits.append({
            'train': vectors_train,
            'test': vectors_test,
            'fold': i + 1
        })

    # use the each fold for training and testing
    vectors_train1, vectors_test1 = train_test_splits[0]['train'], train_test_splits[0]['test']
    vectors_train2, vectors_test2 = train_test_splits[1]['train'], train_test_splits[1]['test']
    vectors_train3, vectors_test3 = train_test_splits[2]['train'], train_test_splits[2]['test']

    # add the train and test sets to lists for iteration
    vectors_train_list = [vectors_train1, vectors_train2, vectors_train3]
    vectors_test_list = [vectors_test1, vectors_test2, vectors_test3]

    #train information
    train_info = ['extend-data', 'wisepanda(tripletnet_loss)x'] #['normal', 'wisepanda(bce_loss)'], ['normal', 'wisepanda(contrastive_loss)'], ['normal', 'wisepanda(triplet_loss)']
    result = []

    for i in range(3):
        vectors_train = vectors_train_list[i]
        vectors_test = vectors_test_list[i]

        dataset_train = VectorDataset(vectors_train)
        dataloader = DataLoader(dataset_train, batch_size=300, shuffle=True)

        f_model = VectorNet()
        #f_model = TransformerVectorNet(d_model=64, nhead=8, num_layers=3, dim_feedforward=128, output_dim=32)
        c_model = CompareNet()

        train(f_model, c_model, dataloader, max_epoch=30, lr=1e-3, f_model_path='models/'+train_info[0]+'/f_model_'+train_info[1]+str(i+1)+'.pth', c_model_path='models/'+train_info[0]+'/c_model_'+train_info[1]+str(i+1)+'.pth')

        real_vectors = np.load("dataset/vector_real_118_patch.npy")
        real_vectors = real_vectors[:, 2:4, :].astype(np.float32)

        length = len(real_vectors)
        dis_map = get_heat_map(f_model, c_model, "dataset/vector_real_118_patch.npy", length, True)
        np.save('heatmap/dis_map3.npy', dis_map)

        # dis_map = np.load('heatmap/dis_map.npy')

        fake_vectors = vectors
        real_vectors = np.load("dataset/vector_real_118_patch.npy")
        # calculate the similarity of two data distributions via t-SNE
        # get_tsne_plots(fake_vectors, real_vectors ,dis_map) 

        # calculate the top k accuracy
        data_real_todo = "dataset/vector_real_118_patch.npy"

        k_list = [1, 5, 10, 20, 50, 100]
        result_list = []
        for i in k_list:
            k = get_top_k_accuracy(i, f_model, c_model, data_real_todo, "longitudinal")
            k_ = get_top_k_accuracy(i, f_model, c_model, data_real_todo, "transverse")
            result_list.append(round((k+k_)/236, 4))
        result_list = [x * 100 for x in result_list]
        result.append(result_list)

    means, stds = calculate_position_stats_numpy(result[0], result[1], result[2])
    print(means)
    print(stds)
