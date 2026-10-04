"""Convert the cached IPEDS parquet files into the CSV layout the Go ingest reads.

    data/ipeds_cache/<year>/<dataset>.parquet  ->  data/ipeds_data/<year>/<dataset>/<dataset>.csv

nces.ed.gov is often unreachable, so the pipeline ingests from this cache instead of downloading.
The parquet files keep the raw IPEDS column names (UNITID, INSTNM, ...), which is what
server/ipeds.go expects.

Usage (from the project root):
    python server/scripts/ipeds/parquet_to_csv.py [year ...]     # default: every cached year
"""

import sys
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.csv as pacsv
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[3]
CACHE = ROOT / "data" / "ipeds_cache"
OUT = ROOT / "data" / "ipeds_data"


def whole_floats_as_ints(table: pa.Table) -> pa.Table:
    """Floats holding whole numbers become int64, so the CSV says 45679156000, not 4.5679156e+10."""
    for i, field in enumerate(table.schema):
        if not pa.types.is_floating(field.type):
            continue
        col = table.column(i)
        valid = pc.drop_null(col)
        if len(valid) and pc.all(pc.equal(valid, pc.round(valid))).as_py():
            table = table.set_column(i, field.name, pc.cast(col, pa.int64()))
    return table


def convert_year(year: str) -> None:
    files = sorted((CACHE / year).glob("*.parquet"))
    if not files:
        print(f"no parquet files in {CACHE / year}")
        return
    for f in files:
        dataset = f.stem
        target = OUT / year / dataset / f"{dataset}.csv"
        target.parent.mkdir(parents=True, exist_ok=True)
        table = whole_floats_as_ints(pq.read_table(f))
        pacsv.write_csv(table, target)
        print(f"{year}/{dataset}: {table.num_rows} rows")


def main() -> None:
    years = sys.argv[1:] or sorted(p.name for p in CACHE.iterdir() if p.is_dir())
    for year in years:
        convert_year(year)


if __name__ == "__main__":
    main()
