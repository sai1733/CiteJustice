"""
scripts/package_model_handoff.py

Assembles the standalone CiteJustice_Phase1_Model_Handoff package
for Google Drive sharing and Model Architecture team onboarding.

Author: Sai Sonawane (Computer Engineering Lead)
Date: September 30, 2026
"""

import os
import sys
import shutil
from pathlib import Path

# Reconfigure stdout for utf-8 on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

REPO_DIR = Path(__file__).resolve().parent.parent
OUTER_DIR = REPO_DIR.parent
TARGET_DIR = OUTER_DIR / "CiteJustice_Phase1_Model_Handoff"

def build_handoff_package():
    print("=" * 75, flush=True)
    print("CiteJustice - Packaging Phase 1 Model Team Handoff", flush=True)
    print(f"Source Directory: {REPO_DIR}", flush=True)
    print(f"Target Directory: {TARGET_DIR}", flush=True)
    print("=" * 75, flush=True)

    if TARGET_DIR.exists():
        print(f"Target directory exists. Cleaning old files at {TARGET_DIR}...", flush=True)
        shutil.rmtree(TARGET_DIR)

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    (TARGET_DIR / "data" / "splits").mkdir(parents=True, exist_ok=True)
    (TARGET_DIR / "data" / "graph").mkdir(parents=True, exist_ok=True)
    (TARGET_DIR / "data" / "clean").mkdir(parents=True, exist_ok=True)
    (TARGET_DIR / "notebooks").mkdir(parents=True, exist_ok=True)
    (TARGET_DIR / "docs" / "dataset_cards").mkdir(parents=True, exist_ok=True)

    print("\n[Stage 1/4] Generating root README.md and requirements.txt...", flush=True)
    
    # 1. requirements.txt
    reqs_content = """# CiteJustice Phase 2 - Model Team Requirements
# Tested on Python 3.10 / 3.11 / 3.12 (Windows / Linux)

torch>=2.0.0
torch-geometric>=2.3.0
networkx>=3.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.2.0
matplotlib>=3.7.0
jupyter>=1.0.0
ipykernel>=6.0.0
"""
    with open(TARGET_DIR / "requirements.txt", "w", encoding="utf-8") as f:
        f.write(reqs_content)
    print("  [OK] Created requirements.txt")

    # 2. README.md
    readme_content = """# CiteJustice Phase 1: Production Data & Model Team Handoff Package

**Author:** Sai Sonawane (Computer Engineering Lead)  
**Institution:** Vidya Pratishthan's Kamalnayan Bajaj Institute of Engineering and Technology (VPKBIET), Baramati  
**Academic Year:** 2026–2027  
**Date:** September 30, 2026  
**Parent Project:** CiteJustice — Legal AI Benchmark for the Supreme Court of India  

---

## 🚀 Welcome Model Architecture Team!

This standalone package contains the complete, leak-free, verified **CiteJustice Phase 1 Deliverables**. You have everything required to begin training Large Language Models (LLMs) and Graph Neural Networks (GNNs) immediately without needing access to external scraping repositories.

---

## ⚡ 3-Minute Quickstart on Your Local Machine

### 1. Create and Activate Virtual Environment
Open your terminal inside this folder:
```bash
python -m venv venv
# On Windows:
.\\venv\\Scripts\\activate
# On Linux / Mac:
source venv/bin/activate
```

### 2. Install Required Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Quickstart Notebook
Launch Jupyter or open in VS Code:
```bash
code .
```
Navigate to `notebooks/quickstart.ipynb`, select your Python kernel, and hit **"Run All"**. 
In under 2 minutes, all datasets, split statistics, cryptographic leakage checks, NetworkX graphs, and PyG relational tensors will load cleanly with verified outputs!

---

## 📁 Package Directory Structure

```text
CiteJustice_Phase1_Model_Handoff/
├── README.md                      <-- This Guide
├── requirements.txt               <-- Python dependencies
├── notebooks/
│   └── quickstart.ipynb           <-- 5-minute executable walkthrough (all 15 cells verified)
├── data/
│   ├── splits/                    <-- Core Modeling Datasets
│   │   ├── train.jsonl            (31,567 cases <= 2015, foundational training)
│   │   ├── dev.jsonl              (1,486 cases 2016-2018, tuning & early stopping)
│   │   ├── test.jsonl             (1,900 cases 2019-2024, held-out evaluation)
│   │   ├── pyg_split_masks.npz    (train_mask, val_mask, test_mask for PyG)
│   │   └── split_stats.json       (Machine-readable split metrics)
│   ├── graph/                     <-- Precedent Evolution Graph (DPEG)
│   │   ├── citation_graph.graphml (Signed NetworkX multi-graph, 66K nodes, 94K edges)
│   │   ├── pyg_edge_tensors.npz   (edge_index, edge_weight, edge_type for GNNs)
│   │   ├── pyg_node_map.json      (case_id -> continuous tensor index mapping)
│   │   └── graph_construction_stats.json
│   └── clean/                     <-- Master Lookup & Audits
│       ├── cases.jsonl            (36,025 master judgments with Schema v1.1.0)
│       ├── exact_duplicates.csv   (1,068 excluded duplicate case IDs)
│       └── near_duplicates.csv    (809 audited companion pairs)
└── docs/                          <-- Full Documentation & Specifications
    ├── model_team_handoff.md      <-- Mandatory Modeling Rules & Targets
    ├── schema.md                  <-- Canonical Schema v1.1.0-frozen specification
    ├── preprocessing.md           <-- End-to-end cleaning pipeline & Viva Q&A
    ├── split_rationale.md         <-- COVID-19 empirical dip & Option A rationale
    ├── graph_stats.md             <-- Scale-free gamma=2.14 & DPEG network metrics
    ├── near_duplicate_audit.md    <-- Legal review of batch companion petitions
    └── dataset_cards/             <-- Hugging Face format dataset cards
```

---

## 🎯 Phase 2 Benchmark Stretch Targets

* **Zero-Intelligence Floor (Majority Class Baseline):** 58.00% Accuracy (Predict all as Allowed)
* **Phase 2 Stretch Benchmark Goal:**
  * **Accuracy:** $\ge 82.0\%$
  * **Macro F1:** $\ge 80.0\%$
  * **AUC-ROC:** $\ge 0.860$
  * **Citation Recall@10:** $\ge 65.0\%$

Refer to `docs/model_team_handoff.md` for the official modeling rules of engagement.
"""
    with open(TARGET_DIR / "README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print("  [OK] Created README.md")

    # --------------------------------------------------------------------------
    # Stage 2: Copy Notebooks
    # --------------------------------------------------------------------------
    print("\n[Stage 2/4] Copying notebooks...", flush=True)
    shutil.copy2(REPO_DIR / "notebooks" / "quickstart.ipynb", TARGET_DIR / "notebooks" / "quickstart.ipynb")
    print("  [OK] Copied notebooks/quickstart.ipynb")

    # --------------------------------------------------------------------------
    # Stage 3: Copy Data Files
    # --------------------------------------------------------------------------
    print("\n[Stage 3/4] Copying production data splits, graph tensors, and master files...", flush=True)
    
    # data/splits/
    for fname in ["train.jsonl", "dev.jsonl", "test.jsonl", "pyg_split_masks.npz", "split_stats.json"]:
        src = REPO_DIR / "data" / "splits" / fname
        if src.exists():
            shutil.copy2(src, TARGET_DIR / "data" / "splits" / fname)
            print(f"  [OK] Copied data/splits/{fname} ({src.stat().st_size / (1024*1024):.2f} MB)")

    # data/graph/
    for fname in ["citation_graph.graphml", "pyg_edge_tensors.npz", "pyg_node_map.json", "graph_construction_stats.json"]:
        src = REPO_DIR / "data" / "graph" / fname
        if src.exists():
            shutil.copy2(src, TARGET_DIR / "data" / "graph" / fname)
            print(f"  [OK] Copied data/graph/{fname} ({src.stat().st_size / (1024*1024):.2f} MB)")

    # data/clean/
    for fname in ["cases.jsonl", "exact_duplicates.csv", "near_duplicates.csv", "build_nodes_summary.csv"]:
        src = REPO_DIR / "data" / "clean" / fname
        if src.exists():
            shutil.copy2(src, TARGET_DIR / "data" / "clean" / fname)
            print(f"  [OK] Copied data/clean/{fname} ({src.stat().st_size / (1024*1024):.2f} MB)")

    # --------------------------------------------------------------------------
    # Stage 4: Copy Documentation
    # --------------------------------------------------------------------------
    print("\n[Stage 4/4] Copying documentation and dataset cards...", flush=True)
    doc_files = [
        "model_team_handoff.md", "schema.md", "preprocessing.md", "split_rationale.md",
        "graph_stats.md", "near_duplicate_audit.md", "outcome_rules.md", "act_lookup.csv",
        "references.bib", "week5_report.md", "week6_report.md"
    ]
    for fname in doc_files:
        src = REPO_DIR / "docs" / fname
        if src.exists():
            shutil.copy2(src, TARGET_DIR / "docs" / fname)
            print(f"  [OK] Copied docs/{fname}")

    # docs/dataset_cards/
    for card in (REPO_DIR / "docs" / "dataset_cards").glob("*.md"):
        shutil.copy2(card, TARGET_DIR / "docs" / "dataset_cards" / card.name)
        print(f"  [OK] Copied docs/dataset_cards/{card.name}")

    print("\n" + "=" * 75, flush=True)
    print("HANDOFF PACKAGE ASSEMBLED SUCCESSFULLY!")
    print(f"Location: {TARGET_DIR}")
    print("=" * 75, flush=True)

if __name__ == "__main__":
    build_handoff_package()
