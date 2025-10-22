import torch.nn as nn
import torch
import math
class VectorNet(nn.Module):
    def __init__(
        self,
    ) -> None:
        super(VectorNet, self).__init__()
        # 64 -> 55
        self.conv1 = nn.Conv1d(in_channels=1, out_channels=5, kernel_size=10, padding="valid")
        self.a1 = nn.PReLU()
        # 55 -> 51
        self.conv2 = nn.Conv1d(in_channels=5, out_channels=5, kernel_size=5, padding="valid")
        self.a2 = nn.PReLU()
        self.fc1 = nn.Linear(5 * 51, 32)
        self.a3 = nn.PReLU()

    def forward(self, x):
        x = self.conv1(x)
        x = self.a1(x)
        x = self.conv2(x)
        x = self.a2(x)
        x = x.view(x.size(0), -1)
        x = self.fc1(x)
        x = self.a3(x)
        return x
class CompareNet(nn.Module):
    def __init__(self):
        super(CompareNet, self).__init__()
        # 32 -> 23
        self.conv1 = nn.Conv1d(in_channels=2, out_channels=4, kernel_size=10, padding="valid")
        self.a1 = nn.PReLU()
        # 23 -> 19
        self.conv2 = nn.Conv1d(in_channels=4, out_channels=2, kernel_size=5, padding="valid")
        self.a2 = nn.PReLU()
        self.fc1 = nn.Linear(2 * 19, 1)
        self.a3 = nn.Sigmoid()

    def forward(self, x):
        x = self.conv1(x)
        x = self.a1(x)
        x = self.conv2(x)
        x = self.a2(x)
        x = x.view(x.size(0), -1)
        x = self.fc1(x)
        x = self.a3(x)
        return x
