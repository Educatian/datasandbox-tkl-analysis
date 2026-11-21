# Data schema

Participant data are not distributed. The pipeline reads the files below.

## Raw inputs (outside the package; paths in `run_all.py` → `RAW`)

| File | Unit | Columns used |
|---|---|---|
| `user_logs_participants.csv` | logged event | `user_id` (account e-mail, `…N@…`), `timestamp` (ISO 8601, UTC), `session_id` (logger session), `page` (module slug or `portal`), `click_type` (`CHAT`, `CUSTOM_EVENT`, `GLOBAL_CLICK`, `SMART_CLICK`, `UI_CLICK`), `target_tag` (`USER`/`BOT` for chat, `auth` for login/logout, else the HTML tag), `target_id` (element id; keyword rates in the ESM) |
| `manual_chat_codes.csv` | learner request | `user`, `timestamp` (UTC, minute resolution), `page`, `code` (primary content code), `subcode`, `message` (chat text, never leaves `data/`) |
| `provisional_crosswalk_analysis_pseudonymized.csv` | learner | `participant` (`Pk` = k-th account number in `log_account_suffixes`), `Current Score`, `Final Score`, `Exams Final Score`, `Assignments Final Score` |
| `jev_second_coder_log.csv` | learner request | `row` (0-based row index into `manual_chat_codes.csv`), `jev_code` (AI second coder, blind to everything but the text) |

## Local files in `data/` (gitignored)

| File | Written by | Content |
|---|---|---|
| `crosswalk.json` | owner (by hand) | `consent_suffixes` (account numbers with Research Consent = Yes), `log_account_suffixes` (the 23 logged accounts, in P-code order), `test_account_suffix` + `test_day` (documented team test, dropped), `window_start` (first class session, Mountain time) |
| `survey_raw.csv` | form export | `Timestamp`, `Date`, login-ID column (name contains `ID`), three 5-point items (columns 4–6), comment (column 7) |
| `user_logs_consented.csv`, `manual_chat_codes_consented.csv`, `survey_consented.csv` | `build_extract.py` | consent- and window-filtered copies of the inputs (survey adds `_s`, the account number) |
| `survey_comments_LOCAL.csv` | `survey.py` | comments by wave; local only |

## Derived, shareable outputs

`results/` and `figures/data/` hold aggregates only: counts, rates, model estimates, minutes since session start, anonymized learner codes P01–P15, and Mountain-time course weeks (Monday dates). No learner IDs, e-mails, chat text or clock times.
