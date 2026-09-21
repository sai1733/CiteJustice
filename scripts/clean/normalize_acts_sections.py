"""
scripts/clean/normalize_acts_sections.py

Pipeline module to normalize Indian statutory sections and acts into canonical identifiers:
Format: ACT_SECTION (e.g. IPC_302, CrPC_482, NI_ACT_138, COI_ART_21)

Leverages:
- docs/act_lookup.csv (Act name to standard abbreviation mapping)
- docs/section_formats.md (Syntactic section prefixes & compound offenses)

Usage:
    python scripts/clean/normalize_acts_sections.py --sample 50
    python scripts/clean/normalize_acts_sections.py --dataset single
    python scripts/clean/normalize_acts_sections.py --dataset multi
"""

import os
import re
import sys
import csv
import json
import argparse
from pathlib import Path

# Increase CSV field size limit
csv.field_size_limit(sys.maxsize)

BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "ildc"
CLEAN_DIR = BASE_DIR / "data" / "clean"
DOCS_DIR = BASE_DIR / "docs"

CLEAN_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------
# 1. Load and Compile Act Lookup Patterns
# --------------------------------------------------------------------------
def load_act_patterns(csv_path: Path):
    patterns = []
    if not csv_path.exists():
        return [
            (re.compile(r"\b(?:I\.?P\.?C\.?|Indian\s+Penal\s+Code)\b", re.I), "IPC"),
            (re.compile(r"\b(?:Cr\.?P\.?C\.?|Code\s+of\s+Criminal\s+Procedure)\b", re.I), "CrPC"),
            (re.compile(r"\b(?:C\.?P\.?C\.?|Code\s+of\s+Civil\s+Procedure)\b", re.I), "CPC"),
            (re.compile(r"\b(?:I\.?E\.?A\.?|Indian\s+Evidence\s+Act|Evidence\s+Act)\b", re.I), "IEA"),
            (re.compile(r"\b(?:N\.?I\.?\s*Act|Negotiable\s+Instruments\s+Act)\b", re.I), "NI_ACT"),
            (re.compile(r"\b(?:Constitution\s+of\s+India|the\s+Constitution)\b", re.I), "COI"),
        ]

    with open(csv_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            abbr = row["abbreviation"].strip().replace(" ", "_")
            pat_str = row.get("regex_pattern", "").strip()
            if pat_str:
                try:
                    compiled = re.compile(pat_str, re.IGNORECASE)
                    patterns.append((compiled, abbr))
                except re.error:
                    pass
    return patterns

ACT_LOOKUP = load_act_patterns(DOCS_DIR / "act_lookup.csv")

# --------------------------------------------------------------------------
# 2. Section Patterns & Matchers
# --------------------------------------------------------------------------
SECTION_WITH_EXPLICIT_ACT = re.compile(
    r"(?i)\b(?:under\s+sections?|u/s\.?|u/sec\.?|sections?|secs?\.?|s\.?|§)\s*"
    r"(?P<sections>\d+[A-Z]?(?:/\d+[A-Z]?)*(?:\([0-9a-zA-Z]+\))*)"
    r"(?:\s+(?:of\s+(?:the\s+)?)?(?P<act_phrase>[A-Za-z\.\s\(\)-]{2,50}?))"
    r"(?=[,\.;\s]|$)"
)

ARTICLE_REGEX = re.compile(
    r"(?i)\b(?:articles?|arts?\.?)\s*(?P<article>\d+[A-Z]?(?:\([0-9a-zA-Z]+\))*)"
    r"(?:\s+of\s+the\s+Constitution(?:\s+of\s+India)?)?\b"
)

STANDALONE_SECTION_REGEX = re.compile(
    r"(?i)\b(?:under\s+sections?|u/s\.?|u/sec\.?|sections?|secs?\.?|s\.?|§)\s*"
    r"(?P<sections>\d+[A-Z]?(?:/\d+[A-Z]?)*(?:\([0-9a-zA-Z]+\))*)\b"
)

def resolve_act_abbreviation(phrase: str) -> str:
    if not phrase:
        return ""
    phrase = phrase.strip()
    for compiled_pat, abbr in ACT_LOOKUP:
        if compiled_pat.search(phrase):
            return abbr
    return ""

def clean_section_token(sec: str) -> str:
    return sec.strip().replace("-", "").upper()

def normalize_sections_and_acts(text: str) -> tuple[str, list[str]]:
    if not isinstance(text, str) or not text.strip():
        return "", []

    found_sections = set()

    # Step 1: Normalize Constitutional Articles
    def repl_article(m):
        art = clean_section_token(m.group("article"))
        tag = f"COI_ART_{art}"
        found_sections.add(tag)
        return tag

    text = ARTICLE_REGEX.sub(repl_article, text)

    # Step 2: Normalize sections followed explicitly by an Act name
    def repl_explicit_act(m):
        raw_secs = m.group("sections")
        act_phrase = m.group("act_phrase") or ""
        act_abbr = resolve_act_abbreviation(act_phrase)

        if not act_abbr:
            return m.group(0)

        tags = []
        for sec in raw_secs.split("/"):
            sec_clean = clean_section_token(sec)
            if sec_clean:
                tag = f"{act_abbr}_{sec_clean}"
                tags.append(tag)
                found_sections.add(tag)

        return " ".join(tags)

    text = SECTION_WITH_EXPLICIT_ACT.sub(repl_explicit_act, text)

    # Step 3: Handle standalone sections
    def repl_standalone(m):
        raw_secs = m.group("sections")
        tags = []
        for sec in raw_secs.split("/"):
            sec_clean = clean_section_token(sec)
            if sec_clean:
                tag = f"SEC_{sec_clean}"
                tags.append(tag)
                found_sections.add(tag)
        return " ".join(tags)

    text = STANDALONE_SECTION_REGEX.sub(repl_standalone, text)

    return text, sorted(list(found_sections))

def process_dataset(input_file: Path, output_file: Path, sample_size: int = None):
    print("=" * 65)
    print("CiteJustice - Statutory Section Normalization Pipeline")
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

    out_fields = fieldnames + ["text_with_normalized_sections", "statutory_sections", "section_count"]
    total_sections_extracted = 0
    cases_with_sections = 0

    with open(output_file, mode="w", encoding="utf-8", newline="") as f_out:
        writer = csv.DictWriter(f_out, fieldnames=out_fields)
        writer.writeheader()

        for idx, row in enumerate(rows, 1):
            src_text = row.get("normalized_text") or row.get("cleaned_text") or row.get("text", "")
            norm_text, sections = normalize_sections_and_acts(src_text)

            row["text_with_normalized_sections"] = norm_text
            row["statutory_sections"] = json.dumps(sections)
            row["section_count"] = len(sections)

            if sections:
                cases_with_sections += 1
                total_sections_extracted += len(sections)

            writer.writerow(row)

            if idx % 500 == 0 or idx == total_records:
                print(f"  Processed {idx:,} / {total_records:,} cases ({(idx/total_records)*100:.1f}%)...")

    print(f"\n[OK] Section-normalized dataset saved to: {output_file}")

    print("\n" + "-" * 40)
    print("Execution Summary:")
    print(f"  Cases processed              : {total_records:,}")
    print(f"  Cases citing statutory laws  : {cases_with_sections:,} ({(cases_with_sections/total_records)*100:.1f}%)")
    print(f"  Total sections extracted     : {total_sections_extracted:,}")
    print(f"  Average sections per case    : {total_sections_extracted/total_records:.2f}")
    print("-" * 40)

def main():
    parser = argparse.ArgumentParser(description="Normalize statutory acts & sections in ILDC cases.")
    parser.add_argument("--dataset", choices=["single", "multi"], default="single",
                        help="Dataset to process: 'single' (9,110 cases) or 'multi' (34,816 cases).")
    parser.add_argument("--sample", type=int, default=None,
                        help="Process only a sample of N cases for fast testing.")
    args = parser.parse_args()

    t2_input = CLEAN_DIR / f"ildc_{args.dataset}_citations_normalized.csv"
    t1_input = CLEAN_DIR / f"ildc_{args.dataset}_noise_removed.csv"
    raw_input = RAW_DIR / ("ILDC_single.csv" if args.dataset == "single" else "ILDC_multi.csv")

    if t2_input.exists():
        input_path = t2_input
    elif t1_input.exists():
        input_path = t1_input
    else:
        input_path = raw_input

    output_filename = f"ildc_{args.dataset}_sections_normalized.csv"
    if args.sample:
        output_filename = f"ildc_{args.dataset}_sample_{args.sample}_sections.csv"

    output_path = CLEAN_DIR / output_filename
    process_dataset(input_path, output_path, sample_size=args.sample)

if __name__ == "__main__":
    main()
