#!/bin/bash
# Score generated composites: CLIP-I (subject identity), CLIP-T, aesthetics (metrics_v2.py)
# and CSD style consistency with the background (CSD/csd_infer.py). Set SKIP_CSD=1 to skip CSD.
#
# Usage:  bash eval/run.sh <gpu> <benchmark> <method> [n_chunks=1] [chunk_id=0]
#   benchmark: iisbench | aicomposer | anydoor | subjectplop | tficon   (same names as inference/infer.sh)
#   method:    ours | anydoor | aicomposer | dreamfuse | tale | tficon | <any label>
#   Results are read from <results_dir>/<id>.png:
#     ours   -> inference/generations/<benchmark>
#     others -> $RESULTS_DIR (or {{BASELINES_ROOT}}/all_results/<benchmark>_bench/<method>)
# Scores go to eval/scores/<benchmark>/<method>.<chunk_id>.jsonl and eval/scores/<benchmark>/csd/;
# summarise with get_means.py.
set -euo pipefail
cd "$(dirname "$0")"

GPU=${1:?gpu id}; BENCH=${2:?benchmark}; METHOD=${3:?method}; NCH=${4:-1}; CID=${5:-0}

case "$BENCH" in
  iisbench)    JSON=../benchmark/insert_in_style_bench_788.json; ROOT=../benchmark; BDIR=our_bench ;;
  aicomposer)  JSON={{BASELINES_ROOT}}/benchmark_jsons/ai-composer.json;  ROOT=; BDIR=aicomposer_bench ;;
  anydoor)     JSON={{BASELINES_ROOT}}/benchmark_jsons/anydoor-real.json; ROOT=; BDIR=anydoor_bench ;;
  subjectplop) JSON={{BASELINES_ROOT}}/benchmark_jsons/subjectplop.json;  ROOT=; BDIR=subjectplop_bench ;;
  tficon)      JSON={{BASELINES_ROOT}}/benchmark_jsons/tf-icon.json;      ROOT=; BDIR=tficon_bench ;;
  *) echo "unknown benchmark: $BENCH"; exit 1 ;;
esac

if [[ -n "${RESULTS_DIR:-}" ]]; then DIR=$RESULTS_DIR
elif [[ "$METHOD" == "ours" ]]; then DIR=../inference/generations/$BENCH
else DIR={{BASELINES_ROOT}}/all_results/$BDIR/$METHOD
fi

if [[ -n "${CONDA_ENV:-}" ]]; then
  source "$(conda info --base)/etc/profile.d/conda.sh"; conda activate "$CONDA_ENV"
fi

echo "gpu=$GPU bench=$BENCH method=$METHOD json=$JSON results=$DIR chunks=$CID/$NCH"
CUDA_VISIBLE_DEVICES=$GPU python3 metrics_v2.py \
    --jsonfile "$JSON" \
    --data_root "$ROOT" \
    --results-dir "$DIR" \
    --benchmark "$BENCH" \
    --output_dir "scores/$BENCH" \
    --method "$METHOD" \
    --n-chunks "$NCH" \
    --chunk-id "$CID"

# csd_infer.py has no chunking: it scores the whole benchmark, so only chunk 0 runs it.
if [[ -z "${SKIP_CSD:-}" && "$CID" == "0" ]]; then
  DIR_ABS=$(cd "$DIR" && pwd); JSON_ABS=$(cd "$(dirname "$JSON")" && pwd)/$(basename "$JSON")
  OUT_ABS=$(pwd)/scores/$BENCH/csd
  (cd CSD && CUDA_VISIBLE_DEVICES=$GPU python3 csd_infer.py \
      --model_path {{MODELS_ROOT}}/CSD-ViT-L/pytorch_model.bin \
      --jsonfile "$JSON_ABS" \
      --data_root "$ROOT" \
      --results_dir "$DIR_ABS" \
      --benchmark "$BENCH" \
      --output_dir "$OUT_ABS" \
      --method "$METHOD" \
      --no_fp16)
fi
