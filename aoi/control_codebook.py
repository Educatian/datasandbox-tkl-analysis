"""Step 1 of the AOI work: map each logged control (page, target_tag, target_class) to the source element(s) that carry
that className in the Feb-2026 app build, with a label (visible text, aria-label, or onClick handler).
Unit: control class. Output (aggregate, no learner data): results/aoi/control_codebook.csv
  n_events  = SMART_CLICK + GLOBAL_CLICK events with this class in the consented extract
  n_sources = elements in the source with exactly this className -> 1 = unambiguous; >1 = needs XY to tell apart
Run: python -X utf8 aoi/control_codebook.py"""
import re
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "figures/interface/ds31_feb18"
OUT = ROOT / "results/aoi"; OUT.mkdir(parents=True, exist_ok=True)

files = {p: p.read_text(encoding="utf-8", errors="ignore") for p in list(SRC.glob("components/*.tsx")) + [SRC / "App.tsx"]}
# page id -> rendering component (App.tsx CURRICULUM + render switch, Feb-2026 build); shared files are searched for every page
PAGE_FILE = {"data-sorter": "DataSorterGame", "god-mode": "GodModeSwitch", "summation-machine": "SummationMachine",
             "bin-squeezer": "ZTestAnalysis", "rank-line": "RankLine", "box-plot": "BoxPlotBuilder", "balance-beam": "BalanceBeam",
             "dart-board": "DartBoard", "mode-viz": "ModeVisualizer", "prob-scanner": "ProbabilityScannerGame",
             "sample-pumper": "ConfidenceIntervalAnalysis", "galton-board": "GaltonBoard", "coin-flipper": "CoinFlipper",
             "radar-detector": "ZTestAnalysis", "p-hacking": "PHackingSim", "power-triangle": "PowerAnalysisGame", "portal": "App"}
SHARED = {"App", "UnifiedGenAIChat"}
d = pd.read_csv(ROOT / "data/user_logs_consented.csv")
c = d[d.click_type.isin(["SMART_CLICK", "GLOBAL_CLICK"]) & d.target_class.notna()]
combos = c.groupby(["page", "click_type", "target_tag", "target_class"]).size().rename("n_events").reset_index()


def label_at(src, i, tag):
    """Visible text / aria-label / onClick handler of the JSX element whose className starts near index i."""
    start = src.rfind("<", 0, i); end = src.find(">", i)
    head = src[start:end + 1]
    close = src.find(f"</{tag.lower()}>", end) if tag.isupper() else -1
    inner = re.sub(r"\{[^{}]*\}|<[^>]+>", " ", src[end + 1:close]) if close > 0 and close - end < 600 else ""
    aria = re.search(r'aria-label="([^"]+)"', head); click = re.search(r"onClick=\{\(?\)?\s*=?>?\s*([\w.]+)", head)
    onchange = re.search(r"onChange=\{[^}]*?(set\w+)", head)
    text = " ".join(inner.split())[:60]
    return text or (aria.group(1) if aria else "") or (click.group(1) if click else "") or (onchange.group(1) if onchange else "")


rows = []
for r in combos.itertuples():
    hits = []
    want = {PAGE_FILE.get(r.page)} | SHARED
    for p, src in files.items():
        if p.stem not in want: continue
        for m in re.finditer(r'className=(?:"([^"]*)"|\{`([^`]*)`\})', src):
            lit, tpl = m.group(1), m.group(2)
            if lit is not None: ok = " ".join(lit.split()) == r.target_class.strip()
            else:  # template: every static chunk must appear in the logged class, in order
                chunks = [" ".join(s.split()) for s in re.split(r"\$\{[^}]*\}", tpl) if s.strip()]
                pos, ok = 0, bool(chunks)
                for ch in chunks:
                    k = r.target_class.find(ch, pos)
                    if k < 0: ok = False; break
                    pos = k + len(ch)
            if ok: hits.append((p.name, label_at(src, m.start(), r.target_tag)))
    rows.append({"page": r.page, "click_type": r.click_type, "target_tag": r.target_tag, "n_events": r.n_events,
                 "n_sources": len(hits), "files": ";".join(sorted({h[0] for h in hits})),
                 "labels": " | ".join(h[1] for h in hits)[:200], "target_class": r.target_class})
cb = pd.DataFrame(rows).sort_values(["page", "n_events"], ascending=[True, False])
cb.to_csv(OUT / "control_codebook.csv", index=False)
ev = cb.n_events.sum()
print(f"classes {len(cb)}; events {ev}")
for k, lab in [(1, "unambiguous (1 source element)"), (0, "not found in source")]:
    s = cb[cb.n_sources == k]; print(f"  {lab}: {len(s)} classes, {s.n_events.sum()} events ({s.n_events.sum() / ev:.1%})")
s = cb[cb.n_sources > 1]; print(f"  ambiguous (>1 element, needs XY): {len(s)} classes, {s.n_events.sum()} events ({s.n_events.sum() / ev:.1%})")
