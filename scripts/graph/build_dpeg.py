"""
scripts/graph/build_dpeg.py

Week 3 - Task 3: Dynamic Precedent Evolution Graph (DPEG) Construction Pipeline
Author: Sai Sonawane (CiteJustice)

Assembles classified citation edges into a formal, time-directed legal network:
G = (V, E, W, T)
1. Nodes (V): Supreme Court cases (internal judgments with labels + landmark precedent citations)
2. Directed Edges (E): Citing case -> Cited precedent
3. Signed Weights (W):
   - FOLLOWED:      +1.00 * confidence (authority reinforced)
   - OVERRULED:     -1.00 * confidence (authority extinguished)
   - DISTINGUISHED: +0.40 * confidence (factual boundary restriction)
   - CONSIDERED:    +0.20 * confidence (neutral discussion)
   - Submissions:   x 0.70 attenuation (counsel contention vs court ratio)
4. Temporal Slices (T):
   - Era 1: 1950 - 1975 (Foundational Constitutionalism)
   - Era 2: 1976 - 2000 (Basic Structure, Due Process & PIL Expansion)
   - Era 3: 2001 - 2020 (Modern Regulatory & Commercial Era)
   - Master: 1950 - 2020

Usage:
    py scripts/graph/build_dpeg.py --dataset single --sample 100
    py scripts/graph/build_dpeg.py --dataset single
    py scripts/graph/build_dpeg.py --dataset multi
    py scripts/graph/build_dpeg.py --dataset combined
"""

import os
import sys
import csv
import json
import argparse
from pathlib import Path
from collections import defaultdict

# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CLEAN_DIR = BASE_DIR / "data" / "clean"
DPEG_DIR = CLEAN_DIR / "dpeg"
DPEG_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Weight Calculation Formulas
# --------------------------------------------------------------------------
BASE_RELATIONSHIP_WEIGHTS = {
    "FOLLOWED": 1.00,
    "OVERRULED": -1.00,
    "DISTINGUISHED": 0.40,
    "CONSIDERED": 0.20
}

def calculate_edge_weight(relationship: str, confidence: float, is_submission: bool) -> float:
    """Computes signed edge weight based on relationship type, confidence, and zone."""
    base = BASE_RELATIONSHIP_WEIGHTS.get(relationship, 0.20)
    w = base * float(confidence)
    if is_submission:
        w *= 0.70
    return round(w, 4)

def assign_temporal_era(year: int) -> str:
    """Categorizes case year into one of the 3 canonical Indian legal eras."""
    if not year or year < 1950:
        return "Pre-1950"
    elif year <= 1975:
        return "1950-1975 (Era 1: Foundational)"
    elif year <= 2000:
        return "1976-2000 (Era 2: Basic Structure & PIL)"
    elif year <= 2020:
        return "2001-2020 (Era 3: Modern Regulatory)"
    else:
        return "2021-2024 (Era 4: Post-COVID & Digital Courts)"

def load_case_metadata(dataset: str) -> dict:
    """Loads case metadata (year, label, split) from segmented JSONL files."""
    metadata = {}
    sources = []
    if dataset in ["single", "combined"]:
        p = CLEAN_DIR / "ildc_single_segmented.jsonl"
        if p.exists():
            sources.append(p)
    if dataset in ["multi", "combined"]:
        p = CLEAN_DIR / "ildc_multi_segmented.jsonl"
        if p.exists():
            sources.append(p)
    if dataset in ["nyaya", "combined"]:
        p = CLEAN_DIR / "nyaya_2021_2024_segmented.jsonl"
        if p.exists():
            sources.append(p)

    for p in sources:
        print(f"Loading case node metadata from: {p.name}...")
        with open(p, mode="r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                cid = d.get("id")
                if not cid:
                    continue
                year = None
                if "_" in cid:
                    try:
                        year = int(cid.split("_")[0])
                    except ValueError:
                        pass
                metadata[cid] = {
                    "year": year,
                    "label": d.get("label", ""),
                    "split": d.get("split", "train"),
                    "node_type": "internal_case"
                }
    return metadata

def build_graph(dataset: str = "combined", sample_size: int = None):
    print("=" * 70)
    print("CiteJustice - Week 3 Task 3: Dynamic Precedent Evolution Graph (DPEG)")
    print(f"Dataset Target: {dataset.upper()}")
    print(f"Output Directory: {DPEG_DIR}")
    print("=" * 70)

    # Determine input classified edge files
    edge_sources = []
    if dataset in ["single", "combined"]:
        p = CLEAN_DIR / "ildc_single_classified_edges.jsonl"
        if p.exists():
            edge_sources.append(p)
    if dataset in ["multi", "combined"]:
        p = CLEAN_DIR / "ildc_multi_classified_edges.jsonl"
        if p.exists():
            edge_sources.append(p)
    if dataset in ["nyaya", "combined"]:
        p = CLEAN_DIR / "nyaya_2021_2024_classified_edges.jsonl"
        if p.exists():
            edge_sources.append(p)

    if not edge_sources:
        print("Error: No classified edge files found in data/clean. Run Task 2 first.")
        sys.exit(1)

    # 1. Load case metadata
    case_meta = load_case_metadata(dataset)
    print(f"Loaded metadata for {len(case_meta):,} internal judgment nodes.\n")

    # 2. Read classified edges
    raw_edges = []
    for p in edge_sources:
        print(f"Reading classified citation edges from: {p.name}...")
        with open(p, mode="r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                raw_edges.append(json.loads(line))
                if sample_size and len(raw_edges) >= sample_size:
                    break
        if sample_size and len(raw_edges) >= sample_size:
            break

    total_input_edges = len(raw_edges)
    print(f"Loaded {total_input_edges:,} citation edges to build graph.\n")

    # 3. Discover all unique nodes (both citing cases and cited precedents)
    node_to_idx = {}
    idx_to_node = []

    def get_or_create_node(node_id: str, default_year: int = None, node_type: str = "cited_precedent"):
        if node_id not in node_to_idx:
            idx = len(idx_to_node)
            node_to_idx[node_id] = idx
            meta = case_meta.get(node_id, {})
            node_obj = {
                "node_index": idx,
                "node_id": node_id,
                "node_type": meta.get("node_type", node_type),
                "year": meta.get("year", default_year),
                "label": meta.get("label", -1),
                "split": meta.get("split", "precedent"),
                "in_degree": 0,
                "out_degree": 0,
                "overruled_count": 0,
                "followed_count": 0,
                "distinguished_count": 0
            }
            idx_to_node.append(node_obj)
            return idx
        return node_to_idx[node_id]

    # Pre-populate internal cases
    for cid in case_meta.keys():
        get_or_create_node(cid, default_year=case_meta[cid]["year"], node_type="internal_case")

    # 4. Construct edge list and update node degree counts
    graph_edges = []
    era_edge_counts = defaultdict(int)
    rel_counts = defaultdict(int)

    for idx, e in enumerate(raw_edges, 1):
        citing_id = e.get("citing_case_id")
        cited_id = e.get("cited_citation")
        if not citing_id or not cited_id:
            continue

        citing_yr = e.get("citing_year")
        cited_yr = e.get("cited_year")

        src_idx = get_or_create_node(citing_id, default_year=citing_yr, node_type="internal_case")
        tgt_idx = get_or_create_node(cited_id, default_year=cited_yr, node_type="cited_precedent")

        relationship = e.get("relationship", "CONSIDERED")
        confidence = float(e.get("confidence", 0.50))
        is_sub = bool(e.get("is_submission", False))
        weight = calculate_edge_weight(relationship, confidence, is_sub)

        # Update node statistics
        idx_to_node[src_idx]["out_degree"] += 1
        idx_to_node[tgt_idx]["in_degree"] += 1

        if relationship == "OVERRULED":
            idx_to_node[tgt_idx]["overruled_count"] += 1
        elif relationship == "FOLLOWED":
            idx_to_node[tgt_idx]["followed_count"] += 1
        elif relationship == "DISTINGUISHED":
            idx_to_node[tgt_idx]["distinguished_count"] += 1

        rel_counts[relationship] += 1
        era = assign_temporal_era(citing_yr)
        era_edge_counts[era] += 1

        graph_edges.append({
            "edge_id": e.get("edge_id", f"edge_{idx:06d}"),
            "source_idx": src_idx,
            "target_idx": tgt_idx,
            "source_id": citing_id,
            "target_id": cited_id,
            "relationship": relationship,
            "weight": weight,
            "confidence": confidence,
            "citing_year": citing_yr,
            "cited_year": cited_yr,
            "temporal_era": era,
            "rhetorical_zone": e.get("rhetorical_zone", "UNSPECIFIED"),
            "is_submission": is_sub
        })

    total_nodes = len(idx_to_node)
    total_edges = len(graph_edges)
    print(f"Graph construction complete: {total_nodes:,} nodes and {total_edges:,} directed edges.\n")

    # 5. Export DPEG Nodes CSV
    nodes_csv = DPEG_DIR / f"dpeg_{dataset}_nodes.csv"
    with open(nodes_csv, mode="w", encoding="utf-8", newline="") as f_nodes:
        fields = ["node_index", "node_id", "node_type", "year", "label", "split", "in_degree", "out_degree", "overruled_count", "followed_count", "distinguished_count"]
        writer = csv.DictWriter(f_nodes, fieldnames=fields)
        writer.writeheader()
        writer.writerows(idx_to_node)
    print(f"[OK] DPEG Nodes CSV saved to: {nodes_csv.name}")

    # 6. Export DPEG Edges CSV
    edges_csv = DPEG_DIR / f"dpeg_{dataset}_edges.csv"
    with open(edges_csv, mode="w", encoding="utf-8", newline="") as f_edges:
        fields = ["edge_id", "source_idx", "target_idx", "source_id", "target_id", "relationship", "weight", "confidence", "citing_year", "cited_year", "temporal_era", "rhetorical_zone", "is_submission"]
        writer = csv.DictWriter(f_edges, fieldnames=fields)
        writer.writeheader()
        writer.writerows(graph_edges)
    print(f"[OK] DPEG Edges CSV saved to: {edges_csv.name}")

    # 7. Export PyG / NetworkX edge_index TSV (source_idx \t target_idx \t weight)
    tsv_path = DPEG_DIR / f"dpeg_{dataset}_edge_list.tsv"
    with open(tsv_path, mode="w", encoding="utf-8") as f_tsv:
        f_tsv.write("source\ttarget\tweight\n")
        for ge in graph_edges:
            f_tsv.write(f"{ge['source_idx']}\t{ge['target_idx']}\t{ge['weight']}\n")
    print(f"[OK] GNN Edge List TSV saved to: {tsv_path.name}")

    # 8. Compute Top Landmark Hubs
    top_cited = sorted(idx_to_node, key=lambda x: x["in_degree"], reverse=True)[:10]
    top_overruled = sorted(idx_to_node, key=lambda x: x["overruled_count"], reverse=True)[:10]

    # 9. Export Comprehensive Graph Statistics JSON
    graph_stats = {
        "dataset": dataset,
        "total_nodes": total_nodes,
        "internal_case_nodes": sum(1 for n in idx_to_node if n["node_type"] == "internal_case"),
        "precedent_landmark_nodes": sum(1 for n in idx_to_node if n["node_type"] == "cited_precedent"),
        "total_directed_edges": total_edges,
        "edge_relationships": dict(rel_counts),
        "temporal_eras": dict(era_edge_counts),
        "graph_density": (total_edges / (total_nodes * (total_nodes - 1))) if total_nodes > 1 else 0,
        "top_10_most_cited_landmarks": [
            {
                "citation": n["node_id"],
                "year": n["year"],
                "total_citations": n["in_degree"],
                "overruled_by": n["overruled_count"],
                "followed_by": n["followed_count"]
            }
            for n in top_cited if n["in_degree"] > 0
        ],
        "top_10_most_overruled_landmarks": [
            {
                "citation": n["node_id"],
                "year": n["year"],
                "total_citations": n["in_degree"],
                "overruled_by": n["overruled_count"]
            }
            for n in top_overruled if n["overruled_count"] > 0
        ]
    }

    stats_json = DPEG_DIR / f"dpeg_{dataset}_stats.json"
    with open(stats_json, mode="w", encoding="utf-8") as f_json:
        json.dump(graph_stats, f_json, indent=2, ensure_ascii=False)
    print(f"[OK] Graph Statistics JSON saved to: {stats_json.name}")

    # Console Summary
    print("\n" + "=" * 50)
    print("DPEG Network Summary:")
    print(f"  Total Graph Nodes (|V|)       : {total_nodes:,}")
    print(f"    - Internal Judgments        : {graph_stats['internal_case_nodes']:,}")
    print(f"    - Historical Precedents     : {graph_stats['precedent_landmark_nodes']:,}")
    print(f"  Total Directed Edges (|E|)    : {total_edges:,}")
    print(f"  Graph Density                 : {graph_stats['graph_density']:.6f}")
    print("\n  Edge Distribution by Relationship:")
    for r, cnt in rel_counts.items():
        pct = (cnt / max(1, total_edges)) * 100
        print(f"    - {r:<14}: {cnt:>6,} edges ({pct:>5.1f}%)")
    print("\n  Edge Distribution by Temporal Era:")
    for era, cnt in sorted(era_edge_counts.items()):
        pct = (cnt / max(1, total_edges)) * 100
        print(f"    - {era:<35}: {cnt:>6,} edges ({pct:>5.1f}%)")
    print("\n  Top 5 Landmark Authority Hubs:")
    for i, lm in enumerate(graph_stats["top_10_most_cited_landmarks"][:5], 1):
        print(f"    {i}. {lm['citation']} ({lm['year']}): cited {lm['total_citations']} times (Overruled: {lm['overruled_by']}, Followed: {lm['followed_by']})")
    print("=" * 50)

def main():
    parser = argparse.ArgumentParser(description="Build the Dynamic Precedent Evolution Graph (DPEG).")
    parser.add_argument("--dataset", choices=["single", "multi", "combined"], default="combined",
                        help="Dataset: 'single', 'multi', or 'combined' (default: combined).")
    parser.add_argument("--sample", type=int, default=None,
                        help="Process only a sample of N edges for fast testing.")
    args = parser.parse_args()

    build_graph(dataset=args.dataset, sample_size=args.sample)

if __name__ == "__main__":
    main()
