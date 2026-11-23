"""Second-coder (Jev) agreement on the consented, in-window requests (Method, Data and Event Coding: 91.1%,
kappa = .88 [.76, .97]). Reuses the existing blind Jev codes (2026-11-20 run; row index into the raw
manual_chat_codes.csv); no new coding run, no API call. Aggregates only.
Run: python -X utf8 jev_agreement_consent16.py
"""
import numpy as np, pandas as pd
from common import CODE_ADJ, DATA, JEV_LOG, RAW_CODES, RESULTS, SEED, dump

# Unit: coded request. Raw row index -> keep rows whose (user, timestamp) is in the consented codes file, so the Jev
# rows of non-consenters never enter the merge; asserted to cover all 45 consented requests.
d = pd.read_csv(RAW_CODES); keep = pd.read_csv(DATA / "manual_chat_codes_consented.csv")
key = lambda f: f.user.astype(str) + "|" + f.timestamp.astype(str)
d["row"] = range(len(d)); d = d[key(d).isin(set(key(keep)))]
m = pd.read_csv(JEV_LOG).merge(d[["row", "code"]], on="row")
assert len(m) == len(keep), (len(m), len(keep))
labels = sorted(set(m.code) | set(m.jev_code))

def kappa(a, b):
    po = (a == b).mean(); pe = sum((a == l).mean() * (b == l).mean() for l in labels); return (po - pe) / (1 - pe), po

# Cohen's kappa; percentile bootstrap CI over 5,000 message resamples, seeded from default_rng(SEED).
k, po = kappa(m.code.values, m.jev_code.values)
rng = np.random.default_rng(SEED); boot = []
for _ in range(5000):
    s = m.sample(len(m), replace=True, random_state=rng.integers(1 << 31)); boot.append(kappa(s.code.values, s.jev_code.values)[0])
lo, hi = np.nanpercentile(boot, [2.5, 97.5])
res = {"n": len(m), "kappa": round(k, 3), "ci": [round(lo, 3), round(hi, 3)], "agreement": round(po, 3),
       "disagreements": int((m.code != m.jev_code).sum()), "first_coder_counts": m.code.value_counts().to_dict()}
# Expert verification (audit, not independent reliability: the first author saw the proposed code) and Jev vs final codes.
f = m.merge(pd.read_csv(CODE_ADJ)[["row", "final_code"]].rename(columns={"final_code": "final"}), on="row", validate="one_to_one")
assert len(f) == len(m) and sorted(f.final) == sorted(keep.code)   # same final codes build_extract applied
kf, pof = kappa(f.final.values, f.jev_code.values)
res["verification"] = {"kept": int((f.code == f.final).sum()), "changed": int((f.code != f.final).sum()),
                       "kept_share": round((f.code == f.final).mean(), 3),
                       "changes": f[f.code != f.final].groupby(["code", "final"]).size().rename("n").reset_index().to_dict("records"),
                       "changed_to_jev_code": int(((f.code != f.final) & (f.final == f.jev_code)).sum()),
                       "jev_vs_final": {"kappa": round(kf, 3), "agreement": round(pof, 3)}}
dump(res, RESULTS / "jev_agreement_consent16.json"); print(res)
