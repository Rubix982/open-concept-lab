let globalEntriesData = []; // will hold all entries once loaded
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const search = $("#search");
const category = $("#category");
const date = $("#date");
const printBtn = $("#print");
const chips = $$("#chips .chip");
const tooltip = $("#heatmap-tooltip");

// Restore last filters
const saved = JSON.parse(localStorage.getItem("lj.filters") || "{}");
if (saved.search) search.value = saved.search;
if (saved.category) category.value = saved.category;
if (saved.date) date.value = saved.date;
if (saved.chip)
  chips.forEach((c) =>
    c.dataset.chip === saved.chip
      ? c.classList.add("active")
      : c.classList.remove("active")
  );

// On DOM ready

document.addEventListener("DOMContentLoaded", () => {
  const loader = document.getElementById("loader");
  const entriesContainer = document.getElementById("entries");

  fetch("./../data/entries.json")
    .then((res) => res.json())
    .then((entriesData) => {
      globalEntriesData = entriesData;
      renderEntries(entriesData); // populate <ul>
      renderYearlyHeatmap();
      loader.style.display = "none"; // hide loader
      entriesContainer.style.display = "block"; // show entries

      // if filters were saved in localStorage, apply them now
      const savedFilters = JSON.parse(
        localStorage.getItem("lj.filters") || "{}"
      );
      if (savedFilters) {
        search.value = savedFilters.search || "";
        category.value = savedFilters.category || "";
        date.value = savedFilters.date || "";
        // update chip selection if needed
      }

      applyFilters(); // filter immediately
    })
    .catch((err) => {
      loader.textContent = "Failed to load entries.";
      console.error("Failed to load entries", err);
    });

  fetch("./../data/categories.json")
    .then((res) => res.json())
    .then((categoryMap) => {
      const categories = Object.keys(categoryMap.categories || {});

      if (categories.length === 0) {
        return;
      }
      // Populate category dropdown
      const categorySelect = document.getElementById("category");

      // By default, always add the "All Categories" option
      const defaultOption = document.createElement("option");
      defaultOption.value = "";
      defaultOption.textContent = "All Categories";
      categorySelect.appendChild(defaultOption);

      categories.forEach((cat) => {
        const option = document.createElement("option");
        option.value = cat;
        option.textContent = cat;
        categorySelect.appendChild(option);
      });

      const chipSelect = document.getElementById("chips");

      categories.forEach((cat) => {
        const chipSpan = document.createElement("span");
        chipSpan.textContent = cat;
        chipSpan.className = "chip";
        chipSpan.setAttribute("data-chip", cat);
        chipSelect.appendChild(chipSpan);
      });

      const heatMapDiv = document.getElementById("heatmap-legend");

      Object.values(categoryMap.categories).forEach((cat) => {
        const legendDiv = document.createElement("div");
        legendDiv.className = "heatmap-legend-item";

        // Background Color
        const legendSpanColor = document.createElement("span");
        legendSpanColor.style.background = "#" + cat.color;
        legendDiv.appendChild(legendSpanColor);

        // Color
        const legendSpanText = document.createElement("span");
        legendSpanText.textContent = cat.name;
        legendDiv.appendChild(legendSpanText);

        heatMapDiv.appendChild(legendDiv);
      });
    })
    .catch((err) => {
      console.error("Failed to load categories.", err);
    });

  const monthLabelsDiv = document.getElementById("month-labels");

  [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
  ].forEach((m) => {
    const span = document.createElement("span");
    span.textContent = m;
    monthLabelsDiv.appendChild(span);
  });

  renderYearlyHeatmap();

  // Event wiring
  [search, category, date].forEach((el) =>
    el.addEventListener("input", applyFilters)
  );
  chips.forEach((ch) =>
    ch.addEventListener("click", () => {
      const wasActive = ch.classList.contains("active");
      chips.forEach((c) => c.classList.remove("active"));
      if (!wasActive) ch.classList.add("active");
      applyFilters();
    })
  );
  printBtn.addEventListener("click", () => window.print());

  // Initial run
  applyFilters();
});

function renderEntries(entries) {
  const ul = document.getElementById("entries");
  if (!ul) return;

  ul.innerHTML = ""; // clear existing content

  entries.forEach((entry) => {
    const li = document.createElement("li");
    li.className = "entry";
    li.dataset.date = entry.date;
    li.dataset.category = entry.category;
    li.dataset.tags = entry.tags.join(",");
    li.id = getLiId(entry);

    li.innerHTML = `
      <a href="${"./content/" + entry.date + "/"}" target="_blank">${
      entry.date
    } — ${entry.category} — ${entry.title}</a>
      <p>${entry.description}</p>
      <div class="badges">
        ${entry.tags
          .map((tag) => `<span class="badge">#${tag}</span>`)
          .join("")}
      </div>
    `;

    ul.appendChild(li);
  });
}

function normalize(s) {
  return (s || "").toLowerCase();
}

function getLiId(entry) {
  return (
    entry.date +
    "__" +
    entry.category +
    "__" +
    entry.title.toLowerCase().replace(/\s+/g, "-")
  );
}

function applyFilters() {
  const q = normalize(search.value);
  const cat = category.value;
  const d = date.value;
  const activeChip = chips.find((c) => c.classList.contains("active"));
  const chipVal = activeChip ? activeChip.dataset.chip : "";

  globalEntriesData.forEach((entry) => {
    const title =
      entry.date +
      " " +
      entry.category +
      " " +
      entry.title +
      " " +
      entry.description;
    const note = entry.description || "";
    const tags = entry.tags || [];
    const hay = normalize([title, note, tags].join(" "));
    const passSearch = q ? hay.includes(q) : true;
    const passCat = cat ? entry.category === cat : true;
    const passDate = d ? entry.date === d : true;
    const passChip = chipVal
      ? entry.category === chipVal ||
        (entry.tags || "").toLowerCase().includes(chipVal.toLowerCase())
      : true;
    const ok = passSearch && passCat && passDate && passChip;
    if (ok) {
      document.getElementById(getLiId(entry)).style.display = "";
    } else {
      document.getElementById(getLiId(entry)).style.display = "none";
    }
  });

  computeStats();
  renderYearlyHeatmap();
  localStorage.setItem(
    "lj.filters",
    JSON.stringify({
      search: search.value,
      category: category.value,
      date: date.value,
      chip: chipVal,
    })
  );
}

function computeStats() {
  // Total entries (visible) & unique days
  $("#stat-total").textContent = globalEntriesData.length;

  const days = new Set(globalEntriesData.map((entry) => entry.date));
  $("#stat-days").textContent = days.size;

  // Top category among visible
  const counts = {};
  globalEntriesData.forEach((entry) => {
    counts[entry.category] = (counts[entry.category] || 0) + 1;
  });
  const top = Object.entries(counts).sort((a, b) => b[1] - a[1])[0];
  $("#stat-top").textContent = top ? `${top[0]} (${top[1]})` : "—";

  // Streak (consecutive days up to today)
  const sorted = Array.from(days).sort();
  const today = new Date();
  const yyyy = today.getFullYear();
  const mm = String(today.getMonth() + 1).padStart(2, "0");
  const dd = String(today.getDate()).padStart(2, "0");
  const todayStr = `${yyyy}-${mm}-${dd}`;

  function prevDateStr(s) {
    const t = new Date(s);
    t.setDate(t.getDate() - 1);
    const y = t.getFullYear();
    const m = String(t.getMonth() + 1).padStart(2, "0");
    const d = String(t.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
  }
  let streak = 0;
  if (sorted.length) {
    let cur = todayStr;
    // Count backwards while we have that date in Set
    while (days.has(cur)) {
      streak++;
      cur = prevDateStr(cur);
    }
  }

  $("#stat-streak").textContent = streak;
}

function renderYearlyHeatmap() {
  const heatmapContainer = $("#heatmap");
  if (!heatmapContainer) return;

  // Organize entries per day with categories
  const dayData = {};
  globalEntriesData.forEach((dataset) => {
    const d = dataset.date;
    const category = dataset.category || "Other";
    const text = dataset.textContent || dataset.innerText || "";

    if (!dayData[d]) dayData[d] = {};
    if (!dayData[d][category]) dayData[d][category] = [];
    dayData[d][category].push(text);
  });

  const today = new Date();
  const start = new Date(today.getFullYear(), 0, 1); // Jan 1
  const end = today;

  heatmapContainer.innerHTML = "";

  // Iterate days of the year
  for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
    let dateStr = d.toISOString().slice(0, 10);
    const dataForDay = dayData[dateStr] || {};
    const count = Object.values(dataForDay).reduce(
      (sum, arr) => sum + arr.length,
      0
    );
    // Count total entries for intensity
    const maxCount = Math.max(
      ...Object.values(dayData).map((day) =>
        Object.values(day).reduce((s, arr) => s + arr.length, 0)
      ),
      1
    );

    const intensity = Math.floor((count / maxCount) * 4);

    const div = document.createElement("div");
    div.className = `heatcell level-${intensity} day`;

    // Optional: dataset category for CSS
    if (Object.keys(dataForDay).length === 1) {
      div.dataset.category = Object.keys(dataForDay)[0];
    }

    const dateObj = new Date(dateStr);
    const year = new Intl.DateTimeFormat("en", { year: "numeric" }).format(
      dateObj
    );
    const month = new Intl.DateTimeFormat("en", { month: "long" }).format(
      dateObj
    );
    const day = new Intl.DateTimeFormat("en", { day: "2-digit" }).format(
      dateObj
    );
    dateStr = `${month} ${day}, ${year}`;

    // Custom tooltip events
    div.addEventListener("mouseenter", (e) => {
      let html = `<strong>${dateStr}</strong> — ${count} entries<br><br>`;
      for (const [category, entries] of Object.entries(dataForDay)) {
        html += `<span style="color:${getCategoryColor(
          category
        )}">${category}</span> (${entries.length}):<br>`;
        entries.forEach((en) => (html += `&nbsp;&nbsp; ${en}<br>`));
      }
      tooltip.innerHTML = html;
      tooltip.style.display = "block";
    });

    div.addEventListener("mousemove", (e) => {
      tooltip.style.left = e.pageX + 15 + "px";
      tooltip.style.top = e.pageY + 15 + "px";
    });

    div.addEventListener("mouseleave", () => {
      tooltip.style.display = "none";
    });

    heatmapContainer.appendChild(div);
  }
}

// helper to match your legend colors
function getCategoryColor(cat) {
  const colors = {
    DB: "#facc15",
    Distributed: "#3b82f6",
    Parallel: "#10b981",
    "Algorithms-C": "#f97316",
    Other: "#888",
  };
  return colors[cat] || "#888";
}
