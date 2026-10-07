/* ==========================================================================
   HealthMate - logjika e faqes (frontend)
   JavaScript i thjeshtë, pa librari. Flet me backend-in përmes /api/...
   ========================================================================== */
"use strict";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

const state = { profile: null, catalog: [], labs: [], therapies: [], symptoms: [], pendingQuestion: null };

/* ---------- Komunikimi me backend-in ---------- */
async function api(path, { method = "GET", body } = {}) {
  const res = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    let msg = "";
    try { const d = await res.json(); msg = typeof d.detail === "string" ? d.detail : ""; } catch { /* pa detaje */ }
    throw new Error(msg || `Gabim ${res.status}`);
  }
  return res.json();
}

/* ---------- Ndihmës për formatim ---------- */
const MONTHS = ["janar", "shkurt", "mars", "prill", "maj", "qershor", "korrik", "gusht", "shtator", "tetor", "nëntor", "dhjetor"];
const DAYS = ["e diel", "e hënë", "e martë", "e mërkurë", "e enjte", "e premte", "e shtunë"];
const SLOTS = { morning: "Mëngjes", noon: "Mesditë", evening: "Mbrëmje", night: "Para gjumit" };
const SLOT_ICONS = { morning: "sunrise", noon: "sun", evening: "sunset", night: "moon" };
const STATUS = {
  normal: { label: "Në rregull", icon: "check" },
  high: { label: "E lartë", icon: "up" },
  low: { label: "E ulët", icon: "down" },
  unknown: { label: "Pa kufij", icon: null },
};

const todayISO = () => {
  const d = new Date();
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
};
const toDate = (iso) => new Date(String(iso).slice(0, 10) + "T00:00:00");
const fmtDate = (iso) => { if (!iso) return ""; const d = toDate(iso); return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`; };
const fmtShort = (iso) => { const d = toDate(iso); return `${d.getDate()} ${MONTHS[d.getMonth()].slice(0, 3)}`; };
const fmtNum = (v) => Number(v).toLocaleString("sq-AL", { maximumFractionDigits: 2 });
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const icon = (name) => `<svg class="icon" aria-hidden="true"><use href="#i-${name}"/></svg>`;

function badge(status) {
  const s = STATUS[status] || STATUS.unknown;
  return `<span class="badge badge-${status}">${s.icon ? icon(s.icon) : ""}${s.label}</span>`;
}

function rangeText(low, high, unit) {
  const u = unit ? ` ${unit}` : "";
  if (low != null && high != null) return `Normale: ${fmtNum(low)} – ${fmtNum(high)}${u}`;
  if (high != null) return `Normale: nën ${fmtNum(high)}${u}`;
  if (low != null) return `Normale: mbi ${fmtNum(low)}${u}`;
  return "";
}

function toast(msg) {
  const t = $("#toast");
  t.textContent = msg;
  t.classList.add("show");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => t.classList.remove("show"), 2800);
}

/* Shndërron tekstin e asistentit (markdown i thjeshtë) në HTML të sigurt */
function renderText(text) {
  const inline = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>").replace(/(^|\s)\*(\S.+?)\*(?=\s|$)/g, "$1<em>$2</em>");
  const out = [];
  let list = null, table = null;
  const flushTable = () => {
    if (!table) return;
    const [head, ...body] = table;
    out.push(`<div class="review-scroll"><table class="simple"><thead><tr>${head.map((c) => `<th>${inline(c)}</th>`).join("")}</tr></thead>
      <tbody>${body.map((r) => `<tr>${r.map((c) => `<td>${inline(c)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`);
    table = null;
  };
  for (const raw of String(text).split("\n")) {
    const line = raw.trim();
    // Tabelë markdown: | a | b |
    if (/^\|.*\|$/.test(line)) {
      if (list) { out.push(`</${list.type}>`); list = null; }
      if (/^\|[\s:|-]+\|$/.test(line)) continue;   // rreshti ndarës |---|---|
      (table = table || []).push(line.slice(1, -1).split("|").map((c) => c.trim()));
      continue;
    }
    flushTable();
    const ul = line.match(/^[-*•]\s+(.*)/);
    const ol = line.match(/^\d+[.)]\s+(.*)/);
    if (ul || ol) {
      const type = ul ? "ul" : "ol";
      if (!list || list.type !== type) { if (list) out.push(`</${list.type}>`); list = { type }; out.push(`<${type}>`); }
      out.push(`<li>${inline((ul || ol)[1])}</li>`);
      continue;
    }
    if (list) { out.push(`</${list.type}>`); list = null; }
    if (!line) continue;
    const h = line.match(/^#{1,4}\s+(.*)/);
    out.push(h ? `<h3>${inline(h[1])}</h3>` : `<p>${inline(line)}</p>`);
  }
  flushTable();
  if (list) out.push(`</${list.type}>`);
  return out.join("");
}

/* ---------- Madhësia e shkrimit ---------- */
function initTextSize() {
  let size = "m";
  try { size = localStorage.getItem("hm-size") || "m"; } catch (e) { /* pa ruajtje */ }
  const apply = (s) => {
    document.documentElement.dataset.size = s;
    $$(".textsize button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.size === s)));
    try { localStorage.setItem("hm-size", s); } catch (e) { /* pa ruajtje */ }
  };
  $$(".textsize button").forEach((b) => b.addEventListener("click", () => apply(b.dataset.size)));
  const order = ["m", "l", "xl"];
  $("#btn-size-cycle").addEventListener("click", () => {
    const next = order[(order.indexOf(document.documentElement.dataset.size) + 1) % order.length];
    apply(next);
    toast({ m: "Shkrim normal", l: "Shkrim i madh", xl: "Shkrim shumë i madh" }[next]);
  });
  apply(size);
}

/* Inicialet e emrit në rrethin e profilit (lart djathtas) */
function initials(name) {
  return (name || "").trim().split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0].toUpperCase()).join("");
}
function setAvatar(profile) {
  const ini = initials(profile?.name);
  $("#header-avatar").innerHTML = ini ? esc(ini) : icon("user");
}

/* ---------- Navigimi ndërmjet faqeve ---------- */
const PAGES = {
  kreu: loadHome, analizat: loadLabs, terapia: loadTherapies, simptomat: loadSymptoms,
  asistenti: loadChat, bota: loadWho, profili: loadProfile,
};

function route() {
  const page = (location.hash.slice(1) || "kreu").split("?")[0];
  const name = PAGES[page] ? page : "kreu";
  $$(".page").forEach((p) => (p.hidden = p.id !== `page-${name}`));
  $$("[data-page]").forEach((a) => {
    a.classList.toggle("active", a.dataset.page === name);
    if (a.dataset.page === name) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
  });
  window.scrollTo(0, 0);
  PAGES[name]().catch((e) => { console.error(e); toast("Diçka nuk shkoi mirë. Provoni përsëri."); });
}

function initToggles() {
  document.addEventListener("click", (e) => {
    const t = e.target.closest("[data-toggle]");
    if (t) {
      const target = document.getElementById(t.dataset.toggle);
      target.hidden = !target.hidden;
      if (!target.hidden) { const f = target.querySelector("input, select, textarea"); if (f) f.focus(); }
    }
    const open = e.target.closest("[data-open]");
    if (open) state.openOnLoad = open.dataset.open;
  });
}

function openPending() {
  if (!state.openOnLoad) return;
  const el = document.getElementById(state.openOnLoad);
  state.openOnLoad = null;
  if (el) { el.hidden = false; const f = el.querySelector("input, select, textarea"); if (f) f.focus(); }
}

/* Hap bisedën dhe i dërgon asistentit një pyetje të gatshme */
function askAssistant(question) {
  state.pendingQuestion = question;
  if (location.hash === "#asistenti") loadChat();
  else location.hash = "#asistenti";
}

/* ==========================================================================
   KREU
   ========================================================================== */
async function loadHome() {
  const [profile, doses, labs, symptoms] = await Promise.all([
    api("/api/profile"), api("/api/therapies/today"), api("/api/labs"), api("/api/symptoms"),
  ]);
  state.profile = profile;
  setAvatar(profile);

  const now = new Date();
  const hour = now.getHours();
  const hello = hour < 12 ? "Mirëmëngjes" : hour < 18 ? "Mirëdita" : "Mirëmbrëma";
  const first = (profile.name || "").trim().split(/\s+/)[0];
  $("#greeting").textContent = first ? `${hello}, ${first}` : hello;
  $("#today-date").textContent = `Sot është ${DAYS[now.getDay()]}, ${fmtDate(todayISO())}`;

  // Analizat: vlera e fundit e çdo analize që nuk është në rregull
  const latest = latestPerTest(labs);
  const flagged = latest.filter((l) => l.status === "high" || l.status === "low");

  // Një fjali e shkurtër për ditën
  const left = doses.filter((d) => !d.taken).length;
  const parts = [];
  if (doses.length) parts.push(left ? `Ju mbeten ${left} doza barnash për sot.` : "I keni marrë të gjitha barnat e sotme.");
  if (flagged.length) parts.push(`${flagged.length} ${flagged.length === 1 ? "analizë kërkon" : "analiza kërkojnë"} vëmendje.`);
  $("#hero-sub").textContent = parts.join(" ") || "Gjithë shëndeti juaj, në një vend.";

  renderPatientCard(profile);
  renderDoses(doses);

  $("#home-labs").innerHTML = !labs.length
    ? `<p class="empty">Nuk keni shtuar ende analiza.</p>
       <p style="margin:.75rem 0 0"><a class="btn btn-soft btn-small" href="#analizat" data-open="lab-photo">${icon("camera")}Dërgo foton e parë</a></p>`
    : !flagged.length
      ? `<p style="margin:0">${badge("normal")}</p><p style="margin:.6rem 0 0">Të gjitha analizat tuaja të fundit janë brenda normës.</p>`
      : `<ul class="list">${flagged.slice(0, 4).map((l) => `
          <li><div class="li-main"><div class="title">${esc(l.test_name)}</div>
            <div class="sub">${fmtNum(l.value)} ${esc(l.unit)} · ${fmtDate(l.taken_on)}</div></div>
            ${badge(l.status)}</li>`).join("")}</ul>
          <p style="margin:.9rem 0 0"><a class="link" href="#analizat">${flagged.length > 4
            ? `Shiko edhe ${flagged.length - 4} të tjera` : "Shiko të gjitha analizat"}</a></p>`;

  $("#home-symptoms").innerHTML = symptoms.length
    ? `<ul class="list">${symptoms.slice(0, 3).map(symptomRow).join("")}</ul>`
    : `<p class="empty">Nuk keni shënuar simptoma. Kjo është shenjë e mirë.</p>`;
}

/* Kartela e pacientit: emri, mosha, alergjitë, sëmundjet, mjeku */
function renderPatientCard(p) {
  const box = $("#home-card");
  const head = `<div class="patient-label">${icon("shield")}Kartela ime</div>`;
  if (!p.name) {
    box.innerHTML = `${head}<div class="patient-top"><span class="avatar">${icon("user")}</span>
      <div><div class="patient-name">Mirë se vini</div><div class="patient-meta">Plotësoni kartelën tuaj</div></div></div>
      <div class="patient-empty"><p>Shkruani emrin, alergjitë dhe mjekun tuaj. Kështu këshillat do të jenë më të sakta për ju.</p>
      <a class="btn btn-primary" href="#profili">Plotëso kartelën</a></div>`;
    return;
  }
  const age = p.birth_year ? `${new Date().getFullYear() - p.birth_year} vjeç` : "";
  const sex = p.sex === "F" ? "Femër" : p.sex === "M" ? "Mashkull" : "";
  const allergies = (p.allergies || "").split(/[,;]/).map((a) => a.trim()).filter(Boolean);
  const tel = (n) => String(n).replace(/[^\d+]/g, "");
  const none = `<span class="muted">Nuk ka të shënuara</span>`;
  const contact = (label, name, phone) => (name || phone) ? `<div><dt>${label}</dt><dd class="patient-call"><span>${esc(name)}</span>
        ${phone ? `<a class="call-btn" href="tel:${esc(tel(phone))}">${icon("phone")}Telefono</a>` : ""}</dd></div>` : "";
  box.innerHTML = `${head}
    <div class="patient-top"><span class="avatar">${esc(initials(p.name))}</span>
      <div><div class="patient-name">${esc(p.name)}</div><div class="patient-meta">${[age, sex].filter(Boolean).join(" · ")}</div></div></div>
    <dl>
      <div><dt>Alergji</dt><dd>${allergies.length
        ? allergies.map((a) => `<span class="allergy">${icon("alert")}${esc(a)}</span>`).join("") : none}</dd></div>
      <div><dt>Sëmundje kronike</dt><dd>${esc(p.conditions) || none}</dd></div>
      ${contact("Mjeku im", p.doctor_name, p.doctor_phone)}
      ${contact("Në rast urgjence", p.emergency_name, p.emergency_phone)}
    </dl>`;
}

function renderDoses(doses) {
  const box = $("#home-doses");
  const progress = () => {
    const done = $$(".dose[aria-pressed=true]", box).length, all = $$(".dose", box).length;
    $("#dose-progress").textContent = all ? `${done} nga ${all} të marra` : "";
    const bar = $(".progress > span", box);
    if (bar) bar.style.width = all ? `${(done / all) * 100}%` : "0";
  };
  if (!doses.length) {
    box.innerHTML = `<p class="empty">Nuk ka barna të planifikuara për sot.</p>
      <p style="margin:.75rem 0 0"><a class="btn btn-soft btn-small" href="#terapia" data-open="therapy-form">${icon("plus")}Shto një bar</a></p>`;
    progress();
    return;
  }
  let html = `<div class="progress" aria-hidden="true"><span></span></div>`, lastSlot = null;
  for (const d of doses) {
    if (d.slot !== lastSlot) { html += `<div class="dose-slot">${icon(SLOT_ICONS[d.slot])}${SLOTS[d.slot]}</div>`; lastSlot = d.slot; }
    html += `<button class="dose" aria-pressed="${d.taken}" data-tid="${d.therapy_id}" data-slot="${d.slot}">
      <span class="box">${icon("check")}</span>
      <span><span class="dose-name"><strong>${esc(d.medication)}</strong></span> ${d.dose ? `<span class="muted">${esc(d.dose)}</span>` : ""}</span>
      <span class="dose-state">${d.taken ? "E mora" : ""}</span></button>`;
  }
  box.innerHTML = html;
  progress();
  $$(".dose", box).forEach((b) => b.addEventListener("click", async () => {
    const taken = b.getAttribute("aria-pressed") !== "true";
    b.setAttribute("aria-pressed", String(taken));
    $(".dose-state", b).textContent = taken ? "E mora" : "";
    progress();
    await api(`/api/therapies/${b.dataset.tid}/dose`, { method: "POST", body: { slot: b.dataset.slot, taken } });
  }));
}

function latestPerTest(labs) {
  const seen = new Set(), out = [];
  for (const l of labs) {
    const k = l.test_key === "custom" ? "c:" + l.test_name.toLowerCase() : l.test_key;
    if (!seen.has(k)) { seen.add(k); out.push(l); }
  }
  return out;
}

/* ==========================================================================
   ANALIZAT
   ========================================================================== */
let labsInit = false;

async function loadLabs() {
  if (!labsInit) initLabForms();
  labsInit = true;
  const [catalog, labs, profile, reports] = await Promise.all([
    state.catalog.length ? state.catalog : api("/api/labs/catalog"), api("/api/labs"), api("/api/profile"),
    api("/api/labs/reports"),
  ]);
  state.catalog = catalog; state.labs = labs; state.profile = profile; state.reports = reports;
  fillLabSelect();
  renderLabs();
  renderReports();
  openPending();
}

/* ---------- Foto e fletës së analizave ---------- */
const photo = { dataUrl: null, items: [] };

function photoStep(step) {
  ["pick", "preview", "busy", "review"].forEach((s) => ($(`#photo-step-${s}`).hidden = s !== step));
}

function photoBusy(text) {
  $("#photo-busy-text").textContent = text;
  photoStep("busy");
}

function resetPhoto() {
  photo.dataUrl = null; photo.items = [];
  $("#photo-input").value = "";
  $("#photo-camera").value = "";
  $("#photo-step-review").innerHTML = "";
  photoStep("pick");
}

/* Zvogëlon foton para dërgimit (më shpejt, më pak internet) dhe e kthen në JPG */
async function shrinkImage(file, max = 2000) {
  const bmp = await createImageBitmap(file);
  const scale = Math.min(1, max / Math.max(bmp.width, bmp.height));
  const canvas = document.createElement("canvas");
  canvas.width = Math.round(bmp.width * scale);
  canvas.height = Math.round(bmp.height * scale);
  canvas.getContext("2d").drawImage(bmp, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL("image/jpeg", 0.88);
}

async function pickPhoto(file) {
  if (!file) return;
  if (!file.type.startsWith("image/")) { toast("Ju lutem zgjidhni një foto."); return; }
  try {
    photo.dataUrl = await shrinkImage(file);
  } catch {
    toast("Kjo foto nuk mund të hapet. Provoni një foto JPG ose PNG.");
    return;
  }
  $("#photo-preview").src = photo.dataUrl;
  photoStep("preview");
}

function evalStatus(v, low, high) {
  if (low == null && high == null) return "unknown";
  if (high != null && v > high) return "high";
  if (low != null && v < low) return "low";
  return "normal";
}

async function readPhoto() {
  photoBusy("Po lexoj fletën e analizave. Kjo zgjat disa sekonda...");
  try {
    const data = await api("/api/labs/photo/read", { method: "POST", body: { image: photo.dataUrl } });
    renderReview(data);
  } catch (e) {
    photoStep("preview");
    toast(e.message || "Fotoja nuk u lexua dot.");
  }
}

function renderReview(data) {
  photo.items = data.items;
  const box = $("#photo-step-review");
  if (!data.items.length) {
    box.innerHTML = `<p class="note">Nuk gjeta vlera analizash në këtë foto. Sigurohuni që fleta të shihet e plotë dhe e qartë, pastaj provoni përsëri.</p>
      <div class="form-actions"><button class="btn btn-primary" data-photo="again">Provo një foto tjetër</button></div>`;
    photoStep("review");
    return;
  }
  box.innerHTML = `
    <p class="note" style="display:block">Gjeta <strong>${data.items.length} vlera</strong>. Ju lutem kontrolloni që numrat të jenë njësoj si në fletë.
      Nëse ndonjë është gabim, ndryshojeni. Hiqni shenjën te ato që nuk doni t'i ruani.</p>
    <div class="review-meta">
      <div class="field"><label for="photo-date">Data e analizave</label><input type="date" id="photo-date" value="${data.date || todayISO()}"></div>
      <p class="muted" style="margin:0 0 .6rem">${data.date ? "Data u lexua nga fleta." : "Data nuk u gjet në fletë. Ju lutem kontrollojeni."}</p>
    </div>
    <div class="review-list">${data.items.map((it, i) => `
      <div class="review-row" data-i="${i}">
        <label class="r-check"><input type="checkbox" checked data-keep aria-label="Ruaj ${esc(it.test_name)}"></label>
        <div class="r-name">${esc(it.test_name)}
          ${it.note ? `<small>${esc(it.note)}</small>` : ""}
          ${it.test_key === "custom" ? `<small>Ruhet me kufijtë e fletës</small>` : ""}</div>
        <div class="r-status" data-status>${badge(it.status)}</div>
        <div class="r-value">
          <input type="number" step="any" inputmode="decimal" value="${it.value}" data-val aria-label="Vlera e ${esc(it.test_name)}">
          <span class="unit">${esc(it.unit)}</span>
          <span class="range">${rangeText(it.range_low, it.range_high, "") || "Pa kufij normalë"}</span>
        </div>
      </div>`).join("")}</div>
    <div class="form-actions" style="margin-top:1.25rem">
      <button class="btn btn-primary" data-photo="save"><svg class="icon"><use href="#i-doc"/></svg>Ruaj dhe bëj raportin</button>
      <button class="btn btn-ghost" data-photo="again">Fillo nga e para</button>
    </div>`;
  photoStep("review");
}

async function savePhoto() {
  const date = $("#photo-date").value || todayISO();
  const items = $$("#photo-step-review .review-row")
    .filter((tr) => $("[data-keep]", tr).checked && $("[data-val]", tr).value !== "")
    .map((tr) => {
      const it = photo.items[Number(tr.dataset.i)];
      return { test_key: it.test_key, test_name: it.test_name, value: Number($("[data-val]", tr).value),
               unit: it.unit, ref_low: it.ref_low, ref_high: it.ref_high, note: it.note, taken_on: date };
    });
  if (!items.length) { toast("Zgjidhni të paktën një vlerë për ta ruajtur."); return; }

  photoBusy(`Po ruaj ${items.length} analiza dhe po përgatis raportin...`);
  try {
    const report = await api("/api/labs/photo/save", { method: "POST", body: { image: photo.dataUrl, taken_on: date, items } });
    resetPhoto();
    $("#lab-photo").hidden = true;
    toast(report.skipped
      ? `U ruajtën ${report.saved} analiza. ${report.skipped} ishin ruajtur më parë dhe nuk u dyfishuan.`
      : `U ruajtën ${report.saved} analiza`);
    await loadLabs();
    showReport(report);
  } catch (e) {
    photoStep("review");
    toast(e.message || "Nuk u ruajt. Provoni përsëri.");
  }
}

function initPhoto() {
  const input = $("#photo-input"), camera = $("#photo-camera"), zone = $(".dropzone");
  input.addEventListener("change", () => pickPhoto(input.files[0]));
  camera.addEventListener("change", () => pickPhoto(camera.files[0]));
  zone.addEventListener("dragover", (e) => { e.preventDefault(); zone.classList.add("drag"); });
  zone.addEventListener("dragleave", () => zone.classList.remove("drag"));
  zone.addEventListener("drop", (e) => { e.preventDefault(); zone.classList.remove("drag"); pickPhoto(e.dataTransfer.files[0]); });
  $("#btn-change-photo").addEventListener("click", resetPhoto);
  $("#btn-read-photo").addEventListener("click", readPhoto);

  const review = $("#photo-step-review");
  review.addEventListener("click", (e) => {
    const b = e.target.closest("[data-photo]");
    if (b?.dataset.photo === "save") savePhoto();
    if (b?.dataset.photo === "again") resetPhoto();
  });
  review.addEventListener("input", (e) => {
    const tr = e.target.closest(".review-row");
    if (!tr) return;
    const it = photo.items[Number(tr.dataset.i)];
    if (e.target.matches("[data-val]")) {
      const v = Number(e.target.value);
      $("[data-status]", tr).innerHTML = e.target.value === "" ? "" : badge(evalStatus(v, it.range_low, it.range_high));
    }
    if (e.target.matches("[data-keep]")) tr.classList.toggle("off", !e.target.checked);
  });
}

/* ---------- Raportet ---------- */
function showReport(r) {
  const box = $("#lab-report-view");
  box.hidden = false;
  box.innerHTML = `
    <div class="report-head">
      <h2>Raporti i analizave – ${fmtDate(r.taken_on)}</h2>
      <div class="report-actions">
        <button class="btn btn-small" data-print-report="${r.id}"><svg class="icon"><use href="#i-print"/></svg>Printo</button>
        <button class="btn btn-ghost btn-small" data-close-report>Mbyll</button>
      </div>
    </div>
    ${renderText(r.content)}
    <p class="muted small" style="margin-top:1rem">Ky raport u ruajt te "Raportet e mia", bashkë me foton e fletës.</p>`;
  box.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderReports() {
  const box = $("#report-list");
  const reports = state.reports || [];
  if (!reports.length) {
    box.innerHTML = `<p class="empty">Kur dërgoni foton e një flete analizash, raporti ruhet këtu.</p>`;
    return;
  }
  box.innerHTML = reports.map((r) => `
    <details class="card report-item">
      <summary>
        <span class="report-doc">${icon("doc")}</span>
        <div><div class="title">Analizat e ${fmtDate(r.taken_on)}</div>
          <div class="muted small">${r.item_count} vlera${r.image_file ? " · me foto të fletës" : ""}</div></div>
        <span class="chev"><span class="chev-open">Hape</span><span class="chev-close">Mbylle</span></span>
      </summary>
      <div class="report-body report">
        ${renderText(r.content)}
        ${r.image_file ? `<p><a href="/api/labs/reports/${r.id}/image" target="_blank" rel="noopener">
          <img class="report-thumb" loading="lazy" src="/api/labs/reports/${r.id}/image" alt="Fotoja e fletës"></a></p>` : ""}
        <div class="report-actions">
          <button class="btn btn-small" data-print-report="${r.id}"><svg class="icon"><use href="#i-print"/></svg>Printo</button>
          <button class="btn btn-ghost btn-small btn-danger-text" data-del-report="${r.id}"><svg class="icon"><use href="#i-trash"/></svg>Fshi raportin</button>
        </div>
      </div>
    </details>`).join("");
}

function printReport(id) {
  const r = (state.reports || []).find((x) => x.id === id);
  if (!r) return;
  const p = state.profile || {};
  const labs = state.labs.filter((l) => l.taken_on === r.taken_on);
  const flag = { high: "↑ e lartë", low: "↓ e ulët", normal: "normale", unknown: "" };
  $("#print-view").innerHTML = `
    <h1>Raporti i analizave${p.name ? ` – ${esc(p.name)}` : ""}</h1>
    <p>Data e analizave: ${fmtDate(r.taken_on)}</p>
    ${labs.length ? `<h2>Vlerat</h2><table><tr><th>Analiza</th><th>Vlera</th><th>Normale</th><th>Gjendja</th></tr>
      ${labs.map((l) => `<tr><td>${esc(l.test_name)}</td><td>${fmtNum(l.value)} ${esc(l.unit)}</td>
        <td>${rangeText(l.ref_low, l.ref_high, "").replace("Normale: ", "")}</td>
        <td class="${l.status === "normal" ? "" : "flag"}">${flag[l.status]}</td></tr>`).join("")}</table>` : ""}
    <h2>Shpjegimi</h2>${renderText(r.content)}
    <p style="margin-top:20pt;font-size:10pt">Përgatitur me HealthMate. Ky raport nuk e zëvendëson mendimin e mjekut.</p>`;
  window.print();
}

function initReports() {
  $("#page-analizat").addEventListener("click", async (e) => {
    const pr = e.target.closest("[data-print-report]");
    if (pr) printReport(Number(pr.dataset.printReport));
    if (e.target.closest("[data-close-report]")) $("#lab-report-view").hidden = true;
    const del = e.target.closest("[data-del-report]");
    if (del && confirm("Ta fshij këtë raport dhe foton? Vlerat e analizave mbeten në historik.")) {
      await api(`/api/labs/reports/${del.dataset.delReport}`, { method: "DELETE" });
      toast("Raporti u fshi");
      loadLabs();
    }
  });
}

function fillLabSelect() {
  const sel = $("#lab-test");
  if (sel.options.length) return;
  sel.innerHTML = `<option value="">Zgjidhni analizën...</option>` +
    state.catalog.map((c) => `<option value="${c.key}">${esc(c.name)}</option>`).join("") +
    `<option value="custom">Tjetër (e shkruaj vetë)</option>`;
}

function initLabForms() {
  initPhoto();
  initReports();
  $("#lab-date").value = todayISO();
  $("#paste-date").value = todayISO();

  $("#lab-test").addEventListener("change", (e) => {
    const c = state.catalog.find((x) => x.key === e.target.value);
    $("#lab-custom-name-wrap").hidden = e.target.value !== "custom";
    $("#lab-unit").value = c ? c.unit : "";
    let low = c?.low, high = c?.high;
    const sex = state.profile?.sex;
    if (c && sex && c[sex]) [low, high] = c[sex];
    $("#lab-range-hint").textContent = c ? `${c.what} ${rangeText(low, high, c.unit)}.` : "";
  });

  $("#lab-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const key = $("#lab-test").value;
    const num = (id) => ($(id).value === "" ? null : Number($(id).value));
    const lab = await api("/api/labs", { method: "POST", body: {
      test_key: key, test_name: key === "custom" ? $("#lab-custom-name").value.trim() : "",
      value: Number($("#lab-value").value), unit: $("#lab-unit").value.trim(),
      taken_on: $("#lab-date").value, ref_low: num("#lab-low"), ref_high: num("#lab-high"),
    } });
    $("#lab-value").value = ""; $("#lab-low").value = ""; $("#lab-high").value = "";
    $("#lab-form").hidden = true;
    toast(`U ruajt: ${lab.test_name} – ${STATUS[lab.status].label.toLowerCase()}`);
    loadLabs();
  });

  $("#btn-parse").addEventListener("click", async () => {
    const text = $("#paste-text").value.trim();
    if (!text) return;
    const found = await api("/api/labs/parse", { method: "POST", body: { text } });
    const box = $("#paste-preview");
    if (!found.length) {
      box.innerHTML = `<p class="note" style="margin-top:1rem">Nuk gjeta analiza të njohura në këtë tekst. Mund t'i shtoni një nga një me butonin "Shto një analizë".</p>`;
      return;
    }
    box.innerHTML = `<h3 style="margin-top:1.25rem">Gjeta ${found.length} vlera. Kontrollojini para se t'i ruani:</h3>
      <table class="simple"><thead><tr><th>Ruaj</th><th>Analiza</th><th>Vlera</th><th>Gjendja</th></tr></thead><tbody>
      ${found.map((f, i) => `<tr>
        <td><input type="checkbox" checked data-i="${i}" aria-label="Ruaj ${esc(f.test_name)}" style="width:1.4rem;min-height:1.4rem"></td>
        <td>${esc(f.test_name)}${f.note ? `<div class="muted small">${esc(f.note)}</div>` : ""}</td>
        <td class="num">${fmtNum(f.value)} ${esc(f.unit)}</td><td>${badge(f.status)}</td></tr>`).join("")}
      </tbody></table>
      <div class="form-actions" style="margin-top:1rem"><button class="btn btn-primary" id="btn-save-parsed">Ruaj të zgjedhurat</button></div>`;
    $("#btn-save-parsed").addEventListener("click", async () => {
      const date = $("#paste-date").value || todayISO();
      const chosen = $$("input[data-i]:checked", box).map((c) => found[Number(c.dataset.i)]);
      await api("/api/labs/bulk", { method: "POST", body: chosen.map((f) => ({
        test_key: f.test_key, test_name: f.test_name, value: f.value, unit: f.unit, taken_on: date, note: f.note,
      })) });
      box.innerHTML = ""; $("#paste-text").value = ""; $("#lab-paste").hidden = true;
      toast(`U ruajtën ${chosen.length} analiza`);
      loadLabs();
    });
  });

  $("#btn-explain-labs").addEventListener("click", async (e) => {
    const btn = e.currentTarget, box = $("#lab-explain");
    if (!state.labs.length) { toast("Shtoni fillimisht disa analiza"); return; }
    btn.disabled = true;
    box.hidden = false;
    box.innerHTML = `<p class="typing">Asistenti po i lexon analizat tuaja. Kjo mund të zgjasë deri në një minutë...</p>`;
    box.scrollIntoView({ behavior: "smooth", block: "nearest" });
    try {
      const r = await api("/api/chat/explain-labs", { method: "POST" });
      box.innerHTML = `<h2>Shpjegimi i analizave</h2>${renderText(r.text)}
        <p class="muted small">Ky shpjegim u ruajt edhe te "Bisedë", ku mund të bëni pyetje të tjera.</p>`;
    } catch {
      box.innerHTML = `<p>Nuk arrita të lidhem me asistentin. Provoni përsëri pas pak.</p>`;
    }
    btn.disabled = false;
  });

  $("#lab-list").addEventListener("click", async (e) => {
    const del = e.target.closest("[data-del-lab]");
    if (del && confirm("Ta fshij këtë rezultat?")) {
      await api(`/api/labs/${del.dataset.delLab}`, { method: "DELETE" });
      toast("Rezultati u fshi");
      loadLabs();
    }
    const ask = e.target.closest("[data-ask-lab]");
    if (ask) askAssistant(ask.dataset.askLab);
  });
}

function renderLabs() {
  const box = $("#lab-list");
  if (!state.labs.length) {
    box.innerHTML = `<div class="card card-quiet"><h2>Ende pa analiza</h2>
      <p style="margin:0">Mënyra më e lehtë: klikoni <strong>"Dërgo foto të fletës së analizave"</strong> dhe fotografoni fletën që ju dha laboratori.</p></div>`;
    return;
  }
  // Grupo sipas analizës (p.sh. të gjitha matjet e glukozës bashkë)
  const groups = new Map();
  for (const l of state.labs) {
    const k = l.test_key === "custom" ? "c:" + l.test_name.toLowerCase() : l.test_key;
    if (!groups.has(k)) groups.set(k, []);
    groups.get(k).push(l);
  }
  // Grafiku vizatohet me gjerësinë reale të ekranit, që shkronjat të mbeten të lexueshme në celular
  const cols = window.matchMedia("(min-width: 900px)").matches ? 2 : 1;
  const chartW = Math.max(280, Math.min(720, ((box.clientWidth || 640) - (cols - 1) * 22) / cols - 44));
  box.innerHTML = [...groups.values()].map((items) => {
    const last = items[0];
    const q = `Analiza ime e fundit: ${last.test_name} = ${fmtNum(last.value)} ${last.unit} (${fmtDate(last.taken_on)}). Çfarë do të thotë kjo për mua?`;
    const range = rangeText(last.ref_low, last.ref_high, last.unit);
    return `<article class="card lab-card" data-status="${last.status}">
      <div class="lab-top">
        <h3 class="lab-name">${esc(last.test_name)}</h3>
        ${badge(last.status)}
      </div>
      <div class="lab-value">${fmtNum(last.value)}<small>${esc(last.unit)}</small></div>
      <p class="lab-meta">${fmtDate(last.taken_on)}${range ? `<br>${range}` : ""}</p>
      ${last.explanation ? `<p class="lab-explain">${esc(last.explanation)}</p>` : ""}
      ${items.length > 1 ? lineChart(items.slice().reverse(), last.ref_low, last.ref_high, last.unit, last.test_name, chartW) : ""}
      <div class="lab-foot">
        <details class="history"><summary>Të gjitha matjet (${items.length})</summary>
        <div class="table-scroll"><table class="simple"><thead><tr><th>Data</th><th>Vlera</th><th>Gjendja</th><th><span class="sr-only">Fshi</span></th></tr></thead><tbody>
        ${items.map((l) => `<tr><td>${fmtDate(l.taken_on)}</td><td class="num">${fmtNum(l.value)} ${esc(l.unit)}</td>
          <td>${badge(l.status)}</td>
          <td style="text-align:right"><button class="icon-btn" data-del-lab="${l.id}" aria-label="Fshi">${icon("trash")}</button></td></tr>`).join("")}
        </tbody></table></div>
        </details>
        <button class="btn btn-soft btn-small" data-ask-lab="${esc(q)}">${icon("chat")}Pyet asistentin</button>
      </div>
    </article>`;
  }).join("");
}

/* Grafik i thjeshtë me vija: si ka ndryshuar vlera me kohë.
   Brezi i gjelbër i lehtë tregon zonën normale. */
function lineChart(points, low, high, unit, name, W = 640) {
  const H = W < 420 ? 170 : 190, L = 46, R = 18, T = 26, B = 28;
  const vals = points.map((p) => p.value);
  let min = Math.min(...vals, low ?? Infinity), max = Math.max(...vals, high ?? -Infinity);
  if (min === max) { min -= 1; max += 1; }
  const pad = (max - min) * 0.12;
  min -= pad; max += pad;
  if (Math.min(...vals) >= 0 && min < 0) min = 0;

  const times = points.map((p) => toDate(p.taken_on).getTime());
  const t0 = Math.min(...times), t1 = Math.max(...times);
  const x = (i) => (t1 === t0 ? L + (W - L - R) * (points.length === 1 ? .5 : i / (points.length - 1))
    : L + ((times[i] - t0) / (t1 - t0)) * (W - L - R));
  const y = (v) => T + (1 - (v - min) / (max - min)) * (H - T - B);

  let band = "";
  if (low != null || high != null) {
    const top = y(high ?? max), bottom = y(low ?? min);
    band = `<rect class="band" x="${L}" y="${top}" width="${W - L - R}" height="${Math.max(0, bottom - top)}" rx="4"/>`;
    if (high != null) band += `<line class="band-edge" x1="${L}" x2="${W - R}" y1="${y(high)}" y2="${y(high)}"/><text class="axis" x="${L - 8}" y="${y(high) + 4}" text-anchor="end">${fmtNum(high)}</text>`;
    if (low != null) band += `<line class="band-edge" x1="${L}" x2="${W - R}" y1="${y(low)}" y2="${y(low)}"/><text class="axis" x="${L - 8}" y="${y(low) + 4}" text-anchor="end">${fmtNum(low)}</text>`;
  }
  const path = points.map((p, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(p.value).toFixed(1)}`).join(" ");
  const colW = (W - L - R) / Math.max(points.length, 1);
  const pts = points.map((p, i) => {
    const tip = `${fmtDate(p.taken_on)}<br><strong>${fmtNum(p.value)} ${esc(unit)}</strong> · ${STATUS[p.status].label}`;
    return `<g class="pt" data-tip="${esc(tip)}">
      <line class="hover-line" x1="${x(i)}" x2="${x(i)}" y1="${T}" y2="${H - B}" visibility="hidden"/>
      <circle class="dot${i === points.length - 1 ? " dot-last" : ""}" cx="${x(i)}" cy="${y(p.value)}" r="5"/>
      <rect class="hit" x="${x(i) - colW / 2}" y="0" width="${colW}" height="${H}"/></g>`;
  }).join("");
  const lastI = points.length - 1;
  const lastLabel = `<text class="val-label" x="${x(lastI)}" y="${y(points[lastI].value) - 12}" text-anchor="${x(lastI) > W - 60 ? "end" : "middle"}">${fmtNum(points[lastI].value)}</text>`;
  const xLabels = `<text class="axis" x="${x(0)}" y="${H - 6}" text-anchor="start">${fmtShort(points[0].taken_on)}</text>
    <text class="axis" x="${x(lastI)}" y="${H - 6}" text-anchor="end">${fmtShort(points[lastI].taken_on)}</text>`;

  return `<svg class="chart" viewBox="0 0 ${W} ${H}" role="img" aria-label="Ecuria e ${esc(name)} me kohë">
    ${band}<path class="line" d="${path}"/>${xLabels}${lastLabel}${pts}</svg>`;
}

function initTooltip() {
  const tip = $("#tooltip");
  document.addEventListener("mouseover", (e) => {
    const g = e.target.closest(".pt");
    $$(".pt .hover-line").forEach((l) => l.setAttribute("visibility", "hidden"));
    if (!g) { tip.hidden = true; return; }
    $(".hover-line", g).setAttribute("visibility", "visible");
    tip.innerHTML = g.dataset.tip;
    tip.hidden = false;
  });
  document.addEventListener("mousemove", (e) => {
    if (tip.hidden) return;
    const w = tip.offsetWidth;
    const left = Math.min(e.clientX + 14, window.innerWidth - w - 8);
    tip.style.left = left + "px";
    tip.style.top = (e.clientY - tip.offsetHeight - 12) + "px";
  });
}

/* ==========================================================================
   TERAPIA
   ========================================================================== */
let therapyInit = false;

async function loadTherapies() {
  if (!therapyInit) initTherapyForm();
  therapyInit = true;
  state.therapies = await api("/api/therapies");
  const active = state.therapies.filter((t) => t.active);
  const past = state.therapies.filter((t) => !t.active);

  $("#therapy-active").innerHTML = active.length ? active.map((t) => `
    <article class="card therapy">
      <span class="therapy-icon">${icon("pill")}</span>
      <div class="therapy-body">
        <h3>${esc(t.medication)} ${t.dose ? `<span class="muted" style="font-weight:400">${esc(t.dose)}</span>` : ""}</h3>
        ${t.times.length ? `<div class="tags">${t.times.map((s) => `<span class="tag">${icon(SLOT_ICONS[s])}${SLOTS[s]}</span>`).join("")}</div>` : ""}
        <p class="muted" style="margin:0">${t.reason ? `Për: ${esc(t.reason)} · ` : ""}Që nga ${fmtDate(t.start_date)}${t.notes ? ` · ${esc(t.notes)}` : ""}</p>
        <div class="therapy-actions">
          <button class="btn btn-soft btn-small" data-ask-th="${t.id}">${icon("chat")}Pyet për këtë bar</button>
          <button class="btn btn-soft btn-small" data-stop-th="${t.id}">${icon("stop")}E përfundova</button>
          <button class="icon-btn" data-del-th="${t.id}" aria-label="Fshi ${esc(t.medication)}">${icon("trash")}</button>
        </div>
      </div>
    </article>`).join("")
    : `<p class="empty card card-quiet">Nuk keni barna aktive të shënuara.</p>`;

  $("#therapy-past").innerHTML = past.length
    ? `<div class="card"><ul class="list">${past.map((t) => `
        <li><div class="li-main"><div class="title">${esc(t.medication)} ${esc(t.dose)}</div>
          <div class="sub">${fmtDate(t.start_date)} – ${fmtDate(t.end_date)}${t.reason ? ` · ${esc(t.reason)}` : ""}</div></div>
          <button class="icon-btn" data-del-th="${t.id}" aria-label="Fshi">${icon("trash")}</button></li>`).join("")}</ul></div>`
    : `<p class="empty">Barnat që i përfundoni ruhen këtu, që ta keni historikun të plotë.</p>`;
  openPending();
}

function initTherapyForm() {
  $("#th-start").value = todayISO();

  $("#therapy-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const med = $("#th-name").value.trim(), dose = $("#th-dose").value.trim();
    await api("/api/therapies", { method: "POST", body: {
      medication: med, dose,
      times: $$("input[name=th-times]:checked").map((c) => c.value),
      reason: $("#th-reason").value.trim(), start_date: $("#th-start").value || todayISO(),
      notes: $("#th-notes").value.trim(),
    } });
    e.target.reset(); $("#th-start").value = todayISO(); e.target.hidden = true;
    toast(`${med} u shtua në terapi`);
    await loadTherapies();
    // Ofro kontrollin e barit të ri me barnat e tjera
    const others = state.therapies.filter((t) => t.active && t.medication !== med);
    const note = document.createElement("div");
    note.className = "note";
    note.innerHTML = `<p>${others.length
      ? `Dëshironi të kontrolloni nëse <strong>${esc(med)}</strong> shkon mirë me barnat e tjera që merrni?`
      : `Dëshironi të dini më shumë për <strong>${esc(med)}</strong>?`}</p>
      <button class="btn btn-primary">Pyet asistentin</button>`;
    $("button", note).addEventListener("click", () => askAssistant(others.length
      ? `Sapo fillova ${med} ${dose}. A ka ndonjë rrezik ose ndërveprim me barnat e tjera që marr dhe me alergjitë e mia? Për çfarë duhet të kem kujdes?`
      : `Sapo fillova ${med} ${dose}. Për çfarë shërben, si duhet ta marr dhe për çfarë efektesh anësore duhet të kem kujdes?`));
    $("#therapy-active").prepend(note);
  });

  $("#page-terapia").addEventListener("click", async (e) => {
    const ask = e.target.closest("[data-ask-th]"), stop = e.target.closest("[data-stop-th]"), del = e.target.closest("[data-del-th]");
    if (ask) {
      const t = state.therapies.find((x) => x.id === Number(ask.dataset.askTh));
      askAssistant(`Më trego për barin tim ${t.medication} ${t.dose}: për çfarë shërben, si ta marr saktë dhe çfarë efektesh anësore mund të ketë.`);
    }
    if (stop && confirm("Ta shënoj këtë bar si të përfunduar? Do të ruhet në historik.")) {
      await api(`/api/therapies/${stop.dataset.stopTh}/stop`, { method: "POST" });
      toast("Terapia u kalua në historik");
      loadTherapies();
    }
    if (del && confirm("Ta fshij plotësisht këtë bar nga lista?")) {
      await api(`/api/therapies/${del.dataset.delTh}`, { method: "DELETE" });
      toast("U fshi");
      loadTherapies();
    }
  });
}

/* ==========================================================================
   SIMPTOMAT
   ========================================================================== */
const COMMON_SYMPTOMS = ["Dhimbje koke", "Marramendje", "Lodhje", "Kollë", "Temperaturë", "Dhimbje barku",
  "Të përziera", "Dhimbje kyçesh", "Pagjumësi", "Mungesë fryme", "Ënjtje këmbësh"];
let symptomsInit = false, severity = 5;

function severityWord(n) {
  return n <= 3 ? "e lehtë" : n <= 6 ? "mesatare" : n <= 8 ? "e fortë" : "shumë e fortë";
}

function symptomRow(s) {
  const cls = s.severity >= 7 ? "sev-high" : s.severity >= 4 ? "sev-mid" : "";
  return `<li><div class="li-main"><div class="title">${esc(s.description)}</div>
    <div class="sub">${fmtDate(s.started_on || s.created_at)}${s.notes ? ` · ${esc(s.notes)}` : ""}</div></div>
    <span class="li-end"><span class="sev-pill ${cls}" title="Rëndësia">${s.severity}/10</span></span></li>`;
}

function setSeverity(n) {
  severity = n;
  $$("#sy-severity button").forEach((b) => b.setAttribute("aria-pressed", String(Number(b.dataset.v) === n)));
  $("#sy-sev-label").textContent = `– ${n} nga 10, ${severityWord(n)}`;
}

function initSymptomForm() {
  $("#sy-date").value = todayISO();
  $("#sy-chips").innerHTML = COMMON_SYMPTOMS.map((s) => `<button type="button" class="chip">${s}</button>`).join("");
  $("#sy-chips").addEventListener("click", (e) => {
    const c = e.target.closest(".chip");
    if (!c) return;
    const ta = $("#sy-desc");
    ta.value = ta.value.trim() ? `${ta.value.trim()}, ${c.textContent.toLowerCase()}` : c.textContent;
    ta.focus();
  });
  $("#sy-severity").innerHTML = Array.from({ length: 10 }, (_, i) =>
    `<button type="button" data-v="${i + 1}" aria-label="${i + 1} nga 10">${i + 1}</button>`).join("");
  $("#sy-severity").addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) setSeverity(Number(b.dataset.v)); });
  setSeverity(5);

  $("#symptom-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const desc = $("#sy-desc").value.trim(), date = $("#sy-date").value || todayISO(), sev = severity;
    await api("/api/symptoms", { method: "POST", body: { description: desc, severity: sev, started_on: date } });
    $("#sy-desc").value = ""; setSeverity(5); $("#sy-date").value = todayISO();
    toast("Simptoma u ruajt");
    const after = $("#symptom-after");
    after.hidden = false;
    after.innerHTML = `<p>U ruajt. Dëshironi ta pyesni asistentin se çfarë mund të jetë dhe çfarë të bëni?</p>
      <button class="btn btn-primary">Pyet asistentin</button>`;
    $("button", after).addEventListener("click", () => {
      after.hidden = true;
      askAssistant(`Kam një simptomë të re që nga ${fmtDate(date)}: ${desc}. Rëndësia ${sev} nga 10. ` +
        "Çfarë mund të jetë, a lidhet me barnat ose analizat e mia, çfarë mund të bëj vetë dhe kur duhet të shkoj te mjeku?");
    });
    loadSymptoms();
  });

  $("#symptom-list").addEventListener("click", async (e) => {
    const del = e.target.closest("[data-del-sy]");
    if (del && confirm("Ta fshij këtë shënim?")) {
      await api(`/api/symptoms/${del.dataset.delSy}`, { method: "DELETE" });
      loadSymptoms();
    }
  });
}

async function loadSymptoms() {
  if (!symptomsInit) initSymptomForm();
  symptomsInit = true;
  state.symptoms = await api("/api/symptoms");
  $("#symptom-list").innerHTML = state.symptoms.length
    ? `<div class="card"><ul class="list">${state.symptoms.map((s) =>
        symptomRow(s).replace("</span></span></li>", `</span><button class="icon-btn" data-del-sy="${s.id}" aria-label="Fshi">${icon("trash")}</button></span></li>`)).join("")}</ul></div>`
    : `<p class="empty">Ende nuk keni shënuar asnjë simptomë.</p>`;
}

/* ==========================================================================
   BISEDA ME ASISTENTIN
   ========================================================================== */
let chatInit = false, sending = false;

function msgHtml(m) {
  const time = m.created_at ? new Date(m.created_at.replace(" ", "T") + "Z") : new Date();
  const hhmm = time.toLocaleTimeString("sq-AL", { hour: "2-digit", minute: "2-digit", hour12: false });
  const who = m.role === "user" ? "Ju"
    : `<span class="mini-mark"><svg viewBox="0 0 24 24"><path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/></svg></span>Asistenti`;
  const body = m.role === "user" ? `<p>${esc(m.content).replace(/\n/g, "<br>")}</p>` : renderText(m.content);
  return `<div class="msg msg-${m.role}"><div class="msg-who">${who}</div>${body}<div class="msg-time">${hhmm}</div></div>`;
}

function chatIntro() {
  const first = (state.profile?.name || "").trim().split(/\s+/)[0];
  return `<div class="chat-empty"><h2>Përshëndetje${first ? ", " + esc(first) : ""}.</h2>
    <p>Mund të më pyesni për çdo gjë që ka të bëjë me shëndetin tuaj: çfarë do të thotë një analizë, si të merrni një bar,
    apo çfarë të bëni me një shqetësim të ri. Unë i shoh analizat, terapinë dhe simptomat që keni shënuar këtu.</p>
    <p style="margin:0">Shkruani poshtë, ose zgjidhni një nga pyetjet e gatshme.</p></div>`;
}

async function loadChat() {
  if (!chatInit) {
    chatInit = true;
    $("#chat-form").addEventListener("submit", (e) => { e.preventDefault(); sendChat($("#chat-input").value); });
    const input = $("#chat-input");
    input.setAttribute("enterkeyhint", "send");
    input.addEventListener("input", () => { input.style.height = "auto"; input.style.height = Math.min(input.scrollHeight, 200) + "px"; });
    $("#chat-input").addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendChat($("#chat-input").value); }
    });
    $("#chat-suggest").addEventListener("click", (e) => { const c = e.target.closest(".chip"); if (c) sendChat(c.textContent); });
    $("#btn-clear-chat").addEventListener("click", async () => {
      if (!confirm("Ta fshij të gjithë bisedën? Të dhënat tuaja shëndetësore nuk fshihen.")) return;
      await api("/api/chat/history", { method: "DELETE" });
      $("#chat-emergency").hidden = true;
      loadChat();
    });
  }
  const [history, profile] = await Promise.all([api("/api/chat/history"), api("/api/profile")]);
  state.profile = profile;
  const log = $("#chat-log");
  log.innerHTML = history.length ? history.map(msgHtml).join("") : chatIntro();
  $("#chat-suggest").hidden = history.length > 0;
  if (history.length) log.lastElementChild.scrollIntoView({ block: "end" });

  if (state.pendingQuestion) {
    const q = state.pendingQuestion;
    state.pendingQuestion = null;
    sendChat(q);
  } else {
    $("#chat-input").focus();
  }
}

async function sendChat(text) {
  text = String(text || "").trim();
  if (!text || sending) return;
  sending = true;
  const log = $("#chat-log"), btn = $("#chat-form button");
  btn.disabled = true;
  $("#chat-input").value = "";
  $("#chat-suggest").hidden = true;
  $(".chat-empty", log)?.remove();

  log.insertAdjacentHTML("beforeend", msgHtml({ role: "user", content: text }));
  $("#chat-input").style.height = "auto";
  log.insertAdjacentHTML("beforeend", msgHtml({ role: "assistant", content: "" })
    .replace('class="msg msg-assistant"', 'class="msg msg-assistant" id="typing"')
    .replace(/<div class="msg-time">.*?<\/div>/, '<p class="typing">Po shkruan përgjigjen...</p>'));
  $("#typing").scrollIntoView({ behavior: "smooth", block: "end" });
  const slow = setTimeout(() => {
    const t = $("#typing .typing");
    if (t) t.textContent = "Po shkruan përgjigjen... Shërbimi është pak i zënë, ju lutem prisni edhe pak.";
  }, 10000);

  try {
    const r = await api("/api/chat", { method: "POST", body: { message: text } });
    $("#typing").outerHTML = msgHtml(r.reply);
    if (r.emergency) $("#chat-emergency").hidden = false;
  } catch {
    $("#typing").outerHTML = msgHtml({ role: "assistant", content: "Nuk arrita ta dërgoj mesazhin. Kontrolloni internetin dhe provoni përsëri." });
  }
  clearTimeout(slow);
  log.lastElementChild.scrollIntoView({ behavior: "smooth", block: "start" });
  btn.disabled = false;
  sending = false;
  $("#chat-input").focus();
}

/* ==========================================================================
   SHËNDETI NË BOTË (OBSH)
   ========================================================================== */
let whoInit = false;

async function loadWho() {
  if (!whoInit) {
    whoInit = true;
    const [countries, profile] = await Promise.all([api("/api/who/countries"), api("/api/profile")]);
    const sel = $("#who-country");
    sel.innerHTML = countries.map((c) => `<option value="${c.code}">${esc(c.name)}</option>`).join("");
    sel.value = profile.country || "ALB";
    sel.addEventListener("change", () => loadWhoIndicators(sel.value));
    loadWhoNews();
  }
  loadWhoIndicators($("#who-country").value);
}

async function loadWhoIndicators(country) {
  const box = $("#who-indicators");
  box.innerHTML = Array.from({ length: 6 }, () => `<div class="stat loading">Po ngarkohet...</div>`).join("");
  try {
    const data = await api(`/api/who/indicators?country=${country}`);
    if ($("#who-country").value !== country) return;
    box.innerHTML = data.indicators.map((i) => {
      const c = i.country, eu = i.europe;
      return `<div class="stat">
        <p class="stat-title">${esc(i.title)}</p>
        ${c ? `<div class="stat-value">${fmtNum(c.value)}<small>${esc(i.unit)}</small></div>
               <p class="stat-compare">${esc(data.country_name)}, ${c.year}${eu ? `<br>Mesatarja në Evropë: <strong>${fmtNum(eu.value)} ${esc(i.unit)}</strong>` : ""}</p>`
            : `<p class="stat-compare muted">Nuk ka të dhëna për këtë shtet.</p>`}
        <p class="stat-info">${esc(i.info)}</p></div>`;
    }).join("");
  } catch {
    box.innerHTML = `<p class="card card-quiet">Të dhënat e OBSH-së nuk u ngarkuan. Kontrolloni lidhjen me internet.</p>`;
  }
}

async function loadWhoNews() {
  const item = (n) => `<li><a href="${esc(n.url)}" target="_blank" rel="noopener">${esc(n.title)}</a><span class="date">${fmtDate(n.date)}</span></li>`;
  try {
    const d = await api("/api/who/news");
    $("#who-news").innerHTML = d.news.map(item).join("") || `<li class="muted">Nuk ka lajme tani.</li>`;
    $("#who-outbreaks").innerHTML = d.outbreaks.map(item).join("") || `<li class="muted">Nuk ka njoftime tani.</li>`;
  } catch {
    $("#who-news").innerHTML = `<li class="muted">Lajmet nuk u ngarkuan.</li>`;
  }
}

/* ==========================================================================
   PROFILI
   ========================================================================== */
const PROFILE_FIELDS = {
  name: "#pf-name", birth_year: "#pf-birth", height_cm: "#pf-height", weight_kg: "#pf-weight", country: "#pf-country",
  allergies: "#pf-allergies", conditions: "#pf-conditions", doctor_name: "#pf-doc", doctor_phone: "#pf-docphone",
  emergency_name: "#pf-em", emergency_phone: "#pf-emphone",
};
let profileInit = false;

async function loadProfile() {
  if (!profileInit) {
    profileInit = true;
    const countries = await api("/api/who/countries");
    $("#pf-country").innerHTML = countries.map((c) => `<option value="${c.code}">${esc(c.name)}</option>`).join("");
    $("#profile-form").addEventListener("submit", async (e) => {
      e.preventDefault();
      const body = {};
      for (const [k, sel] of Object.entries(PROFILE_FIELDS)) {
        const v = $(sel).value.trim();
        body[k] = ["birth_year", "height_cm", "weight_kg"].includes(k) ? (v === "" ? null : Number(v)) : v;
      }
      body.sex = $("input[name=pf-sex]:checked")?.value || "";
      state.profile = await api("/api/profile", { method: "PUT", body });
      setAvatar(state.profile);
      toast("Profili u ruajt");
    });
  }
  const [p, ai] = await Promise.all([api("/api/profile"), api("/api/chat/status")]);
  state.profile = p;
  setAvatar(p);
  for (const [k, sel] of Object.entries(PROFILE_FIELDS)) $(sel).value = p[k] ?? "";
  $$("input[name=pf-sex]").forEach((r) => (r.checked = r.value === p.sex));
  $("#ai-status").textContent = `Asistenti përdor shërbimin ${ai.active} (modeli ${ai.model}). Nëse nuk përgjigjet, provohen me radhë: ${ai.chain.join(", ")}.`;
}

/* ==========================================================================
   PRINTIMI PËR MJEKUN
   ========================================================================== */
async function printSummary() {
  const [p, labs, therapies, symptoms] = await Promise.all([
    api("/api/profile"), api("/api/labs"), api("/api/therapies"), api("/api/symptoms"),
  ]);
  const active = therapies.filter((t) => t.active);
  const latest = latestPerTest(labs);
  const recentSym = symptoms.slice(0, 15);
  const age = p.birth_year ? ` · ${new Date().getFullYear() - p.birth_year} vjeç` : "";
  const flag = { high: "↑ e lartë", low: "↓ e ulët", normal: "normale", unknown: "" };

  $("#print-view").innerHTML = `
    <h1>Përmbledhje shëndetësore${p.name ? ` – ${esc(p.name)}` : ""}</h1>
    <p>Data: ${fmtDate(todayISO())}${age}${p.sex ? ` · ${p.sex === "F" ? "Femër" : "Mashkull"}` : ""}</p>
    <p><strong>Alergji:</strong> ${esc(p.allergies) || "nuk janë shënuar"}<br>
       <strong>Sëmundje kronike:</strong> ${esc(p.conditions) || "nuk janë shënuar"}</p>

    <h2>Terapia aktuale</h2>
    ${active.length ? `<table><tr><th>Bari</th><th>Doza</th><th>Kur</th><th>Për</th><th>Që nga</th></tr>
      ${active.map((t) => `<tr><td>${esc(t.medication)}</td><td>${esc(t.dose)}</td><td>${t.times.map((s) => SLOTS[s]).join(", ")}</td>
      <td>${esc(t.reason)}</td><td>${fmtDate(t.start_date)}</td></tr>`).join("")}</table>` : "<p>Asnjë.</p>"}

    <h2>Analizat e fundit</h2>
    ${latest.length ? `<table><tr><th>Analiza</th><th>Vlera</th><th>Normale</th><th>Gjendja</th><th>Data</th></tr>
      ${latest.map((l) => `<tr><td>${esc(l.test_name)}</td><td>${fmtNum(l.value)} ${esc(l.unit)}</td>
      <td>${rangeText(l.ref_low, l.ref_high, "").replace("Normale: ", "")}</td>
      <td class="${l.status === "normal" ? "" : "flag"}">${flag[l.status]}</td><td>${fmtDate(l.taken_on)}</td></tr>`).join("")}</table>` : "<p>Asnjë.</p>"}

    <h2>Simptomat e shënuara</h2>
    ${recentSym.length ? `<table><tr><th>Data</th><th>Simptoma</th><th>Rëndësia</th></tr>
      ${recentSym.map((s) => `<tr><td>${fmtDate(s.started_on)}</td><td>${esc(s.description)}</td><td>${s.severity}/10</td></tr>`).join("")}</table>` : "<p>Asnjë.</p>"}

    <p style="margin-top:20pt;font-size:10pt">Përgatitur me HealthMate. ${p.doctor_name ? `Mjeku: ${esc(p.doctor_name)}.` : ""}</p>`;
  window.print();
}

/* ---------- Nisja ---------- */
document.addEventListener("DOMContentLoaded", () => {
  initTextSize();
  initToggles();
  initTooltip();
  $("#btn-print").addEventListener("click", printSummary);
  window.addEventListener("hashchange", route);
  route();
  api("/api/profile").then(setAvatar).catch(() => {});
});
