/* octo-data.js — shared READER backbone for OCTOPUS worlds (library, not a snapshot).
   File mtime may be old (code). Data freshness = window.LIVE_DATA.generated from
   nervous-system/live-data.js loaded first. Zero side-effect; idempotent; read-only. */
(function () {
  'use strict';

  // ── palette ──
  const PAL = {
    cyan: '#22d3ee', pink: '#f472b6', gold: '#fcd34d',
    purple: '#a855f7', green: '#34d399', red: '#ef4444'
  };

  // ── number formatter (fa-IR) ──
  function nf(n) {
    if (n == null) return '—';
    return Number(n).toLocaleString('fa-IR');
  }

  // ── source accessors ──
  const LIVE = window.LIVE_DATA || null;
  const OPS = window.OPS_DATA || null;
  const GRAPH = window.OCTOPUS_GRAPH || null;
  const NEURAL = window.NEURAL_DATA || null;
  const HEALTH = window.HEALTH_DATA || null;
  const CRYPTO = window.CRYPTO_DATA || null;
  const MINING = window.MINING_DATA || null;
  const TASK = window.TASK_DATA || window.TASK_SUMMARY_DATA || null;
  const GIT = window.GIT_DATA || null;
  const RESEARCH = window.RESEARCH_DATA || null;

  // ── freshness helper ──
  function _freshness(src) {
    if (!src || !src.generated) return { ageMin: Infinity, label: 'غایب', color: PAL.red, emoji: '🔴' };
    const gen = new Date(src.generated).getTime();
    const now = Date.now();
    const ageMin = Math.round((now - gen) / 60000);
    if (ageMin > 45) return { ageMin, label: 'کهنه', color: PAL.gold, emoji: '🟡' };
    return { ageMin, label: 'تازه', color: PAL.green, emoji: '🟢' };
  }

  // ── sog ──
  function sog() {
    if (!LIVE) return null;
    const s = LIVE.sog || {};
    return {
      identity_now: s.identity_now,
      drift_now: s.drift_now,
      healthy: !!s.healthy,
      default: s.default || null,
      surface: s.surface || null
    };
  }

  // ── events ──
  function events() {
    if (!LIVE) return null;
    const ev = LIVE.events || {};
    return {
      total_rows: ev.total_rows || 0,
      recent: ev.recent || [],
      by_name: ev.by_name || {},
      by_status: ev.by_status || {},
      by_agent: ev.by_agent || {}
    };
  }

  // ── frontier ──
  function frontier() {
    if (!LIVE) return null;
    const fr = LIVE.frontier || {};
    return {
      total_cells: fr.total_cells || 0,
      families: fr.families || 0,
      generation: fr.generation || 0,
      cells: (fr.cells || []).map(c => ({
        family: c.family || c.key || '?',
        rho: c.rho,
        kurt: c.kurt,
        mi: c.mi,
        count: c.count
      }))
    };
  }

  // ── budget ──
  function budget() {
    if (!LIVE) return null;
    const bg = LIVE.budget || {};
    return {
      cap: bg.cap,
      cloud_calls: bg.cloud_calls,
      remaining: bg.remaining,
      by_provider: bg.by_provider || {}
    };
  }

  // ── packets ──
  function packets() {
    if (!LIVE) return null;
    return (LIVE.packets || []).slice();
  }

  // ── daemon ──
  function daemon() {
    if (!LIVE) return null;
    const dm = LIVE.daemon || {};
    return {
      total_ticks: dm.total_ticks,
      stopped_at: dm.stopped_at || null,
      generation: dm.generation
    };
  }

  // ── money ──
  function money() {
    if (!OPS) return null;
    const m = OPS.money || {};
    return {
      month: m.month || {},
      today: m.today,
      confirmed: m.confirmed,
      claimed: m.claimed,
      weights: m.weights || {},
      spend: m.spend,
      projects: (m.projects || []).slice(),
      proposals: (m.proposals || []).slice()
    };
  }

  // ── time ──
  function time() {
    if (!OPS) return null;
    const t = OPS.time || {};
    return {
      chrono_beat: t.chrono_beat,
      metabolic_age: t.metabolic_age,
      age_tick: t.age_tick,
      deadlines: (t.deadlines || []).slice(),
      wires_on: t.wires_on,
      wires_total: t.wires_total,
      epoch_mode: t.epoch_mode
    };
  }

  // ── graph ──
  function graph() {
    if (!GRAPH) return null;
    return {
      nodes: (GRAPH.nodes || []).slice(),
      edges: (GRAPH.edges || []).slice(),
      groups: (GRAPH.groups || []).slice(),
      total_files: GRAPH.total_files || 0,
      total_links: GRAPH.total_links || 0,
      shown_nodes: GRAPH.shown_nodes || 0
    };
  }

  // ── neural ──
  function neural() {
    if (!NEURAL) return null;
    const n = NEURAL;
    return {
      vitals: n.vitals || null,
      rhythm: n.rhythm || null,
      circadian: n.circadian || null,
      hebbian: n.hebbian || null,
      consolidation: n.consolidation || null,
      organism: n.organism || null
    };
  }

  // ── neuralVitals (for cockpit mode_color bar) ──
  function neuralVitals() {
    if (!NEURAL) return null;
    const v = NEURAL.vitals || {};
    return {
      mode_color: v.mode_color || 'GREEN',
      readiness: v.readiness != null ? v.readiness : 0.7,
      stress: v.stress != null ? v.stress : 0,
      protective: !!v.protective,
      advisory: v.advisory || '—',
      bar_color: v.bar_color || '#34d399'
    };
  }

  // ── circadianMap (for time world) ──
  function circadianMap() {
    if (!NEURAL || !NEURAL.circadian) return null;
    const c = NEURAL.circadian;
    return {
      hour: c.hour != null ? c.hour : new Date().getHours(),
      phase: c.phase || 'active',
      readiness: c.readiness != null ? c.readiness : 0.7,
      is_maintenance: !!c.is_maintenance,
      best_platform: c.best_platform || '—'
    };
  }

  // ── crypto (CH-08) ──
  function crypto() {
    if (!CRYPTO) return null;
    const p = CRYPTO.project || {};
    const comp = CRYPTO.composite || {};
    const reg = CRYPTO.registry || {};
    return {
      name: p.name,
      phase: p.phase,
      action_mode: p.action_mode,
      risk_level: p.risk_level,
      security_gate: p.security_gate,
      autonomy_floor: p.autonomy_floor,
      score: comp.score,
      status: comp.status,
      emoji: comp.emoji,
      registry_empty: reg.registry_empty,
      positions_active: reg.positions_active_count || 0,
      blockers_active: (CRYPTO.blockers || []).filter(b => b.active).length,
      lunarcrush_verdict: ((CRYPTO.lunarcrush || {}).summary || {}).buy_signals + ' buy / ' + ((CRYPTO.lunarcrush || {}).summary || {}).sell_signals + ' sell',
      cryptoquant_verdict: ((CRYPTO.cryptoquant || {}).aggregate || {}).verdict || '—',
    };
  }

  // ── health (CH-07) ──
  function health() {
    if (!HEALTH) return null;
    const h = HEALTH;
    const sub = h.subscores || {};
    const det = h.details || {};
    const sys = det.system || {};
    const fit = det.fitness || {};
    const tel = det.telemetry || {};
    return {
      overall: h.overall,
      status: h.status || 'نامشخص',
      emoji: h.status_emoji || '⚪',
      system: sub.system,
      fitness: sub.fitness,
      telemetry: sub.telemetry,
      wires_on: sys.wires_on,
      wires_total: sys.wires_total,
      wires_pct: sys.wires_pct,
      frozen: sys.frozen,
      halted: sys.halted,
      cardiac_depleted: sys.cardiac_depleted,
      cartographer_stale: sys.cartographer_stale,
      fitness_authoritative: fit.authoritative,
      fitness_avg: fit.fitness_avg,
      integrity_alert_count: fit.integrity_alert_count,
      suspect_zero_total: tel.suspect_zero_total,
      spend_pct: tel.spend_pct,
      conflict_count: tel.conflict_count,
      governor_alert_count: (h.alerts || {}).governor_alert_count || 0
    };
  }

  // ── mining (CH-09) ──
  function mining() {
    if (!MINING) return null;
    const m = MINING;
    const fl = m.fleet || {};
    const rd = m.readiness || {};
    const sec = m.security || {};
    const gates = sec.gates || {};
    return {
      readiness_score: rd.score,
      readiness_mood: rd.mood,
      nodes_total: fl.nodes_total,
      nodes_running: fl.nodes_running,
      electricity_safe: fl.electricity_safe,
      electricity_mood: fl.electricity_mood,
      hashrate_measured: fl.hashrate_measured,
      candidates_count: (m.coins || {}).candidates_count || 0,
      verdicts_pending: (m.verdicts || {}).pending_count || 0,
      phase: (m.project || {}).phase,
      status: (m.project || {}).status,
      primary_blocker: (m.project || {}).primary_blocker,
      gate_wallet: (gates.wallet_zero_access || {}).pass,
      gate_electricity: (gates.electricity_verified || {}).pass,
      gate_registry: (gates.registry_filled || {}).pass,
      gate_verdicts: (gates.verdict_queue_clear || {}).pass,
    };
  }

  // ── tasks (CH-05) ──
  function tasks() {
    if (!TASK) return null;
    const sm = TASK.summary || {};
    return {
      open: sm.open_tasks || 0,
      done: sm.done_tasks || 0,
      total: sm.total_tasks || 0,
      completion_rate: sm.completion_rate || 0,
      by_priority: sm.by_priority || {},
      next_action: sm.next_action || null,
    };
  }

  // ── git (CH-02) ──
  function git() {
    if (!GIT) return null;
    const sm = GIT.summary || {};
    const repos = GIT.repos || [];
    const first = repos[0] || {};
    const st = first.status || {};
    return {
      total_repos: sm.total_repos || 0,
      clean_repos: sm.clean_repos || 0,
      dirty_repos: sm.dirty_repos || 0,
      ahead_repos: sm.ahead_repos || 0,
      behind_repos: sm.behind_repos || 0,
      branch: first.branch || '—',
      last_commit_message: (first.last_commit || {}).message || '—',
      last_commit_short: (first.last_commit || {}).hash_short || '—',
      dirty_total: st.dirty_total || 0,
      modified: st.modified || 0,
      untracked: st.untracked || 0,
      repos_list: repos.map(r => ({
        name: r.name,
        branch: r.branch,
        clean: (r.status || {}).clean,
        dirty_total: (r.status || {}).dirty_total || 0,
        ahead: (r.status || {}).ahead || 0,
        behind: (r.status || {}).behind || 0,
        last_message: ((r.last_commit || {}).message || '').slice(0, 60)
      }))
    };
  }

  // ── research (scout fleet) ──
  function research() {
    if (!RESEARCH) return null;
    const p = RESEARCH.pipeline || {};
    const f = RESEARCH.fleet || {};
    const s = RESEARCH.synthesis || {};
    const t = RESEARCH.triage || {};
    const h = RESEARCH.health || {};
    return {
      digests: p.total_digests || 0,
      findings: p.total_findings || 0,
      sources: p.total_sources || 0,
      scouts: f.active_scouts || 0,
      stale: f.stale_scouts ? f.stale_scouts.length : 0,
      coverage_24h: f.coverage_24h != null ? f.coverage_24h : 0,
      coverage_7d: f.coverage_7d != null ? f.coverage_7d : 0,
      latest_synthesis: s.latest_date || '—',
      synthesis_count: s.count || 0,
      open_proposals: t.open_proposals || 0,
      top_salience: t.top_salience != null ? t.top_salience : 0,
      health: h.score != null ? h.score : 0
    };
  }

  // ── risks (derived) ──
  function risks() {
    const s = sog(), bg = budget(), dm = daemon(), ev = events(), pk = packets();
    const h = health();
    const nv = neuralVitals();
    const cr = crypto();
    const mn = mining();
    const tk = tasks();
    const drift = (s && s.drift_now) || 0;
    const bf = (bg && bg.remaining != null && bg.cap) ? bg.remaining / bg.cap : 1;
    const fail = (ev && ev.by_status && (ev.by_status.failed || ev.by_status.error)) || 0;
    const pktCount = pk ? pk.length : 0;
    const risksArr = [
      { k: 'drift هویت', level: (drift > 1e-4 ? 3 : 1), impact: 3 },
      { k: 'ته‌کشیدنِ بودجه', level: (bf < 0.15 ? 3 : bf < 0.4 ? 2 : 1), impact: 2 },
      { k: 'توقفِ daemon', level: (dm && dm.stopped_at != null ? 3 : 1), impact: 3 },
      { k: 'صفِ owner-gate', level: (pktCount > 5 ? 3 : pktCount > 0 ? 2 : 1), impact: 2 },
      { k: 'رویدادِ failed', level: (fail > 10 ? 3 : fail > 0 ? 2 : 1), impact: 2 },
      { k: 'واگراییِ frontier', level: 1, impact: 2 }
    ];
    if (h) {
      const hl = h.overall >= 80 ? 1 : h.overall >= 60 ? 2 : h.overall >= 40 ? 3 : 3;
      risksArr.push({ k: 'health score', level: hl, impact: 3 });
    }
    if (nv) {
      risksArr.push({
        k: 'stress neural',
        level: (nv.protective ? 3 : nv.mode_color === 'RED' ? 3 : nv.mode_color === 'AMBER' ? 2 : 1),
        impact: 2
      });
    }
    if (cr) {
      const cl = cr.score >= 80 ? 1 : cr.score >= 50 ? 2 : 3;
      risksArr.push({ k: 'crypto/wallet', level: cl, impact: 2 });
    }
    if (mn) {
      const ml = mn.readiness_score >= 70 ? 1 : mn.readiness_score >= 40 ? 2 : 3;
      risksArr.push({ k: 'mining readiness', level: ml, impact: 2 });
      if (!mn.electricity_safe) {
        risksArr.push({ k: 'mining electricity gate', level: 3, impact: 3 });
      }
      if (mn.verdicts_pending > 0) {
        risksArr.push({ k: 'mining verdicts', level: mn.verdicts_pending > 3 ? 3 : 2, impact: 2 });
      }
    }
    if (tk) {
      const tc = tk.by_priority['بحرانی'] || 0;
      const th = tk.by_priority['بالا'] || 0;
      risksArr.push({ k: 'task backlog', level: (tc > 0 ? 3 : th > 5 ? 2 : tk.open > 50 ? 2 : 1), impact: 2 });
    }
    const rs = research();
    if (rs) {
      const rl = rs.health >= 0.8 ? 1 : rs.health >= 0.5 ? 2 : 3;
      risksArr.push({ k: 'scout fleet', level: rl, impact: 2 });
      if (rs.stale > 5) {
        risksArr.push({ k: 'stale scouts', level: 2, impact: 2 });
      }
    }
    const g = git();
    if (g) {
      const dirty = g.dirty_total;
      risksArr.push({ k: 'git dirty', level: (dirty > 200 ? 3 : dirty > 50 ? 2 : dirty > 0 ? 1 : 1), impact: 2 });
      if (g.behind_repos > 0) {
        risksArr.push({ k: 'git behind remote', level: 2, impact: 2 });
      }
    }
    return risksArr;
  }

  // ── vitals string ──
  function vitals() {
    const s = sog(), ev = events(), fr = frontier(), bg = budget(), dm = daemon();
    const nv = neuralVitals();
    const h = health();
    const cr = crypto();
    const ok = s && s.healthy;
    const beat = ok ? PAL.green : PAL.red;
    const idv = (s && s.identity_now != null) ? s.identity_now.toFixed(6) : '—';
    const dr = (s && s.drift_now != null) ? s.drift_now.toExponential(1) : '—';
    const paused = dm && dm.stopped_at != null;
    const parts = [];
    parts.push('<span style="color:' + beat + '">❤ identity ' + idv + ' ' + (ok ? '✓' : '⚠') + '<i style="opacity:.82;margin-inline-start:5px">drift ' + dr + '</i></span>');
    if (h) {
      const hc = h.overall >= 80 ? PAL.green : h.overall >= 60 ? PAL.gold : h.overall >= 40 ? '#f97316' : PAL.red;
      parts.push(h.emoji + ' health <i style="color:' + hc + '">' + h.overall + ' · ' + h.status + '</i>');
    }
    if (ev) parts.push('📡 ' + nf(ev.total_rows) + ' events<i>' + (ev.recent ? ev.recent.length : 0) + ' live</i>');
    if (fr) parts.push('🧬 gen ' + nf(fr.generation) + '<i>' + nf(fr.total_cells) + ' frontier</i>');
    if (bg) parts.push('🔋 ' + nf(bg.remaining) + '/' + nf(bg.cap) + '<i>cloud ' + nf(bg.cloud_calls) + ' · ' + (paused ? 'daemon paused' : 'daemon ' + nf(dm.total_ticks) + ' ticks') + '</i>');
    if (GRAPH) parts.push('🕸 ' + nf(GRAPH.total_files) + ' notes · ' + nf(GRAPH.total_links) + ' links');
    if (nv) {
      const emoji = nv.mode_color === 'GREEN' ? '🟢' : nv.mode_color === 'AMBER' ? '🟡' : '🔴';
      parts.push(emoji + ' neural <i>' + nv.mode_color + ' · readiness ' + Math.round(nv.readiness * 100) + '%' + (nv.protective ? ' · PROTECTIVE' : '') + '</i>');
    }
    if (cr) {
      const cc = cr.score >= 80 ? PAL.green : cr.score >= 50 ? PAL.gold : PAL.red;
      parts.push(cr.emoji + ' crypto <i style="color:' + cc + '">' + cr.score + ' · ' + cr.status + ' · ' + cr.action_mode + '</i>');
    }
    const tk = tasks();
    if (tk) {
      const tc = tk.by_priority['بحرانی'] || 0;
      const th = tk.by_priority['بالا'] || 0;
      const tcColor = tc > 0 ? PAL.red : th > 0 ? PAL.gold : PAL.green;
      parts.push('✓ ' + nf(tk.open) + ' task<i style="color:' + tcColor + '">' + (tc > 0 ? tc + ' بحرانی' : th > 0 ? th + ' بالا' : 'همه متوسط') + '</i>');
    }
    const g = git();
    if (g) {
      const gc = g.dirty_total === 0 ? PAL.green : g.dirty_total > 200 ? PAL.red : PAL.gold;
      parts.push('⛓ git <i style="color:' + gc + '">' + g.branch + ' · ' + g.last_commit_short + ' · ' + nf(g.dirty_total) + ' dirty</i>');
    }
    const rs = research();
    if (rs) {
      const rc = rs.health >= 0.8 ? PAL.green : rs.health >= 0.5 ? PAL.gold : PAL.red;
      parts.push('🔬 ' + nf(rs.digests) + ' digest<i style="color:' + rc + '">' + nf(rs.findings) + ' finding · ' + nf(rs.scouts) + ' scout · ' + (rs.health * 100).toFixed(0) + '%</i>');
    }
    return parts;
  }

  // ── nextAction (most important now) ──
  function nextAction() {
    const dm = daemon(), pk = packets(), s = sog();
    const h = health();
    const cr = crypto();
    const tk = tasks();
    if (dm && dm.stopped_at != null) return { action: 'دیمِن متوقف است — یک tick بزن', why: 'حلقهٔ متابولیسم ایستاده؛ تا حرکت نکند، خونی جاری نمی‌شود.' };
    if (h && h.overall < 40) return { action: 'health score بحرانی — ' + h.status, why: 'ارگانیسم در وضعیتِ بحرانی (' + h.overall + '/100) — system=' + h.system + ' fitness=' + h.fitness + ' telemetry=' + h.telemetry };
    if (pk && pk.length > 0) return { action: pk.length + ' تصمیمِ منتظرِ تو (owner gate)', why: 'اکشن‌های بیرونی پشتِ دروازهٔ مالک صف‌اند؛ فقط تو verdict می‌دهی.' };
    if (s && !s.healthy) return { action: 'لنگرِ هویت drift کرد — بررسی کن', why: 'identity از لنگر دور شد (drift ' + (s.drift_now || '?') + ')؛ سیستم fail-closed می‌ایستد.' };
    if (cr && cr.blockers_active > 0) return { action: 'crypto: ' + cr.blockers_active + ' blocker فعال — بررسی کن', why: 'پروژهٔ Crypto-eToro ' + cr.status + ' (' + cr.score + '/100) — ' + cr.phase };
    if (tk && tk.by_priority['بحرانی'] > 0) {
      const na = tk.next_action;
      return { action: 'task بحرانی: ' + (na ? na.text.slice(0, 60) : 'بررسی شود'), why: 'صندوق کارهای باز: ' + tk.open + ' task (' + tk.by_priority['بحرانی'] + ' بحرانی) در انتظارِ اقدام.' };
    }
    return { action: 'سالم — چرخه ادامه دارد', why: 'هویت روی لنگر، بودجه باز، صفِ تصمیم خالی. کارِ تو: نظارت.' };
  }

  // ── freshness of all sources ──
  function freshness() {
    return {
      live: _freshness(LIVE),
      ops: _freshness(OPS),
      graph: _freshness(GRAPH),
      neural: _freshness(NEURAL),
      health: _freshness(HEALTH),
      crypto: _freshness(CRYPTO),
      mining: _freshness(MINING),
      tasks: _freshness(TASK),
      git: _freshness(GIT),
      research: _freshness(RESEARCH)
    };
  }

  // ── owner-gate badge count ──
  function gateCount() {
    const pk = packets();
    return pk ? pk.filter(p => {
      const rec = (p.recommendation || '');
      return !/نیاز به تو:\s*هیچ/.test(rec) && !/نیازی به اقدام/.test(rec);
    }).length : 0;
  }

  // ── export ──
  window.OCTO_DATA = {
    PAL, nf,
    sog, events, frontier, budget, packets, daemon,
    money, time, graph, neural, neuralVitals, circadianMap, health, crypto, mining, tasks, git, research,
    risks, vitals, nextAction, freshness, gateCount,
    _raw: { LIVE, OPS, GRAPH, NEURAL, HEALTH, CRYPTO, MINING, TASK, GIT, RESEARCH }
  };
})();
