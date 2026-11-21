# Intent cross-check: Method text vs code (2026-11-21)

Sources: `TKL_manuscript.md` (Method → Data and Event Coding, Data Analysis; Findings) and `ESM_S1.md`, read-only. Code: the consent16 scripts after the refactor (`common.py` holds the shared coding). `independent_check.py` re-implements the headline numbers without importing any analysis code: **all 25 checks match** (Table 1, totals, next-event shares, base rate, KM, primary GEE). `repro/check_numbers.py` checks 171 data-derived numbers: 170 match, and 1 is the profile count below.

| Analysis | Method says | Code does | Match? | Fix |
|---|---|---|---|---|
| Consent filter, logs | Only consenting students; 15 of 16 consent records link to an account | `build_extract.py` keeps the 15 consent account numbers (now read from `data/crosswalk.json`, not hard-coded); every later step reads only `data/*_consented.csv`. Account set in the extract = consent set (verified) | yes | Account numbers moved out of code |
| Consent filter, codes | 45 coded requests | Codes filtered by consent + start date. The test-day exclusion was **not** applied to codes (0 rows affected). All 45 codes match a logged request (same learner, page and UTC minute) | yes (latent gap) | Same window rule as the logs + assertion codes = logged requests |
| Consent filter, survey | 33 responses, 13 learners | Typed login ID → account number → consent set; 33 of 38 rows kept, all on class days | yes | — (a mistyped ID could mislink; not checkable beyond the number) |
| Consent filter, Jev | κ on the 45 requests | Jev log joined via raw row index only for rows whose (user, timestamp) is in the consented codes; asserted n = 45 | yes | — |
| Consent filter, grades | 15 learners linked | P code → account via the 23-account list (now in `crosswalk.json`); inner join with the consented extract; grade file holds exactly the 15 consenters | yes | Assertion added |
| Event codes vs Table 1 | M on module pages, G, P portal, S login/logout, U, R, T | U/B = CHAT USER/BOT; S = CUSTOM_EVENT `auth` (any page, 520 of them on the portal); G = GLOBAL_CLICK (any page, 36 on the portal); P = remaining portal events; M = everything else on module pages (SMART/UI clicks and non-auth custom events). Counts 4,125/798/520/834/45/40/364 | counts yes; P definition loose | Wording only: P is "other non-chat events on the portal page"; portal global clicks count as G and portal logins as S |
| Earlier scheme | 1,354 events reclassified; 404 tutor messages, only 40 replies | 834 S + 520 P were M in the 4-code scheme; B = 404 | yes | — |
| Session definition | "session" (not defined) | Logger `session_id`; one learner per session; start = first event of any code. Sessions can stay open for days (max ≈ 13.8 days); 2 span two course weeks | yes | — |
| Survival 0.1–120 min rule | "kept sessions lasting 0.1 to 120 minutes … 57 of the 72 sessions, including all 15 sessions with a request" | Rule is applied to the **observed time** (to the first request, or to the last event if censored), not to session length. Three request sessions last > 120 min but had their first request within minutes, so they stay in | **wording mismatch** | Code kept (an event time observed within 120 min is valid). Suggested wording: "we kept sessions whose observed time, to the first request or to the last event, was 0.1 to 120 minutes". Under a literal session-length rule the numbers would be 54 sessions, 12 events, median 2.92 (IQR 1.89–4.07), S(5) = .778, S(10) = .669 |
| Time to first request | From session start; censored at last event | t0 = first event; event = first U; censored at last event; T = 0 sessions dropped | yes | — |
| Module × week | Course weeks | Figures: Monday weeks in Mountain time. `reanalysis.py` used UTC ISO weeks; 49 events (0.7%) fall in another week under UTC, request-week counts identical (17/25/3). ESM active days used UTC dates | yes for quoted numbers | One `week_mt()` in `common.py`; active days now Mountain-time dates (changes the 4 active-days ρ, none quoted) |
| Busiest weeks | "Forty-two of the 45 requests fell in the two busiest course weeks" | Weeks of Jan 12 and Jan 26 are busiest by events (Fig 1) and by module sessions (Fig 5); 17 + 25 = 42 | yes | Now computed (was only implicit) |
| Content codes | Table 2: n, %, learners per code; "three learners wrote 30"; "two wrote all 10 frustration" | No script computed the Learners column or the top-3 share (`content_by_profile` was computed instead, which is not reported) | numbers yes, code missing | Table 2 block added to `reanalysis.py` |
| Profiles | Request-rate tertiles × manipulation above/below the median; middle tertile merged; "3 of the 15 learners changing profiles" when the coding was corrected | Tertiles 5/5/5 on U / all events; median split of M / (M + G + P), ≥ median = high (8/7). The change count compared with the **2026-05-04 profiles of 23 learners** (other sample, window and tertile cuts), so it mixed the sample change with the coding change | **mismatch** | Earlier coding (M4 / all events, 2026-05-04 rule) applied to the same 15 learners: **2** of 15 change, not 3. Manuscript not edited |
| Lag-1 transitions | 6,654 within-session transitions | Transitions never cross a session (`sequences()`); 6,726 − 72 = 6,654 | yes | — |
| Reply vs tutor-initiated split | R = right after a request or continuing that reply | `reanalysis.py` used a within-session shift plus the previous label; `sensitivity.py` and the prep scripts a stateful loop. Row-by-row identical: R = 40, T = 364 | yes | One `split_tutor()` in `common.py`; re-implemented in `independent_check.py` |
| Adjusted residuals | Observed vs expected under independence, \|z\| > 1.96 descriptive | z = (O − E)/√(E(1 − r/N)(1 − c/N)) on the pooled table; R→M 2.06, T→M 6.38 | yes | — |
| Base rates | 62.0% "for all next events"; 61.3% "share of all events" (Fig 6) | 62.0% = column share of M among transitions (Fig 7, S1); 61.3% = event share (Fig 6, `base_rate_M` in the LSA table) | yes | Both definitions labelled in code |
| Return curve | Followed by ≥ 1 M within 1–5 events, same session | Source events need a following event (37 R, 361 T); window truncated at session end | yes | — |
| Peri-request windows | ±10 events, same session, no padding | Lags outside the session are skipped; n per lag shrinks | yes | — |
| Before/after first request | Sessions with ≥ 3 non-chat, non-system events on each side | Same; request excluded; M / (M + G + P); Wilcoxon signed-rank | yes | — |
| GEE | Outcome excludes chat and system events; M vs G on module pages; module FE; exchangeable; clusters = learner; bias-reduced SE; one module dropped, 15 learners remain | Same (`C2`); the dropped module has only M events. `reanalysis.py` refitted the same model twice (B2 = B3 = C2) | yes | Duplicate GEE block removed from `reanalysis.py` |
| Specification curve | Eight models, all intervals include 1, all converged | 6 GEE (bias-reduced) + 2 FE logit (cluster SE) | yes | — |
| Survey waves | Three class sessions | Nearest class date to the form timestamp; all consented timestamps fall on the class days | yes | — |
| ESM linkage | Request rate = learner requests per logged event; 24 uncorrected ρ | Same; bootstrap 5,000 resamples, seeded | yes | Seed from one config |
| Seeds | — | Both bootstraps use `default_rng(20261121)`; no other randomness | yes | `SEED` in `run_all.py` |

## Manuscript numbers that would change

| Location | Old | New | Why |
|---|---|---|---|
| Findings, RQ2 ("with 3 of the 15 learners changing profiles") | 3 | 2 | Same-sample comparison (see Profiles row) |

No other reported number changes. The survival row is a wording issue only, unless the owner prefers the literal session-length rule.
