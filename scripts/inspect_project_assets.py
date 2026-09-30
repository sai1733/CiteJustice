"""
scripts/inspect_project_assets.py
Deeply inspects CiteJustice_Research_Paper.docx and ppt.pptx
"""

import sys
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

outer = Path("..")

# 1. Inspect ppt.pptx
pptx = outer / "ppt.pptx"
if pptx.exists():
    print("=" * 70)
    print("PPTX SLIDES INSPECTION")
    print("=" * 70)
    with zipfile.ZipFile(pptx) as z:
        slides = sorted([f for f in z.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')],
                        key=lambda x: int(x.replace('ppt/slides/slide','').replace('.xml','')))
        for idx, sf in enumerate(slides):
            tree = ET.fromstring(z.read(sf))
            texts = [node.text.strip() for node in tree.iter('{http://schemas.openxmlformats.org/drawingml/2006/main}t') if node.text and node.text.strip()]
            print(f"\n--- SLIDE {idx+1} ---")
            print("\n".join(texts))

# 2. Inspect docx
docx = outer / "CiteJustice_Research_Paper.docx"
if docx.exists():
    print("\n" + "=" * 70)
    print("RESEARCH PAPER DOCX INSPECTION")
    print("=" * 70)
    with zipfile.ZipFile(docx) as z:
        tree = ET.fromstring(z.read('word/document.xml'))
        paras = []
        for p in tree.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
            t = "".join([node.text for node in p.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t') if node.text])
            if t.strip():
                paras.append(t.strip())
        print(f"Total Paragraphs: {len(paras)}")
        print("\n--- PAPER OUTLINE / HEADINGS ---")
        for p in paras:
            if any(p.startswith(h) for h in ["I.", "II.", "III.", "IV.", "V.", "VI.", "VII.", "VIII.", "Abstract", "Keywords", "TABLE", "Fig"]):
                print(p[:120])
