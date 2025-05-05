# Custom dataset for training the Network
import numpy as np
from torch.utils.data import Dataset

# Custom dataset for training the Network
class VectorDataset(Dataset):
    '''Description: This class is used to define the VectorDataset'''
    def __init__(self, vectors):
        super().__init__()
        # assume vectors is n x 2 x 64
        self.vectors = vectors

    def __getitem__(self, index):
        vector = self.vectors[index, 0, :]
        pos_vector = self.vectors[index, 1, :]

        # generate negative index, can't be index itself
        available_indices = np.arange(self.vectors.shape[0])
        available_indices = np.delete(available_indices, index)
        neg_index = np.random.choice(available_indices)

        neg_vector = self.vectors[neg_index, 1, :]

        # add channel 1 for conv1d
        vector = vector[np.newaxis, :]
        pos_vector = pos_vector[np.newaxis, :]
        neg_vector = neg_vector[np.newaxis, :]

        vector /= vector.max()
        pos_vector /= pos_vector.max()
        neg_vector /= neg_vector.max()
        return vector, pos_vector, neg_vector

    def __len__(self):
        return self.vectors.shape[0]