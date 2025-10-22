import cv2
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

def extract_black_text(image_path, threshold=50):
    """
    Extract black text from bamboo slip image
    
    Args:
        image_path: Path to the bamboo slip image
        threshold: Grayscale threshold for black text (lower = darker)
        
    Returns:
        original: Original grayscale image
        binary_text: Binary image with black text on white background
    """
    # Load image
    img = cv2.imread(image_path)
    # img = img
    # print(f"Image shape: {img.shape}")
    
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Simple thresholding to extract dark text (text becomes white, background black)
    _, binary_inv = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
    
    # Clean up noise with morphological operations
    kernel = np.ones((2, 2), np.uint8)
    binary_inv = cv2.morphologyEx(binary_inv, cv2.MORPH_OPEN, kernel)
    
    # Invert colors so text is black and background is white
    binary_text = cv2.bitwise_not(binary_inv)
    
    return img, binary_text

def stitch_bamboo_slips(left_img_path, right_img_path, threshold=50):
    """
    Stitch two bamboo slip images together by analyzing their edges
    
    Args:
        left_img_path: Path to the left bamboo slip image
        right_img_path: Path to the right bamboo slip image
        threshold: Grayscale threshold for black text
        
    Returns:
        stitched_image: Stitched image with white background where needed
    """
    # Extract black text from both images
    original_left, binary_left = extract_black_text(left_img_path, threshold)
    original_right, binary_right = extract_black_text(right_img_path, threshold)
    
    # Get dimensions
    left_height, left_width = original_left.shape[:2]
    right_height, right_width = original_right.shape[:2]
    
    # Analyze right edge of left image
    right_edge_profile = []
    for y in range(left_height):
        # Count non-white pixels from the right edge
        for x in range(left_width-1, 0, -1):
            if np.sum(original_left[y, x, :]) < 700:  # Non-white pixel
                right_edge_profile.append(left_width - x)
                break
        else:
            right_edge_profile.append(0)  # No dark pixels in this row
    
    # Analyze left edge of right image
    left_edge_profile = []
    for y in range(right_height):
        # Count non-white pixels from the left edge
        for x in range(right_width):
            if np.sum(original_right[y, x, :]) < 700:  # Non-white pixel
                left_edge_profile.append(x)
                break
        else:
            left_edge_profile.append(right_width)  # No dark pixels in this row
    
    # Ensure profiles are the same length by padding the shorter one
    max_height = max(left_height, right_height)
    if len(right_edge_profile) < max_height:
        right_edge_profile.extend([0] * (max_height - len(right_edge_profile)))
    if len(left_edge_profile) < max_height:
        left_edge_profile.extend([right_width] * (max_height - len(left_edge_profile)))
    
    # Determine optimal vertical alignment
    optimal_vertical_offset = 0
    best_alignment_score = float('-inf')
    minimum_gap = 1  # Enforce a minimum gap of 10 pixels between images
    
    # Try different vertical alignments within a reasonable range
    search_range = min(left_height, right_height) // 4
    for offset in range(-search_range, search_range+1):
        alignment_scores = []
        valid_rows = 0
        
        for i in range(max(0, offset), min(left_height, right_height + offset)):
            left_idx = i
            right_idx = i - offset
            
            if left_idx < left_height and right_idx < right_height and right_idx >= 0:
                # Only consider rows where both images have content
                if right_edge_profile[left_idx] > 0 and left_edge_profile[right_idx] < right_width:
                    # Higher scores mean better alignment patterns (but not overlapping)
                    alignment_score = -(abs(right_edge_profile[left_idx] - left_edge_profile[right_idx]))
                    alignment_scores.append(alignment_score)
                    valid_rows += 1
        
        if valid_rows > 0 and len(alignment_scores) > 0:
            avg_alignment_score = sum(alignment_scores) / len(alignment_scores)
            if avg_alignment_score > best_alignment_score:
                best_alignment_score = avg_alignment_score
                optimal_vertical_offset = offset
    
    # Create the stitched image with guaranteed gap
    total_width = left_width + right_width + minimum_gap  # Always add a gap between images
    total_height = max(left_height, right_height + optimal_vertical_offset)
    
    # Create blank white canvas
    stitched_image = np.ones((total_height, total_width, 3), dtype=np.uint8) * 255
    
    # Place the left image
    stitched_image[0:left_height, 0:left_width] = original_left
    
    # Place the right image with the enforced gap
    right_x_offset = left_width + minimum_gap
    right_y_offset = max(0, optimal_vertical_offset)
    
    # Make sure we don't go out of bounds
    y_end = min(total_height, right_height + right_y_offset)
    x_end = min(total_width, right_width + right_x_offset)
    
    # Copy the right image to the stitched image
    right_img_height = y_end - right_y_offset
    right_img_width = x_end - right_x_offset
    
    if right_img_height > 0 and right_img_width > 0:
        stitched_image[right_y_offset:y_end, right_x_offset:x_end] = original_right[:right_img_height, :right_img_width]
    
    return stitched_image

def extract_black_text_stitched(image, threshold=50):
    """
    Extract black text from bamboo slip image
    
    Args:
        image_path: Path to the bamboo slip image
        threshold: Grayscale threshold for black text (lower = darker)
        
    Returns:
        original: Original grayscale image
        binary_text: Binary image with black text on white background
    """
    # Load image
    # img = cv2.imread(image_path)
    img = image
    # print(f"Image shape: {img.shape}")
    
    if img is None:
        raise ValueError(f"Could not read image: {image_path}")
    
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Simple thresholding to extract dark text (text becomes white, background black)
    _, binary_inv = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
    
    # Clean up noise with morphological operations
    kernel = np.ones((2, 2), np.uint8)
    binary_inv = cv2.morphologyEx(binary_inv, cv2.MORPH_OPEN, kernel)
    
    # Invert colors so text is black and background is white
    binary_text = cv2.bitwise_not(binary_inv)
    
    return img, binary_text

def find_text_regions_and_boundaries(binary_text, min_text_height=10, min_gap_height=20, peak_proximity_threshold=0.3):
    """
    Find text regions and their boundaries by analyzing horizontal projection
    and grouping peak areas into the same text region
    
    Args:
        binary_text: Binary image with black text on white background
        min_text_height: Minimum height of a text region
        min_gap_height: Minimum height of a gap between text regions
        peak_proximity_threshold: Threshold for peak detection and proximity (0-1)
        
    Returns:
        text_regions: List of (start, end) tuples for text regions
        gap_regions: List of (start, end) tuples for gap regions
        h_projection: Horizontal projection profile
    """
    # Invert binary image to find white (text) pixels
    inverted = 255 - binary_text
    
    # Calculate horizontal projection (sum of white/text pixels per row)
    h_projection = np.sum(inverted, axis=1)
    
    # Smooth the projection to reduce noise
    kernel = np.ones(6) / 6
    h_projection_smoothed = np.convolve(h_projection, kernel, mode='same')
    
    # Normalize projection to [0, 1] range for visualization
    h_projection_norm = h_projection_smoothed / np.max(h_projection_smoothed)
    
    # Define valid region (exclude margins)
    margin = 5
    valid_region = slice(margin, binary_text.shape[0] - margin)
    valid_projection = h_projection_norm[valid_region]
    
    # Find peaks in the projection profile
    peak_height = peak_proximity_threshold * np.max(valid_projection)
    peaks, _ = find_peaks(valid_projection, height=peak_height, distance=min_text_height//2)
    
    # Adjust peak indices to account for margin
    peaks = peaks + margin
    
    # Calculate text presence threshold (lower than before to include more of the peak areas)
    text_threshold = 0.05 * np.max(h_projection_norm[valid_region])
    
    # Find text regions based on peaks and connecting threshold areas
    text_regions = []
    
    if len(peaks) == 0:
        return [], [], h_projection_norm
    
    # Process each peak and find its surrounding text region
    for peak_idx in peaks:
        # Find start of region (scan backward from peak)
        start_idx = peak_idx
        while start_idx > valid_region.start:
            if h_projection_norm[start_idx] <= text_threshold:
                start_idx += 1  # Move back to the last position above threshold
                break
            start_idx -= 1
        
        # Find end of region (scan forward from peak)
        end_idx = peak_idx
        while end_idx < valid_region.stop - 1:
            if h_projection_norm[end_idx] <= text_threshold:
                end_idx -= 1  # Move back to the last position above threshold
                break
            end_idx += 1
        
        # If region is large enough, add it
        if end_idx - start_idx >= min_text_height:
            # Check if this region overlaps with any existing region
            overlapped = False
            for i, (existing_start, existing_end) in enumerate(text_regions):
                # Check for overlap
                if (start_idx <= existing_end and end_idx >= existing_start):
                    # Merge regions
                    text_regions[i] = (min(start_idx, existing_start), max(end_idx, existing_end))
                    overlapped = True
                    break
            
            # If no overlap, add as a new region
            if not overlapped:
                text_regions.append((start_idx, end_idx))
    
    # Sort text regions by start position
    text_regions.sort(key=lambda x: x[0])
    
    # Merge text regions that are close to each other
    i = 0
    while i < len(text_regions) - 1:
        current_end = text_regions[i][1]
        next_start = text_regions[i+1][0]
        
        if next_start - current_end < min_gap_height:
            # Merge these regions
            text_regions[i] = (text_regions[i][0], text_regions[i+1][1])
            # Remove the merged region
            text_regions.pop(i+1)
        else:
            i += 1
    
    # Find gaps between text regions
    gap_regions = []
    for i in range(len(text_regions) - 1):
        gap_start = text_regions[i][1] + 1
        gap_end = text_regions[i+1][0] - 1
        
        if gap_end - gap_start >= min_gap_height:
            gap_regions.append((gap_start, gap_end))
    
    return text_regions, gap_regions, h_projection_norm

def extract_single_words_region(original, binary_text, text_regions):
    """
    Extract and display each text region as a separate image
    
    Args:
        original: Original RGB image
        binary_text: Binary image with black text on white background
        text_regions: List of (start, end) tuples for text regions
    """
    # 存储切分后的RGB图像
    left_img_list = []
    
    # Create figure for displaying text regions
    n_regions = len(text_regions)
    if n_regions == 0:
        print("No text regions found to display.")
        return []
    
    # Calculate grid dimensions
    n_cols = min(3, n_regions)  # Max 3 columns
    n_rows = (n_regions + n_cols - 1) // n_cols  # Ceiling division
    
    # Create the figure
    # plt.figure(figsize=(15, 5 * n_rows))
    
    # For visualization, convert to RGB if needed
    if len(original.shape) == 2:
        original_rgb = cv2.cvtColor(original, cv2.COLOR_GRAY2RGB)
    else:
        original_rgb = cv2.cvtColor(original, cv2.COLOR_BGR2RGB)
    
    binary_rgb = cv2.cvtColor(binary_text, cv2.COLOR_GRAY2RGB)
    
    # # Extract and display each text region
    # for i, (start, end) in enumerate(text_regions):
    #     region_height = end - start + 1
        
    #     # Create subplots for original and binary version of each region
    #     plt.subplot(n_rows, n_cols * 2, i * 2 + 1)
        
    #     # Extract region from original image
    #     region_original = original_rgb[start:end+1, :, :]
    #     plt.imshow(region_original)
    #     plt.title(f'Region {i+1} Original')
    #     plt.axis('off')
        
    #     # Extract region from binary image
    #     plt.subplot(n_rows, n_cols * 2, i * 2 + 2)
    #     region_binary = binary_rgb[start:end+1, :, :]
    #     plt.imshow(region_binary)
    #     plt.title(f'Region {i+1} Binary')
    #     plt.axis('off')
    
    # plt.tight_layout()
    # plt.show()
    
    # Optionally, save each region as a separate file
    for i, (start, end) in enumerate(text_regions):
        region_original = original[start:end+1, :]
        region_binary = binary_text[start:end+1, :]

        #BGR to RGB 
        region_original_rgb = cv2.cvtColor(region_original, cv2.COLOR_BGR2RGB)
        left_img_list.append(region_original_rgb)
        # print(f"region_original_rgb shape:{region_original.shape},{type(region_original)}")
        
    return left_img_list