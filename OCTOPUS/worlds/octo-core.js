/* octo-core.js — shared engine for the mobile Obsidian-graph views.
   Renders the REAL vault graph in window.OCTOPUS_GRAPH. No external deps. */
window.OCTO = (function () {
  const G = window.OCTOPUS_GRAPH || { nodes: [], edges: [], groups: [] };

  function fit(canvas) {
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    const w = window.innerWidth, h = window.innerHeight;
    canvas.width = Math.floor(w * dpr);
    canvas.height = Math.floor(h * dpr);
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { ctx, w, h, dpr };
  }

  function adjacency() {
    const adj = G.nodes.map(() => []);
    G.edges.forEach(function (e) { adj[e[0]].push(e[1]); adj[e[1]].push(e[0]); });
    return adj;
  }

  // BFS distance (in hops) from a source node over the real edge graph
  function bfs(src, adj) {
    const dist = new Array(G.nodes.length).fill(-1);
    dist[src] = 0; const q = [src];
    for (let h = 0; h < q.length; h++) {
      const u = q[h];
      for (const v of adj[u]) if (dist[v] < 0) { dist[v] = dist[u] + 1; q.push(v); }
    }
    return dist;
  }

  // Fruchterman–Reingold-ish force layout, run once at load. Returns [{x,y}]
  function forceLayout(w, h, iters) {
    const n = G.nodes.length, P = new Array(n);
    for (let i = 0; i < n; i++) {
      const a = Math.random() * 6.283, r = 0.15 + Math.random() * 0.35;
      P[i] = { x: w / 2 + Math.cos(a) * r * w, y: h / 2 + Math.sin(a) * r * h, vx: 0, vy: 0 };
    }
    const E = G.edges, k = Math.sqrt((w * h) / Math.max(n, 1)) * 0.85;
    let temp = Math.min(w, h) * 0.10;
    for (let it = 0; it < iters; it++) {
      for (let i = 0; i < n; i++) {
        let fx = 0, fy = 0;
        for (let j = 0; j < n; j++) {
          if (i === j) continue;
          let dx = P[i].x - P[j].x, dy = P[i].y - P[j].y, d2 = dx * dx + dy * dy + 0.01;
          const f = (k * k) / d2; fx += dx * f; fy += dy * f;
        }
        P[i].vx = fx; P[i].vy = fy;
      }
      for (const e of E) {
        const a = e[0], b = e[1];
        let dx = P[a].x - P[b].x, dy = P[a].y - P[b].y, d = Math.sqrt(dx * dx + dy * dy) + 0.01;
        const f = (d * d) / k, ox = dx / d * f, oy = dy / d * f;
        P[a].vx -= ox; P[a].vy -= oy; P[b].vx += ox; P[b].vy += oy;
      }
      for (let i = 0; i < n; i++) {
        P[i].vx += (w / 2 - P[i].x) * 0.006; P[i].vy += (h / 2 - P[i].y) * 0.006;
        let dx = P[i].vx, dy = P[i].vy, d = Math.sqrt(dx * dx + dy * dy) + 0.01, m = Math.min(d, temp);
        P[i].x += dx / d * m; P[i].y += dy / d * m;
        P[i].x = Math.max(10, Math.min(w - 10, P[i].x));
        P[i].y = Math.max(10, Math.min(h - 10, P[i].y));
      }
      temp *= 0.975;
    }
    return P;
  }

  function radius(d) { return 1.6 + Math.sqrt(d) * 0.95; }

  // shared UI chrome (title chip + real-data footer + back link)
  function chrome(title, subtitle) {
    const g = G;
    const bar = document.createElement("div"); bar.className = "octo-chip";
    bar.innerHTML = '<b>' + title + '</b><span>' + (subtitle || '') + '</span>';
    document.body.appendChild(bar);
    const foot = document.createElement("div"); foot.className = "octo-foot";
    foot.innerHTML = '<a href="index.html">‹ hub</a>' +
      '<span>' + g.total_files + ' notes · ' + g.total_links + ' links · top ' +
      g.shown_nodes + ' shown</span><span class="ep">access-consciousness model · not qualia</span>';
    document.body.appendChild(foot);
  }

  return { G: G, fit: fit, adjacency: adjacency, bfs: bfs, forceLayout: forceLayout, radius: radius, chrome: chrome };
})();
