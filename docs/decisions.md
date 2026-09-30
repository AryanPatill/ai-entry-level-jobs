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
