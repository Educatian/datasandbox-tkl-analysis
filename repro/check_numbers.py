"""Self-check: every data-derived number in results/manuscript_numbers.json must match the regenerated outputs at the
precision the manuscript prints (|computed - printed| <= half a unit in the last printed digit).
Exit 0 = all match. 'pending' entries must equal their corrected value and are listed as manuscript updates.
Run: python -X utf8 repro/check_numbers.py
"""
import json, re, sys
from importlib.metadata import version
from pathlib import Path
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import FIGDATA, RESULTS

HERE = Path(__file__).resolve().parent
J = lambda f: json.load(open(RESULTS / f))
ra, sm, sv, esm, jev = J("reanalysis/reanalysis_summary.json"), J("summary.json"), J("survey_summary.json"), J("esm_outcome_key.json"), J("jev_agreement_consent16.json")
F = lambda f: pd.read_csv(FIGDATA / f)
peri, comp, ret, tr, forest, tot, net = (F(f) for f in ("figA_peri_event.csv", "fig3_next_composition.csv", "fig3_return_curve.csv",
                                                       "fig3_transitions.csv", "fig4_forest.csv", "fig2_module_totals.csv", "figC_transitions.csv"))
gee = pd.read_csv(RESULTS / "gee_models.csv"); prim = gee[gee.model.str.contains("primary")].iloc[0]
wave = pd.read_csv(RESULTS / "survey_by_wave.csv").astype({"wave": str}); spear = pd.read_csv(RESULTS / "esm_outcome_spearman.csv")
lsa = pd.DataFrame(sm["lsa_key"]); key = lambda sch, a, b, col: float(lsa.query("scheme == @sch and `from` == @a and to == @b")[col].iloc[0])
pk = lambda panel, lag, cat: peri.query("panel.str.contains(@panel) and lag == @lag and cat == @cat", engine="python")
share = lambda panel, lag, cat: 100 * float(pk(panel, lag, cat).share.sum())
sinfo = (HERE / "sessionInfo.txt").read_text()
zero = tot[(tot.requests == 0) & (tot.sessions >= 10)]
rr_other = spear[(spear.feature == "request_rate") & (spear.outcome != "Assignments Final Score")].rho
link = pd.DataFrame(sv["link"])
s, km, rq, t2, c = ra["sample"], ra["survival"], ra["requests"], ra["table2"], ra["counts_corrected"]

C = {f"versions.{m}": version(m) for m in ("pandas", "statsmodels", "scipy", "lifelines")}
C |= {"versions.python": sys.version.split()[0], "versions.R": re.search(r"R version (\S+)", sinfo)[1],
      "versions.ggplot2": re.search(r"ggplot2_(\S+)", sinfo)[1]}
C |= {"sample.learners": s["learners"], "sample.events": s["events"], "sample.sessions": s["sessions"], "sample.modules": s["modules"],
      "sample.portal_pages": s["pages"] - s["modules"],
      "sample.first_day": s["first_day"], "sample.last_day": s["last_day"],
      "sample.events_per_learner_min": s["events_per_learner"][0], "sample.events_per_learner_max": s["events_per_learner"][1],
      "sample.sessions_per_learner_min": s["sessions_per_learner"][0], "sample.sessions_per_learner_max": s["sessions_per_learner"][1],
      "sample.class_day_pct": 100 * s["class_day_share"], "fig1.learner_rows": len(F("figB_learner_totals.csv"))}
C |= {f"table1.{k}": c[k] for k in "MGPSURT"}
C |= {"earlier.reclassified_as_M": sum(ra["reclassified_from_earlier_M"].values()), "earlier.tutor_messages": ra["counts_earlier"]["B"],
      "jev.n": jev["n"], "jev.agreement_pct": 100 * jev["agreement"], "jev.kappa": jev["kappa"], "jev.ci_lo": jev["ci"][0], "jev.ci_hi": jev["ci"][1],
      "verif.kept": jev["verification"]["kept"], "verif.changed": jev["verification"]["changed"],
      "verif.changed_to_jev": jev["verification"]["changed_to_jev_code"], "jev.disagreements": jev["disagreements"]}
C |= {"km.sessions": km["n_sessions"], "km.events": km["n_events"], "km.at_risk_30": km["at_risk_30"], "km.conditional_median": km["conditional_median_min"],
      "km.iqr_lo": km["iqr_min"][0], "km.iqr_hi": km["iqr_min"][1], "km.S10_pct": 100 * km["S10"], "km.S5": km["S5"]}
C |= {"lsa.transitions": int(comp[comp.source.str.startswith("All")].n.sum()), "gee.dropped_modules": int(len(tot) - prim.n_pages),
      "gee.learners": prim.n_learners}
C |= {"requests.learners": rq["learners"], "requests.n": rq["n"], "requests.sessions": rq["sessions"],
      "requests.per_requester_median": rq["per_requester_median"], "requests.per_requester_min": rq["per_requester_range"][0],
      "requests.per_requester_max": rq["per_requester_range"][1], "requests.two_busiest_weeks": rq["in_two_busiest_weeks"],
      "fig5.galton_requests": tot.set_index("page").requests["galton-board"], "fig5.galton_sessions": tot.set_index("page").sessions["galton-board"],
      "fig5.zero_request_modules_10plus": len(zero), "fig5.zero_request_sessions_min": zero.sessions.min(), "fig5.zero_request_sessions_max": zero.sessions.max()}
for code, r in t2["by_code"].items(): C |= {f"table2.{code}.n": r["n"], f"table2.{code}.pct": r["pct"], f"table2.{code}.learners": r["learners"]}
C |= {"table2.total": t2["total"], "table2.requesters": t2["requesters"], "table2.top3_requests": t2["top3_requests"],
}
rr = J("review_r1.json"); ci = rr["cluster_boot_95ci"]; lag = rr["req_lag3_10_mean_share"]; me = rr["module_entry_to_first_request_min"]
rr_ep = rr["episodes"]
C |= {"epi.n": rr_ep["n"], "epi.multi": rr_ep["multi_request"], "epi.max": rr_ep["requests_per_episode_max"],
      "epi.reply_then_request": rr_ep["reply_then_request"], "epi.start_M": rr_ep["start_prev"].get("M", 0),
      "epi.start_T": rr_ep["start_prev"].get("T", 0), "epi.start_G": rr_ep["start_prev"].get("G", 0), "epi.return": rr_ep["M_within5_after_end"]}
specs = pd.concat([pd.read_csv(RESULTS / "gee_models.csv").OR, pd.read_csv(RESULTS / "fe_logit_models.csv").OR])
C |= {"rev.MM_pct": 100 * rr["next_is_M"]["M_to_M"], "rev.MM_lo": 100 * ci["M_to_M"][0], "rev.MM_hi": 100 * ci["M_to_M"][1],
      "rev.R_lo": 100 * ci["reply"][0], "rev.R_hi": 100 * ci["reply"][1], "rev.T_lo": 100 * ci["tutor_initiated"][0], "rev.T_hi": 100 * ci["tutor_initiated"][1],
      "rev.sec_R": rr["seconds_to_next_M_median_iqr"]["reply"][0], "rev.sec_T": rr["seconds_to_next_M_median_iqr"]["tutor_initiated"][0],
      "rev.T_state_pct": 100 * rr["next_is_M"]["T_state"], "rev.T_state_n": rr["n"]["T_state"],
      "rev.T_welcome_pct": 100 * rr["next_is_M"]["T_welcome"], "rev.T_welcome_n": rr["n"]["T_welcome"],
      "rev.top3_reply_n": rr["without_top3"]["n_reply"], "rev.top3_reply_M": round(rr["without_top3"]["reply"] * rr["without_top3"]["n_reply"]),
      "rev.entry_median": me["median"], "rev.entry_iqr_lo": me["iqr"][0], "rev.entry_iqr_hi": me["iqr"][1], "rev.entry_visits": me["n_visits_with_request"],
      "rev.lag_nav_pct": 100 * lag["Navigation"], "rev.lag_req_pct": 100 * lag["Learner request"], "rev.lag_login_pct": 100 * lag["Login or logout"],
      "rev.windows_truncated": 45 - rr["req_windows_reaching_lag10"], "rev.no_reply": sum(v for k, v in rr["request_next_code"].items() if k != "R"),
      "rev.spec_or_min": specs.min(), "rev.spec_or_max": specs.max(),
      "rev.instrumental_pct": 100 * (t2["by_code"]["sensemaking"]["n"] + t2["by_code"]["clarification"]["n"]) / t2["total"]}
C |= {"fig6.U_prev_M_pct": share("learner", -1, "Manipulation"), "fig6.U_prev_M_n": int(pk("learner", -1, "Manipulation")["count"].sum()),
      "fig6.U_prev_nav_login": int(pk("learner", -1, "Navigation")["count"].sum() + pk("learner", -1, "Login or logout")["count"].sum()),
      "fig6.U_next_tutor_pct": share("learner", 1, "Tutor message"), "fig6.U_plus2_M_pct": share("learner", 2, "Manipulation"),
      "fig6.T_prev_M_pct": share("tutor", -1, "Manipulation"), "fig6.T_plus2_tutor_pct": share("tutor", 2, "Tutor message"),
      "fig6.base_M_pct": 100 * float(F("figA_base.csv").set_index("cat").share["Manipulation"])}
C |= {"next.U_reply_pct": 100 * key("corrected_split", "U", "R", "p_next"), "next.R_n": key("corrected_split", "R", "M", "n_from"),
      "next.R_M_pct": 100 * key("corrected_split", "R", "M", "p_next"), "next.R_z": key("corrected_split", "R", "M", "z"),
      "next.T_n": key("corrected_split", "T", "M", "n_from"), "next.T_M_pct": 100 * key("corrected_split", "T", "M", "p_next"),
      "next.T_z": key("corrected_split", "T", "M", "z"), "next.base_pct": 100 * float(tr[tr.scheme == "Corrected coding"].base.iloc[0]),
      "next.R_ended_session": c["R"] - key("corrected_split", "R", "M", "n_from"),
      "return.R_5_pct": 100 * float(ret.query("source.str.startswith('Reply') and k == 5", engine="python").share.iloc[0]),
      "return.T_5_pct": 100 * float(ret.query("source.str.startswith('Tutor') and k == 5", engine="python").share.iloc[0])}
C |= {"t3.pre": 100 * ra["T3"]["pre"], "t3.post": 100 * ra["T3"]["post"], "t3.sessions": ra["T3"]["n_sessions"], "t3.W": ra["T3"]["W"], "t3.p": ra["T3"]["p"],
      "gee.OR": prim.OR, "gee.lo": prim.lo_bias_reduced, "gee.hi": prim.hi_bias_reduced, "gee.p": prim.p_bias_reduced, "gee.events": prim.n_events,
      "spec.models": len(forest), "spec.intervals_including_1": int(((forest.lo < 1) & (forest.hi > 1)).sum()), "spec.converged": int(forest.converged.sum())}
C |= {"earlier.base_pct": 100 * float(tr[tr.scheme == "Earlier coding"].base.iloc[0]),
      "earlier.R_M_pct": 100 * key("locked_split", "R", "M", "p_next"), "earlier.T_M_pct": 100 * key("locked_split", "T", "M", "p_next"),
      "earlier.R_z": key("locked_split", "R", "M", "z"), "earlier.T_z": key("locked_split", "T", "M", "z"),
      "s3.transitions_with_request": int(net[net.panel.str.contains("with a")]["count"].sum()),
      "s3.transitions_without_request": int(net[net.panel.str.contains("without")]["count"].sum()),
      "s3.max_incoming": int(net.groupby(["panel", "to"])["count"].sum().max())}
w = wave.set_index(["wave", "item"])
for wv in ("1", "2", "3", "all"):
    C |= {f"survey.{wv}.n": w.loc[(wv, "control"), "n"], f"survey.{wv}.learners": w.loc[(wv, "control"), "learners"]}
    for it in ("control", "depth", "ease"): C |= {f"survey.{wv}.{it}.M": w.loc[(wv, it), "M"], f"survey.{wv}.{it}.SD": w.loc[(wv, it), "SD"]}
rq_rho, ev_rho = link[link.x == "requests"].rho, link[link.x == "events"].rho
C |= {"survey.learners": sv["respondents"], "survey.responses": sv["responses"], "survey.wave3_min_M": w.loc["3"].M.min(), "survey.wave3_max_M": w.loc["3"].M.max(),
      "survey.rho_requests_min": rq_rho.min(), "survey.rho_requests_max": rq_rho.max(), "survey.rho_events_min": ev_rho.min(), "survey.rho_events_max": ev_rho.max(),
      "survey.link_n": int(link.n.iloc[0]), "survey.max_responses_in_one_wave": sv["max_responses_in_one_wave"]}
C |= {"esm.n": esm["n"], "esm.n_tests": esm["n_tests"], "esm.rho": esm["rho"], "esm.ci_lo": esm["ci"][0], "esm.ci_hi": esm["ci"][1],
      "esm.request_rate_min": rr_other.min(), "esm.request_rate_max": rr_other.max(), "esm.max_rho": esm["max_abs"]["rho"]}


# ---- control-level (AOI) patterns: Online Resource 1 Note 4, RQ3 Findings ----
A = HERE.parent / "results" / "aoi"
if (A / "aoi_summary.json").exists():
    s4 = json.load(open(A / "aoi_summary.json")); nv = json.load(open(A / "nav_in_M.json"))
    pe = pd.read_csv(A / "patterns_peri.csv").set_index("source").loc["tutor-initiated"]
    pmod = pd.read_csv(A / "patterns_module.csv")
    C |= {"aoi.clicks": s4["clicks"], "aoi.class": s4["class"], "aoi.label": s4["label"], "aoi.xy": s4["xy_aoi"],
          "aoi.resolved": s4["clicks"] - s4["unresolved"], "aoi.resolved_pct": 100 * (1 - s4["unresolved"] / s4["clicks"]),
          "aoi.nav_in_M": nv["nav_in_M"], "aoi.M_events": nv["M_events"],
          "aoi.repeat_min_pct": 100 * pmod.repeat_share.min(), "aoi.repeat_max_pct": 100 * pmod.repeat_share.max(),
          "aoi.T_n": pe["n"], "aoi.T_learners": pe["learners"], "aoi.T_same_pct": 100 * pe["same_control"],
          "aoi.T_base_pct": 100 * pe["base_same_in_module"], "aoi.T_diff_pp": 100 * pe["diff"],
          "aoi.T_diff_lo": 100 * pe["diff_lo"], "aoi.T_diff_hi": 100 * pe["diff_hi"]}


# ---- coding multiverse, dialogue outcomes, leave-one-learner-out (robustness/multiverse.py; Online Resource 1 Note 3) ----
R2 = HERE.parent / "results" / "robustness"
if (R2 / "dialogue_summary.json").exists():
    ds = json.load(open(R2 / "dialogue_summary.json"))
    C |= {"recode.back": ds["back_clicks"], "dlg.n": ds["dialogues"], "dlg.ret5": ds["ret5"], "dlg.left5": ds["left5"],
          "dlg.left_other": ds["left_then_other"], "dlg.left_pct": ds["left5_pct"], "dlg.leave_base_pct": ds["leave_base_pct"],
          "mv.ret_lo": ds["ret5_range_unamb"][0], "mv.ret_hi": ds["ret5_range_unamb"][1], "rev.lag_M_pct": 100 * lag["Manipulation"]}
    for k, (h, n_) in ds["claims"].items(): C[f"mv.{k}"] = h
    for k, (lo_, hi_) in ds["jk"].items(): C[f"jk.{k}_lo"], C[f"jk.{k}_hi"] = lo_, hi_


def match(got, printed):
    if re.fullmatch(r"-?\d*\.?\d+", printed) is None: return str(got) == printed   # versions, dates
    dp = len(printed.split(".")[1]) if "." in printed else 0
    return abs(float(got) - float(printed)) <= 0.5 * 10 ** -dp + 1e-9


fails, pending, n_ok, n_ext = [], [], 0, 0
for e in json.load(open(HERE / "results" / "manuscript_numbers.json"))["numbers"]:
    i, v = e["id"], e["value"]
    if "external" in e: n_ext += 1; continue
    got = C.get(i, "MISSING")
    if "pending" in e:
        (pending if match(got, e["pending"]["new"]) else fails).append(f"{i}: manuscript {v} -> computed {got}"); continue
    if match(got, v): n_ok += 1
    else: fails.append(f"{i}: manuscript {v}, computed {got}")
print(f"checked {n_ok + len(pending) + len(fails)} data-derived numbers: {n_ok} match, {len(pending)} pending manuscript update, "
      f"{len(fails)} mismatch; {n_ext} external (not computed)")
for p in pending: print("  PENDING", p)
for f in fails: print("  FAIL", f)
print("PASS" if not fails else "FAIL"); sys.exit(1 if fails else 0)
