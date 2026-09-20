"""
scripts/download_nyayaanumana.py
Inspection and acquisition script for NyayaAnumana dataset from L-NLProc on Hugging Face.

Usage:
    python scripts/download_nyayaanumana.py --sample-only
    python scripts/download_nyayaanumana.py --token <HF_TOKEN> --subset <SUBSET_NAME>
"""

import os
import argparse
from pathlib import Path
from huggingface_hub import HfApi

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data" / "raw" / "nyayaanumana"

COLLECTION_URL = "https://huggingface.co/collections/L-NLProc/nyayaanumana-and-inlegalllama-dataset"

def list_collection_datasets():
    print("=" * 65)
    print("Fetching available NyayaAnumana datasets under L-NLProc...")
    print("=" * 65)
    api = HfApi()
    try:
        datasets = api.list_datasets(author="L-NLProc")
        print("Available datasets in L-NLProc organization:")
        for idx, ds in enumerate(datasets, 1):
            print(f"  {idx}. {ds.id} (Downloads: {getattr(ds, 'downloads', 'N/A')})")
        print("\nCollection Link:", COLLECTION_URL)
    except Exception as e:
        print(f"Could not list remote datasets: {e}")

def main():
    parser = argparse.ArgumentParser(description="NyayaAnumana Dataset Tool")
    parser.add_argument("--list", action="store_true", default=True, help="List datasets in L-NLProc")
    parser.add_argument("--token", default=os.getenv("HF_TOKEN"), help="Hugging Face Token")
    args = parser.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    list_collection_datasets()

if __name__ == "__main__":
    main()
