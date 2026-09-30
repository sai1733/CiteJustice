# CiteJustice Phase 1 to Phase 2: Formal Model Team Handoff Specification

**Project:** CiteJustice — Automated Legal Judgment Prediction & Dynamic Precedent Evolution Graph for Indian Courts  
**Author:** Sai Sonawane (Computer Engineering Lead)  
**Institution:** Vidya Pratishthan's Kamalnayan Bajaj Institute of Engineering and Technology (VPKBIET), Baramati  
**Date:** September 30, 2026  
**Status:** **Formal Phase 1 Closeout & Phase 2 Kickoff Specification**  

---

## 1. Executive Summary & Handoff Objective

This document marks the formal completion of **Phase 1 (Data & Graph Engineering)** and provides the operational handoff contract for the **Model Architecture Sub-team (Phase 2)**. 

All raw judicial records have been cleaned, deduplicated, verified against target leakage, and partitioned into chronological sets. The relational Precedent Graph (DPEG) has been structured into sparse PyTorch Geometric (PyG) tensors and GraphML specifications.

---

## 2. Handoff Deliverables Checklist

The model team receives the verified **CiteJustice Production Data Pack**:

| Artifact Group | File Path | Format | Size | Description / Function |
| :--- | :--- | :---: | :---: | :--- |
| **Training Split** | `data/splits/train.jsonl` | JSONL | 1.05 GB | **31,567 judgments** (≤ 2015) for LLM & GNN training |
| **Validation Split** | `data/splits/dev.jsonl` | JSONL | 46.0 MB | **1,486 judgments** ($2016–2018$) for hyperparameter tuning & early stopping |
| **Test Split** | `data/splits/test.jsonl` | JSONL | 39.7 MB | **1,900 held-out judgments** ($2019–2024$) for final benchmark evaluation |
| **Split Statistics** | `data/splits/split_stats.json` | JSON | 2.8 KB | Machine-readable telemetry and class distributions |
| **PyG Split Masks** | `data/splits/pyg_split_masks.npz` | NPZ | 120 KB | Boolean arrays: `train_mask`, `val_mask`, `test_mask` |
| **Relational Tensors**| `data/graph/pyg_edge_tensors.npz` | NPZ | 0.52 MB | `edge_index [2, 94672]`, `edge_weight`, `edge_type` |
| **Node Mapping Dict** | `data/graph/pyg_node_map.json` | JSON | 1.43 MB | Canonical mapping of 66,671 `case_id` strings to tensor row indices |
| **Precedent Graph** | `data/graph/citation_graph.graphml` | GraphML | 56.7 MB | NetworkX & Gephi signed multi-graph |
| **Quickstart Guide** | [`notebooks/quickstart.ipynb`](../notebooks/quickstart.ipynb) | Jupyter | 15 Cells | Runnable 5-minute onboarding notebook |

---

## 3. Mandatory Modeling Rules of Engagement

The Model Architecture team must adhere to four strict technical constraints:

### Rule 1: Strict Training Isolation
* **Directive:** Model fine-tuning (e.g. INLegalLlama, RoBERTa-Legal) and GNN training must draw samples **exclusively** from `data/splits/train.jsonl` (or nodes where `train_mask == True`).
* **Validation:** All early stopping, learning rate schedulers, and prompt variations must be monitored strictly on `data/splits/dev.jsonl` (or `val_mask`).
* **Test Isolation:** The test partition (`data/splits/test.jsonl` / `test_mask`) must be evaluated **exactly once** for final reporting.

### Rule 2: Prohibition of Inductive Future Leakage in GNNs
* **Directive:** When performing graph message passing (e.g. using `torch_geometric.nn.RGCNConv` or `GATConv`), models must **never pass edges originating from test cases into the training neighborhood**.
* **Enforcement:** Use inductive subgraph masking:
  ```python
  subgraph_edge_index, subgraph_edge_weight = subgraph(
      subset=train_mask, 
      edge_index=edge_index, 
      edge_attr=edge_weight, 
      relabel_nodes=True
  )
  ```

### Rule 3: Target Leakage Verification
* **Directive:** Models must ingest `text_features.clean_text` for factual representations. Under no circumstances should `disposition_span` be input to the encoder during prediction.

### Rule 4: Handling Length Skew & Edge Cases
* **Constitutional Matters (>4,096 tokens):** Do not discard long judgments. Extract either rhetorical facts (`facts` zone) or feed text embeddings through the DPEG graph hierarchy.
* **Ultra-Short Orders (<50 tokens):** Apply length-masking or filter procedural chamber orders during rhetorical zone evaluation.


---

## 4. Model Team Operational Scope & Checkpoints (Phases 1 & 2)

The Model Architecture team is responsible for executing **Phase 1** and **Phase 2** of the master development plan.

### Immediate Task 1: Baseline Models (Phase 1)
* **Dataset Files:** `data/splits/train.jsonl` (31,567 cases), `data/splits/dev.jsonl` (1,486 cases), `data/splits/test.jsonl` (1,900 cases).
* **Input Fields:** `text_features.clean_text` (or rhetorical zones `facts` / `court_analysis`).
* **Target Label:** `outcome.binary_label` (`1` = Allowed, `0` = Dismissed).
* **Work to Perform:**
  1. Verify data and split shapes via `notebooks/quickstart.ipynb`.
  2. Implement lexical baselines (TF-IDF + Logistic Regression / LightGBM) to establish the empirical floor.
  3. Evaluate legal deep learning baselines using open-source models:
     * `law-ai/InLegalBERT` (Indian legal domain adapted encoder).
     * Hierarchical Longformer / LED for long judgments.
     * Zero-Shot / Prompted `law-ai/INLegalLlama` (7B generative legal LLM in 4-bit) to benchmark raw LLM prediction vs graph models.
  4. Evaluate on `test.jsonl` and record Accuracy, Macro F1, AUC-ROC, and Matthews Correlation Coefficient (MCC).

### Immediate Task 2: Relational Graph & Multi-Modal Fusion (Phase 2)
* **Dataset Files:** `data/graph/pyg_edge_tensors.npz`, `data/graph/pyg_node_map.json`, `data/splits/pyg_split_masks.npz`.
* **Tensor Specifications:**
  * `edge_index`: Shape `[2, 94672]` across 66,671 nodes.
  * `edge_type`: Categorical integers (`0: CONSIDERED`, `1: DISTINGUISHED`, `2: FOLLOWED`, `3: OVERRULED`).
  * `edge_weight`: Continuous signed float weights in $[-0.98, +0.95]$.
* **Work to Perform:**
  1. Build a 2-layer Relational Graph Convolutional Network (`torch_geometric.nn.RGCNConv`) using edge types and continuous signed weights.
  2. Implement dual-stream late fusion: concatenate 768-dim `InLegalBERT` text embeddings with 256-dim PyG graph node embeddings through a gated MLP.
  3. Generate edge-level explainability attributions using `Captum` (Integrated Gradients) to trace precedent influence.
  4. Conduct ablation studies (Text-only vs. Graph-only vs. Multi-modal; Unweighted vs. Signed weights; Random vs. Option A chronological split).
  5. Compile benchmark tables for **Research Paper 1**.

---

```
╔════════════════════════════════════════════════════════════════════════════════════════════════╗
║                   🛑 CRITICAL CHECKPOINT: MODEL TEAM STOPS & WAITS FOR SAI                   ║
╠════════════════════════════════════════════════════════════════════════════════════════════════╣
║ 1. Upon completing Phase 2 evaluation, the Model Team MUST STOP and place code on standby.     ║
║ 2. The Model Team MUST NOT attempt to scrape, parse, or download High Court data.              ║
║ 3. Log all V1 test metrics and compile results for Paper 1 (Supreme Court Benchmark).          ║
║ 4. SAI SONAWANE takes over to build, clean, namespace, and bridge the V2 Multi-Tier Dataset.   ║
║ 5. The Model Team resumes ONLY in Phase 4 when Sai delivers `CiteJustice_Phase2_V2_Handoff`.   ║
╚════════════════════════════════════════════════════════════════════════════════════════════════╝
```

*For the complete 6-phase master architecture, consult the authoritative documentation in [`docs/master_roadmap.md`](master_roadmap.md).*

---

## 5. Formal Sign-off

With the delivery of this specification, [`docs/preprocessing.md`](preprocessing.md), [`docs/master_roadmap.md`](master_roadmap.md), and [`notebooks/quickstart.ipynb`](../notebooks/quickstart.ipynb), Phase 1 is formally declared complete and handed off to Phase 2.

**Sai Sonawane**  
Computer Engineering Lead, CiteJustice Project  
VPKBIET, Baramati  
September 30, 2026

