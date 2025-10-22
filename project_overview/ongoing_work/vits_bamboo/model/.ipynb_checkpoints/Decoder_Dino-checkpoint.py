import torch
import torch.nn as nn
# import transformers.models

from timm.models.vision_transformer import Block

class DecoderV1(nn.Module):
    def __init__(self, config):
        print("Dino_Only: DecoderV1_1")
        super().__init__()
        
        model_config = config['model']
        
        vit_c, vit_h, vit_w  = config['basemodel']['dino']['vit_output_shape']
        self.num_c    = vit_c
        self.feat_h   = vit_h
        self.feat_w   = vit_w
        
        self.depth   = model_config['num_layers']
        self.cls_num = model_config['cls_num']
        layer_params = model_config['Block_params']
        
        self.dim = model_config['Block_params']['dim']
        
        # self.pose_pos_embed    = nn.Parameter(torch.randn(pos_h*pos_w, self.dim) * .02)
        # self.point_type_embed  = nn.Parameter(torch.randn(self.keypoint_num, self.dim) * .02)
        
        self.first_norm = nn.LayerNorm(self.num_c)
        self.dim_red    = nn.Linear(self.num_c, self.dim)
        self.cls_token  = nn.Parameter(torch.randn(1, 1, self.dim) * 0.02)
       
        model_seq = []
        for i in range(self.depth):
            block_layer = Block(**layer_params)
            model_seq.append(block_layer)
            
        self.blocks    = nn.Sequential(*model_seq)
        self.last_norm = nn.LayerNorm(self.dim)
        self.cls_fc    = nn.Linear(self.dim, self.cls_num)
        
        self.sigmoid   = nn.Sigmoid()
        self.soft_max  = nn.Softmax(dim=-1)
        
    def forward(self, dino_feat:torch.Tensor, base_feat:torch.Tensor):    
    # def forward(self, dino_feat:torch.Tensor):
        '''
        input:
            pose_feat (batchsize, point_num, height, width) human pose inference result
            
        output:
            cls_logits (batchsize, cls_num)
        '''
        batch_size, c_num, feat_h, feat_w = dino_feat.shape
        assert(self.num_c   == c_num)
        assert(self.feat_h  == feat_h)
        assert(self.feat_w  == feat_w)
        
        x = dino_feat.reshape([batch_size, c_num, -1]).permute(0,2,1)
        x = self.first_norm(x)
        x = self.dim_red(x)
        
        batched_cls_token = self.cls_token.repeat(batch_size, 1, 1)
        x = torch.cat([batched_cls_token, x], dim=1)
        x = self.blocks(x)
        
        if self.last_norm != None:
            self.last_norm(x)
        
        cls_feature = x[:, 0,:]
        cls_logits = self.cls_fc(cls_feature)
        
        if self.cls_num == 1:
            cls_probs = self.sigmoid(cls_logits)
        else:
            cls_probs = self.soft_max(cls_logits)
        
        return cls_logits,cls_probs