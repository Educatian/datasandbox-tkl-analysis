"""One entry point: consent/window extract -> analyses -> figure data -> R figures -> number check.
  python -X utf8 repro/run_all.py   needs the raw inputs under data/raw/ (not shared; see README data-access note)
"""
import os, shutil, subprocess, sys, time
from pathlib import Path

# ---------------- config ----------------
ROOT = Path(__file__).resolve().parents[1]           # the analysis folder (consent16)
RAW = {  # raw inputs (participant data, not shared), relative to ROOT
    "TKL_RAW_LOGS": "data/raw/user_logs_participants.csv",
    "TKL_RAW_CODES": "data/raw/manual_chat_codes.csv",
    "TKL_GRADES": "data/raw/provisional_crosswalk_analysis_pseudonymized.csv",
    "TKL_JEV_LOG": "data/raw/jev_second_coder_log.csv",
    "TKL_CODE_ADJ": "data/raw/code_adjudication.csv",
}
SEED = "20261121"                                     # bootstrap seed (esm_outcome.py, jev_agreement_consent16.py)
RSCRIPT = os.environ.get("RSCRIPT") or shutil.which("Rscript") or r"C:\Program Files\R\R-4.5.2\bin\Rscript.exe"
PY_STEPS = ["build_extract.py", "reanalysis.py", "sensitivity.py", "survey.py", "esm_outcome.py",
            "jev_agreement_consent16.py", "figures/prep_figure_data.py",
            "review_r1_analyses.py"]
R_STEPS = ["tkl_figures.R", "tkl_figures_redesign.R", "tkl_figures_new.R", "tkl_figure_framework.R"]  # cwd = figures/
# ----------------------------------------

env = dict(os.environ, TKL_SEED=SEED, PYTHONUTF8="1")
env.update({k: str((ROOT / v).resolve()) for k, v in RAW.items()})

t0 = time.time()
def run(cmd, cwd, label):
    print(f"\n=== {label}  [{time.time() - t0:.0f}s]", flush=True)
    subprocess.run(cmd, cwd=cwd, env=env, check=True)
for s in PY_STEPS: run([sys.executable, "-X", "utf8", str(ROOT / s)], ROOT, s)
for s in R_STEPS: run([RSCRIPT, s], ROOT / "figures", "figures/" + s)
run([sys.executable, "-X", "utf8", str(ROOT / "repro" / "check_numbers.py")], ROOT, "repro/check_numbers.py")
print(f"\nall steps finished in {time.time() - t0:.0f}s")
