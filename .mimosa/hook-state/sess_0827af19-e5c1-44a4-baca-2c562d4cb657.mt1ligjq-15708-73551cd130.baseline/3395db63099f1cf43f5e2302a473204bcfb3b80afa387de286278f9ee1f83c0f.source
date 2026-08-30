/* octo-info.js — holographic 3D "math shape" overlay.
   Each page defines window.MATHVIZ = {type,color,formula,value,gap,...}.
   The formula/logic is shown as a rotating hologram, not prose.
   Three.js is lazy-loaded from CDN on first open (jsDelivr -> unpkg). */
(function () {
  var M = window.MATHVIZ; if (!M) return;
  var COL = M.color || 0x22d3ee, HEX = '#' + COL.toString(16).padStart(6, '0');
  var css =
    '#omB{position:fixed;top:calc(env(safe-area-inset-top,0px) + 9px);left:66px;z-index:40;background:rgba(8,12,20,.72);' +
    'color:' + HEX + ';border:1px solid ' + HEX + '66;border-radius:999px;padding:5px 12px;font:12px Tahoma,sans-serif;cursor:pointer}' +
    '#omO{position:fixed;inset:0;z-index:50;background:#04070c;display:none}' +
    '#omO.show{display:block}#omC{position:absolute;inset:0}' +
    '#omScan{position:absolute;inset:0;pointer-events:none;background:repeating-linear-gradient(0deg,transparent 0 2px,' + HEX + '11 2px 3px);opacity:.5}' +
    '#omF{position:absolute;left:0;right:0;bottom:calc(env(safe-area-inset-bottom,0px) + 16px);text-align:center;direction:ltr;' +
    'font:15px Consolas,monospace;color:' + HEX + ';text-shadow:0 0 10px ' + HEX + '99;pointer-events:none}' +
    '#omF small{display:block;margin-top:4px;font-size:12px;color:#cbd5e1}' +
    '#omG{position:absolute;top:calc(env(safe-area-inset-top,0px) + 12px);right:14px;direction:rtl;font:11px Tahoma;color:#fca5a5;' +
    'border:1px dashed #7f1d1d;border-radius:8px;padding:3px 8px;pointer-events:none}' +
    '#omX{position:absolute;top:calc(env(safe-area-inset-top,0px) + 10px);left:14px;z-index:60;color:#e2e8f0;background:rgba(8,12,20,.7);' +
    'border:1px solid #334155;border-radius:999px;font:13px Tahoma;padding:5px 12px;cursor:pointer}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  var btn = document.createElement('button'); btn.id = 'omB'; btn.textContent = '◆ ریاضی ۳بعدی'; document.body.appendChild(btn);
  var ov = document.createElement('div'); ov.id = 'omO';
  ov.innerHTML = '<canvas id="omC"></canvas><div id="omScan"></div>' +
    '<div id="omF">' + (M.formula || '') + '<small>' + (M.value || '') + '</small></div>' +
    (M.gap ? '<div id="omG">⚠ ' + M.gap + '</div>' : '') +
    '<button id="omX">✕</button>';
  document.body.appendChild(ov);
  var started = false, updaters = [];
  btn.onclick = function () { ov.classList.add('show'); if (!started) { started = true; loadThree(init); } };
  document.getElementById('omX').onclick = function () { ov.classList.remove('show'); };

  function loadThree(cb) {
    if (window.THREE) return cb();
    var s = document.createElement('script'); s.src = 'https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js';
    s.onload = cb; s.onerror = function () { var u = document.createElement('script'); u.src = 'https://unpkg.com/three@0.128.0/build/three.min.js'; u.onload = cb; document.head.appendChild(u); };
    document.head.appendChild(s);
  }

  function init() {
    var cv = document.getElementById('omC');
    var scene = new THREE.Scene(); scene.fog = new THREE.FogExp2(0x04070c, 0.02);
    var cam = new THREE.PerspectiveCamera(55, innerWidth / innerHeight, 0.1, 1000); cam.position.set(0, 6, M.dist || 34);
    var r = new THREE.WebGLRenderer({ canvas: cv, antialias: true, alpha: true });
    r.setPixelRatio(Math.min(devicePixelRatio, 2)); r.setSize(innerWidth, innerHeight); r.setClearColor(0x04070c, 1);
    scene.add(new THREE.AmbientLight(0xffffff, 0.8));
    var grid = new THREE.GridHelper(80, 40, COL, COL); grid.material.opacity = 0.12; grid.material.transparent = true; grid.position.y = -10; scene.add(grid);
    var g = new THREE.Group(); scene.add(g);
    build(g, COL);
    ghost(g);
    (function loop() { if (!ov.classList.contains('show')) { requestAnimationFrame(loop); return; }
      requestAnimationFrame(loop); g.rotation.y += 0.006; var t = performance.now() / 1000;
      updaters.forEach(function (f) { f(t); }); r.render(scene, cam); })();
    addEventListener('resize', function () { cam.aspect = innerWidth / innerHeight; cam.updateProjectionMatrix(); r.setSize(innerWidth, innerHeight); });
  }

  function wire(geo, col, op) { return new THREE.LineSegments(new THREE.EdgesGeometry(geo), new THREE.LineBasicMaterial({ color: col, transparent: true, opacity: op == null ? 0.9 : op })); }
  function glow(geo, col, op) { return new THREE.Mesh(geo, new THREE.MeshBasicMaterial({ color: col, transparent: true, opacity: op == null ? 0.12 : op })); }

  function build(g, C) {
    var T = M.type;
    if (T === 'bars' || T === 'matrix') {
      var vals = M.bars || [[1, 2, 3], [2, 4, 6], [3, 6, 9]];
      if (T === 'matrix') { for (var a = 0; a < 3; a++) for (var b = 0; b < 3; b++) { var h = (a + 1) * (b + 1); var col = h >= 6 ? 0xef4444 : h >= 4 ? 0xfb923c : h >= 2 ? 0xfacc15 : 0x4ade80; var bx = new THREE.BoxGeometry(4, h, 4); var m = glow(bx, col, 0.18); m.position.set((a - 1) * 6, h / 2 - 10, (b - 1) * 6); g.add(m); var w = wire(bx, col); w.position.copy(m.position); g.add(w); } }
      else { vals.forEach(function (h, i) { var bx = new THREE.BoxGeometry(4, h, 4); var big = h >= Math.max.apply(null, vals); var m = glow(bx, C, big ? 0.3 : 0.12); m.position.set((i - 1) * 7, h / 2 - 10, 0); g.add(m); var w = wire(bx, C, big ? 1 : 0.6); w.position.copy(m.position); g.add(w); }); }
    } else if (T === 'spheres') {
      (M.sizes || [1, 0.7, 0.5, 0.4, 0.3, 0.25]).forEach(function (s, i) { var rad = 1.5 + s * 6; var sp = new THREE.SphereGeometry(rad, 16, 12); var ang = i / 6 * Math.PI * 2; var p = new THREE.Vector3(Math.cos(ang) * 12, Math.sin(i) * 3, Math.sin(ang) * 12); if (i === 0) p.set(0, 0, 0); var w = wire(sp, C, 0.8); w.position.copy(p); g.add(w); var m = glow(sp, C, 0.14); m.position.copy(p); g.add(m); if (i) { var ln = new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(0, 0, 0), p]), new THREE.LineBasicMaterial({ color: C, transparent: true, opacity: 0.3 })); g.add(ln); } });
    } else if (T === 'wave') {
      var band = 6; [band, -band].forEach(function (y) { var pl = new THREE.GridHelper(30, 1, C, C); pl.position.y = y; pl.material.opacity = 0.3; pl.material.transparent = true; g.add(pl); });
      var geo = new THREE.BufferGeometry(); var N = 120, arr = new Float32Array(N * 3); geo.setAttribute('position', new THREE.BufferAttribute(arr, 3));
      var line = new THREE.Line(geo, new THREE.LineBasicMaterial({ color: C })); g.add(line);
      updaters.push(function (t) { for (var i = 0; i < N; i++) { var x = -15 + i / N * 30; arr[i * 3] = x; arr[i * 3 + 1] = Math.sin(x * 0.5 + t * 1.4) * band; arr[i * 3 + 2] = 0; } geo.attributes.position.needsUpdate = true; });
    } else if (T === 'galaxy') {
      var pts = [], N2 = 260; for (var i = 0; i < N2; i++) { var rr = (i / N2) * 14; var an = i * 0.5; pts.push(new THREE.Vector3(Math.cos(an) * rr, (Math.random() - 0.5) * 2, Math.sin(an) * rr)); }
      var pg = new THREE.BufferGeometry().setFromPoints(pts); g.add(new THREE.Points(pg, new THREE.PointsMaterial({ color: C, size: 0.5 })));
    } else if (T === 'ring') {
      var segs = M.segs || [7, 4, 2, 5, 2, 4], cols = [0x6366f1, C, 0xfbbf24, 0x64748b, 0x34d399, 0x22d3ee], tot = 24, acc = 0;
      segs.forEach(function (v, i) { var a0 = acc / tot * Math.PI * 2, a1 = (acc + v) / tot * Math.PI * 2; acc += v; for (var a = a0; a < a1; a += 0.12) { var bx = new THREE.BoxGeometry(1, 1, 3.4); var m = glow(bx, cols[i % 6], 0.5); m.position.set(Math.cos(a) * 11, 0, Math.sin(a) * 11); g.add(m); } });
    } else if (T === 'balance') {
      var p = M.p || 0.8, good = M.good || 90, bad = M.bad || -20, ev = Math.round(p * good + (1 - p) * bad);
      var beam = new THREE.BoxGeometry(24, 0.6, 0.6); var w = wire(beam, C); g.add(w); var bm = glow(beam, C, 0.2); g.add(bm);
      var tilt = Math.max(-0.5, Math.min(0.5, -ev / 200));
      w.rotation.z = tilt; bm.rotation.z = tilt;
      var mL = glow(new THREE.SphereGeometry(1 + p * 3, 16, 12), C, 0.3); mL.position.set(-11, Math.sin(tilt) * -11, 0); g.add(mL); g.add(function () { var x = wire(new THREE.SphereGeometry(1 + p * 3, 8, 6), C); x.position.copy(mL.position); return x; }());
      var mR = glow(new THREE.SphereGeometry(1 + (1 - p) * 3, 16, 12), 0xef4444, 0.3); mR.position.set(11, Math.sin(tilt) * 11, 0); g.add(mR);
      var post = wire(new THREE.CylinderGeometry(0.2, 1.4, 8, 6), C); post.position.y = -6; g.add(post);
    } else if (T === 'vectors') {
      var A = new THREE.Vector3(9, 5, 0), B = new THREE.Vector3(10, -1, 3);
      g.add(new THREE.ArrowHelper(A.clone().normalize(), new THREE.Vector3(0, 0, 0), A.length(), C, 2, 1.2));
      g.add(new THREE.ArrowHelper(B.clone().normalize(), new THREE.Vector3(0, 0, 0), B.length(), 0xf0abfc, 2, 1.2));
      var arc = []; var a0 = Math.atan2(A.y, A.x), a1 = Math.atan2(B.y, B.x); for (var a = Math.min(a0, a1); a <= Math.max(a0, a1); a += 0.08) arc.push(new THREE.Vector3(Math.cos(a) * 5, Math.sin(a) * 5, 0));
      g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(arc), new THREE.LineBasicMaterial({ color: 0xfde68a })));
    } else if (T === 'curve') {
      var k = M.k || 0.1, pts2 = []; for (var x = 0; x <= 24; x += 0.3) pts2.push(new THREE.Vector3(x - 12, (1 - Math.exp(-k * x)) * 14 - 8, 0));
      g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts2), new THREE.LineBasicMaterial({ color: C })));
      var dot = glow(new THREE.SphereGeometry(0.8, 12, 8), C, 0.9); g.add(dot);
      updaters.push(function (t) { var s = (t * 3) % 24; dot.position.set(s - 12, (1 - Math.exp(-k * s)) * 14 - 8, 0); });
      var axis = wire(new THREE.BoxGeometry(24, 0.05, 0.05), C, 0.4); axis.position.y = -8; g.add(axis);
    } else if (T === 'flow') {
      for (var i = 0; i < 3; i++) { var cu = new THREE.CatmullRomCurve3([new THREE.Vector3(-14, (i - 1) * 4, 0), new THREE.Vector3(-4, (i - 1) * 2, 0), new THREE.Vector3(0, 0, 0)]); g.add(new THREE.Mesh(new THREE.TubeGeometry(cu, 20, 0.5 + i * 0.2, 6, false), new THREE.MeshBasicMaterial({ color: C, transparent: true, opacity: 0.4 }))); }
      for (var j = 0; j < 3; j++) { var cu2 = new THREE.CatmullRomCurve3([new THREE.Vector3(0, 0, 0), new THREE.Vector3(4, (j - 1) * 2, 0), new THREE.Vector3(14, (j - 1) * 4, 0)]); g.add(new THREE.Mesh(new THREE.TubeGeometry(cu2, 20, 0.5, 6, false), new THREE.MeshBasicMaterial({ color: [0xf59e0b, 0x34d399, 0x22d3ee][j], transparent: true, opacity: 0.4 }))); }
      g.add(wire(new THREE.SphereGeometry(2, 16, 12), 0xffffff));
    } else if (T === 'layers') {
      ['#7dd3fc', '#a5b4fc', '#f0abfc'].forEach(function (c, i) { var pl = new THREE.BoxGeometry(20, 0.4, 20); var m = glow(pl, parseInt(c.slice(1), 16), 0.12); m.position.y = (1 - i) * 8; g.add(m); var w = wire(pl, parseInt(c.slice(1), 16)); w.position.y = (1 - i) * 8; g.add(w); });
      for (var i = 0; i < 6; i++) { var x = (Math.random() - 0.5) * 14, z = (Math.random() - 0.5) * 14; g.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints([new THREE.Vector3(x, 8, z), new THREE.Vector3(x * 0.6, -8, z * 0.6)]), new THREE.LineBasicMaterial({ color: 0x7dd3fc, transparent: true, opacity: 0.4 }))); }
    }
  }

  function ghost(g) {
    var ring = new THREE.RingGeometry(15, 15.4, 40);
    var m = new THREE.Mesh(ring, new THREE.MeshBasicMaterial({ color: 0xef4444, transparent: true, opacity: 0.18, side: THREE.DoubleSide }));
    m.rotation.x = Math.PI / 2; m.position.y = -9.7; g.add(m);
  }
})();
