"""
scripts/splits/temporal_split.py

Week 5 - Task 3: Temporal Dataset Splitting Pipeline (Option A)
Author: Sai Sonawane (Computer Engineering Lead)
Institution: VPKBIET, Baramati

Implements strictly forward-looking temporal dataset partitioning:
- Train: 1950 <= year <= 2015 (~85%)
- Dev (Validation): 2016 <= year <= 2018 (~7.2%)
- Test (Held-out): 2019 <= year <= 2024 (~7.8%)

Excludes exact duplicates (Task 1) and cross-boundary near-duplicate pairs (Task 2)
to guarantee zero look-ahead bias and zero train/test contamination.

Outputs:
1. data/splits/train.jsonl
2. data/splits/dev.jsonl
3. data/splits/test.jsonl
4. data/splits/split_stats.json
5. data/splits/pyg_split_masks.npz (aligned with data/graph/pyg_node_map.json)

Usage:
    python scripts/splits/temporal_split.py
"""

import os
import sys
import csv
import json
import time
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List, Set
import numpy as np

# Reconfigure stdout/stderr for UTF-8 on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_CLEAN = BASE_DIR / "data" / "clean"
DATA_SPLITS = BASE_DIR / "data" / "splits"
DATA_GRAPH = BASE_DIR / "data" / "graph"

CASES_JSONL = DATA_CLEAN / "cases.jsonl"
EXACT_DUP_CSV = DATA_CLEAN / "exact_duplicates.csv"
NEAR_DUP_CSV = DATA_CLEAN / "near_duplicates.csv"

TRAIN_JSONL = DATA_SPLITS / "train.jsonl"
DEV_JSONL = DATA_SPLITS / "dev.jsonl"
TEST_JSONL = DATA_SPLITS / "test.jsonl"
STATS_JSON = DATA_SPLITS / "split_stats.json"
PYG_MASKS_NPZ = DATA_SPLITS / "pyg_split_masks.npz"
PYG_NODE_MAP = DATA_GRAPH / "pyg_node_map.json"

TRAIN_YEAR_MAX = 2015
DEV_YEAR_MAX = 2018

def get_temporal_split(year: int) -> str:
    """Returns the temporal split partition for a given judgment year."""
    if year is None:
        return "train"
    if year <= TRAIN_YEAR_MAX:
        return "train"
    elif year <= DEV_YEAR_MAX:
        return "dev"
    else:
        return "test"

def run_temporal_split():
    print("=" * 75, flush=True)
    print("CiteJustice - Week 5 Task 3: Temporal Dataset Splitting (Option A)", flush=True)
    print(f"Author: Sai Sonawane (Computer Engineering Lead)", flush=True)
    print(f"Temporal Boundaries: Train <= {TRAIN_YEAR_MAX} | Dev 2016-{DEV_YEAR_MAX} | Test >= 2019", flush=True)
    print("=" * 75, flush=True)

    start_time = time.time()
    DATA_SPLITS.mkdir(parents=True, exist_ok=True)

    # Stage 1: Load exclusions (Exact duplicates & Cross-split near duplicates)
    print("\n[Stage 1/5] Loading duplicate exclusions...", flush=True)
    exact_duplicates = set()
    if EXACT_DUP_CSV.exists():
        with open(EXACT_DUP_CSV, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dup_id = row.get("duplicate_case_id")
                if dup_id:
                    exact_duplicates.add(dup_id)
        print(f"  [OK] Loaded {len(exact_duplicates):,} exact duplicate case IDs.", flush=True)

    # Check for near-duplicates that cross the split boundary (Test vs Dev/Train)
    cross_split_exclusions = set()
    if NEAR_DUP_CSV.exists():
        with open(NEAR_DUP_CSV, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    ya = int(row.get("year_a", 0))
                    yb = int(row.get("year_b", 0))
                except (ValueError, TypeError):
                    continue
                sa = get_temporal_split(ya)
                sb = get_temporal_split(yb)
                if sa != sb:
                    # Drop the later case to preserve past-to-future purity
                    if ya < yb:
                        cross_split_exclusions.add(row.get("case_id_b"))
                    else:
                        cross_split_exclusions.add(row.get("case_id_a"))
        print(f"  [OK] Flagged {len(cross_split_exclusions):,} cross-boundary near-duplicate cases for exclusion.", flush=True)

    total_exclusions = exact_duplicates | cross_split_exclusions
    print(f"  [OK] Total excluded cases: {len(total_exclusions):,}", flush=True)

    # Stage 2: Partitioning master dataset
    print("\n[Stage 2/5] Partitioning master cases into Train, Dev, Test...", flush=True)
    
    split_counts = {"train": 0, "dev": 0, "test": 0, "excluded": 0}
    yearly_distribution = {"train": defaultdict(int), "dev": defaultdict(int), "test": defaultdict(int)}
    binary_label_dist = {"train": defaultdict(int), "dev": defaultdict(int), "test": defaultdict(int)}
    ternary_label_dist = {"train": defaultdict(int), "dev": defaultdict(int), "test": defaultdict(int)}
    word_count_stats = {"train": [], "dev": [], "test": []}
    court_tier_dist = {"train": defaultdict(int), "dev": defaultdict(int), "test": defaultdict(int)}

    case_id_to_split = {}
    temp_cases_path = DATA_CLEAN / "cases_updated_splits.jsonl"

    f_train = open(TRAIN_JSONL, mode="w", encoding="utf-8")
    f_dev = open(DEV_JSONL, mode="w", encoding="utf-8")
    f_test = open(TEST_JSONL, mode="w", encoding="utf-8")
    f_updated_all = open(temp_cases_path, mode="w", encoding="utf-8")

    total_scanned = 0
    t0_scan = time.time()

    with open(CASES_JSONL, mode="r", encoding="utf-8") as f_in:
        for line in f_in:
            if not line.strip():
                continue
            total_scanned += 1
            record = json.loads(line)
            cid = record["case_id"]
            year = record.get("year", 2000)

            if cid in total_exclusions:
                assigned_split = "excluded"
                split_counts["excluded"] += 1
                record["split"] = "excluded"
                case_id_to_split[cid] = "excluded"
            else:
                assigned_split = get_temporal_split(year)
                split_counts[assigned_split] += 1
                record["split"] = assigned_split
                case_id_to_split[cid] = assigned_split

                yearly_distribution[assigned_split][year] += 1
                court_tier = record.get("court_tier", "APEX")
                court_tier_dist[assigned_split][court_tier] += 1

                wc = record.get("text_features", {}).get("word_count", 0)
                word_count_stats[assigned_split].append(wc)

                outcome = record.get("outcome", {})
                b_lbl = outcome.get("binary_label")
                t_lbl = outcome.get("ternary_label")
                binary_label_dist[assigned_split][str(b_lbl)] += 1
                ternary_label_dist[assigned_split][str(t_lbl)] += 1

                # Write to respective split partition file
                line_str = json.dumps(record, ensure_ascii=False) + "\n"
                if assigned_split == "train":
                    f_train.write(line_str)
                elif assigned_split == "dev":
                    f_dev.write(line_str)
                elif assigned_split == "test":
                    f_test.write(line_str)

            # Write updated record to master jsonl
            f_updated_all.write(json.dumps(record, ensure_ascii=False) + "\n")

            if total_scanned % 10000 == 0:
                print(f"  Processed {total_scanned:,} cases...", flush=True)

    f_train.close()
    f_dev.close()
    f_test.close()
    f_updated_all.close()

    # Replace old cases.jsonl with updated split tags
    if temp_cases_path.exists():
        temp_cases_path.replace(CASES_JSONL)
        print(f"  [OK] Updated master cases file with new split tags: {CASES_JSONL}", flush=True)

    active_cases = split_counts["train"] + split_counts["dev"] + split_counts["test"]
    print(f"\n[Stage 3/5] Partitioning Summary:")
    print(f"  - Train Split (<= 2015):       {split_counts['train']:,} ({split_counts['train'] / active_cases * 100:.2f}%)")
    print(f"  - Dev Split   (2016 - 2018):   {split_counts['dev']:,} ({split_counts['dev'] / active_cases * 100:.2f}%)")
    print(f"  - Test Split  (2019 - 2024):   {split_counts['test']:,} ({split_counts['test'] / active_cases * 100:.2f}%)")
    print(f"  - Excluded (Duplicates/Leaks): {split_counts['excluded']:,}")
    print(f"  - Total Clean Active Cases:    {active_cases:,}")

    # Stage 4: Generate PyG Split Masks
    print(f"\n[Stage 4/5] Generating PyTorch Geometric split masks...", flush=True)
    if PYG_NODE_MAP.exists():
        with open(PYG_NODE_MAP, mode="r", encoding="utf-8") as f_map:
            node_map = json.load(f_map)

        num_nodes = len(node_map)
        train_mask = np.zeros(num_nodes, dtype=bool)
        val_mask = np.zeros(num_nodes, dtype=bool)
        test_mask = np.zeros(num_nodes, dtype=bool)

        matched_nodes = 0
        for cid, node_idx in node_map.items():
            s = case_id_to_split.get(cid)
            if s == "train":
                train_mask[node_idx] = True
                matched_nodes += 1
            elif s == "dev":
                val_mask[node_idx] = True
                matched_nodes += 1
            elif s == "test":
                test_mask[node_idx] = True
                matched_nodes += 1

        np.savez_compressed(
            PYG_MASKS_NPZ,
            train_mask=train_mask,
            val_mask=val_mask,
            test_mask=test_mask
        )
        print(f"  [OK] Exported PyG split masks: {PYG_MASKS_NPZ}")
        print(f"       Mask nodes matched: {matched_nodes:,} / {num_nodes:,} (Train: {train_mask.sum():,}, Val: {val_mask.sum():,}, Test: {test_mask.sum():,})")
    else:
        print(f"  [WARN] PyG node map not found at {PYG_NODE_MAP}. Skipping PyG mask export.")

    # Stage 5: Compile Telemetry & Statistics
    print(f"\n[Stage 5/5] Exporting split statistics & telemetry...", flush=True)
    stats_data = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "author": "Sai Sonawane (Computer Engineering Lead)",
        "boundaries": {
            "train": f"1950 - {TRAIN_YEAR_MAX}",
            "dev": f"2016 - {DEV_YEAR_MAX}",
            "test": f"2019 - 2024"
        },
        "counts": {
            "total_master_cases": total_scanned,
            "total_active_clean_cases": active_cases,
            "exact_duplicates_excluded": len(exact_duplicates),
            "cross_split_leaks_excluded": len(cross_split_exclusions),
            "total_excluded": split_counts["excluded"],
            "train": split_counts["train"],
            "dev": split_counts["dev"],
            "test": split_counts["test"]
        },
        "percentages": {
            "train": round(split_counts["train"] / active_cases * 100, 2),
            "dev": round(split_counts["dev"] / active_cases * 100, 2),
            "test": round(split_counts["test"] / active_cases * 100, 2)
        },
        "binary_label_balance": {
            s: dict(binary_label_dist[s]) for s in ["train", "dev", "test"]
        },
        "ternary_label_balance": {
            s: dict(ternary_label_dist[s]) for s in ["train", "dev", "test"]
        },
        "mean_word_count": {
            s: round(float(np.mean(word_count_stats[s])), 1) if word_count_stats[s] else 0 for s in ["train", "dev", "test"]
        },
        "court_tiers": {
            s: dict(court_tier_dist[s]) for s in ["train", "dev", "test"]
        },
        "yearly_cases": {
            s: dict(sorted(yearly_distribution[s].items())) for s in ["train", "dev", "test"]
        }
    }

    with open(STATS_JSON, mode="w", encoding="utf-8") as f_out:
        json.dump(stats_data, f_out, indent=2)
    print(f"  [OK] Saved split telemetry: {STATS_JSON}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 75, flush=True)
    print("TASK 3 COMPLETED SUCCESSFULLY", flush=True)
    print(f"Train Cases:        {split_counts['train']:,} ({stats_data['percentages']['train']}%) -> {TRAIN_JSONL}")
    print(f"Dev Cases:          {split_counts['dev']:,} ({stats_data['percentages']['dev']}%) -> {DEV_JSONL}")
    print(f"Test Cases:         {split_counts['test']:,} ({stats_data['percentages']['test']}%) -> {TEST_JSONL}")
    print(f"Split Stats:        {STATS_JSON}")
    print(f"Execution Time:     {elapsed:.2f} seconds")
    print("=" * 75, flush=True)

if __name__ == "__main__":
    run_temporal_split()
