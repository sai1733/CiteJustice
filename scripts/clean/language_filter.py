"""
scripts/clean/language_filter.py

Pipeline module to detect, tag, and filter cases by language:
1. Detects primary language using langdetect across document samples.
2. Identifies mixed-language documents (e.g. English judgments quoting vernacular FIRs/depositions).
3. Produces a clean English-primary dataset for CiteJustice V1 training.
4. Segregates non-English or heavily mixed cases for future multilingual V2 analysis.

Usage:
    python scripts/clean/language_filter.py --sample 50
    python scripts/clean/language_filter.py --dataset single
    python scripts/clean/language_filter.py --dataset multi
"""

import os
import sys
import csv
import argparse
from pathlib import Path
from collections import Counter

# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "ildc"
CLEAN_DIR = BASE_DIR / "data" / "clean"
CLEAN_DIR.mkdir(parents=True, exist_ok=True)

# Attempt to import langdetect with graceful fallback
try:
    from langdetect import detect_langs, DetectorFactory
    DetectorFactory.seed = 42
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

def detect_case_language(text: str) -> tuple[str, float, bool]:
    """
    Detects the primary language and whether the case is mixed-language.
    Returns:
        (primary_language_code, confidence_score, is_mixed_flag)
    """
    if not isinstance(text, str) or not text.strip():
        return ("unknown", 0.0, False)

    if not LANGDETECT_AVAILABLE:
        # Fallback heuristic: check ASCII / Latin character ratio
        latin_chars = sum(1 for c in text if c.isascii() and c.isalpha())
        total_chars = max(1, sum(1 for c in text if c.isalpha()))
        ratio = latin_chars / total_chars
        if ratio > 0.85:
            return ("en", ratio, False)
        else:
            return ("non-en", 1.0 - ratio, True)

    try:
        # Sample slices from head, middle, and tail to catch mixed language excerpts
        text_len = len(text)
        samples = []
        samples.append(text[:1500])
        if text_len > 3000:
            mid = text_len // 2
            samples.append(text[mid:mid + 1500])
        if text_len > 6000:
            samples.append(text[-1500:])

        all_detected = []
        for s in samples:
            if len(s.strip()) > 50:
                langs = detect_langs(s)
                all_detected.extend(langs)

        if not all_detected:
            return ("en", 0.5, False)

        # Count frequencies of languages across samples
        top_lang = max(all_detected, key=lambda x: x.prob)
        primary_lang = top_lang.lang
        confidence = round(top_lang.prob, 3)

        # Check if another language with notable probability (>0.25) exists
        secondary_langs = [l for l in all_detected if l.lang != primary_lang and l.prob > 0.25]
        is_mixed = len(secondary_langs) > 0

        return (primary_lang, confidence, is_mixed)

    except Exception:
        return ("en", 0.5, False)

def process_dataset(input_file: Path, output_file: Path, sample_size: int = None):
    print("=" * 65)
    print("CiteJustice - Language Filtering & Tagging Pipeline")
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

    out_fields = fieldnames + ["detected_language", "lang_confidence", "is_mixed_language", "is_english_primary"]
    
    lang_counter = Counter()
    mixed_count = 0
    english_primary_count = 0

    english_rows = []
    non_english_rows = []

    for idx, row in enumerate(rows, 1):
        # Prefer cleanest available text representation
        src_text = (
            row.get("text_with_normalized_sections")
            or row.get("normalized_text")
            or row.get("cleaned_text")
            or row.get("text", "")
        )

        lang, conf, is_mixed = detect_case_language(src_text)
        is_english = (lang == "en")

        row["detected_language"] = lang
        row["lang_confidence"] = conf
        row["is_mixed_language"] = is_mixed
        row["is_english_primary"] = is_english

        lang_counter[lang] += 1
        if is_mixed:
            mixed_count += 1
        if is_english:
            english_primary_count += 1
            english_rows.append(row)
        else:
            non_english_rows.append(row)

        if idx % 500 == 0 or idx == total_records:
            print(f"  Processed {idx:,} / {total_records:,} cases ({(idx/total_records)*100:.1f}%)...")

    # Save English-primary dataset (V1 benchmark training set)
    with open(output_file, mode="w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=out_fields)
        writer.writeheader()
        writer.writerows(english_rows)

    # Save non-English / segregated cases if any exist
    if non_english_rows:
        segregated_file = output_file.parent / (output_file.stem + "_non_english_flagged.csv")
        with open(segregated_file, mode="w", encoding="utf-8", newline="") as f_seg:
            writer = csv.DictWriter(f_seg, fieldnames=out_fields)
            writer.writeheader()
            writer.writerows(non_english_rows)
        print(f"[Notice] Segregated {len(non_english_rows)} non-English cases into: {segregated_file.name}")

    print(f"\n[OK] English-primary dataset saved to: {output_file}")

    print("\n" + "-" * 40)
    print("Execution Summary:")
    print(f"  Cases evaluated              : {total_records:,}")
    print(f"  English-primary cases (V1)   : {english_primary_count:,} ({(english_primary_count/total_records)*100:.1f}%)")
    print(f"  Non-English cases            : {len(non_english_rows):,}")
    print(f"  Mixed-language flagged cases : {mixed_count:,} ({(mixed_count/total_records)*100:.1f}%)")
    print("  Language distribution:")
    for l_code, count_val in lang_counter.most_common(5):
        print(f"    - {l_code:<6}: {count_val:>5,} cases")
    print("-" * 40)

def main():
    parser = argparse.ArgumentParser(description="Language detection and filtering for ILDC cases.")
    parser.add_argument("--dataset", choices=["single", "multi"], default="single",
                        help="Dataset to filter: 'single' (9,110 cases) or 'multi' (34,816 cases).")
    parser.add_argument("--sample", type=int, default=None,
                        help="Process only a sample of N cases for fast testing.")
    args = parser.parse_args()

    # Cascade inputs: prefer Task 3 (sections) -> Task 2 (citations) -> Task 1 (noise) -> raw
    t3_input = CLEAN_DIR / f"ildc_{args.dataset}_sections_normalized.csv"
    t2_input = CLEAN_DIR / f"ildc_{args.dataset}_citations_normalized.csv"
    t1_input = CLEAN_DIR / f"ildc_{args.dataset}_noise_removed.csv"
    raw_input = RAW_DIR / ("ILDC_single.csv" if args.dataset == "single" else "ILDC_multi.csv")

    if t3_input.exists():
        input_path = t3_input
    elif t2_input.exists():
        input_path = t2_input
    elif t1_input.exists():
        input_path = t1_input
    else:
        input_path = raw_input

    output_filename = f"ildc_{args.dataset}_english_primary.csv"
    if args.sample:
        output_filename = f"ildc_{args.dataset}_sample_{args.sample}_english.csv"

    output_path = CLEAN_DIR / output_filename
    process_dataset(input_path, output_path, sample_size=args.sample)

if __name__ == "__main__":
    main()
