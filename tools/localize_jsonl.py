#!/usr/bin/env python3
"""Expand the released data files into rows with absolute local image paths.

Each output row keeps the released fields and adds instance, instance_mask, scene, composed
(under $DREAMFUSE_ROOT/extracted_data) and stylised (under $STYLIZED_ROOT); see tools/rows.py.

    python tools/localize_jsonl.py data/stylized_final_115k out/style_jsons_final
    python tools/localize_jsonl.py data/stylized_final_115k out/style_jsons_final --drop_missing

A folder gives one <style>.jsonl per input file; a single .jsonl gives one file.
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rows import list_files, paths, read_rows, stem  # noqa: E402
from set_paths import load_env  # noqa: E402

STYLIZED = ("stylised",)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src", help=".jsonl(.gz) file or folder of them")
    ap.add_argument("dst", help="output folder (or .jsonl file when src is a file)")
    ap.add_argument("--env", default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs", "paths.env"))
    ap.add_argument("--check", action="store_true", help="count rows whose images are missing")
    ap.add_argument("--drop_missing", action="store_true",
                    help="leave out rows whose images are missing (e.g. CSGO/CAST rows when only Kontext images were regenerated)")
    a = ap.parse_args()

    env = load_env(a.env)
    roots = {"df": os.path.join(env["DREAMFUSE_ROOT"], "extracted_data"), "sty": env["STYLIZED_ROOT"]}
    if os.path.isdir(a.src):
        os.makedirs(a.dst, exist_ok=True)
        jobs = [(f, os.path.join(a.dst, stem(f) + ".jsonl")) for f in list_files(a.src)]
    else:
        os.makedirs(os.path.dirname(os.path.abspath(a.dst)), exist_ok=True)
        jobs = [(a.src, a.dst)]

    total = missing = 0
    for s, d in jobs:
        with open(d, "w", encoding="utf-8") as f:
            for r in read_rows(s):
                p = {k: os.path.join(roots["sty" if k in STYLIZED else "df"], v) for k, v in paths(r).items()}
                if a.check or a.drop_missing:
                    if not all(os.path.exists(v) for v in p.values()):
                        missing += 1
                        if a.drop_missing:
                            continue
                f.write(json.dumps({**p, **r}, ensure_ascii=False) + "\n")
                total += 1
    note = f", {missing} {'dropped' if a.drop_missing else 'with missing images'}" if (a.check or a.drop_missing) else ""
    print(f"wrote {len(jobs)} file(s), {total} rows{note}")


if __name__ == "__main__":
    main()
