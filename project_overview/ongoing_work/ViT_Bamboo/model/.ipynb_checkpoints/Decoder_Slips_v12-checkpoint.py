import torch
import torch.nn as nn
from timm.models.vision_transformer import Block

class DecoderV1_2(nn.Module):
    def __init__(self, config):
        print("Slips_Only: DecoderV1_2")
        super().__init__()
        
        model_config = config['model']
        
        self.bamboo_feature_dim = 256 * 96 
        
        self.feature_extractor = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),  
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),  
            nn.Flatten(),
            nn.Linear(64 * 64 * 24, 512),
            nn.ReLU(),
            nn.Dropout(0.3)
        )
        
        self.match_classifier = nn.Sequential(
            nn.Linear(512 * 2, 512),  
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, 2)  
        )
        
        self.sigmoid = nn.Sigmoid()
        self.soft_max = nn.Softmax(dim=-1)
        
    def forward(self, img_256_entorphy: torch.Tensor, img_256_entorphy_sum: torch.Tensor):
        left_half = img_256_entorphy[:, 0:1, :, :]  
        right_half = img_256_entorphy[:, 1:2, :, :]  
        
        device = next(self.feature_extractor.parameters()).device
        left_half = left_half.to(device)
        right_half = right_half.to(device)
        
        left_features = self.feature_extractor(left_half)  
        right_features = self.feature_extractor(right_half) 
        
        combined_features = torch.cat([left_features, right_features], dim=1) 
        
        match_logits = self.match_classifier(combined_features) 
        match_probs = self.soft_max(match_logits)  
        
        return match_logits, match_probs