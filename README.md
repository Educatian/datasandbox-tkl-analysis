# DataSandbox GenAI help-seeking analysis

Analysis code for the manuscript *Pausing to Ask: Help-Seeking Dialogues With an Optional Generative AI Tutor in Manipulative Statistics Simulations*. The code turns DataSandbox interaction logs, coded tutor requests, an end-of-session survey and course grades into every number, table and figure reported in the manuscript and its supplementary material. The analyses include time-to-first-request survival, lag-sequential analysis, module-adjusted GEE models, and the specification curve.

## Data

The learner data are **not** included and are not publicly available, because of participant consent and ethics restrictions. To run the code on your own data, provide files in the formats described in [`repro/data_schema.md`](repro/data_schema.md) under `data/raw/`.

## Run

```
python -m venv .venv
.venv/Scripts/python -m pip install -r repro/requirements.txt     # bin/python on macOS/Linux
.venv/Scripts/python -X utf8 repro/run_all.py
```

Requirements:
- Python 3.11 with the pinned packages in `repro/requirements.txt`.
- R 4.5.2 with the packages in `repro/sessionInfo.txt`. Rscript must be on PATH, or set `RSCRIPT`.

`run_all.py` builds the analysis extract and runs all analyses, writes the figure data, renders the figures in R, and finally runs `repro/check_numbers.py`. That check compares the results with the numbers reported in the manuscript (`repro/results/manuscript_numbers.json`). It passes only on the original data.

## Code → manuscript

| Code | Manuscript |
|---|---|
| `common.py` | Event codes (Table 1; clicks inside the chat panel are merged into the request they belong to), reply matching (first tutor message after an unanswered request), lag-sequential and GEE helpers |
| `review_r1_analyses.py` | RQ3 help dialogues, continuation baseline with learner-resampled intervals, welcome vs. state-triggered messages; RQ1 timing from module entry |
| `build_extract.py` | Consent and time-window filter (Setting and Participants) |
| `reanalysis.py` | Sample counts, Table 1, RQ1 survival and request counts, Table 2, profiles, RQ3 before/after test |
| `sensitivity.py` | RQ3 adjusted residuals, primary GEE, earlier-coding checks, fixed-effects logit (ESM Figures S1–S2) |
| `survey.py` | Learners' Perceptions; ESM Table S1 |
| `esm_outcome.py` | ESM Supplementary Note 1 |
| `jev_agreement_consent16.py` | Second-coder agreement and the first author's verification of the content codes (Data and Event Coding) |
| `figures/` | Figures 1 and 3–7 and ESM Figures S1–S3 (R); Figure 2 is built from interface screenshots (`figures/interface/`) |
| `independent_check.py` | Independent re-implementation of the headline numbers |

Details: [`repro/README.md`](repro/README.md). Method-versus-code checks: [`crosscheck.md`](crosscheck.md).

## License

MIT (see `LICENSE`).
