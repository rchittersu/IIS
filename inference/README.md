# Inference

FLUX.1-dev with the three Insert In Style LoRA adapters, all active at generation time (built on [OminiControl](https://github.com/Yuanshi9815/OminiControl), Apache-2.0, see `LICENSE`):

| Adapter | Role |
|---|---|
| `subject` | identity branch: encodes the reference subject |
| `token_integration` | style branch: conditions on the scene outside the insertion region |
| `instyle` | composition: inserts the subject in the scene's style |

```
infer.py / infer.sh    generate for a benchmark or any pair JSON
checkpoints/           the paper's three adapters (subject / token_integration / instyle .safetensors),
                       downloaded from Google Drive (link in the top-level README)
omini/pipeline/        the multi-condition FLUX pipeline
```

## Usage

```bash
bash inference/infer.sh <gpu> <benchmark> [n_chunks=1] [chunk_id=0] [out_dir]
#   benchmark: iisbench | aicomposer | anydoor | subjectplop | tficon
#   env: CKPT (adapter folder, default checkpoints/), IMG_GUIDE (default 1.5)
```

Outputs go to `inference/generations/<benchmark>/<id>.png`, which is where `eval/run.sh` looks. For your own pairs, call `infer.py` directly:

```bash
python inference/infer.py --json pairs.json --data_root <root> --out <out_dir>
```

`pairs.json` is a list of `{id, background_image, background_mask, ref_image, ref_mask}`. The background mask marks the insertion region, and the ref mask cuts out the subject. Settings follow the paper: 768 px on the long side, 20 steps, image guidance 1.5, seed 0.
