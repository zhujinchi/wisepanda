import os
import torch
import torch.nn as nn
import numpy as np
import yaml
import argparse
import shutil as su
import copy

from torch.utils.data import DataLoader
from torch.utils.tensorboard import SummaryWriter
from sklearn.metrics import average_precision_score
from tqdm import tqdm, trange

parser = argparse.ArgumentParser()
parser.add_argument('--config',type=str,default='')
parser.add_argument('--seed',type=int,default=8888)
cfg = parser.parse_args()


from DataLoader.BoxDataSetWapper import BD_Wapper
from DataLoader.FoundationModelInf.BMIFactory import BaseModelFnMap
from model.DecoderFactory import Decoder_map

def train_v1(cfg, model_fn:nn.Module, model_fn_ema:nn.Module, train_data, val_data, f_model_map, f_model_input_cfg, optimizer:torch.optim.Optimizer, loss_fn, warmup_optimizer:torch.optim.Optimizer, warmup_epoch=3):
    model_fn.cuda()
    model_fn_ema.cuda()

    
    train_param = cfg['train_param']
    
    assert(cfg['loss'].lower() in ['ce','focal'])
    assert(not os.path.exists(train_param['save_dir']))
    
    os.mkdir(train_param['save_dir'])
    cfg_file        = os.path.join(train_param['save_dir'],'train_cfg.yaml')
    model_save_path = os.path.join(train_param['save_dir'],'saved_model')
    summary_path    = os.path.join(train_param['save_dir'],'summary')
    
    sum_writer = SummaryWriter(summary_path)
    with open(cfg_file,'w') as cfg_f:
        output_cfg = copy.deepcopy(cfg)
        output_cfg['model']['Block_params']['proj_drop'] = 0.0
        output_cfg['model']['Block_params']['attn_drop'] = 0.0
        yaml.dump(output_cfg,cfg_f)
    os.mkdir(model_save_path)
    
    # 创建train_record.txt文件用于记录每个epoch的训练信息
    train_record_path = os.path.join(train_param['save_dir'], 'train_record.txt')
    with open(train_record_path, 'w') as f:
        f.write('Training Record\n')
        f.write('==============\n\n')
        f.write('Format: epoch, mAP, mAP_ema, train_loss, valid_loss, valid_loss_ema, AP details\n\n')
    
    train_loader = DataLoader(train_data, train_param['t_batch'], shuffle=True, num_workers=8, pin_memory=True, persistent_workers=False)
    valid_loader = DataLoader(val_data, train_param['v_batch'], shuffle=False, num_workers=2, pin_memory=True, persistent_workers=True)
    
    iter_count = 0
    
    cur_lr = cfg['optimizer']['lr']
    
    # 用于计算平均训练损失
    epoch_train_losses = []
    
    if warmup_optimizer is not None:
        for ep_i in trange(warmup_epoch,desc='WarmUp:'):
            #warmup_process
            epoch_train_losses = []
            model_fn.train()
            for data in tqdm(train_loader, desc='Train'):
                # print(data['img_256_entorphy'].shape)  #[128, 2, 256]
                warmup_optimizer.zero_grad()

                decoder_inputs = []
                with torch.no_grad():
                    for cfg_cell in f_model_input_cfg:
                        idx, data_key, model_key = cfg_cell
                        img_data = data[data_key].cuda()                    
                        f_feature = f_model_map[model_key](img_data)
                        decoder_inputs.append(f_feature)

                match_logits, match_probs = model_fn(data['img_256_entorphy'],data['img_256_entorphy_sum'])
                label   = data['label'].cuda()
                loss = loss_fn(match_logits,label)

                loss.backward()
                warmup_optimizer.step()
                
                loss_val = loss.detach().cpu().numpy()
                epoch_train_losses.append(loss_val)
                sum_writer.add_scalar('train_loss',loss_val,global_step=iter_count)
                iter_count += 1
            
            epoch_train_loss = sum(epoch_train_losses) / (len(epoch_train_losses) + 1e-3)
            with open(train_record_path, 'a') as f:
                f.write(f'WarmUp Epoch {ep_i}: train_loss={epoch_train_loss:.6f}\n')

    #copy ema after warmup
    model_fn_ema.load_state_dict(model_fn.state_dict())
    
    max_mAP     = 0.
    max_mAP_ema = 0.
    for ep_i in trange(train_param['epoch'],desc='Epoch:'):
        #train_process
        if 'lr_adjust' in cfg['optimizer']:
            if (ep_i + 1) % cfg['optimizer']['lr_adjust']['decay_ep'] == 0:
                cur_lr = cur_lr * cfg['optimizer']['lr_adjust']['decay_val']
            
            cur_lr = max(cur_lr, cfg['optimizer']['lr_adjust']['min_val'])
            for p_group in optimizer.param_groups:
                p_group['lr'] = cur_lr
        
        epoch_train_losses = []
        model_fn.train()
        for data in tqdm(train_loader, desc='Train'):
            optimizer.zero_grad()
            
            decoder_inputs = []
            with torch.no_grad():
                for cfg_cell in f_model_input_cfg:
                    idx, data_key, model_key = cfg_cell
                    img_data = data[data_key].cuda()                    
                    f_feature = f_model_map[model_key](img_data)
                    decoder_inputs.append(f_feature)

            match_logits, match_probs = model_fn(data['img_256_entorphy'],data['img_256_entorphy_sum'])
            label   = data['label'].cuda()
            loss = loss_fn(match_logits, label)

            loss.backward()
            optimizer.step()
            
            loss_val = loss.detach().cpu().numpy()
            epoch_train_losses.append(loss_val)
            
            sum_writer.add_scalar('train_loss',loss_val,global_step=iter_count)

            #update EMA model param
            with torch.no_grad():
                m = 1 - max(0.1 * ( 0.9 ** int(ep_i / 10) ), 0.001)  # momentum parameter
                for param_q, param_k in zip(model_fn.parameters(), model_fn_ema.parameters()):
                    param_k.data.mul_(m).add_((1 - m) * param_q.detach().data)
            
            if iter_count%5000 == 0:
                sum_writer.add_images('check_images', data['img_256'], global_step=1,dataformats='NCHW')
            iter_count += 1

        epoch_train_loss = sum(epoch_train_losses) / (len(epoch_train_losses) + 1e-3)

        #valid_process
        model_fn.eval()
        model_fn_ema.eval()
        with torch.no_grad():
            loss_val_list     = []
            loss_val_list_ema = []
            prob_list         = []
            prob_list_ema     = []
            label_list        = []
            
            for data in tqdm(valid_loader,desc='Valid'):
                decoder_inputs = []
                with torch.no_grad():
                    for cfg_cell in f_model_input_cfg:
                        idx, data_key, model_key = cfg_cell
                        img_data = data[data_key].cuda()                    
                        f_feature = f_model_map[model_key](img_data)
                        decoder_inputs.append(f_feature)
    
                match_logits, match_probs = model_fn(data['img_256_entorphy'],data['img_256_entorphy_sum'])
                match_logits_ema, match_probs_ema = model_fn_ema(data['img_256_entorphy'],data['img_256_entorphy_sum'])
                
                label   = data['label'].cuda()
                loss = loss_fn(match_logits, label)
                loss_ema = loss_fn(match_logits_ema,label)
                
                prob_list.append(match_probs.detach().cpu().numpy())
                prob_list_ema.append(match_probs_ema.detach().cpu().numpy())
                label_list.append(label.detach().cpu().numpy())
                
                loss_val = loss.detach().cpu().numpy()
                loss_val_list.append(loss_val)

                loss_val_ema = loss_ema.detach().cpu().numpy()
                loss_val_list_ema.append(loss_val_ema)
                
            mean_loss     = sum(loss_val_list) / (len(loss_val_list) + 1e-3)
            mean_loss_ema = sum(loss_val_list_ema) / (len(loss_val_list_ema) + 1e-3)

            all_prob_np     = np.concatenate(prob_list,axis=0)
            all_prob_np_ema = np.concatenate(prob_list_ema,axis=0)
            all_label_np    = np.concatenate(label_list,axis=0)
            
            AP_list = []
            AP_dict = {}
            AP_list_ema = []
            b_size,cls_num = all_prob_np.shape
            
            for i in range(cls_num):
                cur_prob_np     = all_prob_np[:,i]
                cur_prob_np_ema = all_prob_np_ema[:,i]
                cur_label_np    = all_label_np == i
                AP_val          = average_precision_score(cur_label_np, cur_prob_np)
                AP_val_ema      = average_precision_score(cur_label_np, cur_prob_np_ema)
                AP_list.append(AP_val)
                AP_dict[str(i)]     = AP_val
                AP_dict['ema_{}'.format(i)] = AP_val_ema
                AP_list_ema.append(AP_val_ema)
                
            mAP     = sum(AP_list) / (len(AP_list) + 1e-3)
            mAP_ema = sum(AP_list_ema) / (len(AP_list_ema) + 1e-3)
            
            sum_writer.add_scalar('valid_loss', mean_loss, global_step=ep_i)
            sum_writer.add_scalar('valid_loss_ema', mean_loss_ema, global_step=ep_i)
            sum_writer.add_scalar('mAP', mAP, global_step=ep_i)
            sum_writer.add_scalar('mAP_ema', mAP_ema, global_step=ep_i)
            sum_writer.add_scalars('AP', AP_dict, global_step=ep_i)
            
            with open(train_record_path, 'a') as f:
                f.write(f'Epoch {ep_i}:\n')
                f.write(f'  mAP: {mAP:.6f}, mAP_ema: {mAP_ema:.6f}\n')
                f.write(f'  train_loss: {epoch_train_loss:.6f}\n')
                f.write(f'  valid_loss: {mean_loss:.6f}, valid_loss_ema: {mean_loss_ema:.6f}\n')
                f.write('  AP values:\n')
                for i in range(cls_num):
                    f.write(f'    Class {i}: {AP_dict[str(i)]:.6f}, ema: {AP_dict["ema_"+str(i)]:.6f}\n')
                f.write('\n')
        
        torch.save(model_fn.state_dict(), os.path.join(model_save_path,'last.pt'))
        torch.save(model_fn_ema.state_dict(), os.path.join(model_save_path,'last_ema.pt'))
        if max_mAP < mAP:
            max_mAP = mAP
            su.copy(os.path.join(model_save_path,'last.pt'),os.path.join(model_save_path,'best.pt'))
            with open(os.path.join(model_save_path,'best_info.txt'),'w') as f:
                f.write('epoch: {}\n'.format(ep_i))
                f.write('mAP: {}\n'.format(mAP))
                f.write('AP:\n')
                for key in AP_dict:
                    f.write('\t{}: {}\n'.format(key,AP_dict[key]))

        if max_mAP_ema < mAP_ema:
            max_mAP_ema = mAP_ema
            su.copy(os.path.join(model_save_path,'last_ema.pt'),os.path.join(model_save_path,'best_ema.pt'))
            with open(os.path.join(model_save_path,'best_ema_info.txt'),'w') as f:
                f.write('epoch: {}\n'.format(ep_i))
                f.write('mAP: {}\n'.format(mAP_ema))
                f.write('AP:\n')
                for key in AP_dict:
                    f.write('\t{}: {}\n'.format(key,AP_dict[key]))

def main(cfg):

    torch.manual_seed(cfg.seed)
    with open(cfg.config,'r') as f:
        opt = yaml.load(f.read(), Loader=yaml.FullLoader)
    
    gpu_ids = opt['gpu_ids']
    # torch.cuda.set_device('cuda:' + gpu_ids)
    # os.environ['CUDA_VISIBLE_DEVICES'] = gpu_ids

    assert(opt['version'] >= 2)

    base_model_cfg = opt['basemodel']
    model_keys     = base_model_cfg.keys()

    foundation_model   = {}
    f_model_input_cfg  = []
    for m_key in model_keys:
        cur_cfg          = base_model_cfg[m_key]
        weight_file_path = cur_cfg['model_path']
        base_model_fn = BaseModelFnMap[m_key](weight_file_path)
        foundation_model[m_key] = base_model_fn
        f_model_input_cfg.append(
            [
                cur_cfg['decode_idx'], 
                cur_cfg['input_key'],
                m_key
            ]
        )
    f_model_input_cfg = sorted(f_model_input_cfg, key=lambda cell:cell[0])

    
    #config dataset
    train_dataset = BD_Wapper(opt, datatype='train')
    valid_dataset = BD_Wapper(opt, datatype='valid')
        
    #config model
    model_key   = opt['model']['decoder_key']
    decoder_fn  = Decoder_map[model_key]
    act_decoder = decoder_fn(opt)

    #decoder EMA model config
    act_decoder_ema = decoder_fn(opt)
    act_decoder_ema.load_state_dict(act_decoder.state_dict())
    for p in act_decoder_ema.parameters():
        p.requires_grad = False
    
    
    #config_loss
    loss_fn = None
    if opt['loss'].lower() == 'bce':
        loss_fn = nn.BCELoss()
    if opt['loss'].lower() == 'focal':
        #not ready
        # loss_fn = None
        from loss.focal_loss import focal_loss
        
        loss_params = opt['loss_params']
        loss_fn     = focal_loss(**loss_params)
        
    if opt['loss'].lower() == 'ce':
        loss_fn = nn.CrossEntropyLoss()
    
    assert(loss_fn != None)
    #config_optimizer
    tuning_opt = None
    if opt['optimizer']['type'].lower() == 'sgd':
        tuning_opt   = torch.optim.SGD(act_decoder.parameters(),lr=opt['optimizer']['lr'],momentum=opt['optimizer']['momentum'])
    elif opt['optimizer']['type'].lower() == 'adam':
        tuning_opt  = torch.optim.Adam(act_decoder.parameters(),lr=opt['optimizer']['lr']) 
    elif opt['optimizer']['type'].lower() == 'adamw':
        tuning_opt = torch.optim.AdamW(act_decoder.parameters(),lr=opt['optimizer']['lr'])
    
    warmup_opt = torch.optim.SGD(act_decoder.parameters(),lr=1e-3,momentum=0.9)
    
    assert(tuning_opt != None)
    train_v1(
        cfg=opt,
        model_fn=act_decoder,
        model_fn_ema=act_decoder_ema,
        train_data=train_dataset,
        val_data=valid_dataset,
        f_model_map=foundation_model,
        f_model_input_cfg = f_model_input_cfg,
        optimizer=tuning_opt,
        loss_fn=loss_fn,
        warmup_optimizer=warmup_opt,
        warmup_epoch=3,
        )
    # print(opt)

if __name__ == '__main__':
    main(cfg)
