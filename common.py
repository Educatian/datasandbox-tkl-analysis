"""Shared config, event coding and estimators for the consent-16 TKL analysis (one module, imported by every script).

Paths come from environment variables that repro/run_all.py sets; the defaults are relative to this folder, so the
scripts also run on their own once data/ holds the consented extract. No absolute paths live in code.
"""
import json, math, os
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
from scipy import stats

ROOT = Path(__file__).resolve().parent
env = lambda var, default: Path(os.environ.get(var, ROOT / default))
DATA = env("TKL_DATA", "data")                  # consented extract + crosswalk (gitignored)
RESULTS = env("TKL_RESULTS", "results")         # aggregate results
FIGDATA = env("TKL_FIGDATA", "figures/data")    # aggregate figure inputs read by the R scripts
# raw inputs (outside the package; only build_extract.py, esm_outcome.py and jev_agreement_consent16.py read them)
RAW_LOGS = env("TKL_RAW_LOGS", "data/raw/user_logs_participants.csv")
RAW_CODES = env("TKL_RAW_CODES", "data/raw/manual_chat_codes.csv")
GRADES = env("TKL_GRADES", "data/raw/provisional_crosswalk_analysis_pseudonymized.csv")
JEV_LOG = env("TKL_JEV_LOG", "data/raw/jev_second_coder_log.csv")
SEED = int(os.environ.get("TKL_SEED", 20261121))  # every bootstrap draws from np.random.default_rng(SEED)
TZ = "America/Denver"                             # course time zone; dates and weeks are local (Mountain) time
NON_OUTCOME = ["U", "R", "T", "S"]                # chat + system codes, never in a manipulation denominator
GROUP = {"M": "Manipulation", "U": "Learner request", "R": "Tutor message", "T": "Tutor message",
         "G": "Navigation", "P": "Navigation", "S": "Login or logout"}   # display categories for Figures 6-7


def crosswalk():
    """Account-number crosswalk and window rules (data/crosswalk.json; local only, never in the package)."""
    return json.load(open(DATA / "crosswalk.json"))


def suffix(v):
    """Trailing account number of a log account or a typed login ID; None if absent."""
    s = str(v).strip().split("@")[0]
    digits = s[len(s.rstrip("0123456789")):]
    return int(digits) if digits else None


def week_mt(ts):
    """Monday of the course week in Mountain time, as a naive date-time (weeks start Monday)."""
    loc = ts.dt.tz_convert(TZ).dt.tz_localize(None).dt.normalize()
    return loc - pd.to_timedelta(loc.dt.weekday, unit="D")


def split_tutor(d, col):
    """Split tutor messages B into R (reply: right after U, or continuing a reply chain) and T (tutor-initiated).
    Within session only: the first event of a session has no predecessor, so a leading B is T. Needs d sorted."""
    out, prev, sid = [], None, None
    for s, c in zip(d.session_id, d[col]):
        if s != sid: prev, sid = None, s
        if c == "B": c = "R" if prev in ("U", "R") else "T"
        out.append(c); prev = c
    return out


def load_logs():
    """Consented extract, sorted within session by time (stable: tied timestamps keep extract order), with codes:
      c4  locked 2026-05-04 scheme  M = SMART/UI/CUSTOM click (any page, auth included), U, B, G = global click
      c4s c4 with B split into R/T
      c7  corrected scheme before the split  U, B, S = auth custom event, G = global click, P = other portal event,
          M = everything else (module-page simulation controls)
      c   corrected 7-code scheme of Table 1 (M, G, P, S, U, R, T)
    plus sess_req (1 if the session holds any learner request) and week (Mountain-time Monday)."""
    d = pd.read_csv(DATA / "user_logs_consented.csv")
    d["timestamp"] = pd.to_datetime(d.timestamp, utc=True, format="ISO8601")
    d = d.sort_values(["session_id", "timestamp"], kind="stable").reset_index(drop=True)
    chat = d.click_type.eq("CHAT"); user = chat & d.target_tag.eq("USER"); bot = chat & d.target_tag.eq("BOT")
    auth = d.click_type.eq("CUSTOM_EVENT") & d.target_tag.eq("auth"); glob = d.click_type.eq("GLOBAL_CLICK")
    d["c4"] = np.select([d.click_type.isin(["SMART_CLICK", "UI_CLICK", "CUSTOM_EVENT"]), user, bot, glob], list("MUBG"), "X")
    d["c7"] = np.select([user, bot, auth, glob, d.page.eq("portal")], list("UBSGP"), "M")
    d["c4s"] = split_tutor(d, "c4"); d["c"] = split_tutor(d, "c7")
    d["sess_req"] = d.groupby("session_id").c.transform(lambda s: int(s.eq("U").any()))
    d["week"] = week_mt(d.timestamp)
    return d


def sequences(d, col="c"):
    """One code list per session, in time order (lag-1 transitions never cross a session boundary)."""
    return [g[col].tolist() for _, g in d.groupby("session_id", sort=False)]


def lsa(d, col, states):
    """Lag-1 lag-sequential analysis within sessions. Returns observed counts, adjusted residuals
    z = (O - E) / sqrt(E (1 - r/N)(1 - c/N)), E = r c / N (Bakeman & Quera, 2011), and row probabilities."""
    obs = pd.DataFrame(0.0, index=states, columns=states)
    for s in sequences(d, col):
        for a, b in zip(s[:-1], s[1:]): obs.loc[a, b] += 1
    N = obs.values.sum(); r = obs.sum(1).values; c = obs.sum(0).values
    E = np.outer(r, c) / N
    with np.errstate(divide="ignore", invalid="ignore"):
        Z = (obs.values - E) / np.sqrt(E * (1 - r[:, None] / N) * (1 - c[None, :] / N))
    return obs, pd.DataFrame(np.nan_to_num(Z), index=states, columns=states), obs.div(obs.sum(1).replace(0, np.nan), axis=0)


def varying_pages(df, f):
    """With page FE, drop pages where the outcome never varies (perfect prediction), as conditional logit does."""
    if "C(page)" not in f: return df
    y = f.split("~")[0].strip()
    return df[df.groupby("page")[y].transform("nunique") > 1]


def gee(df, f, label):
    """GEE logistic, exchangeable working correlation, clusters = learner; OR for sess_req with robust and
    bias-reduced (Mancl-DeRouen) 95% Wald CIs. Row order does not matter for the exchangeable structure."""
    df = varying_pages(df, f)
    rec = {"model": label, "n_events": len(df), "n_learners": df.user_id.nunique(), "n_pages": df.page.nunique()}
    for cov in ("robust", "bias_reduced"):
        m = smf.gee(f, groups="user_id", data=df, family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit(cov_type=cov)
        b, se = m.params["sess_req"], m.bse["sess_req"]
        rec["OR"] = round(math.exp(b), 3)
        rec[f"lo_{cov}"] = round(math.exp(b - 1.96 * se), 3); rec[f"hi_{cov}"] = round(math.exp(b + 1.96 * se), 3)
        rec[f"p_{cov}"] = round(float(2 * stats.norm.sf(abs(b / se))), 3)
    return rec


def dump(obj, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(obj, open(path, "w"), indent=1, default=str)
