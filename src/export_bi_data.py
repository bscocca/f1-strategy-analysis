"""Build the data file for the Tableau Public dashboard.

Writes bi/f1_strategy.xlsx, with one sheet per table. Excel is used instead
of CSV because it stores numbers as numbers whatever the language settings
of the computer: in a CSV, a decimal point can be misread in locales that
use a decimal comma, such as Italian.

Run it after notebooks 03 and 04:
    python src/export_bi_data.py
"""

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
BI_DIR = ROOT / "bi"
OUTPUT_PATH = BI_DIR / "f1_strategy.xlsx"

SHEETS = {
    "degradation": "tyre_degradation_by_race.parquet",
    "undercut_attempts": "undercut_attempts.parquet",
}


def main() -> None:
    BI_DIR.mkdir(parents=True, exist_ok=True)

    tables = {}
    for sheet, file_name in SHEETS.items():
        source = PROCESSED_DIR / file_name
        if not source.exists():
            raise SystemExit(
                f"{source} not found: run notebooks 03 and 04 before this script."
            )
        tables[sheet] = pd.read_parquet(source)

    with pd.ExcelWriter(OUTPUT_PATH) as writer:
        for sheet, table in tables.items():
            table.to_excel(writer, sheet_name=sheet, index=False)
            print(f"{sheet}: {len(table):,} rows, columns: {', '.join(table.columns)}")

    print(f"Saved {OUTPUT_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()