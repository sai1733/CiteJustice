"""
scripts/graph/build_graph.py

Week 4 - Task 3: Production Graph Construction & Dual Exporter
Author: Sai Sonawane (Computer Engineering Lead)
Institution: VPKBIET, Baramati

Outputs:
1. data/graph/citation_graph.graphml (Standard Open Format for Gephi, Cytoscape, NetworkX)
2. data/graph/pyg_edge_tensors.npz (High-performance NumPy tensor pack for PyTorch Geometric):
   - edge_index: [2, E] int64 array
   - edge_weight: [E] float32 signed weights [-1.0, +1.0]
   - edge_type: [E] int64 relationship type indices (0=CONSIDERED, 1=DISTINGUISHED, 2=FOLLOWED, 3=OVERRULED)
   - node_ids: [N] canonical string identifiers
   - node_labels: [N] int64 ground truth outcomes (-1 for external landmarks)
   - node_splits: [N] string partition tags (train, dev, test, precedent)
3. data/graph/pyg_node_map.json (ID -> node_index mapping dictionary)
4. data/graph/graph_construction_stats.json (Topological metrics & tensor shapes)

Usage:
    python scripts/graph/build_graph.py
"""

import os
import sys
import csv
import json
import time
from pathlib import Path
import networkx as nx
import numpy as np
import pandas as pd

# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_CLEAN = BASE_DIR / "data" / "clean"
DPEG_DIR = DATA_CLEAN / "dpeg"
GRAPH_DIR = BASE_DIR / "data" / "graph"
GRAPH_DIR.mkdir(parents=True, exist_ok=True)

REL_TO_INT = {
    "CONSIDERED": 0,
    "DISTINGUISHED": 1,
    "FOLLOWED": 2,
    "OVERRULED": 3
}

def build_production_graph():
    print("=" * 75)
    print("CiteJustice - Week 4 Task 3: Production Graph Construction & Exporter")
    print("Constructing NetworkX MultiDiGraph & PyG-Ready Relational Tensors")
    print("=" * 75)

    start_time = time.time()
    nodes_csv = DPEG_DIR / "dpeg_combined_nodes.csv"
    edges_csv = DPEG_DIR / "dpeg_combined_edges.csv"
    cases_jsonl = DATA_CLEAN / "cases.jsonl"

    graphml_path = GRAPH_DIR / "citation_graph.graphml"
    npz_path = GRAPH_DIR / "pyg_edge_tensors.npz"
    node_map_path = GRAPH_DIR / "pyg_node_map.json"
    stats_path = GRAPH_DIR / "graph_construction_stats.json"

    if not nodes_csv.exists() or not edges_csv.exists():
        print("Error: DPEG node or edge CSV missing in data/clean/dpeg/. Run Week 3 build_dpeg.py first.")
        sys.exit(1)

    # ----------------------------------------------------------------------
    # 1. Load Nodes & Metadata
    # ----------------------------------------------------------------------
    print("\n[Stage 1/5] Loading and indexing 66,671 DPEG nodes...")
    df_nodes = pd.read_csv(nodes_csv)
    total_nodes = len(df_nodes)

    # Load rich attributes from cases.jsonl for internal cases
    internal_case_meta = {}
    if cases_jsonl.exists():
        print(f"  Enriching internal cases with features from {cases_jsonl.name}...")
        with open(cases_jsonl, mode="r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                d = json.loads(line)
                cid = d["case_id"]
                internal_case_meta[cid] = {
                    "court_tier": d.get("court_tier", "APEX"),
                    "matter_type": d.get("matter_type") or "UNKNOWN",
                    "section_count": d.get("statutory_entities", {}).get("section_count", 0),
                    "confidence_tier": d.get("outcome", {}).get("confidence_tier", "LOW"),
                    "binary_label": d.get("outcome", {}).get("binary_label", -1),
                    "char_count": d.get("text_features", {}).get("char_count", 0)
                }
        print(f"  ? Enriched {len(internal_case_meta):,} internal case nodes.")

    G = nx.MultiDiGraph()
    node_id_to_idx = {}
    node_idx_to_id = {}
    node_labels = np.full(total_nodes, -1, dtype=np.int64)
    node_splits = []
    node_ids_list = []

    for _, row in df_nodes.iterrows():
        idx = int(row["node_index"])
        cid = str(row["node_id"])
        ntype = str(row["node_type"])
        year = int(row["year"]) if pd.notna(row["year"]) and str(row["year"]).isdigit() else 2000
        split = str(row["split"]) if pd.notna(row["split"]) else "precedent"
        lbl = int(row["label"]) if pd.notna(row["label"]) and str(row["label"]).isdigit() else -1

        node_id_to_idx[cid] = idx
        node_idx_to_id[idx] = cid
        node_labels[idx] = lbl
        node_splits.append(split)
        node_ids_list.append(cid)

        # Base node attributes for GraphML
        node_attrs = {
            "node_index": idx,
            "node_type": ntype,
            "year": year,
            "split": split,
            "label": lbl,
            "in_degree": int(row.get("in_degree", 0)),
            "out_degree": int(row.get("out_degree", 0)),
            "overruled_count": int(row.get("overruled_count", 0)),
            "followed_count": int(row.get("followed_count", 0)),
            "distinguished_count": int(row.get("distinguished_count", 0))
        }

        # Merge rich attributes if internal
        if cid in internal_case_meta:
            extra = internal_case_meta[cid]
            node_attrs["court_tier"] = extra["court_tier"]
            node_attrs["matter_type"] = extra["matter_type"]
            node_attrs["section_count"] = extra["section_count"]
            node_attrs["confidence_tier"] = extra["confidence_tier"]

        G.add_node(cid, **node_attrs)

    print(f"  ? Added {G.number_of_nodes():,} nodes to NetworkX MultiDiGraph.")

    # ----------------------------------------------------------------------
    # 2. Load Edges & Build Tensors
    # ----------------------------------------------------------------------
    print("\n[Stage 2/5] Loading and wiring 94,672 DPEG directed edges...")
    df_edges = pd.read_csv(edges_csv)
    total_edges = len(df_edges)

    src_indices = []
    tgt_indices = []
    edge_weights = []
    edge_types = []

    for _, row in df_edges.iterrows():
        src_id = str(row["source_id"])
        tgt_id = str(row["target_id"])
        src_idx = int(row["source_idx"])
        tgt_idx = int(row["target_idx"])
        rel = str(row["relationship"]).upper()
        w = float(row["weight"])
        conf = float(row["confidence"])
        citing_year = int(row["citing_year"]) if pd.notna(row["citing_year"]) else 2000
        cited_year = int(row["cited_year"]) if pd.notna(row["cited_year"]) else 2000
        is_sub = bool(row.get("is_submission", False))
        era = str(row.get("temporal_era", ""))

        src_indices.append(src_idx)
        tgt_indices.append(tgt_idx)
        edge_weights.append(w)
        edge_types.append(REL_TO_INT.get(rel, 0))

        # Add directed edge to NetworkX graph
        G.add_edge(
            src_id,
            tgt_id,
            key=str(row.get("edge_id", f"{src_id}_{tgt_id}")),
            relationship=rel,
            weight=w,
            confidence=conf,
            citing_year=citing_year,
            cited_year=cited_year,
            is_submission=is_sub,
            temporal_era=era
        )

    print(f"  ? Added {G.number_of_edges():,} edges to NetworkX MultiDiGraph.")

    # ----------------------------------------------------------------------
    # 3. Export High-Performance PyG Tensor Pack (.npz & .json)
    # ----------------------------------------------------------------------
    print("\n[Stage 3/5] Exporting PyG tensor pack for Graph Neural Network training...")
    edge_index_arr = np.array([src_indices, tgt_indices], dtype=np.int64)
    edge_weight_arr = np.array(edge_weights, dtype=np.float32)
    edge_type_arr = np.array(edge_types, dtype=np.int64)
    node_ids_arr = np.array(node_ids_list, dtype=object)
    node_splits_arr = np.array(node_splits, dtype=object)

    np.savez_compressed(
        npz_path,
        edge_index=edge_index_arr,
        edge_weight=edge_weight_arr,
        edge_type=edge_type_arr,
        node_ids=node_ids_arr,
        node_labels=node_labels,
        node_splits=node_splits_arr
    )
    print(f"  ? Saved PyG tensor pack: {npz_path} ({os.path.getsize(npz_path) / (1024*1024):.2f} MB)")
    print(f"    - edge_index shape:  {edge_index_arr.shape} (int64)")
    print(f"    - edge_weight shape: {edge_weight_arr.shape} (float32, range: [{edge_weight_arr.min():.2f}, {edge_weight_arr.max():.2f}])")
    print(f"    - edge_type shape:   {edge_type_arr.shape} (int64, classes: 0=CONSIDERED, 1=DISTINGUISHED, 2=FOLLOWED, 3=OVERRULED)")

    with open(node_map_path, mode="w", encoding="utf-8") as f:
        json.dump(node_id_to_idx, f)
    print(f"  ? Saved canonical node mapping dictionary: {node_map_path} ({len(node_id_to_idx):,} mappings)")

    # ----------------------------------------------------------------------
    # 4. Export GraphML for Visualization (Gephi / Cytoscape)
    # ----------------------------------------------------------------------
    print("\n[Stage 4/5] Exporting GraphML specification for Gephi / Cytoscape visualizer...")
    t0 = time.time()
    nx.write_graphml(G, graphml_path, encoding="utf-8")
    print(f"  ? Exported GraphML: {graphml_path} ({os.path.getsize(graphml_path) / (1024*1024):.2f} MB in {time.time() - t0:.2f}s)")

    # ----------------------------------------------------------------------
    # 5. Compute Graph Topology & Export Telemetry Stats
    # ----------------------------------------------------------------------
    print("\n[Stage 5/5] Computing graph density and connectivity metrics...")
    num_nodes = G.number_of_nodes()
    num_edges = G.number_of_edges()
    density = num_edges / (num_nodes * (num_nodes - 1)) if num_nodes > 1 else 0

    in_degrees = [d for _, d in G.in_degree()]
    out_degrees = [d for _, d in G.out_degree()]
    isolates = list(nx.isolates(G))
    isolated_count = len(isolates)

    graph_stats = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "graph_type": "MultiDiGraph",
        "total_nodes": num_nodes,
        "internal_case_nodes": len(df_nodes[df_nodes["node_type"] == "internal_case"]),
        "cited_precedent_nodes": len(df_nodes[df_nodes["node_type"] == "cited_precedent"]),
        "total_directed_edges": num_edges,
        "graph_density": float(f"{density:.8f}"),
        "isolated_nodes_count": isolated_count,
        "isolated_nodes_pct": round((isolated_count / num_nodes) * 100, 2),
        "mean_in_degree": round(float(np.mean(in_degrees)), 2),
        "median_in_degree": float(np.median(in_degrees)),
        "max_in_degree": int(np.max(in_degrees)),
        "mean_out_degree": round(float(np.mean(out_degrees)), 2),
        "median_out_degree": float(np.median(out_degrees)),
        "max_out_degree": int(np.max(out_degrees)),
        "pyg_tensor_shapes": {
            "edge_index": list(edge_index_arr.shape),
            "edge_weight": list(edge_weight_arr.shape),
            "edge_type": list(edge_type_arr.shape),
            "node_labels": list(node_labels.shape)
        },
        "relationship_counts": {
            "CONSIDERED": int((edge_type_arr == 0).sum()),
            "DISTINGUISHED": int((edge_type_arr == 1).sum()),
            "FOLLOWED": int((edge_type_arr == 2).sum()),
            "OVERRULED": int((edge_type_arr == 3).sum())
        }
    }

    with open(stats_path, mode="w", encoding="utf-8") as f:
        json.dump(graph_stats, f, indent=2)
    print(f"  ? Saved construction stats: {stats_path}")

    elapsed = time.time() - start_time
    print("\n" + "=" * 75)
    print("TASK 3 COMPLETED SUCCESSFULLY")
    print(f"Total Nodes:                {num_nodes:,}")
    print(f"Total Directed Edges:       {num_edges:,}")
    print(f"GraphML Visualization File: {graphml_path} ({os.path.getsize(graphml_path) / (1024*1024):.2f} MB)")
    print(f"PyG Relational Tensor Pack: {npz_path} ({os.path.getsize(npz_path) / (1024*1024):.2f} MB)")
    print(f"Node Mapping Dictionary:    {node_map_path}")
    print(f"Execution Time:             {elapsed:.2f} seconds")
    print("=" * 75)

if __name__ == "__main__":
    build_production_graph()
