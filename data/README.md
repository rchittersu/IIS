# Data files

The Insert In Style training set: 114,935 rows, one `.jsonl` per style in `stylized_final_115k/` (output of iteration 4 of the iterative filter). These are annotation files only and contain no images. DreamFuse images come from the [DreamFuse](https://huggingface.co/datasets/LL3RD/DreamFuse) release. To rebuild the stylized images, see `data_generation/README.md`.

```json
{"id": "data_animal/icp_v2_model_2_animal_2_flux/subj_000000036", "style": "Ghibli", "prompt": "A toy owl.",
 "bbox": [0.48, 0.598, 0.384, 0.563], "bbox_stylised": [0.477, 0.569, 0.377, 0.571],
 "clip_sim": 0.754, "dino_sim": 0.608, "csd_sim": 0.509}
```

| Field | Meaning |
|---|---|
| `id` | DreamFuse triplet, relative to `$DREAMFUSE_ROOT/extracted_data` |
| `style` | one of 19 Kontext LoRA styles (e.g. `Ghibli`), or `CSGO` / `CAST` |
| `style_ref` | CSGO / CAST only: the Style30K style reference (`sNNNN`, Style30K's own naming) |
| `mask_ext` | only when the subject mask is not `.png` |
| `prompt` | short subject caption |
| `bbox`, `bbox_stylised` | subject box (GroundingDINO, normalised cx, cy, w, h) in the composite and in the stylized image |
| `clip_sim`, `dino_sim`, `csd_sim` | filter scores (subject identity: CLIP, DINOv2; background style: CSD) |

Image paths follow from `id` (`tools/rows.py`):

| Image | Path |
|---|---|
| subject, subject mask | `<id>_0.jpg`, `<id>_0_mask.png` |
| empty scene | `<id>_1.jpg` |
| composite | `<id>_2.jpg` |
| stylized composite (Kontext) | `$STYLIZED_ROOT/kontext/<style>/<id>_2.jpg` |
| stylized composite (CSGO / CAST) | `$STYLIZED_ROOT/{csgo,cast}/<id>_2_sty_<style_ref>.png` |

To get rows with absolute image paths:

```bash
python tools/localize_jsonl.py data/stylized_final_115k out/style_jsons_final                 # paths from configs/paths.env
python tools/localize_jsonl.py data/stylized_final_115k out/style_jsons_final --drop_missing  # skip rows whose images are missing
```
