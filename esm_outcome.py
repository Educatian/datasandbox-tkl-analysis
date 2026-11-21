"""ESM Supplementary Note 1: exploratory grade linkage on the consented, course-window extract. Aggregates only.
Run: python -X utf8 esm_outcome.py
"""
import numpy as np, pandas as pd
from scipy import stats
from common import GRADES, RESULTS, SEED, TZ, crosswalk, dump, load_logs, suffix

# ---------- Linkage ----------
# Unit: learner. Grades come from the pseudonymized 2026-09-15 crosswalk: participant Pk = k-th account number among
# the 23 logged accounts (list in data/crosswalk.json). Inner merge with the consented extract keeps consenters only
# (15; asserted). Activity indicators on all in-window events: request rate = learner requests / events (tutor messages
# not counted); keyword-based advanced-action and manipulation rates as in 2026-09-15; active days in Mountain time.
G = pd.read_csv(GRADES); acct = crosswalk()["log_account_suffixes"]
G["s"] = G.participant.map(lambda p: acct[int(p[1:]) - 1])
d = load_logs(); d["s"] = d.user_id.map(suffix)
tg = d.target_id.astype(str).str.lower() + " " + d.target_tag.astype(str).str.lower()
d["adv"] = tg.str.contains(r"outlier|comparison|p-value|analytic|achieved_useful")
d["man"] = tg.str.contains(r"slider|change|add_block|remove_block|create_outlier|comparison|p-value|reset")
d["req"] = d.c.eq("U"); d["day"] = d.timestamp.dt.tz_convert(TZ).dt.date
F = d.groupby("s").agg(events=("s", "size"), sessions=("session_id", "nunique"), active_days=("day", "nunique"),
                       advanced_action_rate=("adv", "mean"), manipulation_rate=("man", "mean"), request_rate=("req", "mean")).reset_index()
outs = ["Current Score", "Final Score", "Exams Final Score", "Assignments Final Score"]; feats = list(F.columns[1:])
C = G[["s"] + outs].merge(F, on="s")
assert len(C) == d.user_id.nunique(), "grade linkage must cover exactly the consented learners"

# ---------- 24 uncorrected Spearman correlations + bootstrap CI for request rate x assignments ----------
# Percentile bootstrap, 5,000 learner resamples, rng = default_rng(SEED). Feeds rho = .20 [-.35, .66], ".18 to .37",
# largest rho = .62 (keyword manipulation rate x final score).
R = pd.DataFrame([{"outcome": o, "feature": f, "n": len(C), "rho": round(stats.spearmanr(C[o], C[f]).statistic, 3)} for o in outs for f in feats])
R.to_csv(RESULTS / "esm_outcome_spearman.csv", index=False)
x, y = C["Assignments Final Score"].to_numpy(float), C.request_rate.to_numpy(float)
rng = np.random.default_rng(SEED); boot = [stats.spearmanr(x[i], y[i]).statistic for i in (rng.integers(0, len(x), len(x)) for _ in range(5000))]
rr = R[R.feature.eq("request_rate")].rho
key = {"n": len(C), "rho": round(float(stats.spearmanr(x, y).statistic), 3), "ci": [round(float(np.nanquantile(boot, q)), 3) for q in (.025, .975)],
       "n_tests": len(R), "request_rate_range": [float(rr.min()), float(rr.max())], "max_abs": R.loc[R.rho.abs().idxmax()].to_dict()}
dump(key, RESULTS / "esm_outcome_key.json"); print(key)
