// ============================================================================
// Tissue Clocks minicourse — interactivity
// All chart data below is real, computed in analysis/*.py — see results.json,
// gap_by_hardy.csv, gap_by_tissue.csv. Nothing here is mocked.
// ============================================================================

const RESULTS = {
  "Brain - Cortex":      { n_train: 337, n_test: 86,  accuracy: 0.4419, mae: 7.44,  baseline: 7.33  },
  "Colon - Sigmoid":     { n_train: 633, n_test: 159, accuracy: 0.327,  mae: 10.00, baseline: 13.27 },
  "Colon - Transverse":  { n_train: 740, n_test: 188, accuracy: 0.367,  mae: 9.26,  baseline: 13.24 },
  "Lung":                { n_train: 681, n_test: 169, accuracy: 0.4497, mae: 7.93,  baseline: 12.13 },
  "Skin (not sun-exp.)": { n_train: 646, n_test: 162, accuracy: 0.3889, mae: 8.33,  baseline: 12.90 },
  "Skin (sun-exp.)":     { n_train: 795, n_test: 195, accuracy: 0.3897, mae: 7.79,  baseline: 13.18 },
};

const HARDY_GAP = [
  { label: "Fast death\n(violent)",   mean: 4.12,  sem: 1.73, n: 17  },
  { label: "Fast death\n(natural)",   mean: 2.76,  sem: 0.54, n: 275 },
  { label: "Intermediate\ndeath",     mean: -2.97, sem: 1.03, n: 74  },
  { label: "Slow death",              mean: 3.36,  sem: 0.83, n: 152 },
  { label: "Ventilator\ncase",        mean: 6.49,  sem: 0.60, n: 441 },
];

const CONFUSION = {
  labels: ["20-29", "30-39", "40-49", "50-59", "60-69", "70-79"],
  // row-normalized, real values from analysis/test_predictions.csv confusion_matrix
  matrix: [
    [0.35, 0.07, 0.19, 0.35, 0.04, 0.00],
    [0.12, 0.03, 0.18, 0.53, 0.14, 0.00],
    [0.03, 0.02, 0.14, 0.48, 0.33, 0.00],
    [0.01, 0.00, 0.05, 0.40, 0.54, 0.00],
    [0.00, 0.00, 0.03, 0.29, 0.67, 0.00],
    [0.00, 0.00, 0.00, 0.26, 0.74, 0.00],
  ],
};

const TISSUE_COUNTS = [
  { label: "Skin (sun-exposed)", value: 990 },
  { label: "Colon - Transverse", value: 928 },
  { label: "Lung", value: 850 },
  { label: "Skin (not sun-exp.)", value: 808 },
  { label: "Colon - Sigmoid", value: 792 },
  { label: "Brain - Cortex", value: 423 },
];

const AGE_COUNTS = [
  { label: "20-29", value: 351 },
  { label: "30-39", value: 353 },
  { label: "40-49", value: 702 },
  { label: "50-59", value: 1528 },
  { label: "60-69", value: 1681 },
  { label: "70-79", value: 176 },
];

// ---------------------------------------------------------------- utils --

function css(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function isDarkMode() {
  const current = document.documentElement.getAttribute("data-theme");
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  return current ? current === "dark" : prefersDark;
}

function hexToRgb(hex) {
  hex = hex.replace("#", "");
  if (hex.length === 3) hex = hex.split("").map(c => c + c).join("");
  const num = parseInt(hex, 16);
  return [(num >> 16) & 255, (num >> 8) & 255, num & 255];
}

function mixRgb(rgbA, rgbB, t) {
  return [0, 1, 2].map(i => Math.round(rgbA[i] * t + rgbB[i] * (1 - t)));
}

// relative luminance -> best text color, using the exact crossover point
// where black-on-bg and white-on-bg contrast ratios are equal (~0.179),
// not a naive 0.5 midpoint.
function textColorFor(rgb) {
  const [r, g, b] = rgb.map(v => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  });
  const lum = 0.2126 * r + 0.7152 * g + 0.0722 * b;
  return lum > 0.179 ? "#0b0b0b" : "#ffffff";
}

function makeTooltip(container) {
  const el = document.createElement("div");
  el.className = "tooltip";
  container.style.position = "relative";
  container.appendChild(el);
  return {
    show(x, y, html) {
      el.innerHTML = html;
      el.style.left = x + "px";
      el.style.top = (y - 8) + "px";
      el.classList.add("visible");
    },
    hide() { el.classList.remove("visible"); },
  };
}

// ------------------------------------------------------- simple bar chart --

function renderBarChart(containerId, data, opts) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const tooltip = makeTooltip(container);
  const maxVal = Math.max(...data.map(d => Math.max(...opts.series.map(s => d[s.key]))));

  const wrap = document.createElement("div");
  wrap.className = "bar-chart";

  data.forEach(d => {
    opts.series.forEach(s => {
      const row = document.createElement("div");
      row.className = "bar-row";

      const label = document.createElement("div");
      label.className = "bar-label";
      label.textContent = opts.series.length > 1 ? `${d.label} — ${s.label}` : d.label;
      row.appendChild(label);

      const track = document.createElement("div");
      track.className = "bar-track";
      const fill = document.createElement("div");
      fill.className = "bar-fill";
      fill.style.background = s.color;
      fill.style.width = "0%";
      track.appendChild(fill);
      row.appendChild(track);

      const val = document.createElement("div");
      val.className = "bar-value";
      val.textContent = opts.formatValue ? opts.formatValue(d[s.key]) : d[s.key];
      row.appendChild(val);

      row.addEventListener("mouseenter", (e) => {
        const rect = container.getBoundingClientRect();
        const rowRect = row.getBoundingClientRect();
        tooltip.show(rowRect.left - rect.left + rowRect.width / 2, rowRect.top - rect.top,
          opts.tooltip ? opts.tooltip(d, s) : `${d[s.key]}`);
      });
      row.addEventListener("mouseleave", () => tooltip.hide());

      wrap.appendChild(row);

      requestAnimationFrame(() => {
        setTimeout(() => { fill.style.width = (d[s.key] / maxVal * 100) + "%"; }, 30);
      });
    });
  });

  container.appendChild(wrap);
}

// ------------------------------------------------------ diverging chart --

function renderDivergingChart(containerId, data) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const tooltip = makeTooltip(container);

  const w = container.clientWidth || 640;
  const h = 280;
  const marginL = 20, marginR = 20, marginT = 20, marginB = 50;
  const plotW = w - marginL - marginR;
  const plotH = h - marginT - marginB;
  const maxAbs = Math.max(...data.map(d => Math.abs(d.mean) + d.sem)) * 1.25;
  const barW = plotW / data.length * 0.55;
  const zeroY = marginT + plotH / 2;

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
  svg.setAttribute("width", "100%");
  svg.style.overflow = "visible";

  // zero line
  const zeroLine = document.createElementNS("http://www.w3.org/2000/svg", "line");
  zeroLine.setAttribute("x1", marginL); zeroLine.setAttribute("x2", w - marginR);
  zeroLine.setAttribute("y1", zeroY); zeroLine.setAttribute("y2", zeroY);
  zeroLine.setAttribute("stroke", css("--baseline-axis"));
  zeroLine.setAttribute("stroke-width", "1");
  svg.appendChild(zeroLine);

  data.forEach((d, i) => {
    const cx = marginL + (i + 0.5) * (plotW / data.length);
    const barH = Math.abs(d.mean) / maxAbs * (plotH / 2);
    const y = d.mean >= 0 ? zeroY - barH : zeroY;
    const color = d.mean >= 0 ? css("--accent-orange") : css("--accent-aqua");

    const g = document.createElementNS("http://www.w3.org/2000/svg", "g");

    const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    rect.setAttribute("x", cx - barW / 2);
    rect.setAttribute("y", y);
    rect.setAttribute("width", barW);
    rect.setAttribute("height", 0);
    rect.setAttribute("fill", color);
    rect.setAttribute("rx", 2);
    g.appendChild(rect);

    // error bar
    const semPx = d.sem / maxAbs * (plotH / 2);
    const errTop = document.createElementNS("http://www.w3.org/2000/svg", "line");
    const barCenterY = d.mean >= 0 ? y : y + barH;
    errTop.setAttribute("x1", cx); errTop.setAttribute("x2", cx);
    errTop.setAttribute("y1", barCenterY - semPx); errTop.setAttribute("y2", barCenterY + semPx);
    errTop.setAttribute("stroke", css("--text-primary"));
    errTop.setAttribute("stroke-width", "1.5");
    g.appendChild(errTop);
    [-1, 1].forEach(sign => {
      const cap = document.createElementNS("http://www.w3.org/2000/svg", "line");
      cap.setAttribute("x1", cx - 4); cap.setAttribute("x2", cx + 4);
      cap.setAttribute("y1", barCenterY + sign * semPx); cap.setAttribute("y2", barCenterY + sign * semPx);
      cap.setAttribute("stroke", css("--text-primary"));
      cap.setAttribute("stroke-width", "1.5");
      g.appendChild(cap);
    });

    // label
    const label = document.createElementNS("http://www.w3.org/2000/svg", "text");
    label.setAttribute("x", cx);
    label.setAttribute("y", h - marginB + 16);
    label.setAttribute("text-anchor", "middle");
    label.setAttribute("font-size", "10.5");
    label.setAttribute("fill", css("--text-secondary"));
    d.label.split("\n").forEach((line, li) => {
      const tspan = document.createElementNS("http://www.w3.org/2000/svg", "tspan");
      tspan.setAttribute("x", cx);
      tspan.setAttribute("dy", li === 0 ? 0 : 12);
      tspan.textContent = line;
      label.appendChild(tspan);
    });
    g.appendChild(label);

    // hit area
    const hit = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    hit.setAttribute("x", cx - plotW / data.length / 2);
    hit.setAttribute("y", marginT);
    hit.setAttribute("width", plotW / data.length);
    hit.setAttribute("height", plotH);
    hit.setAttribute("fill", "transparent");
    hit.style.cursor = "pointer";
    hit.addEventListener("mouseenter", () => {
      const rect2 = container.getBoundingClientRect();
      tooltip.show(cx / w * rect2.width, (y - 6) / h * rect2.height,
        `<strong>${d.label.replace("\n"," ")}</strong><br>mean gap: ${d.mean > 0 ? "+" : ""}${d.mean.toFixed(1)} yr &plusmn; ${d.sem.toFixed(1)} SEM<br>n = ${d.n}`);
    });
    hit.addEventListener("mouseleave", () => tooltip.hide());
    g.appendChild(hit);

    svg.appendChild(g);

    requestAnimationFrame(() => {
      setTimeout(() => {
        rect.setAttribute("height", barH);
        rect.setAttribute("y", y);
      }, 30 + i * 40);
    });
  });

  container.appendChild(svg);
}

// ----------------------------------------------------- confusion matrix --

function renderConfusionMatrix(containerId, data) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const tooltip = makeTooltip(container);

  const n = data.labels.length;
  const w = 460, h = 460;
  const marginL = 62, marginT = 14, marginR = 14, marginB = 56;
  const cellW = (w - marginL - marginR) / n;
  const cellH = (h - marginT - marginB) / n;

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${w} ${h}`);
  svg.setAttribute("width", "100%");
  svg.style.maxWidth = "460px";
  svg.style.display = "block";
  svg.style.margin = "0 auto";

  const dark = isDarkMode();
  const gridlineRgb = hexToRgb(css("--gridline"));
  // continuous blend in both themes, not discrete buckets — a 6-bucket lookup put
  // every v below 0.2 in the same bucket as v=0, so low-but-nonzero cells were
  // indistinguishable from empty ones.
  const ceilingRgb = dark ? hexToRgb(css("--accent-blue")) : hexToRgb("#0d366b");

  function bgRgbFor(v) {
    // floor at --gridline, not --surface-1: the surface tone is literally the
    // card background, so a v=0 cell would be invisible against it in either theme.
    return mixRgb(ceilingRgb, gridlineRgb, v);
  }

  data.matrix.forEach((row, ri) => {
    row.forEach((v, ci) => {
      const x = marginL + ci * cellW;
      const y = marginT + ri * cellH;
      const bgRgb = bgRgbFor(v);
      const rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");
      rect.setAttribute("class", "cm-cell");
      rect.setAttribute("x", x + 1);
      rect.setAttribute("y", y + 1);
      rect.setAttribute("width", cellW - 2);
      rect.setAttribute("height", cellH - 2);
      rect.setAttribute("fill", `rgb(${bgRgb.join(",")})`);
      rect.setAttribute("stroke", css("--surface-1"));
      rect.setAttribute("rx", 2);
      svg.appendChild(rect);

      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", x + cellW / 2);
      text.setAttribute("y", y + cellH / 2 + 4);
      text.setAttribute("text-anchor", "middle");
      text.setAttribute("font-size", "11.5");
      text.setAttribute("font-weight", "600");
      text.setAttribute("fill", textColorFor(bgRgb));
      text.textContent = v.toFixed(2);
      text.style.pointerEvents = "none";
      svg.appendChild(text);

      rect.addEventListener("mouseenter", () => {
        const containerRect = container.getBoundingClientRect();
        const svgRect = svg.getBoundingClientRect();
        const scaleX = svgRect.width / w;
        const scaleY = svgRect.height / h;
        const offsetX = svgRect.left - containerRect.left;
        const offsetY = svgRect.top - containerRect.top;
        tooltip.show(offsetX + (x + cellW / 2) * scaleX, offsetY + y * scaleY,
          `Actual <strong>${data.labels[ri]}</strong> &rarr; predicted <strong>${data.labels[ci]}</strong><br>${(v*100).toFixed(0)}% of slides in this row`);
      });
      rect.addEventListener("mouseleave", () => tooltip.hide());
    });
  });

  // row labels (actual)
  data.labels.forEach((lab, i) => {
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", marginL - 8);
    text.setAttribute("y", marginT + i * cellH + cellH / 2 + 4);
    text.setAttribute("text-anchor", "end");
    text.setAttribute("font-size", "11");
    text.setAttribute("fill", css("--text-secondary"));
    text.textContent = lab;
    svg.appendChild(text);
  });
  // col labels (predicted)
  data.labels.forEach((lab, i) => {
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", marginL + i * cellW + cellW / 2);
    text.setAttribute("y", h - marginB + 16);
    text.setAttribute("text-anchor", "end");
    text.setAttribute("font-size", "11");
    text.setAttribute("fill", css("--text-secondary"));
    text.setAttribute("transform", `rotate(-40 ${marginL + i * cellW + cellW / 2} ${h - marginB + 16})`);
    text.textContent = lab;
    svg.appendChild(text);
  });
  // axis titles
  const yAxisTitle = document.createElementNS("http://www.w3.org/2000/svg", "text");
  yAxisTitle.setAttribute("x", -h / 2); yAxisTitle.setAttribute("y", 14);
  yAxisTitle.setAttribute("transform", "rotate(-90)");
  yAxisTitle.setAttribute("text-anchor", "middle");
  yAxisTitle.setAttribute("font-size", "11"); yAxisTitle.setAttribute("font-weight", "700");
  yAxisTitle.setAttribute("fill", css("--text-muted"));
  yAxisTitle.textContent = "ACTUAL AGE BRACKET";
  svg.appendChild(yAxisTitle);

  const xAxisTitle = document.createElementNS("http://www.w3.org/2000/svg", "text");
  xAxisTitle.setAttribute("x", marginL + (w - marginL - marginR) / 2); xAxisTitle.setAttribute("y", h - 4);
  xAxisTitle.setAttribute("text-anchor", "middle");
  xAxisTitle.setAttribute("font-size", "11"); xAxisTitle.setAttribute("font-weight", "700");
  xAxisTitle.setAttribute("fill", css("--text-muted"));
  xAxisTitle.textContent = "PREDICTED AGE BRACKET";
  svg.appendChild(xAxisTitle);

  container.appendChild(svg);
}

// ----------------------------------------------------------------- nav --

function initScrollSpy() {
  const sections = document.querySelectorAll("section.course-section[id]");
  const links = document.querySelectorAll(".nav-link");
  if (!sections.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        links.forEach(l => l.classList.remove("active"));
        const active = document.querySelector(`.nav-link[href="#${entry.target.id}"]`);
        if (active) active.classList.add("active");
      }
    });
  }, { rootMargin: "-40% 0px -55% 0px" });

  sections.forEach(s => observer.observe(s));
}

function initThemeToggle() {
  const btn = document.getElementById("theme-toggle");
  if (!btn) return;
  const stored = localStorage.getItem("theme");
  if (stored) document.documentElement.setAttribute("data-theme", stored);
  updateToggleLabel();

  btn.addEventListener("click", () => {
    const current = document.documentElement.getAttribute("data-theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    let next;
    if (!current) next = prefersDark ? "light" : "dark";
    else if (current === "dark") next = "light";
    else next = "dark";
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("theme", next);
    updateToggleLabel();
    // re-render charts so SVG colors pick up new CSS var values
    renderAllCharts();
  });

  function updateToggleLabel() {
    const current = document.documentElement.getAttribute("data-theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = current ? current === "dark" : prefersDark;
    btn.textContent = isDark ? "Light mode" : "Dark mode";
  }
}

// ---------------------------------------------------------------- quiz --

function initQuiz() {
  document.querySelectorAll(".quiz-block").forEach(block => {
    const options = block.querySelectorAll(".quiz-option");
    const feedback = block.querySelector(".quiz-feedback");

    const reset = document.createElement("button");
    reset.type = "button";
    reset.className = "quiz-reset";
    reset.textContent = "Try again";
    reset.hidden = true;
    feedback.insertAdjacentElement("afterend", reset);

    reset.addEventListener("click", () => {
      delete block.dataset.answered;
      options.forEach(o => o.classList.remove("correct", "incorrect"));
      feedback.textContent = "";
      reset.hidden = true;
    });

    options.forEach(opt => {
      opt.addEventListener("click", () => {
        if (block.dataset.answered) return;
        block.dataset.answered = "true";
        const isCorrect = opt.dataset.correct === "true";
        options.forEach(o => {
          if (o.dataset.correct === "true") o.classList.add("correct");
          else if (o === opt) o.classList.add("incorrect");
        });
        feedback.textContent = isCorrect
          ? "Correct — " + block.dataset.explain
          : "Not quite — " + block.dataset.explain;
        reset.hidden = false;
      });
    });
  });
}

// ------------------------------------------------------------- render all --

function renderAllCharts() {
  document.querySelectorAll('[data-chart]').forEach(el => (el.innerHTML = ""));

  renderBarChart("chart-tissue-dist", TISSUE_COUNTS.map(d => ({ label: d.label, value: d.value })), {
    series: [{ key: "value", label: "slides", color: css("--accent-blue") }],
    formatValue: v => v.toLocaleString(),
    tooltip: d => `<strong>${d.label}</strong><br>${d.value.toLocaleString()} slides`,
  });

  renderBarChart("chart-age-dist", AGE_COUNTS.map(d => ({ label: d.label, value: d.value })), {
    series: [{ key: "value", label: "slides", color: css("--accent-orange") }],
    formatValue: v => v.toLocaleString(),
    tooltip: d => `<strong>${d.label}</strong><br>${d.value.toLocaleString()} slides`,
  });

  const maeData = Object.entries(RESULTS).map(([label, r]) => ({ label, mae: r.mae, baseline: r.baseline }));
  renderBarChart("chart-mae", maeData, {
    series: [
      { key: "baseline", label: "baseline", color: css("--text-muted") },
      { key: "mae", label: "our clock", color: css("--accent-aqua") },
    ],
    formatValue: v => v.toFixed(1) + " yr",
    tooltip: (d, s) => `<strong>${d.label}</strong><br>${s.label}: ${d[s.key].toFixed(2)} years MAE`,
  });

  renderDivergingChart("chart-hardy-gap", HARDY_GAP);
  renderConfusionMatrix("chart-confusion", CONFUSION);
}

document.addEventListener("DOMContentLoaded", () => {
  initScrollSpy();
  initThemeToggle();
  initQuiz();
  renderAllCharts();
  window.addEventListener("resize", () => {
    clearTimeout(window.__resizeT);
    window.__resizeT = setTimeout(renderAllCharts, 200);
  });
});
