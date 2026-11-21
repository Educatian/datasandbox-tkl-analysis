"""Main descriptive analyses on the consent-restricted extract: sample, Table 1, RQ1 (survival, module x week),
RQ2 (Table 2, profiles), RQ3 within-session before/after test. Session-level GEE, LSA and the specification set are
in sensitivity.py. Writes aggregates only to results/reanalysis/.
Run: python -X utf8 reanalysis.py
"""
import numpy as np, pandas as pd
from scipy import stats
from lifelines import KaplanMeierFitter
from common import DATA, NON_OUTCOME, RESULTS, TZ, dump, load_logs

OUT = RESULTS / "reanalysis"; OUT.mkdir(parents=True, exist_ok=True)
d = load_logs(); R = {}
d["is_m"] = d.c.eq("M").astype(int)

# ---------- Sample (Method, Setting and Participants; Table 1 note) ----------
# Unit: event / logger session_id / learner. Feeds: 6,726 events, 72 sessions, 15 learners, 16 modules + portal,
# Jan 14-Feb 15, 55-835 events and 2-11 sessions per learner, 86% of events on the three class days.
per = d.groupby("user_id").agg(n=("c", "size"), s=("session_id", "nunique"))
local = d.timestamp.dt.tz_convert(TZ).dt.date.astype(str)
R["sample"] = {"events": len(d), "sessions": d.session_id.nunique(), "learners": d.user_id.nunique(),
               "pages": d.page.nunique(), "modules": d.page[d.page.ne("portal")].nunique(), "first_day": local.min(), "last_day": local.max(),
               "events_per_learner": [int(per.n.min()), int(per.n.max())], "sessions_per_learner": [int(per.s.min()), int(per.s.max())],
               "class_day_share": round(float(local.isin(["2026-01-14", "2026-01-26", "2026-02-02"]).mean()), 4)}

# ---------- Table 1: event codes ----------
# Unit: event. Corrected codes (c) vs the earlier 4-code scheme (c4). Feeds Table 1 and "1,354 events ... 404 tutor
# messages ... only 40 were [replies]" (Data and Event Coding).
R["counts_corrected"] = d.c.value_counts().to_dict()
R["counts_earlier"] = d.c4.value_counts().to_dict()
R["reclassified_from_earlier_M"] = {"system": int((d.c4.eq("M") & d.c.eq("S")).sum()), "portal": int((d.c4.eq("M") & d.c.eq("P")).sum())}

# ---------- RQ3: manipulation share before vs after the first request, within session ----------
# Unit: session with a request and >= 3 non-chat, non-system events on each side of the first request (the request
# itself excluded). Share = M / (M + G + P). Wilcoxon signed-rank on post - pre (scipy default: two-sided, zero_method
# "wilcox"). Feeds ".60 before and .67 after ... (14 sessions; W = 39, p = .43)".
rows = []
for _, g in d.groupby("session_id"):
    idx = np.flatnonzero(g.c.values == "U")
    if not len(idx): continue
    pre, post = g.iloc[:idx[0]], g.iloc[idx[0] + 1:]
    pre, post = pre[~pre.c.isin(NON_OUTCOME)], post[~post.c.isin(NON_OUTCOME)]
    if len(pre) >= 3 and len(post) >= 3: rows.append((pre.is_m.mean(), post.is_m.mean()))
t3 = np.array(rows); w3 = stats.wilcoxon(t3[:, 1] - t3[:, 0])
R["T3"] = {"n_sessions": len(t3), "pre": round(float(t3[:, 0].mean()), 3), "post": round(float(t3[:, 1].mean()), 3),
           "n_down": int((t3[:, 1] < t3[:, 0]).sum()), "n_up": int((t3[:, 1] > t3[:, 0]).sum()),
           "W": float(w3.statistic), "p": round(float(w3.pvalue), 4)}

# ---------- RQ1: time to first request (Kaplan-Meier) ----------
# Unit: session. Start = first logged event of the session (any code). Event = first learner request (U);
# T = minutes to it. Censoring: sessions without a request are censored at their last event. Sessions with T = 0 are
# dropped, then the 0.1-120 min rule is applied to T (observed time: to the request, or to the last event if censored);
# a request session left open > 120 min after an early request is therefore kept (see crosscheck.md).
# Feeds: 57 sessions, 15 events, conditional median 3.18 (IQR 2.25-5.47), S(5) = .767, S(10) = .637; Figure 4.
surv = []
for _, g in d.groupby("session_id"):
    t0, u = g.timestamp.iloc[0], g.timestamp[g.c.eq("U")]
    if len(u): surv.append(((u.iloc[0] - t0).total_seconds() / 60, 1))
    elif (T := (g.timestamp.iloc[-1] - t0).total_seconds() / 60) > 0: surv.append((T, 0))
S = pd.DataFrame(surv, columns=["T", "event"]); S = S[S["T"].between(0.1, 120)]
S.to_csv(OUT / "survival_frame.csv", index=False)       # minutes + event flag only, no IDs or clock times
km = KaplanMeierFitter().fit(S["T"], S.event); ev = S.loc[S.event.eq(1), "T"]
R["survival"] = {"n_sessions": len(S), "n_events": int(S.event.sum()), "conditional_median_min": round(float(ev.median()), 2),
                 "iqr_min": [round(float(ev.quantile(q)), 2) for q in (.25, .75)],
                 "S5": round(float(km.predict(5)), 3), "S10": round(float(km.predict(10)), 3),
                 "at_risk_30": int((S["T"] >= 30).sum())}

# ---------- RQ1: requests by module and Mountain-time course week ----------
# Unit: learner request (U). Feeds "Ten of the 15 learners made 45 requests in 15 of the 72 sessions (median = 3 per
# requester, range = 1-12)" and "Forty-two of the 45 requests fell in the two busiest course weeks".
req = d[d.c.eq("U")]; per_req = req.user_id.value_counts()
busy = d.groupby("week").size().nlargest(2).index          # busiest weeks by events (Figure 1 bold weeks)
R["requests"] = {"n": len(req), "sessions": req.session_id.nunique(), "learners": req.user_id.nunique(),
                 "per_requester_median": float(per_req.median()), "per_requester_range": [int(per_req.min()), int(per_req.max())],
                 "by_module": req.page.value_counts().to_dict(),
                 "by_week": {str(k.date()): int(v) for k, v in req.week.value_counts().sort_index().items()},
                 "in_two_busiest_weeks": int(req.week.isin(busy).sum())}

# ---------- RQ2: Table 2, content codes ----------
# Unit: coded request (one primary code each; consented, in-window codes from build_extract.py). Learners (n) =
# distinct requesters with >= 1 request of that code. Feeds Table 2, "Three learners wrote 30 of the 45 requests",
# "two wrote all 10 frustration messages".
codes = pd.read_csv(DATA / "manual_chat_codes_consented.csv")
t2 = codes.groupby("code").agg(n=("code", "size"), learners=("user", "nunique"))
t2["pct"] = (100 * t2.n / len(codes)).round(1)
R["table2"] = {"by_code": t2.to_dict("index"), "total": len(codes), "requesters": codes.user.nunique(),
               "top3_requests": int(codes.user.value_counts().head(3).sum())}

# ---------- RQ2: descriptive activity profiles ----------
# Unit: learner. Request rate = U / all events; manipulation rate = M / non-chat, non-system events (M + G + P).
# Request-rate tertiles: learners sorted by rate (stable), cut 5/5/5 (n // 3); manipulation split at the median
# (rate >= median counts as high, so 8 high / 7 low); middle tertile = "moderate" -> five profiles.
# The earlier scheme (2026-05-04 rule: M4 share of all events) is applied to the SAME 15 learners, so the comparison
# isolates the coding change. Feeds "3 of the 15 learners changing profiles" (Findings RQ2; now 2, see crosscheck.md).
def profiles(qrate, mrate):
    u = pd.DataFrame({"q": qrate, "m": mrate}).sort_values("q", kind="stable"); n = len(u)
    tier = np.array(["low"] * (n // 3) + ["mid"] * (n // 3) + ["high"] * (n - 2 * (n // 3)))
    hi = np.where(u.m >= u.m.median(), "high-manipulation", "low-manipulation")
    return pd.Series(np.where(tier == "mid", "moderate", np.char.add(np.char.add(tier, "-request/"), hi)), index=u.index)
by = d.groupby("user_id"); qrate = by.c.apply(lambda s: s.eq("U").mean())
new = profiles(qrate, d[~d.c.isin(NON_OUTCOME)].groupby("user_id").is_m.mean())
old = profiles(qrate, by.c4.apply(lambda s: s.eq("M").mean())).reindex(new.index)
R["profiles"] = {"corrected": new.value_counts().to_dict(), "earlier_coding_same_sample": old.value_counts().to_dict(),
                 "changed": int((new != old).sum()), "of": len(new)}

dump(R, OUT / "reanalysis_summary.json")
print(pd.Series(R, dtype=object).to_string())
