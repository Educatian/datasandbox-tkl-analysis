"""RQ3 sequence and session-level models, primary and sensitivity (Data Analysis, RQ3 paragraphs; ESM Figures S1-S2).
Writes aggregate tables only to results/.
Run: python -X utf8 sensitivity.py
"""
import math, warnings
import pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
from scipy import stats
from common import NON_OUTCOME, RESULTS, dump, gee, load_logs, lsa, varying_pages
warnings.filterwarnings("ignore")   # statsmodels convergence/domain chatter on the small-cluster fits

d = load_logs()

# ---------- Lag-sequential analysis, three schemes ----------
# Unit: lag-1 transition within a session (6,654 = 6,726 events - 72 sessions). Adjusted residuals from the pooled
# table, |z| > 1.96 read descriptively. Base rate = share of all events coded M (event share, 61.3% corrected);
# Figure 7 / ESM S1 use the next-event base (column share of transitions, 62.0%), computed in the figure prep.
# Feeds: R->M 29/37 = 78.4% (z = 2.06), T->M 281/361 = 77.8% (z = 6.38); earlier coding 81.1% / 82.3% (z = -0.03 / 0.51).
rows = []
for name, col, states in [("locked_pooled", "c4", ["M", "U", "B", "G", "X"]),
                          ("locked_split", "c4s", ["M", "U", "R", "T", "G", "X"]),
                          ("corrected_split", "c", ["M", "U", "R", "T", "G", "P", "S"])]:
    obs, Z, P = lsa(d, col, states)
    obs.astype(int).to_csv(RESULTS / f"lsa_{name}_counts.csv"); Z.round(2).to_csv(RESULTS / f"lsa_{name}_z.csv"); P.round(3).to_csv(RESULTS / f"lsa_{name}_rowprob.csv")
    base = d[col].eq("M").mean()
    for a in [s for s in states if s in ("U", "B", "R", "T")]:
        for b in [s for s in states if s in ("M", "U", "B", "R", "T", "G")]:
            rows.append({"scheme": name, "from": a, "to": b, "n_from": int(obs.loc[a].sum()), "count": int(obs.loc[a, b]),
                         "p_next": round(float(P.loc[a, b]), 3), "z": round(float(Z.loc[a, b]), 2), "base_rate_M": round(float(base), 3)})
lsa_key = pd.DataFrame(rows); lsa_key.to_csv(RESULTS / "lsa_key_transitions.csv", index=False)

# ---------- Session-level GEE specification set (8 models with the FE logits = ESM Figure S2) ----------
# Unit: event, clustered in learner (15 clusters). Predictor sess_req = any learner request in the session.
# Outcome M vs the rest of the denominator. Earlier coding: m_old = c4 == M. Corrected: m_new = c == M with chat and
# system events (U, R, T, S) out of the denominator; primary C2 also drops portal events (module pages: M vs G) and adds
# page FE; pages without outcome variation are dropped (one module, all events M; 15 learners remain).
# Feeds primary OR 0.70 [0.45, 1.09], p = .12, 4,597 events (bias-reduced SE).
d["m_old"] = d.c4.eq("M").astype(int); d["m_new"] = d.c.eq("M").astype(int)
nochat4 = d[~d.c4.isin(["U", "B"])]
nochat7 = d[~d.c.isin(NON_OUTCOME)]; mod7 = nochat7[nochat7.page.ne("portal") & nochat7.c.isin(["M", "G"])]  # M vs G as described; back-button clicks (P on module pages, 2026-11-26 recode) stay out
g = [gee(d, "m_old ~ sess_req", "A1 locked: all events, no FE"),
     gee(d, "m_old ~ sess_req + C(page)", "A2 locked: all events, page FE"),
     gee(nochat4, "m_old ~ sess_req", "B1 locked: chat excluded, no FE"),
     gee(nochat4, "m_old ~ sess_req + C(page)", "B2 locked: chat excluded, page FE"),
     gee(nochat7, "m_new ~ sess_req", "C1 corrected: chat+system excluded, no FE"),
     gee(mod7, "m_new ~ sess_req + C(page)", "C2 corrected: module pages, page FE (manuscript primary)")]
pd.DataFrame(g).to_csv(RESULTS / "gee_models.csv", index=False)

# ---------- Fixed-effects logit robustness check ----------
# ML binomial GLM with learner + page dummies; cluster-robust SEs by learner (same 15-cluster limit as GEE).
def fe_logit(df, f, label):
    df = varying_pages(df, f)
    m = smf.glm(f, data=df, family=sm.families.Binomial()).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(df.user_id)[0]}, maxiter=200)
    b, se = m.params["sess_req"], m.bse["sess_req"]
    return {"model": label, "n_events": len(df), "n_learners": df.user_id.nunique(), "OR": round(math.exp(b), 3),
            "lo_cluster": round(math.exp(b - 1.96 * se), 3), "hi_cluster": round(math.exp(b + 1.96 * se), 3),
            "p_cluster": round(float(2 * stats.norm.sf(abs(b / se))), 3), "converged": bool(m.converged)}
fe = [fe_logit(nochat4, "m_old ~ sess_req + C(page) + C(user_id)", "FE logit locked: chat excluded, page + learner FE"),
      fe_logit(mod7, "m_new ~ sess_req + C(page) + C(user_id)", "FE logit corrected: module pages, page + learner FE")]
pd.DataFrame(fe).to_csv(RESULTS / "fe_logit_models.csv", index=False)
dump({"counts_locked": d.c4s.value_counts().to_dict(), "counts_corrected": d.c.value_counts().to_dict(),
      "lsa_key": rows, "gee": g, "fe_logit": fe,
      "note": "Bias-reduced SEs = statsmodels GEE cov_type='bias_reduced' (Mancl-DeRouen). FE logit = ML logistic with learner and page dummies, cluster-robust SEs by learner."},
     RESULTS / "summary.json")
print(lsa_key[lsa_key["to"].isin(["M", "R", "T", "B"])].to_string(index=False)); print(pd.DataFrame(g).to_string(index=False)); print(pd.DataFrame(fe).to_string(index=False))
