
import pandas as pd

def read_xlsx(path):
    print(f"Reading {path}")
    try:
        xl = pd.ExcelFile(path)
        for sheet in xl.sheet_names:
            if "REQUIREMENTS" in sheet or "RESIDENTS" in sheet:
                print(f"\n--- Sheet: {sheet} ---")
                df = pd.read_excel(path, sheet_name=sheet)
                print(df.head(20))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    read_xlsx("2025 Updated Schedule - Copy 2026.xlsx")
