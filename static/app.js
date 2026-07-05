// Frontend logic: collect inputs, call the API, render the results.

const $ = (id) => document.getElementById(id);
const fileInput = $("fileInput");
const fileDrop = $("fileDrop");
const fileLabel = $("fileLabel");
const runBtn = $("runBtn");
const results = $("results");

fileDrop.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", () => {
  if (fileInput.files.length) {
    fileLabel.textContent = fileInput.files[0].name;
    fileDrop.classList.add("has-file");
  }
});

const fmt = (n, d = 2) =>
  (n === null || n === undefined || isNaN(n)) ? "" : Number(n).toLocaleString("en-US",
    { minimumFractionDigits: d, maximumFractionDigits: d });
const esc = (s) => String(s ?? "").replace(/[&<>]/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

function statusBar(kind, text) {
  return `<div class="status ${kind}">${esc(text)}</div>`;
}

function performanceTable(rows, metric) {
  const head = ["Ad", "Spend", "CTR %", "CVR %", "CPA", "ROAS", "AOV"];
  const body = rows.map((r) => `
    <tr class="${r.winner ? "win" : ""}">
      <td>${esc(r.ad_name)}</td>
      <td class="num">${fmt(r.spend, 0)}</td>
      <td class="num">${fmt(r.CTR)}</td>
      <td class="num">${fmt(r.CVR)}</td>
      <td class="num">${fmt(r.CPA)}</td>
      <td class="num ${metric === "ROAS" ? "roas-strong" : ""}">${fmt(r.ROAS)}</td>
      <td class="num">${fmt(r.AOV)}</td>
    </tr>`).join("");
  return `<table><thead><tr>${head.map((h, i) =>
    `<th>${h}</th>`).join("")}</tr></thead><tbody>${body}</tbody></table>`;
}

function list(items) {
  return (items && items.length)
    ? `<ul>${items.map((i) => `<li>${esc(i)}</li>`).join("")}</ul>`
    : `<p class="hint">—</p>`;
}

function winnerBreakdownBlock(performance, analyses) {
  const winners = (performance || []).filter((r) => r.winner);
  if (!winners.length) return "";
  const cards = winners.map((row) => {
    const a = (analyses && analyses[row.ad_name]) || {};
    const hookStyle = a.hook_style || {};
    const coreAngle = a.core_angle_mechanism || {};
    const visualScript = a.visual_script_structure || {};
    return `
    <div class="concept">
      <div class="name"><span class="badge">WINNER</span>${esc(row.ad_name)}</div>
      <div class="field"><b>Hook angle:</b> ${esc(hookStyle.angle)}</div>
      <div class="field"><b>Why it grabs them:</b> ${esc(hookStyle.why_it_grabs_them)}</div>
      <div class="field"><b>Main message:</b> ${esc(coreAngle.main_message)}</div>
      <div class="field"><b>Must-have positioning:</b> ${esc(coreAngle.must_have_positioning)}</div>
      <div class="field"><b>Objections handled:</b> ${esc((a.objections_handled || []).join(", "))}</div>
      <div class="field"><b>What video shows:</b> ${esc(visualScript.what_video_shows)}</div>
      <div class="field"><b>What script says:</b> ${esc(visualScript.what_transcript_says)}</div>
      <div class="field"><b>Pacing notes:</b> ${esc(visualScript.pacing_notes)}</div>
      <div class="field"><b>Psychological triggers:</b> ${esc((a.psychological_triggers || []).join(", "))}</div>
    </div>`;
  }).join("");
  return `<div class="section-title"><span class="n">2</span> Winner breakdown</div>${cards}`;
}

function insightsBlock(ins) {
  if (!ins || !ins.winning_patterns) return "";
  const wp = ins.winning_patterns || {};
  const ai = ins.audience_insights || {};
  const why = ins.why_it_works
    ? `<div class="why"><b>Why it works:</b> ${esc(ins.why_it_works)}</div>` : "";
  return `
    <div class="section-title"><span class="n">3</span> What's working &amp; why</div>
    <div class="cards">
      <div class="card"><h4>Winning patterns</h4>
        <b>Hooks</b>${list(wp.common_hooks)}
        <b>Angles</b>${list(wp.common_angles)}
        <b>Formats</b>${list(wp.common_formats)}
        <b>Triggers</b>${list(wp.common_triggers)}
      </div>
      <div class="card"><h4>Audience insights</h4>
        <b>Status drivers</b>${list(ai.status_drivers)}
        <b>Prestige desires</b>${list(ai.prestige_desires)}
        <b>Key objections</b>${list(ai.key_objections)}
      </div>
    </div>${why}`;
}

function conceptsBlock(ins) {
  const concepts = (ins && ins.new_ad_concepts) || [];
  if (!concepts.length) return "";
  const cards = concepts.map((c, i) => `
    <div class="concept">
      <div class="name"><span class="badge">CONCEPT ${i + 1}</span>${esc(c.concept_name)}</div>
      <div class="field"><b>Hook:</b> ${esc(c.hook)}</div>
      <div class="field"><b>Angle:</b> ${esc(c.angle)} &middot; <b>Format:</b> ${esc(c.format)}</div>
      <div class="field"><b>Script outline:</b> ${esc(c.script_outline)}</div>
      <div class="field"><b>Why it should work:</b> ${esc(c.why_it_should_work)}</div>
      <div class="field"><b>What to test:</b> ${esc(c.what_to_test)}</div>
    </div>`).join("");
  return `<div class="section-title"><span class="n">4</span> New creative concepts to test</div>${cards}`;
}

function downloads(id) {
  return `<div class="downloads">
    <a class="primary" href="/api/download/${id}/excel">Download Excel report</a>
    <a href="/api/download/${id}/report">Download written report</a>
  </div>`;
}

function render(data) {
  results.innerHTML =
    statusBar("ok", data.status) +
    `<div class="section-title"><span class="n">1</span> Performance</div>` +
    performanceTable(data.performance, data.metric) +
    winnerBreakdownBlock(data.performance, data.analyses) +
    insightsBlock(data.insights) +
    conceptsBlock(data.insights) +
    downloads(data.report_id);
}

runBtn.addEventListener("click", async () => {
  const apiKey = $("apiKey").value.trim();
  if (!apiKey) { results.innerHTML = statusBar("err", "Enter your API key first."); return; }
  if (!fileInput.files.length) { results.innerHTML = statusBar("err", "Choose a CSV or JSON file first."); return; }

  const form = new FormData();
  form.append("file", fileInput.files[0]);
  form.append("api_key", apiKey);
  form.append("metric", $("metric").value);
  form.append("top_n", $("topN").value);
  form.append("min_spend", $("minSpend").value);
  form.append("audience", $("audience").value.trim());

  runBtn.disabled = true;
  results.innerHTML = statusBar("info", "Analyzing… computing metrics, reading creatives, and building strategy.") +
    `<div class="spinner"></div>`;

  try {
    const res = await fetch("/api/analyze", { method: "POST", body: form });
    const data = await res.json();
    if (!res.ok) { results.innerHTML = statusBar("err", data.detail || "Analysis failed."); return; }
    render(data);
  } catch (e) {
    results.innerHTML = statusBar("err", "Request failed: " + e.message);
  } finally {
    runBtn.disabled = false;
  }
});
