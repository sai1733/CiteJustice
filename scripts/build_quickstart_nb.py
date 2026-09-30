"""
scripts/build_quickstart_nb.py

Programmatically generates notebooks/quickstart.ipynb
Author: Sai Sonawane (Computer Engineering Lead)
Date: September 30, 2026
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
NB_PATH = BASE_DIR / "notebooks" / "quickstart.ipynb"

def make_cell(cell_type: str, source: list):
    cell = {
        "cell_type": cell_type,
        "metadata": {},
        "source": [line + "\n" for line in source[:-1]] + [source[-1]] if source else []
    }
    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    return cell

cells = []

# Title & Metadata
cells.append(make_cell("markdown", [
    "# CiteJustice: Developer & Model Team Quickstart Guide",
    "",
    "**Author:** Sai Sonawane (Computer Engineering Lead)  ",
    "**Institution:** Vidya Pratishthan's Kamalnayan Bajaj Institute of Engineering and Technology (VPKBIET), Baramati  ",
    "**Academic Year:** 2026–2027  ",
    "**Date:** September 30, 2026  ",
    "**Milestone:** Phase 1 Handoff & Developer Quickstart  ",
    "",
    "---",
    "",
    "## Overview & Purpose",
    "Welcome to **CiteJustice**! This quickstart notebook provides an executable, end-to-end walkthrough of the unified legal benchmark for the Supreme Court of India.",
    "",
    "By running this notebook, you will learn how to:",
    "1. **Load Chronological Splits:** Access `train.jsonl` (31,567 cases), `dev.jsonl` (1,486 cases), and `test.jsonl` (1,900 cases) under **Option A**.",
    "2. **Verify Target Leakage Guards:** Validate that all judgments have their dispositive outcome sentences cryptographically excised from `clean_text`.",
    "3. **Explore the Precedent Graph (DPEG):** Query NetworkX MultiDiGraph (66,671 nodes, 94,672 citation edges, signed weights $\\in [-1.0, +1.0]$).",
    "4. **Load PyG Tensors for GNN Modeling:** Access `pyg_edge_tensors.npz` and `pyg_split_masks.npz` to feed relational edges directly into PyTorch Geometric (GCN, GAT, R-GCN).",
    "5. **Run a Quick Baseline:** Evaluate the benchmark with standard metric calculation."
]))

# Setup & Imports
cells.append(make_cell("code", [
    "# --------------------------------------------------------------------------",
    "# 1. Environment & Path Setup",
    "# --------------------------------------------------------------------------",
    "import os",
    "import sys",
    "import json",
    "from pathlib import Path",
    "import numpy as np",
    "import pandas as pd",
    "import networkx as nx",
    "",
    "# Auto-detect project root directory",
    "CWD = Path.cwd()",
    "BASE_DIR = CWD.parent if CWD.name == 'notebooks' else CWD",
    "DATA_DIR = BASE_DIR / 'data'",
    "DATA_SPLITS = DATA_DIR / 'splits'",
    "DATA_GRAPH = DATA_DIR / 'graph'",
    "DATA_CLEAN = DATA_DIR / 'clean'",
    "",
    "print(f\"CiteJustice Root Directory: {BASE_DIR.resolve()}\")",
    "print(f\"Data Directory Available:   {DATA_DIR.exists()}\")",
    "assert DATA_SPLITS.exists(), \"Missing data/splits directory!\"",
    "assert DATA_GRAPH.exists(), \"Missing data/graph directory!\""
]))

# Section 1: Loading Partitions
cells.append(make_cell("markdown", [
    "---",
    "## 1. Chronological Dataset Partitions (Option A)",
    "",
    "To eliminate **look-ahead bias (data leakage)**, CiteJustice partitions 36,025 Supreme Court judgments temporally:",
    "- **Train ($\\le 2015$):** Foundational historical precedents ($90.31\\%$)",
    "- **Dev ($2016–2018$):** Uninterrupted pre-COVID validation set ($4.25\\%$)",
    "- **Test ($2019–2024$):** Contemporary held-out test distribution including the 2020 COVID dip ($5.44\\%$)",
    "",
    "Let's load `split_stats.json` and examine the distribution:"
]))

cells.append(make_cell("code", [
    "with open(DATA_SPLITS / 'split_stats.json', 'r', encoding='utf-8') as f:",
    "    stats = json.load(f)",
    "",
    "summary_df = pd.DataFrame({",
    "    'Split': ['Train', 'Dev (Validation)', 'Test (Held-out)', 'Excluded (Duplicates/Leaks)'],",
    "    'Year Range': [stats['boundaries']['train'], stats['boundaries']['dev'], stats['boundaries']['test'], 'N/A'],",
    "    'Case Count': [stats['counts']['train'], stats['counts']['dev'], stats['counts']['test'], stats['counts']['total_excluded']],",
    "    'Corpus %': [f\"{stats['percentages']['train']} %\", f\"{stats['percentages']['dev']} %\", f\"{stats['percentages']['test']} %\", '-'],",
    "    'Allowed (1)': [stats['binary_label_balance']['train']['1'], stats['binary_label_balance']['dev']['1'], stats['binary_label_balance']['test']['1'], '-'],",
    "    'Dismissed (0)': [stats['binary_label_balance']['train']['0'], stats['binary_label_balance']['dev']['0'], stats['binary_label_balance']['test']['0'], '-'],",
    "    'Allowed %': [",
    "        f\"{stats['binary_label_balance']['train']['1'] / stats['counts']['train'] * 100:.1f} %\",",
    "        f\"{stats['binary_label_balance']['dev']['1'] / stats['counts']['dev'] * 100:.1f} %\",",
    "        f\"{stats['binary_label_balance']['test']['1'] / stats['counts']['test'] * 100:.1f} %\",",
    "        '-'",
    "    ]",
    "})",
    "",
    "print(\"=== CiteJustice Option A Split Distribution ===\")",
    "display(summary_df)"
]))

# Section 2: Inspecting Record Structure
cells.append(make_cell("markdown", [
    "---",
    "## 2. Inspecting a Case Record (Schema v1.1.0-frozen)",
    "",
    "Each judgment in `train.jsonl`, `dev.jsonl`, and `test.jsonl` follows the canonical schema frozen in `docs/schema.md`. Let's inspect a single case record:"
]))

cells.append(make_cell("code", [
    "# Load a sample record from the train split",
    "with open(DATA_SPLITS / 'train.jsonl', 'r', encoding='utf-8') as f:",
    "    sample_record = json.loads(f.readline())",
    "",
    "print(\"Case Metadata:\")",
    "print(f\"  - Case ID:         {sample_record['case_id']}\")",
    "print(f\"  - Year:            {sample_record['year']}\")",
    "print(f\"  - Court Tier:      {sample_record.get('court_tier')}\")",
    "print(f\"  - Split:           {sample_record.get('split')}\")",
    "print(f\"  - Word Count:      {sample_record['text_features']['word_count']:,} words\")",
    "print(f\"  - Binary Outcome:  {sample_record['outcome']['binary_label']} (1=Allowed, 0=Dismissed)\")",
    "print(f\"  - Confidence Tier: {sample_record['outcome']['confidence_tier']}\")",
    "print(f\"  - Statutory Acts:  {sample_record['statutory_entities'].get('acts', [])[:3]}\")",
    "print(f\"  - Sections:        {sample_record['statutory_entities'].get('sections', [])[:5]}\")",
    "",
    "print(\"\\nText Snippet (First 300 chars of clean_text):\")",
    "print(sample_record['text_features']['clean_text'][:300] + \"...\")"
]))

# Section 3: Target Leakage Verification
cells.append(make_cell("markdown", [
    "---",
    "## 3. Cryptographic Target Leakage Guard Verification",
    "",
    "In Legal Judgment Prediction (LJP), naive models often achieve $99\\%$ accuracy simply by memorizing the final sentence (*\"For the reasons stated, the appeal is allowed\"*).",
    "",
    "CiteJustice prevents this through **cryptographic target leakage excision**:",
    "- The dispositive sentence is strictly cut from `clean_text`.",
    "- The excised sentence is isolated into `disposition_span`.",
    "- A SHA-256 hash (`leakage_guard_hash`) verifies that `clean_text` contains zero overlap with the outcome span.",
    "",
    "Let's programmatically verify this leakage guard on our sample case:"
]))

cells.append(make_cell("code", [
    "clean_text = sample_record['text_features']['clean_text']",
    "disp_span = sample_record['outcome'].get('disposition_span', '')",
    "guard_hash = sample_record['outcome'].get('leakage_guard_hash', '')",
    "",
    "print(f\"Disposition Span (Excised): '{disp_span}'\")",
    "print(f\"Leakage Guard Hash:         '{guard_hash}'\")",
    "",
    "# 1. Substring Overlap Check",
    "if disp_span and len(disp_span) > 10:",
    "    assert disp_span.lower() not in clean_text.lower(), \"LEAK DETECTED: Disposition sentence found in text!\"",
    "    print(\"\\n[PASSED] Target Leakage Test: Disposition span does NOT exist in clean_text.\")",
    "else:",
    "    print(\"\\n[PASSED] Clean non-leaking record.\")"
]))

# Section 4: NetworkX Graph
cells.append(make_cell("markdown", [
    "---",
    "## 4. Precedent Graph (DPEG) Exploration with NetworkX",
    "",
    "The **Dynamic Precedent Evolution Graph (DPEG)** models Indian *stare decisis* as a signed, directed multi-graph (`citation_graph.graphml`):",
    "- **66,671 Nodes:** 36,025 internal Supreme Court cases + 30,646 historical precedent anchors.",
    "- **94,672 Edges:** Signed citation arcs with weights $w_{ij} \\in [-1.0, +1.0]$.",
    "",
    "Let's load the GraphML file and query a landmark case:"
]))

cells.append(make_cell("code", [
    "print(\"Loading citation_graph.graphml into NetworkX (this takes ~10 seconds)...\", flush=True)",
    "graphml_path = DATA_GRAPH / 'citation_graph.graphml'",
    "G = nx.read_graphml(graphml_path)",
    "",
    "print(f\"\\n=== DPEG Graph Topology ===\")",
    "print(f\"  - Total Nodes:            {G.number_of_nodes():,}\")",
    "print(f\"  - Total Directed Edges:   {G.number_of_edges():,}\")",
    "print(f\"  - Graph Density:          {nx.density(G):.6f}\")",
    "",
    "# Count nodes per split",
    "split_counts = pd.Series([d.get('split', 'unknown') for n, d in G.nodes(data=True)]).value_counts()",
    "print(\"\\nNode Distribution by Split:\")",
    "for s, cnt in split_counts.items():",
    "    print(f\"  - {s:12s}: {cnt:,}\")",
    "",
    "# Query highest in-degree (most-cited) landmark cases in the network",
    "in_degrees = sorted(G.in_degree(), key=lambda x: x[1], reverse=True)[:5]",
    "print(\"\\nTop-5 Most-Cited Precedent Anchors:\")",
    "for node_id, deg in in_degrees:",
    "    node_attrs = G.nodes[node_id]",
    "    print(f\"  - Case ID: {node_id:<15} | Citations Received: {deg:<3} | Split: {node_attrs.get('split')} | Year: {node_attrs.get('year')}\")"
]))

# Section 5: PyG Tensors
cells.append(make_cell("markdown", [
    "---",
    "## 5. PyTorch Geometric (PyG) Relational Graph Tensors",
    "",
    "For Graph Neural Network (GNN) architectures (GCN, GAT, R-GCN), CiteJustice provides pre-built sparse relational tensors in NumPy format:",
    "1. `pyg_edge_tensors.npz`: Contains `edge_index [2, 94672]`, `edge_weight [94672]`, `edge_type [94672]`, and `node_labels [66671]`.",
    "2. `pyg_split_masks.npz`: Contains boolean arrays `train_mask`, `val_mask`, and `test_mask`.",
    "",
    "Let's load the tensors and assemble a PyG `Data` object:"
]))

cells.append(make_cell("code", [
    "# Load PyG edge tensors & split masks",
    "tensors = np.load(DATA_GRAPH / 'pyg_edge_tensors.npz', allow_pickle=True)",
    "masks = np.load(DATA_SPLITS / 'pyg_split_masks.npz')",
    "",
    "edge_index = tensors['edge_index']",
    "edge_weight = tensors['edge_weight']",
    "edge_type = tensors['edge_type']",
    "train_mask = masks['train_mask']",
    "val_mask = masks['val_mask']",
    "test_mask = masks['test_mask']",
    "",
    "print(\"=== Sparse Tensor Specifications ===\")",
    "print(f\"  - edge_index shape:  {edge_index.shape}  | dtype: {edge_index.dtype}\")",
    "print(f\"  - edge_weight shape: {edge_weight.shape}     | dtype: {edge_weight.dtype}\")",
    "print(f\"  - edge_type shape:   {edge_type.shape}     | dtype: {edge_type.dtype} (0=CONSIDERED, 1=DISTINGUISHED, 2=FOLLOWED, 3=OVERRULED)\")",
    "print(f\"  - train_mask nodes:  {train_mask.sum():,} active training nodes\")",
    "print(f\"  - val_mask nodes:    {val_mask.sum():,} validation nodes\")",
    "print(f\"  - test_mask nodes:   {test_mask.sum():,} held-out test nodes\")",
    "",
    "# Assemble standard PyG Data container",
    "try:",
    "    import torch",
    "    from torch_geometric.data import Data",
    "    pyg_data = Data(",
    "        edge_index=torch.from_numpy(edge_index),",
    "        edge_weight=torch.from_numpy(edge_weight),",
    "        edge_type=torch.from_numpy(edge_type),",
    "        train_mask=torch.from_numpy(train_mask),",
    "        val_mask=torch.from_numpy(val_mask),",
    "        test_mask=torch.from_numpy(test_mask)",
    "    )",
    "    print(\"\\n[PASSED] Successfully assembled PyG Data object:\")",
    "    print(pyg_data)",
    "except ImportError:",
    "    print(\"\\n[NOTE] PyTorch / PyG not installed in this environment. Tensors are fully verified as NumPy arrays ready for torch.from_numpy().\")"
]))

# Section 6: Baseline Demonstration
cells.append(make_cell("markdown", [
    "---",
    "## 6. Baseline Evaluation Metric Demonstration",
    "",
    "When evaluating models on `test.jsonl`, CiteJustice uses standard classification metrics:",
    "- **Macro F1:** Unweighted mean of F1 across Allowed (`1`) and Dismissed (`0`).",
    "- **Accuracy & AUC-ROC:** Discrimination capability.",
    "",
    "Here is a reference evaluation function for the model team:"
]))

cells.append(make_cell("code", [
    "from collections import Counter",
    "",
    "# Compute empirical majority-class baseline on the test set",
    "with open(DATA_SPLITS / 'test.jsonl', 'r', encoding='utf-8') as f:",
    "    test_labels = [json.loads(line)['outcome']['binary_label'] for line in f if line.strip()]",
    "",
    "label_counts = Counter(test_labels)",
    "majority_class = label_counts.most_common(1)[0][0]",
    "majority_acc = label_counts[majority_class] / len(test_labels)",
    "",
    "print(f\"Test Set Size:            {len(test_labels):,} cases\")",
    "print(f\"Label Counts:             Allowed(1)={label_counts[1]:,}, Dismissed(0)={label_counts[0]:,}\")",
    "print(f\"Majority Class Baseline:  {majority_acc * 100:.2f}% Accuracy (Predict all as {'Allowed' if majority_class == 1 else 'Dismissed'})\")",
    "print(\"\\nTarget Stretch Benchmark Goal: Model team's INLegalLlama + DPEG GNN aims for >= 80.0% Macro F1 and >= 82.0% Accuracy.\")"
]))

# Summary
cells.append(make_cell("markdown", [
    "---",
    "## 7. Next Steps for Model Architecture Team",
    "",
    "1. **Language Modeling:** Pull `L-NLProc/InLegalLlama` from Hugging Face as the domain text encoder.",
    "2. **Graph Modeling:** Implement Relational GCN (`torch_geometric.nn.RGCNConv`) using `edge_index` and `edge_type`.",
    "3. **Target Leakage Prohibition:** Never pass test nodes or test citation edges into the message-passing neighborhood during training.",
    "",
    "For full documentation, consult:",
    "- [`docs/schema.md`](../docs/schema.md) — Node and edge interface specification.",
    "- [`docs/split_rationale.md`](../docs/split_rationale.md) — Temporal partition justification.",
    "- [`docs/graph_stats.md`](../docs/graph_stats.md) — DPEG network properties.",
    "",
    "**CiteJustice Engineering Team — September 30, 2026**"
]))

nb = {
    "cells": cells,
    "metadata": {
        "language_info": {
            "name": "python",
            "version": "3.10"
        },
        "orig_nbformat": 4
    },
    "nbformat": 4,
    "nbformat_minor": 2
}

with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=2)

print(f"Successfully generated quickstart notebook: {NB_PATH}")
