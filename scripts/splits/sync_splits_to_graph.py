"""
scripts/splits/sync_splits_to_graph.py

Synchronizes Option A temporal splits from cases.jsonl across:
1. data/clean/build_nodes_summary.csv
2. data/clean/dpeg/dpeg_combined_nodes.csv

Author: Sai Sonawane (Computer Engineering Lead)
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

# Reconfigure stdout/stderr for UTF-8 on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_CLEAN = BASE_DIR / "data" / "clean"
CASES_JSONL = DATA_CLEAN / "cases.jsonl"
BUILD_SUMMARY_CSV = DATA_CLEAN / "build_nodes_summary.csv"
DPEG_NODES_CSV = DATA_CLEAN / "dpeg" / "dpeg_combined_nodes.csv"

def sync_splits():
    print("=" * 70, flush=True)
    print("Syncing Option A Splits to Tabular Node Files", flush=True)
    print("=" * 70, flush=True)

    print("\n[Stage 1/2] Loading verified split tags from cases.jsonl...", flush=True)
    case_splits = {}
    with open(CASES_JSONL, mode="r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            record = json.loads(line)
            case_splits[str(record["case_id"])] = record.get("split", "train")

    print(f"  [OK] Loaded {len(case_splits):,} case split tags from cases.jsonl.", flush=True)

    # 1. Update build_nodes_summary.csv
    if BUILD_SUMMARY_CSV.exists():
        print(f"\n[Stage 2/2] Updating {BUILD_SUMMARY_CSV.name}...", flush=True)
        df_summary = pd.read_csv(BUILD_SUMMARY_CSV)
        df_summary["split"] = df_summary["case_id"].astype(str).map(lambda cid: case_splits.get(cid, "excluded"))
        df_summary.to_csv(BUILD_SUMMARY_CSV, index=False)
        counts_s = df_summary["split"].value_counts().to_dict()
        print(f"  [OK] Updated build_nodes_summary.csv splits: {counts_s}", flush=True)

    # 2. Update dpeg_combined_nodes.csv
    if DPEG_NODES_CSV.exists():
        print(f"  Updating {DPEG_NODES_CSV.name}...", flush=True)
        df_dpeg = pd.read_csv(DPEG_NODES_CSV)
        def map_dpeg(row):
            cid = str(row["node_id"])
            ntype = str(row["node_type"])
            if ntype == "CITED_PRECEDENT":
                return "precedent"
            return case_splits.get(cid, "precedent")

        df_dpeg["split"] = df_dpeg.apply(map_dpeg, axis=1)
        df_dpeg.to_csv(DPEG_NODES_CSV, index=False)
        counts_d = df_dpeg["split"].value_counts().to_dict()
        print(f"  [OK] Updated dpeg_combined_nodes.csv splits: {counts_d}", flush=True)

    print("\n" + "=" * 70, flush=True)
    print("SYNC COMPLETED SUCCESSFULLY", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    sync_splits()
