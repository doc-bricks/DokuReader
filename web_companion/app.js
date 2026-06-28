import { parseLibrary, filterDocuments, buildDemoLibrary, setRead, serializeLibrary } from "./library.js";

let library = null;
let activeTopic = null;

const topicList = document.getElementById("topic-list");
const docList = document.getElementById("doc-list");
const searchInput = document.getElementById("search");
const showMissingChk = document.getElementById("show-missing");
const statusBar = document.getElementById("status-bar");
const dropZone = document.getElementById("drop-zone");
const importBtn = document.getElementById("import-btn");
const exportBtn = document.getElementById("export-btn");
const fileInput = document.getElementById("file-input");

// --- Import ---

function loadLibrary(json) {
  try {
    library = parseLibrary(json);
    activeTopic = library.currentTopic || (library.topics[0]?.name ?? null);
    renderTopics();
    renderDocs();
    exportBtn.hidden = false;
    const total = library.totals;
    setStatus(`${total.topic_count ?? library.topics.length} Themen · ${total.document_count ?? 0} Dokumente geladen`);
  } catch (e) {
    setStatus("Fehler: " + e.message, true);
  }
}

function setStatus(msg, isError = false) {
  statusBar.textContent = msg;
  statusBar.className = "status-bar" + (isError ? " error" : "");
}

importBtn.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", e => {
  const file = e.target.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = ev => {
    try { loadLibrary(JSON.parse(ev.target.result)); } catch { setStatus("Ungültige JSON-Datei.", true); }
  };
  reader.onerror = () => setStatus("Datei konnte nicht gelesen werden.", true);
  reader.readAsText(file, "utf-8");
  e.target.value = "";
});

dropZone.addEventListener("dragover", e => { e.preventDefault(); dropZone.classList.add("drag-over"); });
dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
dropZone.addEventListener("drop", e => {
  e.preventDefault();
  dropZone.classList.remove("drag-over");
  const file = e.dataTransfer.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = ev => {
    try { loadLibrary(JSON.parse(ev.target.result)); } catch { setStatus("Ungültige JSON-Datei.", true); }
  };
  reader.onerror = () => setStatus("Datei konnte nicht gelesen werden.", true);
  reader.readAsText(file, "utf-8");
});

// Demo — buildDemoLibrary() liefert bereits geparste Library; loadLibrary() würde parseLibrary()
// nochmals aufrufen und wegen fehlender schema_version werfen.
document.getElementById("demo-btn").addEventListener("click", () => {
  library = buildDemoLibrary();
  activeTopic = library.currentTopic || (library.topics[0]?.name ?? null);
  renderTopics();
  renderDocs();
  exportBtn.hidden = false;
  const total = library.totals;
  setStatus(`${total.topic_count ?? library.topics.length} Themen · ${total.document_count ?? 0} Dokumente geladen`);
});

// --- Export ---

exportBtn.addEventListener("click", () => {
  if (!library) return;
  const json = JSON.stringify(serializeLibrary(library), null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "dokureader-library-v1.json";
  a.click();
  URL.revokeObjectURL(url);
  setStatus("Bibliothek mit aktuellem Lesestatus exportiert.");
});

// --- Render ---

function renderTopics() {
  if (!library) return;
  topicList.replaceChildren();

  const all = document.createElement("li");
  all.textContent = "Alle Themen";
  all.className = "topic-item" + (activeTopic === null ? " active" : "");
  all.addEventListener("click", () => { activeTopic = null; renderTopics(); renderDocs(); });
  topicList.appendChild(all);

  for (const t of library.topics) {
    const li = document.createElement("li");
    li.className = "topic-item" + (activeTopic === t.name ? " active" : "");
    li.textContent = `${t.name} (${t.documents.length})`;
    li.addEventListener("click", () => { activeTopic = t.name; renderTopics(); renderDocs(); });
    topicList.appendChild(li);
  }
}

function emptyMsg(text) {
  const p = document.createElement("p");
  p.className = "empty";
  p.textContent = text;
  return p;
}

function renderDocs() {
  if (!library) { docList.replaceChildren(emptyMsg("Noch keine Bibliothek geladen.")); return; }
  const q = searchInput.value;
  const showMissing = showMissingChk.checked;
  const docs = filterDocuments(library, { topic: activeTopic, query: q, showMissing });

  if (docs.length === 0) {
    docList.replaceChildren(emptyMsg("Keine Dokumente gefunden."));
    return;
  }

  docList.replaceChildren();
  for (const d of docs) {
    const card = document.createElement("div");
    card.className = "doc-card" + (d.missing ? " missing" : "") + (d.read ? " read" : "");
    card.setAttribute("role", "button");
    card.setAttribute("tabindex", "0");
    card.setAttribute("aria-label", `${d.filename} — ${d.read ? "Gelesen" : "Ungelesen"}, Klicken zum Umschalten`);

    const badge = document.createElement("span");
    badge.className = "ext-badge";
    badge.textContent = d.extension || "?";

    const info = document.createElement("div");
    info.className = "doc-info";

    const name = document.createElement("strong");
    name.textContent = d.filename;

    const meta = document.createElement("span");
    meta.className = "doc-meta";
    const parts = [];
    if (activeTopic === null) parts.push(d.topicName);
    if (d.sizeBytes !== null) parts.push(formatSize(d.sizeBytes));
    if (d.mtime) parts.push(formatDate(d.mtime));
    if (d.missing) parts.push("⚠ Datei fehlt");
    meta.textContent = parts.join(" · ");

    const readBadge = document.createElement("span");
    readBadge.className = "read-badge";
    readBadge.textContent = d.read ? "✓ Gelesen" : "Ungelesen";

    info.append(name, meta);
    card.append(badge, info, readBadge);

    // Klick und Enter/Space schalten den Gelesen-Status um
    const toggleRead = () => {
      setRead(library, d.path, !d.read);
      renderDocs();
    };
    card.addEventListener("click", toggleRead);
    card.addEventListener("keydown", e => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); toggleRead(); }
    });

    docList.appendChild(card);
  }
}

searchInput.addEventListener("input", renderDocs);
showMissingChk.addEventListener("change", renderDocs);

function formatSize(bytes) {
  if (bytes < 1024) return bytes + " B";
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
  return (bytes / (1024 * 1024)).toFixed(1) + " MB";
}

function formatDate(iso) {
  try { return new Date(iso).toLocaleDateString("de-DE"); } catch { return ""; }
}

// --- Service Worker ---

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js").catch(() => {});
}

// Demo on load if ?demo=1
if (new URLSearchParams(location.search).get("demo") === "1") {
  library = buildDemoLibrary();
  activeTopic = library.currentTopic || (library.topics[0]?.name ?? null);
  renderTopics();
  renderDocs();
  exportBtn.hidden = false;
  const total = library.totals;
  setStatus(`${total.topic_count ?? library.topics.length} Themen · ${total.document_count ?? 0} Dokumente geladen`);
} else {
  renderDocs();
}
