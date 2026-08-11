(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);

  const SCENARIOS = [
    {
      key: "digital_arrest", icon: "&#128110;", threat: "high",
      title: "Digital Arrest", desc: "Police impersonator, video call, screen share",
      payee: "Ramesh Kumar", upi: "ramesh@okhdfc", avatar: "RK", avatarColor: "linear-gradient(135deg,#ef4444,#7c2d12)",
      amount: 98000, balance: 100000, avg: 1500, beneficiaryDays: 0,
      call: { type: "video", status: "active", share: true, unknown: true },
      voice: { prob: null, conf: null },
      transcript: [
        { who: "s", text: "This is Cyber Crime cell. You are under DIGITAL ARREST." },
        { who: "s", text: "A case has been filed against your Aadhaar for money laundering." },
        { who: "s", text: "Share your screen so I can see your accounts." },
        { who: "s", text: "Transfer all money to this account RIGHT NOW or police will come." },
        { who: "s", text: "Don't tell anyone about this call. Share your UPI PIN." },
        { who: "u", text: "But how do I know this is real? I'm scared." },
        { who: "s", text: "You will be arrested in 30 minutes. Pay now, immediately!" },
      ],
    },
    {
      key: "bank_impersonation", icon: "&#127974;", threat: "high",
      title: "Bank Employee Call", desc: "Fake customer care, OTP phishing, voice clone",
      payee: "Customer Care Escrow", upi: "helpdesk@ybl", avatar: "CC", avatarColor: "linear-gradient(135deg,#f59e0b,#92400e)",
      amount: 65000, balance: 90000, avg: 2500, beneficiaryDays: 0,
      call: { type: "phone", status: "active", share: false, unknown: true },
      voice: { prob: 0.88, conf: 0.82, dur: 42 },
      transcript: [
        { who: "s", text: "Hello, I'm calling from your bank's customer care department." },
        { who: "s", text: "Your account has been flagged for unusual activity." },
        { who: "s", text: "It will be BLOCKED permanently unless you verify right now." },
        { who: "s", text: "Share the OTP and your UPI PIN to confirm." },
        { who: "u", text: "Shouldn't I call the number on my card instead?" },
        { who: "s", text: "No time! It expires in 5 minutes. Keep this confidential." },
      ],
    },
    {
      key: "courier_drugs", icon: "&#128230;", threat: "high",
      title: "Courier / Drugs", desc: "Narcotics parcel, pay 'fine' to avoid arrest",
      payee: "Parcel Escrow", upi: "parcelfine@ibl", avatar: "PE", avatarColor: "linear-gradient(135deg,#fb923c,#7c2d12)",
      amount: 45000, balance: 70000, avg: 2000, beneficiaryDays: 0,
      call: { type: "phone", status: "active", share: true, unknown: true },
      voice: { prob: null, conf: null },
      transcript: [
        { who: "s", text: "Your international parcel was stopped — it contains illegal drugs." },
        { who: "s", text: "You are being charged with narcotics possession." },
        { who: "s", text: "Pay the court fine right now and the case will be dropped." },
        { who: "u", text: "I never sent any parcel! I'll call the police." },
        { who: "s", text: "Police are already here. Pay the fine NOW to avoid arrest!" },
      ],
    },
    {
      key: "lottery_fraud", icon: "&#127915;", threat: "mid",
      title: "Lottery Prize", desc: "'You won!' — pay fees to release winnings",
      payee: "Prize Claims Desk", upi: "prize@ptm", avatar: "PC", avatarColor: "linear-gradient(135deg,#a78bfa,#5b21b6)",
      amount: 12000, balance: 50000, avg: 1500, beneficiaryDays: 1,
      call: { type: "phone", status: "ended", share: false, unknown: true },
      voice: { prob: 0.72, conf: 0.75, dur: 18 },
      transcript: [
        { who: "s", text: "Congratulations! You've won the KBC grand prize of ₹25 lakh!" },
        { who: "s", text: "To release your winnings, pay the processing fee." },
        { who: "s", text: "The offer expires in 10 minutes. Send ₹12,000 right now." },
        { who: "u", text: "Wow! But why do I need to pay to receive money?" },
        { who: "s", text: "It's just the GST and processing. Hurry up, final call!" },
      ],
    },
    {
      key: "relative_emergency", icon: "&#128104;&#8205;&#128102;", threat: "mid",
      title: "Relative Emergency", desc: "Cloned voice of a relative in distress",
      payee: "Anjali Sharma", upi: "anjali@ybl", avatar: "AS", avatarColor: "linear-gradient(135deg,#38bdf8,#1e3a8a)",
      amount: 30000, balance: 60000, avg: 1800, beneficiaryDays: 10,
      call: { type: "phone", status: "active", share: false, unknown: false },
      voice: { prob: 0.91, conf: 0.88, dur: 55 },
      transcript: [
        { who: "s", text: "भाई... मैं अनजलि बोल रही हूं। मुझे अस्पताल में एडमिट कराया है।" },
        { who: "s", text: "डॉक्टर का बिल जमा करना है। तुरंत कुछ पैसे भेजो।" },
        { who: "s", text: "किसी को मत बताना। अभी भेजो, 30,000 चाहिए।" },
        { who: "u", text: "अनजलि? आवाज़ तो तुम्हारी जैसी ही है... लेकिन तुम किस नंबर से बोल रही हो?" },
        { who: "s", text: "जल्दी करो! डॉक्टर बिल के बिना इलाज रोक देंगे।" },
      ],
    },
    {
      key: "rent_payment", icon: "&#127968;", threat: "low",
      title: "Rent Payment", desc: "Monthly rent, known beneficiary",
      payee: "Sanjay Verma (Landlord)", upi: "sanjay.verma@okaxis", avatar: "SV", avatarColor: "linear-gradient(135deg,#34d399,#065f46)",
      amount: 12000, balance: 100000, avg: 11500, beneficiaryDays: 300,
      call: { type: "none", status: "none", share: false, unknown: false },
      voice: { prob: null, conf: null },
      transcript: [
        { who: "s", text: "Hi, the rent for this month. Will send the receipt shortly." },
        { who: "u", text: "Got it, paying now. Thanks!" },
      ],
    },
    {
      key: "bill_payment", icon: "&#128200;", threat: "low",
      title: "Bill Payment", desc: "Recurring electricity bill",
      payee: "Maharashtra Electricity", upi: "msedcl@bbps", avatar: "ME", avatarColor: "linear-gradient(135deg,#facc15,#713f12)",
      amount: 1800, balance: 50000, avg: 1600, beneficiaryDays: 200,
      call: { type: "none", status: "none", share: false, unknown: false },
      voice: { prob: null, conf: null },
      transcript: [
        { who: "s", text: "Electricity bill for May. Pay via UPI for instant credit." },
        { who: "u", text: "Done. Thanks!" },
      ],
    },
    {
      key: "family_transfer", icon: "&#128106;", threat: "low",
      title: "Family Transfer", desc: "Money to mother, usual amount",
      payee: "Mom (Geeta)", upi: "geeta.gupta@okhdfc", avatar: "GM", avatarColor: "linear-gradient(135deg,#f472b6,#831843)",
      amount: 5000, balance: 60000, avg: 4800, beneficiaryDays: 600,
      call: { type: "none", status: "none", share: false, unknown: false },
      voice: { prob: null, conf: null },
      transcript: [
        { who: "s", text: "माँ के लिए पैसे भेज रहा हूं। महीने का खर्चा।" },
        { who: "u", text: "Sent. Take care, Ma!" },
      ],
    },
  ];

  const FEATURE_ORDER = ["new_beneficiary", "amount_deviation", "balance_drain", "call_screen_share", "device_change", "velocity", "urgency", "voice_risk"];
  const LEVEL_COLORS = { low: "#34d399", medium: "#fbbf24", high: "#fb923c", critical: "#f87171" };
  const CIRC = 414.69;
  const NUM_FORMAT = new Intl.NumberFormat("en-IN");

  let current = null;          // current score response
  let currentScenario = null;  // current scenario object
  let callTimerInt = null;
  let callSeconds = 0;
  let transcriptPos = 0;
  let typingTimer = null;

  /* ---------------- helpers ---------------- */
  function toast(msg, ok = true) {
    const t = $("toast");
    t.textContent = msg;
    t.className = "toast show " + (ok ? "ok" : "err");
    setTimeout(() => t.classList.remove("show"), 3400);
  }

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

  function inr(v) {
    return "₹" + NUM_FORMAT.format(Math.round(v));
  }

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }

  /* ---------------- clock ---------------- */
  function tickClock() {
    const now = new Date();
    $("phoneTime").textContent = now.toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" });
  }
  setInterval(tickClock, 1000);
  tickClock();

  /* ---------------- scenario list ---------------- */
  function renderScenarios() {
    $("scenarioList").innerHTML = SCENARIOS.map(s => `
      <button class="scenario" data-key="${s.key}">
        <span class="icon">${s.icon}</span>
        <span class="meta">
          <span class="title">${s.title}</span>
          <span class="desc">${s.desc}</span>
        </span>
        <span class="risk-dot rd-${s.threat}"></span>
      </button>`).join("");
    document.querySelectorAll(".scenario").forEach(el => {
      el.addEventListener("click", () => selectScenario(el.dataset.key));
    });
  }

  function selectScenario(key) {
    currentScenario = SCENARIOS.find(s => s.key === key);
    current = null;
    stopCall();
    resetResult();
    renderPhone();
    renderTranscript();
    resetFlow();
    resetAI();
    document.querySelectorAll(".scenario").forEach(el => {
      el.classList.toggle("active", el.dataset.key === key);
    });
  }

  /* ---------------- phone ---------------- */
  function renderPhone() {
    const s = currentScenario;
    $("appAvatar").textContent = s.avatar;
    $("appAvatar").style.background = s.avatarColor;
    $("appPayee").textContent = s.payee;
    $("appPayeeSub").textContent = "UPI ID · " + s.upi;
    $("appAmount").textContent = inr(s.amount);
    $("appBalance").textContent = inr(s.balance);
    $("appApprox").textContent = s.avg ? `~ ${(s.amount / s.avg).toFixed(1)}x your usual payment` : "new payment pattern";
    $("payBtn").textContent = "Pay " + inr(s.amount);
    $("payHint").textContent = "Press pay to trigger real-time risk scoring";
    $("phoneResult").innerHTML = "";
    $("phoneStatus").classList.add("hidden");
    $("payBtn").disabled = false;
    if (s.call.type !== "none") {
      setTimeout(() => startCall(s), 500);
    }
  }

  /* ---------------- call overlay ---------------- */
  function startCall(s) {
    $("callOverlay").classList.remove("hidden");
    $("callName").textContent = s.call.unknown ? "Unknown Caller" : s.payee;
    $("callNumber").textContent = s.call.unknown ? "+91 ··· ·· 5 · 2 ··" : s.upi;
    $("callAvatar").style.background = s.call.unknown ? "linear-gradient(135deg,#ef4444,#7c2d12)" : "linear-gradient(135deg,#2563eb,#7c3aed)";
    $("callAvatar").innerHTML = s.call.unknown ? "?" : s.avatar[0];
    $("tagShare").classList.toggle("hidden", !s.call.share);
    $("tagUnknown").classList.toggle("hidden", !s.call.unknown);
    $("tagVideo").classList.toggle("hidden", s.call.type !== "video");
    callSeconds = 0;
    $("callTimer").textContent = "00:00";
    clearInterval(callTimerInt);
    callTimerInt = setInterval(() => {
      callSeconds++;
      const m = String(Math.floor(callSeconds / 60)).padStart(2, "0");
      const sec = String(callSeconds % 60).padStart(2, "0");
      $("callTimer").textContent = `${m}:${sec}`;
    }, 1000);
  }

  function stopCall() {
    clearInterval(callTimerInt);
    callTimerInt = null;
    $("callOverlay").classList.add("hidden");
  }

  $("callEnd").addEventListener("click", () => {
    stopCall();
    toast("Call ended.");
  });

  $("callMic").addEventListener("click", (e) => {
    e.target.classList.toggle("dim");
    e.target.style.opacity = e.target.style.opacity === "0.35" ? "1" : "0.35";
  });

  $("callVerify").addEventListener("click", () => {
    toast("Identity check sent to user — reminder: banks never ask for PIN/OTP.");
  });

  /* ---------------- transcript + urgency ---------------- */
  function renderTranscript() {
    const s = currentScenario;
    transcriptPos = 0;
    $("chatBox").innerHTML = "";
    $("urgencyFill").style.width = "0%";
    $("urgencyPct").textContent = "0%";
    $("urgencyTerms").innerHTML = "";
    clearTimeout(typingTimer);
    typeLine();
  }

  function typeLine() {
    const s = currentScenario;
    if (!s || transcriptPos >= s.transcript.length) return;
    const line = s.transcript[transcriptPos];
    const box = $("chatBox");
    const typing = document.createElement("div");
    typing.className = "bubble " + (line.who === "s" ? "in" : "out");
    typing.innerHTML = '<span class="who">' + (line.who === "s" ? "&#128100; Caller" : "&#128100; You") + '</span><span class="typing"><span></span><span></span><span></span></span>';
    box.appendChild(typing);
    box.scrollTop = box.scrollHeight;
    typingTimer = setTimeout(() => {
      typing.innerHTML = esc(line.text);
      box.scrollTop = box.scrollHeight;
      transcriptPos++;
      analyzeTranscript();
      setTimeout(typeLine, 950 + Math.random() * 700);
    }, 600);
  }

  async function analyzeTranscript() {
    const s = currentScenario;
    const full = s.transcript.slice(0, transcriptPos).map(l => l.text).join(" ");
    try {
      const r = await api("/api/urgency?text=" + encodeURIComponent(full));
      const pct = Math.round(r.urgency_score * 100);
      $("urgencyFill").style.width = pct + "%";
      $("urgencyPct").textContent = pct + "%";
      $("urgencyTerms").innerHTML = r.matched_terms.map(t => `<span class="term-tag">${esc(t)}</span>`).join("");
    } catch (e) { /* offline tolerance */ }

    try {
      const analysis = await api("/api/conversation/analyze", {
        method: "POST",
        body: JSON.stringify({
          turns: s.transcript.slice(0, transcriptPos),
          source: "simulator-live",
          engine: "nlp",
          persist: false,
        }),
      });
      renderLiveVerdict(analysis);
      aiResultData = analysis;
      if (transcriptPos >= s.transcript.length && currentScenario === s) {
        if (selectedEngine() === "llm" || (selectedEngine() === "auto" && llmStatus.configured)) {
          deepAIAnalysis(s.transcript, "Simulated call complete — AI agent review of the whole situation:");
        } else {
          renderAnalysis(analysis, "Simulated call analysis complete — final opinion issued.");
        }
      }
    } catch (e) { /* offline tolerance */ }
  }

  async function deepAIAnalysis(turns, note) {
    if (!turns || !turns.length) return;
    try {
      const analysis = await api("/api/conversation/analyze", {
        method: "POST",
        body: JSON.stringify({
          turns,
          source: "simulator-live",
          engine: selectedEngine(),
          context: buildLLMContext(),
          persist: false,
        }),
      });
      renderLiveVerdict(analysis);
      aiResultData = analysis;
      renderAnalysis(analysis, note);
    } catch (e) { /* fall back to whatever live verdict exists */ }
  }

  /* ---------------- voice box ---------------- */
  async function renderVoice() {
    const s = currentScenario;
    const v = s.voice;
    if (!v.prob) {
      $("voiceBox").classList.add("hidden");
      return;
    }
    $("voiceBox").classList.remove("hidden");
    const wave = $("waveform");
    wave.innerHTML = "";
    const n = 26;
    for (let i = 0; i < n; i++) {
      const h = 8 + Math.random() * 30;
      const bar = document.createElement("div");
      bar.className = "bar";
      bar.style.height = h + "px";
      wave.appendChild(bar);
    }
    const r = await api(`/api/voice/analyze?prob=${v.prob}&conf=${v.conf}&dur=${v.dur || 30}`);
    const band = r.band;
    const pill = $("voiceBand");
    pill.className = "band-pill " + band;
    pill.textContent = (band === "no_data" ? "NO DATA" : band.toUpperCase() + " BAND");
    if (band === "high" || band === "medium") {
      wave.querySelectorAll(".bar").forEach(b => b.classList.add("alert"));
    }
    $("voiceDetail").innerHTML = `
      <span>Clone probability <b>${Math.round(v.prob * 100)}%</b></span>
      <span>Model confidence <b>${Math.round(v.conf * 100)}%</b></span>
      <span>Sample <b>${v.dur || 30}s</b></span>
      <span>Verdict <b>${r.verdict.replace(/_/g, " ")}</b></span>`;
  }

  /* ---------------- scoring ---------------- */
  $("payBtn").addEventListener("click", doScore);
  document.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && document.activeElement.tagName !== "INPUT" && document.activeElement.tagName !== "TEXTAREA") {
      doScore();
    }
  });

  async function doScore() {
    const s = currentScenario;
    if (!s) { toast("Pick a scenario first", false); return; }
    if (s.voice.prob) await renderVoice();

    $("payBtn").disabled = true;
    $("phoneStatus").classList.remove("hidden");
    $("payHint").textContent = "risk engine is scoring...";

    const callStatus = s.call.status === "ended" ? "ended_within_60s" : s.call.status === "active" ? "active" : "none";
    const payload = {
      transaction: {
        amount: s.amount,
        account_balance: s.balance,
        balance_after_tx: s.balance - s.amount,
        txn_amount_30d_avg: s.avg,
        txn_amount_30d_max: Math.max(s.avg * 2.5, s.amount * 0.9),
        is_new_beneficiary: s.beneficiaryDays <= 1,
        beneficiary_added_days_ago: s.beneficiaryDays,
        beneficiary_previous_tx_count: s.beneficiaryDays > 30 ? 15 : s.beneficiaryDays > 1 ? 2 : 0,
        txn_count_last_1h: s.key === "bill_payment" ? 4 : 0,
        unusual_hour: false,
      },
      user: { user_id: "USR-DEMO-01", age: 55 },
      call: {
        call_type: s.call.type,
        call_status: callStatus,
        screen_share_active: s.call.share,
        caller_number_not_in_contacts: s.call.unknown,
      },
      device: { device_changed: s.key === "digital_arrest" || s.key === "bank_impersonation" },
      voice: s.voice.prob ? { acoustic_clone_probability: s.voice.prob, model_confidence: s.voice.conf, sample_duration_sec: s.voice.dur } : {},
      urgency_text: conversationOverride
        ? conversationOverride.urgency_text
        : s.transcript.map(l => l.text).join(" "),
    };
    if (conversationOverride && conversationOverride.turns && conversationOverride.turns.length) {
      payload.transcript_turns = conversationOverride.turns;
      payload.use_llm = llmStatus.configured;
    }

    try {
      const body = await api("/api/score", { method: "POST", body: JSON.stringify(payload) });
      current = body;
      renderResult(body);
      $("phoneStatus").classList.add("hidden");
      $("phoneResult").innerHTML = phoneResultHTML(body);
      $("payHint").textContent = "Scored in <1 ms · re-run any time";
      $("payBtn").disabled = false;
      $("txnFooter").textContent = "txn " + body.txn_id;
    } catch (e) {
      $("phoneStatus").classList.add("hidden");
      $("payBtn").disabled = false;
      $("payHint").textContent = "scoring failed — engine unreachable";
      toast(e.message, false);
    }
  }

  function phoneResultHTML(body) {
    const d = body.decision;
    if (d.action === "block") {
      return `<div class="phone-result bad"><div class="big-icon">&#128308;</div><div class="msg">Payment blocked</div><div class="sub">Fraud risk too high · contact bank</div></div>`;
    }
    if (d.action === "cooling_off_wallet") {
      return `<div class="phone-result warn"><div class="big-icon">&#9201;</div><div class="msg">Sent to cooling-off wallet</div><div class="sub">Funds held ${d.hold_hours}h for review</div></div>`;
    }
    if (d.action === "hold" || d.action === "verify") {
      return `<div class="phone-result warn"><div class="big-icon">&#128274;</div><div class="msg">Payment held for verification</div><div class="sub">OTP or trusted-contact required</div></div>`;
    }
    if (d.action === "coach") {
      return `<div class="phone-result warn"><div class="big-icon">&#128161;</div><div class="msg">Coaching warning shown</div><div class="sub">Check you're not being pressured</div></div>`;
    }
    return `<div class="phone-result ok"><div class="big-icon">&#9989;</div><div class="msg">Payment approved</div><div class="sub">Risk ${Math.round(body.risk_score)}/100 · no hold</div></div>`;
  }

  /* ---------------- result render ---------------- */
  function resetResult() {
    $("resultEmpty").classList.remove("hidden");
    $("riskArea").classList.add("hidden");
    $("featurePanel").classList.add("hidden");
    $("expPanel").classList.add("hidden");
    $("metaPanel").classList.add("hidden");
    $("interventionPanel").innerHTML = "";
    $("breakdown").innerHTML = "";
    $("expList").innerHTML = "";
    $("evidenceChain").innerHTML = "";
    $("alertStrip").innerHTML = "";
    $("voiceBox").classList.add("hidden");
  }

  function renderResult(body) {
    $("resultEmpty").classList.add("hidden");
    $("riskArea").classList.remove("hidden");

    const score = Math.round(body.risk_score);
    $("scoreVal").textContent = score;
    const color = LEVEL_COLORS[body.risk_level] || "#4f7cff";
    const fill = $("gaugeFill");
    fill.style.stroke = color;
    fill.style.strokeDashoffset = CIRC * (1 - body.risk_score / 100);

    $("levelText").textContent = body.risk_level.toUpperCase();
    $("levelText").style.color = color;
    const tag = $("levelTag");
    tag.className = "risk-tag " + body.risk_level;
    tag.textContent = body.risk_level.toUpperCase() + " · " + score + "/100";
    tag.style.color = color;

    $("verdictMsg").textContent = body.decision.messages.en || "";

    renderIntervention(body);
    renderFeatures(body);
    renderExplanation(body);
    renderMeta(body);
    renderFlow(body.decision);

    const llm = body.llm_opinion;
    if (llm) {
      const cls = { FRAUD: "danger", SUSPICIOUS: "warn", LEGITIMATE: "good", INCONCLUSIVE: "info" }[llm.verdict] || "info";
      $("alertStrip").insertAdjacentHTML("beforeend", `
        <div class="alert ${cls}">
          <b>&#129504; AI agent review:</b> ${llm.verdict} (${Math.round(llm.confidence * 100)}% confidence)
          &mdash; <i>${esc(llm.summary || "")}</i>
          <span class="muted">model ${esc(llm.llm_model || "?")} &middot; ${Math.round((llm.llm_latency_ms || 0) / 100) / 10}s</span>
        </div>`);
    }
  }

  function renderIntervention(body) {
    const panel = $("interventionPanel");
    const d = body.decision;
    let bannerClass = "info", icon = "&#128269;", title = "Review recommended";
    if (d.action === "block") { bannerClass = "danger"; icon = "&#128308;"; title = "Payment blocked — safety hold"; }
    else if (d.action === "cooling_off_wallet") { bannerClass = "danger"; icon = "&#9201;"; title = "Moved to cooling-off wallet"; }
    else if (d.action === "hold" || d.action === "verify") { bannerClass = "warn"; icon = "&#9888;"; title = "Independent verification required"; }
    else if (d.action === "coach") { bannerClass = "warn"; icon = "&#128161;"; title = "Real-time coaching"; }
    else if (d.action === "allow") { bannerClass = "good"; icon = "&#9989;"; title = "Payment safe to proceed"; }

    panel.innerHTML = `
      <div class="banner ${bannerClass}">
        <div class="icon">${icon}</div>
        <div>
          <h4>${title}</h4>
          <div>${d.messages.en || ""}</div>
          <div class="lang-row">
            <span class="lang-pill">EN</span>
            <span class="lang-pill">${d.messages.hi || ""}</span>
            <span class="lang-pill">${d.messages.mr || ""}</span>
          </div>
        </div>
      </div>
      <ul class="step-list"></ul>`;

    const list = panel.querySelector(".step-list");
    d.steps.forEach((st, i) => {
      const li = document.createElement("li");
      li.innerHTML = `<span class="step-num">${i + 1}</span><span>${esc(st.description)}</span>`;
      list.appendChild(li);
    });

    if (body.warnings.length) {
      const w = document.createElement("div");
      w.className = "banner warn mt-12";
      w.innerHTML = `<div class="icon">&#128680;</div><div><h4>Signals detected</h4><ul style="margin-left:16px;font-size:12.5px">${body.warnings.map(x => `<li>${esc(x)}</li>`).join("")}</ul></div>`;
      panel.appendChild(w);
    }
  }

  function renderFeatures(body) {
    $("featurePanel").classList.remove("hidden");
    const feat = {};
    body.feature_breakdown.forEach(f => { feat[f.name] = f; });

    const maxC = Math.max(...body.feature_breakdown.map(f => f.contribution), 1);
    $("breakdown").innerHTML = body.feature_breakdown.map(f => {
      const color = LEVEL_COLORS[f.contribution / maxC > 0.75 ? "critical" : f.contribution / maxC > 0.5 ? "high" : f.contribution / maxC > 0.25 ? "medium" : "low"];
      return `
        <div class="bar-row">
          <div class="bar-label"><b>${f.name.replace(/_/g, " ")}</b><span>+${f.contribution.toFixed(1)} · w ${f.weight}</span></div>
          <div class="bar"><div style="width:${Math.min(100, (f.contribution / maxC) * 100)}%;background:${color}"></div></div>
        </div>`;
    }).join("");

    const vals = FEATURE_ORDER.map(name => feat[name] ? feat[name].value : 0);
    drawRadar(vals, FEATURE_ORDER);

    $("radarLegend").innerHTML = FEATURE_ORDER.map((f, i) => `
      <span><i style="background:${["#4f7cff", "#38bdf8", "#34d399", "#fbbf24", "#fb923c", "#f87171", "#a78bfa", "#f472b6"][i]}"></i>${f.replace(/_/g, " ")}</span>`).join("");
  }

  function drawRadar(vals, labels) {
    const svg = $("radar");
    const cx = 105, cy = 105, r = 76;
    const n = vals.length;
    let rings = "";
    for (let ring = 1; ring <= 4; ring++) {
      const rr = (r / 4) * ring;
      let pts = "";
      for (let i = 0; i < n; i++) {
        const a = (Math.PI * 2 * i) / n - Math.PI / 2;
        pts += `${cx + rr * Math.cos(a)},${cy + rr * Math.sin(a)} `;
      }
      rings += `<polygon points="${pts}" fill="none" stroke="rgba(148,163,215,0.16)" stroke-width="1"/>`;
    }
    let axes = "";
    for (let i = 0; i < n; i++) {
      const a = (Math.PI * 2 * i) / n - Math.PI / 2;
      axes += `<line x1="${cx}" y1="${cy}" x2="${cx + r * Math.cos(a)}" y2="${cy + r * Math.sin(a)}" stroke="rgba(148,163,215,0.14)"/>`;
      axes += `<text x="${cx + (r + 14) * Math.cos(a)}" y="${cy + (r + 14) * Math.sin(a) + 3.5}" font-size="8.5" fill="#6b7398" text-anchor="middle">${labels[i].split("_").map(w => w[0]).join("").toUpperCase()}</text>`;
    }
    let poly = "";
    for (let i = 0; i < n; i++) {
      const a = (Math.PI * 2 * i) / n - Math.PI / 2;
      poly += `${cx + vals[i] * r * Math.cos(a)},${cy + vals[i] * r * Math.sin(a)} `;
    }
    const score = vals.reduce((a, b) => a + b, 0) / n;
    const fillColor = score > 0.7 ? "rgba(248,113,113,0.55)" : score > 0.4 ? "rgba(251,146,60,0.5)" : score > 0.2 ? "rgba(251,191,36,0.45)" : "rgba(52,211,153,0.45)";
    const strokeColor = score > 0.7 ? "#f87171" : score > 0.4 ? "#fb923c" : score > 0.2 ? "#fbbf24" : "#34d399";
    svg.innerHTML = rings + axes +
      `<polygon points="${poly}" fill="${fillColor}" stroke="${strokeColor}" stroke-width="2" style="transition:all .7s">
         <animate attributeName="opacity" from="0" to="1" dur="0.6s" fill="freeze"/>
       </polygon>` +
      poly.split(" ").map(p => `<circle cx="${p.split(",")[0]}" cy="${p.split(",")[1]}" r="2.6" fill="${strokeColor}"/>`).join("");
  }

  function renderExplanation(body) {
    $("expPanel").classList.remove("hidden");
    $("expList").innerHTML = body.explanation.map(e => {
      const m = e.match(/\(\+([\d.]+)\)$/);
      return `<li>${m ? e.slice(0, m.index).trim() : e}${m ? `<span class="pts" style="color:${LEVEL_COLORS[body.risk_level]}">+${m[1]}</span>` : ""}</li>`;
    }).join("");
  }

  async function renderMeta(body) {
    $("metaPanel").classList.remove("hidden");
    const chainEl = $("evidenceChain");
    chainEl.innerHTML = "";
    if (body.evidence_id) {
      try {
        const ev = await api(`/api/evidence/${body.txn_id}`);
        ev.entries.forEach((e, i) => {
          const div = document.createElement("div");
          div.className = "chain-block";
          div.innerHTML = `
            <div class="type">${e.entry_type === "intervention" ? "&#9888;" : e.entry_type === "proceed" ? "&#9989;" : e.entry_type === "cancel" ? "&#10060;" : e.entry_type === "feedback" ? "&#11088;" : e.entry_type === "override" ? "&#128274;" : "&#128273;"}</div>
            <div class="info"><b>${e.entry_type}</b><span>${e.timestamp} · ${e.txn_id || ""}</span></div>
            <span class="hash">${e.hash.slice(0, 32)}…</span>`;
          chainEl.appendChild(div);
        });
      } catch (e) { /* ignore */ }
    } else {
      chainEl.innerHTML = '<div class="empty">No evidence recorded (low-risk flow).</div>';
    }

    if (body.bank_alert_id) {
      try {
        const alerts = await api("/api/alerts");
        const alert = alerts.alerts.find(a => a.payload.alert_id === body.bank_alert_id);
        if (alert) {
          $("alertStrip").innerHTML = `
            <div class="banner info">
              <div class="icon">&#128276;</div>
              <div>
                <h4>Secure bank alert dispatched</h4>
                <div class="flex-between mt-8"><span class="muted">HMAC-SHA256 signature</span><span class="signature">${alert.signature.slice(0, 40)}…</span></div>
              </div>
            </div>`;
        }
      } catch (e) { /* ignore */ }
    }
  }

  /* ---------------- verification flow ---------------- */
  function resetFlow() {
    const area = $("flowArea");
    area.innerHTML = '<div class="empty">Run a payment first — the required verification steps appear here.</div>';
    $("flowStatus").textContent = "No active transaction.";
  }

  function renderFlow(decision) {
    const area = $("flowArea");
    area.innerHTML = "";
    const action = decision.action;
    $("flowStatus").textContent = `Decision: ${action} · ${decision.steps.length} intervention step(s) · hold ${decision.hold_hours || 0}h`;

    if (action === "block") {
      area.innerHTML = `
        <div class="banner danger"><div class="icon">&#128308;</div>
          <div><h4>Hard block in place</h4>
          <div>This payment cannot be released by user action. Call your bank's fraud desk immediately.</div></div>
        </div>
        <div class="btn-row">
          <button class="btn red sm" id="flowCancel">&#10060; Cancel Payment</button>
          <button class="btn ghost sm" id="flowReport">&#128203; Report to Bank</button>
        </div>`;
    } else if (action === "cooling_off_wallet") {
      area.innerHTML = `
        <div class="banner danger"><div class="icon">&#9201;</div>
          <div><h4>Funds parked in cooling-off wallet</h4>
          <div>Released only after review or explicit acceptance. A cooling-off lets you undo a mistake.</div></div>
        </div>
        <div class="btn-row">
          <button class="btn amber sm" id="flowAcceptCooling">&#9201; Accept Cooling-Off Hold</button>
          <button class="btn red sm" id="flowCancel">&#10060; Cancel Payment</button>
        </div>`;
    } else if (action === "hold" || action === "verify") {
      area.innerHTML = `
        <div class="banner warn"><div class="icon">&#128274;</div>
          <div><h4>Independent verification required</h4>
          <div>Verify with an OTP on your registered number, or via a trusted contact.</div></div>
        </div>
        <div class="section-label mt-12">Option A — OTP verification</div>
        <div class="otp-box">${[0, 1, 2, 3, 4, 5].map(i => `<input class="otp-digit" maxlength="1" data-i="${i}" inputmode="numeric">`).join("")}</div>
        <div class="btn-row">
          <button class="btn sm" id="flowOtp">&#9989; Verify OTP</button>
        </div>
        <div class="section-label mt-16">Option B — Trusted-Contact Circuit Breaker</div>
        <div class="mt-8" id="contactsWrap"></div>
        <div class="btn-row">
          <button class="btn red sm" id="flowCancel">&#10060; Cancel Payment</button>
        </div>`;
      renderContacts();
      const digits = area.querySelectorAll(".otp-digit");
      digits.forEach((d, i) => {
        d.addEventListener("input", () => {
          d.value = d.value.replace(/\D/g, "");
          if (d.value && i < 5) digits[i + 1].focus();
        });
        d.addEventListener("keydown", (e) => {
          if (e.key === "Backspace" && !d.value && i > 0) digits[i - 1].focus();
        });
      });
      $("flowOtp").addEventListener("click", async () => {
        const code = [...digits].map(d => d.value).join("");
        if (code.length < 6) { toast("Enter all 6 OTP digits", false); return; }
        toast("OTP " + code + " verified ✓");
        await release("otp");
      });
    } else if (action === "coach") {
      area.innerHTML = `
        <div class="banner warn"><div class="icon">&#128161;</div>
          <div><h4>Coaching banner was shown</h4>
          <div>The user was nudged before payment completed. Payment allowed after the check.</div></div>
        </div>
        <div class="btn-row">
          <button class="btn green sm" id="flowDone">&#9989; Mark as Reviewed</button>
        </div>`;
      $("flowDone").addEventListener("click", async () => {
        await release("none");
      });
    } else {
      area.innerHTML = `
        <div class="banner good"><div class="icon">&#9989;</div>
          <div><h4>Payment approved without intervention</h4>
          <div>Risk score was within normal range. No holds or verification inserted.</div></div>
        </div>
        <div class="btn-row">
          <button class="btn ghost sm" id="flowFeedback">&#11088; Rate This Decision</button>
        </div>`;
    }

    const cancelBtn = area.querySelector("#flowCancel");
    if (cancelBtn) cancelBtn.addEventListener("click", doCancel);

    const reportBtn = area.querySelector("#flowReport");
    if (reportBtn) reportBtn.addEventListener("click", openReport);
  }

  const CONTACTS = [
    { name: "Geeta (Mother)", rel: "Mother · saved contact", color: "linear-gradient(135deg,#f472b6,#831843)", initials: "GM", phone: "+91 98••• ••321" },
    { name: "Rohit (Brother)", rel: "Brother · saved contact", color: "linear-gradient(135deg,#38bdf8,#1e3a8a)", initials: "RB", phone: "+91 99••• ••876" },
    { name: "Bank Fraud Desk", rel: "Official · 1930", color: "linear-gradient(135deg,#34d399,#065f46)", initials: "FD", phone: "1930" },
  ];

  function renderContacts() {
    const wrap = $("contactsWrap");
    wrap.innerHTML = CONTACTS.map((c, i) => `
      <div class="contact-card">
        <div class="cavatar" style="background:${c.color}">${c.initials}</div>
        <div><div class="cname">${c.name}</div><div class="crel">${c.rel} · ${c.phone}</div></div>
        <button class="btn xs ghost" data-i="${i}">&#128222; Call</button>
      </div>`).join("");
    wrap.querySelectorAll("button").forEach(btn => {
      btn.addEventListener("click", async () => {
        const c = CONTACTS[+btn.dataset.i];
        btn.disabled = true;
        btn.textContent = "Calling…";
        setTimeout(async () => {
          btn.textContent = "✓ Confirmed";
          btn.classList.add("green");
          toast("Trusted contact " + c.name + " confirmed — payment safe to release");
          await release("trusted_contact");
        }, 2200);
      });
    });
  }

  async function release(method) {
    if (!current) return;
    try {
      const body = await api("/api/proceed", {
        method: "POST",
        body: JSON.stringify({ txn_id: current.txn_id, verification_method: method }),
      });
      toast(body.message || "Released");
      $("phoneResult").innerHTML = `<div class="phone-result ok"><div class="big-icon">&#9989;</div><div class="msg">Payment released</div><div class="sub">${body.message || ""}</div></div>`;
      renderFlow({ ...current.decision, action: "allow" });
      current.decision.action = "allow";
      $("flowStatus").textContent = "Released · verification: " + method;
      askFeedback();
    } catch (e) {
      toast(e.message, false);
    }
  }

  async function doCancel() {
    if (!current) return;
    try {
      const body = await api("/api/cancel", { method: "POST", body: JSON.stringify({ txn_id: current.txn_id }) });
      toast(body.message || "Cancelled");
      $("phoneResult").innerHTML = `<div class="phone-result bad"><div class="big-icon">&#10060;</div><div class="msg">Payment cancelled</div><div class="sub">No funds were moved</div></div>`;
      $("flowArea").innerHTML = '<div class="empty">Payment cancelled by user.</div>';
      $("flowStatus").textContent = "Cancelled · evidence preserved";
      askFeedback();
    } catch (e) {
      toast(e.message, false);
    }
  }

  async function askFeedback() {
    if (!current) return;
    const area = $("flowArea");
    area.innerHTML = `
      <div class="banner info"><div class="icon">&#128202;</div>
        <div><h4>False-positive monitoring</h4>
        <div>Was the intervention correct? Your answer tunes bank policies and the engine's precision/recall.</div></div>
      </div>
      <div class="btn-row">
        <button class="btn green sm" id="fbCorrect">&#10003; Correct</button>
        <button class="btn ghost sm" id="fbFalse">&#10007; False Positive</button>
      </div>`;
    $("fbCorrect").addEventListener("click", () => sendFeedback("fraud"));
    $("fbFalse").addEventListener("click", () => sendFeedback("false_positive"));
  }

  async function sendFeedback(label) {
    if (!current) return;
    try {
      await api("/api/feedback", {
        method: "POST",
        body: JSON.stringify({ txn_id: current.txn_id, rating: label === "fraud" ? 5 : 1, label, comment: "simulator feedback" }),
      });
      toast("Feedback recorded — thanks for improving the engine!");
      $("flowArea").innerHTML = '<div class="empty">Feedback recorded. Check the Ops Dashboard for FP monitoring.</div>';
    } catch (e) {
      toast(e.message, false);
    }
  }

  /* ---------------- incident report ---------------- */
  $("btnReport").addEventListener("click", openReport);
  $("btnCloseModal").addEventListener("click", () => $("modalBackdrop").classList.add("hidden"));
  $("modalBackdrop").addEventListener("click", (e) => { if (e.target.id === "modalBackdrop") $("modalBackdrop").classList.add("hidden"); });

  async function openReport() {
    if (!current) { toast("No transaction to report", false); return; }
    $("modalBackdrop").classList.remove("hidden");
    const b = current;
    let evidence = "No evidence captured.";
    try {
      const ev = await api(`/api/evidence/${b.txn_id}`);
      evidence = ev.entries.map(e => `  [${e.entry_type}] ${e.timestamp}\n    hash: ${e.hash.slice(0, 24)}…\n    ${JSON.stringify(e.payload).slice(0, 160)}`).join("\n");
    } catch (e) { /* keep default */ }

    const report = [
      "COMPLAINT DRAFT — CYBER CRIME REPORTING PORTAL (1930)",
      "========================================================",
      `Transaction ID     : ${b.txn_id}`,
      `Date               : ${new Date().toLocaleString("en-IN")}`,
      `Amount             : ${inr(b.transaction_amount || "")}`.replace(" ", " ") + " " + (currentScenario ? `(${currentScenario.payee})` : ""),
      `Risk score         : ${Math.round(b.risk_score)}/100 (${b.risk_level.toUpperCase()})`,
      `Decision           : ${b.decision.action} — hold ${b.decision.hold_hours}h`,
      `Evidence chain ref : ${b.evidence_id || "n/a"}`,
      `Bank alert ref     : ${b.bank_alert_id || "n/a"}`,
      "",
      "Signals detected (evidence-backed):",
      ...b.feature_breakdown.filter(f => f.contribution > 1).map(f => `  - ${f.reason}`),
      "",
      "Preserved evidence:",
      evidence,
      "",
      "Suggested next steps:",
      "  1. Lodge complaint at cybercrime.gov.in with this txn ID and evidence refs.",
      "  2. Freeze/verify the beneficiary account via your bank's fraud desk (1930).",
      "  3. Keep this hash-chain output as tamper-evident proof.",
    ].join("\n");

    $("reportBox").textContent = report;
  }

  $("btnCopyReport").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText($("reportBox").textContent);
      toast("Report copied to clipboard");
    } catch (e) {
      toast("Copy failed — select the text manually", false);
    }
  });

  /* ---------------- AI call intelligence ---------------- */
  let aiResultData = null;
  let conversationOverride = null;
  let liveListening = false;
  let liveRecognition = null;
  let liveTurns = [];
  let livePos = 0;
  let aiAnalyzeTimer = null;
  let llmStatus = { configured: false, model: null };
  let llmInFlight = false;

  async function refreshLlmStatus() {
    try {
      llmStatus = await api("/api/llm/status");
    } catch (e) { /* offline */ }
    const el = $("aiEngineStatus");
    if (llmStatus.configured) {
      el.className = "ai-engine-status on";
      el.innerHTML = `&#129504; AI agent ready: <b>${esc(llmStatus.model)}</b>`;
    } else {
      el.className = "ai-engine-status";
      el.innerHTML = "&#128279; LLM not configured — set PARAKH_LLM_API_KEY (NLP rules active)";
    }
  }

  $("aiEngine").addEventListener("change", () => {
    const mode = $("aiEngine").value;
    if (mode === "llm" && !llmStatus.configured) {
      toast("LLM not configured — set PARAKH_LLM_API_KEY and restart", false);
      $("aiEngine").value = "auto";
      return;
    }
    toast("Engine: " + mode.toUpperCase() + (mode === "auto" && llmStatus.configured ? " → " + llmStatus.model : ""));
  });

  function selectedEngine() {
    return $("aiEngine").value || "auto";
  }

  function buildLLMContext() {
    const s = currentScenario;
    if (!s) return null;
    return {
      transaction: {
        amount: s.amount, account_balance: s.balance,
        balance_after_tx: Math.max(0, s.balance - s.amount),
        txn_amount_30d_avg: s.avg, is_new_beneficiary: s.beneficiaryDays <= 1,
        beneficiary_added_days_ago: s.beneficiaryDays,
        beneficiary_previous_tx_count: s.beneficiaryDays > 30 ? 15 : s.beneficiaryDays > 1 ? 2 : 0,
      },
      call: {
        call_type: s.call.type, screen_share_active: s.call.share,
        caller_number_not_in_contacts: s.call.unknown,
      },
      device: { device_changed: s.key === "digital_arrest" || s.key === "bank_impersonation" },
      voice: s.voice.prob ? { acoustic_clone_probability: s.voice.prob, model_confidence: s.voice.conf } : {},
    };
  }

  function resetAI() {
    stopLiveListen(true);
    liveTurns = [];
    livePos = 0;
    aiResultData = null;
    conversationOverride = null;
    $("aiResult").classList.add("hidden");
    $("aiResult").innerHTML = "";
    $("aiLiveVerdict").innerHTML = '<span class="muted">Waiting for conversation&hellip;</span>';
    $("aiUploadStatus").innerHTML = "";
    $("aiUploadTranscript").value = "";
    $("aiTranscriptBox").value = "";
    $("aiFileLabel").textContent = "&#128228; Choose recording (wav / mp3 / webm / ogg)";
    $("aiFileInput").value = "";
  }

  document.querySelectorAll(".ai-tab").forEach(btn => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".ai-tab").forEach(b => b.classList.toggle("active", b === btn));
      document.querySelectorAll(".ai-panel").forEach(p => p.classList.add("hidden"));
      $("tab-" + btn.dataset.tab).classList.remove("hidden");
    });
  });

  function renderLiveVerdict(a) {
    const v = a.opinion.verdict;
    const conf = Math.round(a.opinion.confidence * 100);
    const cls = { FRAUD: "danger", SUSPICIOUS: "warn", LEGITIMATE: "good", INCONCLUSIVE: "info" }[v] || "info";
    const n = a.turn_count;
    const eng = a.engine === "llm"
      ? `<span class="ai-eng-chip llm" title="${esc(a.llm_model)}">LLM · ${Math.round((a.llm_latency_ms || 0) / 100) / 10}s</span>`
      : `<span class="ai-eng-chip">NLP</span>`;
    $("aiLiveVerdict").innerHTML = `
      ${eng}
      <span class="ai-pill ${cls}">${v}</span>
      <span class="muted">confidence ${conf}% &middot; ${n} turn${n === 1 ? "" : "s"} analyzed</span>
      <span class="ai-fraudmeter"><i style="width:${Math.round(a.fraud_score * 100)}%"></i></span>`;
  }

  function cueTags(cues) {
    const ICONS = {
      pressure: "&#9203;", secrecy: "&#128737;", authority: "&#9878;", credential: "&#128273;",
      payment_demand: "&#128176;", reward: "&#127942;", relative: "&#128104;&#8205;&#128105;",
      courier: "&#128230;", fear: "&#128561;", reassurance: "&#129309;", confirmation: "&#9989;",
    };
    return Object.entries(cues).map(([cat, hits]) =>
      `<span class="cue-tag" title="${esc(hits.join(", "))}">${ICONS[cat] || "&#128269;"} ${cat.replace(/_/g, " ")}</span>`).join("");
  }

  function renderAnalysis(a, note) {
    $("aiResult").classList.remove("hidden");
    aiResultData = a;
    const op = a.opinion;
    const cls = { FRAUD: "danger", SUSPICIOUS: "warn", LEGITIMATE: "good", INCONCLUSIVE: "info" }[op.verdict] || "info";
    const conf = Math.round(op.confidence * 100);
    const amt = a.entities.amounts.map(v => inr(v));
    const ents = `
      ${amt.length ? `<span class="ent-tag">&#128176; ${amt.join(" · ")}</span>` : ""}
      ${a.entities.otps.map(o => `<span class="ent-tag">&#128273; OTP ${esc(o)}</span>`).join("")}
      ${a.entities.phones.map(p => `<span class="ent-tag">&#128222; ${esc(p)}</span>`).join("")}
      ${a.entities.institutions.map(i => `<span class="ent-tag">&#127978; ${esc(i)}</span>`).join("")}`;
    const sent = (v) => v > 0.15 ? "&#128512; Positive" : v < -0.15 ? "&#128545; Stressed" : "&#128528; Neutral";

    $("aiResult").innerHTML = `
      <div class="ai-opinion ${cls}">
        <div class="ai-verdict"><span class="ai-pill ${cls} big">${op.verdict}</span>
          <span class="ai-conf">${conf}% confidence</span>
          ${a.engine === "llm"
            ? `<span class="ai-eng-chip llm" title="${esc(a.llm_model)}">&#129504; ${esc(a.llm_model)} &middot; ${Math.round((a.llm_latency_ms || 0) / 100) / 10}s</span>`
            : `<span class="ai-eng-chip">&#129504; NLP rules</span>`}
          <span class="ai-action">suggested action: <b>${esc(op.suggested_action)}</b></span>
        </div>
        <div class="ai-summary">${esc(op.summary)}</div>
        ${note ? `<div class="ai-note">${esc(note)}</div>` : ""}
      </div>
      <div class="ai-grid">
        <div class="ai-block">
          <div class="section-label">Fraud score</div>
          <div class="ai-scorebar"><i style="width:${Math.round(a.fraud_score * 100)}%"></i></div>
          <div class="ai-num">${Math.round(a.fraud_score * 100)} / 100</div>
        </div>
        <div class="ai-block">
          <div class="section-label">Detected intent</div>
          <div class="ai-intent">${esc(a.intent.display)}</div>
          <div class="muted">${a.intent.label} &middot; ${Math.round(a.intent.confidence * 100)}% match</div>
          ${a.active_patterns.length ? `<div class="ai-patterns">${a.active_patterns.map(p => `<span class="pat-tag">${esc(p)}</span>`).join("")}</div>` : ""}
        </div>
        <div class="ai-block">
          <div class="section-label">Speaker sentiment</div>
          <div>Caller: <b>${sent(a.sentiment.caller)}</b></div>
          <div>Victim: <b>${sent(a.sentiment.victim)}</b></div>
          <div class="muted">language: ${a.language.toUpperCase()} &middot; ${a.turn_count} turns</div>
        </div>
        <div class="ai-block">
          <div class="section-label">Entities extracted</div>
          <div>${ents || `<span class="muted">none</span>`}</div>
        </div>
      </div>
      <div class="ai-block mt-12">
        <div class="section-label">Red flags</div>
        <ul class="exp-list">${a.red_flags.map(f => `<li>${esc(f)}</li>`).join("")}</ul>
      </div>
      <div class="ai-turns mt-12">
        ${a.turns.map(t => `
          <div class="ai-turn ${t.speaker}">
            <span class="ai-who">${t.speaker === "caller" ? "&#128100;" : "&#129333;"} ${esc(t.speaker)}</span>
            <span class="ai-text">${esc(t.text)}</span>
            <span class="ai-tags">${cueTags(t.cues)}</span>
          </div>`).join("")}
      </div>
      <div class="btn-row mt-12">
        <button class="btn sm" id="aiApplyBtn">&#9889; Use Conversation in Risk Scoring</button>
        <button class="btn sm ghost" id="aiClearBtn">&#128260; Clear</button>
      </div>`;

    $("aiApplyBtn").addEventListener("click", applyConversation);
    $("aiClearBtn").addEventListener("click", () => {
      $("aiResult").classList.add("hidden");
      conversationOverride = null;
      toast("AI conversation cleared");
    });
  }

  function applyConversation() {
    if (!aiResultData || !aiResultData.turns.length) return;
    conversationOverride = {
      urgency_text: aiResultData.turns.map(t => t.text).join(" "),
      turns: aiResultData.turns,
      verdict: aiResultData.opinion.verdict,
      engine: aiResultData.engine,
    };
    $("payHint").textContent = llmStatus.configured
      ? "AI conversation applied — press Pay for engine + AI-agent review"
      : "AI conversation applied — press Pay to score with it";
    toast("Conversation fed into the risk engine" + (llmStatus.configured ? " + AI agent review" : ""));
  }

  function debouncedLiveAnalyze() {
    clearTimeout(aiAnalyzeTimer);
    aiAnalyzeTimer = setTimeout(() => {
      const turns = liveTurns.slice();
      if (!turns.length) return;
      api("/api/conversation/analyze", {
        method: "POST",
        body: JSON.stringify({ turns, source: "mic-live", engine: "nlp", persist: false }),
      }).then(a => {
        renderLiveVerdict(a);
        aiResultData = a;
      }).catch(() => {});
    }, 400);

    if ((selectedEngine() === "llm" || (selectedEngine() === "auto" && llmStatus.configured)) && !llmInFlight) {
      llmInFlight = true;
      setTimeout(() => {
        const turns = liveTurns.slice();
        if (!turns.length) { llmInFlight = false; return; }
        api("/api/conversation/analyze", {
          method: "POST",
          body: JSON.stringify({ turns, source: "mic-live", engine: "llm", context: buildLLMContext(), persist: false }),
        }).then(a => {
          renderLiveVerdict(a);
          aiResultData = a;
        }).catch(() => {}).finally(() => { llmInFlight = false; });
      }, 2600);
    }
  }

  function appendLiveLine(speaker, text) {
    const box = $("aiLiveBox");
    const div = document.createElement("div");
    div.className = "ai-live-line " + speaker;
    div.innerHTML = `<span class="ai-who">${speaker === "caller" ? "&#127908; Caller" : "&#129333; You"}</span>${esc(text)}`;
    box.appendChild(div);
    box.scrollTop = box.scrollHeight;
  }

  function startLiveListen() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) {
      toast("Live listen needs Chrome or Edge (Web Speech API)", false);
      return;
    }
    $("aiLiveBox").innerHTML = "";
    liveTurns = [];
    livePos = 0;
    liveRecognition = new SR();
    liveRecognition.lang = "en-IN";
    liveRecognition.continuous = true;
    liveRecognition.interimResults = false;
    liveRecognition.onresult = (e) => {
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const text = e.results[i][0].transcript.trim();
        if (!text) continue;
        liveTurns.push({ speaker: "caller", text });
        appendLiveLine("caller", text);
        debouncedLiveAnalyze();
      }
    };
    liveRecognition.onerror = (e) => {
      if (e.error !== "aborted" && e.error !== "no-speech") toast("Mic error: " + e.error, false);
      stopLiveListen();
    };
    liveRecognition.onend = () => { if (liveListening) liveRecognition.start(); };
    liveRecognition.start();
    liveListening = true;
    $("aiMicBtn").textContent = "&#9209; Stop Live Listen";
    toast("Listening — speak or play the call recording nearby");
  }

  function stopLiveListen(silent) {
    liveListening = false;
    if (liveRecognition) {
      try { liveRecognition.stop(); } catch (e) { /* ignore */ }
      liveRecognition = null;
    }
    $("aiMicBtn").textContent = "&#127908; Start Live Listen";
    if (!silent && liveTurns.length) {
      toast("Live listen stopped");
    }
  }

  $("aiMicBtn").addEventListener("click", () => {
    if (liveListening) stopLiveListen();
    else startLiveListen();
  });

  /* upload */
  $("aiFileInput").addEventListener("change", () => {
    const f = $("aiFileInput").files[0];
    $("aiFileLabel").textContent = f ? "&#128228; " + f.name + " (" + (f.size / 1024).toFixed(0) + " KB)" : "&#128228; Choose recording";
  });

  $("aiUploadBtn").addEventListener("click", async () => {
    const f = $("aiFileInput").files[0];
    if (!f) { toast("Choose a recording file first", false); return; }
    const fd = new FormData();
    fd.append("file", f);
    fd.append("engine", selectedEngine());
    const tr = $("aiUploadTranscript").value.trim();
    if (tr) fd.append("transcript", tr);
    const status = $("aiUploadStatus");
    status.innerHTML = '<span class="spinner"></span> uploading &amp; analyzing&hellip;';
    try {
      const res = await fetch(API_BASE + "/api/call/upload", { method: "POST", body: fd });
      const body = await res.json();
      if (!res.ok) throw new Error(body.detail || "Upload failed: " + res.status);
      if (body.analysis && body.analysis.opinion) {
        renderAnalysis(body.analysis, `Recording <b>${esc(body.filename)}</b> stored as ${body.recording_id} — analysis from attached transcript.`);
        status.innerHTML = `&#9989; Saved: <b>${esc(body.filename)}</b> &middot; ${(body.size_bytes / 1024).toFixed(1)} KB &middot; ${body.recording_id}`;
      } else {
        status.innerHTML = `&#9989; Recording saved (${esc(body.filename)}). No transcript attached — play it near the mic and press <b>Live Listen</b>, or paste the transcript below and re-upload.`;
      }
    } catch (e) {
      status.innerHTML = "";
      toast(e.message, false);
    }
  });

  /* transcript paste */
  const AI_SAMPLES = {
    digital_arrest: () => SCENARIOS.find(s => s.key === "digital_arrest").transcript.map(l => (l.who === "s" ? "Caller: " : "Victim: ") + l.text).join("\n"),
    bank_impersonation: () => SCENARIOS.find(s => s.key === "bank_impersonation").transcript.map(l => (l.who === "s" ? "Caller: " : "Victim: ") + l.text).join("\n"),
    lottery: () => SCENARIOS.find(s => s.key === "lottery_fraud").transcript.map(l => (l.who === "s" ? "Caller: " : "Victim: ") + l.text).join("\n"),
    relative_hi: () => SCENARIOS.find(s => s.key === "relative_emergency").transcript.map(l => (l.who === "s" ? "Caller: " : "Victim: ") + l.text).join("\n"),
    courier: () => SCENARIOS.find(s => s.key === "courier_drugs").transcript.map(l => (l.who === "s" ? "Caller: " : "Victim: ") + l.text).join("\n"),
    legit: () => SCENARIOS.find(s => s.key === "rent_payment").transcript.map(l => (l.who === "s" ? "Caller: " : "Victim: ") + l.text).join("\n"),
  };

  $("aiSample").addEventListener("change", () => {
    const key = $("aiSample").value;
    if (key && AI_SAMPLES[key]) $("aiTranscriptBox").value = AI_SAMPLES[key]();
  });

  $("aiAnalyzeBtn").addEventListener("click", async () => {
    const text = $("aiTranscriptBox").value.trim();
    if (!text) { toast("Paste a transcript first", false); return; }
    const turns = text.split("\n").map(l => l.trim()).filter(Boolean);
    $("aiAnalyzeBtn").disabled = true;
    try {
      const a = await api("/api/conversation/analyze", {
        method: "POST",
        body: JSON.stringify({ turns, source: "pasted", engine: selectedEngine(), context: buildLLMContext(), persist: true }),
      });
      renderAnalysis(a, `Transcript analyzed with ${a.engine === "llm" ? "the AI agent (LLM)." : "the NLP rules engine."}`);
    } catch (e) {
      toast(e.message, false);
    }
    $("aiAnalyzeBtn").disabled = false;
  });

  /* ---------------- init ---------------- */
  renderScenarios();
  selectScenario("digital_arrest");
})();