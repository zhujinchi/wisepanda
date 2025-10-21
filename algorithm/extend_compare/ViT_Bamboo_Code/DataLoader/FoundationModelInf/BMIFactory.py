from DataLoader.FoundationModelInf.ViTInference import ViTmodel_jit
from DataLoader.FoundationModelInf.ViTInferenceDINO import DINOmodel_jit


BaseModelFnMap={
    'vit': ViTmodel_jit,
    'dino': DINOmodel_jit
}