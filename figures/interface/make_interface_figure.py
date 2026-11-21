"""Figure 1 (GenAI tutor interface): crops of local data-period build screenshots (commit eb29e0e, local screenshot
account, no database) with numbered callouts. 174 mm wide; PDF + 600 dpi PNG/TIFF."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import rcParams
from PIL import Image
HERE = Path(__file__).parent; OUT = HERE.parent / "out"
rcParams["font.family"] = "Arial"; rcParams["pdf.fonttype"] = 42
INK = "#1F2430"; ACC = "#D4A24C"
S = 2  # capture scale (CSS px -> image px)
# panel: file, crop (CSS px: x0, y0, x1, y1), callouts [(n, target_x, target_y, label_x, label_y)] in CSS px
P = {  # A: module in use; B: illustrative request-reply (scripted pair injected locally, no API call); C: scripted message; D: portal
 "A": ("A_galton_2x.png", (155, 72, 1320, 795), [(1, 455, 520, 260, 600), (2, 378, 745, 300, 745), (3, 985, 212, 985, 150),
                                                 (4, 1245, 322, 1288, 322), (5, 1110, 726, 1110, 672)]),
 "B": ("D_request_reply_2x.png", (905, 180, 1318, 795), [(6, 1016, 420, 932, 420), (7, 967, 550, 932, 550)]),
 "C": ("B_coin_2x.png", (155, 72, 1320, 905), [(2, 370, 567, 315, 567), (8, 968, 585, 933, 585), (9, 212, 703, 178, 703),
                                               (10, 740, 855, 790, 815)]),
 "D": ("C_portal_2x.png", (155, 200, 1320, 916), [(11, 541, 470, 553, 470)]),
}
def panel(ax, key):
    f, (x0, y0, x1, y1), calls = P[key]
    im = Image.open(HERE / f).crop((x0 * S, y0 * S, x1 * S, y1 * S))
    ax.imshow(im, extent=(x0, x1, y1, y0)); ax.set_xlim(x0, x1); ax.set_ylim(y1, y0); ax.axis("off")
    for n, tx, ty, lx, ly in calls:
        ax.annotate("", xy=(tx, ty), xytext=(lx, ly), arrowprops=dict(arrowstyle="-", color="white", lw=1.6, shrinkA=0, shrinkB=0))
        ax.annotate("", xy=(tx, ty), xytext=(lx, ly), arrowprops=dict(arrowstyle="-", color=INK, lw=0.6, shrinkA=0, shrinkB=0))
        ax.plot(tx, ty, "o", ms=2.2, color=ACC, mec=INK, mew=0.4)
        ax.text(lx, ly, str(n), ha="center", va="center", fontsize=6.5, fontweight="bold", color=INK,
                bbox=dict(boxstyle="circle,pad=0.25", fc="white", ec=INK, lw=0.6))
    ax.text(0.0, 1.015, key, transform=ax.transAxes, fontsize=9, fontweight="bold", color=INK, va="bottom")
W = 174 / 25.4; H = 150 / 25.4
fig = plt.figure(figsize=(W, H))
axA = fig.add_axes([0.0, 0.445, 0.685, 0.525]); panel(axA, "A")
axB = fig.add_axes([0.70, 0.445, 0.30, 0.525]); panel(axB, "B")
axC = fig.add_axes([0.0, 0.0, 0.495, 0.405]); panel(axC, "C")
axD = fig.add_axes([0.505, 0.0, 0.495, 0.405]); panel(axD, "D")
for ext, kw in (("pdf", {}), ("png", {"dpi": 600}), ("tiff", {"dpi": 600, "pil_kwargs": {"compression": "tiff_lzw"}})):
    fig.savefig(OUT / f"Figure2_genai_tutor_interface.{ext}", facecolor="white", **kw)
print("saved")
