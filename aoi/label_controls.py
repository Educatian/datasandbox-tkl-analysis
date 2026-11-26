"""Step 2 of the AOI work: give every simulation click a control label, in this order:
  1. class   : the logged className matches exactly one element in the module's source (control_codebook.csv)
  2. label   : several elements share the class; the logged context_label (button text) picks one of their source labels
  3. xy_aoi  : still ambiguous; the click's page coordinates fall inside a rendered AOI box (Summation Machine i/n inputs,
               boxes from the local Feb-2026 build at each logged viewport: results/aoi/summation_input_aoi.json; 8 px tolerance)
GLOBAL_CLICK (clicks outside controls) keep their event code G and get no control label.
Per-event output stays in data/ (it carries learner IDs and raw context labels, which can contain login e-mails).
Aggregate output: results/aoi/control_counts.csv (page, control, n events, n learners). Run: python -X utf8 aoi/label_controls.py"""
import json, re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/aoi"
norm = lambda s: re.sub(r"\s+", " ", str(s).replace("&larr;", "←")).strip()
key = lambda s: re.sub(r"[^a-z0-9←+\-−×σ]", "", norm(s).lower())
keyd = lambda s: re.sub(r"[0-9]", "", key(s))  # fallback only: button text can carry live values ("Run 10 Samples")

d = pd.read_csv(ROOT / "data/user_logs_consented.csv")
cb = pd.read_csv(OUT / "control_codebook.csv")
aoi = {(o["w"], o["h"]): o["boxes"] for o in json.load(open(OUT / "summation_input_aoi.json"))}
SUM_INPUT = "w-16 bg-slate-900 border border-slate-700 rounded text-center text-white font-bold"
page_labels = cb.dropna(subset=["labels"]).groupby("page").labels.apply(
    lambda s: sorted({norm(l) for x in s for l in str(x).split(" | ") if norm(l)}))

s = d[d.click_type == "SMART_CLICK"].merge(cb[["page", "click_type", "target_tag", "target_class", "n_sources", "labels"]],
                                           on=["page", "click_type", "target_tag", "target_class"], how="left")


def pick(cands, ctx):
    for kf in (key, keyd):  # exact text first (keeps "Flip 1x" vs "Flip 10x", "Q1" vs "Q3" apart), then digit-free
        k = kf(ctx); hit = [c for c in cands if kf(c) and k == kf(c)]
        if len({kf(h) for h in hit}) == 1: return hit[0]
    k = key(ctx); hit = [c for c in cands if key(c) and k.startswith(key(c))]
    if len({key(h) for h in hit}) == 1: return hit[0]
    hit = [c for c in cands if key(c) and key(c).startswith(k) and len(k) >= 3]  # dynamic text, e.g. "Run 10 Samples" vs "Run Samples"
    return hit[0] if len(hit) == 1 else None


def label(r):
    srcs = [norm(l) for l in str(r.labels).split(" | ")] if isinstance(r.labels, str) else []
    if r.n_sources == 1: return (srcs[0] if srcs and srcs[0] else f"{r.target_tag.lower()} control"), "class"
    if isinstance(r.target_class, str) and r.target_class.strip() == SUM_INPUT and r.page == "summation-machine":
        for b, lab in zip(aoi.get((r.viewport_width, r.viewport_height), []), ["Upper limit n", "Start index i"]):
            if b["x0"] - 8 <= r.coord_page_x <= b["x1"] + 8 and b["y0"] - 8 <= r.coord_page_y <= b["y1"] + 8: return lab, "xy_aoi"
        return None, "unresolved"
    cands = [c for c in srcs if c] if r.n_sources and r.n_sources > 1 else page_labels.get(r.page, [])
    p = pick(cands, r.context_label)
    if p: return p, "label"
    k = key(r.context_label)
    if "backtoportal" in k or "exitsimulation" in k: return "← Back to Portal", "label"
    if r.page == "portal" and k.startswith("the"): return "Module card", "label"  # click inside a module card (card text)
    return None, "unresolved"


s[["control", "how"]] = s.apply(lambda r: pd.Series(label(r)), axis=1)

# 3) xy_aoi for anything still generic or unresolved: rendered AOI map of the module at the click's viewport
#    (results/aoi/module_aoi.json, local Feb-2026 build); slider labels lose their live values; repeated slider names get an index
maps = {}
for o in json.load(open(OUT / "module_aoi.json")):
    els = [e for e in o["els"] if "Ask Dr. Gem" not in e["label"] and e["type"] != "submit"]
    clean = lambda e: re.sub(r"\s*[\d.,%]+$", "", re.sub(r"\s+[\d.]+%?$", "", e["label"])).strip() or (e["tag"].lower() + (" " + e["type"] if e["type"] else ""))
    names = [clean(e) for e in els]
    for e, nm in zip(els, names):
        e["name"] = nm if names.count(nm) == 1 or e["tag"] != "INPUT" else f"{nm} {[x['y0'] for x, m in zip(els, names) if m == nm].index(e['y0']) + 1}"
    maps[(o["page"], o["w"], o["h"])] = els
GENERIC = {"input control", "button control", "setInput", None}
def aoi_label(r):
    els = maps.get((r.page, r.viewport_width, r.viewport_height))
    if not els: return None
    inside = [e for e in els if e["x0"] - 8 <= r.coord_page_x <= e["x1"] + 8 and e["y0"] - 8 <= r.coord_page_y <= e["y1"] + 8]
    same = [e for e in inside if norm(e["cls"]) == norm(r.target_class)] or inside
    return same[0]["name"] if len({e["name"] for e in same}) == 1 else None
g = s.control.isin(GENERIC) | s.control.isna()
lab = s[g].apply(aoi_label, axis=1)
s.loc[g & lab.notna().reindex(s.index, fill_value=False), "how"] = "xy_aoi"
s.loc[g, "control"] = lab.where(lab.notna(), s.loc[g, "control"])
s.loc[s.control.isna() | s.control.isin(GENERIC), "how"] = "unresolved"

# 4) readable names for handler-derived labels (from the component source)
READABLE = {"handleRecord": "Observe & Record / Run Experiment", "setSunlightInput": "Sunlight slider", "toggleRun": "Stream Balls / Stop",
            "navigateTo": "Module card", "handleLogout": "Log out", "setIsAutoRunning": "Auto-Run toggle", "toggleComparisonMode": "Compare Players",
            "onBack": "← Back to Portal", "← Exit Simulation": "← Back to Portal", "runSimulation": "CRUNCH", "setEffectSize": "Effect Size (d)",
            "setSampleSize": "Sample Size (n)", "setAlpha": "Alpha (α)", "setEndN": "Upper limit n", "setStartI": "Start index i"}
s["control"] = s.control.replace(READABLE)
s[["id", "user_id", "session_id", "timestamp", "page", "target_tag", "control", "how"]].to_csv(ROOT / "data/smart_click_controls.csv", index=False)
print(s.how.value_counts().to_dict(), "of", len(s), "SMART_CLICK events;",
      f"resolved {s.how.ne('unresolved').mean():.1%}")
agg = s.dropna(subset=["control"]).groupby(["page", "control"]).agg(n=("id", "size"), learners=("user_id", "nunique")).reset_index()
agg = agg[~agg.control.str.contains("@")]  # never let an e-mail-like label out
agg.sort_values(["page", "n"], ascending=[True, False]).to_csv(OUT / "control_counts.csv", index=False)
json.dump({"clicks": len(s), **{k: int(v) for k, v in s.how.value_counts().items()}}, open(OUT / "aoi_summary.json", "w"), indent=1)
u = s[s.how == "unresolved"]
print("unresolved by page/tag:", u.groupby(["page", "target_tag"]).size().sort_values(ascending=False).head(8).to_dict())
