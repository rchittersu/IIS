#!/usr/bin/env python3
"""Regenerate the Kontext-stylized images listed in the released filtered set.

The stylized images are not distributed. The filtered annotation files in data/ list,
for every kept pair, which DreamFuse composite was stylized and with which style, so the
Kontext part (19 styles, ~90k images) can be regenerated with the settings used in the paper:

    FLUX.1-Kontext-dev + style LoRA (scale 1.0), 1024x1024, 24 steps, guidance 1.0,
    prompt "Convert the image to {style} style while maintaining the exact original
    composition and placement"

Each image is written to $STYLIZED_ROOT/kontext/<Style>/<id>_2.jpg, the path tools/rows.py
expects, so tools/localize_jsonl.py works on the result unchanged.

CSGO / CAST rows are skipped; see data_generation/README.md.

Example (4 GPUs):
    for i in 0 1 2 3; do
      CUDA_VISIBLE_DEVICES=$i python data_generation/regenerate_stylized.py \
          data/stylized_final_115k --n_chunks 4 --chunk_id $i &
    done

Style LoRAs are downloaded from Hugging Face (see LORA_SOURCES):
  * 16 styles from Owen777/Kontext-Style-Loras
  * Watercolor, Mosaic_Art, Impressionist from fal/*-Art-Kontext-Dev-LoRA. These ship in
    ComfyUI key format and are converted to the PEFT key layout we used (fal_to_peft).
To use local copies instead, pass --lora_dir with <Style>/pytorch_lora_weights.safetensors.
"""
import argparse
import os
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "tools"))
from rows import KONTEXT_FREE, paths, read_rows  # noqa: E402
from set_paths import load_env  # noqa: E402

# style folder name -> (HF repo, file, key format)
_OWEN = "Owen777/Kontext-Style-Loras"
LORA_SOURCES = {
    **{s: (_OWEN, f"{s}_lora_weights.safetensors", "diffusers") for s in (
        "American_Cartoon", "Chinese_Ink", "Fabric", "Ghibli", "Irasutoya", "LEGO", "Line", "Oil_Painting",
        "Origami", "Paper_Cutting", "Picasso", "Pixel", "Poly", "Rick_Morty", "Van_Gogh", "Vector")},
    "Watercolor": ("fal/Watercolor-Art-Kontext-Dev-LoRA",
                   "EAA_1Pfw0sBAvtBbv401y_8a8c4091e9ae45869b469bec4a0d8446_adapter_model_comfy_converted.safetensors", "fal"),
    "Mosaic_Art": ("fal/Mosaic-Art-Kontext-Dev-LoRA",
                   "g_IGTyyzfC27UT9AVlt-v_adapter_model_comfy_converted.safetensors", "fal"),
    "Impressionist": ("fal/Impressionist-Art-Kontext-Dev-LoRA",
                      "5SX6j2wcLJKgudBqlmver_adapter_model_comfy_converted.safetensors", "fal"),
}


def fal_to_peft(sd):
    """ComfyUI keys (lora_unet_double_blocks_0_img_attn_qkv.lora_down.weight) ->
    base_model.model.double_blocks.0.img_attn.qkv.lora_A.weight, as done for the paper."""
    out = {}
    for k, v in sd.items():
        k2 = k.replace("lora_unet_", "base_model.model.")
        new, n = "", 0
        for ch in k2:
            if ch != "_":
                new += ch
            else:
                new += "." if n in (2, 3, 5) else "_"
                n += 1
        for a, b in (("modulation_lin", "modulation.lin"), ("lora_down", "lora_A"), ("lora.down", "lora_A"),
                     ("lora_up", "lora_B"), ("lora.up", "lora_B")):
            new = new.replace(a, b)
        out[new] = v
    return out


def load_style_lora(pipe, style, lora_dir=None):
    local = os.path.join(lora_dir, style, "pytorch_lora_weights.safetensors") if lora_dir else None
    if local and os.path.exists(local):
        pipe.load_lora_weights(os.path.dirname(local), weight_name="pytorch_lora_weights.safetensors", adapter_name="style")
        return
    if style not in LORA_SOURCES:
        sys.exit(f"no LoRA source for style {style}")
    from huggingface_hub import hf_hub_download
    repo, fname, kind = LORA_SOURCES[style]
    path = hf_hub_download(repo, fname)
    if kind == "fal":
        from safetensors.torch import load_file
        pipe.load_lora_weights(fal_to_peft(load_file(path)), adapter_name="style")
    else:
        pipe.load_lora_weights(os.path.dirname(path), weight_name=fname, adapter_name="style")


PROMPT = "Convert the image to {style} style while maintaining the exact original composition and placement"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help="filtered .jsonl file or folder, e.g. data/stylized_final_115k")
    ap.add_argument("--lora_dir", default=None, help="optional local LoRAs (<Style>/pytorch_lora_weights.safetensors); default: download")
    ap.add_argument("--kontext", default=None, help="FLUX.1-Kontext-dev path or HF id (default: $MODELS_ROOT/FLUX.1-Kontext-dev)")
    ap.add_argument("--env", default=os.path.join(REPO, "configs", "paths.env"))
    ap.add_argument("--styles", nargs="*", help="only these styles (folder names, e.g. Ghibli LEGO)")
    ap.add_argument("--n_chunks", type=int, default=1)
    ap.add_argument("--chunk_id", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0, help="base seed; row i uses seed+i so reruns are reproducible")
    ap.add_argument("--dry_run", action="store_true", help="only print what would be generated")
    a = ap.parse_args()

    env = load_env(a.env)
    df_img = os.path.join(env["DREAMFUSE_ROOT"], "extracted_data")
    out_root = env["STYLIZED_ROOT"]

    # unique (style, composed) jobs; the same composite can appear in several style files
    jobs, skipped = {}, defaultdict(int)
    for e in read_rows(a.src):
        style = e["style"]
        if style in KONTEXT_FREE:
            skipped[style] += 1
            continue
        if a.styles and style not in a.styles:
            continue
        p = paths(e)
        jobs[p["stylised"]] = (style, p["composed"])
    jobs = sorted(jobs.items())
    mine = [(i, j) for i, j in enumerate(jobs) if i % a.n_chunks == a.chunk_id]
    todo = [(i, j) for i, j in mine if not os.path.exists(os.path.join(out_root, j[0]))]
    by_style = defaultdict(list)
    for i, (rel, (style, composed)) in todo:
        by_style[style].append((i, rel, composed))

    print(f"{len(jobs)} Kontext images in total, {len(mine)} in chunk {a.chunk_id}/{a.n_chunks}, {len(todo)} still to do")
    for k, v in skipped.items():
        print(f"skipped {v} {k} rows (not Kontext)")
    if a.dry_run or not todo:
        for s, v in sorted(by_style.items()):
            print(f"  {s}: {len(v)}")
        return

    import torch
    from diffusers import FluxKontextPipeline
    from diffusers.utils import load_image
    from tqdm import tqdm

    pipe = FluxKontextPipeline.from_pretrained(
        a.kontext or os.path.join(env["MODELS_ROOT"], "FLUX.1-Kontext-dev"), torch_dtype=torch.bfloat16
    ).to("cuda")

    for style, items in sorted(by_style.items()):
        pipe.unload_lora_weights()
        load_style_lora(pipe, style, a.lora_dir)
        pipe.set_adapters(["style"], adapter_weights=[1.0])
        prompt = PROMPT.format(style=style.replace("_", " "))
        for i, rel, composed in tqdm(items, desc=style):
            out = os.path.join(out_root, rel)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            img = pipe(
                image=load_image(os.path.join(df_img, composed)),
                prompt=prompt,
                height=1024,
                width=1024,
                num_inference_steps=24,
                guidance_scale=1.0,
                generator=torch.Generator("cuda").manual_seed(a.seed + i),
            ).images[0]
            img.save(out)


if __name__ == "__main__":
    main()
