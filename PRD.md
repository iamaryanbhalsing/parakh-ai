# PRD — Parakh (परख) AI: UPI Fraud Intervention Engine

**Version:** 1.0 · **Status:** Prototype (synthetic/simulated data) · **Owner:** Parakh AI Team

---

## 1. Problem Statement & Keyword Analysis

> Interrupt genuinely high-risk transactions while minimizing unnecessary blocks on legitimate payments.
> Fraudsters impersonate bank employees, police, employers, merchants, or relatives and pressure users
> into approving UPI payments during phone/video calls, using voice cloning, screen sharing, urgency, and
> newly added beneficiaries.

**Keyword clusters → system modules:**

| Cluster | Module |
|---|---|
| Impersonation actors (bank/police/relative) | Urgency NLP, warnings, coaching banner |
| Call / screen-share context | Call-context signals (phone/video/screen-share/unknown caller) |
| Voice cloning | Voice-clone indicator with confidence bands |
| Urgency | Conversational pressure detection (EN + HI) |
| New/unusual beneficiaries | Beneficiary-recently-added & history signals |
| Adaptive holds / proportionate steps | Tiers → hold / verify / cooling-off / block |
| Explainability | Feature breakdown + human-readable "why" |
| Evidence preservation | SHA-256 hash-chained tamper-evident evidence log |
| Bank alerts | HMAC-signed secure alerts to institution |
| False-positive monitoring | User feedback labels → FP-rate stats |

## 2. Goals & KPIs

**North-star:** *Interrupt fraud before authorization; never sandbag a legitimate payment.*

| KPI | Target |
|---|---|
| Fraud capture rate (high+critical) | ≥ 90% of synthetic scam scenarios interrupted pre-authorization |
| False-positive rate (legit held) | ≤ 5% of legitimate payments |
| Decision latency (p95) | < 100 ms (prototype: sub-ms on rules) |
| Explainability | 100% of decisions include feature breakdown + reasons |
| Evidence integrity | 100% of chains verify (tamper = 0) |

## 3. Personas

- **Suresh (54, semi-retired)** — target of "digital arrest" / bank-scam calls; a new beneficiary + urgent
  video call within 60 s is the fraud pattern. Needs warnings he understands and one-tap verification.
- **Priya (28, frequent UPI user)** — pays rent, bills, friends daily; must not be friction-blocked.
  Needs fast allow-path with a lightweight coaching banner at most.
- **Bank Fraud-Ops Analyst** — needs a queue, alert log, FP monitoring, evidence access, and operator
  override with audit trail.
- **Vulnerable User (elderly / flagged)** — gets **Trusted-Contact Circuit Breaker** and **Cooling-Off
  Wallet** instead of a flat block.

## 4. User Journeys

1. **Scam attempted** — Suresh gets a "digital arrest" video call; scammer shares a payment link. Engine
   scores CRITICAL → hold + multilingual warning + bank alert + evidence; Suresh calls trusted contact →
   cancels. Funds safe.
2. **Legit payment** — Priya pays rent (known beneficiary, normal amount, no call). Engine scores Low →
   instant allow, no friction.
3. **Legit-but-unusual** — Priya pays a big bill at 2 AM from a new phone. Engine scores Medium/High →
   coaching banner (not a block) + optional OTP verification; she completes it and gives feedback
   "false_positive", feeding FP stats.
4. **Hard-block edge** — Extreme case (95+): cooling-off wallet + trusted-contact circuit breaker + bank
   alert; ops override possible with audit.

## 5. Functional Requirements

| ID | Requirement |
|---|---|
| FR-1 | Score every payment request in real time from 8 fused signals with per-feature breakdown |
| FR-2 | Detect new/unusual beneficiaries (recently added, no history) |
| FR-3 | Detect amount deviation vs. 30-day pattern and balance-drain risk |
| FR-4 | Consume call context: phone/video call active or ended ≤ 60 s, screen-sharing, unknown caller |
| FR-5 | Consume device-context signals: device change, rooted/emulator, location change, session count |
| FR-6 | Consume conversational-urgency text (EN + Hindi) and return matched terms + score |
| FR-7 | Consume voice-clone acoustic probability → confidence band (never a fake binary verdict) |
| FR-8 | Map score to tiers and insert proportionate steps: allow → coach → verify/OTP → hold → cooling-off → block |
| FR-9 | Show understandable multilingual warnings and explanations (EN / हिंदी / मराठी) |
| FR-10 | Preserve evidence in a tamper-evident hash chain; support verification endpoint |
| FR-11 | Notify institution via secure (HMAC-signed, simulated) alert channel for high+ risk |
| FR-12 | Collect user feedback & ops overrides; compute false-positive statistics |
| FR-13 | Trusted-Contact Circuit Breaker for vulnerable users (release only after trust-circle call) |
| FR-14 | Bank-configurable policy: thresholds, holds, alert levels, voice cap via API without redeploy |

## 6. Non-Functional Requirements

| ID | NFR |
|---|---|
| NFR-1 | Latency: score decision p95 < 100 ms; single-digit ms prototype |
| NFR-2 | Availability: 99.9% (prototype: stateless scoring, restartable stores) |
| NFR-3 | Privacy-by-default: call/voice data consent-gated, transient (feature vectors only), minimal retention, no raw audio stored |
| NFR-4 | Security: HMAC-signed external alerts; evidence chain tamper-resistant |
| NFR-5 | Explainability: every decision exposes contributions + reasons (auditable) |
| NFR-6 | Configurability: policy adjustable per institution at runtime; no redeploy for threshold tuning |
| NFR-7 | Auditability: overrides & feedback appended to evidence chain with actor metadata |
| NFR-8 | Testability: deterministic rules + synthetic dataset enable offline evaluation (precision/recall/FP/latency) |

## 7. Architecture

```
user payment request
      │
      ▼
┌───────────────────────── forwarder/consent gate ─────────────────────────┐
│                                                                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐ ┌─────────────┐  │
│  │ txn context  │ │ call context │ │ device context   │ │ voice model │  │
│  │ (amount, ben)│ │ (call, share)│ │ (device, loc)    │ │ (bands)     │  │
│  └──────┬───────┘ └──────┬───────┘ └────────┬─────────┘ └──────┬──────┘  │
│         └────────────────┴──────────┬───────┴──────────────────┘         │
│                         ┌───────────▼───────────┐                        │
│                         │  Risk Engine (8 fuses, │                        │
│                         │   explainable weights) │                        │
│                         └───────────┬───────────┘                        │
│                                     ▼                                    │
│                          ┌─────────────────────┐                         │
│                          │ Policy / Decision   │ tiers → proportionate   │
│                          │ (per-bank config)   │ steps                   │
│                          └─────────┬───────────┘                         │
│                                    ▼                                     │
│              ┌────────────┬────────┴───────┬──────────────┐               │
│              ▼            ▼                ▼              ▼               │
│        warnings      verification     holds/         evidence            │
│        (EN/HI/MR)    (OTP/trusted)   cooling-off      chain              │
│                                        /block          + bank alert      │
└──────────────────────────────────────────────────────────────────────────┘
```

## 8. Data / Model Plan

- **Data:** synthetic generator (`synthetic_data.py`) producing scam / legit / legit-but-unusual scenarios
  for offline eval; simulated at runtime for the demo UI.
- **Rules + light ML:** deterministic weighted rules first (prototype), with the voice model treated as an
  external/streaming provider (acoustic features → probability + confidence).
- **Voice-clone indicator:** confidence bands (low / uncertain / medium / high) — never a binary verdict —
  to avoid overclaiming; bands factored into decision only above a configurable cap.
- **Evaluation plan:** offline harness measures precision, recall, F1, FP rate, latency on N scenarios and
  seeds; feedback loop for FP monitoring drives threshold tuning per bank.

## 9. Impactful Features (beyond the base ask)

1. **Trusted-Contact Circuit Breaker** — hard-release only after a trusted-contact callback for flagged users.
2. **Cooling-Off Wallet** — proportionate alternative to a flat hard block (release on review/accept).
3. **Real-Time Coaching Banner** — lightweight nudge fired *before* full intervention when pressure detected.
4. **Post-Incident Reporting Assistant** — pre-filled cybercrime complaint from preserved evidence chain.
5. **Voice-clone confidence bands** — honest uncertainty instead of overclaiming.
6. **Bank-configurable policy engine** — per-institution thresholds without redeployment.

## 10. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| False positives annoy users | Coaching banner first; optional verification; FP monitoring + per-bank tuning |
| Voice-clone false alarms | Confidence bands; voice risk weight cap; no hard action solely from voice |
| Privacy / consent issues | Consent-gated, transient processing, no raw audio retention, minimal scope |
| Missing context (no call data) | Engine degrades gracefully; pure-call scams still caught by amount/beneficiary/urgency |
| Telecommunication/legal approval | Production scope explicitly excludes real audio surveillance until RBI/NPCI-approved |

## 11. Out of Scope (prototype)

- Real NPCI/UPI integration, real money movement, RBI/NPCI certification
- Real audio recording/telephony interception (simulated flags + acoustic features only)
- Multi-institution deployment tooling (config-only per-bank policy)