/* shared-ui.js — shared vitals header, cross-world nav, owner-gate badge, MATHVIZ gap fix.
   Injected into every world page after octo-data.js. */
(function () {
  'use strict';
  const O = window.OCTO_DATA; if (!O) return;

  // ── palette ──
  const PAL = O.PAL || { cyan: '#22d3ee', pink: '#f472b6', gold: '#fcd34d', purple: '#a855f7', green: '#34d399', red: '#ef4444' };

  // ── vitals bar ──
  function injectVitals() {
    if (document.getElementById('octo-vitals')) return;
    const bar = document.createElement('div');
    bar.id = 'octo-vitals';
    bar.style.cssText = 'position:fixed;top:calc(env(safe-area-inset-top,0px) + 38px);left:0;right:0;z-index:8;display:flex;flex-wrap:wrap;justify-content:center;gap:5px;padding:4px 8px;pointer-events:none;';
    const parts = O.vitals ? O.vitals() : [];
    parts.forEach(function (p) {
      const span = document.createElement('span');
      span.style.cssText = 'background:rgba(8,12,20,.75);border:1px solid #1b2735;border-radius:999px;padding:3px 10px;font:11px Tahoma,sans-serif;color:#cbd5e1;white-space:nowrap;direction:ltr;';
      span.innerHTML = p;
      bar.appendChild(span);
    });
    if (!parts.length) {
      const span = document.createElement('span');
      span.style.cssText = 'background:rgba(8,12,20,.75);border:1px solid #7f1d1d;border-radius:999px;padding:3px 10px;font:11px Tahoma,sans-serif;color:#fca5a5;';
      span.textContent = '⚠ دادهٔ زنده لود نشد — extract_live_data.py را اجرا کن';
      bar.appendChild(span);
    }
    document.body.appendChild(bar);
  }

  // ── cross-world nav (thin strip below vitals) ──
  function injectNav() {
    if (document.getElementById('octo-nav')) return;
    const nav = document.createElement('div');
    nav.id = 'octo-nav';
    nav.style.cssText = 'position:fixed;top:calc(env(safe-area-inset-top,0px) + 62px);left:0;right:0;z-index:7;display:flex;justify-content:center;gap:6px;padding:2px 8px;pointer-events:auto;overflow-x:auto;';

    const worlds = [
      {n:1,dir:'01-cockpit',fa:'اتاق فرمان',c:'#22d3ee'},
      {n:2,dir:'02-ontology',fa:'هستی‌شناسی',c:'#60a5fa'},
      {n:3,dir:'03-money',fa:'موتور پول',c:'#34d399'},
      {n:4,dir:'04-twin',fa:'دوقلوی دیجیتال',c:'#f0abfc'},
      {n:5,dir:'05-galaxy',fa:'کهکشان دانش',c:'#c084fc'},
      {n:6,dir:'06-time',fa:'رودخانهٔ زمان',c:'#fb7185'},
      {n:7,dir:'07-decision',fa:'درخت تصمیم',c:'#fca5a5'},
      {n:8,dir:'08-risk',fa:'گنبد ریسک',c:'#4ade80'},
      {n:9,dir:'09-compass',fa:'قطب‌نمای ارزش',c:'#fcd34d'},
      {n:10,dir:'10-habit',fa:'بلور عادت',c:'#a5b4fc'}
    ];

    // detect current dir from URL
    const here = location.pathname.split('/').filter(Boolean).pop() || '';

    worlds.forEach(function (w) {
      const a = document.createElement('a');
      a.href = '../' + w.dir + '/index.html';
      a.textContent = w.n;
      a.title = w.fa;
      const active = here === w.dir;
      a.style.cssText = 'display:inline-block;width:22px;height:22px;line-height:22px;text-align:center;border-radius:50%;font:10px Tahoma,sans-serif;text-decoration:none;' +
        (active ? 'background:' + w.c + ';color:#000;font-weight:700;' : 'background:rgba(8,12,20,.6);border:1px solid ' + w.c + '55;color:' + w.c + ';');
      nav.appendChild(a);
    });
    document.body.appendChild(nav);
  }

  // ── owner-gate badge ──
  function injectGateBadge() {
    if (document.getElementById('octo-gate')) return;
    const count = O.gateCount ? O.gateCount() : 0;
    if (count <= 0) return;
    const badge = document.createElement('div');
    badge.id = 'octo-gate';
    badge.style.cssText = 'position:fixed;top:calc(env(safe-area-inset-top,0px) + 10px);right:10px;z-index:9;background:rgba(239,68,68,.85);color:#fff;border-radius:999px;padding:4px 10px;font:700 11px Tahoma,sans-serif;pointer-events:none;';
    badge.textContent = '⛔ gate ' + count;
    document.body.appendChild(badge);
  }

  // ── mode label badge (world pages only) ──
  function injectModeLabel() {
    if (document.getElementById('octo-mode')) return;
    const path = location.pathname;
    const worldMatch = path.match(/worlds\/(\d{2}-[^/]+)\//);
    if (!worldMatch) return; // hub page — no per-world badge
    const worldDir = worldMatch[1];
    let mode = 'READ-ONLY', color = PAL.cyan, border = 'rgba(34,211,238,.3)', bg = 'rgba(34,211,238,.08)';
    if (worldDir === '03-money') {
      mode = 'SHADOW MODE'; color = PAL.purple; border = 'rgba(168,85,247,.3)'; bg = 'rgba(168,85,247,.08)';
    }
    const hasGate = !!document.getElementById('octo-gate');
    const topOffset = hasGate ? 36 : 10;
    const badge = document.createElement('div');
    badge.id = 'octo-mode';
    badge.style.cssText = 'position:fixed;top:calc(env(safe-area-inset-top,0px) + ' + topOffset + 'px);right:10px;z-index:10;' +
      'border:1px solid ' + border + ';border-radius:999px;padding:2px 10px;font:700 10px Tahoma,sans-serif;' +
      'color:' + color + ';background:' + bg + ';pointer-events:none;white-space:nowrap;direction:ltr;';
    badge.textContent = mode;
    document.body.appendChild(badge);
  }

  // ── stale / fresh indicator ──
  function injectStaleIndicator() {
    if (document.getElementById('octo-stale')) return;
    const f = O.freshness ? O.freshness() : {};
    const live = f.live || { label: 'غایب', color: PAL.red, emoji: '🔴', ageMin: Infinity };
    const el = document.createElement('div');
    el.id = 'octo-stale';
    el.style.cssText = 'position:fixed;top:calc(env(safe-area-inset-top,0px) + 34px);left:50%;transform:translateX(-50%);z-index:11;' +
      'border:1px solid ' + live.color + '44;border-radius:999px;padding:2px 10px;font:700 10px Tahoma,sans-serif;' +
      'color:' + live.color + ';background:' + live.color + '11;pointer-events:none;white-space:nowrap;direction:ltr;';
    const ageText = live.ageMin != null && live.ageMin !== Infinity
      ? ' · ' + (live.ageMin < 60 ? live.ageMin + 'm' : Math.round(live.ageMin / 60) + 'h')
      : '';
    el.textContent = live.emoji + ' live ' + live.label + ageText;
    document.body.appendChild(el);
  }

  // ── fix MATHVIZ.gap if empty ──
  function fixMathviz() {
    const M = window.MATHVIZ; if (!M) return;
    if (M.gap != null && M.gap !== '') return;
    // heuristic based on type
    const fixes = {
      'bars': 'no historical series / single snapshot',
      'matrix': 'no aggregation / decay',
      'spheres': 'no real signal / ODE',
      'wave': 'no real signal / ODE',
      'galaxy': 'no real signal / ODE',
      'ring': 'no calendar / solver',
      'balance': 'no utility / Bayes',
      'vectors': 'values not vectorized',
      'curve': 'no forgetting curve',
      'flow': 'no variance / scenarios',
      'layers': 'no real signal / ODE'
    };
    M.gap = fixes[M.type] || 'needs source / [EST]';
  }

  // ── run ──
  injectVitals();
  injectNav();
  injectGateBadge();
  injectModeLabel();
  injectStaleIndicator();
  fixMathviz();
})();
