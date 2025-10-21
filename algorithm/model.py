# This file contains the model architecture for the VectorNet and CompareNet
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

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=64):
        super().__init__()
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # [1, max_len, d_model]
        self.register_buffer('pe', pe)

    def forward(self, x):
        # x: [batch, seq_len, d_model]
        return x + self.pe[:, :x.size(1), :]


class TransformerVectorNet(nn.Module):
    def __init__(self, d_model=64, nhead=8, num_layers=3, dim_feedforward=128, output_dim=32):
        super(TransformerVectorNet, self).__init__()
        
        # Input projection: 1D curve -> d_model dimension
        self.input_proj = nn.Linear(1, d_model)
        
        # Positional encoding
        self.pos_encoder = PositionalEncoding(d_model, max_len=64)
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            batch_first=True,  # Important: batch first format
            activation='gelu'
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        
        # Output projection
        self.fc = nn.Sequential(
            nn.Linear(d_model, output_dim),
            nn.PReLU()  # Keep consistent with original
        )

    def forward(self, x):
        # x shape: [batch, 1, 64]
        # Transpose to [batch, 64, 1] for processing
        x = x.transpose(1, 2)  # [batch, 64, 1]
        
        # Project to d_model dimension
        x = self.input_proj(x)  # [batch, 64, d_model]
        
        # Add positional encoding
        x = self.pos_encoder(x)  # [batch, 64, d_model]
        
        # Transformer encoding
        x = self.transformer_encoder(x)  # [batch, 64, d_model]
        
        # Global average pooling over sequence dimension
        x = x.mean(dim=1)  # [batch, d_model]
        
        # Output projection
        x = self.fc(x)  # [batch, 32]
        
        return x
    