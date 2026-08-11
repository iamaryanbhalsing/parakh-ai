# Parakh (परख) AI — Real-Time UPI Fraud-Intervention Engine

An explainable, real-time fraud-intervention engine that detects and interrupts impersonation-driven UPI fraud
(digital arrest, bank-employee scams, courier/drugs, lottery, relative-emergency voice-clone scams) **before
authorization**, while minimizing unnecessary blocks on legitimate payments.

Built as a **fully working end-to-end prototype**: FastAPI backend + browser payment simulator + fraud-ops
dashboard + AI call-conversation analysis (live listen / upload / transcript → final opinion) + offline
evaluation harness + 30 passing unit tests. All data is synthetic/simulated — this is a
prototype design, not a production system.

---

## Quick Start

```bash
# 1. enter backend
cd backend

# 2. install dependencies (Python 3.10+)
pip install -r requirements.txt

# 3. run tests (optional but recommended)
pytest -q

# 4. start the server
uvicorn app.main:app --reload --port 8000
```

Open in your browser:

| Page | URL |
|---|---|
| Payment simulator (the main demo) | http://localhost:8000/static/index.html |
| Fraud-ops dashboard | http://localhost:8000/static/dashboard.html |
| Interactive API docs (Swagger) | http://localhost:8000/docs |

---

## One-Minute Demo

1. On the **Payment Simulator**, the `Digital Arrest` scam preset is pre-loaded — press **Run Risk Score**.
2. The engine returns a **CRITICAL (100/100)** explainable score: the payment is held, a multilingual
   warning banner (EN / हिंदी / मराठी) appears, evidence is captured into a tamper-evident chain, and an
   HMAC-signed bank alert fires.
3. Choose an action: **Verify (OTP)**, **Accept Cooling-Off Hold**, or **Cancel Payment** — then check the
   **Ops Dashboard** to see the intervention queue, bank alert log with signatures, evidence-chain status,
   and feedback.
4. Try the `Rent (legit)` preset to see a normal transaction pass without intervention (low false-positive
   behavior).

---

## How It Works

### Risk scoring (explainable, weighted fusion)

`POST /api/score` runs eight combined signals through a weighted fusion model, each returning
`(value, weight, contribution, reason)`:

| Signal | Weight | What it catches |
|---|---|---|
| New/unusual beneficiary | 0.14 | Beneficiary added within hours/days, no prior history |
| Amount deviation | 0.18 | Amount far above the user's 30-day pattern |
| Balance drain | 0.12 | Payment would leave < 20% of the account |
| Call + screen-share composite | 0.20 | Active audio/video call, screen sharing, unknown caller |
| Device change | 0.08 | New device, rooted/emulator, radical location change |
| Velocity | 0.10 | Burst of payments in the last hour |
| Conversational urgency | 0.10 | Coercion keywords in EN + हिंदी (OTP/PIN pressuring, arrest threats, secrecy demands) |
| Voice-clone indicator | 0.25 | Acoustic deepfake probability, model confidence, sample duration |

Score → tier (Low / Medium / High / Critical) → **proportionate intervention**:

| Tier | Action |
|---|---|
| Low / Medium | Allow; optional warning/coaching banner for mild pressure cues |
| High | **Adaptive hold (2 h)** + independent OTP verification before release |
| Critical (85–94) | **Hold 24 h**, independent verification + bank alert |
| Critical (95+) | **Cooling-off wallet / hard block** + trusted-contact circuit breaker + bank alert |

The engine never overclaims: voice cloning is reported as a **confidence band**
(low / uncertain / medium / high), not a binary "is cloned / isn't cloned".

### AI Call Intelligence (conversation NLP)

`POST /api/conversation/analyze` runs a lightweight multilingual NLP pipeline over a call transcript
(English + हिंदी) and issues a **final opinion** on the conversation:

- **Turn-level cue detection** — pressure, secrecy ("don't tell anyone"), authority claims (police/court/
  RBI/cyber cell), credential requests (OTP/PIN), payment demands, prize/reward offers, relative
  emergencies, courier/parcel stories, fear-inducing threats.
- **Entity extraction** — amounts (₹, lakh/crore, plain), OTP codes, phone numbers, institutions.
- **Per-speaker sentiment** — caller vs. victim stress/confidence profile.
- **Scam-intent classification** — authority impersonation, bank impersonation, lottery/prize fraud,
  relative-emergency (voice-clone) fraud, courier/parcel fraud, or legitimate — with a match score.
- **Fraud score + final opinion** — `FRAUD / SUSPICIOUS / LEGITIMATE / INCONCLUSIVE` with confidence %,
  red flags, detected scam patterns, and a suggested action (block / verify / allow).

Three ways to feed it a conversation:

| Mode | How |
|---|---|
| **Live Listen** | Browser microphone → Web Speech API (Chrome/Edge) → transcript streamed turn-by-turn with a live verdict. The simulated call is analyzed automatically this way. |
| **Upload Recording** | `POST /api/call/upload` stores the audio (wav/mp3/webm/ogg); attach a transcript, or play the file near the mic under Live Listen to transcribe it. |
| **Transcript paste** | Paste any dialogue (`Caller: … / Victim: …`) or raw text; sample transcripts included. |

The opinion can be applied into risk scoring (`Use Conversation in Risk Scoring`), feeding the
engine's conversational-urgency signal with the actual call text.

### Extra safety features (beyond the base ask)

- **Trusted-Contact Circuit Breaker** — a call to a pre-registered trust circle before a hard block is lifted.
- **Cooling-Off Wallet** — instead of a flat hard block, critical-but-not-extreme cases go to a review
  wallet that releases after review or explicit acceptance.
- **Real-Time Coaching Banner** — a lightweight nudge fires *before* a hard intervention when conversation
  pressure is detected (e.g. "verify you are not sharing your screen").
- **Post-Incident Reporting Assistant** — evidence chain + full feature snapshot ready to pre-fill a
  cybercrime complaint (exportable via `/api/evidence/{txn_id}`).
- **Bank-configurable policy engine** — thresholds, hold durations, alert levels and voice-risk cap are
  tunable per institution via `POST /api/policy` (no redeployment).

### Evidence preservation (tamper-evident)

Every intervention/override/feedback event is appended to a **SHA-256 hash chain**
(`data/evidence_chain.json`). Verify integrity anytime: `GET /api/evidence/chain/verify`.

### Bank alerts (secure channel)

Simulated secure alerts to the institution are **HMAC-SHA256 signed**
(`data/bank_alert.py`) and logged with signatures; the dashboard shows a VALID / TAMPERED status.

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app: /api/score, proceed, cancel, override, feedback,
│   │                        #   evidence, alerts, transactions, stats, urgency, voice,
│   │                        #   conversation/analyze, call/upload, policy
│   ├── schemas.py           # Pydantic request/response models
│   ├── config.py            # default policy, multilingual messages (EN/HI/MR), policy I/O
│   ├── risk_engine.py       # explainable weighted risk-fusion engine (8 signals)
│   ├── nlp_urgency.py       # multilingual (EN + HI) coercion/urgency keyword detector
│   ├── conversation_analysis.py  # AI call analysis: cues, entities, sentiment, intent,
│   │                            #   final opinion (EN + HI) + analysis/recording store
│   ├── voice_analysis.py    # voice-clone indicator with confidence bands
│   ├── evidence_store.py    # SHA-256 hash-chained tamper-evident evidence log
│   ├── bank_alert.py        # HMAC-signed simulated secure bank alert
│   ├── transaction_store.py # stateful store for holds/overrides/feedback/stats
│   ├── synthetic_data.py    # scam/legit scenario dataset generator
│   └── static/              # frontend (see below)
├── evaluate.py              # offline evaluation harness (precision/recall/F1/FP rate/latency)
├── tests/                   # 30 unit tests
├── requirements.txt
└── data/                    # runtime artifacts (gitignored): transactions, evidence chain,
                             #   call analyses, uploaded recordings, policy
```

### Frontend (plain HTML/JS/CSS, no build step)

- `static/index.html` — **payment simulator** built as a realistic mobile-banking experience:
  - a **phone-frame UPI app** that plays out 8 attack scenarios (digital arrest, bank impersonation,
    courier/drugs, lottery, relative-emergency voice clone, plus legit rent/bill/family);
  - a **simulated incoming-call overlay** (caller card, live timer, screen-share / unknown-caller /
    video badges, mute & end buttons);
  - a **live conversation transcript** with typing animation and a real-time conversational-pressure
    meter fed by the urgency API;
  - a **voice-clone panel** with an animated waveform and confidence-band verdict (never a fake binary);
  - an animated **risk gauge**, per-feature contribution bars, and an **SVG radar profile** of all 8 signals;
  - a **verification flow** with a 6-digit OTP pad and a **Trusted-Contact Circuit Breaker**
    (call mother / brother / fraud desk to release);
  - multilingual warning banners (EN / हिंदी / मराठी), cooling-off wallet release, cancel path,
    a hash-chained **evidence viewer**, the HMAC-signed **bank alert** receipt, and a
    **post-incident report assistant** that drafts a 1930-ready cybercrime complaint from preserved evidence;
  - an **AI Call Intelligence** panel with three tabs:
    - **Live Listen** — microphone → Web Speech API → turn-by-turn NLP with a live verdict pill,
      confidence, and pressure meter while the call plays (the simulated call is analyzed automatically);
    - **Upload Recording** — send a wav/mp3/webm/ogg call recording, optionally with a transcript;
    - **Transcript** — paste or load a sample dialogue and run the full NLP analysis;
    - the analysis renders the **final opinion** (FRAUD / SUSPICIOUS / LEGITIMATE / INCONCLUSIVE),
      fraud-score bar, intent, red flags, extracted entities (amounts/OTPs/phones/institutions),
      per-turn cue tags and speaker sentiment — and can be **applied into risk scoring**.
- `static/dashboard.html` — **fraud-ops dashboard**:
  - KPI cards with sparklines, risk-distribution **donut**, score **timeline** with the intervention line;
  - expandable intervention queue with per-transaction context; bank alert log with live
    HMAC **signature verification** (VALID / TAMPERED);
  - evidence-chain status + latest ledger entries; false-positive feedback table;
  - **AI call analyses** table (verdict, confidence, fraud score, intent, source) and
    **uploaded recordings** ledger;
  - a **policy engine panel** to tune thresholds, holds and synergy bonuses live via
    `POST /api/policy` (persisted, no redeploy);
  - a **live demo stream** that auto-generates synthetic scam/legit traffic every ~3 s
    to demo real-time queue behavior. Auto-refreshes every 4 s.

---

## Evaluation

```bash
cd backend
python evaluate.py 250 42        # n scenarios, seed
```

Runs the full engine offline over synthetic scam/legit/legit-but-unusual scenarios and reports
precision, recall, F1, false-positive rate, and latency:

```text
n_scenarios: 250        (500 on seed 7)
precision: 1.0          (1.0)
recall:    1.0          (0.976)
f1:        1.0          (0.988)
false_positive_rate: 0.0
avg_latency_ms: < 0.1 ms
```

> **Honest caveat:** these numbers come from clean synthetic archetypes and a deterministic rule engine.
> They demonstrate that the *plumbing* — scoring, decisioning, evaluation — works. They are **not**
> a claim about real-world performance, where precision/recall must come from data collected in production
> or high-fidelity simulation.

---

## API Reference (core endpoints)

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/score` | Score a transaction → risk tier, decision, explanation, evidence, bank alert |
| POST | `/api/proceed` | Release a held payment after verification (otp / trusted_contact / cooling_off_accept) |
| POST | `/api/cancel` | User cancels the held payment |
| POST | `/api/override` | Operator override with reason (audited + evidence-logged) |
| POST | `/api/feedback` | User rating/label (fraud / false_positive / unclear) — feeds FP monitoring |
| GET | `/api/evidence/{txn_id}` | Full evidence chain for a transaction (reporting assistant) |
| GET | `/api/evidence/latest?n=5` | Latest evidence-chain entries (dashboard ledger) |
| GET | `/api/evidence/chain/verify` | Tamper-evidence check for the whole chain |
| GET | `/api/alerts` | Bank alert log with HMAC signatures |
| GET | `/api/stats` | Dashboard statistics incl. false-positive rate |
| GET/POST | `/api/policy` | Read / tune bank-configurable thresholds without redeployment |
| POST | `/api/conversation/analyze` | NLP analysis of a call transcript → cues, entities, sentiment, intent, **final opinion** |
| GET | `/api/conversation/recent?n=10` | Recent AI call analyses (dashboard) |
| POST | `/api/call/upload` | Upload a recording (multipart audio + optional transcript) → stored + analyzed |
| GET | `/api/call/recordings?n=10` | Uploaded-recording ledger |

---

## What's Real vs. Simulated (productionization notes)

| Component | In this prototype | In production |
|---|---|---|
| Transaction data | Synthetic scenarios | NPCI UPI event streams, bank core systems |
| Call / screen-share context | Simulated flags | Device-level SDK with **explicit consent** (Telecom / TRAI & app-permission context) |
| Voice cloning | Simulated acoustic probability input | Real deepfake model streaming features; needs RBI/NPCI + legal approval, **transient processing, no raw audio retention** |
| Conversational urgency | Keyword rules EN/HI | LLM/NLU + speech-transcript pipeline, multilingual |
| Bank alerts | HMAC-signed simulation | NPCI/ISO 20022 secure channels, mTLS |
| Policy engine | JSON config | Centralized registrar, per-institution tuning UI + A/B |

**Explicitly out of scope (flagged in the PRD):** production RBI/NPCI certification, real audio surveillance,
and real-money movement. This prototype simulates all external integrations.

**Privacy-by-default:** call/voice handling is consent-gated, audio is processed transiently (feature
vectors only — never raw recordings stored), and retention is minimal. The engine's non-functional
requirements mandate this (see `PRD.md` §NFRs).

---

## Tests

```bash
cd backend
pytest -q          # 30 tests, all passing
```

Covers: risk-engine tiers & weights, balance-drain flags, voice-risk contribution, urgency detection
(EN + HI), voice confidence bands, evidence-chain integrity & tamper detection, HMAC signature
verification, full API flows (score → proceed → feedback → evidence → chain verify), and the AI
conversation analyzer (scam transcripts → FRAUD opinions, legit → LEGITIMATE, Hindi relative-emergency,
entity extraction, speaker parsing, short-transcript inconclusive).

---

## License / Disclaimer

Prototype for hackathon/evaluation use with synthetic data. Not affiliated with NPCI/RBI. Do not use
with real payments without certification.