# ⚖️ CiteJustice

**Automated Legal Judgment Prediction for Indian Courts Using Graph Neural Networks**

CiteJustice is an AI decision-support system designed for the Indian judiciary. Unlike traditional systems that solely rely on semantic text similarity, CiteJustice incorporates a **Dynamic Precedent Evolution Graph (DPEG)** to model how legal precedents evolve over time (followed, distinguished, or overruled).

---

## 📂 Repository Structure

- data/
  - aw/ - Raw downloaded legal datasets (e.g. ILDC)
  - clean/ - Preprocessed and normalized legal text
  - graph/ - Citation edge lists, node schemas, and exported graphs
  - splits/ - Temporal train/val/test splits
- 
otebooks/ - Jupyter notebooks for exploratory data analysis, profiling, and quickstarts
- scripts/
  - clean/ - Text cleaning, section normalization, and OCR cleanup scripts
  - graph/ - Citation extraction and NetworkX graph builders
  - dedup/ - Exact and near-duplicate removal scripts
- docs/ - Lookup tables, schemas, and citation signal reference documents

---

## 🚀 Setup & Installation

`ash
# Clone the repository
git clone https://github.com/sai1733/CiteJustice.git
cd CiteJustice

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
`
