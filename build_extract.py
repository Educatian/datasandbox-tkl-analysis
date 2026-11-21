"""Consent filter + course-window filter. Runs first; every later step reads only its outputs in data/.

Unit: event (logs), coded request (codes), survey response. Consent = gradebook Research Consent = Yes, linked by the
account-number crosswalk between the gradebook and the log accounts; 15 of 16 consent-Yes records
link to telemetry (Method, Setting and Participants). The account numbers live in data/crosswalk.json, not in code.
Window: from the first in-class use (Wed 2026-01-14, Mountain time) onward, minus the documented team test of one
assigned account on 2026-02-18 (emails document pre-launch testing on Jan 8 and 12 too, removed by the start date).
Inputs : RAW_LOGS, RAW_CODES, data/survey_raw.csv. Outputs: data/user_logs_consented.csv (6,726 events),
data/manual_chat_codes_consented.csv (45 coded requests), data/survey_consented.csv (33 responses). Raw rows stay in data/.
"""
import pandas as pd
from common import DATA, RAW_CODES, RAW_LOGS, TZ, crosswalk, suffix

cw = crosswalk(); CONSENT = set(cw["consent_suffixes"]); start = pd.Timestamp(cw["window_start"]).date()
local_date = lambda ts: pd.to_datetime(ts, utc=True, format="ISO8601").dt.tz_convert(TZ).dt.date

d = pd.read_csv(RAW_LOGS); s = d.user_id.map(suffix); day = local_date(d.timestamp)
win = (day >= start) & ~((s == cw["test_account_suffix"]) & (day == pd.Timestamp(cw["test_day"]).date()))
print("dropped pre-launch/testing events among consenters:", int((s.isin(CONSENT) & ~win).sum()))
k = d[s.isin(CONSENT) & win]
k.to_csv(DATA / "user_logs_consented.csv", index=False)

# Codes: same consent + window rule (no coded request falls on the test day; asserted so a new extract cannot leak one).
codes = pd.read_csv(RAW_CODES); cs = codes.user.map(suffix); cday = local_date(codes.timestamp)
ckeep = cs.isin(CONSENT) & (cday >= start) & ~((cs == cw["test_account_suffix"]) & (cday == pd.Timestamp(cw["test_day"]).date()))
codes[ckeep].to_csv(DATA / "manual_chat_codes_consented.csv", index=False)
n_req = int((k.click_type.eq("CHAT") & k.target_tag.eq("USER")).sum())
assert int(ckeep.sum()) == n_req, ("coded requests != logged requests", int(ckeep.sum()), n_req)

# Survey: typed login ID -> account number; consenters only (no date window: forms were only open on class days).
sv = pd.read_csv(DATA / "survey_raw.csv"); idc = next(c for c in sv.columns if "ID" in c)
sv["_s"] = sv[idc].map(suffix)
sv[sv._s.isin(CONSENT)].to_csv(DATA / "survey_consented.csv", index=False)
print("learners", k.user_id.nunique(), "events", len(k), "sessions", k.session_id.nunique(), "requests", n_req,
      "coded", int(ckeep.sum()), "survey rows", int(sv._s.isin(CONSENT).sum()), "of", len(sv),
      "survey learners", sv.loc[sv._s.isin(CONSENT), "_s"].nunique())
