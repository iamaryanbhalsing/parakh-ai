(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);

  const API_BASE = (window.PARAKH_API_BASE || "").replace(/\/+$/, "");

  async function api(path, options = {}) {
    const res = await fetch(API_BASE + path, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail || "Request failed: " + res.status);
    }
    return res.json();
  }

  function toast(msg, ok = true) {
    const t = $("toast");
    t.textContent = msg;
    t.className = "toast show " + (ok ? "ok" : "err");
    setTimeout(() => t.classList.remove("show"), 3200);
  }

  const pill = (lvl) => `<span class="pill ${lvl}">${lvl}</span>`;

  const STATUS_MAP = {
    held: "held", processed: "processed", overridden: "overridden",
    cancelled: "cancelled", blocked: "blocked", false_positive: "false_positive",
  };
  const statusPill = (st) => `<span class="pill ${STATUS_MAP[st] || "processed"}">${(st || "").replace(/_/g, " ")}</span>`;

  /* ---------- sparkline ---------- */
  function spark(el, values, color) {
    if (!values || values.length < 2) return;
    const w = 110, h = 34;
    const max = Math.max(...values, 1);
    const pts = values.map((v, i) => `${(i / (values.length - 1)) * w},${h - (v / max) * (h - 4) - 2}`).join(" ");
    el.innerHTML = `<polyline points="${pts}" fill="none" stroke="${color}" stroke-width="1.8" opacity="0.85"/>
      <circle cx="${w}" cy="${h - (values[values.length - 1] / max) * (h - 4) - 2}" r="2.4" fill="${color}"/>`;
  }

  /* ---------- KPI history (session-local accumulation) ---------- */
  const history = { total: [], held: [], critical: [], fp: [] };

  /* ---------- donut ---------- */
  function drawDonut(dist) {
    const svg = $("donut");
    const total = Object.values(dist).reduce((a, b) => a + b, 0);
    if (!total) {
      svg.innerHTML = '<text x="75" y="80" text-anchor="middle" fill="#6b7398" font-size="13">no data</text>';
      $("donutLegend").innerHTML = "";
      return;
    }
    const cols = { low: "#34d399", medium: "#fbbf24", high: "#fb923c", critical: "#f87171" };
    const names = { low: "Low", medium: "Medium", high: "High", critical: "Critical" };
    let offset = 0;
    let inner = "";
    let legend = "";
    const C = 2 * Math.PI * 60;
    Object.keys(cols).forEach(k => {
      const v = dist[k] || 0;
      if (!v) return;
      const frac = v / total;
      inner += `<circle cx="75" cy="75" r="60" fill="none" stroke="${cols[k]}" stroke-width="17"
        stroke-dasharray="${frac * C} ${C}" stroke-dashoffset="${-offset * C}"
        transform="rotate(-90 75 75)" opacity="0.92">
        <animate attributeName="opacity" from="0" to="0.92" dur="0.5s" fill="freeze"/></circle>`;
      offset += frac;
      legend += `<div class="flex-center" style="margin-bottom:5px"><i style="width:10px;height:10px;border-radius:3px;background:${cols[k]};display:inline-block"></i>${names[k]} <b style="margin-left:auto">${v}</b></div>`;
    });
    svg.innerHTML = inner + `<text x="75" y="72" text-anchor="middle" fill="#eef1fb" font-size="20" font-weight="800">${total}</text>
      <text x="75" y="90" text-anchor="middle" fill="#6b7398" font-size="10">scored</text>`;
    $("donutLegend").innerHTML = legend;
  }

  /* ---------- timeline ---------- */
  function drawTimeline(txns) {
    const svg = $("timeline");
    const recent = txns.slice(0, 40).reverse();
    if (!recent.length) {
      svg.innerHTML = '<text x="280" y="75" text-anchor="middle" fill="#6b7398" font-size="13">no transactions yet</text>';
      return;
    }
    const w = 560, h = 150;
    const maxScore = 100;
    let pts = "";
    recent.forEach((t, i) => {
      const x = (i / (recent.length - 1 || 1)) * (w - 16) + 8;
      const y = h - 20 - (t.risk_score / maxScore) * (h - 44);
      pts += `${x},${y} `;
    });
    const last = recent[recent.length - 1];
    const lastY = h - 20 - (last.risk_score / maxScore) * (h - 44);
    const lastX = w - 8;
    const color = last.risk_level === "critical" ? "#f87171" : last.risk_level === "high" ? "#fb923c" : last.risk_level === "medium" ? "#fbbf24" : "#34d399";
    svg.innerHTML = `
      <line x1="8" y1="h-20" x2="${w - 8}" y2="h-20" stroke="rgba(148,163,215,0.2)"/>
      <line x1="8" y1="40" x2="${w - 8}" y2="40" stroke="rgba(148,163,215,0.12)" stroke-dasharray="4 4"/>
      <polyline points="${pts}" fill="none" stroke="${color}" stroke-width="2.5" opacity="0.9"/>
      <circle cx="${lastX}" cy="${lastY}" r="4" fill="${color}">
        <animate attributeName="r" values="3;5;3" dur="1.6s" repeatCount="indefinite"/></circle>`
      .replace(/h-20/g, String(h - 20));
  }

  /* ---------- queue ---------- */
  let txnsCache = [];

  async function loadTransactions() {
    const data = await api("/api/transactions");
    txnsCache = data.transactions;
    const rows = $("txnRows");
    if (!txnsCache.length) {
      rows.innerHTML = '<tr><td colspan="5" class="empty">No transactions yet — start the live demo stream or run the simulator.</td></tr>';
      return;
    }
    rows.innerHTML = txnsCache.slice(0, 12).map(t => `
      <tr class="expandable" data-id="${t.txn_id}">
        <td><code>${t.txn_id.slice(-10)}</code></td>
        <td>${pill(t.risk_level)}</td>
        <td><b>${Math.round(t.risk_score)}</b></td>
        <td>${statusPill(t.status)}</td>
        <td>${t.decision && t.decision.hold_hours ? t.decision.hold_hours + "h" : "—"}</td>
      </tr>
      <tr class="detail-row hidden" id="detail-${t.txn_id}"><td colspan="5"><div class="detail-box" id="detailbox-${t.txn_id}"></div></td></tr>`).join("");

    rows.querySelectorAll("tr.expandable").forEach(tr => {
      tr.addEventListener("click", () => {
        const id = tr.dataset.id;
        const det = $(`detail-${id}`);
        det.classList.toggle("hidden");
        if (!det.classList.contains("hidden") && !$(`detailbox-${id}`).dataset.loaded) {
          renderDetail(id);
        }
      });
    });
  }

  async function renderDetail(txnId) {
    const t = txnsCache.find(x => x.txn_id === txnId);
    if (!t) return;
    const box = $(`detailbox-${txnId}`);
    box.dataset.loaded = "1";
    const req = t.request || {};
    const steps = (t.decision && t.decision.steps || []).map(s => `• ${s.description}`).join("<br>");
    box.innerHTML = `
      <div class="grid grid-2" style="margin-top:10px">
        <div>
          <b style="font-size:13px">Decision</b><br>
          action: <code>${t.decision.action}</code> · verified: <code>${t.decision.verified}</code><br>
          <div style="margin-top:6px">${steps}</div>
        </div>
        <div>
          <b style="font-size:13px">Context</b><br>
          amount: ${req.transaction ? "₹" + req.transaction.amount.toLocaleString("en-IN") : "—"} ·
          balance after: ₹${req.transaction ? req.transaction.balance_after_tx.toLocaleString("en-IN") : "—"}<br>
          call: <code>${(req.call || {}).call_type || "none"}</code> ·
          screen-share: <code>${(req.call || {}).screen_share_active ? "yes" : "no"}</code><br>
          device change: <code>${(req.device || {}).device_changed ? "yes" : "no"}</code>
          ${t.override ? `<br>override: <code>${t.override.override_to}</code> — ${t.override.reason}` : ""}
        </div>
      </div>`;
  }

  /* ---------- alerts ---------- */
  async function loadAlerts() {
    const data = await api("/api/alerts");
    const rows = $("alertRows");
    if (!data.alerts.length) {
      rows.innerHTML = '<tr><td colspan="4" class="empty">No alerts fired yet.</td></tr>';
      return;
    }
    rows.innerHTML = data.alerts.slice().reverse().slice(0, 10).map(a => `
      <tr class="live-row">
        <td><code>${a.payload.alert_id.slice(0, 13)}…</code></td>
        <td>${a.payload.event_type}<br><span class="muted">${a.payload.txn_id}</span></td>
        <td>${pill(a.payload.risk_level)} <b>${Math.round(a.payload.risk_score)}</b></td>
        <td>${a.signature_valid === false
          ? '<span class="pill false_positive">TAMPERED</span>'
          : '<span class="pill processed">VALID</span>'}</td>
      </tr>`).join("");
  }

  /* ---------- chain ---------- */
  async function loadChain() {
    const c = await api("/api/evidence/chain/verify");
    const ok = c.verified;
    $("chainStatus").innerHTML = `
      <div class="banner ${ok ? "good" : "danger"}">
        <div class="icon">${ok ? "&#9989;" : "&#10060;"}</div>
        <div>
          <h4>${ok ? "Evidence chain verified — no tampering" : "Chain INVALID — tampering detected"}</h4>
          <div>${c.entries} entries, SHA-256 linked. ${ok ? "Every block links to the previous one." : JSON.stringify(c.first_error)}</div>
        </div>
      </div>`;
    const list = $("chainList");
    list.innerHTML = "";
    if (c.entries) {
      const latest = await api("/api/evidence/latest?n=5");
      latest.entries.forEach(e => {
        const div = document.createElement("div");
        div.className = "chain-block live-row";
        div.innerHTML = `
          <div class="type">${e.entry_type === "intervention" ? "&#9888;" : e.entry_type === "proceed" ? "&#9989;" : e.entry_type === "cancel" ? "&#10060;" : e.entry_type === "feedback" ? "&#11088;" : "&#128273;"}</div>
          <div class="info"><b>${e.entry_type}</b><span>${e.timestamp} · ${e.txn_id || ""}</span></div>
          <span class="hash">${e.hash.slice(0, 24)}…</span>`;
        list.appendChild(div);
      });
    }
  }

  /* ---------- feedback ---------- */
  async function loadFeedback() {
    const data = await api("/api/transactions");
    const fb = data.transactions.filter(t => t.feedback);
    const rows = $("fbRows");
    if (!fb.length) {
      rows.innerHTML = '<tr><td colspan="4" class="empty">No feedback yet — run the simulator and rate a decision.</td></tr>';
      return;
    }
    rows.innerHTML = fb.map(t => `
      <tr>
        <td><code>${t.txn_id.slice(-10)}</code></td>
        <td>${"★".repeat(t.feedback.rating)}<span style="opacity:.25">${"★".repeat(5 - t.feedback.rating)}</span></td>
        <td>${t.feedback.label ? `<span class="pill ${t.feedback.label === "false_positive" ? "false_positive" : "critical"}">${t.feedback.label}</span>` : "—"}</td>
        <td class="muted">${t.feedback.comment || "—"}</td>
      </tr>`).join("");
  }

  /* ---------- stats ---------- */
  async function loadStats() {
    const s = await api("/api/stats");
    $("statTotal").textContent = s.total;
    $("statHeld").textContent = s.held;
    $("statCritical").textContent = s.critical;
    $("statFp").textContent = (s.fp_rate * 100).toFixed(1) + "%";

    history.total.push(s.total); history.held.push(s.held);
    history.critical.push(s.critical); history.fp.push(s.fp_rate * 100);
    if (history.total.length > 30) {
      ["total", "held", "critical", "fp"].forEach(k => history[k].shift());
    }
    spark($("sparkTotal"), history.total, "#38bdf8");
    spark($("sparkHeld"), history.held, "#fbbf24");
    spark($("sparkCritical"), history.critical, "#f87171");
    spark($("sparkFp"), history.fp, "#34d399");

    drawDonut({ low: s.total - s.high - s.critical - s.medium, medium: s.medium, high: s.high, critical: s.critical });
  }

  /* ---------- policy ---------- */
  async function loadPolicy() {
    const p = await api("/api/policy");
    $("polMedium").value = p.thresholds.medium;
    $("polHigh").value = p.thresholds.high;
    $("polCritical").value = p.thresholds.critical;
    $("polHoldHigh").value = p.holds.high_hours;
    $("polHoldCrit").value = p.holds.critical_hours;
    $("polUrgency").value = p.urgent_critical_bonus;
    $("polPattern").value = p.pattern_bonus;
    $("polSocial").value = p.social_engineering_bonus;
    dumpPolicy(p);
  }

  function dumpPolicy(p) {
    $("policyDump").textContent = JSON.stringify(p, null, 2);
  }

  $("btnSavePolicy").addEventListener("click", async () => {
    const body = {
      thresholds: {
        low: 30,
        medium: +$("polMedium").value,
        high: +$("polHigh").value,
        critical: +$("polCritical").value,
      },
      holds: { high_hours: +$("polHoldHigh").value, critical_hours: +$("polHoldCrit").value },
      urgent_critical_bonus: +$("polUrgency").value,
      pattern_bonus: +$("polPattern").value,
      social_engineering_bonus: +$("polSocial").value,
    };
    try {
      const r = await api("/api/policy", { method: "POST", body: JSON.stringify(body) });
      dumpPolicy(r.policy);
      toast("Policy applied live — engine re-instantiated");
    } catch (e) {
      toast(e.message, false);
    }
  });

  $("btnResetPolicy").addEventListener("click", async () => {
    const body = {
      thresholds: { low: 30, medium: 55, high: 75, critical: 85 },
      holds: { high_hours: 2, critical_hours: 24 },
      urgent_critical_bonus: 15, pattern_bonus: 10, social_engineering_bonus: 12,
    };
    const r = await api("/api/policy", { method: "POST", body: JSON.stringify(body) });
    dumpPolicy(r.policy);
    toast("Policy reset to defaults");
    loadPolicy();
  });

  /* ---------- live demo stream ---------- */
  const DEMO_PAYLOADS = [
    (rng) => ({ // digital arrest
      transaction: { amount: 95000, account_balance: 100000, balance_after_tx: 5000, txn_amount_30d_avg: 1500, txn_amount_30d_max: 4000, is_new_beneficiary: true, beneficiary_added_days_ago: 0, beneficiary_previous_tx_count: 0, txn_count_last_1h: 0, unusual_hour: false },
      user: { user_id: "USR-" + rng(9000, 9999), age: 55 },
      call: { call_type: "video", call_status: "active", screen_share_active: true, caller_number_not_in_contacts: true },
      device: { device_changed: true },
      urgency_text: "You are under digital arrest. Transfer all money right now or police will come. Share your PIN. Don't tell anyone.",
    }),
    (rng) => ({ // bank impersonation with voice clone
      transaction: { amount: 60000, account_balance: 90000, balance_after_tx: 30000, txn_amount_30d_avg: 2500, txn_amount_30d_max: 6000, is_new_beneficiary: true, beneficiary_added_days_ago: 1, beneficiary_previous_tx_count: 0, txn_count_last_1h: 1, unusual_hour: false },
      user: { user_id: "USR-" + rng(9000, 9999), age: 47 },
      call: { call_type: "phone", call_status: "active", screen_share_active: false, caller_number_not_in_contacts: true },
      device: { device_changed: true },
      voice: { acoustic_clone_probability: 0.84, model_confidence: 0.8, sample_duration_sec: 40 },
      urgency_text: "Bank customer care. Share your OTP and UPI PIN immediately or your account will be blocked.",
    }),
    (rng) => ({ // legit rent
      transaction: { amount: 12000, account_balance: 100000, balance_after_tx: 88000, txn_amount_30d_avg: 11500, txn_amount_30d_max: 14000, is_new_beneficiary: false, beneficiary_added_days_ago: 300, beneficiary_previous_tx_count: 20, txn_count_last_1h: 0, unusual_hour: false },
      user: { user_id: "USR-" + rng(9000, 9999), age: 32 },
      call: { call_type: "none", call_status: "none", screen_share_active: false, caller_number_not_in_contacts: false },
      urgency_text: "Transferring rent for this month as usual. Thanks!",
    }),
    (rng) => ({ // legit bill
      transaction: { amount: 1800, account_balance: 50000, balance_after_tx: 48200, txn_amount_30d_avg: 1600, txn_amount_30d_max: 2500, is_new_beneficiary: false, beneficiary_added_days_ago: 200, beneficiary_previous_tx_count: 30, txn_count_last_1h: 3, unusual_hour: false },
      user: { user_id: "USR-" + rng(9000, 9999), age: 29 },
      call: { call_type: "none", call_status: "none", screen_share_active: false, caller_number_not_in_contacts: false },
      urgency_text: "Monthly electricity bill paid via UPI.",
    }),
    (rng) => ({ // lottery
      transaction: { amount: 10000, account_balance: 40000, balance_after_tx: 30000, txn_amount_30d_avg: 1500, txn_amount_30d_max: 3000, is_new_beneficiary: true, beneficiary_added_days_ago: 2, beneficiary_previous_tx_count: 0, txn_count_last_1h: 0, unusual_hour: true },
      user: { user_id: "USR-" + rng(9000, 9999), age: 41 },
      call: { call_type: "phone", call_status: "ended_within_60s", screen_share_active: false, caller_number_not_in_contacts: true },
      voice: { acoustic_clone_probability: 0.68, model_confidence: 0.7, sample_duration_sec: 15 },
      urgency_text: "Congratulations! You won the grand prize. Pay the processing fee right now to release your winnings.",
    }),
  ];

  let streamTimer = null;
  $("btnLiveDemo").addEventListener("click", () => {
    if (streamTimer) {
      clearInterval(streamTimer);
      streamTimer = null;
      $("btnLiveDemo").textContent = "&#9889; Start Live Demo Stream";
      $("demoState").textContent = "paused";
      toast("Live demo stream paused");
      return;
    }
    const rng = (lo, hi) => Math.floor(lo + Math.random() * (hi - lo));
    const fire = async () => {
      const make = DEMO_PAYLOADS[rng(0, DEMO_PAYLOADS.length)];
      try {
        await api("/api/score", { method: "POST", body: JSON.stringify(make(rng)) });
        refresh();
      } catch (e) { /* keep streaming */ }
    };
    fire();
    streamTimer = setInterval(fire, 3200);
    $("btnLiveDemo").textContent = "&#10074;&#10074; Pause Stream";
    $("demoState").textContent = "streaming every 3.2s";
    toast("Live demo stream started — synthetic transactions flowing");
  });

  /* ---------- AI call analyses + recordings ---------- */
  async function loadAI() {
    const [ana, rec] = await Promise.all([api("/api/conversation/recent?n=12"), api("/api/call/recordings?n=10")]);

    const aiRows = $("aiRows");
    if (!ana.analyses.length) {
      aiRows.innerHTML = '<tr><td colspan="6" class="empty">No call analyses yet — run the simulator or paste a transcript.</td></tr>';
    } else {
      const VCLS = { FRAUD: "critical", SUSPICIOUS: "high", LEGITIMATE: "processed", INCONCLUSIVE: "held" };
      aiRows.innerHTML = ana.analyses.map(a => `
        <tr class="live-row" title="${esc((a.opinion.summary || "").slice(0, 140))}">
          <td class="muted">${(a.timestamp || "").slice(11, 19)}</td>
          <td><span class="pill ${VCLS[a.opinion.verdict] || "held"}">${a.opinion.verdict}</span> <span class="muted">${Math.round(a.opinion.confidence * 100)}%</span></td>
          <td><b>${Math.round(a.fraud_score * 100)}</b></td>
          <td class="muted">${esc((a.intent.display || a.intent.label || "").slice(0, 34))}</td>
          <td>${a.engine === "llm"
            ? `<span class="pill high" title="${esc(a.llm_model || "")}">LLM</span>`
            : `<span class="pill processed">NLP</span>`}</td>
          <td class="muted">${esc(a.source || "api")}</td>
        </tr>`).join("");
    }

    const recRows = $("recRows");
    if (!rec.recordings.length) {
      recRows.innerHTML = '<tr><td colspan="4" class="empty">No recordings uploaded yet.</td></tr>';
    } else {
      recRows.innerHTML = rec.recordings.map(r => `
        <tr class="live-row">
          <td><code>${esc(r.filename)}</code></td>
          <td>${(r.size_bytes / 1024).toFixed(1)} KB</td>
          <td>${esc(r.format || "—")}</td>
          <td>${r.analysis_id
            ? `<span class="pill ${r.analysis_id ? "processed" : "held"}">analyzed</span>`
            : '<span class="pill held">no transcript</span>'}</td>
        </tr>`).join("");
    }
  }

  function esc(s) {
    if (s === null || s === undefined) return "";
    const d = document.createElement("div");
    d.textContent = String(s);
    return d.innerHTML;
  }

  /* ---------- refresh ---------- */
  async function refresh() {
    try {
      await Promise.all([loadStats(), loadTransactions(), loadAlerts(), loadChain(), loadFeedback(), loadAI()]);
      drawTimeline(txnsCache);
    } catch (e) {
      toast("Refresh failed: " + e.message, false);
    }
  }

  refresh();
  setInterval(refresh, 4000);
})();