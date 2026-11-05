#!/usr/bin/env python3
"""Insert In Style inference: FLUX.1-dev with the subject, token_integration and instyle LoRAs.

    python infer.py --json ../benchmark/insert_in_style_bench_788.json --data_root ../benchmark --out generations/iisbench

The JSON is a list of {id, background_image, background_mask, ref_image, ref_mask}; relative paths are
joined to --data_root. Writes <out>/<id>.png and skips ids that already exist. Settings as in the paper:
768 px (long side), 20 steps, image guidance 1.5, seed 0.
"""
import argparse
import json
import math
import os

import torch
from diffusers.pipelines import FluxPipeline
from PIL import Image
from tqdm import tqdm

from omini.pipeline.flux_omini import Condition, generate, seed_everything

HERE = os.path.dirname(os.path.abspath(__file__))
ADAPTERS = ("subject", "token_integration", "instyle")


def subject_canvas(image, mask, size=768):
    """Cut the subject out with its mask, centre it on white, longest side = 80% of the canvas."""
    mask = mask.resize(image.size, Image.NEAREST).convert("L").point(lambda x: 255 if x > 127 else 0)
    box = mask.getbbox()
    image, mask = image.convert("RGB").crop(box), mask.crop(box)
    image = Image.composite(image, Image.new("RGB", image.size, "white"), mask)
    r = int(size * 0.8) / max(image.size)
    image = image.resize((int(image.width * r), int(image.height * r)))
    canvas = Image.new("RGB", (size, size), "white")
    canvas.paste(image, (size // 2 - image.width // 2, size // 2 - image.height // 2))
    return canvas


def scene_and_masks(scene, mask, long_side=768):
    """Resize the scene so the long side is 768 and both sides are multiples of 16; the insertion
    region (mask bbox, in 16-px latent cells) is what gets generated."""
    w, h = scene.size
    if w >= h:
        W, H = long_side, int(long_side // (w / h) // 16) * 16
    else:
        H = long_side
        W = int(H * w / h) - int(H * w / h) % 16
    scene = scene.convert("RGB").resize((W, H), Image.LANCZOS)
    x0, y0, x1, y1 = (math.ceil(v / 16) for v in mask.convert("L").resize((W, H), Image.NEAREST).getbbox())
    cond_mask = torch.ones((W // 16, H // 16), dtype=bool)
    cond_mask[x0:x1, y0:y1] = False
    return scene, cond_mask, W, H


def load_pipe(flux, ckpt_dir):
    pipe = FluxPipeline.from_pretrained(flux, torch_dtype=torch.bfloat16).to("cuda")
    for name in ADAPTERS:
        pipe.load_lora_weights(ckpt_dir, weight_name=f"{name}.safetensors", adapter_name=name)
    pipe.set_adapters(list(ADAPTERS))
    return pipe


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", required=True)
    ap.add_argument("--data_root", default="", help="root for relative paths in --json")
    ap.add_argument("--out", required=True)
    ap.add_argument("--ckpt", default=os.path.join(HERE, "checkpoints"), help="folder with the three adapter .safetensors")
    ap.add_argument("--flux", default="{{MODELS_ROOT}}/FLUX.1-dev")
    ap.add_argument("--img_guidance", type=float, default=1.5)
    ap.add_argument("--steps", type=int, default=20)
    ap.add_argument("--n_chunks", type=int, default=1)
    ap.add_argument("--chunk_id", type=int, default=0)
    a = ap.parse_args()

    items = [e for e in json.load(open(a.json)) if e["id"] % a.n_chunks == a.chunk_id]
    path = lambda p: p if os.path.isabs(p) else os.path.join(a.data_root, p)
    os.makedirs(a.out, exist_ok=True)
    todo = [e for e in items if not os.path.exists(os.path.join(a.out, f"{e['id']}.png"))]
    print(f"{len(items)} items in chunk {a.chunk_id}/{a.n_chunks}, {len(todo)} to generate")
    if not todo:
        return
    pipe = load_pipe(a.flux, a.ckpt)

    for e in tqdm(todo):
        ref = subject_canvas(Image.open(path(e["ref_image"])), Image.open(path(e["ref_mask"])))
        scene, cond_mask, W, H = scene_and_masks(Image.open(path(e["background_image"])), Image.open(path(e["background_mask"])))
        seed_everything(0)
        result = generate(
            pipe,
            prompt="this",
            conditions=[
                Condition(ref, "subject", position_delta=(0, -48)),
                Condition(scene, "token_integration", latent_mask=cond_mask, is_complement=True),
            ],
            image_guidance_scale=[a.img_guidance, 1.0],
            num_inference_steps=a.steps,
            height=H,
            width=W,
            latent_mask=torch.logical_not(cond_mask),
            main_adapter="instyle",
            all_condition_attention=False,
        ).images[0]
        result.save(os.path.join(a.out, f"{e['id']}.png"))


if __name__ == "__main__":
    main()
