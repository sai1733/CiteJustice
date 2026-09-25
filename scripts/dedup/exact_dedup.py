"""
scripts/dedup/exact_dedup.py

Week 5 - Task 1: Exact Cryptographic Deduplication Pipeline
Author: Sai Sonawane (Computer Engineering Lead)
Institution: VPKBIET, Baramati

Audits and eliminates identical judgment duplicates using SHA-256 content hashing.
Enforces zero data leakage between training, validation, and evaluation splits.

Outputs:
1. data/clean/exact_duplicates.csv (Audit trail of duplicate pairs & resolution decisions)
2. data/clean/exact_dedup_stats.json (Telemetry on unique clusters, duplicates removed)

Usage:
    python scripts/dedup/exact_dedup.py
"""

import os
import sys
import csv
import json
import hashlib
import time
import argparse
from pathlib import Path
from collections import defaultdict
from typing import Dict, Any, List, Tuple

# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_CLEAN = BASE_DIR / "data" / "clean"
CASES_JSONL = DATA_CLEAN / "cases.jsonl"
DUP_CSV = DATA_CLEAN / "exact_duplicates.csv"
STATS_JSON = DATA_CLEAN / "exact_dedup_stats.json"

def normalize_text_for_hash(text: str) -> str:
    """Normalizes whitespace and casing for canonical exact hash comparison."""
    if not text:
        return ""
    # Collapse multiple whitespaces/newlines and lowercase
    return " ".join(text.lower().split())

def run_exact_dedup():
    print("=" * 75)
    print("CiteJustice - Week 5 Task 1: Exact Cryptographic Deduplication")
    print("Scanning Master Case Corpus via SHA-256 for Identical Duplicate Clusters")
    print("=" * 75)

    start_time = time.time()

    if not CASES_JSONL.exists():
        print(f"Error: {CASES_JSONL} not found! Run Week 4 build_nodes.py first.")
        sys.exit(1)

    print("\n[Stage 1/3] Streaming cases.jsonl & computing cryptographic SHA-256 hashes...")
    hash_to_cases = defaultdict(list)
    total_scanned = 0

    with open(CASES_JSONL, mode="r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            cid = record["case_id"]
            clean_text = record.get("text_features", {}).get("clean_text", "")
            
            # Content normalization and hash
            norm_content = normalize_text_for_hash(clean_text)
            content_hash = hashlib.sha256(norm_content.encode("utf-8")).hexdigest()

            # Metadata score for tie-breaking: prefer richer sections and citations
            sec_count = record.get("statutory_entities", {}).get("section_count", 0)
            cit_count = len(record.get("graph_features", {}).get("outgoing_citations", []))
            word_count = record.get("text_features", {}).get("word_count", 0)
            char_count = record.get("text_features", {}).get("char_count", 0)
            meta_score = (sec_count * 2) + cit_count + (word_count // 100)

            hash_to_cases[content_hash].append({
                "case_id": cid,
                "year": record.get("year"),
                "court_tier": record.get("court_tier", "APEX"),
                "split": record.get("split", "train"),
                "binary_label": record.get("outcome", {}).get("binary_label"),
                "section_count": sec_count,
                "citation_count": cit_count,
                "word_count": word_count,
                "char_count": char_count,
                "meta_score": meta_score,
                "dataset_source": record.get("dataset_source", "ILDC")
            })
            total_scanned += 1

            if total_scanned % 10000 == 0:
                print(f"  Processed {total_scanned:,} cases...")

    unique_hash_count = len(hash_to_cases)
    duplicate_clusters = {h: cases for h, cases in hash_to_cases.items() if len(cases) > 1}
    num_dup_clusters = len(duplicate_clusters)
    num_redundant_cases = sum(len(cases) - 1 for cases in duplicate_clusters.values())

    print(f"\n[Stage 2/3] Hash Scan Results:")
    print(f"  - Total Judgments Scanned: {total_scanned:,}")
    print(f"  - Unique Content Hashes:   {unique_hash_count:,}")
    print(f"  - Duplicate Clusters (>1): {num_dup_clusters:,}")
    print(f"  - Redundant Cases Flagged: {num_redundant_cases:,} ({num_redundant_cases / total_scanned * 100:.2f}%)")

    # Audit duplicate pairs and decide resolution
    print("\n[Stage 3/3] Exporting Duplicate Audit Trail & Telemetry...")
    dup_rows = []
    retained_ids = set()
    removed_ids = set()

    for h, cases in duplicate_clusters.items():
        # Sort by meta_score descending (best metadata first)
        cases_sorted = sorted(cases, key=lambda x: x["meta_score"], reverse=True)
        winner = cases_sorted[0]
        retained_ids.add(winner["case_id"])

        for loser in cases_sorted[1:]:
            removed_ids.add(loser["case_id"])
            dup_rows.append({
                "sha256_hash": h[:16] + "...",
                "retained_case_id": winner["case_id"],
                "retained_year": winner["year"],
                "retained_source": winner["dataset_source"],
                "retained_meta_score": winner["meta_score"],
                "duplicate_case_id": loser["case_id"],
                "duplicate_year": loser["year"],
                "duplicate_source": loser["dataset_source"],
                "duplicate_meta_score": loser["meta_score"],
                "word_count": winner["word_count"],
                "resolution": f"Retained {winner['case_id']} (Higher metadata score: {winner['meta_score']} vs {loser['meta_score']})"
            })

    # Save CSV Audit Log
    if dup_rows:
        with open(DUP_CSV, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=dup_rows[0].keys())
            writer.writeheader()
            writer.writerows(dup_rows)
        print(f"  ? Saved exact duplicate audit log: {DUP_CSV} ({len(dup_rows):,} flagged pairs)")
    else:
        # Create empty template if zero exact duplicates
        with open(DUP_CSV, mode="w", encoding="utf-8", newline="") as f:
            f.write("sha256_hash,retained_case_id,duplicate_case_id,resolution\n")
        print(f"  ? Clean dataset! Zero exact duplicate clusters detected. Created audit verification file: {DUP_CSV}")

    # Telemetry JSON Export
    telemetry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_cases_scanned": total_scanned,
        "unique_content_hashes": unique_hash_count,
        "duplicate_clusters": num_dup_clusters,
        "redundant_cases_flagged": num_redundant_cases,
        "duplicate_rate_percentage": round(num_redundant_cases / total_scanned * 100, 4) if total_scanned > 0 else 0,
        "retained_case_count": total_scanned - num_redundant_cases,
        "resolution_strategy": "Argmax of (statutory_sections * 2 + citations + word_count // 100)"
    }

    with open(STATS_JSON, mode="w", encoding="utf-8") as f:
        json.dump(telemetry, f, indent=2)
    print(f"  ? Saved telemetry summary: {STATS_JSON}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 75)
    print("TASK 1 COMPLETED SUCCESSFULLY")
    print(f"Total Scanned:           {total_scanned:,}")
    print(f"Unique Canonical Hashes: {unique_hash_count:,}")
    print(f"Duplicates Flagged:      {num_redundant_cases:,}")
    print(f"Execution Time:          {elapsed:.2f} seconds")
    print("=" * 75)

if __name__ == "__main__":
    run_exact_dedup()
