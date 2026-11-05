# Insert In Style

**A Zero-Shot Generative Framework for Harmonious Cross-Domain Object Composition** (ACM Multimedia 2026)

Raghu Vamsi Chittersu, Yuvraj Singh Rathore, Pranav Adlinge, Eswar Sai Pashaula, Kunal Swami

[Paper](https://arxiv.org/abs/2511.15197) · [Project page](https://rchittersu.github.io/IIS/) · Checkpoint (coming soon)

Given a reference object, a stylized scene and a mask, *Insert In Style* generates the object in the scene's style while keeping its identity, with no per-subject finetuning.

## What's included

| Folder | Contents |
|---|---|
| `inference/` | inference code for FLUX.1-dev with the three Insert In Style adapters |
| `data/` | the 115k training set as compact annotation files (`.jsonl.gz`) |
| `data_generation/` | stylization, scoring and iterative filtering used to build the training set |
| `benchmark/` | Insert In Style Bench: 788 pairs, masks, and a script that fetches the source images |
| `eval/` | CLIP-I, CSD and aesthetics metrics |
| `tools/` | path setup and data-row helpers |
| `docs/` | project page |

## Setup

```bash
conda create -n insertinstyle python=3.10 -y
conda activate insertinstyle
pip install -r inference/requirements.txt
```

1. Download the base models into one folder (`MODELS_ROOT`): [FLUX.1-dev](https://huggingface.co/black-forest-labs/FLUX.1-dev), and for evaluation `clip-vit-large-patch14`, `dinov2-large`, `CSD-ViT-L` and the LAION aesthetic predictor (`aes-predictor/`). For data generation, also FLUX.1-Kontext-dev.
2. Download the checkpoint (Google Drive link coming soon) into `inference/checkpoints/`. It contains `subject.safetensors`, `token_integration.safetensors` and `instyle.safetensors` (332 MB).
3. Set your local paths in `configs/paths.env` and apply them:
   ```bash
   python tools/set_paths.py           # fill the path placeholders in the scripts
   python tools/set_paths.py --check   # list placeholders that are still unset
   ```

## Quick start

```bash
# 1. complete the benchmark images (see benchmark/README.md)
python benchmark/retrieve_images.py --humanart_root /path/to/HumanArt
# 2. generate (here split over 4 GPUs)
for i in 0 1 2 3; do bash inference/infer.sh $i iisbench 4 $i & done; wait
# 3. evaluate
for i in 0 1 2 3; do bash eval/run.sh $i iisbench ours 4 $i & done; wait
python eval/get_means.py eval/scores/iisbench
```

Results are written to `inference/generations/iisbench/<id>.png` and scores to `eval/scores/iisbench/`. To run on your own images, see `inference/README.md`.

## Training data

`data/stylized_final_115k/` lists the 114,935 training samples: the DreamFuse triplet, the style, subject boxes and the filter scores. See `data/README.md` for the format. Images are not redistributed:

- DreamFuse images come from the [DreamFuse](https://huggingface.co/datasets/LL3RD/DreamFuse) release.
- The 90k Kontext-stylized images can be regenerated with `data_generation/regenerate_stylized.py`.
- The CSGO / CAST samples list their Style30K style reference and can be regenerated with the official [CSGO](https://github.com/instantX-research/CSGO) and [CAST](https://github.com/zyxElsa/CAST_pytorch) code.

See `data_generation/README.md` for details.

## Citation

```bibtex
@inproceedings{chittersu2026insertinstyle,
  title     = {Insert In Style: A Zero-Shot Generative Framework for
               Harmonious Cross-Domain Object Composition},
  author    = {Chittersu, Raghu Vamsi and Rathore, Yuvraj Singh and
               Adlinge, Pranav and Pashaula, Eswar Sai and Swami, Kunal},
  booktitle = {Proceedings of the 34th ACM International Conference on Multimedia},
  year      = {2026}
}
```

If you use the benchmark, please also cite its image sources (`benchmark/sources.bib`).

## Acknowledgements

The inference code builds on [OminiControl](https://github.com/Yuanshi9815/OminiControl), and the style metric on [CSD](https://github.com/learn2phoenix/CSD). The training data builds on [DreamFuse](https://huggingface.co/datasets/LL3RD/DreamFuse) and Style30K.
