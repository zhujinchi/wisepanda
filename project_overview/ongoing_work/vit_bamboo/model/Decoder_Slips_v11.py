import torch
import torch.nn as nn
from timm.models.vision_transformer import Block

class DecoderV1_1(nn.Module):
    def __init__(self, config):
        print("Slips_Only_v11: img_256_entorphy_sum Only")
        super().__init__()
        
        model_config = config['model']
        
        self.sum_feature_extractor = nn.Sequential(
            nn.Conv1d(1, 32, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(2),  
            nn.Conv1d(32, 64, kernel_size=3, padding=1),
            nn.ReLU(),
            nn.MaxPool1d(2),  
            nn.Flatten(),
            nn.Linear(64 * 64, 256),
            nn.ReLU(),
            nn.Dropout(0.3)
        )
        
        self.sum_match_classifier = nn.Sequential(
            nn.Linear(256 * 2, 256),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(128, 2)
        )
        
        self.soft_max = nn.Softmax(dim=-1)
        
    def forward(self, img_256_entorphy: torch.Tensor, img_256_entorphy_sum: torch.Tensor):
        left_sum = img_256_entorphy_sum[:, 0:1, :]  
        right_sum = img_256_entorphy_sum[:, 1:2, :] 
        
        device = next(self.sum_feature_extractor.parameters()).device
        left_sum = left_sum.to(device)
        right_sum = right_sum.to(device)
        
        left_sum_features = self.sum_feature_extractor(left_sum)   
        right_sum_features = self.sum_feature_extractor(right_sum) 
        
        combined_sum_features = torch.cat([left_sum_features, right_sum_features], dim=1)
        
        match_logits = self.sum_match_classifier(combined_sum_features)
        match_probs = self.soft_max(match_logits)  
        
        return match_logits, match_probs