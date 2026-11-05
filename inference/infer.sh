#!/bin/bash
# Usage:  bash inference/infer.sh <gpu> <benchmark> [n_chunks=1] [chunk_id=0] [out_dir]
#   benchmark: iisbench (Insert In Style Bench, 788 pairs)
#              aicomposer | anydoor | subjectplop | tficon  (their JSONs under {{BASELINES_ROOT}}/benchmark_jsons)
#   Output: inference/generations/<benchmark>/<id>.png (what eval/run.sh reads).
#   Split over GPUs with n_chunks / chunk_id (sample i goes to chunk i % n_chunks).
#   Env: CKPT (adapter folder, default inference/checkpoints), IMG_GUIDE (default 1.5)
set -euo pipefail
cd "$(dirname "$0")"

GPU=${1:?gpu id}; BENCH=${2:?benchmark}; NCH=${3:-1}; CID=${4:-0}
case "$BENCH" in
  iisbench)    JSON=../benchmark/insert_in_style_bench_788.json; ROOT=../benchmark ;;
  aicomposer)  JSON={{BASELINES_ROOT}}/benchmark_jsons/ai-composer.json;  ROOT= ;;
  anydoor)     JSON={{BASELINES_ROOT}}/benchmark_jsons/anydoor-real.json; ROOT= ;;
  subjectplop) JSON={{BASELINES_ROOT}}/benchmark_jsons/subjectplop.json;  ROOT= ;;
  tficon)      JSON={{BASELINES_ROOT}}/benchmark_jsons/tf-icon.json;      ROOT= ;;
  *) echo "unknown benchmark: $BENCH"; exit 1 ;;
esac

CUDA_VISIBLE_DEVICES=$GPU python infer.py --json "$JSON" --data_root "$ROOT" --out "${5:-generations/$BENCH}" \
    --ckpt "${CKPT:-checkpoints}" --img_guidance "${IMG_GUIDE:-1.5}" --n_chunks "$NCH" --chunk_id "$CID"
