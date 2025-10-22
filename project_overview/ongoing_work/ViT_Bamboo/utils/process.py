import torch
import torch.nn.functional as F
import numpy as np
import cv2
import math

def cut_half_image(box_image_256):
    w = box_image_256.size(2)
    half_w = w // 2
    
    box_image_256_left = box_image_256[:, :, :half_w]    
    box_image_256_right = box_image_256[:, :, half_w:]   

    return box_image_256_left, box_image_256_right

def extract_black_text(image_tensor, threshold=0.2):
    """
    Extract black text from bamboo slip image tensor
    
    Args:
        image_tensor: PyTorch tensor with shape (3,256,192) and values in range 0-1
        threshold: Grayscale threshold for black text (lower = darker)
        
    Returns:
        gray: Grayscale tensor with shape (1,256,192)
        binary_text: Binary tensor with black text on white background, shape (1,256,192)
    """ 
    # Get target dimensions
    target_height, target_width = 256, 96
    
    # Convert RGB to grayscale using standard conversion factors
    # Formula: gray = 0.299*R + 0.587*G + 0.114*B
    rgb_weights = torch.tensor([0.299, 0.587, 0.114], device=image_tensor.device)
    gray = torch.sum(image_tensor * rgb_weights.view(3, 1, 1), dim=0, keepdim=True)
    
    # Apply thresholding to extract dark text (text becomes 1, background 0)
    binary_inv = (gray < threshold).float()
    
    # Skip morphological operations to preserve dimensions
    # Simply use the binary inverse as is
    binary_inv_cleaned = binary_inv
    
    # Invert colors so text is 0 (black) and background is 1 (white)
    binary_text = 1 - binary_inv_cleaned
    
    return gray, binary_text


def extract_angled_horizontal_strokes_tensor(binary_tensor):
    """
    Extract horizontal strokes with angle contributions from a tensor
    
    Args:
        binary_tensor: Tensor of shape (1, 256, 192) with values 0-1
                       where 0 is text and 1 is background
        
    Returns:
        horizontal_strokes: Tensor containing only horizontal strokes (0 for strokes, 1 for background)
        angle_vis: Visualization showing contributions from different angles as RGB tensor
    """
    # Convert to PyTorch tensor if needed
    if not isinstance(binary_tensor, torch.Tensor):
        binary_tensor = torch.tensor(np.array(binary_tensor, dtype=np.float32))
        
    # 确保形状是 (1, 256, 192)
    if binary_tensor.dim() == 2:
        binary_tensor = binary_tensor.unsqueeze(0)
    
    assert binary_tensor.shape[1:] == (256, 96), f"Expected shape (1, 256, 96), got {binary_tensor.shape}"
    
    batch, height, width = binary_tensor.shape
    text_white = 1 - binary_tensor
    
    # angles = [-15, -10, -5, 0, 5, 10, 15]
    angles = [-10, -5, 0, 5, 10]
    
    angle_results = []
    angle_combined = torch.zeros_like(text_white)
    angle_vis = torch.zeros((3, height, width), dtype=torch.float32, device=binary_tensor.device)
    
    angle_colors = [
        torch.tensor([1.0, 0.0, 0.0]),  
        torch.tensor([1.0, 0.5, 0.0]),  
        torch.tensor([1.0, 1.0, 0.0]),  
        torch.tensor([0.0, 1.0, 0.0]),  
        torch.tensor([0.0, 1.0, 1.0]),  
        torch.tensor([0.0, 0.5, 1.0]),  
        torch.tensor([0.0, 0.0, 1.0])   
    ]
    
    for i, angle in enumerate(angles):
        if angle == 0:
            kernel_size = (1, 51)
            kernel = torch.ones((1, 1, kernel_size[0], kernel_size[1]), 
                                device=binary_tensor.device)
            
            pad_h = kernel_size[0] // 2
            pad_w = kernel_size[1] // 2
            
            eroded = F.conv2d(
                text_white.unsqueeze(1), 
                kernel,
                padding=(pad_h, pad_w)
            )
            eroded = (eroded >= kernel.sum()).float()
            
            result = F.conv2d(
                eroded, 
                kernel,
                padding=(pad_h, pad_w)
            )
            result = (result > 0).float().squeeze(1)
            
        else:
            kernel_size = 21 
            kernel = torch.zeros((1, 1, kernel_size, kernel_size), 
                                device=binary_tensor.device)
            
            center_x, center_y = kernel_size // 2, kernel_size // 2
            angle_rad = torch.tensor(angle * 3.14159 / 180.0)
            length = 10  
            
            cos_angle = torch.cos(angle_rad)
            sin_angle = torch.sin(angle_rad)
            
            start_x = int(center_x - length * cos_angle)
            start_y = int(center_y - length * sin_angle)
            end_x = int(center_x + length * cos_angle)
            end_y = int(center_y + length * sin_angle)
            
            dx = abs(end_x - start_x)
            dy = abs(end_y - start_y)
            sx = 1 if start_x < end_x else -1
            sy = 1 if start_y < end_y else -1
            err = dx - dy
            
            x, y = start_x, start_y
            while x != end_x or y != end_y:
                if 0 <= x < kernel_size and 0 <= y < kernel_size:
                    kernel[0, 0, y, x] = 1
                e2 = 2 * err
                if e2 > -dy:
                    err -= dy
                    x += sx
                if e2 < dx:
                    err += dx
                    y += sy
                    
            # 确保终点也被标记
            if 0 <= end_x < kernel_size and 0 <= end_y < kernel_size:
                kernel[0, 0, end_y, end_x] = 1
                
            pad_h = kernel_size // 2
            pad_w = kernel_size // 2
            
            eroded = F.conv2d(
                text_white.unsqueeze(1), 
                kernel,
                padding=(pad_h, pad_w)
            )
            eroded = (eroded >= kernel.sum()).float()
            
            result = F.conv2d(
                eroded, 
                kernel,
                padding=(pad_h, pad_w)
            )
            result = (result > 0).float().squeeze(1)
            
        assert result.shape == text_white.shape, f"Shape mismatch: {result.shape} vs {text_white.shape}"
            
        angle_results.append(result)
        
        angle_combined = torch.max(angle_combined, result)
        
        mask = result > 0
        for c in range(3):
            color_val = angle_colors[i][c].to(binary_tensor.device)
            angle_vis[c][mask.squeeze(0)] = color_val
    
    dilate_kernel = torch.ones((1, 1, 1, 3), device=binary_tensor.device)
    
    dilated = F.conv2d(
        angle_combined.unsqueeze(1), 
        dilate_kernel,
        padding=(0, 1)  
    )
    angle_combined = (dilated > 0).float().squeeze(1)
    
    # horizontal_strokes = 1 - angle_combined
    horizontal_strokes = angle_combined
    
    return horizontal_strokes, angle_vis


def calculate_contribution_value(image, edge_x, lambda_value=0.2):
    _, height, width = image.shape
    x_coords = torch.arange(width, device=image.device).float()
    contribution_map = torch.exp(-lambda_value * torch.abs(x_coords - edge_x))
    contribution_map = contribution_map.reshape(1, 1, width) * image.float()
    C = contribution_map.sum(dim=2).squeeze(0)  
    
    return C, contribution_map.squeeze(0)  

def slips_kmeans(data, n_clusters=2, n_init=10, max_iters=100):
    """
    Perform K-means clustering on a tensor using PyTorch operations
    
    Args:
        data (torch.Tensor): Input tensor of shape (1, H, W)
        n_clusters (int): Number of clusters (default 2)
        n_init (int): Number of times to run with different centroid initializations
        max_iters (int): Maximum number of iterations
    
    Returns:
        torch.Tensor: Clustered tensor with the same shape as input
    """
    # Ensure input is a tensor
    if not isinstance(data, torch.Tensor):
        data = torch.tensor(data, dtype=torch.float32)
    
    # Reshape tensor to 2D for clustering (flattening spatial dimensions)
    original_shape = data.shape
    X = data.view(-1, 1)
    
    # Best result tracking
    best_inertia = float('inf')
    best_labels = None
    
    for _ in range(n_init):
        # Random initialization of centroids
        # Sample unique initial centroids from the data
        rand_indices = torch.randperm(X.size(0))[:n_clusters]
        centroids = X[rand_indices]
        
        for _ in range(max_iters):
            # Compute distances to centroids
            distances = torch.cdist(X, centroids)
            
            # Assign points to nearest centroid
            labels = torch.argmin(distances, dim=1)
            
            # Update centroids
            new_centroids = torch.stack([
                X[labels == k].mean(dim=0) if (labels == k).any() else centroids[k]
                for k in range(n_clusters)
            ])
            
            # Check for convergence
            if torch.allclose(centroids, new_centroids, rtol=1e-4):
                break
            
            centroids = new_centroids
        
        # Compute inertia (sum of squared distances to closest centroid)
        distances = torch.cdist(X, centroids)
        inertia = torch.sum(torch.min(distances, dim=1)[0] ** 2)
        
        # Update best result if current is better
        if inertia < best_inertia:
            best_inertia = inertia
            best_labels = labels
    
    # Reconstruct the original tensor shape
    clustered_tensor = centroids[best_labels].view(original_shape)
    # clustered_tensor = 1- clustered_tensor
    
    return clustered_tensor