"""End-of-session survey (consenters only): three 5-point items by session (wave); learner-level link to logged activity.
Descriptive only (n = 13 respondents). Comments are written to data/ (LOCAL) and never to results/.
Run: python -X utf8 survey.py
"""
import numpy as np, pandas as pd
from scipy import stats
from common import DATA, NON_OUTCOME, RESULTS, dump, load_logs, suffix

s = pd.read_csv(DATA / "survey_consented.csv"); s["ts"] = pd.to_datetime(s.Timestamp)
items = {"control": s.columns[3], "depth": s.columns[4], "ease": s.columns[5]}; comment = s.columns[6]

# ---------- Wave assignment ----------
# Unit: survey response. Wave = class session whose date is nearest the form timestamp (the typed Date field has
# typos). All consented timestamps fall on the three class days, so nearest = same day. Feeds ESM Table S1.
waves = pd.to_datetime(["2026-01-14", "2026-01-26", "2026-02-02"])
s["wave"] = [int(np.argmin(np.abs((waves - t.normalize()).days))) + 1 for t in s.ts]
print(s.groupby("wave").ts.agg(day=lambda x: ", ".join(sorted(set(x.dt.date.astype(str)))), n="size"))   # dates only, no clock times
rows = []
for w, g in list(s.groupby("wave")) + [("all", s)]:
    for k, c in items.items():
        rows.append({"wave": w, "item": k, "n": int(g[c].notna().sum()), "learners": int(g._s.nunique()), "M": round(g[c].mean(), 2),
                     "SD": round(g[c].std(), 2), "Mdn": g[c].median(), "pct_agree": round((g[c] >= 4).mean() * 100, 1)})
W = pd.DataFrame(rows); W.to_csv(RESULTS / "survey_by_wave.csv", index=False); print(W.to_string(index=False))

# ---------- Learner-level link ----------
# Unit: respondent (mean rating across waves) inner-joined to logged activity (consented extract, 13 of 15 learners).
# Spearman rho with requests, events and manipulation share (M / non-chat, non-system events). Feeds "unrelated to the
# number of requests (rho = .06 to .10) but rose with total logged activity (rho = .56 to .67; n = 13)".
d = load_logs(); d["s"] = d.user_id.map(suffix)
nc = d[~d.c.isin(NON_OUTCOME)]
P = pd.DataFrame({"requests": d.groupby("s").c.apply(lambda x: int(x.eq("U").sum())), "events": d.groupby("s").size(),
                  "m_share": nc.assign(m=nc.c.eq("M")).groupby("s").m.mean()})
P["any_request"] = (P.requests > 0).astype(int)
L = s.groupby("_s")[list(items.values())].mean(); L.columns = list(items); L = L.join(P, how="inner")
link = [{"item": k, "x": x, "n": len(L), "rho": round(stats.spearmanr(L[k], L[x]).statistic, 2)} for k in items for x in ("requests", "m_share", "events")]
grp = {k: {"requesters": [int(L.any_request.sum()), round(L.loc[L.any_request == 1, k].mean(), 2)],
           "non_requesters": [int((L.any_request == 0).sum()), round(L.loc[L.any_request == 0, k].mean(), 2)]} for k in items}
res = {"respondents": int(s._s.nunique()), "responses": len(s), "consenters_with_telemetry": int(d.user_id.nunique()), "link": link,
       "by_request_status": grp, "responses_per_learner": s.groupby("_s").size().value_counts().to_dict(),
       "max_responses_in_one_wave": int(s.groupby(["_s", "wave"]).size().max()),
       "n_comments": int(s[comment].notna().sum())}
dump(res, RESULTS / "survey_summary.json"); print(res)
s[["wave", "_s", comment]].dropna().to_csv(DATA / "survey_comments_LOCAL.csv", index=False)
