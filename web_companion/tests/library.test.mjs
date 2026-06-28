import { test } from "node:test";
import assert from "node:assert/strict";
import { parseLibrary, filterDocuments, buildDemoLibrary, setRead, serializeLibrary, SCHEMA } from "../library.js";

const SAMPLE = {
  schema_version: SCHEMA,
  exported_at: "2026-06-01T10:00:00Z",
  current_topic: "Forschung",
  topics: [
    {
      name: "Forschung",
      documents: [
        { filename: "paper.pdf", extension: ".pdf", read: true, size_bytes: 100000, mtime: "2026-05-01T00:00:00Z", missing: false, path: "/docs/paper.pdf" },
        { filename: "lost.txt", extension: ".txt", read: false, size_bytes: null, mtime: null, missing: true, path: "/docs/lost.txt" }
      ]
    },
    {
      name: "Verträge",
      documents: [
        { filename: "vertrag.pdf", extension: ".pdf", read: false, size_bytes: 50000, mtime: "2026-01-01T00:00:00Z", missing: false, path: "/docs/vertrag.pdf" }
      ]
    }
  ],
  totals: { topic_count: 2, document_count: 3, missing_documents: 1 }
};

test("parseLibrary extracts topics and documents", () => {
  const lib = parseLibrary(SAMPLE);
  assert.equal(lib.topics.length, 2);
  assert.equal(lib.topics[0].name, "Forschung");
  assert.equal(lib.topics[0].documents.length, 2);
  assert.equal(lib.currentTopic, "Forschung");
  assert.equal(lib.totals.document_count, 3);
});

test("parseLibrary maps document fields correctly", () => {
  const lib = parseLibrary(SAMPLE);
  const d = lib.topics[0].documents[0];
  assert.equal(d.filename, "paper.pdf");
  assert.equal(d.read, true);
  assert.equal(d.missing, false);
  assert.equal(d.sizeBytes, 100000);
});

test("parseLibrary rejects unknown schema", () => {
  assert.throws(
    () => parseLibrary({ ...SAMPLE, schema_version: "andere-v99" }),
    /Unbekanntes Schema/
  );
});

test("filterDocuments returns all docs without filter", () => {
  const lib = parseLibrary(SAMPLE);
  const docs = filterDocuments(lib);
  assert.equal(docs.length, 3);
});

test("filterDocuments filters by topic", () => {
  const lib = parseLibrary(SAMPLE);
  const docs = filterDocuments(lib, { topic: "Verträge" });
  assert.equal(docs.length, 1);
  assert.equal(docs[0].filename, "vertrag.pdf");
});

test("filterDocuments filters missing documents when showMissing=false", () => {
  const lib = parseLibrary(SAMPLE);
  const docs = filterDocuments(lib, { showMissing: false });
  assert.ok(docs.every(d => !d.missing));
  assert.equal(docs.length, 2);
});

test("filterDocuments searches by filename", () => {
  const lib = parseLibrary(SAMPLE);
  const docs = filterDocuments(lib, { query: "paper" });
  assert.equal(docs.length, 1);
  assert.equal(docs[0].filename, "paper.pdf");
});

test("filterDocuments adds topicName to each document", () => {
  const lib = parseLibrary(SAMPLE);
  const docs = filterDocuments(lib);
  assert.ok(docs.every(d => typeof d.topicName === "string"));
  assert.equal(docs[0].topicName, "Forschung");
});

test("buildDemoLibrary returns parseable demo data", () => {
  const lib = buildDemoLibrary();
  assert.ok(lib.topics.length >= 2);
  assert.ok(lib.totals.topic_count >= 2);
});

// --- setRead ---

test("setRead schaltet Gelesen-Status eines Dokuments anhand des Pfads um", () => {
  const lib = parseLibrary(SAMPLE);
  const doc = lib.topics[0].documents[0]; // paper.pdf, read: true
  assert.equal(doc.read, true);
  setRead(lib, "/docs/paper.pdf", false);
  assert.equal(doc.read, false);
  setRead(lib, "/docs/paper.pdf", true);
  assert.equal(doc.read, true);
});

test("setRead gibt false zurück bei unbekanntem Pfad", () => {
  const lib = parseLibrary(SAMPLE);
  assert.equal(setRead(lib, "/existiert/nicht.pdf", true), false);
});

test("setRead gibt true zurück wenn Dokument gefunden und geändert wurde", () => {
  const lib = parseLibrary(SAMPLE);
  assert.equal(setRead(lib, "/docs/vertrag.pdf", true), true);
});

// --- serializeLibrary ---

test("serializeLibrary Round-Trip erhält alle Felder", () => {
  const lib = parseLibrary(SAMPLE);
  const serialized = serializeLibrary(lib);
  const lib2 = parseLibrary(serialized);
  assert.equal(lib2.topics.length, lib.topics.length);
  assert.equal(lib2.topics[0].documents[0].filename, "paper.pdf");
  assert.equal(lib2.topics[0].documents[0].sizeBytes, 100000);
  assert.equal(lib2.topics[0].documents[1].missing, true);
  assert.equal(lib2.currentTopic, "Forschung");
});

test("serializeLibrary Round-Trip überträgt geänderten Gelesen-Status korrekt", () => {
  const lib = parseLibrary(SAMPLE);
  setRead(lib, "/docs/paper.pdf", false);
  const serialized = serializeLibrary(lib);
  const lib2 = parseLibrary(serialized);
  assert.equal(lib2.topics[0].documents[0].read, false);
});

test("serializeLibrary erzeugt gültiges dokureader-library-v1 Schema", () => {
  const lib = parseLibrary(SAMPLE);
  const serialized = serializeLibrary(lib);
  assert.equal(serialized.schema_version, SCHEMA);
  assert.ok(typeof serialized.exported_at === "string");
  assert.ok(Array.isArray(serialized.topics));
  assert.equal(serialized.totals.topic_count, 2);
  assert.equal(serialized.totals.document_count, 3);
  assert.equal(serialized.totals.missing_documents, 1);
});

test("serializeLibrary mappt sizeBytes auf size_bytes zurück", () => {
  const lib = parseLibrary(SAMPLE);
  const serialized = serializeLibrary(lib);
  assert.equal(serialized.topics[0].documents[0].size_bytes, 100000);
  assert.equal(serialized.topics[0].documents[1].size_bytes, null);
});
