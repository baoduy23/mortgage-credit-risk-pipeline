"""Load raw Freddie Mac SFLLD text files into Parquet partitioned by vintage year.

Raw files are pipe-delimited with no header. Every column is kept as VARCHAR here;
typing and sentinel handling (e.g. credit_score 9999 = not available) happen in dbt staging,
so this layer stays a faithful copy of the source.

Usage:
    python -m mortgage_risk.ingest data/raw --out data/parquet
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import duckdb
import yaml

LAYOUT_PATH = Path(__file__).resolve().parents[2] / "config" / "file_layout.yml"

# sample_orig_2019.txt / sample_svcg_2019.txt (sample dataset)
# historical_data_2019Q1.txt / historical_data_time_2019Q1.txt (full dataset)
FILE_PATTERNS = {
    "origination": [
        re.compile(r"^sample_orig_(?P<year>\d{4})\.txt$"),
        re.compile(r"^historical_data_(?P<year>\d{4})(?P<quarter>Q[1-4])\.txt$"),
    ],
    "performance": [
        re.compile(r"^sample_svcg_(?P<year>\d{4})\.txt$"),
        re.compile(r"^historical_data_time_(?P<year>\d{4})(?P<quarter>Q[1-4])\.txt$"),
    ],
}


class LayoutMismatchError(ValueError):
    """Raised when a raw file's column count does not match config/file_layout.yml."""


def load_layout(path: Path = LAYOUT_PATH) -> dict[str, list[str]]:
    with open(path) as f:
        return yaml.safe_load(f)


def classify(path: Path) -> tuple[str, str, str | None] | None:
    """Return (kind, vintage_year, quarter) for a recognised raw file, else None."""
    for kind, patterns in FILE_PATTERNS.items():
        for pattern in patterns:
            m = pattern.match(path.name)
            if m:
                return kind, m.group("year"), m.groupdict().get("quarter")
    return None


def check_column_count(path: Path, expected: list[str]) -> None:
    with open(path, encoding="latin-1") as f:
        first_line = f.readline().rstrip("\r\n")
    found = first_line.count("|") + 1
    if found != len(expected):
        raise LayoutMismatchError(
            f"{path.name}: found {found} columns, layout expects {len(expected)}. "
            "Update config/file_layout.yml from the current Freddie Mac File Layout."
        )


def ingest_file(
    con: duckdb.DuckDBPyConnection, path: Path, out_dir: Path, layout: dict[str, list[str]]
) -> Path:
    info = classify(path)
    if info is None:
        raise ValueError(f"Unrecognised file name: {path.name}")
    kind, year, quarter = info
    columns = layout[kind]
    check_column_count(path, columns)

    # One file per source file keeps re-runs idempotent: re-ingesting overwrites, never appends.
    target_dir = out_dir / kind / f"vintage_year={year}"
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{path.stem}.parquet"

    col_spec = "{" + ", ".join(f"'{c}': 'VARCHAR'" for c in columns) + "}"
    con.execute(
        f"""
        COPY (
            SELECT *, '{path.name}' AS source_file{f", '{quarter}' AS vintage_quarter" if quarter else ""}
            FROM read_csv(?, delim='|', header=false, columns={col_spec}, quote='', escape='')
        ) TO '{target}' (FORMAT parquet, COMPRESSION zstd)
        """,
        [str(path)],
    )
    return target


def ingest_dir(raw_dir: Path, out_dir: Path) -> list[Path]:
    layout = load_layout()
    files = sorted(p for p in raw_dir.glob("*.txt") if classify(p) is not None)
    if not files:
        raise FileNotFoundError(f"No Freddie Mac files found in {raw_dir}. See data/README.md.")
    con = duckdb.connect()
    written = []
    for path in files:
        target = ingest_file(con, path, out_dir, layout)
        print(f"{path.name} -> {target}")
        written.append(target)
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("raw_dir", type=Path)
    parser.add_argument("--out", type=Path, default=Path("data/parquet"))
    args = parser.parse_args()
    ingest_dir(args.raw_dir, args.out)


if __name__ == "__main__":
    main()
