# Evaluation

Paper metrics: **CLIP-I** (subject identity), **CSD** (style consistency with the background) and **aesthetics**.

```bash
bash eval/run.sh <gpu> <benchmark> <method> [n_chunks=1] [chunk_id=0]
#   reads <results_dir>/<id>.png: inference/generations/<benchmark> for method=ours,
#   otherwise RESULTS_DIR=/folder/with/<id>.png
#   SKIP_CSD=1 skips the CSD pass
python eval/get_means.py eval/scores/<benchmark>
```

`run.sh` runs two scorers:

| Script | Scores | Output |
|---|---|---|
| `metrics_v2.py` | `clip-i` (subject crop vs. reference crop), `clip-t`, `aes` (LAION aesthetic predictor), `strength` (edit strength vs. the original background) | `scores/<benchmark>/<method>.<chunk>.jsonl` |
| `CSD/csd_infer.py` | CSD style similarity between result and background (`{{MODELS_ROOT}}/CSD-ViT-L`). No chunking, so only chunk 0 runs it | `scores/<benchmark>/csd/` |

`CSD/` is adapted from https://github.com/learn2phoenix/CSD (commit 3a9df32), with our `csd_infer.py` (benchmark scoring) and `csd_clip_infer.py` (the `csd_sim` score used to filter the training data).

Model weights needed in `MODELS_ROOT`: `clip-vit-large-patch14`, `aes-predictor/sa_0_4_vit_l_14_linear.pth`, `CSD-ViT-L/pytorch_model.bin`.
