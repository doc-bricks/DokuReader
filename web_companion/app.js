import {
  parseLibrary,
  filterDocuments,
  buildDemoLibrary,
  setRead,
  serializeLibrary,
  STORAGE_KEYS,
  saveLibrarySnapshot,
  loadLibrarySnapshot,
  clearLibrarySnapshot
} from "./library.js";
import { SUPPORTED_LANGUAGES, normalizeLanguage, getDateLocale, t } from "./i18n.js";

let library = null;
let activeTopic = null;
let currentLang = "de";
let lastStatus = null;

const topicList = document.getElementById("topic-list");
const docList = document.getElementById("doc-list");
const searchInput = document.getElementById("search");
const showMissingChk = document.getElementById("show-missing");
const statusBar = document.getElementById("status-bar");
const dropZone = document.getElementById("drop-zone");
const importBtn = document.getElementById("import-btn");
const demoBtn = document.getElementById("demo-btn");
const exportBtn = document.getElementById("export-btn");
const clearBtn = document.getElementById("clear-btn");
const langSelect = document.getElementById("lang-select");
const fileInput = document.getElementById("file-input");

function getSafeStorage() {
  try {
    return typeof window !== "undefined" && window.localStorage ? window.localStorage : null;
  } catch {
    return null;
  }
}

function resolveInitialLanguage() {
  const params = new URLSearchParams(location.search);
  const queryLang = params.get("lang");
  if (queryLang && SUPPORTED_LANGUAGES.includes(normalizeLanguage(queryLang, ""))) {
    return normalizeLanguage(queryLang, "de");
  }
  const storage = getSafeStorage();
  if (storage) {
    try {
      const saved = storage.getItem(STORAGE_KEYS.lang);
      if (saved) return normalizeLanguage(saved, "de");
    } catch {
      // Storage gesperrt -> Browser-Sprache nutzen.
    }
  }
  return normalizeLanguage(navigator.language || "de", "de");
}

function applyStaticTranslations() {
  document.documentElement.lang = currentLang;
  document.title = t("app_title", currentLang);
  if (langSelect) {
    langSelect.value = currentLang;
    langSelect.setAttribute("aria-label", t("lang_label", currentLang));
  }
  for (const el of document.querySelectorAll("[data-i18n]")) {
    const key = el.getAttribute("data-i18n");
    if (key) el.textContent = t(key, currentLang);
  }
  searchInput.placeholder = t("search_placeholder", currentLang);
  searchInput.setAttribute("aria-label", t("search_aria", currentLang));
}

function setStatusKey(key, params = {}, isError = false) {
  lastStatus = { key, params, isError };
  statusBar.textContent = t(key, currentLang, params);
  statusBar.className = "status-bar" + (isError ? " error" : "");
}

function updateActionVisibility() {
  const hasLibrary = Boolean(library);
  exportBtn.hidden = !hasLibrary;
  if (clearBtn) clearBtn.hidden = !hasLibrary;
}

function persistState() {
  const storage = getSafeStorage();
  if (!storage || !library) return { saved: true };
  const result = saveLibrarySnapshot(storage, library, activeTopic);
  if (result.saved === false && result.reason === "quota") {
    const { topicCount, docCount } = countTotals(library);
    setStatusKey("status_storage_quota", { topicCount, docCount });
  }
  return result;
}

function countTotals(lib) {
  const topicCount = lib.totals?.topic_count ?? lib.topics.length;
  const docCount =
    lib.totals?.document_count ??
    lib.topics.reduce((sum, topic) => sum + topic.documents.length, 0);
  return { topicCount, docCount };
}

// --- Language switcher ---

if (langSelect) {
  langSelect.addEventListener("change", () => {
    currentLang = normalizeLanguage(langSelect.value, "de");
    const storage = getSafeStorage();
    if (storage) {
      try { storage.setItem(STORAGE_KEYS.lang, currentLang); } catch { /* ignore */ }
    }
    applyStaticTranslations();
    renderTopics();
    renderDocs();
    if (lastStatus) {
      setStatusKey(lastStatus.key, lastStatus.params, lastStatus.isError);
    }
  });
}

// --- Import ---

function loadLibrary(json) {
  try {
    library = parseLibrary(json);
    activeTopic = library.currentTopic || (library.topics[0]?.name ?? null);
    const persisted = persistState();
    renderTopics();
    renderDocs();
    updateActionVisibility();
    const { topicCount, docCount } = countTotals(library);
    if (persisted.saved === false && persisted.reason === "quota") {
      setStatusKey("status_storage_quota", { topicCount, docCount });
    } else {
      setStatusKey("status_loaded", { topicCount, docCount });
    }
  } catch (e) {
    setStatusKey("status_error_prefix", { message: e.message }, true);
  }
}

importBtn.addEventListener("click", () => fileInput.click());
dropZone.addEventListener("click", () => fileInput.click());
fileInput.addEventListener("change", e => {
  const file = e.target.files?.[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = ev => {
    try { loadLibrary(JSON.parse(ev.target.result)); } catch { setStatusKey("status_invalid_json", {}, true); }
  };
  reader.onerror = () => setStatusKey("status_read_error", {}, true);
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
    try { loadLibrary(JSON.parse(ev.target.result)); } catch { setStatusKey("status_invalid_json", {}, true); }
  };
  reader.onerror = () => setStatusKey("status_read_error", {}, true);
  reader.readAsText(file, "utf-8");
});

// Demo — buildDemoLibrary() liefert bereits eine geparste Library; parseLibrary()
// darf darauf nicht erneut aufgerufen werden.
demoBtn.addEventListener("click", () => {
  library = buildDemoLibrary();
  activeTopic = library.currentTopic || (library.topics[0]?.name ?? null);
  persistState();
  renderTopics();
  renderDocs();
  updateActionVisibility();
  const { topicCount, docCount } = countTotals(library);
  setStatusKey("status_loaded", { topicCount, docCount });
});

// --- Clear persisted local data ---

if (clearBtn) {
  clearBtn.addEventListener("click", () => {
    clearLibrarySnapshot(getSafeStorage());
    library = null;
    activeTopic = null;
    topicList.replaceChildren();
    updateActionVisibility();
    renderDocs();
    setStatusKey("status_cleared");
  });
}

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
  setStatusKey("status_exported");
});

// --- Render ---

function renderTopics() {
  if (!library) {
    topicList.replaceChildren();
    return;
  }
  topicList.replaceChildren();

  const addTopic = (label, topic) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    const isActive = activeTopic === topic;
    button.type = "button";
    button.className = "topic-item" + (isActive ? " active" : "");
    button.textContent = label;
    if (isActive) button.setAttribute("aria-current", "true");
    button.addEventListener("click", () => {
      activeTopic = topic;
      if (topic !== null) library.currentTopic = topic;
      persistState();
      renderTopics();
      renderDocs();
    });
    item.appendChild(button);
    topicList.appendChild(item);
  };

  addTopic(t("all_topics", currentLang), null);

  for (const topic of library.topics) {
    addTopic(`${topic.name} (${topic.documents.length})`, topic.name);
  }
}

function emptyMsg(text) {
  const p = document.createElement("p");
  p.className = "empty";
  p.textContent = text;
  return p;
}

function renderDocs() {
  if (!library) {
    docList.replaceChildren(emptyMsg(t("empty_no_library", currentLang)));
    return;
  }
  const q = searchInput.value;
  const showMissing = showMissingChk.checked;
  const docs = filterDocuments(library, { topic: activeTopic, query: q, showMissing });

  if (docs.length === 0) {
    docList.replaceChildren(emptyMsg(t("empty_no_results", currentLang)));
    return;
  }

  docList.replaceChildren();
  for (const d of docs) {
    const card = document.createElement("div");
    card.className = "doc-card" + (d.missing ? " missing" : "") + (d.read ? " read" : "");
    card.setAttribute("role", "button");
    card.setAttribute("tabindex", "0");
    const stateText = t(d.read ? "state_read" : "state_unread", currentLang);
    card.setAttribute(
      "aria-label",
      t("card_aria_toggle", currentLang, { filename: d.filename, state: stateText })
    );

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
    if (d.missing) parts.push(t("missing_flag", currentLang));
    meta.textContent = parts.join(" · ");

    const readBadge = document.createElement("span");
    readBadge.className = "read-badge";
    readBadge.textContent = t(d.read ? "badge_read" : "badge_unread", currentLang);

    info.append(name, meta);
    card.append(badge, info, readBadge);

    // Klick und Enter/Space schalten den Gelesen-Status um und sichern ihn offline
    const toggleRead = () => {
      setRead(library, d.path, !d.read, d.topicName);
      persistState();
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
  try { return new Date(iso).toLocaleDateString(getDateLocale(currentLang)); } catch { return ""; }
}

// --- Service Worker ---

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("sw.js").catch(() => {});
}

// --- Bootstrapping (Language + Offline State Restoration) ---

currentLang = resolveInitialLanguage();
applyStaticTranslations();

if (new URLSearchParams(location.search).get("demo") === "1") {
  library = buildDemoLibrary();
  activeTopic = library.currentTopic || (library.topics[0]?.name ?? null);
  renderTopics();
  renderDocs();
  updateActionVisibility();
  const { topicCount, docCount } = countTotals(library);
  setStatusKey("status_loaded", { topicCount, docCount });
} else {
  const restored = loadLibrarySnapshot(getSafeStorage());
  if (restored && restored.library) {
    library = restored.library;
    activeTopic = restored.activeTopic;
    renderTopics();
    renderDocs();
    updateActionVisibility();
    const { topicCount, docCount } = countTotals(library);
    setStatusKey("status_restored", { topicCount, docCount });
  } else {
    updateActionVisibility();
    renderDocs();
    if (restored && restored.error === "corrupt") {
      setStatusKey("status_corrupt_cleared", {}, true);
    }
  }
}
