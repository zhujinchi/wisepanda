import torch
import torch.nn as nn
from torch.nn import functional as F


class focal_loss(nn.Module):
    def __init__(self, num_classes=2, alpha=[0.5,0.5], gamma=2, size_average=True):
        super(focal_loss, self).__init__()
        self.size_average = size_average
        assert(len(alpha) == num_classes)
        self.alpha = torch.Tensor(alpha)
        self.gamma = gamma
        
    def forward(self, logits:torch.Tensor, labels:torch.Tensor):
        '''
        logits (batch_size, cls_num)
        labels (batch_size)
        '''
        
        cur_alpha = self.alpha.to(logits.device)
        # print(logits.device)
        # print(labels.device)
        # print(self.alpha.device)
        probs     = F.softmax(logits, dim=1)
        log_probs = torch.log(probs)
        
        probs     = probs.gather(1,labels.view(-1,1))
        log_probs = log_probs.gather(1,labels.view(-1,1))
        cur_alpha = cur_alpha.gather(0,labels.view(-1))
        
        loss = -torch.mul(torch.pow(1 - probs, self.gamma), log_probs)
        loss = torch.mul(cur_alpha, loss.t())
        
        if self.size_average:
            return loss.mean()
        else:
            return loss
        
if __name__ == '__main__':
    loss_fn = focal_loss()
    print(loss_fn.alpha.shape)