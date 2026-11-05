#!/usr/bin/env python
"""
CSD Style Similarity Calculator - Based on Official Repository
===============================================================

This script uses the actual CSD repository structure to compute style similarity
between two images using Contrastive Style Descriptors.

Based on: https://github.com/learn2phoenix/CSD
Reference: main_sim.py from the official repository
"""

import cv2
import argparse
import os
import os.path as osp
import sys
from pathlib import Path
import json
import torch
import torch.nn as nn
import numpy as np
from PIL import Image
import builtins
import pathlib
import random
import warnings
from tqdm import tqdm
import numpy as np
import torch
import torch.nn as nn
import torch.nn.parallel
import torch.backends.cudnn as cudnn
import torch.distributed as dist
import torch.optim
import torch.multiprocessing as mp
import torch.utils.data
import torch.utils.data.distributed
from torchvision import transforms
import torchvision.models as torchvision_models
from torchvision.models import VGG16_Weights

sys.path.insert(0, str(pathlib.Path(__file__).parent.resolve()))

import utils
from utils import extract_features_pca
# from models import dino_vits, moco_vits

# ============================================================================
# CSD Model Loading (from official repo structure)
# ============================================================================
def get_cropped_image(image, mask):
    x, y, w, h = mask
    return image.crop((x, y, x+w, y+h))

def get_bbox(mask):
    mask = mask.convert('L')
    W, H = mask.size
    mask_ = np.array(mask)
    contours, _ = cv2.findContours(mask_, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest = max(contours, key=lambda c: cv2.contourArea(cv2.boxPoints(cv2.minAreaRect(c))))
    x, y, w, h = cv2.boundingRect(largest)

    scale = 0
    x1 = max(0, x - int(scale*w))
    x2 = min(W, x1 + w + int(scale*w))
    y1 = max(0, y - int(scale*h))
    y2 = min(H, y1 + h + int(scale*h))
    return x1, y1, x2-x1, y2-y1

def load_csd_model(model_path, arch='vit_large', content_proj_head='default'):
    """
    Load CSD model following the official repository structure
    
    Args:
        model_path: Path to CSD checkpoint (.pth file)
        arch: Architecture ('vit_base' or 'vit_large')
        content_proj_head: Projection head type
    
    Returns:
        Loaded model ready for inference
    """
    try:
        # Import from CSD module structure
        sys.path.insert(0, str(Path(__file__).parent.resolve()))
        from CSD.model import CSD_CLIP
        from CSD.utils import has_batchnorms, convert_state_dict
    except ImportError:
        print("Error: CSD module not found!")
        print("\nPlease ensure you have cloned the CSD repository:")
        print("  git clone https://github.com/learn2phoenix/CSD.git")
        print("\nOr create a CSD directory with model.py and utils.py")
        raise
    
    print(f"Loading CSD model: {arch}")
    
    # Create model
    model = CSD_CLIP(arch, content_proj_head)
    
    # Handle batch normalization
    if has_batchnorms(model):
        model = nn.SyncBatchNorm.convert_sync_batchnorm(model)
    
    # Load checkpoint
    if model_path.endswith('.bin'):
        state_dict = torch.load(model_path, map_location="cpu", weights_only=False)
    elif model_path.endswith('.pth'):
        checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)
        state_dict = checkpoint['model_state_dict']
        
    state_dict = convert_state_dict(state_dict)
    msg = model.load_state_dict(state_dict, strict=False)
    
    print(f"Model loaded with message: {msg}")
    
    return model


def get_csd_transform():
    """
    Get the official CSD preprocessing transform
    This matches the transforms_branch0 from CSD.loss_utils
    """
    from CSD.loss_utils import transforms_branch0
    return transforms_branch0


def get_standard_transform():
    """
    Standard ImageNet preprocessing (fallback if CSD transform not available)
    """
    return transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


# ============================================================================
# Feature Extraction (following official repo)
# ============================================================================

def extract_features_single(model, image_tensor, eval_embed='head', use_fp16=True):
    """
    Extract features from a single image using CSD model
    Following the extract_features function from CSD.utils
    
    Args:
        model: CSD model
        image_tensor: Preprocessed image tensor (1, 3, 224, 224)
        eval_embed: Which embedding to use ('head' or 'backbone')
        use_fp16: Use half precision for efficiency
    
    Returns:
        Feature embedding (numpy array)
    """
    model.eval()
    
    with torch.no_grad():
        if use_fp16:
            image_tensor = image_tensor.half()
            model = model.half()
        
        # Forward pass through model
        if eval_embed == 'head':
            # Use the projection head output (default for style comparison)
            features = model(image_tensor)
        else:
            # Use backbone features
            features = model.encode_image(image_tensor)
        
        # Convert to numpy
        # print(type(features[0]))
        if isinstance(features, tuple):
            features = features[0]
        features = features.cpu().float().numpy()

        # features = np.array([tensor.cpu().float().numpy() for tensor in features])
    
    return features


def load_and_preprocess_image(image, transform):
    """
    Load and preprocess an image for CSD model
    
    Args:
        image_path: Path to image file
        transform: Preprocessing transform
    
    Returns:
        Preprocessed tensor ready for model
    """
    # image = Image.open(image_path).convert('RGB')
    image_tensor = transform(image).unsqueeze(0)  # Add batch dimension
    return image_tensor


# ============================================================================
# Similarity Computation
# ============================================================================

def compute_cosine_similarity(features1, features2):
    """
    Compute cosine similarity between two feature vectors
    
    Args:
        features1: First feature vector (numpy array)
        features2: Second feature vector (numpy array)
    
    Returns:
        Cosine similarity score (float)
    """
    # Normalize features
    features1 = features1 / (np.linalg.norm(features1) + 1e-8)
    features2 = features2 / (np.linalg.norm(features2) + 1e-8)
    
    # Compute dot product (cosine similarity for normalized vectors)
    similarity = np.dot(features1.flatten(), features2.flatten())
    
    return float(similarity)


def compute_euclidean_distance(features1, features2):
    """
    Compute Euclidean distance between two feature vectors
    
    Args:
        features1: First feature vector
        features2: Second feature vector
    
    Returns:
        Euclidean distance (lower = more similar)
    """
    distance = np.linalg.norm(features1 - features2)
    return float(distance)


# ============================================================================
# Main Comparison Function
# ============================================================================

def compare_images_csd(image1, image2, model, transform, 
                       eval_embed='head', use_fp16=True, metric='cosine'):
    """
    Compare style similarity between two images using CSD
    
    Args:
        image1_path: Path to first image
        image2_path: Path to second image
        model: Loaded CSD model
        transform: Image preprocessing transform
        eval_embed: Which embedding to use ('head' or 'backbone')
        use_fp16: Use half precision
        metric: Similarity metric ('cosine' or 'euclidean')
    
    Returns:
        Similarity score
    """
    print(f"\nProcessing images...")
    # print(f"  Image 1: {image1_path}")
    # print(f"  Image 2: {image2_path}")
    
    # Move model to GPU if available
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = model.to(device)
    
    # Load and preprocess images
    img1_tensor = load_and_preprocess_image(image1, transform).to(device)
    img2_tensor = load_and_preprocess_image(image2, transform).to(device)
    
    # Extract features
    print(f"  Extracting features using '{eval_embed}' embeddings...")
    features1 = extract_features_single(model, img1_tensor, eval_embed, use_fp16)
    features2 = extract_features_single(model, img2_tensor, eval_embed, use_fp16)
    
    print(f"  Feature shape: {features1.shape}")
    
    # Compute similarity
    if metric == 'cosine':
        score = compute_cosine_similarity(features1, features2)
    elif metric == 'euclidean':
        score = compute_euclidean_distance(features1, features2)
    else:
        raise ValueError(f"Unknown metric: {metric}")
    
    return score

# ============================================================================
# Command Line Interface
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='CSD Style Similarity - Official Repository Implementation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare two images
  python csd_official.py --image1 img1.jpg --image2 img2.jpg --model_path csd_vitl.pth
  
  # Batch comparison
  python csd_official.py --image1 query.jpg --batch img1.jpg img2.jpg img3.jpg --model_path csd_vitl.pth
  
  # Use backbone features instead of projection head
  python csd_official.py --image1 img1.jpg --image2 img2.jpg --model_path csd_vitl.pth --eval_embed backbone
        """
    )
    
    # Required arguments
    parser.add_argument('--jsonfile', type=str, required=True,
                       help='jsonfile to process')
    parser.add_argument('--results_dir', type=str, required=True,
                       help='generated image location')
    parser.add_argument('--output_dir', type=str, required=True,
                       help='output_dir to store jsonl of metrics')
    parser.add_argument('--benchmark', type=str, required=True,
                       help='benchmark used for generation')
    parser.add_argument('--method', type=str, required=True,
                       help='method used for generation')
    parser.add_argument('--model_path', '-mp', type=str, required=True,
                       help='Path to CSD model checkpoint (.pth or .bin file)')
    
    # Model arguments
    parser.add_argument('--arch', '-a', type=str, default='vit_base',
                       choices=['vit_base', 'vit_large'],
                       help='Model architecture (default: vit_large)')
    parser.add_argument('--eval_embed', type=str, default='head',
                       choices=['head', 'backbone'],
                       help='Which embedding to use: head (default) or backbone')
    parser.add_argument('--content_proj_head', type=str, default='default',
                       help='Content projection head type')
    
    # Computation arguments
    parser.add_argument('--metric', type=str, default='cosine',
                       choices=['cosine', 'euclidean'],
                       help='Similarity metric (default: cosine)')
    parser.add_argument('--no_fp16', action='store_true',
                       help='Disable half precision (use full fp32)')
    parser.add_argument('--data_root', type=str, default='',
                       help='root for relative image paths in --jsonfile (e.g. benchmark/)')
    parser.add_argument('--gpu', type=int, default=None,
                       help='GPU id to use (default: auto-detect)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not os.path.exists(args.model_path):
        parser.error(f"Model path does not exist: {args.model_path}")
    
    print("="*70)
    print("CSD Style Similarity Calculator")
    print("Official Repository Implementation")
    print("="*70)
    
    # Setup GPU
    if args.gpu is not None:
        torch.cuda.set_device(args.gpu)
        print(f"\nUsing GPU: {args.gpu}")
    else:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"\nUsing device: {device}")
    
    # Load model
    print(f"\nLoading CSD model from: {args.model_path}")
    model = load_csd_model(args.model_path, args.arch, args.content_proj_head)
    model.eval()
    print("✓ Model loaded successfully!")
    
    # Get transform
    print("\nSetting up image preprocessing...")
    try:
        transform = get_csd_transform()
        print("✓ Using official CSD transform")
    except:
        transform = get_standard_transform()
        print("✓ Using standard ImageNet transform (fallback)")
    
    use_fp16 = not args.no_fp16
    
    
    os.makedirs(args.output_dir,exist_ok=True)
    # read json..
    valid_info = json.load(open(args.jsonfile))
    for info in valid_info:  # benchmark JSONs store paths relative to the benchmark root
        for k in ("ref_image", "ref_mask", "background_image", "background_mask"):
            if k in info and not os.path.isabs(info[k]):
                info[k] = os.path.join(args.data_root, info[k])

    method = args.method

    for info in tqdm(valid_info, desc='files'):
        id = info['id']
        org_img = Image.open(info['background_image']).convert("RGB")
        # print(img_name)

        fg_img_path = info["ref_image"]
        fg_img = Image.open(fg_img_path).convert('RGB')
        fg_mask_path = info['ref_mask']
        fg_mask = Image.open(fg_mask_path)
        fg_mask_bbox = get_bbox(fg_mask)
        fg_img_cropped = get_cropped_image(fg_img, fg_mask_bbox)
        json_out_name = osp.join(args.output_dir, f"{method}.jsonl")
        bg_img_path = os.path.join(args.results_dir, f"{str(id)}.png")
        # bg_img_path = os.path.join(args.results_dir, args.benchmark, f"{str(id)}.png")
        if not os.path.isfile(bg_img_path):
            print(f"Skipping {bg_img_path} as its not generated for {method}")
            continue
        
        bg_img = Image.open(bg_img_path).convert('RGB')
        bg_mask_path = info["background_mask"]
        bg_mask = Image.open(bg_mask_path).resize(bg_img.size, Image.NEAREST)
        print(bg_mask.size, bg_img.size)
        bg_mask_bbox = get_bbox(bg_mask)
        bg_img_cropped = get_cropped_image(bg_img, bg_mask_bbox)
        
        csd_similarity = compare_images_csd(
            bg_img_cropped, org_img, model, transform, # hmm
            eval_embed=args.eval_embed,
            use_fp16=use_fp16,
            metric=args.metric
        )
        
        ans = {
            'id': id,
            'csd': csd_similarity
        }
        with open(json_out_name,"a+") as op:
            op.write(json.dumps(ans) + "\n")

if __name__ == '__main__':
    main()