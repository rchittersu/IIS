#!/usr/bin/env python
"""
CSD + CLIP Style Similarity Calculator - Combined Implementation
===============================================================

This script computes both CSD style similarity and CLIP visual similarity
for stylized images, saving both metrics to the output JSON.

Based on:
- CSD: https://github.com/learn2phoenix/CSD
- CLIP: OpenAI CLIP-ViT-Large-Patch14
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
from torchvision.ops import box_convert
from transformers import CLIPProcessor, CLIPModel
import torch.nn.functional as F
sys.path.insert(0, str(pathlib.Path(__file__).parent.resolve()))

import utils
from utils import extract_features_pca

# ============================================================================
# CLIP Model Loading and Functions
# ============================================================================
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# Load CLIP model (image + text encoder)
clip_model_name = "{{MODELS_ROOT}}/clip-vit-large-patch14"
clip_model = CLIPModel.from_pretrained(clip_model_name).to(device)
clip_model.eval()
clip_processor = CLIPProcessor.from_pretrained(clip_model_name)

def get_image_embedding(image):
    inputs = clip_processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        image_features = clip_model.get_image_features(**inputs)
    # Normalize
    image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
    return image_features

def get_clip_score(img, tgt):
    emb1 = get_image_embedding(img)
    emb2 = get_image_embedding(tgt)
    # Compute cosine similarity
    cos_sim = F.cosine_similarity(emb1, emb2).item()
    return cos_sim

# ============================================================================
# CSD Model Loading (from official repo structure)
# ============================================================================
def get_cropped_image(image, mask):
    x, y, w, h = mask
    return image.crop((x, y, x+w, y+h))

def get_bbox(mask):
    mask = mask.convert('L')
    mask_ = np.array(mask)
    contours, _ = cv2.findContours(mask_, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    largest = max(contours, key=lambda c: cv2.contourArea(cv2.boxPoints(cv2.minAreaRect(c))))
    x, y, w, h = cv2.boundingRect(largest)
    return (x, y, w, h)

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
        checkpoint = torch.load(model_path, map_location="cpu")
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
            image_tensor = image_tensor.cuda().float()
            model = model.cuda().float()
        
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
    features1 = extract_features_single(model, img1_tensor, eval_embed, use_fp16)
    features2 = extract_features_single(model, img2_tensor, eval_embed, use_fp16)
        
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
def sample_patch_outside_bbox(img, x1, y1, x2, y2, yy, xx):
    H, W = img.shape[:2]
    max_retries = 100
    retries=0
    while retries<max_retries:
        retries += 1
        # Random top-left corner
        top = np.random.randint(0, H - yy)
        left = np.random.randint(0, W - xx)

        # Check if patch is completely OUTSIDE the bbox
        # A 40x40 patch from (left, top) to (left+p, top+p)
        if top + yy <= y1 or top >= y2 or left + xx <= x1 or left >= x2:
            patch = img[top:top + yy, left:left + xx]
            return patch
    return None

def main():
    parser = argparse.ArgumentParser(
        description='CSD + CLIP Style Similarity Calculator - Combined Implementation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare images with both CSD and CLIP
  python csd_clip_infer.py --jsonpath 'American_Cartoon'
  
  # Use specific GPU
  python csd_clip_infer.py --jsonpath 'Ghibli' --gpu 1
        """
    )
    
    # Required arguments
    parser.add_argument('--jsonfile', type=str,
                       help='jsonfile to process')
    parser.add_argument('--results_dir', type=str,
                       help='generated image location')
    parser.add_argument('--output_dir', type=str,
                       help='output_dir to store jsonl of metrics')
    parser.add_argument('--benchmark', type=str,
                       help='benchmark used for generation')
    parser.add_argument('--method', type=str,
                       help='method used for generation')
    parser.add_argument('--model_path', '-mp', type=str, default = "{{MODELS_ROOT}}/CSD-ViT-L/pytorch_model.bin",
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
    parser.add_argument('--gpu', type=int, default=None,
                       help='GPU id to use (default: auto-detect)')
    parser.add_argument('--jsonpath', type=str, required=True,
                       help='name of the .jsonl file (without extension) inside --src_dir')
    parser.add_argument('--src_dir', type=str, required=True,
                       help='folder with the input .jsonl files (localized rows, see tools/localize_jsonl.py)')
    parser.add_argument('--out_dir', type=str, required=True,
                       help='folder for the scored .jsonl files (csd_sim added)')
    
    args = parser.parse_args()
    args.jsonpath = f"{args.jsonpath}.jsonl"
    
    fulldata = []
    source_json = args.src_dir
    target_dir = args.out_dir
    os.makedirs(target_dir, exist_ok=True)
    with open(os.path.join(source_json, args.jsonpath)) as f:
        data = [json.loads(line) for line in f]
        fulldata += data
    
    # Validate arguments
    if not os.path.exists(args.model_path):
        parser.error(f"Model path does not exist: {args.model_path}")
    
    print("="*70)
    print("CSD + CLIP Style Similarity Calculator")
    print("Combined Implementation")
    print("="*70)
    
    # Setup GPU
    if args.gpu is not None:
        torch.cuda.set_device(args.gpu)
        print(f"\nUsing GPU: {args.gpu}")
    else:
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        print(f"\nUsing device: {device}")
    
    # Load CSD model
    print(f"\nLoading CSD model from: {args.model_path}")
    model = load_csd_model(args.model_path, args.arch, args.content_proj_head)
    model.eval()
    print("CSD Model loaded successfully!")

    # CLIP model is already loaded at module level
    print("CLIP Model loaded successfully!")
    
    # Get transform
    print("\nSetting up image preprocessing...")
    try:
        transform = get_csd_transform()
        print("Using official CSD transform")
    except:
        transform = get_standard_transform()
        print("Using standard ImageNet transform (fallback)")
    
    use_fp16 = True
   
    newdata = []
    for ind, info in enumerate(tqdm(fulldata)):
        
        style_img = Image.open(info["stylised"]).resize((512, 512))

        bbox = torch.Tensor(info["bbox_stylised"])
        bbox = box_convert(boxes=bbox * torch.Tensor([512, 512, 512, 512]), in_fmt="cxcywh", out_fmt="xyxy")
        bbox = [int(i) for i in bbox]
        fg = style_img.convert('RGB').crop(bbox)

        arr = np.array(style_img).astype(np.float32)
        
        x1, y1, x2, y2 = bbox      # xyxy
        patch = 64
        arr[y1:y2, x1:x2] = 0
        # Build a pool of outside pixels
        outside_mask = np.ones(arr.shape[:2], bool)
        outside_mask[y1:y2, x1:x2] = False
        outside_pixels = arr[outside_mask].reshape(-1, 3)
        try:
            # Compute CSD similarity
            for yy in range(y1, y2, patch):
                for xx in range(x1, x2, patch):
                    patch_block = sample_patch_outside_bbox(arr, x1, y1, x2, y2, min(patch, y2-yy), min(patch, x2-xx))
                    assert patch_block is not None
                    arr[yy:yy+min(patch, y2-yy), xx:xx+min(patch, x2-xx)] = patch_block

            out = Image.fromarray(arr.clip(0,255).astype(np.uint8))
            # out.save(os.path.join(savedir, f"{ind}_output.png"))
            # fg.save(os.path.join(savedir, f"{ind}_fg.png"))
            csd_similarity = compare_images_csd(
                fg, out, model, transform,
                eval_embed=args.eval_embed,
                metric=args.metric
            )
            info["csd_sim"] = round(csd_similarity, 3)
        except Exception as e:
            print(e)
            info["csd_sim"] = None
        
        # Compute CLIP similarity
        try:
            inpp = info["composed"]
            outp = info["stylised"]
            
            # Process input image
            inp_bbox = torch.Tensor(info["bbox"])
            w, h = Image.open(inpp).size
            inp_bbox = box_convert(boxes=inp_bbox * torch.Tensor([w, h, w, h]), in_fmt="cxcywh", out_fmt="xyxy")
            inp_bbox = [int(i) for i in inp_bbox]
            
            # Process output image to get actual dimensions from the image file
            out_img = Image.open(outp)
            out_h, out_w = out_img.height, out_img.width
            out_bbox = torch.Tensor(info["bbox_stylised"])
            out_bbox = box_convert(boxes=out_bbox * torch.Tensor([out_w, out_h, out_w, out_h]), in_fmt="cxcywh", out_fmt="xyxy")
            out_bbox = [int(i) for i in out_bbox]

            # Crop and compute similarity 
            inp = Image.open(inpp).convert('RGB').crop(inp_bbox)
            out = out_img.convert('RGB').crop(out_bbox)
            clip_similarity = get_clip_score(inp, out)
            info["clip_sim"] = round(clip_similarity, 3)
        except Exception as e:
            print(e)
            info["clip_sim"] = None
        
        
        # Write to output file incrementally
        with open(os.path.join(target_dir, args.jsonpath), 'a+') as f:
            json_string = json.dumps(info)
            f.write(json_string + '\n')

if __name__ == '__main__':
    main()