"""Step 3 of the AOI work: control-level interaction patterns (descriptive).
Units: module visit = consecutive events of one session on one module page. Action = one manipulation (event code M)
labelled with its control (data/smart_click_controls.csv); custom module events get the control they come from, and a
click plus the custom event(s) it fires within 2 s on the same control count as one action.
Outputs (aggregate only, results/aoi/):
  patterns_module.csv     per module: actions, visits, distinct controls used, repeat share (same control again), top transition
  patterns_transitions.csv per module: control -> control transition counts and row shares (first order, within visits)
  patterns_peri.csv       around requests (U) and tutor-initiated messages (T): control of the last action before and the
                          first action after (after a request: after the dialogue ends); share returning to the same control,
                          against the base rate of same-control continuation between consecutive actions in that module
Run: python -X utf8 aoi/patterns.py"""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import load_logs

ROOT = Path(__file__).resolve().parents[1]; OUT = ROOT / "results/aoi"
CUSTOM = {("dart-board", "sd_change"): "SD (Spread)", ("dart-board", "comparison_mode"): "Compare Players",
          ("mode-viz", "add_block"): "+", ("mode-viz", "remove_block"): "-", ("bin-squeezer", "slider_change"): "slider",
          ("balance-beam", "create_outlier"): "Create Outlier!", ("balance-beam", "reset"): "Reset Weights"}
SYSTEM = {"achieved_useful_mode"}  # feedback fired by the module, not a learner action

d = load_logs().sort_values(["session_id", "timestamp"]).reset_index(drop=True)
ctl = pd.read_csv(ROOT / "data/smart_click_controls.csv")[["id", "control"]]
d = d.merge(ctl, on="id", how="left")
cm = (d.c == "M") & (d.click_type == "CUSTOM_EVENT")
d.loc[cm, "control"] = [CUSTOM.get((p, t)) for p, t in zip(d.page[cm], d.target_id[cm])]
M_TOTAL = int((d.c == "M").sum())  # all events coded M (Table 1), before dropping module feedback events
d = d[~((d.c == "M") & d.target_id.isin(SYSTEM))]
GENERIC = {"input control", "button control", "setInput"}
d.loc[d.control.isin(GENERIC), "control"] = None
# slider-drag custom events take the control of the labelled click that started the drag (same visit, <= 5 s)
NAV = {"← Back to Portal", "Module card", "Log out"}  # navigation, not manipulation: excluded from action sequences
d["visit"] = (d.session_id.ne(d.session_id.shift()) | d.page.ne(d.page.shift())).cumsum()
d["t"] = pd.to_datetime(d.timestamp, utc=True, format="ISO8601")
clk = d[(d.c == "M") & (d.click_type == "SMART_CLICK") & d.control.notna()][["visit", "t", "control"]]
last = clk.rename(columns={"t": "t_clk", "control": "clk_control"})
cm2 = d[(d.c == "M") & (d.click_type == "CUSTOM_EVENT") & d.target_id.isin(["sd_change", "slider_change"])]
for i, r in cm2.iterrows():
    prev = last[(last.visit == r.visit) & (last.t_clk <= r.t) & ((r.t - last.t_clk).dt.total_seconds() <= 5)]
    if len(prev): d.at[i, "control"] = prev.clk_control.iloc[-1]

# collapse a click and its follow-on custom events (same visit, same control, <= 2 s) into one action
a = d[d.c == "M"].copy()
a["t"] = pd.to_datetime(a.timestamp, utc=True, format="ISO8601")
dup = a.visit.eq(a.visit.shift()) & a.control.eq(a.control.shift()) & a.control.notna() & \
      (a.t - a.t.shift()).dt.total_seconds().le(2) & a.click_type.eq("CUSTOM_EVENT")
a = a[~dup]
d = d[~d.id.isin(a.index.map(lambda i: None))]  # keep d intact; actions are taken from `a`
a = a[a.page.ne("portal") & ~a.control.isin(NAV)]
a["control"] = a.control.fillna("(unlabelled)")

# ---- per module: repetition vs switching, transitions ----
a["prev"] = a.groupby("visit").control.shift()
pairs = a.dropna(subset=["prev"])
pairs = pairs[(pairs.control != "(unlabelled)") & (pairs.prev != "(unlabelled)")]
tr = pairs.groupby(["page", "prev", "control"]).size().rename("n").reset_index()
tr["row_share"] = (tr.n / tr.groupby(["page", "prev"]).n.transform("sum")).round(3)
tr.sort_values(["page", "n"], ascending=[True, False]).to_csv(OUT / "patterns_transitions.csv", index=False)
switch = tr[tr.prev != tr.control].sort_values("n", ascending=False).groupby("page").head(1).set_index("page")
mod = a.groupby("page").agg(actions=("id", "size"), visits=("visit", "nunique"), learners=("user_id", "nunique"),
                            controls_used=("control", lambda s: s[s != "(unlabelled)"].nunique()),
                            labelled=("control", lambda s: (s != "(unlabelled)").mean()))
rep = pairs.assign(same=pairs.control.eq(pairs.prev)).groupby("page").same.agg(["mean", "size"])
mod["repeat_share"] = rep["mean"]; mod["pairs"] = rep["size"]
mod["top_switch"] = switch.apply(lambda r: f"{r.prev} -> {r.control} ({r.n})", axis=1)
mod.round(3).sort_values("actions", ascending=False).to_csv(OUT / "patterns_module.csv")

# ---- around requests and tutor-initiated messages ----
ev = d.copy()
ev["is_action"] = ev.id.isin(set(a.id))
ev["control"] = ev.control.where(ev.is_action)
rows = []
for v, g in ev[ev.page.ne("portal")].groupby("visit"):
    g = g.reset_index(drop=True)
    i = 0
    while i < len(g):
        code = g.c[i]
        if code in ("U", "T"):
            j = i
            if code == "U":  # whole help dialogue: consecutive U/R (and interleaved chat) until a non-chat event
                while j + 1 < len(g) and g.c[j + 1] in ("U", "R"): j += 1
            before = g.loc[:i - 1]; before = before[before.is_action]
            after = g.loc[j + 1:]; after = after[after.is_action]
            rows.append({"source": "request (dialogue)" if code == "U" else "tutor-initiated", "page": g.page[i], "user": g.user_id[i],
                         "before": before.control.iloc[-1] if len(before) else None,
                         "after": after.control.iloc[0] if len(after) else None})
            i = j + 1
        else:
            i += 1
pe = pd.DataFrame(rows)
both = pe.dropna(subset=["before", "after"])
both = both[(both.before != "(unlabelled)") & (both.after != "(unlabelled)")]
both = both.assign(same=both.before.eq(both.after))
base = rep["mean"]
both["base_same"] = both.page.map(base)
summ = both.groupby("source").agg(n=("same", "size"), same_control=("same", "mean"), base_same_in_module=("base_same", "mean"))
summ["with_action_before"] = pe.groupby("source").before.apply(lambda s: s.notna().mean())
summ["with_action_after"] = pe.groupby("source").after.apply(lambda s: s.notna().mean())
summ["episodes"] = pe.groupby("source").size()
# learner-resampled 95% interval for (same-control share after support) - (module base rate), 5,000 draws
import numpy as np
rng = np.random.default_rng(20261121)
pr = pairs.assign(same=pairs.control.eq(pairs.prev))
for src in summ.index:
    b = both[both.source == src]; us = b.user.unique(); diffs = []
    for _ in range(5000):
        pick = rng.choice(us, len(us), replace=True)
        bb = pd.concat([b[b.user == u] for u in pick]); base_b = pd.concat([pr[pr.user_id == u] for u in pick]).groupby("page").same.mean()
        diffs.append(bb.same.mean() - bb.page.map(base_b).mean())
    summ.loc[src, "diff"] = b.same.mean() - b.base_same.mean()
    summ.loc[src, "diff_lo"], summ.loc[src, "diff_hi"] = np.nanpercentile(diffs, [2.5, 97.5])
    summ.loc[src, "learners"] = len(us)
summ.round(3).to_csv(OUT / "patterns_peri.csv")
import json
mm = d[d.c == "M"]
json.dump({"M_events": M_TOTAL, "nav_in_M": int(mm.control.isin(NAV).sum())}, open(OUT / "nav_in_M.json", "w"))
pm = both.groupby(["source", "page"]).agg(n=("same", "size"), learners=("user", "nunique"), same_after=("same", "mean"), base_same=("base_same", "first")).reset_index()
pm.round(3).to_csv(OUT / "peri_by_module.csv", index=False)
print(mod.round(2)[["actions", "visits", "controls_used", "labelled", "repeat_share", "top_switch"]].sort_values("actions", ascending=False).to_string())
print("\n", summ.round(3).to_string())
sw = both[~both.same].groupby(["source", "page", "before", "after"]).size().sort_values(ascending=False).head(8)
print("\nmost common switches around support:\n", sw.to_string())
