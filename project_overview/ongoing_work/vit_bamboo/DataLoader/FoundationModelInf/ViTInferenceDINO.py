from typing import Any
import torch
import time

from torchvision import transforms

class DINOmodel_jit:
    def __init__(self, jit_model_path, feature_map_shape=[768, 14, 14]):
        self.model_fn = torch.jit.load(jit_model_path)
        self.lock_flag = False
        self.input_norm = transforms.Normalize((0.485, 0.456, 0.406), (0.229, 0.224, 0.225))
        self.fm_shape = feature_map_shape

        self.model_fn.cuda()
        self.model_fn.eval()
        # print('dino base ready')

    def __call__(self, image_input):
        return self.inference(image_input)
    
    def inference(self, image_input):
        '''
            image_input  batch_size * 3 * img_h * img_w with [0,1] value
        '''

        batch_size = image_input.shape[0]
        output_shape = [batch_size]
        output_shape.extend(self.fm_shape)
        # print(output_shape)
        normed_input = self.input_norm(image_input)
        result       = self.model_fn(normed_input)
        result       = result[:,1:,:].permute(0,2,1)  #only featuremap
        result       = result.reshape(output_shape)

        return result
    
if __name__ == '__main__':
    model_path = './RefModel/dino_jits/vit_base_student_224.pth'
    
    vit_small = DINOmodel_jit(model_path)
    
    
    rand_input = torch.randn([1,3,224,224]).cuda()
    for i in range(10):
        print('test inference ',i)
        result = vit_small(rand_input)
        print('test inference done')
    rand_input_batch = rand_input.repeat([128,1,1,1])
    print('test batch input shape: ',rand_input_batch.shape)
    result = vit_small(rand_input_batch)
    print('test batch inference done')
    print(result.shape)
    print(result[0,2,:3,:5])
    print(result[10,2,:3,:5])
