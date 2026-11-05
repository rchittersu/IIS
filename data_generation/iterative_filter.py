#!/usr/bin/env python
"""
Iterative decile filter (paper Sec. 3).

Input: one scored .jsonl per style (rows with clip_sim, dino_sim, csd_sim; see score_identity.py and
eval/CSD/csd_clip_infer.py). For each style:
- drop rows with a missing score,
- then, each iteration, drop every row below the 10th percentile on ANY of the three scores.
Writes <out>/<style>/iteration<N>.jsonl for every iteration, plus iteration_summary.txt / .csv.
We stopped at iteration 4 once human acceptance saturated: that is data/stylized_final_115k
(per-style counts and thresholds in iteration_thresholds.csv).

Usage:
    python data_generation/iterative_filter.py <scored_dir> <out_dir>
"""

import os
import json
import numpy as np
from pathlib import Path

# Set thread limits to avoid pandas/numpy warnings
os.environ['NUMEXPR_MAX_THREADS'] = '16'

import sys
if len(sys.argv) != 3:
    sys.exit(__doc__)
INPUT_DIR, OUTPUT_DIR = sys.argv[1], sys.argv[2]

# Metrics to use for filtering
METRICS = ['clip_sim', 'dino_sim', 'csd_sim']

# Number of iterations
NUM_ITERATIONS = 20


def load_jsonl_file(filepath):
    """
    Load a single JSONL file
    
    Args:
        filepath: Path to JSONL file
    
    Returns:
        List of entries
    """
    data = []
    with open(filepath, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                data.append(entry)
            except json.JSONDecodeError:
                continue
    
    return data


def style_name_to_folder(style_name):
    """
    Convert style name to folder name format
    Example: "American_Cartoon" → "american-cartoon"
    
    Args:
        style_name: Original style name
    
    Returns:
        Folder name (lowercase with hyphens)
    """
    return style_name.lower().replace('_', '-')


def remove_none_values(data, metrics):
    """
    Remove entries where any metric is None or missing
    
    Args:
        data: List of entries
        metrics: List of metric names to check
    
    Returns:
        Tuple of (filtered_data, removed_count)
    """
    filtered_data = []
    removed_count = 0
    
    for entry in data:
        has_none = False
        for metric_name in metrics:
            if metric_name not in entry or entry[metric_name] is None:
                has_none = True
                break
        
        if has_none:
            removed_count += 1
        else:
            filtered_data.append(entry)
    
    return filtered_data, removed_count


def apply_threshold_filter(data, metrics):
    """
    Filter data based on 10th percentile thresholds for all metrics
    
    Removes samples below threshold on ANY metric
    
    Args:
        data: List of entries
        metrics: List of metric names to use
    
    Returns:
        Tuple of (filtered_data, thresholds, removed_count)
    """
    # Calculate thresholds for each metric (10th percentile)
    thresholds = {}
    for metric_name in metrics:
        valid_values = [e[metric_name] for e in data if metric_name in e and e[metric_name] is not None]
        valid_values.sort()
        threshold = np.percentile(valid_values, 10)
        thresholds[metric_name] = threshold
    
    # Identify entries to remove (below threshold on ANY metric)
    filtered_data = []
    removed_count = 0
    
    for entry in data:
        should_remove = False
        for metric_name in metrics:
            if metric_name not in entry or entry[metric_name] is None or entry[metric_name] < thresholds[metric_name]:
                should_remove = True
                break
        
        if should_remove:
            removed_count += 1
        else:
            filtered_data.append(entry)
    
    return filtered_data, thresholds, removed_count


def save_iteration_data(data, output_dir, style_folder_name, iteration_num):
    """
    Save iteration data to JSONL file
    
    Args:
        data: List of entries
        output_dir: Output directory
        style_folder_name: Name of the style folder
        iteration_num: Iteration number
    
    Returns:
        Number of samples saved
    """
    style_dir = os.path.join(output_dir, style_folder_name)
    os.makedirs(style_dir, exist_ok=True)
    
    iteration_file = os.path.join(style_dir, f"iteration{iteration_num}.jsonl")
    
    with open(iteration_file, 'w') as f:
        for entry in data:
            f.write(json.dumps(entry) + '\n')
    
    return len(data)


def main():
    print("="*70)
    print("Iterative decile filter")
    print("="*70)
    print(f"\nInput directory: {INPUT_DIR}")
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Metrics: {METRICS}")
    print(f"Number of iterations: {NUM_ITERATIONS}")
    
    # Get all JSONL files
    jsonl_files = list(Path(INPUT_DIR).glob("*.jsonl"))
    jsonl_files.sort()
    
    print(f"\nFound {len(jsonl_files)} JSONL files to process")
    
    if len(jsonl_files) == 0:
        print("No JSONL files found! Exiting.")
        return
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Process each file
    all_iteration_stats = {}
    
    for jsonl_file in jsonl_files:
        style_name = jsonl_file.stem
        style_folder_name = style_name_to_folder(style_name)
        
        print(f"\n{'='*70}")
        print(f"Processing: {style_name}")
        print('='*70)
        
        # Load initial data
        data = load_jsonl_file(jsonl_file)
        
        if len(data) == 0:
            print(f"  No data found, skipping...")
            continue
        
        print(f"  Total entries: {len(data)}")
        
        iteration_stats = {}
        current_data = data
        
        # Store original count
        original_count = len(data)
        
        # Perform iterations
        for iteration_num in range(1, NUM_ITERATIONS + 1):
            print(f"\n  --- Iteration {iteration_num} ---")
            
            if iteration_num == 1:
                # First iteration: Remove None values first
                print(f"  Removing entries with None values...")
                current_data, none_removed = remove_none_values(current_data, METRICS)
                print(f"  Removed {none_removed} entries with None values")
                print(f"  Remaining entries: {len(current_data)}")
                
                # Store count after removing none values
                count_after_none = len(current_data)
            
            # Calculate thresholds and filter
            print(f"  Calculating 10th percentile thresholds...")
            filtered_data, thresholds, threshold_removed = apply_threshold_filter(current_data, METRICS)
            
            print(f"  Thresholds:")
            for metric_name, threshold in thresholds.items():
                print(f"    {metric_name}: {threshold:.4f}")
            print(f"  Removed {threshold_removed} entries below thresholds")
            print(f"  Remaining entries: {len(filtered_data)}")
            
            # Save iteration data
            sample_count = save_iteration_data(filtered_data, OUTPUT_DIR, style_folder_name, iteration_num)
            print(f"  Saved {sample_count} samples to iteration{iteration_num}.jsonl")
            
            # Store statistics
            iteration_stats[f'iteration{iteration_num}'] = {
                'samples': sample_count,
                'thresholds': thresholds,
                'threshold_removed': threshold_removed,
                'none_removed': none_removed if iteration_num == 1 else 0
            }
            
            # Use filtered data for next iteration
            current_data = filtered_data
            
            # Stop if no data left
            if len(current_data) == 0:
                print(f"  No data remaining, stopping iterations...")
                break
        
        # Store statistics with original and after-none counts
        all_iteration_stats[style_name] = {
            'original_count': original_count,
            'count_after_none': count_after_none,
            'iterations': iteration_stats
        }
    
    # Print summary
    print("\n" + "="*70)
    print("ITERATION SUMMARY")
    print("="*70)
    
    for style_name, style_data in all_iteration_stats.items():
        print(f"\n{style_name}:")
        print(f"  Original count: {style_data['original_count']}")
        print(f"  Count after removing none: {style_data['count_after_none']}")
        
        for iteration_key in sorted(style_data['iterations'].keys()):
            stats = style_data['iterations'][iteration_key]
            print(f"  {iteration_key}:")
            print(f"    Samples: {stats['samples']}")
            print(f"    None removed: {stats['none_removed']}")
            print(f"    Threshold removed: {stats['threshold_removed']}")
            print(f"    Thresholds: {', '.join([f'{k}={v:.4f}' for k, v in stats['thresholds'].items()])}")
    
    print("\n" + "="*70)
    print("Processing complete!")
    print(f"All iterations saved to: {OUTPUT_DIR}")
    print("="*70)
    
    # Save summary to file
    summary_file = os.path.join(OUTPUT_DIR, "iteration_summary.txt")
    with open(summary_file, 'w') as f:
        f.write("Iterative filter summary\n")
        f.write("="*70 + "\n\n")
        f.write(f"Input directory: {INPUT_DIR}\n")
        f.write(f"Output directory: {OUTPUT_DIR}\n")
        f.write(f"Metrics: {METRICS}\n")
        f.write(f"Number of iterations: {NUM_ITERATIONS}\n\n")
        
        for style_name, style_data in all_iteration_stats.items():
            f.write(f"\n{style_name.upper()}\n")
            f.write("-"*70 + "\n")
            f.write(f"Original count: {style_data['original_count']}\n")
            f.write(f"Count after removing none: {style_data['count_after_none']}\n\n")
            
            for iteration_key in sorted(style_data['iterations'].keys()):
                stats = style_data['iterations'][iteration_key]
                f.write(f"  {iteration_key.upper()}:\n")
                f.write(f"    Samples: {stats['samples']}\n")
                f.write(f"    None removed: {stats['none_removed']}\n")
                f.write(f"    Threshold removed: {stats['threshold_removed']}\n")
                f.write(f"    Thresholds:\n")
                for metric_name, threshold in stats['thresholds'].items():
                    f.write(f"      {metric_name}: {threshold:.4f}\n")
    
    print(f"\nSummary saved to: {summary_file}")

    # Export summary as table with steps as rows
    import pandas as pd
    
    # Create DataFrame with steps as rows and styles as columns
    table_data = {}
    
    # Row 0: Original count before removing none
    row_data = {'step': 'Original count before removing none'}
    for style_name, style_stats in all_iteration_stats.items():
        style_folder_name = style_name_to_folder(style_name)
        row_data[style_folder_name] = style_stats['original_count']
    table_data[0] = row_data
    
    # Row 1: Count after removing none
    row_data = {'step': 'Count after removing none'}
    for style_name, style_stats in all_iteration_stats.items():
        style_folder_name = style_name_to_folder(style_name)
        row_data[style_folder_name] = style_stats['count_after_none']
    table_data[1] = row_data
    
    # Rows for each iteration
    for iteration_num in range(1, NUM_ITERATIONS + 1):
        row_data = {'step': f'iteration{iteration_num}'}
        for style_name, style_stats in all_iteration_stats.items():
            style_folder_name = style_name_to_folder(style_name)
            iteration_key = f'iteration{iteration_num}'
            row_data[style_folder_name] = style_stats['iterations'].get(iteration_key, {}).get('samples', 0)
        table_data[iteration_num + 1] = row_data
    
    # Convert to DataFrame
    df_summary = pd.DataFrame.from_dict(table_data, orient='index')
    
    # Reorder columns: step, then all styles in alphabetical order
    style_cols = sorted([style_name_to_folder(name) for name in all_iteration_stats.keys()])
    column_order = ['step'] + style_cols
    df_summary = df_summary[column_order]
    
    # Save to CSV
    summary_table_file = os.path.join(OUTPUT_DIR, "iteration_summary_table.csv")
    df_summary.to_csv(summary_table_file, index=False)
    print(f"Table summary saved to: {summary_table_file}")


if __name__ == '__main__':
    main()