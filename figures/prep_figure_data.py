"""Aggregate inputs for the R figure scripts (FIGDATA/*.csv). Merges the former prep_figure_data.py,
prep_redesign_data.py and prep_new_figures.py. No learner/session IDs, chat text or clock times are written; the
finest time unit is the Mountain-time course week. Runs after reanalysis.py and sensitivity.py (reads their outputs).
Run: python -X utf8 figures/prep_figure_data.py
"""
import sys
from pathlib import Path
import pandas as pd
from lifelines import KaplanMeierFitter
from statsmodels.stats.proportion import proportion_confint
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import FIGDATA, GROUP, RESULTS, load_logs, sequences

FIGDATA.mkdir(parents=True, exist_ok=True)
d = load_logs(); seqs = sequences(d)

# ---------- Figure 4: Kaplan-Meier time to first request ----------
# Unit: session (survival_frame.csv from reanalysis.py: 57 sessions, 15 events). Writes the KM step curve with
# log-log 95% band (lifelines default), censoring ticks, and the at-risk row (0, 5, 10, 30, 60, 120 min).
S = pd.read_csv(RESULTS / "reanalysis/survival_frame.csv")
km = KaplanMeierFitter().fit(S["T"], S.event)
sf = km.survival_function_.join(km.confidence_interval_).reset_index(); sf.columns = ["minutes", "survival", "lo", "hi"]
sf.to_csv(FIGDATA / "fig1_km_curve.csv", index=False)
pd.DataFrame({"minutes": S.loc[S.event.eq(0), "T"].round(2).sort_values().values}).to_csv(FIGDATA / "fig1_censor_times.csv", index=False)
risk = pd.DataFrame({"minutes": [0, 5, 10, 30, 60, 120]})
risk["at_risk"] = [int((S["T"] >= m).sum()) for m in risk.minutes]
risk["cum_events"] = [int(((S["T"] <= m) & S.event.eq(1)).sum()) for m in risk.minutes]
risk.to_csv(FIGDATA / "fig1_risk_table.csv", index=False)

# ---------- ESM Figure S1: P(next = M) after R vs T, both schemes, Wilson 95% CI ----------
# Unit: lag-1 transition from a tutor message with a following event in the same session (37 replies, 361 tutor-
# initiated). Base = share of all transitions whose next event is M (62.0% corrected, 81.3% earlier).
rows = []
for scheme, f in [("Earlier coding", "lsa_locked_split_counts.csv"), ("Corrected coding", "lsa_corrected_split_counts.csv")]:
    c = pd.read_csv(RESULTS / f, index_col=0); base = c["M"].sum() / c.values.sum()
    for code, lab in [("R", "Reply to a learner request"), ("T", "Tutor-initiated message")]:
        n, k = int(c.loc[code].sum()), int(c.loc[code, "M"]); lo, hi = proportion_confint(k, n, method="wilson")
        rows.append({"scheme": scheme, "source": lab, "k": k, "n": n, "p": k / n, "lo": lo, "hi": hi, "base": base})
pd.DataFrame(rows).to_csv(FIGDATA / "fig3_transitions.csv", index=False)

# ---------- ESM Figure S2: specification curve (6 GEE + 2 FE logit from sensitivity.py) ----------
g = pd.read_csv(RESULTS / "gee_models.csv"); fe = pd.read_csv(RESULTS / "fe_logit_models.csv")
lab = {"A1": "Earlier coding, all events, no fixed effects", "A2": "Earlier coding, all events, page fixed effects",
       "B1": "Earlier coding, chat excluded, no fixed effects", "B2": "Earlier coding, chat excluded, page fixed effects",
       "C1": "Corrected coding, chat and system excluded, no fixed effects", "C2": "Corrected coding, module pages, page fixed effects (primary)"}
f4 = [{"spec": lab[r.model[:2]], "events": r.n_events, "OR": r.OR, "lo": r.lo_bias_reduced, "hi": r.hi_bias_reduced,
       "estimator": "GEE, bias-reduced SE", "converged": True} for r in g.itertuples()]
f4 += [{"spec": ("Fixed-effects logit, earlier coding" if "locked" in r.model else "Fixed-effects logit, corrected coding") + ", learner and page dummies",
        "events": r.n_events, "OR": r.OR, "lo": r.lo_cluster, "hi": r.hi_cluster, "estimator": "Fixed-effects logit, cluster SE",
        "converged": bool(r.converged)} for r in fe.itertuples()]
pd.DataFrame(f4).to_csv(FIGDATA / "fig4_forest.csv", index=False)

# ---------- Figure 5: module x course week (sessions visiting, requests) ----------
# Unit: session-module-week (exposure = distinct sessions with any event on the module page that week) and learner
# request. Week = Mountain-time Monday. Modules ordered by first use. Feeds "Galton board ... 12 requests across the
# 10 sessions that visited it", "six modules drew no requests despite being visited in 10 to 14 sessions each".
mod = d[d.page.ne("portal")]; req = d[d.c.eq("U")]
first = mod.groupby("page").timestamp.min().sort_values(); order = {p: i for i, p in enumerate(first.index)}
mw = pd.concat([mod.groupby(["page", "week"]).session_id.nunique().rename("sessions"),
                req.groupby(["page", "week"]).size().rename("requests")], axis=1).fillna(0).reset_index()
mw["order"] = mw.page.map(order); mw.to_csv(FIGDATA / "fig2_module_week.csv", index=False)
tot = mod.groupby("page").session_id.nunique().rename("sessions").to_frame().join(req.groupby("page").size().rename("requests")).fillna(0)
tot["order"] = tot.index.map(order); tot["per10"] = 10 * tot.requests / tot.sessions
tot.reset_index().to_csv(FIGDATA / "fig2_module_totals.csv", index=False)

# ---------- Figure 7: next-event composition + return curve (corrected coding) ----------
# Unit: event with a following event in the same session. (A) share of next-event categories after R, T, any event.
# (B) share of source events followed by >= 1 M within k = 1..5 events, window truncated at session end.
# Feeds 78.4% / 77.8% / 62.0% and 91.9% / 96.1% within five events.
rows, curve = [], []
for lab, f in [("Reply to a learner request", lambda c: c == "R"), ("Tutor-initiated message", lambda c: c == "T"),
               ("All events (base rate)", lambda c: True)]:
    src = [(s, i) for s in seqs for i, c in enumerate(s[:-1]) if f(c)]
    nx = pd.Series([GROUP[s[i + 1]] for s, i in src])
    rows += [{"source": lab, "next": k, "n": int(v), "share": v / len(nx), "N": len(nx)} for k, v in nx.value_counts().items()]
    curve += [{"source": lab, "k": k, "share": sum("M" in s[i + 1:i + 1 + k] for s, i in src) / len(src), "N": len(src)} for k in range(1, 6)]
pd.DataFrame(rows).to_csv(FIGDATA / "fig3_next_composition.csv", index=False)
pd.DataFrame(curve).to_csv(FIGDATA / "fig3_return_curve.csv", index=False)

# ---------- Figure 6: peri-event profile, lags -10..+10 around U and T anchors ----------
# Unit: event at a given lag from an anchor in the same session; truncated at session bounds (no padding), so n per
# lag shrinks with distance. Base = share of all events coded M (61.3%). Feeds 98% (44/45), 89%, 69%, 82%, 49%.
rows = []
for anchor, lab in [("U", "Aligned on learner requests"), ("T", "Aligned on tutor-initiated messages")]:
    for lag in range(-10, 11):
        nx = pd.Series([GROUP[s[i + lag]] for s in seqs for i, c in enumerate(s) if c == anchor and 0 <= i + lag < len(s)])
        rows += [{"panel": lab, "lag": lag, "cat": k, "count": int(v), "n": len(nx), "share": v / len(nx)} for k, v in nx.value_counts().items()]
pd.DataFrame(rows).to_csv(FIGDATA / "figA_peri_event.csv", index=False)
d.c.map(GROUP).value_counts(normalize=True).rename("share").rename_axis("cat").reset_index().to_csv(FIGDATA / "figA_base.csv", index=False)

# ---------- Figure 1: learner x course week overview ----------
# Unit: learner-week. Learners anonymized P01..P15 by descending total events (ties: extract order); weeks only.
# Feeds "from 55 to 835 events and from 2 to 11 sessions per learner".
pid = {u: f"P{i + 1:02d}" for i, u in enumerate(d.groupby("user_id").size().sort_values(ascending=False).index)}
d["pid"] = d.user_id.map(pid); d["wk"] = d.week.dt.date
agg = dict(events=("c", "size"), sessions=("session_id", "nunique"), requests=("c", lambda x: int(x.eq("U").sum())))
d.groupby(["pid", "wk"]).agg(**agg).reset_index().rename(columns={"wk": "week"}).to_csv(FIGDATA / "figB_learner_week.csv", index=False)
d.groupby("pid").agg(**agg).reset_index().to_csv(FIGDATA / "figB_learner_totals.csv", index=False)

# ---------- ESM Figure S3: lag-1 transition probabilities, sessions with vs without a request ----------
# Unit: lag-1 transition within session; navigation N = G + P. Feeds 2,057 / 4,597 transitions, max in-degree 2,931.
rows = []
for lab, keep in [("Sessions with a request", 1), ("Sessions without a request", 0)]:
    nav = [["N" if x in ("G", "P") else x for x in s] for s in sequences(d[d.sess_req.eq(keep)])]
    t = pd.Series([ab for s in nav for ab in zip(s[:-1], s[1:])]).value_counts()
    fn = t.groupby([a for a, _ in t.index]).sum()
    rows += [{"panel": lab, "from": a, "to": b, "count": int(v), "from_n": int(fn[a]), "prob": v / fn[a]} for (a, b), v in t.items()]
pd.DataFrame(rows).to_csv(FIGDATA / "figC_transitions.csv", index=False)
print("figure data written:", sorted(p.name for p in FIGDATA.glob("*.csv")))
