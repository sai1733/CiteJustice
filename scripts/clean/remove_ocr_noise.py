"""
scripts/clean/remove_ocr_noise.py

Pipeline module to sanitize raw Indian Supreme Court judgments by removing:
1. Digital signature blocks & e-filing registry stamps.
2. Systematic ILDC token corruptions (e.g. 'companyplainant' -> 'complainant', 'numberice' -> 'notice').
3. PDF linebreak hyphenations (e.g. 'sen-\\ntenced' -> 'sentenced').
4. Form-feed characters (\\x0c), non-breaking spaces (\\xa0), and control characters.
5. Marginal headers, footers, page numbering stamps, and divider lines.
6. Irregular whitespace and repeated newlines.

Usage:
    python scripts/clean/remove_ocr_noise.py --sample 50
    python scripts/clean/remove_ocr_noise.py --dataset single
    python scripts/clean/remove_ocr_noise.py --dataset multi
"""

import os
import re
import sys
import csv
import argparse
from pathlib import Path

# Increase CSV field size limit for large court judgments
csv.field_size_limit(sys.maxsize)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "ildc"
CLEAN_DIR = BASE_DIR / "data" / "clean"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# 1. ILDC Token Corruption Repair Rules
# --------------------------------------------------------------------------
CORRUPTION_REPAIRS = [
    # "company" corruption repairs
    (re.compile(r"\bcompanynsel\b", re.IGNORECASE), "counsel"),
    (re.compile(r"\bcompanyplainant\b", re.IGNORECASE), "complainant"),
    (re.compile(r"\bcompanyplainants\b", re.IGNORECASE), "complainants"),
    (re.compile(r"\bcompanypromised\b", re.IGNORECASE), "compromised"),
    (re.compile(r"\bcompanysiderable\b", re.IGNORECASE), "considerable"),
    (re.compile(r"\bcompanysideration\b", re.IGNORECASE), "consideration"),
    (re.compile(r"\bcompanysider\b", re.IGNORECASE), "consider"),
    (re.compile(r"\bcompanysidered\b", re.IGNORECASE), "considered"),
    (re.compile(r"\bcompanytradictory\b", re.IGNORECASE), "contradictory"),
    (re.compile(r"\bcompanytradiction\b", re.IGNORECASE), "contradiction"),
    (re.compile(r"\bcompanymon\b", re.IGNORECASE), "common"),
    (re.compile(r"\bcompanypany\b", re.IGNORECASE), "company"),
    (re.compile(r"\bcompanytract\b", re.IGNORECASE), "contract"),
    (re.compile(r"\bcompanytracts\b", re.IGNORECASE), "contracts"),
    (re.compile(r"\bcompanyrt\b", re.IGNORECASE), "court"),
    (re.compile(r"\bcompanyrts\b", re.IGNORECASE), "courts"),
    (re.compile(r"\bcompanyvict\b", re.IGNORECASE), "convict"),
    (re.compile(r"\bcompanyvicted\b", re.IGNORECASE), "convicted"),
    (re.compile(r"\bcompanyviction\b", re.IGNORECASE), "conviction"),
    (re.compile(r"\bcompanyvictions\b", re.IGNORECASE), "convictions"),
    (re.compile(r"\bcompanyfession\b", re.IGNORECASE), "confession"),
    (re.compile(r"\bcompanyfessional\b", re.IGNORECASE), "confessional"),
    (re.compile(r"\bcompanyduct\b", re.IGNORECASE), "conduct"),
    (re.compile(r"\bcompanyducted\b", re.IGNORECASE), "conducted"),
    (re.compile(r"\bcompanyplicity\b", re.IGNORECASE), "complicity"),
    (re.compile(r"\bcompanyclussion\b", re.IGNORECASE), "conclusion"),
    (re.compile(r"\bcompanyclusion\b", re.IGNORECASE), "conclusion"),
    (re.compile(r"\bcompanycurred\b", re.IGNORECASE), "concurred"),
    (re.compile(r"\bcompanycurrence\b", re.IGNORECASE), "concurrence"),
    (re.compile(r"\bcompanysequence\b", re.IGNORECASE), "consequence"),
    (re.compile(r"\bcompanysequences\b", re.IGNORECASE), "consequences"),
    (re.compile(r"\bcompanynected\b", re.IGNORECASE), "connected"),
    (re.compile(r"\bcompanynection\b", re.IGNORECASE), "connection"),

    # "number" corruption repairs
    (re.compile(r"\bnumberice\b", re.IGNORECASE), "notice"),
    (re.compile(r"\bnumberices\b", re.IGNORECASE), "notices"),
    (re.compile(r"\bnumbertified\b", re.IGNORECASE), "notified"),
    (re.compile(r"\bnumbertification\b", re.IGNORECASE), "notification"),
    (re.compile(r"\bnumbertifications\b", re.IGNORECASE), "notifications"),
    (re.compile(r"\bnumbertable\b", re.IGNORECASE), "notable"),
    (re.compile(r"\bnumbertorious\b", re.IGNORECASE), "notorious"),
    (re.compile(r"\bnumbertion\b", re.IGNORECASE), "notion"),
    (re.compile(r"\bnumber affirmed\b", re.IGNORECASE), "not affirmed"),
    (re.compile(r"\bnumber duly\b", re.IGNORECASE), "not duly"),
    (re.compile(r"\bnumber did it\b", re.IGNORECASE), "nor did it"),
    (re.compile(r"\bnumber found\b", re.IGNORECASE), "not found"),
]

# --------------------------------------------------------------------------
# 2. Digital Signature & E-Filing Stamp Patterns
# --------------------------------------------------------------------------
DIGITAL_SIG_PATTERNS = [
    re.compile(r"Signature\s+Not\s+Verified(?:\s+Digitally\s+signed\s+by\s+[^\n\r]+)?", re.IGNORECASE),
    re.compile(r"Digitally\s+signed\s+by\s+[A-Za-z\.\s]{2,50}?\s*Date\s*[:\s]*[\d\.\s:]{8,25}(?:IST|GMT)?(?:\s*Reason\b[^\n\r]*)?", re.IGNORECASE),
    re.compile(r"\bDigitally\s+Signed\s+By:.*?(?:\r?\n|$)", re.IGNORECASE),
]

# --------------------------------------------------------------------------
# 3. Structural Headers, Page Footers & Divider Patterns
# --------------------------------------------------------------------------
PAGE_NUMBER_PATTERN = re.compile(r"(?im)^\s*Page\s+\d+\s+of\s+\d+\s*$")
PAGE_NUM_STANDALONE = re.compile(r"(?im)^\s*\[\s*Page\s*\d+\s*\]\s*$")
PAGE_NUM_BARE = re.compile(r"(?im)^\s*\b(?:Page|Pg\.)\s*\d+\b\s*$")
DIVIDER_LINES = re.compile(r"[-_=\*]{4,}")

# --------------------------------------------------------------------------
# 4. PDF Hyphenation Repair Pattern (word- \n next_word)
# --------------------------------------------------------------------------
HYPHENATED_LINEBREAK = re.compile(r"(\b[A-Za-z]{2,})-\s*(?:\r?\n)+\s*([A-Za-z]{2,}\b)")

# --------------------------------------------------------------------------
# 5. Unicode Quotes & Punctuation Normalization
# --------------------------------------------------------------------------
UNICODE_REPLACEMENTS = {
    "\x0c": " ",      # Form-feed character (printer page break)
    "\xa0": " ",      # Non-breaking space
    "\u200b": "",     # Zero-width space
    "\ufeff": "",     # Byte order mark
    "’": "'",
    "‘": "'",
    "“": '"',
    "”": '"',
    "–": " - ",
    "—": " - ",
    "\t": " ",
}

def remove_ocr_noise(text: str) -> str:
    """Sanitizes raw Indian judgment text by stripping OCR noise and fixing corruptions."""
    if not isinstance(text, str) or not text.strip():
        return ""

    # Step 1: Remove form-feed and unicode control artifacts
    for char, replacement in UNICODE_REPLACEMENTS.items():
        if char in text:
            text = text.replace(char, replacement)

    # Step 2: Strip digital signature and e-filing stamps
    for pat in DIGITAL_SIG_PATTERNS:
        text = pat.sub(" ", text)

    # Step 3: Repair broken PDF line-break hyphenations
    text = HYPHENATED_LINEBREAK.sub(r"\1\2", text)

    # Step 4: Repair known ILDC automated search-and-replace corruptions
    for pat, rep in CORRUPTION_REPAIRS:
        text = pat.sub(rep, text)

    # Step 5: Remove page numbering stamps and decorative divider lines
    text = PAGE_NUMBER_PATTERN.sub(" ", text)
    text = PAGE_NUM_STANDALONE.sub(" ", text)
    text = PAGE_NUM_BARE.sub(" ", text)
    text = DIVIDER_LINES.sub(" ", text)

    # Step 6: Normalize whitespace and multiple newlines
    text = re.sub(r"[ ]{2,}", " ", text)
    text = re.sub(r"\r?\n[ \t]*\r?\n+", "\n\n", text)
    return text.strip()

def process_dataset(input_file: Path, output_file: Path, sample_size: int = None):
    print("=" * 65)
    print("CiteJustice - OCR Noise Removal Pipeline")
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

    # Add new output columns
    out_fields = fieldnames + ["cleaned_text", "raw_char_count", "cleaned_char_count", "chars_removed"]
    
    total_raw_chars = 0
    total_clean_chars = 0

    with open(output_file, mode="w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=out_fields)
        writer.writeheader()

        for idx, row in enumerate(rows, 1):
            raw_text = row.get("text", "")
            clean_text = remove_ocr_noise(raw_text)

            raw_len = len(raw_text)
            clean_len = len(clean_text)
            removed = raw_len - clean_len

            total_raw_chars += raw_len
            total_clean_chars += clean_len

            row["cleaned_text"] = clean_text
            row["raw_char_count"] = raw_len
            row["cleaned_char_count"] = clean_len
            row["chars_removed"] = removed

            writer.writerow(row)

            if idx % 500 == 0 or idx == total_records:
                print(f"  Processed {idx:,} / {total_records:,} cases ({(idx/total_records)*100:.1f}%)...")

    print(f"\n[OK] Cleaned dataset saved to: {output_file}")

    total_removed = total_raw_chars - total_clean_chars
    pct_removed = (total_removed / total_raw_chars * 100) if total_raw_chars > 0 else 0

    print("\n" + "-" * 40)
    print("Execution Summary:")
    print(f"  Cases processed       : {total_records:,}")
    print(f"  Total raw characters  : {total_raw_chars:,}")
    print(f"  Clean characters      : {total_clean_chars:,}")
    print(f"  Garbage chars removed : {total_removed:,} ({pct_removed:.2f}%)")
    print("-" * 40)

def main():
    parser = argparse.ArgumentParser(description="Remove OCR noise and artifacts from ILDC cases.")
    parser.add_argument("--dataset", choices=["single", "multi"], default="single",
                        help="Choose dataset to clean: 'single' (9,110 cases) or 'multi' (34,816 cases). Default is single.")
    parser.add_argument("--sample", type=int, default=None,
                        help="Process only a sample of N cases for fast testing.")
    args = parser.parse_args()

    input_filename = "ILDC_single.csv" if args.dataset == "single" else "ILDC_multi.csv"
    output_filename = f"ildc_{args.dataset}_noise_removed.csv"
    if args.sample:
        output_filename = f"ildc_{args.dataset}_sample_{args.sample}_clean.csv"

    input_path = RAW_DIR / input_filename
    output_path = CLEAN_DIR / output_filename

    process_dataset(input_path, output_path, sample_size=args.sample)

if __name__ == "__main__":
    main()
