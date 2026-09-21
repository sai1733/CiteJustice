"""
scripts/clean/normalize_citations.py

Pipeline module to standardize Indian legal citations into canonical formats:
1. AIR: (e.g. 'A.I.R. 1973 S.C. 1461' -> 'AIR 1973 SC 1461')
2. SCC: (e.g. '2011 (4) SCC 456' -> '(2011) 4 SCC 456')
3. SCR: (e.g. '[1963] 2 S.C.R. 285' -> '[1963] 2 SCR 285')
4. SCALE: (e.g. '2005 (3) Scale 120' -> '(2005) 3 SCALE 120')
5. Neutral Citations: (e.g. '2023:INSC:182' -> '2023 INSC 182')

Also extracts structured citation lists per case for downstream DPEG edge building.

Usage:
    python scripts/clean/normalize_citations.py --sample 50
    python scripts/clean/normalize_citations.py --dataset single
    python scripts/clean/normalize_citations.py --dataset multi
"""

import os
import re
import sys
import csv
import json
import argparse
from pathlib import Path

# Increase CSV field size limit for legal texts
csv.field_size_limit(sys.maxsize)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "ildc"
CLEAN_DIR = BASE_DIR / "data" / "clean"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# Regex Patterns for Citation Normalization & Extraction
# --------------------------------------------------------------------------

# 1. Neutral Citation (INSC): 2023 INSC 182 or 2023:INSC:182
NEUTRAL_INSC_REGEX = re.compile(
    r"\b((?:19|20)\d{2})\s*(?::|\s+)\s*INSC\s*(?::|\s+)\s*(\d+)\b",
    re.IGNORECASE
)

# 2. SCC: e.g. (2018) 1 SCC 1, 2018 (1) SCC 1, 2018 1 SCC 1, (1993) Supp (1) SCC 645
SCC_REGEX = re.compile(
    r"(?:\(|\b)((?:19|20)\d{2})\)?\s+(?:Supp(?:l\.?)?\s*(?:\((\d+)\)\s*)?)?(?:\(?(\d+)\)?\s+)?S\.?C\.?C\.?(?:\s*\(?Online\)?|\s*Online)?\s+(\d+)\b",
    re.IGNORECASE
)

# 3. AIR: e.g. AIR 1973 SC 1461, A.I.R. 1973 S.C. 1461, 1973 AIR SC 1461
AIR_REGEX = re.compile(
    r"\b(?:A\.?I\.?R\.?\s+((?:19|20)\d{2})|((?:19|20)\d{2})\s+A\.?I\.?R\.?)\s+(S\.?C\.?|All|AP|Bom|Cal|Del|Guj|HP|J&K|Kar|Knt|Ker|Mad|MP|Ori|Pat|P&H|Raj)\s+(\d+)\b",
    re.IGNORECASE
)

# 4. SCR: e.g. [1950] SCR 869, (1950) 2 SCR 869, 1950 2 S.C.R. 869
SCR_REGEX = re.compile(
    r"(?:\[|\(|\b)((?:19|20)\d{2})(?:\]|\))?\s+(?:Supp(?:l\.?)?\s*)?(?:\(?(\d+)\)?\s+)?S\.?C\.?R\.?\s+(\d+)\b",
    re.IGNORECASE
)

# 5. SCALE: e.g. 2002 (3) SCALE 456, (1996) 2 SCALE 112
SCALE_REGEX = re.compile(
    r"(?:\(|\b)((?:19|20)\d{2})\)?\s*(?:\((\d+)\)\s*)?SCALE\s+(\d+)\b",
    re.IGNORECASE
)

# 6. Criminal Law Journal: e.g. 1980 Cri LJ 142, 1980 Cr.L.J. 142
CRILJ_REGEX = re.compile(
    r"\b((?:19|20)\d{2})\s+(?:Cri\s*LJ|Cr\.?L\.?J\.?)\s+(\d+)\b",
    re.IGNORECASE
)

def normalize_citations(text: str) -> tuple[str, list[str]]:
    """
    Standardizes all citations in the text to their canonical forms
    and returns:
    (normalized_text, list_of_canonical_citations_found)
    """
    if not isinstance(text, str) or not text.strip():
        return "", []

    found_citations = set()

    # 1. Standardize Neutral Citations -> YYYY INSC NNN
    def repl_neutral(match):
        year, num = match.group(1), match.group(2)
        canonical = f"{year} INSC {num}"
        found_citations.add(canonical)
        return canonical

    text = NEUTRAL_INSC_REGEX.sub(repl_neutral, text)

    # 2. Standardize SCC -> (YYYY) VOL SCC PAGE or (YYYY) Supp VOL SCC PAGE
    def repl_scc(match):
        year = match.group(1)
        supp_vol = match.group(2)
        vol = match.group(3)
        page = match.group(4)
        if supp_vol:
            canonical = f"({year}) Supp ({supp_vol}) SCC {page}"
        elif vol:
            canonical = f"({year}) {vol} SCC {page}"
        else:
            canonical = f"({year}) SCC {page}"
        found_citations.add(canonical)
        return canonical

    text = SCC_REGEX.sub(repl_scc, text)

    # 3. Standardize AIR -> AIR YYYY COURT PAGE
    def repl_air(match):
        year = match.group(1) or match.group(2)
        court = match.group(3).replace(".", "").upper()
        # Canonicalize common court abbreviations
        if court == "SC":
            court_clean = "SC"
        elif court in ["KAR", "KNT"]:
            court_clean = "Kar"
        elif court == "BOM":
            court_clean = "Bom"
        elif court == "DEL":
            court_clean = "Del"
        elif court == "CAL":
            court_clean = "Cal"
        else:
            court_clean = court.capitalize()
        page = match.group(4)
        canonical = f"AIR {year} {court_clean} {page}"
        found_citations.add(canonical)
        return canonical

    text = AIR_REGEX.sub(repl_air, text)

    # 4. Standardize SCR -> [YYYY] VOL SCR PAGE
    def repl_scr(match):
        year = match.group(1)
        vol = match.group(2)
        page = match.group(3)
        if vol:
            canonical = f"[{year}] {vol} SCR {page}"
        else:
            canonical = f"[{year}] SCR {page}"
        found_citations.add(canonical)
        return canonical

    text = SCR_REGEX.sub(repl_scr, text)

    # 5. Standardize SCALE -> (YYYY) VOL SCALE PAGE
    def repl_scale(match):
        year = match.group(1)
        vol = match.group(2)
        page = match.group(3)
        if vol:
            canonical = f"({year}) {vol} SCALE {page}"
        else:
            canonical = f"({year}) SCALE {page}"
        found_citations.add(canonical)
        return canonical

    text = SCALE_REGEX.sub(repl_scale, text)

    # 6. Standardize Cri LJ -> YYYY Cri LJ PAGE
    def repl_crilj(match):
        year, page = match.group(1), match.group(2)
        canonical = f"{year} Cri LJ {page}"
        found_citations.add(canonical)
        return canonical

    text = CRILJ_REGEX.sub(repl_crilj, text)

    return text, sorted(list(found_citations))

def process_dataset(input_file: Path, output_file: Path, sample_size: int = None):
    print("=" * 65)
    print("CiteJustice - Citation Normalization Pipeline")
    print(f"Source: {input_file}")
    print(f"Target: {output_file}")
    print("=" * 65)

    if not input_file.exists():
        print(f"Error: Input file {input_file} does not exist.")
        sys.exit(1)

    print(f"Reading dataset: {input_file.name}...")
    rows = []
    with open(input_file, mode="r", encoding="utf-8", errors="replace") as f_in:
        reader = csv.DictReader(f_in)
        fieldnames = list(reader.fieldnames) if reader.fieldnames else []
        
        count = 0
        for row in reader:
            rows.append(row)
            count += 1
            if sample_size and count >= sample_size:
                break

    total_records = len(rows)
    print(f"Loaded {total_records:,} cases to process.\n")

    out_fields = fieldnames + ["normalized_text", "citations_found", "citation_count"]
    total_citations_extracted = 0
    cases_with_citations = 0

    with open(output_file, mode="w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=out_fields)
        writer.writeheader()

        for idx, row in enumerate(rows, 1):
            # Prefer text already cleaned from Task 1 if present, otherwise fall back to raw text
            src_text = row.get("cleaned_text") or row.get("text", "")
            norm_text, citations = normalize_citations(src_text)

            row["normalized_text"] = norm_text
            row["citations_found"] = json.dumps(citations)
            row["citation_count"] = len(citations)

            if citations:
                cases_with_citations += 1
                total_citations_extracted += len(citations)

            writer.writerow(row)

            if idx % 500 == 0 or idx == total_records:
                print(f"  Processed {idx:,} / {total_records:,} cases ({(idx/total_records)*100:.1f}%)...")

    print(f"\n[OK] Citation-normalized dataset saved to: {output_file}")

    print("\n" + "-" * 40)
    print("Execution Summary:")
    print(f"  Cases processed              : {total_records:,}")
    print(f"  Cases with legal citations   : {cases_with_citations:,} ({(cases_with_citations/total_records)*100:.1f}%)")
    print(f"  Total citations normalized   : {total_citations_extracted:,}")
    print(f"  Average citations per case   : {total_citations_extracted/total_records:.2f}")
    print("-" * 40)

def main():
    parser = argparse.ArgumentParser(description="Normalize legal citations in ILDC cases.")
    parser.add_argument("--dataset", choices=["single", "multi"], default="single",
                        help="Dataset to normalize: 'single' (9,110 cases) or 'multi' (34,816 cases).")
    parser.add_argument("--sample", type=int, default=None,
                        help="Process only a sample of N cases for fast testing.")
    args = parser.parse_args()

    # If Task 1 output exists, use it as input; otherwise use raw dataset
    cleaned_input = CLEAN_DIR / f"ildc_{args.dataset}_noise_removed.csv"
    raw_input = RAW_DIR / ("ILDC_single.csv" if args.dataset == "single" else "ILDC_multi.csv")
    
    input_path = cleaned_input if cleaned_input.exists() else raw_input
    output_filename = f"ildc_{args.dataset}_citations_normalized.csv"
    if args.sample:
        output_filename = f"ildc_{args.dataset}_sample_{args.sample}_citations.csv"

    output_path = CLEAN_DIR / output_filename
    process_dataset(input_path, output_path, sample_size=args.sample)

if __name__ == "__main__":
    main()
