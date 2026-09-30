---
annotations_creators:
- machine-derived
- expert-verified
language:
- en
language_creators:
- found
license:
- cc-by-4.0
multilinguality:
- monolingual
pretty_name: CiteJustice Master Legal Benchmark (1950-2024 Supreme Court Corpus)
size_categories:
- 10K<n<100K
source_datasets:
- ildc_single
- ildc_multi
- nyayaanumana_2020_2024
tags:
- legal
- legal-judgment-prediction
- supreme-court-of-india
- citation-graph
- dynamic-precedent-evolution
- temporal-benchmark
task_categories:
- text-classification
- graph-ml
task_ids:
- binary-classification
- node-classification
- link-prediction
---

# Dataset Card: CiteJustice Master Benchmark (1950–2024)

**Curator & Lead:** Sai Sonawane (Computer Engineering Lead)  
**Institution:** Vidya Pratishthan's Kamalnayan Bajaj Institute of Engineering and Technology (VPKBIET), Baramati  
**Date:** September 30, 2026  
**Artifact Repository:** `data/splits/`, `data/clean/cases.jsonl`, `data/graph/`  

---

## 1. Dataset Summary

The **CiteJustice Master Benchmark** is a unified, leak-free, multimodal legal benchmark for the Supreme Court of India spanning 74 years of jurisprudence (1950–2024). It unites **36,025 master judgments** with a signed, directed **Dynamic Precedent Evolution Graph (DPEG)** of **66,671 legal entities** and **94,672 citation edges**.

* **Underlying Jurisdiction:** Supreme Court of India (Apex Court)
* **Temporal Coverage:** 1950 – 2024 (Continuous 74-Year Historical Span)
* **Total Master Cases:** 36,025 judgments
* **Total Clean Active Cases:** 34,953 judgments (after excluding 1,068 exact duplicates and 4 cross-boundary leaks)
* **Precedent Network Size:** 66,671 Nodes | 94,672 Directed Edges | 4 Relation Types
* **License:** Creative Commons Attribution 4.0 International (CC-BY-4.0)

---

## 2. Chronological Partitions (Option A)

CiteJustice strictly prohibits randomized splitting to eliminate **look-ahead bias (time machine leakage)**. All cases are partitioned chronologically:

| Split | Year Range | Case Count | Corpus Share | Allowed (`1`) | Dismissed (`0`) | Purpose |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Train** | **1950 – 2015** | **31,567** | **90.31%** | 13,241 (41.9%) | 18,326 (58.1%) | Foundational training for GNNs & LLMs |
| **Dev (Val)** | **2016 – 2018** | **1,486** | **4.25%** | 601 (40.4%) | 885 (59.6%) | Hyperparameter tuning & prompt optimization |
| **Test (Held-out)** | **2019 – 2024** | **1,900** | **5.44%** | 1,102 (58.0%) | 798 (42.0%) | Modern evaluation (Pre-COVID, COVID, Post-COVID) |
| **Excluded** | Duplicates/Leaks | **1,072** | — | — | — | Audit trail preserved in CSV |

---

## 3. Data Schema & Feature Groups (`Schema v1.1.0-frozen`)

Each record in `cases.jsonl` contains 5 modular groups:
1. **Core Metadata:** `case_id`, `court`, `court_tier`, `year`, `bench_size`, `split`.
2. **Text Features:** Cleaned rhetorical text (`clean_text`), word count, character count.
3. **Statutory Entities:** Canonical Acts and Sections mapped against Indian Penal Code, CrPC, Constitution, etc.
4. **Graph Features:** DPEG node index (`node_idx`), in-degree, out-degree, temporal era, and outgoing precedent citations.
5. **Outcome & Cryptographic Guard:** Ground truth label (`binary_label`, `ternary_label`), confidence tier, isolated `disposition_span`, and SHA-256 `leakage_guard_hash`.

---

## 4. Graph Neural Network Artifacts (PyTorch Geometric)

* **GraphML:** `data/graph/citation_graph.graphml` (56.7 MB) with `split` attributes embedded on every node.
* **PyG Relational Tensors:** `data/graph/pyg_edge_tensors.npz` (`edge_index [2, 94672]`, `edge_weight [94672]`, `edge_type [94672]`).
* **Split Masks:** `data/splits/pyg_split_masks.npz` (`train_mask`, `val_mask`, `test_mask`).

---

## 5. Usage & Loading

```python
import json

# Stream cases line-by-line
with open("data/splits/train.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        case = json.loads(line)
        # Access text and labels
        text = case["text_features"]["clean_text"]
        label = case["outcome"]["binary_label"]
```

---

## 6. Citation

```bibtex
@article{sonawane2026citejustice,
  title={{CiteJustice}: A Scalable Legal AI Benchmark and Dynamic Precedent Evolution Graph for the Supreme Court of India},
  author={Sonawane, Sai},
  institution={VPKBIET Baramati},
  year={2026}
}
```
