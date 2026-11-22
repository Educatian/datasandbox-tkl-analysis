"""Mock-review round 1: light analyses on the existing consented extract (no new data). Aggregates only.
RQ3 baseline (does manipulation after tutor support exceed simple continuation of manipulation?), learner-cluster
bootstrap CIs, leave-one-learner-out, welcome vs state-triggered tutor messages, lags +3..+10 after requests,
time from module entry to first request, and inter-event times. Writes results/review_r1.json.
Run: python -X utf8 review_r1_analyses.py"""
import numpy as np, pandas as pd
from common import RESULTS, SEED, dump, load_logs

d = load_logs()
d["nxt"] = d.groupby("session_id").c.shift(-1)
d["nxt_t"] = d.groupby("session_id").timestamp.shift(-1)
d["nxt_page"] = d.groupby("session_id").page.shift(-1)
# Unit: page visit = run of consecutive events on the same page within a session.
d["visit"] = (d.page != d.groupby("session_id").page.shift()).cumsum()
# Welcome vs state-triggered tutor-initiated message: welcome = T before any manipulation in the current page visit.
d["m_before_in_visit"] = d.groupby("visit").c.transform(lambda s: s.eq("M").cumsum().shift(fill_value=0))
d["src"] = np.where(d.c.eq("R"), "reply", np.where(d.c.eq("T"), np.where(d.m_before_in_visit.eq(0), "T_welcome", "T_state"),
                    np.where(d.c.eq("M"), "M", "other")))
has_next = d.nxt.notna()
A = d[has_next & d.src.isin(["reply", "T_welcome", "T_state", "M"])].copy()
A["T_any"] = A.src.str.startswith("T")
A["nextM"] = A.nxt.eq("M").astype(int)

def share(df): return float(df.nextM.mean()) if len(df) else float("nan")
groups = {"reply": A[A.src.eq("reply")], "tutor_initiated": A[A.T_any], "T_welcome": A[A.src.eq("T_welcome")],
          "T_state": A[A.src.eq("T_state")], "M_to_M": A[A.src.eq("M")]}
R = {"n": {k: int(len(v)) for k, v in groups.items()}, "next_is_M": {k: round(share(v), 3) for k, v in groups.items()}}

# Learner-cluster bootstrap (resample learners with replacement), 5,000 draws, seed SEED.
users = A.user_id.unique(); rng = np.random.default_rng(SEED); by_user = {u: g for u, g in A.groupby("user_id")}
draws = {k: [] for k in ["reply", "tutor_initiated", "M_to_M", "reply_minus_T", "reply_minus_MM", "T_minus_MM"]}
for _ in range(5000):
    s = pd.concat([by_user[u] for u in rng.choice(users, len(users))])
    r, t, m = share(s[s.src.eq("reply")]), share(s[s.T_any]), share(s[s.src.eq("M")])
    for k, v in (("reply", r), ("tutor_initiated", t), ("M_to_M", m), ("reply_minus_T", r - t), ("reply_minus_MM", r - m), ("T_minus_MM", t - m)):
        draws[k].append(v)
R["cluster_boot_95ci"] = {k: [round(float(np.nanpercentile(v, 2.5)), 3), round(float(np.nanpercentile(v, 97.5)), 3)] for k, v in draws.items()}

# Leave-one-learner-out and without the three heaviest requesters (reply share).
req_by_user = d[d.c.eq("U")].user_id.value_counts()
loo = [share(A[A.src.eq("reply") & A.user_id.ne(u)]) for u in req_by_user.index]
top3 = req_by_user.index[:3]
R["reply_loo_range"] = [round(min(loo), 3), round(max(loo), 3)]
R["without_top3"] = {"n_reply": int((A.src.eq("reply") & ~A.user_id.isin(top3)).sum()),
                     "reply": round(share(A[A.src.eq("reply") & ~A.user_id.isin(top3)]), 3),
                     "tutor_initiated": round(share(A[A.T_any & ~A.user_id.isin(top3)]), 3),
                     "M_to_M": round(share(A[A.src.eq("M") & ~A.user_id.isin(top3)]), 3),
                     "top3_requests": int(req_by_user.iloc[:3].sum())}

# Within five events (return curve) for manipulation anchors, same rule as Figure 7B.
seqs = {sid: g.c.tolist() for sid, g in d.groupby("session_id", sort=False)}
def within_k(code, k=5):
    hit = n = 0
    for s in seqs.values():
        for i, c in enumerate(s):
            if c == code and i + 1 < len(s):
                n += 1; hit += "M" in s[i + 1:i + 1 + k]
    return round(hit / n, 3), n
R["within5_M_anchor"] = within_k("M")

# Inter-event time (seconds) from the anchor to the next event, when that event is a manipulation.
def gap(df): x = (df.nxt_t - df.timestamp).dt.total_seconds()[df.nextM.eq(1)]; return [round(float(x.median()), 1), round(float(x.quantile(.25)), 1), round(float(x.quantile(.75)), 1)]
R["seconds_to_next_M_median_iqr"] = {"reply": gap(groups["reply"]), "tutor_initiated": gap(groups["tutor_initiated"]), "M_to_M": gap(groups["M_to_M"])}
# Leaving the module page right after support (next event on another page) and session end.
R["next_event_on_other_page"] = {k: round(float((v.nxt_page != v.page).mean()), 3) for k, v in (("reply", groups["reply"]), ("tutor_initiated", groups["tutor_initiated"]))}

# Requests without an immediate reply: what came next.
U = d[d.c.eq("U")]
R["request_next_code"] = U.nxt.fillna("session_end").value_counts().to_dict()

# Lags +3..+10 after a request (Figure 6): mean composition and truncated windows.
P = pd.read_csv("figures/data/figA_peri_event.csv"); P = P[P.panel.str.contains("requests") & P.lag.between(3, 10)]
R["req_lag3_10_mean_share"] = P.groupby("cat").share.mean().round(3).to_dict()
n10 = int(P[P.lag.eq(10)].n.iloc[0]); R["req_windows_reaching_lag10"] = n10

# Time from module entry (start of the page visit) to the first request in that visit, module pages only.
vis = d[d.page.ne("portal")].groupby("visit")
rows = []
for v, g in vis:
    u = g[g.c.eq("U")]
    if len(u): rows.append((u.timestamp.iloc[0] - g.timestamp.iloc[0]).total_seconds() / 60)
rows = np.array(rows)
R["module_entry_to_first_request_min"] = {"n_visits_with_request": int(len(rows)), "median": round(float(np.median(rows)), 2),
                                          "iqr": [round(float(np.quantile(rows, .25)), 2), round(float(np.quantile(rows, .75)), 2)],
                                          "share_within_5min": round(float((rows <= 5).mean()), 3)}
R["n_module_visits"] = int(d[d.page.ne("portal")].visit.nunique())

# Help episodes (RQ3): maximal runs of learner requests and tutor replies within a session.
d["prv"] = d.groupby("session_id").c.shift()
d["ep"] = (~d.c.isin(["U", "R"])).cumsum()
E = d[d.c.isin(["U", "R"])]
ep_req = E[E.c.eq("U")].groupby(["session_id", "ep"]).size()
starts = d[d.c.eq("U") & ~d.prv.isin(["U", "R"])]
hit5 = n_ep = 0
for (s, e), g in E.groupby(["session_id", "ep"]):
    if not g.c.eq("U").any(): continue           # a delayed reply alone is part of the preceding dialogue
    pos =d.index.get_loc(g.index[-1]); nxt = d.iloc[pos + 1:pos + 6]; nxt = nxt[nxt.session_id.eq(s)]
    n_ep += 1; hit5 += int(nxt.c.eq("M").any())
R["episodes"] = {"n": int(len(ep_req)), "requests_per_episode_max": int(ep_req.max()), "multi_request": int((ep_req > 1).sum()),
                 "reply_then_request": int((d.c.eq("R") & d.nxt.eq("U")).sum()), "n_reply": int(d.c.eq("R").sum()),
                 "start_prev": starts.prv.fillna("START").value_counts().to_dict(), "M_within5_after_end": hit5, "n_with_end": n_ep}
R["request_prev_code"] = d[d.c.eq("U")].prv.fillna("START").value_counts().to_dict()
dump(R, RESULTS / "review_r1.json")
import json; print(json.dumps(R, indent=1))
