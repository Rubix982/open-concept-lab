// Results first: draws the measured numbers from window.NATIVE_RESULTS
// (data/native.js, written by bench/export.py). A classic script with no
// fetch, so the page works opened straight from disk.
(function () {
  "use strict";
  var R = window.NATIVE_RESULTS;
  var $ = function (id) { return document.getElementById(id); };
  var css = function (name) { return getComputedStyle(document.documentElement).getPropertyValue(name).trim(); };

  function big(x) {
    var u = [[1e12, "T"], [1e9, "G"], [1e6, "M"], [1e3, "k"]];
    for (var i = 0; i < u.length; i++) if (x >= u[i][0]) { var v = x / u[i][0]; return v.toFixed(v >= 100 ? 0 : 1) + " " + u[i][1]; }
    return x.toFixed(0);
  }
  function ms(x) { return x >= 100 ? x.toFixed(0) + " ms" : x >= 10 ? x.toFixed(1) + " ms" : x >= 1 ? x.toFixed(2) + " ms" : (x * 1000).toFixed(0) + " µs"; }
  function times(x) { return (x >= 10 ? x.toFixed(0) : x.toFixed(1)) + "×"; }
  window.ResultsFmt = { big: big, ms: ms, times: times };

  if (!R || !R.native) return;   // the placeholder message stays
  var d = R.native, m = d.machine, nb = d.nbody, st = d.stencil;
  var lastNb = nb[nb.length - 1], lastSt = st[st.length - 1];
  var bigSt = st.filter(function (r) { return r.size >= 4096; });
  if (!bigSt.length) bigSt = [lastSt];
  var stSpeed = bigSt.reduce(function (a, r) { return a + r.cpuMs / r.gpuMs; }, 0) / bigSt.length;
  var gbps = Math.max.apply(null, bigSt.map(function (r) { return r.gpuGBps8; }));

  var nbTable = nb.map(function (r) {
    return "<tr><td>" + r.n.toLocaleString() + "</td><td>" + r.cpuMs.toFixed(3) + "</td><td>" + r.gpuMs.toFixed(3) + "</td><td>" + times(r.cpuMs / r.gpuMs) +
      "</td><td>" + big(r.cpuInteractionsPerSec) + "</td><td>" + big(r.gpuInteractionsPerSec) + "</td></tr>";
  }).join("");
  var stTable = st.map(function (r) {
    return "<tr><td>" + r.size + " × " + r.size + "</td><td>" + r.cpuMs.toFixed(3) + "</td><td>" + r.gpuMs.toFixed(3) + "</td><td>" + times(r.cpuMs / r.gpuMs) +
      "</td><td>" + big(r.cpuCellsPerSec) + "</td><td>" + big(r.gpuCellsPerSec) + "</td><td>" + r.gpuGBps8.toFixed(0) + "</td></tr>";
  }).join("");

  $("results").innerHTML =
    '<p class="machine">Measured on <b>' + m.cpu + "</b> (" + m.model + ", " + m.cpuThreads + " CPU cores, " + Math.round(m.memoryGB) + " GB memory shared by CPU and GPU), " + d.date + ".</p>" +
    '<div class="tiles">' +
      '<div class="tile"><div class="k">Gravity · ' + lastNb.n.toLocaleString() + ' bodies</div><div class="v">GPU ' + times(lastNb.cpuMs / lastNb.gpuMs) + '</div><div class="s">' + ms(lastNb.gpuMs) + " vs " + ms(lastNb.cpuMs) + " per step · " + big(lastNb.gpuInteractionsPerSec) + " vs " + big(lastNb.cpuInteractionsPerSec) + " force calculations/s</div></div>" +
      '<div class="tile"><div class="k">Heat · ' + lastSt.size + " × " + lastSt.size + ' grid</div><div class="v">GPU ' + times(lastSt.cpuMs / lastSt.gpuMs) + '</div><div class="s">' + ms(lastSt.gpuMs) + " vs " + ms(lastSt.cpuMs) + " per step · " + big(lastSt.gpuCellsPerSec) + " vs " + big(lastSt.cpuCellsPerSec) + " cell updates/s</div></div>" +
      '<div class="tile"><div class="k">GPU memory traffic, heat</div><div class="v">' + gbps.toFixed(0) + ' GB/s</div><div class="s">on grids of 4096² and up, at 8 bytes per cell update (one read, one write)</div></div>' +
    "</div>" +
    '<div class="charts">' +
      '<div class="chart" id="cNb"><h3>Gravity: time per step</h3><p class="cap">More bodies → right; slower → up. Both axes logarithmic.</p></div>' +
      '<div class="chart" id="cSt"><h3>Heat: time per step</h3><p class="cap">Bigger grids → right; slower → up. Both axes logarithmic.</p></div>' +
    "</div>" +
    '<details><summary>Every measurement, as tables</summary><div class="scrollx">' +
      "<table><thead><tr><th>Bodies</th><th>CPU ms/step</th><th>GPU ms/step</th><th>GPU faster</th><th>CPU forces/s</th><th>GPU forces/s</th></tr></thead><tbody>" + nbTable + "</tbody></table>" +
      "<table><thead><tr><th>Grid</th><th>CPU ms/step</th><th>GPU ms/step</th><th>GPU faster</th><th>CPU cells/s</th><th>GPU cells/s</th><th>GPU GB/s</th></tr></thead><tbody>" + stTable + "</tbody></table>" +
    "</div></details>" +
    '<p class="caveat">How it was measured: ' + d.method + " CPU means the same arithmetic in C, one thread per core (" + m.cpuThreads + "). The machine was busy with other work during this run (one-minute load average " +
      (d.loadAverage1m != null ? d.loadAverage1m.toFixed(1) : "not recorded") + " on " + m.cpuThreads + " cores). That mostly disturbs the smallest sizes, which take a fraction of a millisecond; the largest sizes held steady across repeated runs.</p>";

  chart($("cNb"), nb.map(function (r) { return { x: r.n, cpu: r.cpuMs, gpu: r.gpuMs, label: r.n.toLocaleString() + " bodies" }; }), function (x) { return x >= 1024 ? x / 1024 + "k" : String(x); }, "CPU, " + m.cpuThreads + " cores (C)", "GPU (Metal)");
  chart($("cSt"), st.map(function (r) { return { x: r.size, cpu: r.cpuMs, gpu: r.gpuMs, label: r.size + " × " + r.size + " grid" }; }), String, "CPU, " + m.cpuThreads + " cores (C)", "GPU (Metal)");

  var first = nb[0];
  $("why").innerHTML =
    '<div class="note"><h3>Gravity is limited by arithmetic</h3>' +
      "<p>At " + lastNb.n.toLocaleString() + " bodies one step is " + big(lastNb.n * (lastNb.n - 1)) + " force calculations, yet the bodies take only " + (lastNb.n * 24 / 1048576).toFixed(1) +
      " MB and are read over and over from cache. Little time goes to waiting on memory, so the job goes to whoever has the most arithmetic units: the GPU was <b>" + times(lastNb.cpuMs / lastNb.gpuMs) + " faster</b> than all " + m.cpuThreads + " CPU cores.</p>" +
      "<p>Double the bodies and the work quadruples, on both sides. At " + first.n.toLocaleString() + " bodies the lead was only " + times(first.cpuMs / first.gpuMs) + ": that's " + first.n.toLocaleString() + " threads, too few to fill the GPU, and the fixed cost of starting work on it counts for more.</p></div>" +
    '<div class="note"><h3>Heat is limited by memory</h3>' +
      "<p>A cell update is about six arithmetic operations but 8 bytes of memory traffic. On the largest grids the GPU moved up to <b>" + gbps.toFixed(0) + " GB/s</b>, close to what the chip's memory can deliver, and the CPU draws on the same memory. So the GPU's lead shrinks to <b>" + bigSt.map(function (r) { return times(r.cpuMs / r.gpuMs) + " at " + r.size + "²"; }).join("</b> and <b>") + "</b>: both sides are waiting on the same thing.</p>" +
      "<p>On small grids the whole plate fits in on-chip caches and the GPU looks far faster, partly because this CPU version starts a fresh thread per core on every step, which costs more than the arithmetic at that size.</p></div>";

  // ---- the same workloads in the browser, measured once (optional)
  var b = R.browser;
  if (b) {
    var rows = function (list, unit) {
      return list.map(function (r) {
        return "<tr><td>" + r.label + "</td><td>" + (r.gpu ? big(r.gpu) : "–") + "</td><td>" + (r.cpu ? big(r.cpu) : "–") + "</td><td>" + (r.gpu && r.cpu ? times(r.gpu / r.cpu) : "–") + "</td></tr>";
      }).join("");
    };
    var hero = b.hero && b.hero.webgpu ? b.hero : null;
    var heroHtml = "";
    if (hero) {
      var gMax = hero.galaxy[hero.galaxy.length - 1], hMax = hero.heat[hero.heat.length - 1];
      var gCpu = hero.galaxy.filter(function (r) { return r.cpuRate; }).pop();
      var natMax = nb.filter(function (r) { return r.n === gMax.n; })[0];
      heroHtml =
        "<h2>The animation at full size, on this Mac</h2>" +
        '<p class="sub">The two scenes at the top of this page, run at their largest sizes in ' + b.browser + " on the same Mac and measured compute-only. Your own browser runs them live, sized to what your GPU can keep smooth.</p>" +
        '<div class="tiles">' +
          '<div class="tile"><div class="k">Galaxies · ' + gMax.n.toLocaleString() + ' bodies</div><div class="v">' + big(gMax.gpuRate) + '</div><div class="s">force calculations a second on WebGPU, ' + gMax.gpuStepsPerSec.toFixed(0) + " steps a second" +
            (natMax ? ". The plain native Metal kernel above managed " + big(natMax.gpuInteractionsPerSec) + " at this size; this one loads bodies into fast shared memory 256 at a time (tiling), and that, not the browser, is the difference." : ".") + "</div></div>" +
          '<div class="tile"><div class="k">Heat · ' + hMax.size + " × " + hMax.size + ' cells</div><div class="v">' + big(hMax.gpuRate) + '</div><div class="s">cell updates a second on WebGPU, ' + Math.round(hMax.gpuStepsPerSec).toLocaleString() + " steps a second</div></div>" +
          (gCpu ? '<div class="tile"><div class="k">One CPU core, same JavaScript</div><div class="v">' + big(gCpu.cpuRate) + '</div><div class="s">force calculations a second at ' + gCpu.n.toLocaleString() + " bodies, " + times(gCpu.gpuRate / gCpu.cpuRate) + " slower than WebGPU at that size; the heat plate manages " + big(hMax.cpuRate) + " cell updates a second</div></div>" : "") +
        "</div>" +
        '<details><summary>Every size</summary><div class="scrollx"><table><thead><tr><th>Galaxies</th><th>WebGPU steps/s</th><th>WebGPU forces/s</th><th>One-core JS forces/s</th></tr></thead><tbody>' +
          hero.galaxy.map(function (r) { return "<tr><td>" + r.n.toLocaleString() + " bodies</td><td>" + r.gpuStepsPerSec.toFixed(1) + "</td><td>" + big(r.gpuRate) + "</td><td>" + (r.cpuRate ? big(r.cpuRate) : "not run") + "</td></tr>"; }).join("") +
        '</tbody></table><table><thead><tr><th>Heat</th><th>WebGPU steps/s</th><th>WebGPU cells/s</th><th>One-core JS cells/s</th></tr></thead><tbody>' +
          hero.heat.map(function (r) { return "<tr><td>" + r.size + " × " + r.size + "</td><td>" + Math.round(r.gpuStepsPerSec).toLocaleString() + "</td><td>" + big(r.gpuRate) + "</td><td>" + big(r.cpuRate) + "</td></tr>"; }).join("") +
        "</tbody></table></div></details>" +
        '<p class="caveat">' + (b.heroMethod || "") + "</p>";
    }
    $("browserResults").innerHTML = heroHtml +
      "<h2>The same workloads in a browser</h2>" +
      '<p class="sub">WebGPU compute shaders against JavaScript on one CPU core, measured once in ' + b.browser + " on the same Mac (" + b.date + "): the plain kernels, one thread per body or cell with no tiling, matching the Metal ones.</p>" +
      '<div class="scrollx"><table><thead><tr><th>Gravity</th><th>WebGPU forces/s</th><th>JavaScript forces/s</th><th>WebGPU faster</th></tr></thead><tbody>' + rows(b.nbody) + "</tbody></table>" +
      '<table><thead><tr><th>Heat</th><th>WebGPU cells/s</th><th>JavaScript cells/s</th><th>WebGPU faster</th></tr></thead><tbody>' + rows(b.stencil) + "</tbody></table></div>" +
      '<p class="caveat">' + b.method + (b.loadAverage1m != null ? " The machine was busy with other work at the time (one-minute load average " + b.loadAverage1m.toFixed(1) + "), so these are lower bounds." : "") + "</p>";
  }

  // A two-series log-log line chart with direct labels and a hover readout.
  function chart(el, rows, xfmt, cpuName, gpuName) {
    var W = 520, H = 280, mg = { l: 54, r: 40, t: 26, b: 34 };
    var xs = rows.map(function (r) { return r.x; });
    var ys = [];
    rows.forEach(function (r) { ys.push(r.cpu, r.gpu); });
    var lx0 = Math.log2(xs[0]), lx1 = Math.log2(xs[xs.length - 1]);
    var ly0 = Math.floor(Math.log10(Math.min.apply(null, ys))), ly1 = Math.ceil(Math.log10(Math.max.apply(null, ys)));
    var X = function (x) { return mg.l + ((Math.log2(x) - lx0) / (lx1 - lx0)) * (W - mg.l - mg.r); };
    var Y = function (y) { return H - mg.b - ((Math.log10(y) - ly0) / (ly1 - ly0)) * (H - mg.t - mg.b); };
    var gpu = css("--gpu"), cpu = css("--cpu");
    var s = "";
    for (var e = ly0; e <= ly1; e++) {
      var v = Math.pow(10, e), y = Y(v);
      s += '<line class="grid" x1="' + mg.l + '" x2="' + (W - mg.r) + '" y1="' + y + '" y2="' + y + '"/><text x="' + (mg.l - 6) + '" y="' + (y + 3.5) + '" text-anchor="end">' + (v >= 1 ? v + " ms" : Math.round(v * 1000) + " µs") + "</text>";
    }
    xs.forEach(function (x) { s += '<text x="' + X(x) + '" y="' + (H - mg.b + 16) + '" text-anchor="middle">' + xfmt(x) + "</text>"; });
    var line = function (k, col) {
      return '<polyline fill="none" stroke="' + col + '" stroke-width="2" stroke-linejoin="round" points="' + rows.map(function (r) { return X(r.x) + "," + Y(r[k]); }).join(" ") + '"/>' +
        rows.map(function (r) { return '<circle cx="' + X(r.x) + '" cy="' + Y(r[k]) + '" r="4" fill="' + col + '" stroke="' + css("--raised") + '" stroke-width="2"/>'; }).join("");
    };
    s += line("cpu", cpu) + line("gpu", gpu);
    var last = rows[rows.length - 1];
    s += '<text class="lbl" x="' + (X(last.x) + 8) + '" y="' + (Y(last.cpu) + 4) + '">CPU</text><text class="lbl" x="' + (X(last.x) + 8) + '" y="' + (Y(last.gpu) + 4) + '">GPU</text>';
    s += '<line class="xh" stroke="' + css("--rule-strong") + '" y1="' + mg.t + '" y2="' + (H - mg.b) + '" visibility="hidden"/>';
    s += '<rect x="' + mg.l + '" y="' + mg.t + '" width="' + (W - mg.l - mg.r) + '" height="' + (H - mg.t - mg.b) + '" fill="transparent"/>';
    el.insertAdjacentHTML("beforeend", '<div class="legend"><span><i style="background:' + cpu + '"></i>' + cpuName + '</span><span><i style="background:' + gpu + '"></i>' + gpuName + "</span></div>" +
      '<svg viewBox="0 0 ' + W + " " + H + '" role="img" aria-label="' + el.querySelector("h3").textContent + '">' + s + "</svg>");
    var svg = el.querySelector("svg"), xh = svg.querySelector(".xh"), tip = $("tip");
    svg.addEventListener("pointermove", function (ev) {
      var r = svg.getBoundingClientRect(), px = ((ev.clientX - r.left) / r.width) * W, best = rows[0];
      rows.forEach(function (row) { if (Math.abs(X(row.x) - px) < Math.abs(X(best.x) - px)) best = row; });
      xh.setAttribute("x1", X(best.x)); xh.setAttribute("x2", X(best.x)); xh.setAttribute("visibility", "visible");
      tip.innerHTML = best.label + "<br>CPU <b>" + ms(best.cpu) + "</b> · GPU <b>" + ms(best.gpu) + "</b><br>GPU faster by <b>" + times(best.cpu / best.gpu) + "</b>";
      tip.style.display = "block";
      var tw = tip.offsetWidth, left = ev.clientX + 14;
      if (left + tw > innerWidth - 8) left = ev.clientX - tw - 14;
      tip.style.left = left + scrollX + "px"; tip.style.top = ev.clientY + scrollY + 14 + "px";
    });
    svg.addEventListener("pointerleave", function () { xh.setAttribute("visibility", "hidden"); tip.style.display = "none"; });
  }
})();
