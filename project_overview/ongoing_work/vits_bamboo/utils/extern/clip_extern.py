from torchvision.transforms import Compose,Resize,CenterCrop,ToTensor,Normalize,InterpolationMode

def _convert_image_to_rgb(image):
    return image.convert("RGB")

def clip_transform(n_px):
    return Compose([
        ToTensor(),
        Resize(n_px, interpolation=InterpolationMode.BICUBIC,antialias=True),
        CenterCrop(n_px),
        # _convert_image_to_rgb,
        Normalize((0.48145466, 0.4578275, 0.40821073), (0.26862954, 0.26130258, 0.27577711)),
    ])

# clip_pre_process = clip_transform(224)