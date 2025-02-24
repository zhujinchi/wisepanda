import torch.nn as nn


class VectorNet(nn.Module):

    def __init__(self):
        super(VectorNet, self).__init__()
        self.conv1 = nn.Conv1d(in_channels=4, out_channels=10, kernel_size=12, padding="same")
        self.relu1 = nn.ReLU()
        self.conv2 = nn.Conv1d(in_channels=10, out_channels=1, kernel_size=3, padding="same")
        self.relu2 = nn.ReLU()
        self.fc1 = nn.Linear(64, 10)
        self.relu3 = nn.ReLU()
        self.fc2 = nn.Linear(10, 1)

    def forward(self, x):
        # torch.Size([10, 4, 64])
        x = self.conv1(x)
        x = self.relu1(x)
        # torch.Size([10, 10, 64])
        x = self.conv2(x)
        x = self.relu2(x)
        # torch.Size([10, 1, 64])
        x = x.view(-1, 64)
        # torch.Size([10, 64])
        x = self.fc1(x)
        x = self.relu3(x)
        # torch.Size([10, 10])
        x = self.fc2(x)
        # torch.Size([10, 1])
        return x