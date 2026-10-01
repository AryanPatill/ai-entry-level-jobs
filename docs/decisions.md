# Decisions

Choices about how the project is built: tools, versions, formats, conventions, and
interpretations of the preregistration where it left room. Newest last.

Research design choices are in `preregistration.md`. Facts learned from data are in
`design_notes.md`. Departures from the design are in `deviations.md`.

| Date | Decision | Reason |
|---|---|---|
| 2026-09-16 | Run this as a learning project alongside the Grid Load Forecaster | Live, contested question; free data; builds causal inference skills |
| 2026-09-16 | No fixed timeline | Depth over speed |
| 2026-09-16 | Preregister the analysis before seeing any results | Prevents cherry-picking |
| 2026-09-16 | The LLM layer never produces numbers; a local model by default | Accuracy and zero cost |
| 2026-09-16 | The agent layer comes after the core analysis (Phase 11) | The causal analysis must stand on its own |
| 2026-09-17 | OCC2010 as the occupation code system | Harmonised across the window |
| 2026-09-17 | Public repo created and pushed before any data download | The design is timestamped before results exist |
| 2026-09-19 | Project Python 3.12.10 with the built-in venv | The only version every required package supports |
| 2026-09-19 | ipumspy 0.8.2 pinned; pandas <3; pyarrow <24 | Required by ipumspy 0.8.2 |
| 2026-09-19 | pandas and DuckDB only; polars dropped | ipumspy and pyfixest both use pandas |
| 2026-09-19 | Agent, dashboard and FRED packages installed in their own phases | Keeps the environment small |
| 2026-09-19 | `settings.yaml` copies design parameters from the preregistration, never invents them | Keeps config and design consistent |
| 2026-09-19 | Text files created in VS Code, never with PowerShell `>` | PowerShell 5.1 writes UTF-16, which git treats as binary |
| 2026-09-19 | `.gitignore` uses `/data/` (root only) | `data/` also ignored `src/data/` code |
| 2026-09-21 | One extract covering 2011-01 onward, not two | Covers the main (2015) and robustness (2011) starts without a second download |
| 2026-09-21 | Pandemic months downloaded, excluded only at analysis time | Section 13 needs them for the keep-with-controls check |
| 2026-09-21 | Case selection AGE 22-64 at IPUMS | Covers every preregistered group and the quintile-cutoff population; anything outside needs a re-extract |
| 2026-09-21 | OCC, IND and LABFORCE requested beyond the strict minimum | Cheap insurance against a second extract |
| 2026-09-21 | Fixed-width format, rectangular on person | Ships the DDI codebook, so value labels survive |
| 2026-09-21 | Submission sends the committed JSON definition, not a fresh build | The data always matches what is in git |
| 2026-09-21 | Extract metadata and file hashes logged to `docs/extract_log.json` | Makes a re-download verifiable |
| 2026-09-21 | Single zstd Parquet file, written in chunks via a temporary file | Fast column reads; a crash cannot leave a half-written file |
| 2026-09-21 | Sector Rule A: follow NAICS where it disagrees with the 1990 grouping | Section 15 names sectors in NAICS terms; keeps results comparable to published sector series |
| 2026-09-21 | Tech and finance (Section 12, threat 1) = sectors 1 and 2 | One definition used for both purposes |
| 2026-09-30 | Exposure file: `occ_level.csv` from openai/GPTs-are-GPTs (https://raw.githubusercontent.com/openai/GPTs-are-GPTs/main/data/occ_level.csv), downloaded 2026-09-30, SHA-256 `40c74f53de40aec91c0017d80690cbba915f83a8bb414bcf2f884692f1749acb`; 923 rows | The paper's own repository; the hash pins the exact version, and the download fails if it differs |
| 2026-09-30 | Primary exposure column `dv_rating_beta` (GPT-4 rating, E1 + 0.5*E2) | Section 5's "GPT-4 beta"; resolves its `[verify]` |
| 2026-09-30 | Exposure codes are O*NET-SOC 2019 (8-digit); chain OCC2010 -> 2010 Census occupation -> SOC 2018 -> O*NET-SOC 2019; `dv_rating_beta` averaged (unweighted) across 8-digit variants within each 6-digit SOC before merging to OCC2010 | Matches the file's code system; SOC 2018 is the common key |
| 2026-09-30 | Occupation crosswalk: Census "2018 Census Occupation Code List with Crosswalk" (https://www2.census.gov/programs-surveys/demo/guidance/industry-occupation/2018-occupation-code-list-and-crosswalk.xlsx), downloaded 2026-09-30, SHA-256 `fca2818d691c32777a4cd733a9ab77c8c5bd47adcacd7ac3aa149bebd45b5f7f`; sheet "2010 to 2018 Crosswalk " | One official file holding 2010 Census -> 2018 Census -> SOC 2018; chain OCC2010 -> 2010 Census -> 2018 Census -> SOC 2018 -> O*NET-SOC 2019 |
| 2026-09-30 | One-to-many rule: unweighted mean twice (O*NET-SOC variants within SOC; SOC targets within OCC2010); `n_soc_targets` stored per OCC2010 code | Simple and transparent; employment-weighted version listed in `plan.md` as a possible robustness check |
| 2026-09-30 | `openpyxl` 3.1.5 added (with `et_xmlfile` 2.0.0) | `pandas.read_excel` needs it for the Census `.xlsx` |
| 2026-09-30 | SOC structure: BLS "2018 SOC Structure" (https://www.bls.gov/soc/2018/soc_structure_2018.xlsx), saved by hand 2026-09-30, SHA-256 `ade08af40923266f3a854842e888ca3e93c15b26a147c20a2b12a61f4c4f4077`. BLS blocks automated download (403 for every User-Agent tried), so this file is fetched manually; `download_sources` verifies it every run, fails with the manual instruction if it is missing, and never downloads it. No contact User-Agent is sent to bls.gov | Official hierarchy for expanding Census aggregate SOC codes |
| 2026-09-30 | Aggregate SOC expansion: groups -> all detailed codes under them (BLS hierarchy); residual X codes -> prefix within the structure minus codes claimed by other 2018 Census codes; detailed codes as is. Title-parenthetical codes are a test only | Set by Aryan; exclusion is the definition of a residual code |
| 2026-09-30 | Wage and salary (Section 4) = CLASSWKR 22, 23, 25, 27, 28 (`design.wage_salary_classwkr`). Checked first: aggregate codes 20, 21, 24 are never used in 2011-2026 (`inspect_codes` section 6) | Set by Aryan; the check shows the inclusion list drops no one silently |
| 2026-09-30 | 2010 -> 2018 Census codes: rows with both codes on the main crosswalk sheet (unchanged codes) plus "Occ Code Changes" (changed codes), forward-filling the 2010 code on split continuations and the 2018 code on merge continuations; the main sheet's half-filled rows are a test only | Set by Aryan; main-sheet row position is ambiguous between splits and merges (design_notes.md) |
| 2026-09-30 | Residual X codes claim detailed codes longest prefix first | Implementation choice, not Aryan's; it decides the 51-9199 case, which awaits Aryan's ruling |
| 2026-09-30 | 51-9199 assigned to Census 8990 by explicit override (`design.occ_crosswalk.soc_overrides`); 53-7065 kept with 9645 | Set by Aryan: the Census title places 51-9199 under 8990; 53-7065 is 9645's own SOC code. An override, not a new claim order, so no other code moves |
| 2026-09-30 | Coverage report written to `results/tables/exposure_coverage.md`; codes-only map to `docs/occ_soc_map.csv` (both committed); OCC2010 scores to `data/interim/occ2010_exposure.parquet` (not committed) | Aggregates are safe to commit; scores stay out of git and out of print until quintiles are approved |
| 2026-09-30 | `download_exposure.py` renamed `download_sources.py`; one hash-checked download loop for both non-IPUMS files | Same pattern for every external file |
