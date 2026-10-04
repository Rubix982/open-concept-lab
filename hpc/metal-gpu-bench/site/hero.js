// The hero: a full-width GPU render at the top of the page.
//
//   WebGPU available → live: a galaxy collision (tiled N-body compute shader,
//     additive glowing sprites, fading trails) or heat on a plate (stencil
//     compute shader, inferno colours, paint with the pointer). A HUD button
//     runs the same arithmetic on one CPU core instead, drawn the same way.
//   No WebGPU → the recording of the same scenes made on this Mac's GPU with
//     Metal (bench --frames → data/frames.js), drawn with WebGL2 in the same
//     style; Canvas 2D if even WebGL2 is missing.
//
// A classic script with no fetch, so the page works from file://. It never
// holds up the results below it.
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var hero = $("hero"), canvas = $("heroCanvas");
  if (!hero || !canvas) return;
  var reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  var small = function () { return hero.clientWidth < 700; };
  var dpr = function () { return Math.min(window.devicePixelRatio || 1, 2); };
  var big = (window.ResultsFmt && window.ResultsFmt.big) || function (x) { return x.toExponential(2); };
  var rateTxt = function (x) { return x >= 100 ? x.toFixed(0) : x >= 10 ? x.toFixed(1) : x.toFixed(2); };

  var state = { scene: "galaxy", mode: null, engine: "gpu", playing: !reduced, visible: true, gpuLabel: "" };

  // ------------------------------------------------------------ scenes
  // Two disc galaxies around heavy cores, spinning clockwise and passing
  // close: the same set-up as galaxy_init in bench/bench.m.
  function galaxies(N) {
    var half = N >> 1, f = new Float32Array(N * 6), s = 7;
    var rnd = function () { return (s = (s * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff; };
    var cx = [-0.45, 0.45], cy = [0.2, -0.2], vx = [0.55, -0.55], vy = [-0.12, 0.12], Mc = 3, Md = 1, soft = 0.0009;
    for (var g = 0; g < 2; g++) {
      var o = g * half;
      f.set([cx[g], cy[g], vx[g], vy[g], Mc, 0], o * 6);
      for (var k = 1; k < half; k++) {
        var u = k / half, r = 0.04 + 0.26 * Math.pow(u, 0.8), a = rnd() * 2 * Math.PI;
        var v = Math.sqrt((Mc + Md * u) / Math.sqrt(r * r + soft));
        f.set([cx[g] + r * Math.cos(a), cy[g] + r * Math.sin(a), vx[g] + v * Math.sin(a), vy[g] - v * Math.cos(a), Md / (half - 1), 0], (o + k) * 6);
      }
    }
    return f;
  }
  var GAL = { dt: 0.0008, soft: 0.0009, G: 1, view: 0.95 };   // view: world units shown half-height

  // heat sources that wander so the plate is alive without a touch
  function movingSources(t, W, H) {
    var out = [];
    for (var k = 0; k < 3; k++) {
      var ph = k * 2.1;
      out.push([W * (0.5 + 0.36 * Math.sin(t * (0.23 + 0.07 * k) + ph)), H * (0.5 + 0.34 * Math.sin(t * (0.31 + 0.05 * k) + ph * 1.7)), Math.max(4, W * 0.012), 1]);
    }
    return out;
  }

  // ------------------------------------------------------------ HUD + tabs
  var hud = $("heroHud"), tabs = $("heroTabs"), hint = $("heroHint"), playBtn = $("heroPlay");
  function setHud(lines) { hud.querySelector(".lines").innerHTML = lines.map(function (l, i) { return i === 0 ? "<b>" + l + "</b>" : "<span>" + l + "</span>"; }).join(""); }
  tabs.addEventListener("click", function (e) {
    var b = e.target.closest("button[data-scene]");
    if (!b || b.dataset.scene === state.scene) return;
    tabs.querySelectorAll("button").forEach(function (x) { x.setAttribute("aria-pressed", x === b); });
    state.scene = b.dataset.scene;
    state.engine = "gpu";
    restart();
  });
  var cpuBtn = $("heroCpu");
  cpuBtn.addEventListener("click", function () { state.engine = state.engine === "gpu" ? "cpu" : "gpu"; restart(); });
  playBtn.addEventListener("click", function () { state.playing = true; playBtn.hidden = true; kick(); });
  new IntersectionObserver(function (es) { state.visible = es[0].isIntersecting && !document.hidden; kick(); }, { threshold: 0.05 }).observe(hero);
  document.addEventListener("visibilitychange", function () { state.visible = !document.hidden; kick(); });

  // pointer painting for the heat scene
  var brush = null;
  function cellAt(e, W, H) { var r = canvas.getBoundingClientRect(); return [(e.clientX - r.left) / r.width * W, (e.clientY - r.top) / r.height * H]; }
  canvas.addEventListener("pointerdown", function (e) { if (state.scene !== "heat") return; brush = e; canvas.setPointerCapture(e.pointerId); });
  canvas.addEventListener("pointermove", function (e) { if (brush) brush = e; });
  ["pointerup", "pointercancel"].forEach(function (t) { canvas.addEventListener(t, function () { brush = null; }); });

  function sizeCanvas() {
    var w = hero.clientWidth, h = hero.clientHeight;
    canvas.width = Math.max(2, Math.round(w * dpr())); canvas.height = Math.max(2, Math.round(h * dpr()));
  }

  // ------------------------------------------------------------ loop
  var engine = null, running = false;
  function kick() {
    if (running || !engine || !state.playing || !state.visible) return;
    running = true;
    requestAnimationFrame(loop);
  }
  async function loop(now) {
    if (!engine || !state.playing || !state.visible) { running = false; return; }
    var e = engine;
    try { await e.frame(now); } catch (err) { console.error(err); running = false; return; }
    if (e !== engine) { running = false; kick(); return; }
    requestAnimationFrame(loop);
  }
  function restart() {
    if (engine && engine.destroy) engine.destroy();
    engine = null;
    sizeCanvas();
    hint.textContent = state.scene === "heat" ? "drag to add heat" : "";
    canvas.style.touchAction = state.scene === "heat" ? "none" : "";
    engine = state.mode === "live" ? (state.scene === "galaxy" ? liveGalaxy() : liveHeat()) :
      state.mode === "gl" ? (state.scene === "galaxy" ? glGalaxy() : glHeat()) : (state.scene === "galaxy" ? c2dGalaxy() : c2dHeat());
    cpuBtn.hidden = state.mode !== "live";
    cpuBtn.textContent = state.engine === "gpu" ? "Run the same on one CPU core" : "Back to the GPU";
    if (!state.playing) { engine.frame(performance.now(), true); playBtn.hidden = false; }
    kick();
  }
  var rs;
  new ResizeObserver(function () { clearTimeout(rs); rs = setTimeout(function () { if (engine) restart(); }, 250); }).observe(hero);

  // ================================================================ WebGPU
  var device = null, format = null, ctx = null;
  async function initWebGPU() {
    if (!navigator.gpu) return false;
    try {
      var adapter = await navigator.gpu.requestAdapter({ powerPreference: "high-performance" });
      if (!adapter) return false;
      device = await adapter.requestDevice({ requiredLimits: { maxStorageBufferBindingSize: Math.min(adapter.limits.maxStorageBufferBindingSize, 128 * 1024 * 1024) } });
      device.lost.then(function () { state.mode = "gl"; device = null; restart(); });
      ctx = canvas.getContext("webgpu");
      format = navigator.gpu.getPreferredCanvasFormat();
      ctx.configure({ device: device, format: format, alphaMode: "opaque" });
      var info = adapter.info || {};
      state.gpuLabel = /apple/i.test(info.vendor || "") ? "WebGPU → Metal" : "WebGPU" + (info.vendor ? " · " + info.vendor : "");
      return true;
    } catch (e) { console.warn("WebGPU unavailable:", e); device = null; return false; }
  }

  var TRI = "@vertex fn vfull(@builtin(vertex_index) i: u32) -> @builtin(position) vec4f {\n" +
    "  var p = array<vec2f, 3>(vec2f(-1, -1), vec2f(3, -1), vec2f(-1, 3));\n  return vec4f(p[i], 0.0, 1.0);\n}\n";
  // inferno, as a polynomial fit (the widely used one by Matt Zucker)
  var INFERNO_WGSL = "fn inferno(t: f32) -> vec3f {\n" +
    "  let c0 = vec3f(0.0002189403691192265, 0.001651004631001012, -0.01948089843709184);\n" +
    "  let c1 = vec3f(0.1065134194856116, 0.5639564367884091, 3.932712388889277);\n" +
    "  let c2 = vec3f(11.60249308247187, -3.972853965665698, -15.9423941062914);\n" +
    "  let c3 = vec3f(-41.70399613139459, 17.43639888205313, 44.35414519872813);\n" +
    "  let c4 = vec3f(77.162935699427, -33.40235894210092, -81.80730925738993);\n" +
    "  let c5 = vec3f(-71.31942824499214, 32.62606426397723, 73.20951985803202);\n" +
    "  let c6 = vec3f(25.13112622477341, -12.24266895238567, -23.07032500287172);\n" +
    "  return clamp(c0 + t * (c1 + t * (c2 + t * (c3 + t * (c4 + t * (c5 + t * c6))))), vec3f(0.0), vec3f(1.0));\n}\n";

  var GAL_WGSL =
    "struct B { pos: vec2f, vel: vec2f, mass: f32, pad: f32 };\n" +
    "struct Prm { n: u32, dt: f32, soft: f32, g: f32 };\n" +
    "@group(0) @binding(0) var<storage, read> src: array<B>;\n" +
    "@group(0) @binding(1) var<storage, read_write> dst: array<B>;\n" +
    "@group(0) @binding(2) var<uniform> prm: Prm;\n" +
    "var<workgroup> tile: array<vec3f, 256>;\n" +
    "// one thread per body; the workgroup loads 256 bodies at a time into fast\n" +
    "// shared memory and every thread reads them from there (tiling)\n" +
    "@compute @workgroup_size(256)\n" +
    "fn step(@builtin(global_invocation_id) gid: vec3u, @builtin(local_invocation_index) li: u32) {\n" +
    "  let i = gid.x;\n  var p: B;\n  if (i < prm.n) { p = src[i]; }\n  var f = vec2f(0.0);\n" +
    "  let tiles = (prm.n + 255u) / 256u;\n" +
    "  for (var t = 0u; t < tiles; t++) {\n" +
    "    let j = t * 256u + li;\n" +
    "    if (j < prm.n) { let q = src[j]; tile[li] = vec3f(q.pos, q.mass); } else { tile[li] = vec3f(0.0); }\n" +
    "    workgroupBarrier();\n" +
    "    for (var k = 0u; k < 256u; k++) { let q = tile[k]; let r = q.xy - p.pos; let inv = inverseSqrt(dot(r, r) + prm.soft); f += q.z * r * (inv * inv * inv); }\n" +
    "    workgroupBarrier();\n  }\n" +
    "  if (i >= prm.n) { return; }\n" +
    "  p.vel += prm.g * f * prm.dt;\n  p.pos += p.vel * prm.dt;\n  dst[i] = p;\n}\n" +
    "struct View { sx: f32, sy: f32, px: f32, py: f32, gain: f32, vref: f32, a: f32, b: f32 };\n" +
    "@group(0) @binding(0) var<storage, read> ps: array<B>;\n" +
    "@group(0) @binding(1) var<uniform> view: View;\n" +
    "struct VO { @builtin(position) pos: vec4f, @location(0) c: vec3f, @location(1) uv: vec2f };\n" +
    "@vertex fn vpts(@builtin(vertex_index) vi: u32, @builtin(instance_index) ii: u32) -> VO {\n" +
    "  var corner = array<vec2f, 6>(vec2f(-1, -1), vec2f(1, -1), vec2f(-1, 1), vec2f(-1, 1), vec2f(1, -1), vec2f(1, 1));\n" +
    "  let p = ps[ii]; let k = corner[vi];\n  var o: VO;\n" +
    "  o.pos = vec4f(p.pos.x * view.sx + k.x * view.px, p.pos.y * view.sy + k.y * view.py, 0.0, 1.0);\n" +
    "  let t = clamp(length(p.vel) / view.vref, 0.0, 1.0);\n" +
    "  o.c = mix(vec3f(0.16, 0.32, 1.0), vec3f(1.0, 0.82, 0.62), t) * view.gain;\n  o.uv = k;\n  return o;\n}\n" +
    "@fragment fn fpts(i: VO) -> @location(0) vec4f { let a = exp(-3.0 * dot(i.uv, i.uv)); return vec4f(i.c * a, 0.0); }\n" +
    TRI +
    "@fragment fn ffade() -> @location(0) vec4f { return vec4f(0.0); }\n" +
    "@group(0) @binding(0) var acc: texture_2d<f32>;\n" +
    "@fragment fn fshow(@builtin(position) fc: vec4f) -> @location(0) vec4f {\n" +
    "  let c = textureLoad(acc, vec2i(fc.xy), 0).rgb;\n" +
    "  let m = 1.0 - exp(-c * 2.0);\n  return vec4f(mix(vec3f(0.02, 0.025, 0.05), vec3f(1.0), m), 1.0);\n}\n";

  function liveGalaxy() {
    var N = GAL_FORCE_N || (small() ? 16384 : 32768), cpu = state.engine === "cpu";
    var w = canvas.width, h = canvas.height;
    var bytes = N * 24;
    var bufs = [0, 1].map(function () { return device.createBuffer({ size: bytes, usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST }); });
    var init = galaxies(N);
    device.queue.writeBuffer(bufs[0], 0, init);
    var prm = device.createBuffer({ size: 16, usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST });
    var pv = new ArrayBuffer(16);
    new Uint32Array(pv, 0, 1)[0] = N;
    new Float32Array(pv, 4, 3).set([GAL.dt, GAL.soft, GAL.G]);
    device.queue.writeBuffer(prm, 0, pv);
    var mod = device.createShaderModule({ code: GAL_WGSL });
    var cp = device.createComputePipeline({ layout: "auto", compute: { module: mod, entryPoint: "step" } });
    var cbinds = [0, 1].map(function (k) { return device.createBindGroup({ layout: cp.getBindGroupLayout(0), entries: [
      { binding: 0, resource: { buffer: bufs[k] } }, { binding: 1, resource: { buffer: bufs[1 - k] } }, { binding: 2, resource: { buffer: prm } }] }); });
    var acc = device.createTexture({ size: [w, h], format: "rgba16float", usage: GPUTextureUsage.RENDER_ATTACHMENT | GPUTextureUsage.TEXTURE_BINDING });
    var add = { color: { srcFactor: "one", dstFactor: "one", operation: "add" }, alpha: { srcFactor: "one", dstFactor: "one", operation: "add" } };
    var fadeB = { color: { srcFactor: "zero", dstFactor: "constant", operation: "add" }, alpha: { srcFactor: "zero", dstFactor: "constant", operation: "add" } };
    var pts = device.createRenderPipeline({ layout: "auto", vertex: { module: mod, entryPoint: "vpts" }, fragment: { module: mod, entryPoint: "fpts", targets: [{ format: "rgba16float", blend: add }] }, primitive: { topology: "triangle-list" } });
    var fade = device.createRenderPipeline({ layout: "auto", vertex: { module: mod, entryPoint: "vfull" }, fragment: { module: mod, entryPoint: "ffade", targets: [{ format: "rgba16float", blend: fadeB }] }, primitive: { topology: "triangle-list" } });
    var show = device.createRenderPipeline({ layout: "auto", vertex: { module: mod, entryPoint: "vfull" }, fragment: { module: mod, entryPoint: "fshow", targets: [{ format: format }] }, primitive: { topology: "triangle-list" } });
    var viewBuf = device.createBuffer({ size: 32, usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST });
    var sy = 1 / GAL.view, sx = sy * h / w, ps = 1.1 * dpr();
    device.queue.writeBuffer(viewBuf, 0, new Float32Array([sx, sy, ps / w * 2, ps / h * 2, 0.12 * Math.sqrt(32768 / N), 4.5, 0, 0]));
    var pbinds = [0, 1].map(function (k) { return device.createBindGroup({ layout: pts.getBindGroupLayout(0), entries: [{ binding: 0, resource: { buffer: bufs[k] } }, { binding: 1, resource: { buffer: viewBuf } }] }); });
    var sbind = device.createBindGroup({ layout: show.getBindGroupLayout(0), entries: [{ binding: 0, resource: acc.createView() }] });
    var cur = 0, perFrame = 2, simSteps = 0, hist = [], first = true, t0 = performance.now();
    // the CPU alternative: the same step in a worker, drawn the same way
    var wk = null, wkBusy = false, wkHist = [];
    if (cpu) {
      wk = new Worker(URL.createObjectURL(new Blob(["(" + GAL_CPU + ")()"], { type: "text/javascript" })));
      wk.postMessage({ type: "init", data: init.buffer.slice(0), dt: GAL.dt, soft: GAL.soft, G: GAL.G });
      wk.onmessage = function (e) { wkBusy = false; device.queue.writeBuffer(bufs[cur], 0, e.data.data); simSteps += e.data.steps; wkHist.push([e.data.steps, e.data.ms]); if (wkHist.length > 6) wkHist.shift(); };
    }
    var api = {
      frame: async function (now, still) {
        if (performance.now() - t0 > 60000 && !still) { restart(); return; }   // start a fresh collision now and then
        var enc = device.createCommandEncoder(), k = 0;
        if (!cpu) {
          k = still ? 900 : perFrame;
          for (var s = 0; s < k; s++) { var pass = enc.beginComputePass(); pass.setPipeline(cp); pass.setBindGroup(0, cbinds[cur]); pass.dispatchWorkgroups(Math.ceil(N / 256)); pass.end(); cur = 1 - cur; }
        } else if (!wkBusy) { wkBusy = true; wk.postMessage({ type: "step", budget: 120 }); }
        var r = enc.beginRenderPass({ colorAttachments: [{ view: acc.createView(), loadOp: first ? "clear" : "load", storeOp: "store", clearValue: { r: 0, g: 0, b: 0, a: 0 } }] });
        first = false;
        r.setPipeline(fade); r.setBlendConstant([0.8, 0.8, 0.8, 0.8]); r.draw(3);
        r.setPipeline(pts); r.setBindGroup(0, pbinds[cur]); r.draw(6, N);
        r.end();
        var p2 = enc.beginRenderPass({ colorAttachments: [{ view: ctx.getCurrentTexture().createView(), loadOp: "clear", storeOp: "store", clearValue: { r: 0, g: 0, b: 0, a: 1 } }] });
        p2.setPipeline(show); p2.setBindGroup(0, sbind); p2.draw(3); p2.end();
        var ta = performance.now();
        device.queue.submit([enc.finish()]);
        await device.queue.onSubmittedWorkDone();
        var ms = performance.now() - ta;
        if (!cpu) {
          simSteps += k;
          hist.push([k, ms]); if (hist.length > 30) hist.shift();
          // keep a frame near 14 ms: more steps when there's room, fewer bodies when there isn't
          if (!still) {
            if (ms > 22 && perFrame === 1 && N > 8192 && hist.length > 20) { restartWith(N / 2); return; }
            perFrame = Math.max(1, Math.min(4, ms < 7 ? perFrame + 1 : ms > 16 ? perFrame - 1 : perFrame));
          }
          var S = 0, T = 0; hist.forEach(function (x) { S += x[0]; T += x[1]; });
          var sps = S / (T / 1000);
          setHud([state.gpuLabel ? "Running live on your GPU (" + state.gpuLabel + ")" : "Running live on your GPU", N.toLocaleString() + " bodies · " + simSteps.toLocaleString() + " steps",
            rateTxt(sps) + " steps/s · " + big(sps * N * (N - 1)) + " force calculations/s"]);
        } else {
          var S2 = 0, T2 = 0; wkHist.forEach(function (x) { S2 += x[0]; T2 += x[1]; });
          var sps2 = T2 ? S2 / (T2 / 1000) : 0;
          setHud(["The same on one CPU core (JavaScript)", N.toLocaleString() + " bodies · " + simSteps.toLocaleString() + " steps",
            (sps2 ? rateTxt(sps2) + " steps/s · " + big(sps2 * N * (N - 1)) + " force calculations/s" : "computing the first step…")]);
        }
      },
      destroy: function () { if (wk) wk.terminate(); bufs.forEach(function (b) { b.destroy(); }); prm.destroy(); viewBuf.destroy(); acc.destroy(); },
    };
    // too slow for this GPU: come back with half the bodies, and stay there
    var restartWith = function (n) { GAL_FORCE_N = n; restart(); };
    return api;
  }
  var GAL_FORCE_N = 0;

  var GAL_CPU = function () {
    var f, n, dt, soft, G, next;
    onmessage = function (e) {
      var m = e.data;
      if (m.type === "init") { f = new Float32Array(m.data); n = f.length / 6; next = new Float32Array(f.length); dt = m.dt; soft = m.soft; G = m.G; return; }
      var t0 = performance.now(), k = 0;
      do {
        for (var i = 0; i < n; i++) {
          var o = i * 6, x = f[o], y = f[o + 1], fx = 0, fy = 0;
          for (var j = 0; j < n; j++) { var q = j * 6, dx = f[q] - x, dy = f[q + 1] - y, inv = 1 / Math.sqrt(dx * dx + dy * dy + soft), s = f[q + 4] * inv * inv * inv; fx += s * dx; fy += s * dy; }
          var vx = f[o + 2] + G * fx * dt, vy = f[o + 3] + G * fy * dt;
          next[o] = x + vx * dt; next[o + 1] = y + vy * dt; next[o + 2] = vx; next[o + 3] = vy; next[o + 4] = f[o + 4];
        }
        var t = f; f = next; next = t; k++;
      } while (performance.now() - t0 < m.budget);
      postMessage({ data: f.slice(), steps: k, ms: performance.now() - t0 });
    };
  };

  var HEAT_WGSL =
    "struct SP { w: u32, h: u32, alpha: f32, n: u32, src: array<vec4f, 8> };\n" +
    "@group(0) @binding(0) var<storage, read> a: array<f32>;\n" +
    "@group(0) @binding(1) var<storage, read_write> b: array<f32>;\n" +
    "@group(0) @binding(2) var<uniform> p: SP;\n" +
    "// one thread per cell, the stencil_step update; sources hold their cells hot\n" +
    "@compute @workgroup_size(16, 16)\n" +
    "fn step(@builtin(global_invocation_id) g: vec3u) {\n" +
    "  let x = g.x; let y = g.y;\n  if (x >= p.w || y >= p.h) { return; }\n  let i = y * p.w + x;\n" +
    "  if (x == 0u || y == 0u || x == p.w - 1u || y == p.h - 1u) { b[i] = 0.0; return; }\n" +
    "  let c = a[i];\n  var v = c + p.alpha * (a[i - 1u] + a[i + 1u] + a[i - p.w] + a[i + p.w] - 4.0 * c);\n" +
    "  for (var k = 0u; k < p.n; k++) { let s = p.src[k]; let d = vec2f(f32(x), f32(y)) - s.xy; if (dot(d, d) < s.z * s.z) { v = max(v, s.w); } }\n" +
    "  b[i] = v;\n}\n" + TRI + INFERNO_WGSL +
    "struct RV { w: u32, h: u32, cw: f32, ch: f32 };\n" +
    "@group(0) @binding(0) var<storage, read> grid: array<f32>;\n" +
    "@group(0) @binding(1) var<uniform> rv: RV;\n" +
    "fn at(x: i32, y: i32) -> f32 { let xx = clamp(x, 0, i32(rv.w) - 1); let yy = clamp(y, 0, i32(rv.h) - 1); return grid[u32(yy) * rv.w + u32(xx)]; }\n" +
    "@fragment fn fshow(@builtin(position) fc: vec4f) -> @location(0) vec4f {\n" +
    "  let u = fc.x / rv.cw * f32(rv.w) - 0.5; let v = fc.y / rv.ch * f32(rv.h) - 0.5;\n" +
    "  let x0 = i32(floor(u)); let y0 = i32(floor(v)); let fx = fract(u); let fy = fract(v);\n" +
    "  let t = mix(mix(at(x0, y0), at(x0 + 1, y0), fx), mix(at(x0, y0 + 1), at(x0 + 1, y0 + 1), fx), fy);\n" +
    "  return vec4f(inferno(pow(clamp(t, 0.0, 1.0), 0.55) * 0.97), 1.0);\n}\n";

  function liveHeat() {
    var cpu = state.engine === "cpu";
    var W = small() ? 512 : 1024, H = Math.max(64, Math.round(W * canvas.height / canvas.width));
    var n = W * H;
    var bufs = [0, 1].map(function () { return device.createBuffer({ size: n * 4, usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST }); });
    var pbuf = device.createBuffer({ size: 16 + 16 * 8, usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST });
    var rbuf = device.createBuffer({ size: 16, usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST });
    var mod = device.createShaderModule({ code: HEAT_WGSL });
    var cp = device.createComputePipeline({ layout: "auto", compute: { module: mod, entryPoint: "step" } });
    var binds = [0, 1].map(function (k) { return device.createBindGroup({ layout: cp.getBindGroupLayout(0), entries: [
      { binding: 0, resource: { buffer: bufs[k] } }, { binding: 1, resource: { buffer: bufs[1 - k] } }, { binding: 2, resource: { buffer: pbuf } }] }); });
    var show = device.createRenderPipeline({ layout: "auto", vertex: { module: mod, entryPoint: "vfull" }, fragment: { module: mod, entryPoint: "fshow", targets: [{ format: format }] }, primitive: { topology: "triangle-list" } });
    var sbinds = [0, 1].map(function (k) { return device.createBindGroup({ layout: show.getBindGroupLayout(0), entries: [{ binding: 0, resource: { buffer: bufs[k] } }, { binding: 1, resource: { buffer: rbuf } }] }); });
    var rv = new ArrayBuffer(16);
    new Uint32Array(rv, 0, 2).set([W, H]); new Float32Array(rv, 8, 2).set([canvas.width, canvas.height]);
    device.queue.writeBuffer(rbuf, 0, rv);
    var cur = 0, perFrame = 24, simSteps = 0, hist = [], t0 = performance.now();
    var sources = function () {
      var s = movingSources((performance.now() - t0) / 1000, W, H);
      if (brush) { var c = cellAt(brush, W, H); s.push([c[0], c[1], Math.max(5, W * 0.016), 1]); }
      return s;
    };
    var writeSources = function (s) {
      var buf = new ArrayBuffer(16 + 16 * 8), u = new Uint32Array(buf), f = new Float32Array(buf);
      u[0] = W; u[1] = H; f[2] = 0.24; u[3] = Math.min(8, s.length);
      s.slice(0, 8).forEach(function (x, k) { f.set(x, 4 + k * 4); });
      device.queue.writeBuffer(pbuf, 0, buf);
    };
    var wk = null, wkBusy = false, wkHist = [];
    if (cpu) {
      wk = new Worker(URL.createObjectURL(new Blob(["(" + HEAT_CPU + ")()"], { type: "text/javascript" })));
      wk.postMessage({ type: "init", w: W, h: H });
      wk.onmessage = function (e) { wkBusy = false; device.queue.writeBuffer(bufs[cur], 0, e.data.data); simSteps += e.data.steps; wkHist.push([e.data.steps, e.data.ms]); if (wkHist.length > 6) wkHist.shift(); };
    }
    return {
      frame: async function (now, still) {
        var s = sources(), enc = device.createCommandEncoder(), k = 0;
        if (!cpu) {
          writeSources(s);
          k = still ? 3000 : perFrame;
          for (var i = 0; i < k; i++) { var pass = enc.beginComputePass(); pass.setPipeline(cp); pass.setBindGroup(0, binds[cur]); pass.dispatchWorkgroups(Math.ceil(W / 16), Math.ceil(H / 16)); pass.end(); cur = 1 - cur; }
        } else if (!wkBusy) { wkBusy = true; wk.postMessage({ type: "step", budget: 60, sources: s }); }
        var r = enc.beginRenderPass({ colorAttachments: [{ view: ctx.getCurrentTexture().createView(), loadOp: "clear", storeOp: "store", clearValue: { r: 0, g: 0, b: 0, a: 1 } }] });
        r.setPipeline(show); r.setBindGroup(0, sbinds[cur]); r.draw(3); r.end();
        var ta = performance.now();
        device.queue.submit([enc.finish()]);
        await device.queue.onSubmittedWorkDone();
        var ms = performance.now() - ta;
        if (!cpu) {
          simSteps += k;
          hist.push([k, ms]); if (hist.length > 30) hist.shift();
          if (!still) perFrame = Math.max(4, Math.min(160, Math.round(perFrame * Math.min(1.25, Math.max(0.8, 10 / Math.max(ms, 0.5))))));
          var S = 0, T = 0; hist.forEach(function (x) { S += x[0]; T += x[1]; });
          var sps = S / (T / 1000);
          setHud([state.gpuLabel ? "Running live on your GPU (" + state.gpuLabel + ")" : "Running live on your GPU", W + " × " + H + " cells · " + simSteps.toLocaleString() + " steps",
            Math.round(sps).toLocaleString() + " steps/s · " + big(sps * W * H) + " cell updates/s"]);
        } else {
          var S2 = 0, T2 = 0; wkHist.forEach(function (x) { S2 += x[0]; T2 += x[1]; });
          var sps2 = T2 ? S2 / (T2 / 1000) : 0;
          setHud(["The same on one CPU core (JavaScript)", W + " × " + H + " cells · " + simSteps.toLocaleString() + " steps",
            sps2 ? Math.round(sps2).toLocaleString() + " steps/s · " + big(sps2 * W * H) + " cell updates/s" : "computing…"]);
        }
      },
      destroy: function () { if (wk) wk.terminate(); bufs.forEach(function (b) { b.destroy(); }); pbuf.destroy(); rbuf.destroy(); },
    };
  }

  var HEAT_CPU = function () {
    var a, b, W, H;
    onmessage = function (e) {
      var m = e.data;
      if (m.type === "init") { W = m.w; H = m.h; a = new Float32Array(W * H); b = new Float32Array(W * H); return; }
      var t0 = performance.now(), k = 0;
      do {
        for (var y = 1; y < H - 1; y++) for (var x = 1; x < W - 1; x++) {
          var i = y * W + x, c = a[i];
          b[i] = c + 0.24 * (a[i - 1] + a[i + 1] + a[i - W] + a[i + W] - 4 * c);
        }
        m.sources.forEach(function (s) {
          for (var yy = Math.max(1, Math.floor(s[1] - s[2])); yy <= Math.min(H - 2, Math.ceil(s[1] + s[2])); yy++)
            for (var xx = Math.max(1, Math.floor(s[0] - s[2])); xx <= Math.min(W - 2, Math.ceil(s[0] + s[2])); xx++)
              if ((xx - s[0]) * (xx - s[0]) + (yy - s[1]) * (yy - s[1]) < s[2] * s[2]) b[yy * W + xx] = Math.max(b[yy * W + xx], s[3]);
        });
        var t = a; a = b; b = t; k++;
      } while (performance.now() - t0 < m.budget);
      postMessage({ data: a.slice(), steps: k, ms: performance.now() - t0 });
    };
  };

  // ============================================================ recordings
  var REC = window.NATIVE_FRAMES;
  function bytes(b64) { var s = atob(b64), o = new Uint8Array(s.length); for (var i = 0; i < s.length; i++) o[i] = s.charCodeAt(i); return o; }
  var recGal = null, recHeat = null;
  function recordedGalaxy() {
    if (recGal || !REC) return recGal;
    var R = REC.nbody, b = bytes(R.pos);
    recGal = { R: R, pos: new Int16Array(b.buffer, b.byteOffset, b.byteLength / 2) };
    return recGal;
  }
  function recordedHeat() {
    if (recHeat || !REC) return recHeat;
    recHeat = { R: REC.stencil, px: bytes(REC.stencil.data) };
    return recHeat;
  }
  var recLabel = function () { return "Recorded on this Mac's GPU (" + ((REC && REC.machine.gpu) || "Apple GPU") + ", Metal)"; };
  // a looping clock over recorded frames, with a pause at the end
  function clock(frames, fps) {
    var t = reduced ? frames * 0.55 : 0, last = performance.now(), hold = 0;
    return function (still) {
      var now = performance.now(), dt = Math.min(0.1, (now - last) / 1000); last = now;
      if (still) return t;
      if (hold > 0) { hold -= dt; return frames - 1; }
      t += dt * fps;
      if (t >= frames - 1) { t = 0; hold = 1.2; return frames - 1; }
      return t;
    };
  }
  // positions of the recorded galaxy at fractional frame t, with speeds
  function galaxyAt(G, t, out) {
    var R = G.R, N = R.bodies, F = R.frames, i = Math.min(F - 2, Math.floor(t)), a = Math.min(1, t - i);
    var o1 = i * N * 2, o2 = (i + 1) * N * 2, k = R.span / 32767, vs = 1 / (R.stepsPerFrame * R.dt);
    for (var b = 0; b < N; b++) {
      // -32768 marks a body that left the recorded square: park it off screen
      if (G.pos[o1 + b * 2] === -32768 || G.pos[o2 + b * 2] === -32768) { out[b * 3] = 1e4; out[b * 3 + 1] = 1e4; out[b * 3 + 2] = 0; continue; }
      var x1 = G.pos[o1 + b * 2] * k, y1 = G.pos[o1 + b * 2 + 1] * k, x2 = G.pos[o2 + b * 2] * k, y2 = G.pos[o2 + b * 2 + 1] * k;
      out[b * 3] = x1 + (x2 - x1) * a; out[b * 3 + 1] = y1 + (y2 - y1) * a; out[b * 3 + 2] = Math.hypot(x2 - x1, y2 - y1) * vs;
    }
    return i;
  }

  // ---- WebGL2: the same look, from the recording
  var gl = null;
  function glProgram(vs, fs) {
    var p = gl.createProgram();
    [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]].forEach(function (x) {
      var s = gl.createShader(x[0]); gl.shaderSource(s, x[1]); gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      gl.attachShader(p, s);
    });
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    return p;
  }
  var FULL_VS = "#version 300 es\nvoid main(){ vec2 p = vec2((gl_VertexID << 1) & 2, gl_VertexID & 2); gl_Position = vec4(p * 2.0 - 1.0, 0.0, 1.0); }";
  var INFERNO_GLSL = "vec3 inferno(float t){" +
    "const vec3 c0=vec3(0.0002189403691192265,0.001651004631001012,-0.01948089843709184);" +
    "const vec3 c1=vec3(0.1065134194856116,0.5639564367884091,3.932712388889277);" +
    "const vec3 c2=vec3(11.60249308247187,-3.972853965665698,-15.9423941062914);" +
    "const vec3 c3=vec3(-41.70399613139459,17.43639888205313,44.35414519872813);" +
    "const vec3 c4=vec3(77.162935699427,-33.40235894210092,-81.80730925738993);" +
    "const vec3 c5=vec3(-71.31942824499214,32.62606426397723,73.20951985803202);" +
    "const vec3 c6=vec3(25.13112622477341,-12.24266895238567,-23.07032500287172);" +
    "return clamp(c0+t*(c1+t*(c2+t*(c3+t*(c4+t*(c5+t*c6))))),0.0,1.0);}";

  function glGalaxy() {
    var G = recordedGalaxy(), R = G.R, N = R.bodies, w = canvas.width, h = canvas.height;
    var half = gl.getExtension("EXT_color_buffer_float");
    var tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
    gl.texImage2D(gl.TEXTURE_2D, 0, half ? gl.RGBA16F : gl.RGBA8, w, h, 0, gl.RGBA, half ? gl.HALF_FLOAT : gl.UNSIGNED_BYTE, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST);
    var fb = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
    var pts = glProgram("#version 300 es\nlayout(location=0) in vec3 b; uniform vec2 s; uniform float size; uniform float gain; out vec3 c;\n" +
      "void main(){ gl_Position = vec4(b.xy * s, 0.0, 1.0); gl_PointSize = size; float t = clamp(b.z / 4.5, 0.0, 1.0); c = mix(vec3(0.16,0.32,1.0), vec3(1.0,0.82,0.62), t) * gain; }",
      "#version 300 es\nprecision mediump float; in vec3 c; out vec4 o; void main(){ vec2 d = gl_PointCoord * 2.0 - 1.0; o = vec4(c * exp(-3.0 * dot(d, d)), 0.0); }");
    var fade = glProgram(FULL_VS, "#version 300 es\nprecision mediump float; out vec4 o; void main(){ o = vec4(0.0); }");
    var show = glProgram(FULL_VS, "#version 300 es\nprecision mediump float; uniform sampler2D acc; out vec4 o; void main(){ vec3 c = texelFetch(acc, ivec2(gl_FragCoord.xy), 0).rgb; vec3 m = 1.0 - exp(-c * 2.0); o = vec4(mix(vec3(0.02,0.025,0.05), vec3(1.0), m), 1.0); }");
    var vbo = gl.createBuffer(), data = new Float32Array(N * 3), vao = gl.createVertexArray();
    gl.bindVertexArray(vao); gl.bindBuffer(gl.ARRAY_BUFFER, vbo); gl.bufferData(gl.ARRAY_BUFFER, data.byteLength, gl.DYNAMIC_DRAW);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 0, 0);
    var sy = 1 / GAL.view, sx = sy * h / w, tick = clock(R.frames, 8);
    // fewer, brighter bodies than the live run (2,048 recorded)
    var gain = half ? 0.12 * Math.sqrt(32768 / N) * 0.6 : 0.5;
    return {
      frame: function (now, still) {
        var t = tick(still), i = galaxyAt(G, t, data);
        gl.bindVertexArray(vao); gl.bindBuffer(gl.ARRAY_BUFFER, vbo); gl.bufferSubData(gl.ARRAY_BUFFER, 0, data);
        gl.bindFramebuffer(gl.FRAMEBUFFER, fb); gl.viewport(0, 0, w, h);
        gl.enable(gl.BLEND);
        gl.useProgram(fade); gl.blendColor(0.8, 0.8, 0.8, 0.8); gl.blendFunc(gl.ZERO, gl.CONSTANT_COLOR); gl.drawArrays(gl.TRIANGLES, 0, 3);
        gl.useProgram(pts); gl.blendFunc(gl.ONE, gl.ONE);
        gl.uniform2f(gl.getUniformLocation(pts, "s"), sx, sy); gl.uniform1f(gl.getUniformLocation(pts, "size"), 4.0 * dpr()); gl.uniform1f(gl.getUniformLocation(pts, "gain"), gain);
        gl.drawArrays(gl.POINTS, 0, N);
        gl.disable(gl.BLEND);
        gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.viewport(0, 0, w, h);
        gl.useProgram(show); gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, tex); gl.uniform1i(gl.getUniformLocation(show, "acc"), 0);
        gl.drawArrays(gl.TRIANGLES, 0, 3);
        setHud([recLabel(), N.toLocaleString() + " bodies · step " + (i * R.stepsPerFrame).toLocaleString() + " of " + ((R.frames - 1) * R.stepsPerFrame).toLocaleString(),
          (R.msPerStep * 1000).toFixed(0) + " µs a step on the GPU · WebGPU isn't available here, so this is the recording"]);
      },
      destroy: function () { gl.bindVertexArray(null); gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.deleteVertexArray(vao); gl.deleteTexture(tex); gl.deleteFramebuffer(fb); gl.deleteBuffer(vbo); },
    };
  }

  function glHeat() {
    var H = recordedHeat(), R = H.R, D = R.size, F = R.frames, w = canvas.width, h = canvas.height;
    var prog = glProgram(FULL_VS, "#version 300 es\nprecision highp float; uniform sampler2D a; uniform sampler2D b; uniform float k; uniform vec2 view; uniform vec2 off; out vec4 o;\n" + INFERNO_GLSL +
      "\nvoid main(){ vec2 uv = (gl_FragCoord.xy - off) / view; uv.y = 1.0 - uv.y; float t = mix(texture(a, uv).r, texture(b, uv).r, k); o = vec4(inferno(t * 0.97), 1.0); }");
    var texs = [0, 1].map(function () {
      var t = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, t);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
      return t;
    });
    gl.pixelStorei(gl.UNPACK_ALIGNMENT, 1);
    var loaded = [-1, -1], tick = clock(F, 6);
    // cover the canvas with the square plate (cropping top and bottom)
    var side = Math.max(w, h);
    return {
      frame: function (now, still) {
        var t = tick(still), i = Math.min(F - 2, Math.floor(t)), k = t - i;
        [i, i + 1].forEach(function (f, s) {
          if (loaded[s] === f) return;
          gl.bindTexture(gl.TEXTURE_2D, texs[s]);
          gl.texImage2D(gl.TEXTURE_2D, 0, gl.R8, D, D, 0, gl.RED, gl.UNSIGNED_BYTE, H.px.subarray(f * D * D, (f + 1) * D * D));
          loaded[s] = f;
        });
        // start from clean state: no vertex arrays, the screen, no blending
        gl.bindVertexArray(null); gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.disable(gl.BLEND);
        gl.viewport(0, 0, w, h); gl.useProgram(prog);
        gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, texs[0]); gl.uniform1i(gl.getUniformLocation(prog, "a"), 0);
        gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, texs[1]); gl.uniform1i(gl.getUniformLocation(prog, "b"), 1);
        gl.uniform1f(gl.getUniformLocation(prog, "k"), k);
        gl.uniform2f(gl.getUniformLocation(prog, "view"), side, side); gl.uniform2f(gl.getUniformLocation(prog, "off"), (w - side) / 2, (h - side) / 2);
        gl.drawArrays(gl.TRIANGLES, 0, 3);
        setHud([recLabel(), R.grid + " × " + R.grid + " cells (shown at " + D + " × " + D + ") · step " + R.stepAt[Math.round(t)].toLocaleString() + " of " + R.stepAt[F - 1].toLocaleString(),
          (R.msPerStep * 1000).toFixed(0) + " µs a step on the GPU · WebGPU isn't available here, so this is the recording"]);
      },
      destroy: function () { texs.forEach(function (t) { gl.deleteTexture(t); }); },
    };
  }

  // ---- Canvas 2D, the last resort
  var c2 = null;
  function c2dGalaxy() {
    var G = recordedGalaxy(), R = G.R, N = R.bodies, data = new Float32Array(N * 3), tick = clock(R.frames, 8);
    return { frame: function (now, still) {
      var w = canvas.width, h = canvas.height, t = tick(still), i = galaxyAt(G, t, data), s = h / 2 / GAL.view;
      c2.globalCompositeOperation = "source-over"; c2.fillStyle = "rgba(5,6,13,0.35)"; c2.fillRect(0, 0, w, h);
      c2.globalCompositeOperation = "lighter";
      for (var b = 0; b < N; b++) { var u = Math.min(1, data[b * 3 + 2] / 4.5); c2.fillStyle = "rgba(" + Math.round(40 + 215 * u) + "," + Math.round(70 + 90 * u) + "," + Math.round(255 - 140 * u) + ",0.55)"; c2.fillRect(w / 2 + data[b * 3] * s, h / 2 - data[b * 3 + 1] * s, 2 * dpr(), 2 * dpr()); }
      c2.globalCompositeOperation = "source-over";
      setHud([recLabel(), N.toLocaleString() + " bodies · step " + (i * R.stepsPerFrame).toLocaleString(), "this browser has neither WebGPU nor WebGL2, so this is a plain replay"]);
    } };
  }
  function c2dHeat() {
    var H = recordedHeat(), R = H.R, D = R.size, F = R.frames, tick = clock(F, 6);
    var off = document.createElement("canvas"); off.width = D; off.height = D;
    var o = off.getContext("2d"), img = o.createImageData(D, D);
    return { frame: function (now, still) {
      var w = canvas.width, h = canvas.height, t = tick(still), i = Math.min(F - 2, Math.floor(t)), k = t - i;
      for (var p = 0; p < D * D; p++) { var v = (H.px[i * D * D + p] * (1 - k) + H.px[(i + 1) * D * D + p] * k) / 255; img.data[p * 4] = 255 * Math.min(1, v * 1.6); img.data[p * 4 + 1] = 255 * Math.max(0, v * 1.4 - 0.45); img.data[p * 4 + 2] = 255 * Math.max(0, 0.35 - v) ; img.data[p * 4 + 3] = 255; }
      o.putImageData(img, 0, 0);
      var side = Math.max(w, h); c2.imageSmoothingEnabled = true; c2.drawImage(off, (w - side) / 2, (h - side) / 2, side, side);
      setHud([recLabel(), R.grid + " × " + R.grid + " cells · step " + R.stepAt[Math.round(t)].toLocaleString(), "this browser has neither WebGPU nor WebGL2, so this is a plain replay"]);
    } };
  }

  // ------------------------------------------------------------ max-size measurement
  // The hero's own kernels, compute only, at their largest sizes: used once by
  // bench/browser-bench.mjs to record what this machine's browser can do.
  async function bestRate(encodeSteps, secs) {
    var k = 1, best = 0, w0 = performance.now();
    var run = async function (n) { var enc = device.createCommandEncoder(); encodeSteps(enc, n); var t = performance.now(); device.queue.submit([enc.finish()]); await device.queue.onSubmittedWorkDone(); return performance.now() - t; };
    while (performance.now() - w0 < 600) await run(k);   // let the GPU clock ramp up
    var t0 = performance.now();
    while (performance.now() - t0 < secs * 1000) {
      var ms = await run(k);
      best = Math.max(best, k / (ms / 1000));
      k = Math.max(1, Math.min(4096, Math.round(k * Math.min(2, 40 / Math.max(ms, 0.05)))));
    }
    return best;   // steps per second
  }
  function cpuRate(src, init, secs, budget) {
    return new Promise(function (res) {
      var w = new Worker(URL.createObjectURL(new Blob(["(" + src + ")()"], { type: "text/javascript" }))), best = 0, t0 = performance.now();
      w.onmessage = function (e) {
        best = Math.max(best, e.data.steps / (e.data.ms / 1000));
        if (performance.now() - t0 < secs * 1000) w.postMessage({ type: "step", budget: budget, sources: [] });
        else { w.terminate(); res(best); }
      };
      w.postMessage(init);
      w.postMessage({ type: "step", budget: budget, sources: [] });
    });
  }
  window.HeroBench = {
    measure: async function (opts) {
      opts = opts || {};
      var secs = opts.seconds || 3;
      state.playing = false;
      if (!device && !(await initWebGPU())) return { webgpu: false };
      var out = { webgpu: true, label: state.gpuLabel, galaxy: [], heat: [] };
      var gN = opts.galaxy || [16384, 32768, 65536], hW = opts.heat || [1024, 2048, 4096];
      var mod = device.createShaderModule({ code: GAL_WGSL });
      var cp = device.createComputePipeline({ layout: "auto", compute: { module: mod, entryPoint: "step" } });
      for (var i = 0; i < gN.length; i++) {
        var N = gN[i], bufs = [0, 1].map(function () { return device.createBuffer({ size: N * 24, usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST }); });
        device.queue.writeBuffer(bufs[0], 0, galaxies(N));
        var prm = device.createBuffer({ size: 16, usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST }), pv = new ArrayBuffer(16);
        new Uint32Array(pv, 0, 1)[0] = N; new Float32Array(pv, 4, 3).set([GAL.dt, GAL.soft, GAL.G]); device.queue.writeBuffer(prm, 0, pv);
        var bg = [0, 1].map(function (k) { return device.createBindGroup({ layout: cp.getBindGroupLayout(0), entries: [{ binding: 0, resource: { buffer: bufs[k] } }, { binding: 1, resource: { buffer: bufs[1 - k] } }, { binding: 2, resource: { buffer: prm } }] }); });
        var cur = 0;
        var sps = await bestRate(function (enc, n) { for (var s = 0; s < n; s++) { var p = enc.beginComputePass(); p.setPipeline(cp); p.setBindGroup(0, bg[cur]); p.dispatchWorkgroups(Math.ceil(N / 256)); p.end(); cur = 1 - cur; } }, secs);
        var row = { n: N, gpuStepsPerSec: sps, gpuRate: sps * N * (N - 1) };
        if (N <= 16384) {
          var csps = await cpuRate(GAL_CPU, { type: "init", data: galaxies(N).buffer, dt: GAL.dt, soft: GAL.soft, G: GAL.G }, 6, 1500);
          row.cpuStepsPerSec = csps; row.cpuRate = csps * N * (N - 1);
        }
        out.galaxy.push(row);
        bufs.forEach(function (b) { b.destroy(); }); prm.destroy();
      }
      var hmod = device.createShaderModule({ code: HEAT_WGSL });
      var hcp = device.createComputePipeline({ layout: "auto", compute: { module: hmod, entryPoint: "step" } });
      for (var j = 0; j < hW.length; j++) {
        var W = hW[j], H = W, hb = [0, 1].map(function () { return device.createBuffer({ size: W * H * 4, usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST }); });
        var hp = device.createBuffer({ size: 144, usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST }), hv = new ArrayBuffer(144), hu = new Uint32Array(hv), hf = new Float32Array(hv);
        hu[0] = W; hu[1] = H; hf[2] = 0.24; hu[3] = 3;
        movingSources(1, W, H).forEach(function (x, k) { hf.set(x, 4 + k * 4); });
        device.queue.writeBuffer(hp, 0, hv);
        var hg = [0, 1].map(function (k) { return device.createBindGroup({ layout: hcp.getBindGroupLayout(0), entries: [{ binding: 0, resource: { buffer: hb[k] } }, { binding: 1, resource: { buffer: hb[1 - k] } }, { binding: 2, resource: { buffer: hp } }] }); });
        var hc = 0;
        var hs = await bestRate(function (enc, n) { for (var s = 0; s < n; s++) { var p = enc.beginComputePass(); p.setPipeline(hcp); p.setBindGroup(0, hg[hc]); p.dispatchWorkgroups(W / 16, H / 16); p.end(); hc = 1 - hc; } }, secs);
        var hrow = { size: W, gpuStepsPerSec: hs, gpuRate: hs * W * H };
        var hcs = await cpuRate(HEAT_CPU, { type: "init", w: W, h: H }, 4, 400);
        hrow.cpuStepsPerSec = hcs; hrow.cpuRate = hcs * W * H;
        out.heat.push(hrow);
        hb.forEach(function (b) { b.destroy(); }); hp.destroy();
      }
      return out;
    },
  };

  // ------------------------------------------------------------ start
  (async function () {
    sizeCanvas();
    if (await initWebGPU()) state.mode = "live";
    else if (REC) {
      gl = canvas.getContext("webgl2", { antialias: false, premultipliedAlpha: false });
      if (gl) state.mode = "gl";
      else { c2 = canvas.getContext("2d"); state.mode = c2 ? "2d" : null; }
    }
    if (!state.mode) { setHud(["No GPU drawing available in this browser", "the measured results below don't need it"]); return; }
    hero.dataset.mode = state.mode;
    restart();
  })();
})();
