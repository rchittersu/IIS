# Insert In Style Bench

788 curated subject–background pairs over 51 stylized backgrounds and 25 subjects.

This folder holds only our own files: the pair JSONs, all masks and the 18 Gemini-generated images. The other 57 images are third-party and are fetched from their sources, so the benchmark is complete only after step 2.

### Getting the images

1. Request Human-Art access at https://github.com/IDEA-Research/HumanArt and unpack it (19 backgrounds come from it).
2. Fetch and rebuild the rest (WikiArt, Kaggle and DreamBooth images download without a login):

   ```bash
   python benchmark/retrieve_images.py --humanart_root /path/to/HumanArt
   ```

   Images are written into `benchmark/` at the paths the pair JSONs use (they are git-ignored). Each one is cropped and resized exactly as we used it and checked against [`image_sources.csv`](image_sources.csv): md5 for files used as-is, a perceptual hash for crops. The script prints one line per image and exits non-zero if anything is missing or differs. Rerunning skips files that already exist.

Layout (paths in the JSONs are relative to `benchmark/`):

```
set1/  set2/  set3/            stylized backgrounds, e.g. set1/cartoon/000000000662.jpg
       <style>_masks/          insertion-region masks, e.g. set1/cartoon_masks/000000000662_mask.png
selected_subjects/             subject images + masks, e.g. apple.png, apple_mask.png
```

| File | Contents |
|---|---|
| `insert_in_style_bench_788.json` | `id`, `background_image`, `background_mask`, `ref_image`, `ref_mask`, `prompt` (paths relative to `benchmark/`) |
| `insert_in_style_bench_788_with_location.json` | same pairs plus location prompts |

## Image sources

- **Backgrounds (51):** 19 Human-Art, 17 WikiArt, 12 from four Kaggle style datasets, 2 generated with Gemini, and 1 web image (`set2/images/WEB_003.jpg`) that is not distributed.
- **Foregrounds (25):** 16 generated with Gemini 2.5 and 9 cut out of DreamBooth photos.

[`SOURCES.md`](SOURCES.md) has the summary with licences, [`IMAGES.md`](IMAGES.md) the per-image table, and [`sources.bib`](sources.bib) the BibTeX. If you use the benchmark, please cite these sources as well as our paper.

`inference/infer.sh` and `eval/run.sh` use the benchmark name `iisbench`.
