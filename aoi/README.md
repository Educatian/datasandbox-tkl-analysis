# Control-level (AOI) interaction patterns — DataSandbox TKL, 2026-11-26

Run in order (consented extract in `data/`; per-event outputs stay in `data/`, aggregates in `results/aoi/`):

1. `control_codebook.py`: maps each logged (page, tag, className) to the element(s) in the Feb-2026 source with that class (`results/aoi/control_codebook.csv`).
2. `label_controls.py`: labels every SMART_CLICK, trying these sources in order:
   - a unique class;
   - the logged button text (`context_label`), matched against the source labels;
   - XY page coordinates matched to rendered AOI boxes (`summation_input_aoi.json`, `module_aoi.json`). These come from the local no-DB build at each logged viewport.

   Result: 93.8% of 3,432 clicks resolved. Output: `data/smart_click_controls.csv` (local) and `results/aoi/control_counts.csv`.
3. `patterns.py`: module-level repetition vs. switching and first-order control transitions, plus the control before and after support. Outputs: `patterns_module.csv`, `patterns_transitions.csv`, `patterns_peri.csv`.

## Notes

- `context_label` can contain a login e-mail. It never leaves `data/`, and the aggregate files are checked for "@".
- AOI boxes were extracted from `figures/interface/ds31_feb18`, run with the local screenshot patch and without Supabase. No DB writes, and the chat was not used.
- 333 of the 4,046 events coded M in `common.py` are "← Back to Portal" clicks (navigation). `patterns.py` excludes them from action sequences. The manuscript coding is unchanged, pending an owner decision.
