# Data generation

How the 115k training set in `data/stylized_final_115k` was built (paper Sec. 3), and how to rebuild its images. Paths come from `configs/paths.env`.

1. **Base triplets.** We start from the [DreamFuse](https://huggingface.co/datasets/LL3RD/DreamFuse) release (`DREAMFUSE_ROOT`, images under `extracted_data/`). Triplets with bad subject boxes, low CLIP scores or unwanted classes were removed. GroundingDINO subject boxes and prompts are already stored in every released row, so this step doesn't need rerunning.
2. **Stylization.** Each composite was restyled with FLUX.1-Kontext-dev + 19 style LoRAs, and with CSGO / CAST using Style30K references (~350k images).
3. **Filtering.** Every stylized pair was scored for identity (CLIP, DINOv2 on the subject crop) and style (CSD on the background), then filtered iteratively: each round, per style, drops rows below the 10th percentile on any score. Iteration 4 is the released set.

| File | What it does |
|---|---|
| `regenerate_stylized.py` | rebuilds the Kontext-stylized images of the 115k set (below) |
| `score_identity.py` | `clip_sim` / `dino_sim`: subject crop in the composite vs. in its stylized version |
| `../eval/CSD/csd_clip_infer.py` | `csd_sim`: CSD style similarity with the subject box filled by background patches |
| `iterative_filter.py` | the iterative decile filter |
| `iteration_thresholds.csv` | per-style row counts and percentile thresholds for every iteration |

## Regenerating the stylized images

The stylized images are not released. Each row of `data/stylized_final_115k` gives the DreamFuse triplet (`id`) and the style; the image paths follow from them (see `data/README.md`).

| Source | Rows | How to get the images |
|---|---|---|
| Kontext, 19 styles | 90,480 | `regenerate_stylized.py` |
| CSGO (`style: CSGO`) | 12,269 | official [CSGO](https://github.com/instantX-research/CSGO) code with the Style30K reference in `style_ref` |
| CAST (`style: CAST`) | 12,186 | official [CAST](https://github.com/zyxElsa/CAST_pytorch) code with the Style30K reference in `style_ref` |

For CSGO / CAST rows, `style_ref` (`sNNNN`) names the Style30K style reference used; the IDs follow Style30K's own style and file naming, so the reference image can be looked up directly in the Style30K dataset.

1. Get FLUX.1-Kontext-dev. The script downloads the style LoRAs from Hugging Face:
   - 16 styles from [Owen777/Kontext-Style-Loras](https://huggingface.co/Owen777/Kontext-Style-Loras).
   - Watercolor, Mosaic_Art and Impressionist from fal: [Watercolor](https://huggingface.co/fal/Watercolor-Art-Kontext-Dev-LoRA), [Mosaic](https://huggingface.co/fal/Mosaic-Art-Kontext-Dev-LoRA), [Impressionist](https://huggingface.co/fal/Impressionist-Art-Kontext-Dev-LoRA). These use ComfyUI key names; the script converts them (`fal_to_peft`).
   - Check each LoRA's licence on its model page. To use local copies, pass `--lora_dir` with `<Style>/pytorch_lora_weights.safetensors`.
2. Set `DREAMFUSE_ROOT`, `STYLIZED_ROOT` and `MODELS_ROOT` in `configs/paths.env`.
3. Run it. It uses the paper's settings (1024 px, 24 steps, guidance 1.0, LoRA scale 1.0, prompt "Convert the image to {style} style while maintaining the exact original composition and placement"), writes to `$STYLIZED_ROOT/kontext/<Style>/<id>_2.jpg` and skips existing images:

```bash
python data_generation/regenerate_stylized.py data/stylized_final_115k --dry_run   # counts per style
for i in 0 1 2 3; do
  CUDA_VISIBLE_DEVICES=$i python data_generation/regenerate_stylized.py data/stylized_final_115k \
      --n_chunks 4 --chunk_id $i &
done
```

4. Optional: to apply the same quality bar to your regenerated images, re-score with `score_identity.py` and `csd_clip_infer.py`, and remove rows below the iteration-4 thresholds in `iteration_thresholds.csv`.

Without CSGO / CAST you can use the 90k Kontext rows only: `python tools/localize_jsonl.py data/stylized_final_115k out/style_jsons_final --drop_missing` leaves out rows whose images are missing.

## Using the data files

To expand the data files into rows with absolute local image paths:

```bash
python tools/localize_jsonl.py data/stylized_final_115k out/style_jsons_final
```
