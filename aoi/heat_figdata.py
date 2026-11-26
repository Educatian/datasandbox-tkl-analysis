"""Aggregate inputs for Online Resource Fig. S4 (click heat + AOI transition map, and the after-tutor-message difference map).
Coordinates: page coordinates shifted to the 1440-px reference (centred layout; checked against rendered AOIs).
Outputs (figures/data/, aggregate only: grids, control centroids, transition counts; no learner IDs, no single clicks):
  aoi_heat.csv  page, gx, gy, val   (click density, 10-px cells, Gaussian smoothed, scaled to max 1 per module; cells < .03 dropped)
  aoi_nodes.csv page, control, x, y, actions, repeats   (median click position of each control; repeats = same control again)
  aoi_edges.csv page, from, to, n (switches between controls within a module visit, n >= 2; navigation excluded)
  aoi_diff.csv  page, gx, gy, val   (share of clicks in the 3 clicks after a tutor-initiated message minus share of all clicks)
  aoi_panel.csv page, clicks, actions, repeat_share, after_T_clicks
Run: python -X utf8 aoi/heat_figdata.py"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.ndimage import gaussian_filter
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import FIGDATA, load_logs

PAGES = ["coin-flipper", "sample-pumper", "galton-board", "god-mode", "summation-machine", "rank-line"]
NAV = {"← Back to Portal", "Module card", "Log out"}
d = load_logs().sort_values(["session_id", "timestamp"]).reset_index(drop=True)
d = d.merge(pd.read_csv(Path(__file__).resolve().parents[1] / "data/smart_click_controls.csv")[["id", "control"]], on="id", how="left")
d["x"] = d.coord_page_x + (1440 - d.viewport_width) / 2; d["y"] = d.coord_page_y
d["visit"] = (d.session_id.ne(d.session_id.shift()) | d.page.ne(d.page.shift())).cumsum()
clk = d[d.page.isin(PAGES) & d.click_type.isin(["SMART_CLICK", "GLOBAL_CLICK"]) & ((d.coord_page_x > 0) | (d.coord_page_y > 0))].copy()
clk["after_T"] = False
for _, g in d[d.page.isin(PAGES)].groupby("visit"):
    cl = g.index[g.index.isin(clk.index)]
    for t in g.index[g.c == "T"]: clk.loc[cl[cl > t][:3], "after_T"] = True


def grid(p, sigma=2.2):
    h, _, _ = np.histogram2d(p.y, p.x, bins=(105, 144), range=[[0, 1050], [0, 1440]]); return gaussian_filter(h, sigma)


def long(page, h, thr):
    gy, gx = np.nonzero(np.abs(h) >= thr)
    return pd.DataFrame({"page": page, "gx": gx * 10 + 5, "gy": gy * 10 + 5, "val": h[gy, gx]})


heat, diff, nodes, edges, panel = [], [], [], [], []
for page in PAGES:
    p = clk[clk.page == page]; h = grid(p); h = h / h.max(); heat.append(long(page, h, 0.03))
    a = d[(d.page == page) & (d.c == "M") & d.control.notna() & ~d.control.isin(NAV)].copy()
    a["prev"] = a.groupby("visit").control.shift()
    cen = p[p.control.notna() & ~p.control.isin(NAV)].groupby("control")[["x", "y"]].median()
    a = a[a.control.isin(cen.index)]; pr = a.dropna(subset=["prev"]); pr = pr[pr.prev.isin(cen.index)]
    rep = pr[pr.prev == pr.control].groupby("control").size()
    n = cen.join(a.control.value_counts().rename("actions")).join(rep.rename("repeats")).fillna(0).reset_index().assign(page=page)
    nodes.append(n)
    e = pr[pr.prev != pr.control].groupby(["prev", "control"]).size().rename("n").reset_index()
    edges.append(e[e.n >= 2].rename(columns={"prev": "from", "control": "to"}).assign(page=page))
    ha, hb = grid(p[p.after_T], 3.2), grid(p, 3.2); dd = ha / ha.sum() - hb / hb.sum(); dd = dd / np.abs(dd).max()
    diff.append(long(page, dd, 0.08))
    panel.append({"page": page, "clicks": len(p), "actions": len(a), "repeat_share": round(len(pr[pr.prev == pr.control]) / max(len(pr), 1), 3),
                  "after_T_clicks": int(p.after_T.sum())})
pd.concat(heat).round(3).to_csv(FIGDATA / "aoi_heat.csv", index=False)
pd.concat(diff).round(3).to_csv(FIGDATA / "aoi_diff.csv", index=False)
pd.concat(nodes).round(1).to_csv(FIGDATA / "aoi_nodes.csv", index=False)
pd.concat(edges).to_csv(FIGDATA / "aoi_edges.csv", index=False)
pd.DataFrame(panel).to_csv(FIGDATA / "aoi_panel.csv", index=False)
print(pd.DataFrame(panel).to_string(index=False))
