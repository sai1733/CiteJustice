"""
scripts/graph/build_edge_list.py

Week 3 - Task 3B: Citation to Case ID Resolution & Master Edge List Builder
Author: Sai Sonawane (CiteJustice)

Deliverable from Team Work Division (Week 3, Sai Task 3 & 4):
1. Builds canonical citation -> case_id lookup dictionary (citation_to_case_id.json).
2. Resolves raw citation spans to actual internal ILDC case IDs where available.
3. Computes and documents empirical resolution statistics (% resolved vs unresolved external).
4. Exports master unified citation edge table to:
   - data/graph/citations.csv
   - data/graph/citation_to_case_id.json
   - data/graph/resolution_stats.json

Usage:
    py scripts/graph/build_edge_list.py
"""

import os
import re
import sys
import csv
import json
from pathlib import Path

# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CLEAN_DIR = BASE_DIR / "data" / "clean"
GRAPH_DIR = BASE_DIR / "data" / "graph"
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

def build_citation_resolution_table():
    print("=" * 70)
    print("CiteJustice - Week 3: Citation to Case ID Resolution & Edge List Builder")
    print(f"Target Output Directory: {GRAPH_DIR}")
    print("=" * 70)

    # 1. Collect all known internal ILDC and Nyaya case IDs
    internal_case_ids = set()
    for fname in ["ildc_single_segmented.jsonl", "ildc_multi_segmented.jsonl", "nyaya_2021_2024_segmented.jsonl"]:
        p = CLEAN_DIR / fname
        if p.exists():
            print(f"Indexing internal case IDs from: {fname}...")
            with open(p, mode="r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    d = json.loads(line)
                    cid = d.get("id")
                    if cid:
                        internal_case_ids.add(cid)

    print(f"Total unique internal case IDs indexed: {len(internal_case_ids):,}\n")

    # 2. Load classified edges from single, multi, and nyaya 2021-2024
    classified_edge_sources = [
        CLEAN_DIR / "ildc_single_classified_edges.jsonl",
        CLEAN_DIR / "ildc_multi_classified_edges.jsonl",
        CLEAN_DIR / "nyaya_2021_2024_classified_edges.jsonl"
    ]

    all_edges = []
    for p in classified_edge_sources:
        if p.exists():
            print(f"Loading classified edges from: {p.name}...")
            with open(p, mode="r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        all_edges.append(json.loads(line))

    total_edges = len(all_edges)
    print(f"Total candidate citation edges loaded: {total_edges:,}\n")

    # 3. Resolve citations to internal case IDs
    # Heuristics:
    # A. Year and final page number matching (e.g. '[1950] SCR 88' -> '1950_88', '(2000) 4 SCC 262' -> '2000_262')
    # B. Year and volume number matching
    citation_to_case_id = {}
    resolved_edges_count = 0
    unresolved_edges_count = 0

    resolved_records = []

    print("Resolving precedent citations to internal case IDs...")
    for idx, e in enumerate(all_edges, 1):
        citing_id = e.get("citing_case_id")
        cited_cit = e.get("cited_citation", "").strip()

        # Check existing mapping cache
        resolved_id = None
        if cited_cit in citation_to_case_id:
            resolved_id = citation_to_case_id[cited_cit]
        else:
            # Try Year + Page
            m_yr = re.search(r"((?:19|20)\d{2})", cited_cit)
            m_page = re.search(r"(\d+)\s*$", cited_cit)
            if m_yr and m_page:
                cand_a = f"{m_yr.group(1)}_{m_page.group(1)}"
                if cand_a in internal_case_ids:
                    resolved_id = cand_a

            if not resolved_id and m_yr:
                # Try Year + Volume
                m_vol = re.search(r"(?:SCR|SCC|AIR|SCALE)\s+(\d+)", cited_cit, re.I)
                if m_vol:
                    cand_b = f"{m_yr.group(1)}_{m_vol.group(1)}"
                    if cand_b in internal_case_ids:
                        resolved_id = cand_b

            citation_to_case_id[cited_cit] = resolved_id if resolved_id else "UNRESOLVED_EXTERNAL"

        target_case_id = citation_to_case_id[cited_cit]
        is_internal = (target_case_id != "UNRESOLVED_EXTERNAL")

        if is_internal:
            resolved_edges_count += 1
        else:
            unresolved_edges_count += 1

        # Calculate weight
        base_weights = {"FOLLOWED": 1.0, "OVERRULED": -1.0, "DISTINGUISHED": 0.4, "CONSIDERED": 0.2}
        rel = e.get("relationship", "CONSIDERED")
        conf = float(e.get("confidence", 0.50))
        is_sub = bool(e.get("is_submission", False))
        weight = base_weights.get(rel, 0.2) * conf
        if is_sub:
            weight *= 0.70

        preview = e.get("context_window_50", "")[:150] + "..." if len(e.get("context_window_50", "")) > 150 else e.get("context_window_50", "")

        resolved_records.append({
            "edge_id": e.get("edge_id", f"edge_{idx:06d}"),
            "citing_case_id": citing_id,
            "citing_year": e.get("citing_year"),
            "cited_citation": cited_cit,
            "cited_year": e.get("cited_year"),
            "resolved_target_case_id": target_case_id,
            "is_internal_precedent": is_internal,
            "relationship": rel,
            "confidence": round(conf, 2),
            "weight": round(weight, 4),
            "rhetorical_zone": e.get("rhetorical_zone", "UNSPECIFIED"),
            "is_submission": is_sub,
            "temporal_valid": e.get("temporal_valid", True),
            "context_preview": preview
        })

    # 4. Save citation_to_case_id lookup JSON
    lookup_file = GRAPH_DIR / "citation_to_case_id.json"
    with open(lookup_file, mode="w", encoding="utf-8") as f:
        json.dump(citation_to_case_id, f, indent=2, ensure_ascii=False)
    print(f"\n[OK] Citation lookup dictionary saved to: {lookup_file.name}")

    # 5. Save master citations.csv
    citations_csv = GRAPH_DIR / "citations.csv"
    fields = [
        "edge_id",
        "citing_case_id",
        "citing_year",
        "cited_citation",
        "cited_year",
        "resolved_target_case_id",
        "is_internal_precedent",
        "relationship",
        "confidence",
        "weight",
        "rhetorical_zone",
        "is_submission",
        "temporal_valid",
        "context_preview"
    ]
    with open(citations_csv, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(resolved_records)
    print(f"[OK] Master citation edge list saved to: {citations_csv.name}")

    # 6. Save resolution stats JSON
    unique_citations = len(citation_to_case_id)
    unique_resolved = sum(1 for v in citation_to_case_id.values() if v != "UNRESOLVED_EXTERNAL")

    stats = {
        "total_citation_edges": total_edges,
        "resolved_to_internal_case": resolved_edges_count,
        "unresolved_external_precedents": unresolved_edges_count,
        "edge_resolution_rate_percent": round((resolved_edges_count / max(1, total_edges)) * 100, 2),
        "unique_citation_spans": unique_citations,
        "unique_citations_resolved": unique_resolved,
        "unique_citation_resolution_percent": round((unique_resolved / max(1, unique_citations)) * 100, 2)
    }

    stats_file = GRAPH_DIR / "resolution_stats.json"
    with open(stats_file, mode="w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)
    print(f"[OK] Resolution statistics saved to: {stats_file.name}")

    # Console Summary
    print("\n" + "=" * 50)
    print("Citation Resolution Summary:")
    print(f"  Total Citation Edges Extracted : {total_edges:,}")
    print(f"  Resolved to Internal Judgments : {resolved_edges_count:,} ({stats['edge_resolution_rate_percent']}%)")
    print(f"  Unresolved External Precedents : {unresolved_edges_count:,} ({100 - stats['edge_resolution_rate_percent']}%)")
    print(f"  Unique Citations Canonicalized : {unique_citations:,}")
    print(f"  Unique Citations Resolved      : {unique_resolved:,} ({stats['unique_citation_resolution_percent']}%)")
    print("=" * 50)

if __name__ == "__main__":
    build_citation_resolution_table()
