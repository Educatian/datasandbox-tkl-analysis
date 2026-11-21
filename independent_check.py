"""Independent recomputation of the headline numbers from data/user_logs_consented.csv. Imports none of the analysis
scripts or common.py: coding, the reply split, transitions and the Kaplan-Meier estimator are re-implemented from the
Method text; only the GEE uses statsmodels directly. Prints aggregates only; exits non-zero on any mismatch.
Run: python -X utf8 independent_check.py
"""
import math, os, sys, warnings
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
warnings.filterwarnings("ignore")
DATA = Path(os.environ.get("TKL_DATA", Path(__file__).resolve().parent / "data"))
ok = True
def check(name, got, want, tol=0):
    global ok
    good = abs(got - want) <= tol
    ok &= good; print(f"{'ok  ' if good else 'FAIL'} {name}: {got} (manuscript {want})")

e = pd.read_csv(DATA / "user_logs_consented.csv")
e["t"] = pd.to_datetime(e.timestamp, utc=True, format="ISO8601")
e = e.sort_values(["session_id", "t"], kind="mergesort").reset_index(drop=True)

# Table 1, from the definitions in the text
def base_code(r):
    if r.click_type == "CHAT": return "U" if r.target_tag == "USER" else "B"
    if r.click_type == "CUSTOM_EVENT" and r.target_tag == "auth": return "S"   # login / logout
    if r.click_type == "GLOBAL_CLICK": return "G"
    return "P" if r.page == "portal" else "M"
code = [base_code(r) for r in e.itertuples()]
# reply = tutor message right after a learner request, or continuing that reply (same session)
final = []
for i, c in enumerate(code):
    same = i > 0 and e.session_id[i] == e.session_id[i - 1]
    final.append(("R" if same and final[-1] in "UR" else "T") if c == "B" else c)
e["c"] = final
cnt = e.c.value_counts()
for k, v in dict(M=4125, G=798, P=520, S=834, U=45, R=40, T=364).items(): check(f"Table 1 {k}", int(cnt.get(k, 0)), v)
check("events", len(e), 6726); check("sessions", e.session_id.nunique(), 72); check("learners", e.user_id.nunique(), 15)

# Next-event shares (lag 1, within session)
nxt = e.groupby("session_id").c.shift(-1)
for src, k, n in (("R", 29, 37), ("T", 281, 361)):
    sel = nxt[e.c == src].dropna()
    check(f"after {src}: n with a next event", len(sel), n); check(f"after {src}: next = M", int((sel == "M").sum()), k)
check("base: share of next events that are M (%)", round(100 * float((nxt.dropna() == "M").mean()), 1), 62.0)
check("lag-1 transitions", int(nxt.notna().sum()), 6654)

# Kaplan-Meier, hand-rolled: time from session start to first request, censored at last event, 0.1-120 min
rows = []
for _, g in e.groupby("session_id"):
    t0 = g.t.iloc[0]; u = g.t[g.c == "U"]
    T, ev = ((u.iloc[0] if len(u) else g.t.iloc[-1]) - t0).total_seconds() / 60, int(len(u) > 0)
    if 0.1 <= T <= 120: rows.append((T, ev))
T = np.array([r[0] for r in rows]); E = np.array([r[1] for r in rows])
def surv(x):
    s = 1.0
    for t in np.unique(T[(E == 1) & (T <= x)]): s *= 1 - ((T == t) & (E == 1)).sum() / (T >= t).sum()
    return s
check("KM sessions", len(T), 57); check("KM events", int(E.sum()), 15)
check("conditional median (min)", round(float(np.median(T[E == 1])), 2), 3.18)
check("S(5)", round(surv(5), 3), 0.767); check("S(10)", round(surv(10), 3), 0.637)

# Primary GEE: module pages, M vs G, page FE, exchangeable, clusters = learner, bias-reduced SE
e["req"] = e.groupby("session_id").c.transform(lambda s: int((s == "U").any()))
m = e[e.c.isin(["M", "G"]) & (e.page != "portal")].assign(y=lambda x: (x.c == "M").astype(int))
m = m[m.groupby("page").y.transform("nunique") > 1]
fit = smf.gee("y ~ req + C(page)", groups="user_id", data=m, family=sm.families.Binomial(),
              cov_struct=sm.cov_struct.Exchangeable()).fit(cov_type="bias_reduced")
b, se = fit.params["req"], fit.bse["req"]
check("GEE events", len(m), 4597)
for name, v, want in (("OR", b, 0.70), ("CI lo", b - 1.96 * se, 0.45), ("CI hi", b + 1.96 * se, 1.09)):
    check(f"GEE {name}", round(math.exp(v), 2), want)
print("ALL MATCH" if ok else "MISMATCH"); sys.exit(0 if ok else 1)
