# data/

Everything in this folder except this file is git-ignored.

Freddie Mac's Single-Family Loan-Level Dataset is free for non-commercial use but may not be
redistributed, so each user downloads it themselves:

1. Register at https://www.freddiemac.com/research/datasets/sf-loanlevel-dataset
2. Download the **sample** files first (e.g. `sample_2019.zip`) and unzip into `data/raw/`:

```
data/raw/sample_orig_2019.txt   # origination: one row per loan
data/raw/sample_svcg_2019.txt   # servicing/performance: one row per loan per month
```

3. Run `python -m mortgage_risk.ingest data/raw` to write partitioned Parquet into `data/parquet/`.
