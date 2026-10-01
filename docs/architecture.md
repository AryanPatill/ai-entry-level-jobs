# Architecture

How the repository is laid out, how data moves through it, and how to run each stage.
Design questions belong in `preregistration.md`; tool choices belong in `decisions.md`.

## Principles

1. **The repository holds definitions, never microdata.** IPUMS data lives in `data/`,
   which git ignores. What is committed is the extract definition, the extract log with
   file hashes, and the code, so anyone with an IPUMS key can rebuild the data exactly.
2. **Design parameters are copied from the preregistration into `config/settings.yaml`,
   never invented in code.**
3. **Every stage is a module run with `python -m`,** from the repository root, and is safe
   to re-run. Re-running does not resubmit an extract or rebuild an existing Parquet file
   unless `--force` is passed.
4. **Notebooks explore; `src/` decides.** Anything a result depends on lives in `src/`.

## Data flow

```
IPUMS CPS API
  |  src/data/extract_definition.py   builds the request from settings.yaml
  v
docs/extract_definition.json          committed: samples, variables, case selection
  |  src/data/ipums_extract.py        submit / status / download
  v
data/raw/cps_extract_00001/           .dat.gz + .xml codebook (never committed)
  |  src/data/convert_to_parquet.py   chunked read, hash check, structural checks
  v
data/raw/cps_extract_00001/*.parquet  12,080,926 person records
  |  src/crosswalks/                  occupation exposure (Phase 4), industry sectors
  |  src/data/ (Phase 5)              sample construction
  v
data/processed/                       analysis panel
  |  src/analysis/ (Phases 6-10)
  v
results/tables/, results/figures/
```

## Layout

```
ai-entry-level-jobs/
├── config/settings.yaml          design parameters copied from the preregistration
├── docs/                         see docs/index.md for what lives where
├── src/
│   ├── data/                     acquisition, conversion, inspection
│   │   ├── check_ipums.py         API key check
│   │   ├── extract_definition.py  build and save the extract definition
│   │   ├── ipums_extract.py       submit, status, download, extract log
│   │   ├── convert_to_parquet.py  fixed-width -> Parquet, structural checks
│   │   ├── inspect_codes.py       code-level checks (NIU, universes, sample size)
│   │   ├── download_sources.py    Eloundou exposure file, Census occ crosswalk; SHA-256 verified
│   │   └── list_industry_codes.py dump IND1990 codes with codebook labels
│   ├── crosswalks/
│   │   ├── industry_sectors.py    IND1990 -> six preregistered sectors
│   │   └── occupation_exposure.py 2010 Census occ -> SOC 2018 -> exposure; coverage report
│   ├── analysis/                 Phases 6-10
│   ├── agents/                   Phase 11
│   └── utils/config.py           settings loader, REPO_ROOT, .env secrets
├── tests/                        pytest; run with `python -m pytest -q`
├── data/                         git-ignored: raw, interim, processed
├── results/                      tables and figures
├── notebooks/                    exploration only
└── app/                          Streamlit dashboard (Phase 13)
```

## Commands

| Stage | Command |
|---|---|
| Check the IPUMS key | `python -m src.data.check_ipums` |
| Build the extract definition | `python -m src.data.extract_definition` |
| Submit / check / download | `python -m src.data.ipums_extract submit \| status \| download` |
| Convert and check | `python -m src.data.convert_to_parquet` (`--force` to rebuild) |
| Code-level checks | `python -m src.data.inspect_codes` |
| Exposure file and occupation crosswalk (download + hash check) | `python -m src.data.download_sources` |
| Occupation -> exposure map and coverage report | `python -m src.crosswalks.occupation_exposure` |
| Industry codes and sectors | `python -m src.data.list_industry_codes` then `python -m src.crosswalks.industry_sectors` |
| Tests | `python -m pytest -q` |

## Conventions

- **Environment:** Python 3.12.10 in `.venv`; packages pinned in `requirements-lock.txt`.
- **Secrets:** `.env`, never committed. `.env.example` lists the names only.
- **Encoding:** all text files are UTF-8. Never create or edit a tracked file with
  PowerShell `>` or `Out-File`; both write UTF-16, which git treats as binary.
- **Integrity:** every downloaded file's SHA-256 is recorded in `docs/extract_log.json`
  and re-checked before the file is read.
- **Outputs that are safe to commit:** anything aggregated (code lists, sector maps,
  counts). Individual records are never committed.
- **Commits:** one per completed step, pushed immediately. The commit message names the
  phase and step. Documentation is committed with the code it describes.
