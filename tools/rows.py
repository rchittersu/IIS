"""Read the released data files and rebuild the image paths of a row.

A row is {"id", "style", ["style_ref"], ["mask_ext"], "prompt", "bbox", "bbox_stylised",
"clip_sim", "dino_sim", "csd_sim"}. `id` is the DreamFuse triplet stem; boxes are normalised cxcywh.
"""
import glob
import gzip
import json
import os

KONTEXT_FREE = {"CSGO": "csgo", "CAST": "cast"}  # styles not made with Kontext LoRAs


def paths(r):
    """Image paths of a row: DreamFuse ones relative to $DREAMFUSE_ROOT/extracted_data,
    `stylised` relative to $STYLIZED_ROOT."""
    i = r["id"]
    if r["style"] in KONTEXT_FREE:
        stylised = f"{KONTEXT_FREE[r['style']]}/{i}_2_sty_{r['style_ref']}.png"
    else:
        stylised = f"kontext/{r['style']}/{i}_2.jpg"
    return {
        "instance": f"{i}_0.jpg",                                 # subject reference
        "instance_mask": f"{i}_0_mask.{r.get('mask_ext', 'png')}",
        "scene": f"{i}_1.jpg",                                    # empty background
        "composed": f"{i}_2.jpg",                                 # DreamFuse composite (realistic)
        "stylised": stylised,                                     # stylized composite
    }


def list_files(src):
    """A .jsonl / .jsonl.gz file, or every such file in a folder."""
    if os.path.isfile(src):
        return [src]
    return sorted(glob.glob(os.path.join(src, "*.jsonl.gz")) + glob.glob(os.path.join(src, "*.jsonl")))


def stem(f):
    """File name without .jsonl / .jsonl.gz, e.g. 'ghibli'."""
    return os.path.basename(f).removesuffix(".gz").removesuffix(".jsonl")


def read_rows(src):
    """Rows of one .jsonl(.gz) file or of every such file in a folder."""
    for f in list_files(src):
        with (gzip.open if f.endswith(".gz") else open)(f, "rt", encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    yield json.loads(line)
