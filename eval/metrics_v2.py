import torch
import torch.nn as nn
import os
import os.path as osp
import json
import numpy as np
from tqdm import tqdm
import cv2
from PIL import Image
import torchvision.transforms as transforms
from torchvision.utils import save_image
import pprint as pp
import argparse
from torchvision.transforms.functional import pil_to_tensor
from transformers import AutoProcessor, AutoTokenizer, CLIPModel, CLIPVisionModel, CLIPVisionModelWithProjection
from transformers import AutoImageProcessor, AutoModel
from transformers import ViTImageProcessor, ViTModel
import torch.nn.functional as F

parser = argparse.ArgumentParser()
parser.add_argument("--jsonfile", required=True, help="json file containing list of names to infer on")
parser.add_argument("--results-dir", required=True, help="directory pointing resulting images")
parser.add_argument("--output_dir", required=True, help="directory pointing resulting images")
parser.add_argument("--method", required=True, help="which sota methods are being used")
parser.add_argument("--benchmark", required=True, help="which benchmark is used for evaluation")
parser.add_argument("--n-chunks", type=int, required=True, help="which sota methods are being used")
parser.add_argument("--chunk-id", type=int, required=True, help="which benchmark is used for evaluation")
parser.add_argument("--data_root", default="", help="root for relative image paths in --jsonfile (e.g. benchmark/)")
args = parser.parse_args()

device = "cuda"

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

def transform_for_lpips(image):
    img = image.convert("RGB") # Ensure 3 channels
    img = img.resize((256,256))
    # Define transform: Resize (optional), ToTensor, Normalize to [-1, 1]
    transform = transforms.Compose([
        transforms.ToTensor(),  # Converts to [0, 1] and shape (C, H, W)
        transforms.Normalize(mean=[0.5, 0.5, 0.5], std=[0.5, 0.5, 0.5])  # Maps [0, 1] -> [-1, 1]
    ])
    # Apply transform
    img_tensor = transform(img)  # shape: (C, H, W)
    # Add batch dimension to make it (1, C, H, W)
    img_tensor = img_tensor.unsqueeze(0)

    return img_tensor

  
class CLIP_metric_text():
    def __init__(self):
        super(CLIP_metric_text, self).__init__()
        model_path = "{{MODELS_ROOT}}/clip-vit-base-patch32"
        self.model = AutoModel.from_pretrained(model_path, attn_implementation="sdpa").to(device)
        self.processor = AutoProcessor.from_pretrained(model_path, use_fast=True)
    
    def eval_metric(self, image, prompt, mask=None, tensor_input=False):
    
        labels = [prompt]
        image = image.resize((256, 256))
        inputs = self.processor(text=labels, images=image, return_tensors="pt", padding=True).to(device)
        outputs = self.model(**inputs)
        return outputs.logits_per_image.item()
  
class CLIP_metric():
    def __init__(self):
        super(CLIP_metric, self).__init__()
        self.model = CLIPModel.from_pretrained("{{MODELS_ROOT}}/clip-vit-large-patch14")
        self.processor = AutoProcessor.from_pretrained("{{MODELS_ROOT}}/clip-vit-large-patch14", use_fast=True)
        path_to_aes_model = "{{MODELS_ROOT}}/aes-predictor/sa_0_4_vit_l_14_linear.pth"
        self.m = nn.Linear(768, 1).to(device)
        s = torch.load(path_to_aes_model)
        self.m.load_state_dict(s)
        self.m.eval()
        self.model = self.model.to(device)

    def image_text_similarity(self, image, prompt, mask=None, tensor_input=False):
        labels = [prompt]
        inputs = self.processor(text=labels, images=image, return_tensors="pt", padding=True).to(device)
        outputs = self.model(**inputs)
        return outputs.logits_per_image.item()
    
    def image_image_similaity(self, pred, target, mask=None, tensor_input=False):
        
        pred = pred.convert("RGB")
        target = target.convert("RGB")
        
        pred = self.processor(images=pred, return_tensors="pt")
        pred = pred.to(device)
        target = self.processor(images=target, return_tensors="pt")
        target = target.to(device)

        pred_features = self.model.get_image_features(**pred)
        target_features = self.model.get_image_features(**target)
        score = torch.cosine_similarity(pred_features, target_features, dim=-1).mean()
        return score.item() 
    
    def get_aes_score(self, image):
        pred = image.convert("RGB")
        
        pred = self.processor(images=pred, return_tensors="pt")
        pred = pred.to(device)

        pred_features = self.model.get_image_features(**pred)
        
        return self.m(pred_features).item()

clip_image = CLIP_metric()

os.makedirs(args.output_dir,exist_ok=True)
# read json..
valid_info = json.load(open(args.jsonfile))
for info in valid_info:  # benchmark JSONs store paths relative to the benchmark root
    for k in ("ref_image", "ref_mask", "background_image", "background_mask"):
        if k in info and not osp.isabs(info[k]):
            info[k] = osp.join(args.data_root, info[k])

method = args.method

# track no of missing file list
missing_list_files = []


def edit_strength(img1, img2):
    diff = np.abs(np.asarray(img1.resize((256, 256))).astype(np.float32)/255.0 - np.asarray(img2.resize((256, 256))).astype(np.float32)/255.0).mean(axis=2)
    diff_u8 = (diff*255).astype(np.uint8)
    # _, thr =  cv2.threshold(diff_u8, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    mask = diff_u8 > 20
    return round(mask.mean().item(), 2)


for info in tqdm(valid_info, desc='files'):
    id = info['id']

    if id % args.n_chunks != args.chunk_id:
        continue
    org_img = Image.open(info['background_image']).convert("RGB")
     
    fg_img_path = info["ref_image"]
    fg_img = Image.open(fg_img_path)

    fg_mask_path = info['ref_mask']
    fg_mask = Image.open(fg_mask_path)

    fg_mask_bbox = get_bbox(fg_mask)
    fg_img_cropped = get_cropped_image(fg_img, fg_mask_bbox)

    json_out_name = osp.join(args.output_dir, f"{method}.{args.chunk_id}.jsonl")

    bg_img_path = os.path.join(args.results_dir, f"{str(id)}.png")
    # bg_img_path = os.path.join(args.results_dir, args.benchmark, f"{str(id)}.png")
    if not os.path.isfile(bg_img_path):
        # TODO: How do we know if we are missing any?
        missing_list_files.append(info)
        continue
    
    try:
        bg_img = Image.open(bg_img_path)
    except:
        continue
    bg_mask_path = info["background_mask"]
    bg_mask = Image.open(bg_mask_path).resize(bg_img.size, Image.NEAREST)

    bg_mask_bbox = get_bbox(bg_mask)
    bg_img_cropped = get_cropped_image(bg_img, bg_mask_bbox)


    # get bbox on org image..
    org_img = org_img.resize(bg_img.size)
    org_img_cropped = get_cropped_image(org_img, bg_mask_bbox)
    

    # calculate metric
    # prompt = ' '.join(info['background_image'].split('/')[-2].split('_')[1:]).strip()
    # print("prompt", prompt)
    if info['prompt']:
        print("prompt", f"a picture of a {info['prompt']}.")
        score_clipt = clip_image.image_text_similarity(bg_img_cropped, info['prompt'])
    else:
        score_clipt = None
    score_clipi = clip_image.image_image_similaity(bg_img_cropped, fg_img_cropped)
    score_aes = clip_image.get_aes_score(bg_img)
    
    
    ans = {
        'id': id,
        'clip-i': score_clipi,
        'aes': score_aes,
        "clip-t": score_clipt,
        "strength": edit_strength(bg_img_cropped, org_img_cropped)
    }
    # edit strength

    print(ans)
    with open(json_out_name,"a+") as op:
        op.write(json.dumps(ans) + "\n")
            
print(f"Missing files for method {args.method} are {len(missing_list_files)}")