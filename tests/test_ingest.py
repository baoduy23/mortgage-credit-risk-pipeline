from pathlib import Path

import duckdb
import pytest

from mortgage_risk.ingest import LayoutMismatchError, classify, ingest_file, load_layout

LAYOUT = load_layout()


def write_rows(path: Path, n_cols: int, n_rows: int = 2) -> None:
    rows = ["|".join(f"v{r}_{c}" for c in range(n_cols)) for r in range(n_rows)]
    path.write_text("\n".join(rows) + "\n")


@pytest.mark.parametrize(
    "name, expected",
    [
        ("sample_orig_2019.txt", ("origination", "2019", None)),
        ("sample_svcg_2019.txt", ("performance", "2019", None)),
        ("historical_data_2008Q3.txt", ("origination", "2008", "Q3")),
        ("historical_data_time_2008Q3.txt", ("performance", "2008", "Q3")),
        ("notes.txt", None),
    ],
)
def test_classify(name, expected):
    assert classify(Path(name)) == expected


def test_ingest_writes_partitioned_parquet(tmp_path):
    raw = tmp_path / "sample_orig_2019.txt"
    write_rows(raw, len(LAYOUT["origination"]))

    target = ingest_file(duckdb.connect(), raw, tmp_path / "parquet", LAYOUT)

    assert target.parent.name == "vintage_year=2019"
    df = duckdb.sql(f"SELECT * FROM '{target}'").fetchall()
    cols = duckdb.sql(f"SELECT * FROM '{target}'").columns
    assert len(df) == 2
    assert cols[:2] == ["credit_score", "first_payment_date"]
    assert "source_file" in cols


def test_rerun_overwrites_instead_of_appending(tmp_path):
    raw = tmp_path / "sample_svcg_2019.txt"
    write_rows(raw, len(LAYOUT["performance"]))
    con = duckdb.connect()

    ingest_file(con, raw, tmp_path / "parquet", LAYOUT)
    target = ingest_file(con, raw, tmp_path / "parquet", LAYOUT)

    assert duckdb.sql(f"SELECT count(*) FROM '{target}'").fetchone()[0] == 2


def test_layout_mismatch_fails_loudly(tmp_path):
    raw = tmp_path / "sample_orig_2019.txt"
    write_rows(raw, len(LAYOUT["origination"]) + 1)

    with pytest.raises(LayoutMismatchError, match="found 33 columns"):
        ingest_file(duckdb.connect(), raw, tmp_path / "parquet", LAYOUT)
