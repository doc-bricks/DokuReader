/**
 * library.js — DokuReader Web Companion core logic & scoped offline persistence
 * Parses, queries, serializes, and locally caches dokureader-library-v1.json payloads.
 */

export const SCHEMA = "dokureader-library-v1";

export const STORAGE_KEYS = Object.freeze({
  library: "dokureader_companion_library_v1",
  topic: "dokureader_companion_topic_v1",
  lang: "dokureader_companion_lang_v1"
});

export const MAX_PERSISTED_BYTES = 4 * 1024 * 1024; // 4 MiB scoped localStorage ceiling (INV-ISOLATION-05)

export function parseLibrary(json) {
  if (!json || typeof json !== "object" || Array.isArray(json)) {
    throw new Error("Ungültiges Bibliotheksformat");
  }
  if (json.schema_version !== SCHEMA) {
    throw new Error(`Unbekanntes Schema: ${json.schema_version}`);
  }
  return {
    exportedAt: json.exported_at || "",
    currentTopic: json.current_topic || null,
    topics: (json.topics || []).map(t => ({
      name: t.name || "",
      documents: (t.documents || []).map(d => ({
        path: d.path || "",
        filename: d.filename || "",
        extension: d.extension || "",
        read: Boolean(d.read),
        sizeBytes: d.size_bytes ?? null,
        mtime: d.mtime || null,
        missing: Boolean(d.missing)
      }))
    })),
    totals: json.totals || {}
  };
}

export function filterDocuments(library, { topic = null, query = "", showMissing = true } = {}) {
  const q = query.trim().toLowerCase();
  return library.topics
    .filter(t => topic === null || t.name === topic)
    .flatMap(t => t.documents
      .filter(d => showMissing || !d.missing)
      .filter(d => !q || d.filename.toLowerCase().includes(q))
      .map(d => ({ ...d, topicName: t.name }))
    );
}

/**
 * Setzt den Gelesen-Status eines Dokuments anhand seines Pfads.
 * Wie am Desktop gilt der Status je Thema: mit topicName nur in diesem Thema
 * (dieselbe Datei kann in mehreren Themen liegen).
 * Gibt true zurück, wenn das Dokument gefunden und geändert wurde.
 */
export function setRead(library, docPath, value, topicName = null) {
  for (const topic of library.topics) {
    if (topicName !== null && topic.name !== topicName) continue;
    for (const doc of topic.documents) {
      if (doc.path === docPath) {
        doc.read = Boolean(value);
        return true;
      }
    }
  }
  return false;
}

/**
 * Serialisiert eine geparste Library zurück ins dokureader-library-v1 JSON-Format.
 * Umkehrung von parseLibrary() — Felder werden auf die JSON-Schlüssel zurückgemappt
 * (sizeBytes → size_bytes, currentTopic → current_topic usw.).
 */
export function serializeLibrary(library) {
  return {
    schema_version: SCHEMA,
    exported_at: new Date().toISOString(),
    current_topic: library.currentTopic || null,
    topics: library.topics.map(t => ({
      name: t.name,
      document_count: t.documents.length,
      documents: t.documents.map(d => ({
        path: d.path,
        filename: d.filename,
        extension: d.extension,
        read: d.read,
        size_bytes: d.sizeBytes ?? null,
        mtime: d.mtime || null,
        missing: d.missing
      }))
    })),
    totals: {
      topic_count: library.topics.length,
      document_count: library.topics.reduce((n, t) => n + t.documents.length, 0),
      missing_documents: library.topics.reduce(
        (n, t) => n + t.documents.filter(d => d.missing).length, 0
      )
    }
  };
}

/**
 * Persistiert die aktuell geladene Bibliothek + Themenauswahl im lokalen Browser-Storage
 * (INV-ISOLATION-05, kein Netzwerk-Egress). Fängt Quota- und Zugriffsausnahmen sicher ab.
 */
export function saveLibrarySnapshot(storage, library, activeTopic = null) {
  if (!storage || !library) {
    return { saved: false, reason: "unavailable" };
  }
  try {
    const payload = serializeLibrary(library);
    const serialized = JSON.stringify(payload);
    const byteLength = new TextEncoder().encode(serialized).length;
    if (byteLength > MAX_PERSISTED_BYTES) {
      return { saved: false, reason: "quota" };
    }
    storage.setItem(STORAGE_KEYS.library, serialized);
    storage.setItem(
      STORAGE_KEYS.topic,
      JSON.stringify({ activeTopic: activeTopic === null ? null : String(activeTopic) })
    );
    return { saved: true, bytes: byteLength };
  } catch {
    return { saved: false, reason: "quota" };
  }
}

/**
 * Stellt eine zuvor lokal gespeicherte Bibliothek beim Offline-Neustart wieder her.
 * Beschädigte oder schemafremde Einträge werden automatisch bereinigt (Self-Healing).
 */
export function loadLibrarySnapshot(storage) {
  if (!storage) {
    return null;
  }
  let rawText = null;
  try {
    rawText = storage.getItem(STORAGE_KEYS.library);
  } catch {
    return null;
  }
  if (!rawText) {
    return null;
  }
  try {
    const byteLength = new TextEncoder().encode(rawText).length;
    if (byteLength > MAX_PERSISTED_BYTES) {
      throw new Error("Persisted library exceeds size ceiling");
    }
    const parsedJson = JSON.parse(rawText);
    const library = parseLibrary(parsedJson);
    let resolvedTopic = library.currentTopic || (library.topics[0]?.name ?? null);
    try {
      const rawTopic = storage.getItem(STORAGE_KEYS.topic);
      if (rawTopic) {
        const topicState = JSON.parse(rawTopic);
        if (topicState && topicState.activeTopic === null) {
          resolvedTopic = null;
        } else if (
          topicState &&
          typeof topicState.activeTopic === "string" &&
          library.topics.some(t => t.name === topicState.activeTopic)
        ) {
          resolvedTopic = topicState.activeTopic;
        }
      }
    } catch {
      // Topic-Zusatzzustand ist optional; Fallback auf currentTopic greift.
    }
    return { library, activeTopic: resolvedTopic, error: null };
  } catch {
    clearLibrarySnapshot(storage);
    return { library: null, activeTopic: null, error: "corrupt" };
  }
}

export function clearLibrarySnapshot(storage) {
  if (!storage) return false;
  try {
    storage.removeItem(STORAGE_KEYS.library);
    storage.removeItem(STORAGE_KEYS.topic);
    return true;
  } catch {
    return false;
  }
}

export function buildDemoLibrary() {
  return parseLibrary({
    schema_version: SCHEMA,
    exported_at: new Date().toISOString(),
    app_name: "Dokumentenbibliothek (Demo)",
    app_version: "demo",
    current_topic: "Forschung",
    topics: [
      {
        name: "Forschung",
        documents: [
          { filename: "Paper.pdf", extension: ".pdf", read: true, size_bytes: 182044, mtime: "2026-05-25T18:42:01Z", missing: false, path: "C:/Demo/Paper.pdf" },
          { filename: "Notizen.txt", extension: ".txt", read: false, size_bytes: null, mtime: null, missing: true, path: "C:/Demo/Notizen.txt" }
        ]
      },
      {
        name: "Verträge",
        documents: [
          { filename: "Mietvertrag.pdf", extension: ".pdf", read: true, size_bytes: 75000, mtime: "2026-01-10T10:00:00Z", missing: false, path: "C:/Demo/Mietvertrag.pdf" },
          { filename: "Arbeitsvertrag.docx", extension: ".docx", read: false, size_bytes: 42000, mtime: "2025-12-01T08:00:00Z", missing: false, path: "C:/Demo/Arbeitsvertrag.docx" }
        ]
      },
      {
        name: "Medizin",
        documents: [
          { filename: "Befund_2026.pdf", extension: ".pdf", read: false, size_bytes: 33000, mtime: "2026-03-15T12:00:00Z", missing: false, path: "C:/Demo/Befund_2026.pdf" }
        ]
      }
    ],
    totals: { topic_count: 3, document_count: 5, missing_documents: 1 }
  });
}
