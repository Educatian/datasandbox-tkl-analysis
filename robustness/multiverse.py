"""Coding multiverse for RQ3 (2026-11-26). Every combination of five event-coding choices that earlier versions of the
analysis made differently (2^5 = 32 codings) is applied to the same consented extract; each RQ3 statistic and claim is
computed under every coding, and claims are kept as findings only if they hold in all 32 (or are reported as coding-dependent).
Choices (True = the manuscript's coding):
  chat   clicks in the chat panel (send button, input box) merged into the request (False: counted as manipulation M)
  back   clicks on a module's back-to-portal button coded as navigation P (False: M)
  system login/logout custom events coded S (False: M)
  portal events on the portal page coded P (False: M)
  dedup  a custom module event fired within 2 s after a simulation click on the same page is dropped as a duplicate
Unit of analysis: lag-1 transitions within sessions; dialogues (runs of U/R); session-level GEE on module pages.
Also: leave-one-learner-out (jackknife) ranges of the dialogue-level statistics under the manuscript coding.
Outputs (aggregate): results/robustness/multiverse.csv, multiverse_claims.csv, jackknife.csv
Run: python -X utf8 robustness/multiverse.py"""
import itertools, math, sys
from pathlib import Path
import numpy as np, pandas as pd
import statsmodels.api as sm, statsmodels.formula.api as smf
from scipy import stats
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import BACK_ICON_CLASS, DATA, RESULTS, chat_ui_clicks, split_tutor, varying_pages

OUT = RESULTS / "robustness"; OUT.mkdir(parents=True, exist_ok=True)
raw = pd.read_csv(DATA / "user_logs_consented.csv")
raw["timestamp"] = pd.to_datetime(raw.timestamp, utc=True, format="ISO8601")
raw = raw.sort_values(["session_id", "timestamp"], kind="stable").reset_index(drop=True)
lab = raw.context_label.fillna("")
raw["is_back"] = raw.click_type.eq("SMART_CLICK") & raw.target_tag.eq("BUTTON") & raw.page.ne("portal") & (
    lab.str.startswith("← Back to Portal") | lab.str.startswith("← Exit Simulation") | raw.target_class.fillna("").eq(BACK_ICON_CLASS))
raw["is_chatui"] = chat_ui_clicks(raw)
prev_click = (raw.click_type.shift().isin(["SMART_CLICK", "UI_CLICK"]) & raw.page.eq(raw.page.shift()) & raw.session_id.eq(raw.session_id.shift())
              & (raw.timestamp - raw.timestamp.shift()).dt.total_seconds().le(2))
raw["is_dup"] = raw.click_type.eq("CUSTOM_EVENT") & ~raw.target_tag.eq("auth") & prev_click


def code(chat, back, system, portal, dedup):
    d = raw.copy()
    if chat: d = d[~d.is_chatui]
    if dedup: d = d[~d.is_dup]
    d = d.reset_index(drop=True)
    ch = d.click_type.eq("CHAT"); user = ch & d.target_tag.eq("USER"); bot = ch & d.target_tag.eq("BOT")
    auth = d.click_type.eq("CUSTOM_EVENT") & d.target_tag.eq("auth"); glob = d.click_type.eq("GLOBAL_CLICK")
    conds = [user, bot, auth if system else np.zeros(len(d), bool), glob,
             (d.page.eq("portal") if portal else np.zeros(len(d), bool)) | (d.is_back if back else np.zeros(len(d), bool))]
    d["c7"] = np.select(conds, list("UBSGP"), "M")
    d["c"] = split_tutor(d, "c7")
    d["nxt"] = d.groupby("session_id").c.shift(-1)
    d["sess_req"] = d.groupby("session_id").c.transform(lambda s: int(s.eq("U").any()))
    return d


def dialogues(d):
    """(return within 5 events: M; left within 5: back-button click before any M) for each dialogue end."""
    rows = []
    for _, g in d.groupby("session_id", sort=False):
        c, b, u, pg = g.c.tolist(), g.is_back.tolist(), g.user_id.iloc[0], g.page.tolist()
        i = 0
        while i < len(c):
            if c[i] == "U":
                j = i
                while j + 1 < len(c) and c[j + 1] in "UR": j += 1
                w = list(range(j + 1, min(j + 6, len(c))))
                fm = next((k for k in w if c[k] == "M"), None); fb = next((k for k in w if b[k]), None)
                left = fb is not None and (fm is None or fb < fm)
                later = left and any(c[k] == "M" and pg[k] not in ("portal", pg[j]) for k in range(fb + 1, len(c)))
                rows.append({"user": u, "ret5": fm is not None, "left5": left, "left_then_other": later, "end5": len(w) < 5 and fm is None and fb is None})
                i = j + 1
            else: i += 1
    return pd.DataFrame(rows)


def leave_base(d):
    """Share of manipulations followed within 5 events by a back-button click before any further manipulation."""
    hits = n = 0
    for _, g in d.groupby("session_id", sort=False):
        c, b = g.c.tolist(), g.is_back.tolist()
        for i, x in enumerate(c):
            if x != "M": continue
            n += 1; w = range(i + 1, min(i + 6, len(c)))
            fm = next((k for k in w if c[k] == "M"), None); fb = next((k for k in w if b[k]), None)
            hits += fb is not None and (fm is None or fb < fm)
    return hits / n


def gee_or(d):
    m = d[d.page.ne("portal") & d.c.isin(["M", "G"])].assign(y=lambda x: x.c.eq("M").astype(int))
    m = varying_pages(m, "y ~ sess_req + C(page)")
    f = smf.gee("y ~ sess_req + C(page)", groups="user_id", data=m, family=sm.families.Binomial(),
                cov_struct=sm.cov_struct.Exchangeable()).fit(cov_type="bias_reduced")
    b, se = f.params["sess_req"], f.bse["sess_req"]
    return math.exp(b), math.exp(b - 1.96 * se), math.exp(b + 1.96 * se)


def stats_for(d):
    p = lambda src, tgt: (d[d.c == src].nxt == tgt).mean()
    dl = dialogues(d); orr, lo, hi = gee_or(d)
    return {"reply_next_M": p("R", "M"), "T_next_M": p("T", "M"), "MM_cont": p("M", "M"), "base_next_M": (d.nxt == "M").mean(),
            "dialogue_ret5": dl.ret5.mean(), "dialogue_left5": dl.left5.mean(), "leave_base": leave_base(d),
            "n_M": int((d.c == "M").sum()), "gee_OR": orr, "gee_lo": lo, "gee_hi": hi}


rows = []
for combo in itertools.product([True, False], repeat=5):
    k = dict(zip(["chat", "back", "system", "portal", "dedup"], combo))
    rows.append({**k, **stats_for(code(**k))})
mv = pd.DataFrame(rows)
mv["manuscript"] = mv.chat & mv.back & mv.system & mv.portal & ~mv.dedup
mv.round(4).to_csv(OUT / "multiverse.csv", index=False)

CLAIMS = {
    "C1 Replies were rarely followed directly by manipulation (below the base rate)": mv.reply_next_M < mv.base_next_M,
    "C2 Tutor-initiated messages were followed by manipulation more often than replies": mv.T_next_M > mv.reply_next_M,
    "C3 Tutor-initiated messages: manipulation below the M->M continuation rate": mv.T_next_M < mv.MM_cont,
    "C4 After a dialogue, half or fewer returned to manipulation within 5 events": mv.dialogue_ret5 <= 0.5,
    "C5 Leaving the module after a dialogue exceeded leaving after a manipulation": mv.dialogue_left5 > mv.leave_base,
    "C6 Sessions with a request: OR < 1 with the interval excluding 1": mv.gee_hi < 1,
    "C7 Sessions with a request: OR < 1 (point estimate)": mv.gee_OR < 1,
}
cl = pd.DataFrame([{"claim": c, "holds_in": int(s.sum()), "of": len(mv), "manuscript_coding": bool(s[mv.manuscript].iloc[0])}
                   for c, s in CLAIMS.items()])
cl.to_csv(OUT / "multiverse_claims.csv", index=False)

# leave-one-learner-out under the manuscript coding
d0 = code(True, True, True, True, False); dl0 = dialogues(d0); jk = []
for u in d0.user_id.unique():
    d1 = d0[d0.user_id != u]; dl1 = dl0[dl0.user != u]
    jk.append({"left_out": "learner", "reply_next_M": (d1[d1.c == "R"].nxt == "M").mean(), "T_next_M": (d1[d1.c == "T"].nxt == "M").mean(),
               "dialogue_ret5": dl1.ret5.mean() if len(dl1) else np.nan, "dialogue_left5": dl1.left5.mean() if len(dl1) else np.nan})
jk = pd.DataFrame(jk); jk.describe().loc[["min", "max"]].round(3).to_csv(OUT / "jackknife.csv")
import json
json.dump({"back_clicks": int(raw.is_back.sum()), "dialogues": len(dl0), "ret5": int(dl0.ret5.sum()), "left5": int(dl0.left5.sum()), "left_then_other": int(dl0.left_then_other.sum()),
           "left5_pct": round(100 * dl0.left5.mean(), 1), "leave_base_pct": round(100 * leave_base(d0), 1),
           "claims": {r.claim[:2]: [int(r.holds_in), int(r.of)] for r in cl.itertuples()},
           "jk": {c: [round(100 * jk[c].min(), 1), round(100 * jk[c].max(), 1)] for c in ["reply_next_M", "T_next_M", "dialogue_ret5", "dialogue_left5"]},
           "unambiguous4": {r.claim[:2]: int(CLAIMS[r.claim][mv.chat & mv.system & mv.portal].sum()) for r in cl.itertuples()},
           "ret5_range_unamb": [round(100 * mv[mv.chat & mv.system & mv.portal].dialogue_ret5.min(), 1), round(100 * mv[mv.chat & mv.system & mv.portal].dialogue_ret5.max(), 1)]},
          open(OUT / "dialogue_summary.json", "w"), indent=1)

pd.set_option("display.width", 200)
print(mv[["chat", "back", "system", "portal", "dedup", "reply_next_M", "T_next_M", "MM_cont", "dialogue_ret5", "dialogue_left5", "leave_base", "gee_OR", "gee_lo", "gee_hi"]]
      .round(2).to_string(index=False))
print("\n", cl.to_string(index=False))
print("\njackknife (min/max):\n", jk.describe().loc[["min", "max"]].round(3).to_string())
