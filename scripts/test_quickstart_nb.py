"""
scripts/test_quickstart_nb.py

Executes all code cells in notebooks/quickstart.ipynb and verifies 100% success.
Author: Sai Sonawane
"""

import sys
import json
from pathlib import Path

# Reconfigure stdout for utf-8 on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def test_notebook():
    nb_path = Path("notebooks/quickstart.ipynb")
    assert nb_path.exists(), f"Notebook not found at {nb_path}"

    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    total_cells = len(nb["cells"])
    print(f"Loaded {nb_path.name} with {total_cells} cells.")

    # Execution environment
    global_scope = {"__file__": str(nb_path.resolve()), "display": print}

    code_cell_count = 0
    for idx, cell in enumerate(nb["cells"]):
        if cell["cell_type"] == "code":
            code_cell_count += 1
            code_str = "".join(cell["source"])
            print(f"\n[Executing Code Cell #{code_cell_count} (index {idx})]")
            try:
                exec(code_str, global_scope)
                print(f"  -> Cell #{code_cell_count} PASSED.")
            except Exception as e:
                print(f"  -> Cell #{code_cell_count} FAILED: {e}")
                raise e

    print("\n" + "=" * 60)
    print("ALL QUICKSTART NOTEBOOK CELLS EXECUTED WITH ZERO ERRORS!")
    print("=" * 60)

if __name__ == "__main__":
    test_notebook()
