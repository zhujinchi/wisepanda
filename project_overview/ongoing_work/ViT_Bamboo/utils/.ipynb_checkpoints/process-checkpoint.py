import torch
import torch.nn.functional as F
import numpy as np
import cv2
import math

def cut_half_image(box_image_256):
    w = box_image_256.size(2)
    half_w = w // 2
    
    box_image_256_left = box_image_256[:, :, :half_w]    # 左半部分
    box_image_256_right = box_image_256[:, :, half_w:]   # 右半部分

    return box_image_256_left, box_image_256_right
    
# def tensor_to_grayscale(tensor):
#     """
#     功能: 提取灰度图或提取反向灰度图（数值越大颜色越黑）
#     将形状为 (3, H, W) 的 tensor 转换为灰度图
#     使用公式: Y = 0.299*R + 0.587*G + 0.114*B
#     """
#     if tensor.dim() != 3 or tensor.size(0) != 3:
#         raise ValueError("输入 tensor 形状应为 (3, H, W)")
    
#     # 转换公式的权重
#     weights = torch.tensor([0.299, 0.587, 0.114], device=tensor.device).view(3, 1, 1)
    
#     # 计算加权和
#     grayscale = (tensor * weights).sum(dim=0, keepdim=True)  # 结果形状 (1, H, W)
#     # grayscale = 1 - (tensor * weights).sum(dim=0, keepdim=True)  # 结果形状 (1, H, W)
    
#     return grayscale

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


# def extract_angled_horizontal_strokes(binary_text_tensor):
#     """
#     Extract horizontal strokes with angle contributions from a PyTorch tensor
    
#     Args:
#         binary_text_tensor: Binary tensor with black text (0) on white background (1),
#                           shape (1, H, W)
        
#     Returns:
#         horizontal_strokes: Binary tensor containing only horizontal strokes, shape (1, H, W)
#         angle_vis: Visualization tensor showing contributions from different angles, shape (3, H, W)
#     """
#     # Ensure tensor is in correct shape (1, H, W)
#     if len(binary_text_tensor.shape) != 3 or binary_text_tensor.shape[0] != 1:
#         raise ValueError("Input tensor should be of shape (1, H, W)")
    
#     height = binary_text_tensor.shape[1]
#     width = binary_text_tensor.shape[2]
    
#     # Initialize output tensors
#     horizontal_strokes = torch.zeros_like(binary_text_tensor)
#     angle_vis = torch.zeros((3, height, width), dtype=torch.float32)
    
#     # Define angles to check
#     angles = [-15, -10, -5, 0, 5, 10, 15]
    
#     # Colors for different angles (BGR format for OpenCV)
#     angle_colors = [(255, 0, 0), (255, 128, 0), (255, 255, 0), 
#                    (0, 255, 0), (0, 255, 255), (0, 128, 255), (0, 0, 255)]
    
#     # Convert tensor to numpy for OpenCV processing
#     binary_text_np = binary_text_tensor[0].cpu().numpy()
#     binary_text_np = (binary_text_np * 255).astype(np.uint8)
    
#     # Invert image so text is white (255) and background is black (0)
#     text_white = cv2.bitwise_not(binary_text_np)
    
#     # Storage for results at different angles
#     angle_combined = np.zeros_like(text_white)
    
#     # Visualization image with color for each angle
#     angle_vis_np = np.zeros((height, width, 3), dtype=np.uint8)
    
#     # Process each angle
#     for i, angle in enumerate(angles):
#         # For 0 degrees (horizontal), use standard morphological opening
#         if angle == 0:
#             kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
#             result = cv2.morphologyEx(text_white, cv2.MORPH_OPEN, kernel)
#         else:
#             # For angled lines, create a custom kernel
#             kernel_size = 21
#             kernel = np.zeros((kernel_size, kernel_size), dtype=np.uint8)
            
#             # Find center point
#             center_x, center_y = kernel_size // 2, kernel_size // 2
            
#             # Draw a line at the specified angle
#             angle_rad = math.radians(angle)
#             length = 10  # Half-length of the line
            
#             start_x = int(center_x - length * math.cos(angle_rad))
#             start_y = int(center_y - length * math.sin(angle_rad))
#             end_x = int(center_x + length * math.cos(angle_rad))
#             end_y = int(center_y + length * math.sin(angle_rad))
            
#             cv2.line(kernel, (start_x, start_y), (end_x, end_y), 1, 1)
            
#             # Apply morphological opening with the angled kernel
#             result = cv2.morphologyEx(text_white, cv2.MORPH_OPEN, kernel)
        
#         # Add to combined result
#         angle_combined = cv2.bitwise_or(angle_combined, result)
        
#         # Add colored version to visualization
#         mask = result > 0
#         angle_vis_np[mask] = angle_colors[i]
    
#     # Apply slight dilation to connect nearby strokes
#     angle_combined = cv2.dilate(angle_combined, np.ones((1, 3), np.uint8), iterations=1)
    
#     # Invert back to black strokes on white background and store in output tensor
#     horizontal_strokes_np = cv2.bitwise_not(angle_combined)
#     horizontal_strokes[0] = torch.from_numpy(horizontal_strokes_np / 255.0).float()
    
#     # Store visualization in output tensor
#     angle_vis = torch.from_numpy(angle_vis_np / 255.0).permute(2, 0, 1).float()
    
#     return horizontal_strokes, angle_vis

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
    
    # 提取尺寸信息
    batch, height, width = binary_tensor.shape
    
    # 反转图像，使文字为1，背景为0（保持在0-1范围内）
    text_white = 1 - binary_tensor
    
    # 定义要检查的角度
    # angles = [-15, -10, -5, 0, 5, 10, 15]
    angles = [-10, -5, 0, 5, 10]
    
    # 存储不同角度的结果
    angle_results = []
    # 使用和输入相同尺寸的tensor初始化angle_combined
    angle_combined = torch.zeros_like(text_white)
    
    # 可视化图像，为每个角度使用不同颜色
    # 创建RGB图像张量
    angle_vis = torch.zeros((3, height, width), dtype=torch.float32, device=binary_tensor.device)
    
    # 为不同角度定义颜色 (R, G, B)，归一化到0-1
    angle_colors = [
        torch.tensor([1.0, 0.0, 0.0]),  # 红色
        torch.tensor([1.0, 0.5, 0.0]),  # 橙色
        torch.tensor([1.0, 1.0, 0.0]),  # 黄色
        torch.tensor([0.0, 1.0, 0.0]),  # 绿色
        torch.tensor([0.0, 1.0, 1.0]),  # 青色
        torch.tensor([0.0, 0.5, 1.0]),  # 浅蓝色
        torch.tensor([0.0, 0.0, 1.0])   # 蓝色
    ]
    
    # 处理每个角度
    for i, angle in enumerate(angles):
        # 对于0度（水平），使用水平线性内核
        if angle == 0:
            # 创建水平线性内核 (50x1)，使用奇数尺寸以避免填充问题
            kernel_size = (1, 51)  # 改为奇数，使padding更容易计算
            kernel = torch.ones((1, 1, kernel_size[0], kernel_size[1]), 
                                device=binary_tensor.device)
            
            # 计算正确的padding以保持输出尺寸与输入相同
            pad_h = kernel_size[0] // 2
            pad_w = kernel_size[1] // 2
            
            # 应用形态学开运算（先腐蚀后膨胀）
            # 腐蚀
            eroded = F.conv2d(
                text_white.unsqueeze(1), 
                kernel,
                padding=(pad_h, pad_w)
            )
            eroded = (eroded >= kernel.sum()).float()
            
            # 膨胀 
            result = F.conv2d(
                eroded, 
                kernel,
                padding=(pad_h, pad_w)
            )
            result = (result > 0).float().squeeze(1)
            
        else:
            # 对于不同角度的线，创建自定义内核
            kernel_size = 21  # 确保是奇数尺寸
            kernel = torch.zeros((1, 1, kernel_size, kernel_size), 
                                device=binary_tensor.device)
            
            # 找中心点
            center_x, center_y = kernel_size // 2, kernel_size // 2
            
            # 在指定角度绘制线
            angle_rad = torch.tensor(angle * 3.14159 / 180.0)
            length = 10  # 线的半长度
            
            # 计算起点和终点
            cos_angle = torch.cos(angle_rad)
            sin_angle = torch.sin(angle_rad)
            
            start_x = int(center_x - length * cos_angle)
            start_y = int(center_y - length * sin_angle)
            end_x = int(center_x + length * cos_angle)
            end_y = int(center_y + length * sin_angle)
            
            # 使用Bresenham算法绘制线
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
                
            # 计算正确的padding以保持输出尺寸与输入相同
            pad_h = kernel_size // 2
            pad_w = kernel_size // 2
            
            # 应用形态学开运算
            # 腐蚀
            eroded = F.conv2d(
                text_white.unsqueeze(1), 
                kernel,
                padding=(pad_h, pad_w)
            )
            eroded = (eroded >= kernel.sum()).float()
            
            # 膨胀
            result = F.conv2d(
                eroded, 
                kernel,
                padding=(pad_h, pad_w)
            )
            result = (result > 0).float().squeeze(1)
            
        # 验证结果尺寸与输入相同
        assert result.shape == text_white.shape, f"Shape mismatch: {result.shape} vs {text_white.shape}"
            
        # 存储此角度的结果
        angle_results.append(result)
        
        # 添加到组合结果（按位或）
        angle_combined = torch.max(angle_combined, result)
        
        # 添加彩色版本到可视化
        mask = result > 0
        for c in range(3):
            # 确保颜色值在设备上
            color_val = angle_colors[i][c].to(binary_tensor.device)
            angle_vis[c][mask.squeeze(0)] = color_val
    
    # 应用轻微的膨胀以连接附近的笔画
    # 创建水平线性内核 (1x3) 用于膨胀，使用奇数尺寸
    dilate_kernel = torch.ones((1, 1, 1, 3), device=binary_tensor.device)
    
    # 使用正确的padding保持尺寸
    dilated = F.conv2d(
        angle_combined.unsqueeze(1), 
        dilate_kernel,
        padding=(0, 1)  # 水平方向上每边填充1，垂直方向不填充
    )
    angle_combined = (dilated > 0).float().squeeze(1)
    
    # 反转回黑色笔画在白色背景上（笔画为0，背景为1）
    # horizontal_strokes = 1 - angle_combined
    horizontal_strokes = angle_combined
    
    return horizontal_strokes, angle_vis


def calculate_contribution_value(image, edge_x, lambda_value=0.2):
    """
    向量化实现，计算单张图像中每一行的总贡献值。
    
    参数:
    image -- 单张二值图像，形状为 (1, height, width)，
             其中边缘像素值为1，非边缘像素值为0。
    edge_x -- 断裂边缘的x坐标。
    lambda_value -- 衰减系数，默认为1.0
    
    返回:
    C -- 每一行的总贡献值，形状为 (height,)
    contribution_map -- 每个像素点的贡献度，形状为 (height, width)
    """
    _, height, width = image.shape
    
    # 创建x坐标网格
    x_coords = torch.arange(width, device=image.device).float()
    
    # 计算所有位置的贡献度
    contribution_map = torch.exp(-lambda_value * torch.abs(x_coords - edge_x))
    
    # 只保留边缘像素的贡献度
    contribution_map = contribution_map.reshape(1, 1, width) * image.float()
    
    # 计算每行的总贡献值
    C = contribution_map.sum(dim=2).squeeze(0)  # 从(1,H,W)到(H,)
    
    return C, contribution_map.squeeze(0)  # 从(1,H,W)到(H,W)

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