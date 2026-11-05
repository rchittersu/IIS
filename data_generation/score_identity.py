#!/usr/bin/env python3
"""Identity scores used by the filter: CLIP and DINOv2 similarity between the subject crop in the
DreamFuse composite and the subject crop in its stylized version (boxes: bbox / bbox_stylised,
normalised cxcywh). Adds clip_sim and/or dino_sim to every row.

    python data_generation/score_identity.py data/stylized_final_115k out/scored --metrics clip dino \
        [--n_chunks 4 --chunk_id 0]

The style score (csd_sim) comes from eval/CSD/csd_clip_infer.py, which fills the subject box with
patches from the rest of the image so that only the background style is compared.
"""
import argparse
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "tools"))
from rows import list_files, paths, read_rows, stem  # noqa: E402
from set_paths import load_env  # noqa: E402


def crop(path, box):
    from PIL import Image

    im = Image.open(path).convert("RGB")
    cx, cy, w, h = box
    W, H = im.size
    return im.crop((int((cx - w / 2) * W), int((cy - h / 2) * H), int((cx + w / 2) * W), int((cy + h / 2) * H)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help=".jsonl file or folder of them, e.g. data/stylized_final_115k")
    ap.add_argument("out", help="output folder; one .jsonl per input file")
    ap.add_argument("--metrics", nargs="+", default=["clip", "dino"], choices=["clip", "dino"])
    ap.add_argument("--env", default=os.path.join(REPO, "configs", "paths.env"))
    ap.add_argument("--n_chunks", type=int, default=1)
    ap.add_argument("--chunk_id", type=int, default=0)
    a = ap.parse_args()

    import torch
    import torch.nn.functional as F
    from torchvision import transforms
    from tqdm import tqdm
    from transformers import AutoModel, CLIPModel, CLIPProcessor

    env = load_env(a.env)
    df_root = os.path.join(env["DREAMFUSE_ROOT"], "extracted_data")
    st_root = env["STYLIZED_ROOT"]
    dev = "cuda" if torch.cuda.is_available() else "cpu"

    scorers = {}
    if "clip" in a.metrics:
        name = os.path.join(env["MODELS_ROOT"], "clip-vit-large-patch14")
        m, p = CLIPModel.from_pretrained(name).to(dev).eval(), CLIPProcessor.from_pretrained(name)
        scorers["clip_sim"] = lambda im: m.get_image_features(**p(images=im, return_tensors="pt").to(dev))
    if "dino" in a.metrics:
        d = AutoModel.from_pretrained(os.path.join(env["MODELS_ROOT"], "dinov2-large")).to(dev).eval()
        tf = transforms.Compose([transforms.Resize(224), transforms.CenterCrop(224), transforms.ToTensor(),
                                 transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])
        scorers["dino_sim"] = lambda im: d(tf(im).unsqueeze(0).to(dev)).last_hidden_state[:, 0, :]

    files = list_files(a.src)
    os.makedirs(a.out, exist_ok=True)
    for f in files:
        rows = list(read_rows(f))[a.chunk_id::a.n_chunks]
        name = stem(f) + ".jsonl"
        out = os.path.join(a.out, name.replace(".jsonl", f".{a.chunk_id}.jsonl" if a.n_chunks > 1 else ".jsonl"))
        with open(out, "w") as fh, torch.no_grad():
            for e in tqdm(rows, desc=name):
                p = paths(e)
                src = crop(os.path.join(df_root, p["composed"]), e["bbox"])
                sty = crop(os.path.join(st_root, p["stylised"]), e["bbox_stylised"])
                for key, emb in scorers.items():
                    e[key] = float(F.cosine_similarity(emb(src), emb(sty)).item())
                fh.write(json.dumps(e) + "\n")
        print("wrote", out)


if __name__ == "__main__":
    main()
