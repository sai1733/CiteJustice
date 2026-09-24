"""
scripts/clean/run_nyaya_pipeline.py

Executes the complete 5-stage CiteJustice cleaning and segmentation pipeline
specifically on the standardized 2021-2024 NyayaAnumana Supreme Court dataset.

Stages executed:
1. remove_ocr_noise.py       -> data/clean/nyaya_2021_2024_noise_removed.csv
2. normalize_citations.py    -> data/clean/nyaya_2021_2024_citations_normalized.csv
3. normalize_acts_sections.py-> data/clean/nyaya_2021_2024_sections_normalized.csv
4. language_filter.py        -> data/clean/nyaya_2021_2024_english_primary.csv
5. extract_sections.py       -> data/clean/nyaya_2021_2024_segmented.jsonl

Usage:
    python scripts/clean/run_nyaya_pipeline.py
"""

import sys
import time
from pathlib import Path

# Setup paths
SCRIPTS_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = SCRIPTS_DIR.parent
DATA_RAW = BASE_DIR / "data" / "raw" / "nyayaanumana"
DATA_CLEAN = BASE_DIR / "data" / "clean"
DATA_CLEAN.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(SCRIPTS_DIR))

from clean import (
    remove_ocr_noise,
    normalize_citations,
    normalize_acts_sections,
    language_filter,
    extract_sections,
)

def run():
    print("=" * 70)
    print("CiteJustice - Processing 2021-2024 NyayaAnumana Supreme Court Judgments")
    print("=" * 70)

    start_total = time.time()
    raw_input = DATA_RAW / "nyaya_sc_standardized.csv"

    if not raw_input.exists():
        print(f"Error: {raw_input} does not exist!")
        sys.exit(1)

    # 1. OCR Noise Removal
    step1_out = DATA_CLEAN / "nyaya_2021_2024_noise_removed.csv"
    print("\n>>> Stage 1: Removing OCR Noise & Formatting Artifacts...")
    t0 = time.time()
    remove_ocr_noise.process_dataset(raw_input, step1_out)
    print(f"Stage 1 completed in {time.time() - t0:.2f}s")

    # 2. Citation Normalization
    step2_out = DATA_CLEAN / "nyaya_2021_2024_citations_normalized.csv"
    print("\n>>> Stage 2: Normalizing Precedent Citations (AIR, SCC, SCR)...")
    t0 = time.time()
    normalize_citations.process_dataset(step1_out, step2_out)
    print(f"Stage 2 completed in {time.time() - t0:.2f}s")

    # 3. Acts & Sections Normalization
    step3_out = DATA_CLEAN / "nyaya_2021_2024_sections_normalized.csv"
    print("\n>>> Stage 3: Normalizing Statutory Sections & Acts...")
    t0 = time.time()
    normalize_acts_sections.process_dataset(step2_out, step3_out)
    print(f"Stage 3 completed in {time.time() - t0:.2f}s")

    # 4. Language Filter
    step4_out = DATA_CLEAN / "nyaya_2021_2024_english_primary.csv"
    print("\n>>> Stage 4: Linguistic Auditing & English Verification...")
    t0 = time.time()
    language_filter.process_dataset(step3_out, step4_out)
    print(f"Stage 4 completed in {time.time() - t0:.2f}s")

    # 5. Rhetorical Zone Segmentation (Zero Target Leakage)
    step5_jsonl = DATA_CLEAN / "nyaya_2021_2024_segmented.jsonl"
    step5_csv = DATA_CLEAN / "nyaya_2021_2024_segmented_summary.csv"
    print("\n>>> Stage 5: Rhetorical Zone Segmentation (Facts, Submissions, Ratio)...")
    t0 = time.time()
    extract_sections.process_dataset(step4_out, step5_jsonl, step5_csv)
    print(f"Stage 5 completed in {time.time() - t0:.2f}s")

    total_time = time.time() - start_total
    print("\n" + "=" * 70)
    print(f"? Pipeline successfully completed in {total_time:.2f} seconds!")
    print(f"Final clean segmented output: {step5_jsonl}")
    print("=" * 70)

if __name__ == "__main__":
    run()
