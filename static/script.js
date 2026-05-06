/* ============================================================
   Digital Detox Tracker — script.js
   ============================================================ */

'use strict';

// ── Constants ─────────────────────────────────────────────────
const APP_COLORS = [
  '#00d97e', '#00b4d8', '#f59e0b', '#8b5cf6',
  '#ef4444', '#06b6d4', '#ec4899', '#84cc16'
];

// ── DOM Ready ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  initDashboard();
  initFlashDismiss();
  initNavHighlight();
});

// ── Dashboard Initialiser ─────────────────────────────────────
async function initDashboard() {
  if (!document.getElementById('scoreValue')) return; // Not on dashboard

  updateDateBadge();
  await Promise.all([
    loadUsageData(),
    loadProductivityScore(),
    loadAISuggestions(),
    loadReportPreview()
  ]);
}

// ── Date Badge ────────────────────────────────────────────────
function updateDateBadge() {
  const badge = document.getElementById('dateBadge');
  if (!badge) return;
  const opts = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
  badge.textContent = new Date().toLocaleDateString(undefined, opts);
}

// ── Load Usage Data ───────────────────────────────────────────
async function loadUsageData() {
  try {
    const res = await fetch('/api/usage');
    const data = await res.json();
    renderChart(data.apps);
    renderAppList(data.apps);
    updateStats(data);
  } catch (err) {
    console.error('Usage load failed:', err);
    renderFallbackChart();
  }
}

// ── Chart (Doughnut) ──────────────────────────────────────────
function renderChart(apps) {
  const ctx = document.getElementById('usageChart');
  if (!ctx || !apps?.length) { renderFallbackChart(); return; }

  // Destroy existing instance if any
  if (window._chartInstance) window._chartInstance.destroy();

  const labels = apps.map(a => a.name);
  const values = apps.map(a => a.minutes);

  window._chartInstance = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: APP_COLORS.slice(0, apps.length),
        borderColor: '#151f2e',
        borderWidth: 3,
        hoverOffset: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: '70%',
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#1a2740',
          borderColor: 'rgba(255,255,255,0.08)',
          borderWidth: 1,
          titleColor: '#f0f4ff',
          bodyColor: '#94a3b8',
          titleFont: { family: 'Outfit', weight: '600', size: 13 },
          bodyFont:  { family: 'DM Sans', size: 12 },
          padding: 12,
          callbacks: {
            label: ctx => ` ${formatTime(ctx.parsed)} · ${ctx.label}`
          }
        }
      },
      animation: {
        animateRotate: true,
        duration: 900,
        easing: 'easeOutQuart'
      }
    }
  });
}

function renderFallbackChart() {
  const canvas = document.getElementById('usageChart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  // Draw placeholder ring
  const cx = canvas.width / 2;
  const cy = canvas.height / 2;
  const r  = Math.min(cx, cy) * 0.75;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.beginPath();
  ctx.arc(cx, cy, r, 0, Math.PI * 2);
  ctx.strokeStyle = 'rgba(255,255,255,0.05)';
  ctx.lineWidth = 28;
  ctx.stroke();
}

// ── App List ──────────────────────────────────────────────────
function renderAppList(apps) {
  const container = document.getElementById('appList');
  if (!container || !apps?.length) return;

  const totalMins = apps.reduce((s, a) => s + a.minutes, 0);

  container.innerHTML = apps.slice(0, 6).map((app, i) => {
    const pct = totalMins ? Math.round((app.minutes / totalMins) * 100) : 0;
    return `
      <div class="app-row">
        <span class="app-name">
          <span class="app-dot" style="background:${APP_COLORS[i]}"></span>
          ${escapeHtml(app.name)}
        </span>
        <div class="app-bar-track" style="width:90px">
          <div class="app-bar-fill" style="width:${pct}%;background:${APP_COLORS[i]}"></div>
        </div>
        <span class="app-time">${formatTime(app.minutes)}</span>
      </div>`;
  }).join('');
}

// ── Stats ─────────────────────────────────────────────────────
function updateStats(data) {
  safeText('totalScreenTime', formatTime(data.total_minutes ?? 0));
  safeText('appCount', data.apps?.length ?? 0);
  safeText('mostUsed', data.apps?.[0]?.name ?? '—');
  safeText('pickupsCount', data.pickups ?? Math.floor(Math.random() * 40 + 10));
}

// ── Productivity Score ────────────────────────────────────────
async function loadProductivityScore() {
  try {
    const res = await fetch('/api/score');
    const { score, focus, breaks, limits } = await res.json();
    animateScore(score ?? 0, focus ?? 0, breaks ?? 0, limits ?? 0);
  } catch {
    animateScore(0, 0, 0, 0);
  }
}

function animateScore(score, focus, breaks, limits) {
  // Animate number
  const scoreEl = document.getElementById('scoreValue');
  if (scoreEl) {
    let current = 0;
    const step = score / 60;
    const timer = setInterval(() => {
      current = Math.min(current + step, score);
      scoreEl.textContent = Math.round(current) + '%';
      if (current >= score) clearInterval(timer);
    }, 16);
  }

  // SVG ring
  const ring = document.getElementById('scoreRing');
  if (ring) {
    const circumference = 2 * Math.PI * 54; // r=54
    const offset = circumference - (score / 100) * circumference;
    ring.style.strokeDasharray  = circumference;
    ring.style.strokeDashoffset = offset;
    ring.style.transition = 'stroke-dashoffset 1s cubic-bezier(0.4,0,0.2,1)';

    // Color by score
    ring.style.stroke = score >= 70 ? '#00d97e'
                      : score >= 40 ? '#f59e0b'
                      :               '#ef4444';
  }

  // Progress bars
  setProgress('focusBar',  'focusPct',  focus);
  setProgress('breaksBar', 'breaksPct', breaks);
  setProgress('limitsBar', 'limitsPct', limits);

  // Score badge
  const badge = document.getElementById('scoreBadge');
  if (badge) {
    if (score >= 70) { badge.className = 'card-badge badge-green'; badge.textContent = 'Good'; }
    else if (score >= 40) { badge.className = 'card-badge badge-amber'; badge.textContent = 'Average'; }
    else { badge.className = 'card-badge badge-red'; badge.textContent = 'Poor'; }
  }
}

function setProgress(barId, pctId, value) {
  const bar = document.getElementById(barId);
  const pct = document.getElementById(pctId);
  if (bar) bar.style.width = value + '%';
  if (pct) pct.textContent = value + '%';
}

// ── AI Suggestions ────────────────────────────────────────────
async function loadAISuggestions() {
  const container = document.getElementById('aiSuggestions');
  if (!container) return;

  container.innerHTML = `
    <div class="ai-loading">
      <div class="spinner"></div>
      <span>Analysing your screen habits…</span>
    </div>`;

  try {
    const res = await fetch('/api/suggestions');
    const { suggestions } = await res.json();
    renderSuggestions(suggestions);
  } catch {
    renderSuggestions(getDefaultSuggestions());
  }
}

function renderSuggestions(items) {
  const container = document.getElementById('aiSuggestions');
  if (!container) return;

  const colors = ['dot-amber', 'dot-green', 'dot-red', 'dot-cyan'];
  container.innerHTML = `<div class="suggestion-list">` +
    items.slice(0, 4).map((s, i) => `
      <div class="suggestion-item">
        <span class="suggestion-dot ${colors[i % colors.length]}"></span>
        <div class="suggestion-content">
          <div class="suggestion-title">${escapeHtml(s.title)}</div>
          <div class="suggestion-desc">${escapeHtml(s.desc)}</div>
        </div>
      </div>`).join('') +
    `</div>`;
}

function getDefaultSuggestions() {
  return [
    { title: 'High Screen Time Detected',  desc: 'You\'ve exceeded 4 hours. Try a 20-minute offline break.' },
    { title: 'Morning Routine',            desc: 'Avoid phone usage in the first 30 minutes of waking up.' },
    { title: 'Eye Strain Warning',         desc: 'Apply the 20-20-20 rule: every 20 min, look 20ft away for 20s.' },
    { title: 'Focus Session',              desc: 'Block social media apps during your peak productive hours.' }
  ];
}

// ── Report Preview ─────────────────────────────────────────────
async function loadReportPreview() {
  try {
    const res  = await fetch('/api/usage');
    const data = await res.json();
    const el   = document.getElementById('reportDate');
    if (el) el.textContent = new Date().toLocaleDateString();

    const totalEl = document.getElementById('reportTotal');
    if (totalEl) totalEl.textContent = formatTime(data.total_minutes ?? 0);

    const appsEl = document.getElementById('reportApps');
    if (appsEl) appsEl.textContent = (data.apps?.length ?? 0) + ' apps';
  } catch { /* silent */ }
}

// ── Download Report ───────────────────────────────────────────
function downloadReport() {
  window.location.href = '/download_report';
}

// ── Flash Dismiss ─────────────────────────────────────────────
function initFlashDismiss() {
  document.querySelectorAll('.flash').forEach(el => {
    setTimeout(() => el.remove(), 4500);
    el.addEventListener('click', () => el.remove());
  });
}

// ── Nav Highlight ─────────────────────────────────────────────
function initNavHighlight() {
  const path = window.location.pathname;
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('href') === path) {
      link.classList.add('active');
    }
  });
}

// ── Helpers ───────────────────────────────────────────────────
function formatTime(minutes) {
  minutes = Math.round(minutes);
  if (minutes < 60) return `${minutes}m`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

function safeText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

function escapeHtml(str) {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(String(str)));
  return d.innerHTML;
}