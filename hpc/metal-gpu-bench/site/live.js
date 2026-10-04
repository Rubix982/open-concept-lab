// The browser engines behind the measured "in a browser" numbers (and any
// optional "Run it live" panels a page wires up; nothing starts by itself). GPU: WebGPU compute shaders (WGSL) mirroring the Metal
// kernels in nbody/ and stencil/. CPU: the same arithmetic in JavaScript, in
// a background worker. A classic script, so the page works from file://.
//
// window.LiveBench.measureAll() runs every engine at a few sizes without
// drawing; bench/browser-bench.mjs uses it to record the browser results.
(function () {
  "use strict";
  var $ = function (id) { return document.getElementById(id); };
  var F = window.ResultsFmt || { big: String, ms: String, times: String };
  var rate = function (x) { return x >= 100 ? x.toFixed(0) : x >= 10 ? x.toFixed(1) : x.toFixed(2); };
  var sleep = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
  var frame = function () { return new Promise(function (r) { requestAnimationFrame(function () { r(); }); }); };

  // ------------------------------------------------------------- WebGPU
  var device = null, gpuWhy = null, gpuInit = null;
  function initGPU() {
    if (gpuInit) return gpuInit;
    gpuInit = (async function () {
      if (!navigator.gpu) { gpuWhy = "This browser has no WebGPU (Chrome, Edge and Safari 26+ have it), so the live demos run on the CPU only. The measured results above don't need it."; return null; }
      try {
        var adapter = await navigator.gpu.requestAdapter({ powerPreference: "high-performance" });
        if (!adapter) { gpuWhy = "WebGPU is here but no GPU adapter is available (it may be switched off), so the live demos run on the CPU only."; return null; }
        var lim = adapter.limits;
        device = await adapter.requestDevice({ requiredLimits: {
          maxStorageBufferBindingSize: Math.min(lim.maxStorageBufferBindingSize, 256 * 1024 * 1024),
          maxBufferSize: Math.min(lim.maxBufferSize, 256 * 1024 * 1024),
        } });
        device.lost.then(function (info) { if ($("gpuNote")) $("gpuNote").textContent = "The GPU device was lost (" + (info.message || info.reason) + "). Reload to try again."; });
        var info = adapter.info || {};
        var name = [info.vendor, info.architecture].filter(Boolean).join(" ");
        if ($("gpuNote")) $("gpuNote").textContent = "Running on WebGPU" + (name ? " (" + name + ")" : "") + ". Switch engines at the same size to compare.";
        return device;
      } catch (e) { gpuWhy = "WebGPU failed to start (" + e.message + "), so the live demos run on the CPU only."; device = null; return null; }
    })();
    return gpuInit;
  }
  var FORMAT = function () { return navigator.gpu.getPreferredCanvasFormat(); };

  function worker(fn) {
    var url = URL.createObjectURL(new Blob(["(" + fn + ")()"], { type: "text/javascript" }));
    return new Worker(url);
  }

  // ============================================================ N-BODY
  // The layout of nbody/NBodySimulator.m: two counter-rotating rings of bodies
  // between r = 0.1 and 0.5, dt = 0.0002. Two changes so the picture holds
  // together while the browser runs hundreds of steps a second: gentler
  // gravity (G = 0.02 at 4,096 bodies, scaled by 4096/N; ε² = 0.004), and each
  // body starts at the circular-orbit speed for the pull it actually feels
  // (in a flat disk, mass outside a body pulls outward too, so the pull is
  // measured on a sample of up to 2,048 bodies). None of this changes the
  // cost of a step.
  function nbInit(N) {
    var G = 0.02 * 4096 / N, soft = 0.004, s = 42;
    var rand = function () { return (s = (s * 1103515245 + 12345) & 0x7fffffff) / 0x7fffffff; };
    var x = new Float32Array(N), y = new Float32Array(N), m = new Float32Array(N), i, j;
    for (i = 0; i < N; i++) { var a = (i / N) * 2 * Math.PI, r = 0.1 + 0.4 * rand(); x[i] = r * Math.cos(a); y[i] = r * Math.sin(a); m[i] = 1 + rand(); }
    var step = Math.max(1, Math.floor(N / 2048)), f = new Float32Array(N * 6);
    for (i = 0; i < N; i++) {
      var rr = Math.hypot(x[i], y[i]), ux = x[i] / rr, uy = y[i] / rr, ring = i < N / 2 ? 1 : -1, pull = 0;
      for (j = 0; j < N; j += step) {
        if (j === i) continue;
        var dx = x[j] - x[i], dy = y[j] - y[i], inv = 1 / Math.sqrt(dx * dx + dy * dy + soft);
        pull += G * m[j] * step * inv * inv * inv * (dx * ux + dy * uy);
      }
      var v = Math.sqrt(Math.max(0, pull) * rr);
      f.set([x[i], y[i], -ring * v * uy, ring * v * ux, m[i], 0], i * 6);
    }
    return { data: f, params: { N: N, dt: 0.0002, soft: soft, G: G } };
  }

  var NB_WGSL = [
    "struct P { pos: vec2f, vel: vec2f, mass: f32, pad: f32 };",
    "struct Params { n: u32, dt: f32, soft: f32, g: f32 };",
    "@group(0) @binding(0) var<storage, read> src: array<P>;",
    "@group(0) @binding(1) var<storage, read_write> dst: array<P>;",
    "@group(0) @binding(2) var<uniform> prm: Params;",
    "// one thread per body, like nbody_update in Shaders.metal; reads a snapshot",
    "// (src) and writes the next state (dst)",
    "@compute @workgroup_size(64)",
    "fn step(@builtin(global_invocation_id) id: vec3u) {",
    "  let i = id.x;",
    "  if (i >= prm.n) { return; }",
    "  var p = src[i];",
    "  var f = vec2f(0.0);",
    "  for (var j = 0u; j < prm.n; j++) {",
    "    if (j == i) { continue; }",
    "    let q = src[j];",
    "    let r = q.pos - p.pos;",
    "    let inv = inverseSqrt(dot(r, r) + prm.soft);",
    "    f += prm.g * q.mass * r * (inv * inv * inv);",
    "  }",
    "  p.vel += f * prm.dt;",
    "  p.pos += p.vel * prm.dt;",
    "  p.pos = fract((p.pos + 3.0) * 0.5) * 2.0 - 1.0;",
    "  dst[i] = p;",
    "}",
    "struct View { sx: f32, sy: f32, px: f32, py: f32 };",
    "@group(0) @binding(0) var<storage, read> ps: array<P>;",
    "@group(0) @binding(1) var<uniform> view: View;",
    "struct VO { @builtin(position) pos: vec4f, @location(0) c: vec3f, @location(1) uv: vec2f };",
    "@vertex",
    "fn vs(@builtin(vertex_index) vi: u32, @builtin(instance_index) ii: u32) -> VO {",
    "  var corner = array<vec2f, 6>(vec2f(-1, -1), vec2f(1, -1), vec2f(-1, 1), vec2f(-1, 1), vec2f(1, -1), vec2f(1, 1));",
    "  let p = ps[ii];",
    "  let k = corner[vi];",
    "  var o: VO;",
    "  o.pos = vec4f(p.pos.x * view.sx + k.x * view.px, p.pos.y * view.sy + k.y * view.py, 0.0, 1.0);",
    "  let t = clamp(length(p.vel) / 12.0, 0.0, 1.0);",
    "  o.c = mix(vec3f(0.36, 0.52, 1.0), vec3f(1.0, 0.62, 0.3), t);",
    "  o.uv = k;",
    "  return o;",
    "}",
    "@fragment",
    "fn fs(i: VO) -> @location(0) vec4f {",
    "  let a = max(0.0, 1.0 - dot(i.uv, i.uv));",
    "  return vec4f(i.c * a * 0.55, a);",
    "}",
  ].join("\n");

  function nbGPU(N) {
    var init = nbInit(N), data = init.data, prm = init.params;
    var mk = function () { return device.createBuffer({ size: data.byteLength, usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST }); };
    var bufs = [mk(), mk()];
    device.queue.writeBuffer(bufs[0], 0, data);
    var pbuf = device.createBuffer({ size: 16, usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST });
    var pv = new ArrayBuffer(16);
    new Uint32Array(pv, 0, 1)[0] = N;
    new Float32Array(pv, 4, 3).set([prm.dt, prm.soft, prm.G]);
    device.queue.writeBuffer(pbuf, 0, pv);
    var mod = device.createShaderModule({ code: NB_WGSL });
    var cp = device.createComputePipeline({ layout: "auto", compute: { module: mod, entryPoint: "step" } });
    var binds = [0, 1].map(function (k) { return device.createBindGroup({ layout: cp.getBindGroupLayout(0), entries: [
      { binding: 0, resource: { buffer: bufs[k] } }, { binding: 1, resource: { buffer: bufs[1 - k] } }, { binding: 2, resource: { buffer: pbuf } }] }); });
    var vbuf = device.createBuffer({ size: 16, usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST });
    var rp = null, rbinds = null, cur = 0;
    return {
      n: N,
      // run k steps; resolves with the wall time until the GPU finished them
      steps: async function (k) {
        var enc = device.createCommandEncoder();
        for (var s = 0; s < k; s++) {
          var pass = enc.beginComputePass();
          pass.setPipeline(cp); pass.setBindGroup(0, binds[cur]); pass.dispatchWorkgroups(Math.ceil(N / 64)); pass.end();
          cur = 1 - cur;
        }
        var t0 = performance.now();
        device.queue.submit([enc.finish()]);
        await device.queue.onSubmittedWorkDone();
        return performance.now() - t0;
      },
      draw: function (view) {
        if (!rp) {
          rp = device.createRenderPipeline({ layout: "auto", vertex: { module: mod, entryPoint: "vs" },
            fragment: { module: mod, entryPoint: "fs", targets: [{ format: FORMAT(), blend: {
              color: { srcFactor: "one", dstFactor: "one", operation: "add" }, alpha: { srcFactor: "one", dstFactor: "one", operation: "add" } } }] },
            primitive: { topology: "triangle-list" } });
          rbinds = [0, 1].map(function (k) { return device.createBindGroup({ layout: rp.getBindGroupLayout(0), entries: [
            { binding: 0, resource: { buffer: bufs[k] } }, { binding: 1, resource: { buffer: vbuf } }] }); });
        }
        var c = view.canvas, w = c.width, h = c.height, mm = Math.min(w, h), px = 1.6 * (window.devicePixelRatio || 1);
        device.queue.writeBuffer(vbuf, 0, new Float32Array([0.95 * mm / w, 0.95 * mm / h, px / w * 2, px / h * 2]));
        var re = device.createCommandEncoder();
        var pass = re.beginRenderPass({ colorAttachments: [{ view: view.ctx.getCurrentTexture().createView(), loadOp: "clear", storeOp: "store", clearValue: { r: 0.043, g: 0.071, b: 0.125, a: 1 } }] });
        pass.setPipeline(rp); pass.setBindGroup(0, rbinds[cur]); pass.draw(6, N); pass.end();
        device.queue.submit([re.finish()]);
      },
      destroy: function () { bufs.forEach(function (b) { b.destroy(); }); pbuf.destroy(); vbuf.destroy(); },
    };
  }

  var NB_WORKER = function () {
    var f, n, prm, next;
    var step = function () {
      // the same loop as cpu_worker in NBodySimulator.m, on one core
      for (var i = 0; i < n; i++) {
        var o = i * 6, x = f[o], y = f[o + 1], fx = 0, fy = 0;
        for (var j = 0; j < n; j++) {
          if (j === i) continue;
          var q = j * 6, dx = f[q] - x, dy = f[q + 1] - y;
          var inv = 1 / Math.sqrt(dx * dx + dy * dy + prm.soft);
          var s = prm.G * f[q + 4] * inv * inv * inv;
          fx += s * dx; fy += s * dy;
        }
        var vx = f[o + 2] + fx * prm.dt, vy = f[o + 3] + fy * prm.dt;
        var px = x + vx * prm.dt, py = y + vy * prm.dt;
        px = ((((px + 3) % 2) + 2) % 2) - 1; py = ((((py + 3) % 2) + 2) % 2) - 1;
        next[o] = px; next[o + 1] = py; next[o + 2] = vx; next[o + 3] = vy; next[o + 4] = f[o + 4];
      }
      var t = f; f = next; next = t;
    };
    onmessage = function (e) {
      var m = e.data;
      if (m.type === "init") { f = new Float32Array(m.data); next = new Float32Array(f.length); n = m.params.N; prm = m.params; return; }
      var t0 = performance.now(), k = 0;
      do { step(); k++; } while (performance.now() - t0 < m.budget);
      postMessage({ data: m.picture ? f.slice() : null, steps: k, ms: performance.now() - t0 });
    };
  };

  function nbCPU(N) {
    var w = worker(NB_WORKER), init = nbInit(N);
    w.postMessage({ type: "init", data: init.data.buffer, params: init.params }, [init.data.buffer]);
    var pending = null;
    w.onmessage = function (e) { var p = pending; pending = null; if (p) p(e.data); };
    return {
      n: N,
      // run steps for ~budget ms in the worker; resolves {steps, ms, data}
      run: function (budget, picture) { return new Promise(function (res) { pending = res; w.postMessage({ type: "step", budget: budget, picture: picture }); }); },
      destroy: function () { w.terminate(); },
    };
  }

  // ============================================================ STENCIL
  var MAX_HEAT = 8;
  var ST_WGSL = [
    "struct SP { w: u32, h: u32, alpha: f32, nheat: u32, heat: array<vec4f, " + MAX_HEAT + "> };",
    "@group(0) @binding(0) var<storage, read> src: array<f32>;",
    "@group(0) @binding(1) var<storage, read_write> dst: array<f32>;",
    "@group(0) @binding(2) var<uniform> p: SP;",
    "// one thread per cell, 16 x 16 per workgroup, like stencil_step in Shaders.metal",
    "@compute @workgroup_size(16, 16)",
    "fn step(@builtin(global_invocation_id) g: vec3u) {",
    "  let x = g.x; let y = g.y;",
    "  if (x >= p.w || y >= p.h) { return; }",
    "  let i = y * p.w + x;",
    "  if (x == 0u || y == 0u || x == p.w - 1u || y == p.h - 1u) { dst[i] = src[i]; return; }",
    "  let c = src[i];",
    "  var v = c + p.alpha * (src[i - 1u] + src[i + 1u] + src[i - p.w] + src[i + p.w] - 4.0 * c);",
    "  // the page's one addition: heaters you place hold their cells hot",
    "  for (var k = 0u; k < p.nheat; k++) {",
    "    let hh = p.heat[k];",
    "    let d = vec2f(f32(x), f32(y)) - hh.xy;",
    "    if (dot(d, d) < hh.z * hh.z) { v = 1.0; }",
    "  }",
    "  dst[i] = v;",
    "}",
    "struct RV { w: u32, h: u32, cw: f32, ch: f32 };",
    "@group(0) @binding(0) var<storage, read> grid: array<f32>;",
    "@group(0) @binding(1) var<uniform> rv: RV;",
    "@vertex",
    "fn vs(@builtin(vertex_index) i: u32) -> @builtin(position) vec4f {",
    "  var pts = array<vec2f, 3>(vec2f(-1, -1), vec2f(3, -1), vec2f(-1, 3));",
    "  return vec4f(pts[i], 0.0, 1.0);",
    "}",
    "fn ramp(t: f32) -> vec3f {",
    "  let c0 = vec3f(0.043, 0.071, 0.125); let c1 = vec3f(0.76, 0.34, 0.05); let c2 = vec3f(1.0, 0.93, 0.62);",
    "  if (t < 0.5) { return mix(c0, c1, t * 2.0); }",
    "  return mix(c1, c2, (t - 0.5) * 2.0);",
    "}",
    "@fragment",
    "fn fs(@builtin(position) fc: vec4f) -> @location(0) vec4f {",
    "  let side = min(rv.cw, rv.ch);",
    "  let ox = (rv.cw - side) * 0.5;",
    "  let u = (fc.x - ox) / side;",
    "  let v = fc.y / side;",
    "  if (u < 0.0 || u >= 1.0) { return vec4f(0.043, 0.071, 0.125, 1.0); }",
    "  let x = min(u32(u * f32(rv.w)), rv.w - 1u);",
    "  let y = min(u32(v * f32(rv.h)), rv.h - 1u);",
    "  return vec4f(ramp(sqrt(clamp(grid[y * rv.w + x], 0.0, 1.0))), 1.0);",
    "}",
  ].join("\n");

  function stGPU(W, heat) {
    var n = W * W;
    var mk = function () { return device.createBuffer({ size: n * 4, usage: GPUBufferUsage.STORAGE | GPUBufferUsage.COPY_DST }); };
    var bufs = [mk(), mk()];
    var pbuf = device.createBuffer({ size: 16 + 16 * MAX_HEAT, usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST });
    var rbuf = device.createBuffer({ size: 16, usage: GPUBufferUsage.UNIFORM | GPUBufferUsage.COPY_DST });
    var mod = device.createShaderModule({ code: ST_WGSL });
    var cp = device.createComputePipeline({ layout: "auto", compute: { module: mod, entryPoint: "step" } });
    var binds = [0, 1].map(function (k) { return device.createBindGroup({ layout: cp.getBindGroupLayout(0), entries: [
      { binding: 0, resource: { buffer: bufs[k] } }, { binding: 1, resource: { buffer: bufs[1 - k] } }, { binding: 2, resource: { buffer: pbuf } }] }); });
    var rp = null, rbinds = null, cur = 0;
    var api = {
      w: W,
      setHeat: function (cells) {
        var buf = new ArrayBuffer(16 + 16 * MAX_HEAT), u = new Uint32Array(buf), f = new Float32Array(buf);
        u[0] = W; u[1] = W; f[2] = 0.24; u[3] = cells.length;
        cells.forEach(function (h, k) { f.set([h[0], h[1], h[2], 0], 4 + k * 4); });
        device.queue.writeBuffer(pbuf, 0, buf);
      },
      steps: async function (k) {
        var enc = device.createCommandEncoder();
        for (var s = 0; s < k; s++) {
          var pass = enc.beginComputePass();
          pass.setPipeline(cp); pass.setBindGroup(0, binds[cur]); pass.dispatchWorkgroups(Math.ceil(W / 16), Math.ceil(W / 16)); pass.end();
          cur = 1 - cur;
        }
        var t0 = performance.now();
        device.queue.submit([enc.finish()]);
        await device.queue.onSubmittedWorkDone();
        return performance.now() - t0;
      },
      draw: function (view) {
        if (!rp) {
          rp = device.createRenderPipeline({ layout: "auto", vertex: { module: mod, entryPoint: "vs" },
            fragment: { module: mod, entryPoint: "fs", targets: [{ format: FORMAT() }] }, primitive: { topology: "triangle-list" } });
          rbinds = [0, 1].map(function (k) { return device.createBindGroup({ layout: rp.getBindGroupLayout(0), entries: [
            { binding: 0, resource: { buffer: bufs[k] } }, { binding: 1, resource: { buffer: rbuf } }] }); });
        }
        var c = view.canvas, u = new ArrayBuffer(16);
        new Uint32Array(u, 0, 2).set([W, W]);
        new Float32Array(u, 8, 2).set([c.width, c.height]);
        device.queue.writeBuffer(rbuf, 0, u);
        var re = device.createCommandEncoder();
        var pass = re.beginRenderPass({ colorAttachments: [{ view: view.ctx.getCurrentTexture().createView(), loadOp: "clear", storeOp: "store", clearValue: { r: 0.043, g: 0.071, b: 0.125, a: 1 } }] });
        pass.setPipeline(rp); pass.setBindGroup(0, rbinds[cur]); pass.draw(3); pass.end();
        device.queue.submit([re.finish()]);
      },
      destroy: function () { bufs.forEach(function (b) { b.destroy(); }); pbuf.destroy(); rbuf.destroy(); },
    };
    api.setHeat(heat);
    return api;
  }

  var ST_WORKER = function () {
    var a, b, W, H, heat = [], alpha = 0.24;
    var step = function () {
      // the same loop as cpu_worker in StencilSimulator.m, on one core
      for (var y = 0; y < H; y++) {
        var r = y * W;
        if (y === 0 || y === H - 1) { b.set(a.subarray(r, r + W), r); continue; }
        b[r] = a[r]; b[r + W - 1] = a[r + W - 1];
        for (var x = 1; x < W - 1; x++) {
          var i = r + x, c = a[i];
          b[i] = c + alpha * (a[i - 1] + a[i + 1] + a[i - W] + a[i + W] - 4 * c);
        }
      }
      heat.forEach(function (h) {
        for (var yy = Math.max(1, Math.floor(h[1] - h[2])); yy <= Math.min(H - 2, Math.ceil(h[1] + h[2])); yy++)
          for (var xx = Math.max(1, Math.floor(h[0] - h[2])); xx <= Math.min(W - 2, Math.ceil(h[0] + h[2])); xx++)
            if ((xx - h[0]) * (xx - h[0]) + (yy - h[1]) * (yy - h[1]) < h[2] * h[2]) b[yy * W + xx] = 1;
      });
      var t = a; a = b; b = t;
    };
    onmessage = function (e) {
      var m = e.data;
      if (m.type === "init") { W = m.w; H = m.h; a = new Float32Array(W * H); b = new Float32Array(W * H); heat = m.heat; return; }
      if (m.type === "heat") { heat = m.heat; return; }
      var t0 = performance.now(), k = 0;
      do { step(); k++; } while (performance.now() - t0 < m.budget);
      var ms = performance.now() - t0;
      if (!m.picture) { postMessage({ steps: k, ms: ms }); return; }
      // a picture no bigger than 512 x 512
      var s = Math.max(1, Math.ceil(W / 512)), w = Math.ceil(W / s), h = Math.ceil(H / s), img = new Float32Array(w * h);
      for (var yy = 0; yy < h; yy++) for (var xx = 0; xx < w; xx++) img[yy * w + xx] = a[yy * s * W + xx * s];
      postMessage({ img: img, w: w, h: h, steps: k, ms: ms }, [img.buffer]);
    };
  };

  function stCPU(W, heat) {
    var w = worker(ST_WORKER), pending = null;
    w.postMessage({ type: "init", w: W, h: W, heat: heat });
    w.onmessage = function (e) { var p = pending; pending = null; if (p) p(e.data); };
    return {
      w: W,
      setHeat: function (cells) { w.postMessage({ type: "heat", heat: cells }); },
      run: function (budget, picture) { return new Promise(function (res) { pending = res; w.postMessage({ type: "step", budget: budget, picture: picture }); }); },
      destroy: function () { w.terminate(); },
    };
  }

  // ============================================================ UI pieces
  function seg(parent, label, options, value, onChange) {
    var el = document.createElement("div");
    el.className = "ctl";
    el.innerHTML = '<span class="lab"><span>' + label + '</span></span><span class="seg" role="group" aria-label="' + label + '">' +
      options.map(function (o) { return '<button type="button" data-v="' + o[0] + '">' + o[1] + "</button>"; }).join("") + "</span>";
    var set = function (v) { el.querySelectorAll("button").forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.v === v); }); };
    set(value);
    el.addEventListener("click", function (e) { var b = e.target.closest("button"); if (b && !b.disabled) { set(b.dataset.v); onChange(b.dataset.v); } });
    parent.appendChild(el);
    return { disable: function (v, off) { el.querySelector('[data-v="' + v + '"]').disabled = off; } };
  }
  function slider(parent, label, min, max, value, show, onInput) {
    var el = document.createElement("label");
    el.className = "ctl";
    el.innerHTML = '<span class="lab"><span>' + label + '</span><span class="val"></span></span><input type="range" min="' + min + '" max="' + max + '" step="1" value="' + value + '">';
    var input = el.querySelector("input"), val = el.querySelector(".val"), t;
    var upd = function () { val.textContent = show(+input.value); };
    upd();
    input.addEventListener("input", function () { upd(); clearTimeout(t); t = setTimeout(function () { onInput(+input.value); }, 150); });
    parent.appendChild(el);
  }
  function button(parent, text, onClick) {
    var wrap = document.createElement("div"), b = document.createElement("button");
    wrap.className = "ctl"; b.type = "button"; b.className = "btn"; b.textContent = text;
    b.addEventListener("click", onClick);
    wrap.appendChild(b); parent.appendChild(wrap);
    return b;
  }
  function canvasFor(stage, gpu) {
    var c = document.createElement("canvas");
    stage.insertBefore(c, stage.firstChild);
    var size = function () {
      var dpr = Math.min(window.devicePixelRatio || 1, 2), w = stage.clientWidth, h = Math.round(Math.min(w / (16 / 9), 560));
      if (w < 600) h = Math.round(w * 0.8);
      c.width = Math.round(w * dpr); c.height = Math.round(h * dpr); c.style.height = h + "px";
    };
    size();
    new ResizeObserver(size).observe(stage);
    var ctx = gpu ? c.getContext("webgpu") : c.getContext("2d");
    if (gpu) ctx.configure({ device: device, format: FORMAT(), alphaMode: "opaque" });
    return { canvas: c, ctx: ctx };
  }
  function onScreen(el, cb) {
    var seen = false;
    new IntersectionObserver(function (es) { seen = es[0].isIntersecting; cb(seen && !document.hidden); }, { threshold: 0.15 }).observe(el);
    document.addEventListener("visibilitychange", function () { cb(seen && !document.hidden); });
  }

  // One live demo panel; `kind` is "nb" or "st".
  function demo(kind) {
    var isNb = kind === "nb";
    var stage = $(kind + "Stage"), ctl = $(kind + "Controls");
    var state = { engine: device ? "gpu" : "cpu", exp: isNb ? 12 : 10, visible: false, paused: false, best: {} };
    var size = function () { return Math.pow(2, state.exp); };
    var heat = [[0.3, 0.42, 0.035], [0.68, 0.6, 0.05]];
    var heatCells = function () { var W = size(); return heat.map(function (h) { return [h[0] * W, h[1] * W, Math.max(1.5, h[2] * W)]; }); };
    var gv = device ? canvasFor(stage, true) : null, cv = canvasFor(stage, false);
    var eng = null, hist = [];

    seg(ctl, "Engine", [["gpu", "GPU · WebGPU"], ["cpu", "CPU · JavaScript"]], state.engine, function (v) { state.engine = v; reset(); }).disable("gpu", !device);
    if (isNb) slider(ctl, "Bodies", 9, 15, state.exp, function (e) { return Math.pow(2, e).toLocaleString(); }, function (e) { state.exp = e; reset(); });
    else slider(ctl, "Grid", 8, 12, state.exp, function (e) { return Math.pow(2, e) + " × " + Math.pow(2, e); }, function (e) { state.exp = e; reset(); });
    var pauseBtn = button(ctl, "Pause", function () { state.paused = !state.paused; pauseBtn.textContent = state.paused ? "Play" : "Pause"; kick(); });
    if (isNb) button(ctl, "Restart", function () { reset(); });
    else {
      button(ctl, "Clear heaters", function () { heat = []; eng && eng.setHeat(heatCells()); });
      stage.addEventListener("click", function (e) {
        var c = (state.engine === "gpu" && gv ? gv : cv).canvas, r = c.getBoundingClientRect();
        var side = Math.min(r.width, r.height), ox = (r.width - side) / 2;
        var u = (e.clientX - r.left - ox) / side, v = (e.clientY - r.top) / side;
        if (u < 0 || u > 1 || v < 0 || v > 1) return;
        heat.push([u, v, 0.03]);
        if (heat.length > MAX_HEAT) heat.shift();
        eng && eng.setHeat(heatCells());
      });
    }

    var unitWork = function () { var s = size(); return isNb ? s * (s - 1) : s * s; };
    function report(steps, ms) {
      hist.push([steps, ms]);
      if (hist.length > 12) hist.shift();
      var S = 0, T = 0;
      hist.forEach(function (h) { S += h[0]; T += h[1]; });
      var sps = S / (T / 1000), r = sps * unitWork();
      $(kind + "Steps").textContent = rate(sps);
      $(kind + "Ms").textContent = F.ms(T / S) + " per step";
      $(kind + "Rate").textContent = F.big(r);
      if (!isNb) $("stBw").textContent = "≈ " + rate(r * 8 / 1e9) + " GB/s moved (read + write, 4 bytes each)";
      var b = (state.best[size()] = state.best[size()] || {});
      b[state.engine] = Math.max(b[state.engine] || 0, r);
      versus();
    }
    function versus() {
      var b = state.best[size()] || {}, label = isNb ? size().toLocaleString() + " bodies" : size() + " × " + size();
      if (b.gpu && b.cpu) { $(kind + "Vs").textContent = "GPU " + F.times(b.gpu / b.cpu) + " faster"; $(kind + "VsS").textContent = "at " + label + ", best of each engine"; }
      else { $(kind + "Vs").textContent = "–"; $(kind + "VsS").textContent = device ? "run the " + (b.gpu ? "CPU" : "GPU") + " engine at " + label + " too" : "needs WebGPU for the comparison"; }
    }

    var lut = null, off = null;
    function drawCPU(res) {
      var c = cv.canvas, ctx = cv.ctx, w = c.width, h = c.height;
      ctx.fillStyle = "#0b1220"; ctx.fillRect(0, 0, w, h);
      if (isNb) {
        var f = res.data, m = Math.min(w, h) * 0.95 / 2, s = Math.max(1, Math.round(1.3 * (window.devicePixelRatio || 1)));
        for (var i = 0; i < size(); i++) {
          var o = i * 6, t = Math.min(1, Math.hypot(f[o + 2], f[o + 3]) / 12);
          ctx.fillStyle = "rgba(" + Math.round(92 + 163 * t) + "," + Math.round(133 + 25 * t) + "," + Math.round(255 - 179 * t) + ",0.8)";
          ctx.fillRect(w / 2 + f[o] * m, h / 2 - f[o + 1] * m, s, s);
        }
        return;
      }
      if (!lut) {
        lut = new Uint8ClampedArray(768);
        var st = [[11, 18, 32], [194, 87, 13], [255, 237, 158]];
        for (var q = 0; q < 256; q++) {
          var tt = Math.sqrt(q / 255), A = tt < 0.5 ? st[0] : st[1], B = tt < 0.5 ? st[1] : st[2], k = tt < 0.5 ? tt * 2 : (tt - 0.5) * 2;
          for (var j = 0; j < 3; j++) lut[q * 3 + j] = A[j] + (B[j] - A[j]) * k;
        }
      }
      if (!off || off.width !== res.w) { off = document.createElement("canvas"); off.width = res.w; off.height = res.h; }
      var octx = off.getContext("2d"), id = octx.createImageData(res.w, res.h);
      for (var p = 0; p < res.img.length; p++) {
        var kk = Math.max(0, Math.min(255, Math.round(res.img[p] * 255))) * 3;
        id.data[p * 4] = lut[kk]; id.data[p * 4 + 1] = lut[kk + 1]; id.data[p * 4 + 2] = lut[kk + 2]; id.data[p * 4 + 3] = 255;
      }
      octx.putImageData(id, 0, 0);
      var side = Math.min(w, h);
      ctx.imageSmoothingEnabled = false;
      ctx.drawImage(off, (w - side) / 2, 0, side, side);
    }

    function reset() {
      if (eng) eng.destroy();
      hist = [];
      [kind + "Steps", kind + "Rate"].forEach(function (id) { $(id).textContent = "–"; });
      $(kind + "Ms").innerHTML = "&nbsp;";
      var gpu = state.engine === "gpu" && device;
      eng = isNb ? (gpu ? nbGPU(size()) : nbCPU(size())) : (gpu ? stGPU(size(), heatCells()) : stCPU(size(), heatCells()));
      eng.perFrame = isNb ? 1 : 4;
      if (gv) gv.canvas.hidden = !gpu;
      cv.canvas.hidden = !!gpu;
      $(kind + "Tag").textContent = (gpu ? "GPU" : "CPU") + " · " + (isNb ? size().toLocaleString() + " bodies" : size() + " × " + size() + " cells");
      versus();
      kick();
    }

    var looping = false;
    async function loop() {
      looping = true;
      while (state.visible && !state.paused) {
        var e = eng;
        if (e.steps) {
          var ms = await e.steps(e.perFrame);
          if (e !== eng) continue;
          report(e.perFrame, ms);
          e.perFrame = Math.max(1, Math.min(isNb ? 64 : 512, Math.round(e.perFrame * Math.min(2, 12 / Math.max(ms, 0.1)))));
          e.draw(gv);
          await frame();
        } else {
          var res = await e.run(30, true);
          if (e !== eng) continue;
          report(res.steps, res.ms);
          drawCPU(res);
          await frame();
        }
      }
      looping = false;
    }
    function kick() { if (!looping && state.visible && !state.paused) loop(); }
    onScreen(stage, function (v) { state.visible = v; kick(); });
    reset();
  }

  async function launch(kind) {
    var btn = $(kind + "Go");
    btn.disabled = true; btn.textContent = "Starting…";
    await initGPU();
    $(kind + "Launch").hidden = true;
    $(kind + "Live").hidden = false;
    if (!device) $("gpuNote").textContent = gpuWhy;
    try { demo(kind); } catch (e) { console.error(e); $(kind + "Live").insertAdjacentHTML("afterbegin", '<p class="caveat">The demo failed to start: ' + e.message + "</p>"); }
  }
  // the panels this wires up are optional; the measurement hook below isn't
  if ($("nbGo")) $("nbGo").addEventListener("click", function () { launch("nb"); });
  if ($("stGo")) $("stGo").addEventListener("click", function () { launch("st"); });
  // say up front, without starting anything, when there's no WebGPU at all
  if (!navigator.gpu && $("nbGo")) {
    ["nbGo", "stGo"].forEach(function (id) { $(id).textContent = "Run it live (CPU only here)"; });
    $("gpuNote").textContent = "This browser has no WebGPU (Chrome, Edge and Safari 26+ have it), so the live demos would run on the CPU only. The measured results above don't need it.";
  }

  // ====================================================== measurement hook
  // Steady-state throughput of every engine at a few sizes, no drawing.
  // Used once by bench/browser-bench.mjs to record the browser results.
  async function measureOne(make, seconds) {
    var e = make(), best = 0, t0 = performance.now(), k = 1;
    try {
      if (e.steps) {
        var w0 = performance.now();
        while (performance.now() - w0 < 500) await e.steps(k);   // let the GPU clock ramp up
        while (performance.now() - t0 < seconds * 1000 + 500) {
          var ms = await e.steps(k);
          best = Math.max(best, k / (ms / 1000));
          k = Math.max(1, Math.min(1024, Math.round(k * Math.min(2, 20 / Math.max(ms, 0.05)))));
        }
      } else {
        while (performance.now() - t0 < seconds * 1000) {
          var r = await e.run(250, false);
          best = Math.max(best, r.steps / (r.ms / 1000));
        }
      }
    } finally { e.destroy(); }
    return best;   // steps per second
  }
  window.LiveBench = {
    measureAll: async function (opts) {
      opts = opts || {};
      var secs = opts.seconds || 2;
      await initGPU();
      var out = { nbody: [], stencil: [] };
      var nbSizes = opts.nbody || [1024, 4096, 16384], stSizes = opts.stencil || [512, 1024, 2048, 4096];
      for (var i = 0; i < nbSizes.length; i++) {
        var N = nbSizes[i], row = { label: N.toLocaleString() + " bodies", n: N };
        if (device) row.gpu = (await measureOne(function () { return nbGPU(N); }, secs)) * N * (N - 1);
        if (N <= 4096) row.cpu = (await measureOne(function () { return nbCPU(N); }, secs)) * N * (N - 1);
        out.nbody.push(row);
      }
      for (var j = 0; j < stSizes.length; j++) {
        var W = stSizes[j], srow = { label: W + " × " + W, size: W };
        if (device) srow.gpu = (await measureOne(function () { return stGPU(W, []); }, secs)) * W * W;
        srow.cpu = (await measureOne(function () { return stCPU(W, []); }, secs)) * W * W;
        out.stencil.push(srow);
      }
      out.webgpu = !!device;
      return out;
    },
  };
})();
