# Reproducibility package: "Asking Without Stopping" (TKL)

This repository holds the analysis code for the manuscript; learner data are not included. `repro/` holds the harness. All paths are relative, and the raw inputs are expected under `data/raw/` (see `RAW` at the top of `run_all.py`).

## Run

```
python -m venv repro/.venv
repro/.venv/Scripts/python -m pip install -r repro/requirements.txt      # Windows; bin/python elsewhere
repro/.venv/Scripts/python -X utf8 repro/run_all.py                       # real data, ends with the number check
repro/.venv/Scripts/python -X utf8 repro/check_numbers.py                 # re-run the check alone
repro/.venv/Scripts/python -X utf8 independent_check.py                   # headline numbers, re-implemented
```

R 4.5.2 must be on PATH (or set `RSCRIPT`), with the packages in `sessionInfo.txt` (ggplot2 4.0.2, dplyr, readr, tidyr, patchwork, scales, ggrepel, ggtext, tidygraph, ggraph, ragg, tibble). Runtime (2026-11-21, laptop): about 40 s for the real data, and about 1 min for the pip install. Seed: 20261121 (`SEED` in `run_all.py`; both bootstraps).


## Scripts → manuscript

| Script | Output | Manuscript |
|---|---|---|
| `build_extract.py` | `data/*_consented.csv` | Setting and Participants (consent filter, window) |
| `common.py` | — | event codes (Table 1), reply/tutor-initiated split, LSA, GEE helpers used by all scripts |
| `reanalysis.py` | `results/reanalysis/` | sample counts; Table 1; RQ1 survival and request counts; Table 2; profiles; RQ3 before/after Wilcoxon |
| `sensitivity.py` | `results/lsa_*`, `gee_models.csv`, `fe_logit_models.csv`, `summary.json` | RQ3 adjusted residuals, primary GEE (OR 0.70), earlier-coding checks, FE logit; ESM Figures S1–S2 |
| `survey.py` | `results/survey_*` | Learners' Perceptions; ESM Table S1 |
| `esm_outcome.py` | `results/esm_outcome_*` | ESM Supplementary Note 1 |
| `jev_agreement_consent16.py` | `results/jev_agreement_consent16.json` | Data and Event Coding (91.1%, κ = .88) |
| `figures/prep_figure_data.py` | `figures/data/*.csv` | inputs for every data figure |
| `figures/tkl_figures_new.R` | Figure 1, Figure 6, Figure S3 | Method; RQ3; ESM |
| `figures/interface/make_interface_figure.py` | Figure 2 | Learning Environment (not run by `run_all.py`, see below) |
| `figures/tkl_figure_framework.R` | Figure 3 | Data Analysis (hand-specified diagram; its *n* values are typed, not computed) |
| `figures/tkl_figures.R` | Figure 4, Figure S1 | RQ1; ESM |
| `figures/tkl_figures_redesign.R` | Figure 5, Figure 7, Figure S2 | RQ1; RQ3; ESM |
| `repro/check_numbers.py` | pass/fail | every data-derived number in `results/manuscript_numbers.json` |

Verified outputs from 2026-11-21: `results/run_all_output.txt` and `results/check_numbers_output.txt`.

## Not reproducible from this package

- **Figure 2** is built from screenshots of a local build of the February 2026 app (commit eb29e0e, local test account, with `figures/interface/local_screenshot_patch.diff` applied). It needs that build and a browser; run `python figures/interface/make_interface_figure.py` once the four `*_2x.png` captures are in `figures/interface/`.
- **Second coder.** The Jev codes came from an AI coder run on 2026-11-20 (an API call). The package reuses its log (`jev_second_coder_log.csv`) and does not call the API again.
- **Consent crosswalk.** The gradebook export that holds the consent field is no longer on disk. The account numbers taken from it are in `data/crosswalk.json` (local only). One of the 16 consent records cannot be matched to an account.
- **Gemini replies** were generated live during the course and cannot be regenerated; only their logged events are analyzed.

## Data access

The logs, chat text, survey answers and grades come from 15 graduate students who consented to research use under an IRB protocol at the instructor's university. They cannot be shared publicly; requests go to the corresponding author and depend on the protocol's data-sharing terms. `data_schema.md` documents every input.
