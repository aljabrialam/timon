const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => Array.from(document.querySelectorAll(sel));
const NA = "n/a";
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const money = (n) => (n == null || Number.isNaN(Number(n)) ? NA : new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 2 }).format(Number(n)));
const pct = (n, digits = 2) => (n == null || Number.isNaN(Number(n)) ? NA : `${Number(n) >= 0 ? "+" : ""}${Number(n).toFixed(digits)}%`);
const escape = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const tidy = (s) => String(s ?? "").replace(/\s*[\u2014\u2013]\s*/g, ", ").replace(/,\s*,/g, ",");
const when = (iso) => (iso ? tidy(String(iso).replace("T", " ").replace(/(\+.*|Z)$/, "").slice(0, 16)) : NA);
const clock = (stamp) => {
  const parts = String(stamp || "").split(" ");
  return parts.length > 1 ? parts.slice(1).join(" ") : NA;
};
const stamp = (iso) => {
  const t = new Date(iso);
  if (!iso || Number.isNaN(t.getTime())) return "no timestamp";
  const hh = String(t.getUTCHours()).padStart(2, "0");
  const mm = String(t.getUTCMinutes()).padStart(2, "0");
  return `${t.getUTCDate()} ${MONTHS[t.getUTCMonth()]} ${hh}:${mm} UTC`;
};

function setPill(el, text, tone = "") {
  el.textContent = String(text ?? NA);
  el.className = tone ? `pill ${tone}` : "pill";
}

function setTone(el, value, base) {
  el.className = `${base}${value > 0 ? " up" : value < 0 ? " down" : ""}`;
}

function renderStatus(d) {
  const s = d.session;
  setPill($("#session-name"), s.session, s.can_enter ? "ok" : "");
  $("#session-clock").textContent = `${clock(s.et)} / ${clock(s.sgt)}`;
  $("#session-rules").textContent = `entries ${s.can_enter ? "open" : "closed"} / flatten ${s.must_flatten ? "pending" : "no"} / ${tidy(s.reason)}`;

  const kill = d.kill;
  if (kill) {
    const action = String(kill.action || "").toUpperCase();
    const tone = /(HALT|FLATTEN|DISABLE|BLOCK)/.test(action) ? "bad" : /(OK|NONE|HOLD|CLEAR|PROCEED)/.test(action) ? "ok" : "warn";
    setPill($("#kill-action"), kill.action || NA, tone);
    $("#kill-reasons").textContent = tidy((kill.reasons || []).join(" / ")) || "no reasons logged";
    const ddLevel = kill.drawdown_pct == null || Number.isNaN(Number(kill.drawdown_pct)) ? NA : `${Math.abs(Number(kill.drawdown_pct)).toFixed(2)}%`;
    $("#kill-levels").textContent = `day ${pct(kill.day_pnl_pct)} / drawdown ${ddLevel}`;
  } else {
    setPill($("#kill-action"), "not evaluated", "");
    $("#kill-reasons").textContent = "no cycle has run";
    $("#kill-levels").textContent = NA;
  }

  const reg = d.regime;
  if (reg) {
    const tone = reg.regime === "RISK_ON" ? "ok" : reg.regime === "RISK_OFF" ? "bad" : reg.regime === "CHOP" ? "warn" : "dark";
    setPill($("#regime-name"), reg.regime, tone);
    $("#regime-evidence").textContent = tidy((reg.evidence || []).join(" / ")) || "no evidence logged";
  } else {
    setPill($("#regime-name"), "no snapshot", "");
    $("#regime-evidence").textContent = "needs a snapshot";
  }

  const led = d.ledger;
  setPill($("#ledger-state"), led.ok ? "verified" : "broken", led.ok ? "ok" : "bad");
  $("#ledger-count").textContent = `${led.entries} ${led.entries === 1 ? "record" : "records"}${led.broken_at ? `, broken at ${led.broken_at}` : ""}`;

  const acct = d.account;
  $("#footer-account").textContent = acct.configured
    ? `Account ${acct.id}. ${acct.env}.`
    : "Competition account ID not set. The executor refuses to trade.";

  const banner = $("#disarmed");
  if (acct.configured) {
    banner.hidden = true;
  } else {
    banner.hidden = false;
    $("#disarmed-reason").textContent = "config/account.yaml has no competition account ID, so the engine emits plans and places nothing.";
  }
}

function renderKpis(d) {
  const st = d.state || {};
  const metrics = d.metrics || {};
  const eq = Number(st.equity ?? 0);
  const start = Number(st.start_of_day_equity ?? eq);
  const dayPnl = eq - start;
  const dayPct = start ? (dayPnl / start) * 100 : 0;

  $("#kpi-equity").textContent = money(eq);
  $("#kpi-equity-sub").textContent = `start ${money(start)}`;
  $("#kpi-peak").textContent = money(st.peak_equity ?? eq);
  const dd = Number(d.equity && d.equity.max_drawdown_pct) || 0;
  $("#kpi-dd").textContent = dd > 0 ? `-${dd.toFixed(2)}%` : "0.00%";

  const dayEl = $("#kpi-day");
  dayEl.textContent = money(dayPnl);
  setTone(dayEl, dayPnl, "figure");

  const deltaEl = $("#kpi-day-pct");
  deltaEl.textContent = pct(dayPct);
  setTone(deltaEl, dayPct, "delta");
  $("#kpi-day-sub").textContent = `from ${money(start)} at the open`;

  $("#kpi-trades").textContent = String(metrics.trades ?? 0);
  $("#kpi-winrate").textContent = metrics.trades ? `${((Number(metrics.win_rate) || 0) * 100).toFixed(1)}% win rate` : "no closed trades yet";
  $("#kpi-exp").textContent = money(metrics.expectancy_usd);
  setTone($("#kpi-exp"), Number(metrics.expectancy_usd) || 0, "perf-val");
  $("#kpi-avgwin").textContent = metrics.trades ? `win ${money(metrics.avg_win)} / loss ${money(metrics.avg_loss)}` : NA;
  $("#kpi-r").textContent = metrics.avg_r == null ? NA : Number(metrics.avg_r).toFixed(2);
  $("#kpi-sharpe").textContent = metrics.sharpe_annualised == null ? "sharpe pending" : `sharpe ${metrics.sharpe_annualised}`;
}

let range = "all";

function rangePoints(all) {
  if (range === "all") return all;
  return all.slice(-Number(range));
}

function renderChart(d) {
  const host = $("#chart");
  const note = $("#chart-note");
  const all = ((d.equity && d.equity.points) || []).slice();

  if (!all.length) {
    host.innerHTML = '<p class="empty">No equity history. The first closed trade adds a point.</p>';
    note.textContent = "";
    return;
  }

  const points = rangePoints(all);
  const first = points[0].date;
  const last = points[points.length - 1].date;
  const lastPoint = points[points.length - 1];
  const single = points.length === 1;

  note.textContent = single
    ? `flat at ${money(lastPoint.equity)}. No closed trades yet.`
    : `${first} to ${last}, ${points.length} points`;

  const w = Math.max(Math.round(host.clientWidth) || 600, 260);
  const h = Math.max(Math.round(host.clientHeight) || 240, 200);
  const compact = w < 520;
  const pad = { top: 42, right: 12, bottom: 44, left: compact ? 50 : 62 };
  const values = points.map((p) => Number(p.equity));
  let lo = Math.min(...values);
  let hi = Math.max(...values);
  if (hi === lo) {
    const span = Math.max(Math.abs(hi) * 0.004, 1);
    lo -= span;
    hi += span;
  }

  const plotW = w - pad.left - pad.right;
  const base = h - pad.bottom;
  const x = (i) => pad.left + (points.length === 1 ? plotW / 2 : (i / (points.length - 1)) * plotW);
  const y = (v) => pad.top + (1 - (v - lo) / (hi - lo)) * (h - pad.top - pad.bottom);
  const axis = (v) => (compact ? `$${(v / 1000).toFixed(1)}k` : Math.round(v).toLocaleString("en-US"));

  const ticks = [hi, (hi + lo) / 2, lo];
  const gridlines = ticks
    .map((v) => `<line class="gridline" x1="${pad.left}" x2="${w - pad.right}" y1="${y(v).toFixed(1)}" y2="${y(v).toFixed(1)}"/>`)
    .join("");
  const tickLabels = ticks
    .map((v) => `<text class="axis-label" x="${pad.left - 9}" y="${(y(v) + 3.3).toFixed(1)}" text-anchor="end">${escape(axis(v))}</text>`)
    .join("");

  const stems = single
    ? ""
    : points
        .map((p, i) => {
          const px = x(i).toFixed(1);
          return `<line class="stem" x1="${px}" x2="${px}" y1="${base.toFixed(1)}" y2="${y(Number(p.equity)).toFixed(1)}"/>`;
        })
        .join("");

  const dots = points
    .map((p, i) => {
      const isLast = i === points.length - 1;
      return `<circle class="dot" cx="${x(i).toFixed(1)}" cy="${y(Number(p.equity)).toFixed(1)}" r="${isLast ? 4.2 : 3.2}"><title>${escape(p.date)}: ${money(p.equity)}</title></circle>`;
    })
    .join("");

  const flat = single
    ? `<line class="flat" x1="${pad.left}" x2="${w - pad.right}" y1="${y(Number(lastPoint.equity)).toFixed(1)}" y2="${y(Number(lastPoint.equity)).toFixed(1)}"/>`
    : "";

  const chipLabel = money(lastPoint.equity);
  const chipW = Math.max(58, chipLabel.length * 6.1 + 18);
  const lastX = x(points.length - 1);
  const lastY = y(Number(lastPoint.equity));
  const chipX = Math.min(Math.max(lastX - chipW / 2, pad.left - 4), w - chipW - 4);
  const chipY = Math.max(2, lastY - 36);
  const chip = `
    <g class="chip">
      <rect x="${chipX.toFixed(1)}" y="${chipY.toFixed(1)}" width="${chipW.toFixed(1)}" height="22" rx="8"/>
      <text x="${(chipX + chipW / 2).toFixed(1)}" y="${(chipY + 15).toFixed(1)}" text-anchor="middle">${escape(chipLabel)}</text>
    </g>`;

  const maxPills = w < 420 ? 3 : w < 640 ? 4 : 5;
  const picked = [];
  if (points.length <= maxPills) {
    points.forEach((_, i) => picked.push(i));
  } else {
    for (let k = 0; k < maxPills; k += 1) picked.push(Math.round((k * (points.length - 1)) / (maxPills - 1)));
  }
  const datePills = [...new Set(picked)]
    .map((i) => {
      const text = escape(points[i].date.slice(5));
      const pw = 40;
      const px = Math.min(Math.max(x(i) - pw / 2, 2), w - pw - 2);
      const py = h - 28;
      const on = i === points.length - 1 ? " on" : "";
      return `<g class="date-pill${on}"><rect x="${px.toFixed(1)}" y="${py}" width="${pw}" height="22" rx="11"/><text x="${(px + pw / 2).toFixed(1)}" y="${py + 14.5}" text-anchor="middle">${text}</text></g>`;
    })
    .join("");

  const aria = `Equity curve, ${points.length} ${points.length === 1 ? "point" : "points"}, ${first} to ${last}, latest ${money(lastPoint.equity)}`;

  host.innerHTML = `
    <svg viewBox="0 0 ${w} ${h}" width="${w}" height="${h}" role="img" aria-label="${escape(aria)}">
      ${gridlines}
      ${tickLabels}
      ${flat}
      ${stems}
      ${dots}
      ${chip}
      ${datePills}
    </svg>`;
}

function renderPositions(d) {
  const rows = (d.state && d.state.positions) || [];
  $("#positions-note").textContent = rows.length ? `${rows.length} open` : "flat";
  $("#positions").closest("table").classList.toggle("is-empty", !rows.length);
  $("#positions").innerHTML = rows.length
    ? rows
        .map((p) => `<tr><td><span class="sym">${escape(p.symbol)}</span></td><td class="num">${escape(p.qty)}</td><td class="num">${money(p.market_value)}</td></tr>`)
        .join("")
    : '<tr><td colspan="3" class="empty">Flat. No open exposure.</td></tr>';
}

function renderProposals(d) {
  const rows = (d.plan && d.plan.shadow) || [];
  $("#proposals").closest("table").classList.toggle("is-empty", !rows.length);
  $("#proposals").innerHTML = rows.length
    ? rows
        .map((s) => `<tr><td><span class="sym">${escape(s.symbol)}</span></td><td class="num">${money(s.entry)}</td><td class="num">${money(s.stop)}</td><td class="num">${money(s.target)}</td></tr>`)
        .join("")
    : `<tr><td colspan="4" class="empty">${d.plan ? "No opening-range break in this snapshot." : "No snapshot yet. Export one with --snapshot."}</td></tr>`;
}

function verdictTag(v) {
  const cls = ["APPROVE", "SHRINK"].includes(v) ? "ok" : v === "ESCALATE" ? "warn" : v === "HOLD" ? "" : "bad";
  return `<span class="pill ${cls}">${escape(v)}</span>`;
}

function renderVerdicts(d) {
  const rows = d.verdicts || [];
  $("#verdicts-body").closest("table").classList.toggle("is-empty", !rows.length);
  $("#verdicts-body").innerHTML = rows.length
    ? rows
        .map((r) => {
          const failed = (r.failed_checks || r.reasons || []).join(" / ");
          return `<tr><td>${when(r.ts)}</td><td><span class="sym">${escape(r.symbol)}</span></td><td>${verdictTag(r.verdict)}</td><td class="num">${escape(r.qty ?? NA)}</td><td class="num">${money(r.risk_usd)}</td><td>${escape(failed) || NA}</td></tr>`;
        })
        .join("")
    : '<tr><td colspan="6" class="empty">No verdicts logged. The first cycle will appear here.</td></tr>';
}

function renderBudget(d) {
  const st = d.state || {};
  const l = d.limits || {};
  const entries = Number(st.entries_today ?? 0);
  const orders = Number(st.orders_today ?? 0);
  const eq = Number(st.equity ?? 0);
  const start = Number(st.start_of_day_equity ?? eq);
  const dayPct = start ? ((eq - start) / start) * 100 : 0;
  const used = Math.max(0, -dayPct);
  const halt = Number(l.daily_loss_halt_pct ?? 0);
  const maxEntries = Number(l.max_new_entries_per_day ?? 0);
  const maxOrders = Number(l.max_orders_per_day ?? 0);

  $("#budget-entries-val").textContent = `${entries} / ${maxEntries}`;
  $("#budget-orders-val").textContent = `${orders} / ${maxOrders}`;
  $("#budget-loss-val").textContent = halt > 0 ? `${used.toFixed(2)}% / ${halt.toFixed(2)}%` : NA;

  const fill = (sel, value, max, extra = "") => {
    const host = $(sel);
    host.innerHTML = "";
    const on = max > 0 ? Math.min(20, Math.max(0, Math.round((value / max) * 20))) : 0;
    for (let i = 0; i < 20; i += 1) {
      const tick = document.createElement("span");
      tick.className = `tick${extra ? ` ${extra}` : ""}${i < on ? " on" : ""}`;
      host.appendChild(tick);
    }
  };

  fill("#budget-entries-ticks", entries, maxEntries);
  fill("#budget-orders-ticks", orders, maxOrders);
  fill("#budget-loss-ticks", used, halt, "loss");
}

function renderLimits(d) {
  const l = d.limits || {};
  const gross = l.gross_cap_pct || {};
  const val = (v, suffix = "") => (v == null ? NA : `${v}${suffix}`);
  const rows = [
    ["Risk / trade", val(l.risk_per_trade_pct, "%")],
    ["Position cap", val(l.max_position_notional_pct, "%")],
    ["Gross cap", gross.RISK_ON == null ? NA : `${gross.RISK_ON} / ${gross.RISK_OFF} / ${gross.CHOP}%`],
    ["Entries / day", val(l.max_new_entries_per_day)],
    ["Orders / day", val(l.max_orders_per_day)],
    ["Entry cutoff", l.entry_cutoff_et ? `${l.entry_cutoff_et} ET` : NA],
    ["Flatten by", l.eod_flatten_et ? `${l.eod_flatten_et} ET` : NA],
    ["Day halt", val(l.daily_loss_halt_pct, "%")],
    ["Flatten at", val(l.drawdown_flatten_pct, "%")],
    ["Target", val(l.target_r, "R")],
    ["Autonomy", l.stage == null ? NA : `stage ${l.stage}`],
  ];
  $("#limits").innerHTML = rows.map(([k, v]) => `<div class="limit"><dt>${escape(k)}</dt><dd>${escape(v)}</dd></div>`).join("");
}

function renderUniverse(d) {
  const symbols = d.universe || [];
  $("#universe").innerHTML = symbols.length
    ? `<span class="universe-label">Universe</span>${symbols.map((s) => `<span class="sym-chip">${escape(s)}</span>`).join("")}`
    : "";
}

function renderRecent(d) {
  const rows = d.recent || [];
  $("#recent").innerHTML = rows.length
    ? rows
        .map((r) => {
          const label = r.symbol || r.session || r.type || "";
          const extra = r.verdict || r.action || r.reason || "";
          const text = tidy(extra ? `${label} / ${extra}` : label);
          return `<li><div class="log-top"><span class="log-when">${when(r.ts)}</span><span class="log-type">${escape(r.type)}</span></div><p class="log-text">${escape(text) || NA}</p></li>`;
        })
        .join("")
    : '<li class="log-empty">The ledger is empty until the first cycle is logged.</li>';
}

function render(d) {
  renderStatus(d);
  renderKpis(d);
  renderChart(d);
  renderPositions(d);
  renderProposals(d);
  renderVerdicts(d);
  renderBudget(d);
  renderLimits(d);
  renderUniverse(d);
  renderRecent(d);

  const g = $("#generated");
  g.textContent = stamp(d.generated_at);
  g.title = `Data exported ${when(d.generated_at)} UTC`;
  g.classList.remove("is-error");
  $("#error").hidden = true;
  document.documentElement.dataset.ready = "true";
}

let current = null;
let busy = false;

function showError(message) {
  $("#error").hidden = false;
  $("#error-text").textContent = message;
  const g = $("#generated");
  g.textContent = "data unavailable";
  g.classList.add("is-error");
}

async function load() {
  if (busy) return;
  busy = true;
  const button = $("#refresh");
  button.setAttribute("aria-busy", "true");

  try {
    const res = await fetch("./data.json", { cache: "no-store" });
    if (!res.ok) throw new Error(`data.json returned ${res.status}`);
    const data = await res.json();
    current = data;
    render(data);
  } catch (err) {
    showError(`Could not load dashboard data. ${err.message}`);
    console.error(err);
  } finally {
    busy = false;
    button.removeAttribute("aria-busy");
  }
}

$$("[data-range]").forEach((btn) => {
  btn.addEventListener("click", () => {
    range = btn.dataset.range;
    $$("[data-range]").forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
    if (current) renderChart(current);
  });
});

$("#refresh").addEventListener("click", load);
$("#retry").addEventListener("click", load);

let resizeFrame;
window.addEventListener("resize", () => {
  if (!current) return;
  cancelAnimationFrame(resizeFrame);
  resizeFrame = requestAnimationFrame(() => renderChart(current));
});

const navLinks = $$(".nav a");
const navTargets = navLinks.map((a) => document.querySelector(a.getAttribute("href"))).filter(Boolean);
if ("IntersectionObserver" in window && navTargets.length) {
  const setActive = (id) => {
    navLinks.forEach((a) => {
      const on = a.getAttribute("href") === `#${id}`;
      a.classList.toggle("is-active", on);
      if (on) a.setAttribute("aria-current", "page");
      else a.removeAttribute("aria-current");
    });
  };
  const io = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          setActive(entry.target.id);
          break;
        }
      }
    },
    { rootMargin: "-25% 0px -60% 0px" }
  );
  navTargets.forEach((t) => io.observe(t));
}

if (document.fonts && document.fonts.ready) {
  document.fonts.ready.then(() => {
    if (current) renderChart(current);
  });
}

load();
