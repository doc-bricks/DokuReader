/**
 * library.js — DokuReader Web Companion core logic
 * Parses and queries dokureader-library-v1.json payloads.
 */

export const SCHEMA = "dokureader-library-v1";

export function parseLibrary(json) {
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
 * Gibt true zurück, wenn das Dokument gefunden und geändert wurde.
 */
export function setRead(library, docPath, value) {
  for (const topic of library.topics) {
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
