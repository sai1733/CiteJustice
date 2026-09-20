"""
scripts/clean/clean_ildc.py
Hands-on cleaning pipeline for the Indian Legal Documents Corpus (ILDC).

Addresses:
1. Digital signature and registry stamps (e-filing / e-Courts PDF stamps)
2. Well-known ILDC textual corruption artifacts ("company" and "number" replacement bugs)
3. Spacing, punctuation, and citation formatting irregularities
4. Page numbers and court metadata footers
"""

import os
import re
import pandas as pd
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
RAW_CSV = BASE_DIR / "data" / "raw" / "ildc" / "ILDC_single.csv"
OUTPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_SAMPLE_CSV = OUTPUT_DIR / "ildc_cleaned_sample.csv"

# 1. Known ILDC automated replacement corruptions
# In the original ILDC pipeline, naive substrings were replaced (e.g. 'co' -> 'company', 'not'/'no' -> 'number')
CORRUPTION_MAP = [
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
    (re.compile(r"\bcompanyvict\b", re.IGNORECASE), "convict"),
    (re.compile(r"\bcompanyviction\b", re.IGNORECASE), "conviction"),
    
    # "number" corruption repairs
    (re.compile(r"\bnumberice\b", re.IGNORECASE), "notice"),
    (re.compile(r"\bnumberices\b", re.IGNORECASE), "notices"),
    (re.compile(r"\bnumber affirmed\b", re.IGNORECASE), "not affirmed"),
    (re.compile(r"\bnumber duly\b", re.IGNORECASE), "not duly"),
    (re.compile(r"\bnumber did it\b", re.IGNORECASE), "nor did it"),
]

# 2. Digital signature and registry metadata patterns (two-part marginal stamps in SC PDFs)
DIGITAL_SIG1_REGEX = re.compile(
    r"\bSignature\s+Not\s+Verified\b",
    re.IGNORECASE
)
DIGITAL_SIG2_REGEX = re.compile(
    r"\bDigitally\s+signed\s+by\s+[A-Za-z\.\s]{2,40}?\s*Date\s*[:\s]*[\d\.\s:]{8,25}(?:IST|GMT)?\s*(?:Reason\b)?",
    re.IGNORECASE
)

# 3. Citation spacing normalization (e.g. " 1977  2 SCC 732" -> "(1977) 2 SCC 732")
UNPARENTHESIZED_SCC = re.compile(
    r"\b(?<!\()((?:19|20)\d{2})\s+(\d+)\s+SCC\s+(\d+)\b"
)
UNPARENTHESIZED_SCR = re.compile(
    r"\b(?<!\[)((?:19|20)\d{2})\s+(\d+)\s+SCR\s+(\d+)\b"
)

# 4. Page numbering and footer stamps
PAGE_NUM_REGEX = re.compile(r"(?im)^\s*Page\s+\d+\s+of\s+\d+\s*$")
DASHED_LINES = re.compile(r"[-_=]{4,}")

def clean_judgment_text(text: str) -> str:
    """Applies a sequence of cleaning rules to raw Indian judgment text."""
    if not isinstance(text, str):
        return ""

    # Step 1: Remove digital signatures & registry stamps
    text = DIGITAL_SIG1_REGEX.sub(" ", text)
    text = DIGITAL_SIG2_REGEX.sub(" ", text)

    # Step 2: Fix ILDC string corruption artifacts
    for pattern, replacement in CORRUPTION_MAP:
        text = pattern.sub(replacement, text)

    # Step 3: Remove page numbering / divider lines
    text = PAGE_NUM_REGEX.sub(" ", text)
    text = DASHED_LINES.sub(" ", text)

    # Step 4: Normalize unparenthesized reporter citations
    text = UNPARENTHESIZED_SCC.sub(r"(\1) \2 SCC \3", text)
    text = UNPARENTHESIZED_SCR.sub(r"[\1] \2 SCR \3", text)

    # Step 5: Normalize unicode quotes and dashes
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("—", " - ").replace("–", " - ")

    # Step 6: Normalize whitespace and newlines
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    text = text.strip()

    return text

def main():
    print("=" * 70)
    print("CiteJustice - ILDC Text Cleaning Pipeline (Hands-on Verification)")
    print("=" * 70)

    if not RAW_CSV.exists():
        print(f"[Error] Raw dataset not found at {RAW_CSV}")
        return

    print(f"Reading sample records from: {RAW_CSV}")
    df = pd.read_csv(RAW_CSV, nrows=5)
    print(f"Loaded {len(df)} sample cases.\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cleaned_rows = []

    for idx, row in df.iterrows():
        raw_text = row["text"]
        cleaned_text = clean_judgment_text(raw_text)
        
        # Calculate statistics
        raw_len = len(raw_text)
        clean_len = len(cleaned_text)
        diff = raw_len - clean_len

        print(f"----------------------------------------------------------------------")
        print(f"CASE {idx} (ID: {row.get('id', idx)}) | Label: {row.get('label')} | Split: {row.get('split')}")
        print(f"Original Length: {raw_len:,} chars | Cleaned: {clean_len:,} chars (diff: -{diff:,})")
        print(f"----------------------------------------------------------------------")
        
        print("\n[BEFORE - Raw Snippet]:")
        print(raw_text[:350].replace("\n", " "))
        print("\n[AFTER - Cleaned Snippet]:")
        print(cleaned_text[:350].replace("\n", " "))
        print("\n")

        row_copy = row.to_dict()
        row_copy["cleaned_text"] = cleaned_text
        cleaned_rows.append(row_copy)

    # Save cleaned sample
    sample_df = pd.DataFrame(cleaned_rows)
    sample_df.to_csv(OUTPUT_SAMPLE_CSV, index=False)
    print("=" * 70)
    print(f"[OK] Cleaned sample successfully saved to: {OUTPUT_SAMPLE_CSV}")
    print("=" * 70)

if __name__ == "__main__":
    main()
