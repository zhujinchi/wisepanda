from DataLoader.BoxDataSet import BoxDataSet
from DataLoader.BoxDataSet_v1 import BoxDataSet

def BD_Wapper(opt, datatype):
    if 'version' in opt and opt['version'] == 1:
        return BoxDataSet_v1(opt, datatype)
    else:
        return BoxDataSet(opt, datatype)