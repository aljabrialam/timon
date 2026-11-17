const $ = (sel) => document.querySelector(sel);
const money = (n) => (n == null ? "—" : new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(n));
const pct = (n, digits = 2) => (n == null ? "—" : `${n >= 0 ? "+" : ""}${n.toFixed(digits)}%`);
const escape = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const when = (iso) => (iso ? String(iso).replace("T", " ").replace(/(\+.*|Z)$/, "").slice(0, 16) : "—");

function tone(el, value) {
  el.classList.remove("up", "down");
  if (value > 0) el.classList.add("up");
  if (value < 0) el.classList.add("down");
}

function renderStatus(d) {
  const s = d.session;
  $("#session-name").textContent = s.session;
  $("#session-clock").textContent = `${s.et} · ${s.sgt.replace(/^\d{4}-\d{2}-\d{2} /, "")}`;
  $("#session-rules").textContent = `entries ${s.can_enter ? "open" : "closed"} · flatten ${s.must_flatten ? "pending" : "no"} · ${s.reason}`;

  const kill = d.kill;
  $("#kill-action").textContent = kill ? kill.action : "not evaluated";
  $("#kill-reasons").textContent = kill ? kill.reasons.join(" · ") : "no cycle has run";
  $("#kill-levels").textContent = kill ? `day ${pct(kill.day_pnl_pct)} · drawdown ${pct(kill.drawdown_pct)}` : "—";

  const reg = d.regime;
  $("#regime-name").textContent = reg ? reg.regime : "—";
  $("#regime-evidence").textContent = reg ? reg.evidence.join(" · ") : "needs a snapshot";

  const led = d.ledger;
  const ledEl = $("#ledger-state");
  ledEl.textContent = led.ok ? "verified" : "BROKEN";
  ledEl.className = "value";
  ledEl.classList.add(led.ok ? "up" : "down");
  $("#ledger-count").textContent = `${led.entries} ${led.entries === 1 ? "record" : "records"}${led.broken_at ? ` · broken at ${led.broken_at}` : ""}`;

  const acct = d.account;
  $("#footer-account").textContent = acct.configured
    ? `Account ${acct.id} · ${acct.env}`
    : "Competition account ID not set — the executor refuses to trade.";

  const banner = $("#disarmed");
  if (acct.configured) {
    banner.hidden = true;
  } else {
    banner.hidden = false;
    $("#disarmed-reason").textContent = "config/account.yaml has no competition account ID, so the engine emits plans and places nothing.";
  }
}

function renderKpis(d) {
  const { state, metrics, equity } = d;
  const dayPnl = (state.equity ?? 0) - (state.start_of_day_equity ?? state.equity ?? 0);

  $("#kpi-equity").textContent = money(state.equity);
  $("#kpi-equity-sub").textContent = `peak ${money(state.peak_equity)}`;

  const dayEl = $("#kpi-day");
  dayEl.textContent = money(dayPnl);
  tone(dayEl, dayPnl);
  $("#kpi-day-sub").textContent = `from ${money(state.start_of_day_equity)}`;

  $("#kpi-dd").textContent = pct(-equity.max_drawdown_pct);
  $("#kpi-trades").textContent = String(metrics.trades);
  $("#kpi-winrate").textContent = metrics.trades ? `${(metrics.win_rate * 100).toFixed(1)}% win rate` : "no closed trades";
  $("#kpi-exp").textContent = money(metrics.expectancy_usd);
  tone($("#kpi-exp"), metrics.expectancy_usd);
  $("#kpi-avgwin").textContent = metrics.trades ? `avg win ${money(metrics.avg_win)} · loss ${money(metrics.avg_loss)}` : "—";
  $("#kpi-r").textContent = metrics.avg_r == null ? "—" : metrics.avg_r.toFixed(2);
  $("#kpi-sharpe").textContent = metrics.sharpe_annualised == null ? "sharpe pending" : `sharpe ${metrics.sharpe_annualised}`;
}

function renderChart(d) {
  const host = $("#chart");
  const points = d.equity.points || [];
  const note = $("#chart-note");

  if (!points.length) {
    host.innerHTML = '<p class="empty">No equity history.</p>';
    note.textContent = "";
    return;
  }

  const single = points.length === 1;
  note.textContent = single
    ? `flat at ${money(points[0].equity)} — no closed trades yet`
    : `${points[0].date} → ${points[points.length - 1].date}`;

  const w = Math.max(host.clientWidth || 720, 320);
  const h = 220;
  const pad = { top: 14, right: 12, bottom: 22, left: 62 };
  const values = points.map((p) => p.equity);
  let lo = Math.min(...values);
  let hi = Math.max(...values);
  if (hi === lo) {
    const padY = Math.max(Math.abs(hi) * 0.01, 1);
    lo -= padY;
    hi += padY;
  }
  const x = (i) => pad.left + (i / Math.max(points.length - 1, 1)) * (w - pad.left - pad.right);
  const y = (v) => pad.top + (1 - (v - lo) / (hi - lo)) * (h - pad.top - pad.bottom);

  const line = points.map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(p.equity).toFixed(1)}`).join(" ");
  const area = `${line} L${x(points.length - 1).toFixed(1)},${(h - pad.bottom).toFixed(1)} L${x(0).toFixed(1)},${(h - pad.bottom).toFixed(1)} Z`;

  const ticks = [hi, (hi + lo) / 2, lo];
  const gridlines = ticks
    .map((v) => `<line class="gridline" x1="${pad.left}" x2="${w - pad.right}" y1="${y(v).toFixed(1)}" y2="${y(v).toFixed(1)}"/>`)
    .join("");
  const labels = ticks
    .map((v) => `<text x="${pad.left - 8}" y="${(y(v) + 3.5).toFixed(1)}" text-anchor="end">${Math.round(v).toLocaleString("en-US")}</text>`)
    .join("");

  const first = points[0].date;
  const last = points[points.length - 1].date;
  const xLabels = single
    ? `<text x="${x(0).toFixed(1)}" y="${h - 4}" text-anchor="middle">${escape(first)}</text>`
    : `<text x="${pad.left}" y="${h - 4}">${escape(first)}</text><text x="${w - pad.right}" y="${h - 4}" text-anchor="end">${escape(last)}</text>`;

  const dot = `<circle class="dot" cx="${x(points.length - 1).toFixed(1)}" cy="${y(points[points.length - 1].equity).toFixed(1)}" r="3.5"/>`;

  host.innerHTML = `
    <svg viewBox="0 0 ${w} ${h}" role="img" aria-label="Equity curve from ${escape(first)} to ${escape(last)}">
      <defs>
        <linearGradient id="fill" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stop-color="#d7a24a" stop-opacity="0.22"/>
          <stop offset="100%" stop-color="#d7a24a" stop-opacity="0"/>
        </linearGradient>
      </defs>
      ${gridlines}
      <line class="axis" x1="${pad.left}" x2="${w - pad.right}" y1="${h - pad.bottom}" y2="${h - pad.bottom}"/>
      ${labels}
      ${xLabels}
      ${single ? `<line class="line" x1="${pad.left}" x2="${w - pad.right}" y1="${y(points[0].equity).toFixed(1)}" y2="${y(points[0].equity).toFixed(1)}" stroke-dasharray="3 5"/>` : `<path class="area" d="${area}"/><path class="line" d="${line}"/>`}
      ${dot}
    </svg>`;
}

function renderPositions(d) {
  const rows = d.state.positions || [];
  const body = $("#positions");
  $("#positions-note").textContent = `${rows.length} open`;
  body.innerHTML = rows.length
    ? rows.map((p) => `<tr><td><span class="sym">${escape(p.symbol)}</span></td><td class="num">${escape(p.qty)}</td><td class="num">${money(p.market_value)}</td></tr>`).join("")
    : '<tr><td colspan="3" class="empty">Flat. No open exposure.</td></tr>';
}

function renderProposals(d) {
  const rows = (d.plan && d.plan.shadow) || [];
  const body = $("#proposals");
  body.innerHTML = rows.length
    ? rows.map((s) => `<tr><td><span class="sym">${escape(s.symbol)}</span></td><td class="num">${money(s.entry)}</td><td class="num">${money(s.stop)}</td><td class="num">${money(s.target)}</td></tr>`).join("")
    : `<tr><td colspan="4" class="empty">${d.plan ? "No opening-range break in this snapshot." : "No snapshot yet — export one with --snapshot."}</td></tr>`;
}

function verdictPill(v) {
  const cls = ["APPROVE", "SHRINK"].includes(v) ? "ok" : v === "ESCALATE" ? "warn" : "bad";
  return `<span class="pill ${cls}">${escape(v)}</span>`;
}

function renderVerdicts(d) {
  const rows = d.verdicts || [];
  const body = $("#verdicts");
  body.innerHTML = rows.length
    ? rows
        .map((r) => {
          const failed = (r.failed_checks || r.reasons || []).join(" · ");
          return `<tr><td>${when(r.ts)}</td><td><span class="sym">${escape(r.symbol)}</span></td><td>${verdictPill(r.verdict)}</td><td class="num">${escape(r.qty ?? "—")}</td><td class="num">${money(r.risk_usd)}</td><td class="muted">${escape(failed) || "—"}</td></tr>`;
        })
        .join("")
    : '<tr><td colspan="6" class="empty">No verdicts logged. The first cycle will appear here.</td></tr>';
}

function renderLimits(d) {
  const l = d.limits;
  const rows = [
    ["Risk per trade", `${l.risk_per_trade_pct}%`],
    ["Position cap", `${l.max_position_notional_pct}%`],
    ["Gross cap", `${l.gross_cap_pct.RISK_ON}% / ${l.gross_cap_pct.CHOP}%`],
    ["Entries / day", String(l.max_new_entries_per_day)],
    ["Orders / day", String(l.max_orders_per_day)],
    ["Entry cutoff", `${l.entry_cutoff_et} ET`],
    ["Flatten by", `${l.eod_flatten_et} ET`],
    ["Target", `${l.target_r}R`],
    ["Autonomy", `stage ${l.stage}`],
  ];
  $("#limits").innerHTML = rows.map(([k, v]) => `<dt>${escape(k)}</dt><dd>${escape(v)}</dd>`).join("");
}

function renderRecent(d) {
  const rows = d.recent || [];
  $("#recent").innerHTML = rows.length
    ? rows
        .map((r) => {
          const label = r.symbol || r.session || r.type;
          const extra = r.verdict || r.action || r.reason || "";
          return `<li><span>${when(r.ts)}</span><span class="type">${escape(r.type)}</span><span>${escape(label)}${extra ? ` · ${escape(extra)}` : ""}</span></li>`;
        })
        .join("")
    : '<li><span>—</span><span class="type">empty</span><span>The ledger is empty until the first cycle is logged.</span></li>';
}

function render(d) {
  renderStatus(d);
  renderKpis(d);
  renderChart(d);
  renderPositions(d);
  renderProposals(d);
  renderVerdicts(d);
  renderLimits(d);
  renderRecent(d);

  $("#generated").textContent = `exported ${when(d.generated_at)}`;
  document.documentElement.dataset.ready = "true";
}

let current = null;

async function load() {
  try {
    const res = await fetch("./data.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`data.json ${res.status}`);
    current = await res.json();
    render(current);
  } catch (err) {
    $("#generated").textContent = "data unavailable";
    console.error(err);
  }
}

$("#refresh").addEventListener("click", load);
window.addEventListener("resize", () => {
  if (current) renderChart(current);
});
load();
