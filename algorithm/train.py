import os
import random
from pathlib import Path
import numpy as np
import torch
import torch.backends.cudnn as cudnn
import torch.nn as nn
from torch.optim.lr_scheduler import OneCycleLR
from torch.utils.data import DataLoader, Dataset
import torch.nn.functional as F

from model import CompareNet, VectorNet
from dataset import VectorDataset
from utils import get_top_k_accuracy, get_tsne_plots, load_training_data
from generator import FractureCurveGenerator


# set environment
def set_env(deterministic, seed, allow_tf32_on_cudnn, allow_tf32_on_matmul):
    """
    Description: This function is used to set the environment for training
    deterministic: whether to set deterministic
    seed: random seed
    allow_tf32_on_cudnn: whether to allow tf32 on cudnn
    allow_tf32_on_matmul: whether to allow tf32 on matmul
    """
    # set deterministic
    if deterministic:
        cudnn.benchmark = False
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
        torch.use_deterministic_algorithms(True, warn_only=True)
    else:
        cudnn.benchmark = True
        torch.use_deterministic_algorithms(False)

    # set seed
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    # The flag below controls whether to allow TF32 on matmul. This flag defaults to False
    # in PyTorch 1.12 and later.
    torch.backends.cuda.matmul.allow_tf32 = allow_tf32_on_matmul
    # The flag below controls whether to allow TF32 on cuDNN. This flag defaults to True.
    torch.backends.cudnn.allow_tf32 = allow_tf32_on_cudnn


# loss function
def loss_fn(dis_pos, dis_neg):
    """
    Description: This function is used to calculate the loss
    dis_pos: distance of positive pair
    dis_neg: distance of negative pair
    """
    loss = torch.mean((dis_pos - 0) ** 2) + torch.mean((dis_neg - 1) ** 2)
    return loss


# train function
def train(
    f_model,
    c_model,
    dataloader,
    max_epoch=100,
    lr=3e-3,
    f_model_path="models/f_model.pth",
    c_model_path="models/c_model.pth",
):
    """
    Description: This function is used to train the model
    f_model: feature extraction model
    c_model: comparison model
    dataloader: dataloader for training
    max_epoch: maximum number of epochs
    lr: learning rate
    f_model_path: path to save the feature extraction model
    c_model_path: path to save the comparison model
    """
    f_model.train()
    c_model.train()
    params = list(f_model.parameters()) + list(c_model.parameters())

    # create optimizer and scheduler
    optimizer = torch.optim.Adam(params, lr=lr)
    scheduler_onecycle = OneCycleLR(
        optimizer,
        max_lr=lr,
        steps_per_epoch=len(dataloader),
        epochs=max_epoch,
        pct_start=0.1,
    )

    # training loop
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
    torch.save(f_model.state_dict(), f_model_path)
    torch.save(c_model.state_dict(), c_model_path)


# main function
if __name__ == "__main__":
    # set environment
    set_env(deterministic=True, seed=0, allow_tf32_on_cudnn=True, allow_tf32_on_matmul=True)
    # real world data (Bamboo236)
    real_world_data = "dataset/vector_real_118_patch.npy"
    generated_data = "dataset/vector_reallike_6000.npy"

    # load training data
    vectors = load_training_data(generated_data, new_data=False)

    # extract the 3rd and 4th channels for training and testing
    total_size = len(vectors)
    vectors_train = vectors[0 : int(total_size / 2), 2:4, :].astype(np.float32)

    # create dataloader
    dataset_train = VectorDataset(vectors_train)
    dataloader = DataLoader(dataset_train, batch_size=100, shuffle=True)

    # load models
    f_model = VectorNet()
    c_model = CompareNet()

    # train models
    train(
        f_model,
        c_model,
        dataloader,
        max_epoch=150,
        lr=1e-3,
        f_model_path="models/f_model.pth",
        c_model_path="models/c_model.pth",
    )

    # Calculate Top-k accuracy on real-world datasets
    # Note: Complete validation results and baseline comparisons are available in method_comparison.ipynb
    k_list = [1, 5, 10, 20, 50, 100]
    result_list = []
    for i in k_list:
        k = get_top_k_accuracy(i, f_model, c_model, real_world_data, "longitudinal")
        k_ = get_top_k_accuracy(i, f_model, c_model, real_world_data, "transverse")
        result_list.append(round((k + k_) / 236, 4))
    print(result_list)
