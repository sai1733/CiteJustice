"""
CiteJustice - Dataset Acquisition Script
Downloads and consolidates the official Indian Legal Documents Corpus (ILDC)
for Court Judgment Prediction and Explanation (CJPE) into data/raw/ildc/.

Usage:
    python scripts/download_data.py --token <YOUR_HF_TOKEN>
    or set environment variable: HF_TOKEN=<YOUR_HF_TOKEN>
"""
import os
import sys
import argparse
import requests
from tqdm import tqdm
import pandas as pd

DEST_DIR = os.path.join("data", "raw", "ildc")
os.makedirs(DEST_DIR, exist_ok=True)

URLS = {
    # ILDC Single
    "single_train.parquet": "https://huggingface.co/datasets/Exploration-Lab/IL-TUR/resolve/main/cjpe/single_train-00000-of-00001.parquet",
    "single_dev.parquet": "https://huggingface.co/datasets/Exploration-Lab/IL-TUR/resolve/main/cjpe/single_dev-00000-of-00001.parquet",
    "test.parquet": "https://huggingface.co/datasets/Exploration-Lab/IL-TUR/resolve/main/cjpe/test-00000-of-00001.parquet",
    # ILDC Multi
    "multi_train_1.parquet": "https://huggingface.co/datasets/Exploration-Lab/IL-TUR/resolve/main/cjpe/multi_train-00000-of-00002.parquet",
    "multi_train_2.parquet": "https://huggingface.co/datasets/Exploration-Lab/IL-TUR/resolve/main/cjpe/multi_train-00001-of-00002.parquet",
    "multi_dev.parquet": "https://huggingface.co/datasets/Exploration-Lab/IL-TUR/resolve/main/cjpe/multi_dev-00000-of-00001.parquet",
}

def download_file(url, filename, headers, max_retries=5):
    import time
    dest_path = os.path.join(DEST_DIR, filename)
    if os.path.exists(dest_path) and os.path.getsize(dest_path) > 1000:
        print(f"[OK] {filename} already exists ({os.path.getsize(dest_path):,} bytes).")
        return dest_path
        
    for attempt in range(1, max_retries + 1):
        print(f"Connecting to download {filename} (Attempt {attempt}/{max_retries})...")
        try:
            response = requests.get(url, headers=headers, stream=True, timeout=60)
            if response.status_code == 401:
                print("Error: 401 Unauthorized. Please provide a valid Hugging Face token authorized for Exploration-Lab/IL-TUR!")
                sys.exit(1)
            elif response.status_code != 200:
                print(f"Error downloading {filename}: HTTP status {response.status_code}")
                time.sleep(5)
                continue
                
            total_size = int(response.headers.get('content-length', 0))
            block_size = 1024 * 1024  # 1MB chunks
            
            temp_dest = dest_path + ".tmp"
            with open(temp_dest, 'wb') as f:
                with tqdm(total=total_size, unit='B', unit_scale=True, desc=filename) as pbar:
                    for chunk in response.iter_content(chunk_size=block_size):
                        if chunk:
                            f.write(chunk)
                            pbar.update(len(chunk))
                            
            if os.path.exists(dest_path):
                os.remove(dest_path)
            os.rename(temp_dest, dest_path)
            print(f"[OK] Downloaded {filename} successfully!\n")
            return dest_path
        except Exception as e:
            print(f"Network error during attempt {attempt}: {e}")
            if attempt < max_retries:
                wait_time = 5 * attempt
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print(f"Failed to download {filename} after {max_retries} attempts.")
                sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Download ILDC dataset")
    parser.add_argument("--token", default=os.getenv("HF_TOKEN"), help="Hugging Face Access Token")
    args = parser.parse_args()

    token = args.token
    if not token:
        # Prompt user if not provided
        token = input("Enter your Hugging Face access token: ").strip()

    headers = {"Authorization": f"Bearer {token}"} if token else {}

    print("="*65)
    print("CiteJustice - Dataset Acquisition (ILDC Corpus)")
    print("="*65)
    
    single_csv = os.path.join(DEST_DIR, "ILDC_single.csv")
    multi_csv = os.path.join(DEST_DIR, "ILDC_multi.csv")
    
    if os.path.exists(single_csv) and os.path.exists(multi_csv):
        print(f"[OK] Both ILDC_single.csv and ILDC_multi.csv are already present in {DEST_DIR}!")
        return

    downloaded = {}
    for fname, url in URLS.items():
        downloaded[fname] = download_file(url, fname, headers)
        
    if not os.path.exists(single_csv):
        print("\nConsolidating ILDC_single.csv...")
        dfs = []
        for split, fname in [("train", "single_train.parquet"), ("dev", "single_dev.parquet"), ("test", "test.parquet")]:
            df_p = pd.read_parquet(downloaded[fname])
            df_p["split"] = split
            dfs.append(df_p)
        full_single = pd.concat(dfs, ignore_index=True)
        full_single.to_csv(single_csv, index=False)
        print(f"[OK] Saved {single_csv} with {len(full_single):,} cases.")

    if not os.path.exists(multi_csv):
        print("\nConsolidating ILDC_multi.csv...")
        dfs = []
        for fname in ["multi_train_1.parquet", "multi_train_2.parquet"]:
            df_p = pd.read_parquet(downloaded[fname])
            df_p["split"] = "train"
            dfs.append(df_p)
        df_dev = pd.read_parquet(downloaded["multi_dev.parquet"])
        df_dev["split"] = "dev"
        dfs.append(df_dev)
        df_test = pd.read_parquet(downloaded["test.parquet"])
        df_test["split"] = "test"
        dfs.append(df_test)
        
        full_multi = pd.concat(dfs, ignore_index=True)
        full_multi.to_csv(multi_csv, index=False)
        print(f"[OK] Saved {multi_csv} with {len(full_multi):,} cases.")

    print("\n" + "="*65)
    print("All datasets downloaded and consolidated successfully!")
    print("="*65)

if __name__ == "__main__":
    main()
