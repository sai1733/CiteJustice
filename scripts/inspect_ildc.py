import pandas as pd

df = pd.read_csv('data/raw/ildc/ILDC_single.csv', nrows=10)
print('Columns:', df.columns.tolist())
for idx, row in df.iterrows():
    print(f"=== Case {idx}: len={len(row['text'])} label={row.get('label')} split={row.get('split')} ===")
    print(row['text'][:500])
    print("-" * 50)
