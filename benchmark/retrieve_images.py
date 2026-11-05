#!/usr/bin/env python3
"""Download the third-party images of Insert In Style Bench and rebuild them exactly as we used them.

Like LAION, we don't redistribute images we don't own. This folder holds only our own files
(pair JSONs, all masks, the Gemini-generated images). Every other image is listed in image_sources.csv
with its source URL, the crop box and output size we used, and a checksum. This script fetches each one
and writes it into benchmark/ at the path the pair JSONs expect (git-ignored).

    python benchmark/retrieve_images.py --humanart_root /path/to/HumanArt

Sources and what the script needs:
  * WikiArt (17), Kaggle (12), DreamBooth (9): downloaded from the URL in the csv (no login needed).
  * Human-Art (19): access-controlled. Request it at https://github.com/IDEA-Research/HumanArt, then
    pass --humanart_root (the folder that contains images/2D_virtual_human/...).
  * DreamBooth: pass --dreambooth_root (a clone of github.com/google/dreambooth) to read it locally instead.

Checks: files used as-is (Human-Art, 4 Kaggle files) must match our md5. Cropped or resized ones can't
match byte for byte because they're re-encoded, so they're checked with a 256-bit difference hash
(dhash column) instead; the Hamming distance should be small (we see 0-12 bits; >24 is reported).

Run with --out pointing at the unpacked benchmark release, so the DreamBooth masks it ships are found.
"""
import argparse
import csv
import hashlib
import io
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
UA = "InsertInStyle-benchmark-retrieval/1.0"
MAX_DHASH = 24


def dhash(im):
    """256-bit difference hash, hex. RGBA is composited on white first."""
    import numpy as np
    from PIL import Image

    if im.mode in ("RGBA", "LA", "P"):
        im = im.convert("RGBA")
        bg = Image.new("RGBA", im.size, (255, 255, 255, 255))
        im = Image.alpha_composite(bg, im)
    a = np.asarray(im.convert("L").resize((17, 16), Image.LANCZOS), dtype=np.int16)
    bits = (a[:, 1:] > a[:, :-1]).ravel()
    return "%064x" % int("".join("1" if b else "0" for b in bits), 2)


def hamming(a, b):
    return bin(int(a, 16) ^ int(b, 16)).count("1")


def fetch(url, cache):
    path = os.path.join(cache, hashlib.md5(url.encode()).hexdigest())
    if os.path.exists(path):
        return open(path, "rb").read()
    err = None
    for attempt in range(3):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60).read()
            break
        except Exception as e:  # e.g. a TLS-intercepting proxy python doesn't trust: fall back to curl
            err = e
            try:
                data = subprocess.run(["curl", "-sfL", "-A", UA, url], check=True, capture_output=True, timeout=120).stdout
                break
            except Exception as e2:
                err = e2
                time.sleep(2 * (attempt + 1))
    else:
        raise RuntimeError(f"download failed: {url}: {err}")
    with open(path + ".tmp", "wb") as fh:
        fh.write(data)
    os.replace(path + ".tmp", path)
    return data


def build(r, a):
    from PIL import Image, ImageOps

    out = os.path.join(a.out, r["file"])
    if r["source"].startswith("Gemini"):
        return "shipped" if os.path.exists(out) else "MISSING (should be in benchmark/)"
    if not r["url"] and r["source"] != "Human-Art":
        return "not distributed"
    if os.path.exists(out) and not a.overwrite:
        return check(r, out, "exists")
    os.makedirs(os.path.dirname(out), exist_ok=True)

    if r["source"] == "Human-Art":
        if not a.humanart_root:
            return "skipped (needs --humanart_root)"
        src = os.path.join(a.humanart_root, r["src_path"])
        if not os.path.exists(src):
            return f"MISSING in Human-Art: {r['src_path']}"
        shutil.copyfile(src, out)
        return check(r, out, "copied")

    if r["source"] == "DreamBooth" and a.dreambooth_root:
        data = open(os.path.join(a.dreambooth_root, r["src_path"]), "rb").read()
    else:
        data = fetch(r["url"], a.cache)

    if not r["crop_box"] and not r["alpha_from"]:  # used as-is: keep the original bytes
        with open(out, "wb") as fh:
            fh.write(data)
        return check(r, out, "downloaded")

    im = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    if r["crop_box"]:
        im = im.crop(tuple(int(v) for v in r["crop_box"].split()))
    w, h = (int(v) for v in r["out_size"].split("x"))
    if im.size != (w, h):
        im = im.resize((w, h), Image.BICUBIC)
    if r["alpha_from"]:
        mask = os.path.join(a.out, r["alpha_from"])
        if not os.path.exists(mask):
            return f"MISSING mask {r['alpha_from']} (unpack the benchmark release into --out first)"
        im.putalpha(Image.open(mask).convert("L").resize((w, h)))
    if out.lower().endswith((".jpg", ".jpeg")):
        im.save(out, quality=95)
    else:
        im.save(out)
    return check(r, out, "built")


def check(r, out, what):
    from PIL import Image

    if r["exact"] == "yes":
        ok = hashlib.md5(open(out, "rb").read()).hexdigest() == r["md5"]
        return f"{what}, md5 ok" if ok else f"{what}, MD5 MISMATCH"
    d = hamming(dhash(Image.open(out)), r["dhash"])
    return f"{what}, dhash {d}/256" + ("" if d <= MAX_DHASH else " TOO DIFFERENT")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=HERE, help="benchmark root (default: this folder)")
    ap.add_argument("--csv", default=os.path.join(HERE, "image_sources.csv"))
    ap.add_argument("--humanart_root", help="local Human-Art root (contains images/2D_virtual_human/...)")
    ap.add_argument("--dreambooth_root", help="optional local clone of github.com/google/dreambooth")
    ap.add_argument("--cache", help="download cache (default: <out>/.download_cache)")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--overwrite", action="store_true", help="rebuild files that already exist")
    a = ap.parse_args()
    a.cache = a.cache or os.path.join(a.out, ".download_cache")
    os.makedirs(a.cache, exist_ok=True)

    rows = list(csv.DictReader(open(a.csv, encoding="utf-8")))

    def run(r):
        try:
            return r, build(r, a)
        except Exception as e:
            return r, f"ERROR {e}"

    bad = 0
    with ThreadPoolExecutor(a.workers) as ex:
        for r, status in ex.map(run, rows):
            flag = any(s in status for s in ("ERROR", "MISSING", "MISMATCH", "TOO DIFFERENT"))
            bad += flag
            print(f"{'!!' if flag else 'ok'}  {r['file']:<45} {r['source']:<40} {status}")
    print(f"\n{len(rows)} images, {bad} problems")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
