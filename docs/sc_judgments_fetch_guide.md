# Supreme Court Judgments Acquisition Guide (~35K Corpus)

**Project:** LexGraphFormer — Legal Explainable Graph Transformer  
**Module:** Data Engineering Pipeline — Judgment Acquisition  
**Target:** Ingest ~35,000 Supreme Court Judgments (1950–Present) for Citation Graph Backbone  
**Prepared For:** Sai (Automation Lead) & Madhav  

---

## 1. Objective & Challenge

To construct the **Dynamic Precedent Evolution Graph (DPEG)**, we require a comprehensive, chronologically complete corpus of Supreme Court judgments (~35,000 judgments from 1950 to 2025/2026).

* **The Problem with Direct Web Scraping:** Official portals like `main.sci.gov.in` and `escr.sci.gov.in` employ CAPTCHA barriers, session timeouts, and rate limits, and serve judgments primarily as scanned or unstructured PDFs.
* **The Solution:** Leverage pre-extracted open data registries (Parquet/JSON) as the primary pipeline, backed up by OpenJustice India scripts for recent incremental updates.

---

## 2. Acquisition Strategies (Ranked by Reliability)

### Method 1 (Recommended): AWS Open Data Registry (Dattam Labs)
Dattam Labs maintains an open-access repository of Indian Supreme Court judgments covering 1950 through 2025. It is freely downloadable without commercial API keys or subscription fees.

* **Format:** Parquet & JSON metadata with full judgment text.
* **Storage Location:** Public AWS S3 Bucket.

#### Quick CLI Download (No AWS Account Required)
```bash
# Verify contents of public bucket
aws s3 ls s3://dattam-legal-data/sc-judgments/ --no-sign-request

# Download entire dataset into data/raw/sc_judgments/
aws s3 sync s3://dattam-legal-data/sc-judgments/ ./data/raw/sc_judgments/ --no-sign-request
```

#### Python Automation Script for Sai (`pipelines/fetch_sc_aws.py`)
```python
"""
pipelines/fetch_sc_aws.py
Automates downloading and verifying SC Judgments from AWS Open Data.
"""

import os
import boto3
from botocore import UNSIGNED
from botocore.client import Config
from pathlib import Path

DATA_DIR = Path("data/raw/sc_judgments")
BUCKET_NAME = "dattam-legal-data"
PREFIX = "sc-judgments/"

def download_sc_corpus():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize unauthenticated S3 client
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    
    paginator = s3.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=BUCKET_NAME, Prefix=PREFIX)
    
    total_files = 0
    print("[*] Starting Supreme Court judgment corpus download...")
    
    for page in pages:
        if "Contents" not in page:
            continue
        for obj in page["Contents"]:
            key = obj["Key"]
            if key.endswith("/"):
                continue
            
            dest_file = DATA_DIR / Path(key).name
            if dest_file.exists():
                continue
                
            print(f"Downloading: {dest_file.name}")
            s3.download_file(BUCKET_NAME, key, str(dest_file))
            total_files += 1

    print(f"[✓] Download complete. Total new files fetched: {total_files}")

if __name__ == "__main__":
    download_sc_corpus()
```

---

### Method 2: OpenJustice India (`openjustice-in/ecourts`)
The OpenJustice India community maintains Python libraries specifically engineered to query and extract court orders from Indian judicial portals.

* **Repository:** [https://github.com/openjustice-in/ecourts](https://github.com/openjustice-in/ecourts)
* **Installation:**
  ```bash
  pip install git+https://github.com/openjustice-in/ecourts.git
  ```

#### Usage Pattern for Incremental Fetching:
```python
"""
pipelines/fetch_openjustice.py
Fetches judgment records using OpenJustice India tooling.
"""

from ecourts import SupremeCourtClient
import json
from pathlib import Path

OUTPUT_DIR = Path("data/raw/openjustice_sc")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

client = SupremeCourtClient()

# Example: Fetch judgments by year range
for year in range(2020, 2026):
    print(f"Fetching SC judgments for year {year}...")
    judgments = client.search_by_year(year=year)
    
    out_file = OUTPUT_DIR / f"sc_judgments_{year}.jsonl"
    with open(out_file, "w", encoding="utf-8") as f:
        for record in judgments:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
```

---

### Method 3: Indian Kanoon API & Fallback Scraper
If specific missing judgments or neutral citation cross-references are required:

* **Endpoint:** `https://api.indiankanoon.org/`
* **Format:** REST API returning HTML/text with pre-tagged citation links (`/doc/<id>/`).
* **Headers:**
  ```http
  Authorization: Token YOUR_INDIAN_KANOON_TOKEN
  Content-Type: application/json
  ```
* **Sample Request:**
  ```python
  import requests

  headers = {"Authorization": "Token YOUR_TOKEN"}
  doc_id = "19734225"  # Kesavananda Bharati
  resp = requests.post(f"https://api.indiankanoon.org/doc/{doc_id}/", headers=headers)
  data = resp.json()
  ```

---

## 3. Standardized Output Schema (`SC_Judgment_v1`)

All ingestion scripts should normalize fetched judgments into the following JSONL/Parquet schema before passing to text cleaning and citation extraction pipelines:

```json
{
  "judgment_id": "1973_INSC_182",
  "neutral_citation": "2023 INSC 182",
  "equivalent_citations": [
    "AIR 1973 SC 1461",
    "(1973) 4 SCC 225",
    "[1973] Supp. SCR 1"
  ],
  "title": "Kesavananda Bharati Sripadagalvaru and Ors. v. State of Kerala and Anr.",
  "petitioner": "Kesavananda Bharati Sripadagalvaru and Ors.",
  "respondent": "State of Kerala and Anr.",
  "decision_date": "1973-04-24",
  "year": 1973,
  "bench": [
    "S.M. Sikri (CJI)",
    "J.M. Shelat",
    "K.S. Hegde",
    "A.N. Grover",
    "A.N. Ray",
    "P. Jaganmohan Reddy",
    "D.G. Palekar",
    "H.R. Khanna",
    "K.K. Mathew",
    "M.H. Beg",
    "S.N. Dwivedi",
    "A.K. Mukherjea",
    "Y.V. Chandrachud"
  ],
  "bench_size": 13,
  "court": "Supreme Court of India",
  "disposal_nature": "Dismissed in part / Allowed in part",
  "full_text": "...",
  "statutes_cited": [
    "Constitution of India, 1950",
    "Kerala Land Reforms Act, 1963"
  ]
}
```

---

## 4. Automation Checklist for Sai

- [ ] **Step 1: Environment Setup**
  - Install AWS CLI (`winget install Amazon.AWSCLI` or via installer).
  - Install Python dependencies: `pip install boto3 pandas pyarrow requests tqdm`.
- [ ] **Step 2: Download Corpus**
  - Execute `aws s3 sync s3://dattam-legal-data/sc-judgments/ ./data/raw/sc_judgments/ --no-sign-request`.
  - Alternatively run `python pipelines/fetch_sc_aws.py`.
- [ ] **Step 3: Verification & Count Check**
  - Check total record count (target: ~35,000).
  - Check distribution of judgments by decade (1950–1960, ..., 2020–2025).
- [ ] **Step 4: Format Hand-off**
  - Save clean output as Parquet in `data/processed/sc_corpus.parquet`.
  - Notify team for citation graph building (DPEG construction).
