"""
scripts/dedup/near_dedup.py

Week 5 - Task 2: Near-Duplicate Detection Pipeline via MinHash LSH
Author: Sai Sonawane (Computer Engineering Lead)
Institution: VPKBIET, Baramati

Uses Locality Sensitive Hashing (LSH) and MinHash (128 permutations)
with 3-gram word shingling to detect fuzzy/companion duplicates (Jaccard similarity >= 0.85).
Optimized with vectorized batch hashing and token windowing for scalable processing.

Outputs:
1. data/clean/near_duplicates.csv (Flagged near-duplicate pairs with Jaccard scores)
2. data/clean/near_dedup_stats.json (Telemetry summary on candidate pairs, similarity quantiles)

Usage:
    python scripts/dedup/near_dedup.py --threshold 0.85
    python scripts/dedup/near_dedup.py --max-tokens 2500 --sample 5000
"""

import os
import sys
import re
import csv
import json
import time
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List, Set, Tuple
import numpy as np
from datasketch import MinHash, MinHashLSH

# Reconfigure stdout/stderr for UTF-8 on Windows
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_CLEAN = BASE_DIR / "data" / "clean"
CASES_JSONL = DATA_CLEAN / "cases.jsonl"
EXACT_DUP_CSV = DATA_CLEAN / "exact_duplicates.csv"
NEAR_DUP_CSV = DATA_CLEAN / "near_duplicates.csv"
STATS_JSON = DATA_CLEAN / "near_dedup_stats.json"

WORD_RE = re.compile(r'\b[a-z]{2,}\b')

def get_3gram_shingles(text: str, max_tokens: int = 2500) -> List[bytes]:
    """Extracts 3-word sliding window shingles encoded as bytes for fast batch updating."""
    tokens = WORD_RE.findall(text.lower())
    if max_tokens and len(tokens) > max_tokens:
        tokens = tokens[:max_tokens]
    if len(tokens) < 3:
        return [t.encode('utf-8') for t in tokens]
    return [f"{tokens[i]} {tokens[i+1]} {tokens[i+2]}".encode('utf-8') for i in range(len(tokens) - 2)]

def build_minhash(shingles: List[bytes], num_perm: int = 128) -> MinHash:
    """Builds a MinHash signature using batch hashing."""
    m = MinHash(num_perm=num_perm)
    if shingles:
        m.update_batch(shingles)
    return m

def run_near_dedup(threshold: float = 0.85, max_tokens: int = 2500, num_perm: int = 128, sample_limit: int = None):
    print("=" * 75, flush=True)
    print("CiteJustice - Week 5 Task 2: Near-Duplicate Detection (MinHash LSH)", flush=True)
    print(f"Author: Sai Sonawane (Computer Engineering Lead)", flush=True)
    print(f"Jaccard Similarity Threshold: {threshold * 100:.1f}% | Permutations: {num_perm} | Max Tokens: {max_tokens}", flush=True)
    if sample_limit:
        print(f"Sample Limit Mode: Scanning first {sample_limit:,} cases", flush=True)
    print("=" * 75, flush=True)

    start_time = time.time()

    # Step 1: Load exact duplicate exclusions
    exact_duplicates = set()
    if EXACT_DUP_CSV.exists():
        with open(EXACT_DUP_CSV, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                dup_id = row.get("duplicate_case_id")
                if dup_id:
                    exact_duplicates.add(dup_id)
        print(f"\n[Stage 1/4] Loaded {len(exact_duplicates):,} exact duplicate IDs to exclude from indexing.", flush=True)
    else:
        print(f"\n[Stage 1/4] No exact duplicates file found at {EXACT_DUP_CSV}. Proceeding with all cases.", flush=True)

    # Step 2: Initialize LSH Index
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    case_minhashes = {}
    case_meta = {}

    print(f"\n[Stage 2/4] Shingling cases & populating MinHash LSH index...", flush=True)
    scanned_count = 0
    indexed_count = 0
    t_stage2_start = time.time()

    with open(CASES_JSONL, mode="r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            cid = record["case_id"]
            scanned_count += 1

            # Skip exact duplicates
            if cid in exact_duplicates:
                continue

            clean_text = record.get("text_features", {}).get("clean_text", "")
            shingles = get_3gram_shingles(clean_text, max_tokens=max_tokens)
            if not shingles:
                continue

            mh = build_minhash(shingles, num_perm=num_perm)
            lsh.insert(cid, mh)

            case_minhashes[cid] = mh
            case_meta[cid] = {
                "year": record.get("year"),
                "court_tier": record.get("court_tier", "APEX"),
                "split": record.get("split", "train"),
                "binary_label": record.get("outcome", {}).get("binary_label"),
                "word_count": record.get("text_features", {}).get("word_count", 0),
                "section_count": record.get("statutory_entities", {}).get("section_count", 0),
                "dataset_source": record.get("dataset_source", "ILDC")
            }
            indexed_count += 1

            if indexed_count % 5000 == 0:
                elapsed_stage = time.time() - t_stage2_start
                rate = indexed_count / elapsed_stage
                print(f"  Indexed {indexed_count:,} cases ({rate:.1f} cases/sec)...", flush=True)

            if sample_limit and indexed_count >= sample_limit:
                print(f"  Reached sample limit of {sample_limit:,} cases.", flush=True)
                break

    print(f"  [OK] Successfully indexed {indexed_count:,} unique cases into LSH in {time.time() - t_stage2_start:.2f}s.", flush=True)

    # Step 3: Query LSH Index for Near-Duplicate Candidate Pairs
    print(f"\n[Stage 3/4] Querying LSH table for pairs with Jaccard similarity >= {threshold * 100:.1f}%...", flush=True)
    t_stage3_start = time.time()
    checked_pairs = set()
    near_dup_records = []
    jaccard_scores = []

    query_count = 0
    for cid, mh in case_minhashes.items():
        query_count += 1
        candidates = lsh.query(mh)
        for cand_id in candidates:
            if cand_id == cid:
                continue
            pair = tuple(sorted([cid, cand_id]))
            if pair in checked_pairs:
                continue
            checked_pairs.add(pair)

            # Compute precise estimated Jaccard similarity between MinHash signatures
            sim = mh.jaccard(case_minhashes[cand_id])
            if sim >= threshold:
                meta_a = case_meta[pair[0]]
                meta_b = case_meta[pair[1]]
                jaccard_scores.append(sim)

                near_dup_records.append({
                    "case_id_a": pair[0],
                    "year_a": meta_a["year"],
                    "source_a": meta_a["dataset_source"],
                    "word_count_a": meta_a["word_count"],
                    "case_id_b": pair[1],
                    "year_b": meta_b["year"],
                    "source_b": meta_b["dataset_source"],
                    "word_count_b": meta_b["word_count"],
                    "jaccard_similarity": round(float(sim), 4),
                    "relationship_type": "COMPANION_BENCH" if meta_a["year"] == meta_b["year"] else "TEMPORAL_BOILERPLATE"
                })

        if query_count % 10000 == 0:
            print(f"  Evaluated {query_count:,} queries... Found {len(near_dup_records):,} pairs so far.", flush=True)

    # Sort near duplicates by Jaccard similarity descending
    near_dup_records.sort(key=lambda x: x["jaccard_similarity"], reverse=True)
    print(f"  [OK] Identified {len(near_dup_records):,} candidate near-duplicate pairs (Jaccard >= {threshold}) in {time.time() - t_stage3_start:.2f}s.", flush=True)

    # Step 4: Export Audit Log and Telemetry
    print("\n[Stage 4/4] Exporting near-duplicate audit trail & telemetry...", flush=True)
    if near_dup_records:
        with open(NEAR_DUP_CSV, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=near_dup_records[0].keys())
            writer.writeheader()
            writer.writerows(near_dup_records)
        print(f"  [OK] Saved near-duplicate audit log: {NEAR_DUP_CSV} ({len(near_dup_records):,} pairs)", flush=True)
    else:
        with open(NEAR_DUP_CSV, mode="w", encoding="utf-8", newline="") as f:
            f.write("case_id_a,year_a,source_a,word_count_a,case_id_b,year_b,source_b,word_count_b,jaccard_similarity,relationship_type\n")
        print(f"  [OK] Clean dataset! Zero near-duplicate pairs above threshold {threshold}.", flush=True)

    # Telemetry JSON Export
    telemetry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "author": "Sai Sonawane (Computer Engineering Lead)",
        "total_cases_scanned": scanned_count,
        "cases_indexed_lsh": indexed_count,
        "exact_duplicates_bypassed": len(exact_duplicates),
        "jaccard_threshold": threshold,
        "num_permutations": num_perm,
        "max_tokens_window": max_tokens,
        "near_duplicate_pairs_found": len(near_dup_records),
        "mean_jaccard_similarity": round(float(np.mean(jaccard_scores)), 4) if jaccard_scores else 0.0,
        "max_jaccard_similarity": round(float(np.max(jaccard_scores)), 4) if jaccard_scores else 0.0,
        "min_jaccard_similarity": round(float(np.min(jaccard_scores)), 4) if jaccard_scores else 0.0,
        "companion_bench_pairs": sum(1 for r in near_dup_records if r["relationship_type"] == "COMPANION_BENCH"),
        "cross_temporal_pairs": sum(1 for r in near_dup_records if r["relationship_type"] == "TEMPORAL_BOILERPLATE"),
        "elapsed_seconds": round(time.time() - start_time, 2)
    }

    with open(STATS_JSON, mode="w", encoding="utf-8") as f:
        json.dump(telemetry, f, indent=2)
    print(f"  [OK] Saved near-dedup telemetry: {STATS_JSON}", flush=True)

    elapsed = time.time() - start_time
    print("\n" + "=" * 75, flush=True)
    print("TASK 2 COMPLETED SUCCESSFULLY", flush=True)
    print(f"Total Unique Cases Evaluated:   {indexed_count:,}", flush=True)
    print(f"Near-Duplicate Pairs Flagged:   {len(near_dup_records):,}", flush=True)
    print(f"Companion Bench Pairs (Same Yr):{telemetry['companion_bench_pairs']:,}", flush=True)
    print(f"Temporal Boilerplate (Diff Yr): {telemetry['cross_temporal_pairs']:,}", flush=True)
    print(f"Audit Trail Saved:              {NEAR_DUP_CSV}", flush=True)
    print(f"Execution Time:                 {elapsed:.2f} seconds", flush=True)
    print("=" * 75, flush=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MinHash LSH Near-Duplicate Detection for CiteJustice")
    parser.add_argument("--threshold", type=float, default=0.85, help="Jaccard similarity threshold (default: 0.85)")
    parser.add_argument("--max-tokens", type=int, default=2500, help="Max tokens window to shingle (default: 2500)")
    parser.add_argument("--num-perm", type=int, default=128, help="Number of MinHash permutations (default: 128)")
    parser.add_argument("--sample", type=int, default=None, help="Process top N cases for fast profiling")
    args = parser.parse_args()

    run_near_dedup(threshold=args.threshold, max_tokens=args.max_tokens, num_perm=args.num_perm, sample_limit=args.sample)
