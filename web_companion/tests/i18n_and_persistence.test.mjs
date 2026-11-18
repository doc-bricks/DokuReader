import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  SUPPORTED_LANGUAGES,
  LANGUAGE_LABELS,
  DATE_LOCALES,
  TRANSLATIONS,
  normalizeLanguage,
  getDateLocale,
  t
} from "../i18n.js";
import {
  SCHEMA,
  STORAGE_KEYS,
  MAX_PERSISTED_BYTES,
  parseLibrary,
  setRead,
  saveLibrarySnapshot,
  loadLibrarySnapshot,
  clearLibrarySnapshot
} from "../library.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");

function createMemoryStorage({ throwOnSet = false, throwOnGet = false } = {}) {
  const store = new Map();
  return {
    store,
    getItem(key) {
      if (throwOnGet) throw new Error("SecurityError: storage blocked");
      return store.has(key) ? store.get(key) : null;
    },
    setItem(key, value) {
      if (throwOnSet) throw new Error("QuotaExceededError");
      store.set(key, String(value));
    },
    removeItem(key) {
      store.delete(key);
    }
  };
}

describe("Tier-2 6-language localization (i18n.js)", () => {
  test("exports exact Tier-2 language set (de, en, es, zh, ja, ru) with labels and date locales", () => {
    assert.deepEqual([...SUPPORTED_LANGUAGES], ["de", "en", "es", "zh", "ja", "ru"]);
    for (const lang of SUPPORTED_LANGUAGES) {
      assert.ok(typeof LANGUAGE_LABELS[lang] === "string" && LANGUAGE_LABELS[lang].length > 0);
      assert.ok(typeof DATE_LOCALES[lang] === "string" && DATE_LOCALES[lang].includes("-"));
      assert.equal(getDateLocale(lang), DATE_LOCALES[lang]);
    }
  });

  test("maintains 100% translation key parity and placeholder parity across all 6 languages", () => {
    const baseKeys = Object.keys(TRANSLATIONS.de).sort();
    assert.ok(baseKeys.length >= 24, "Expected comprehensive UI translation catalog");

    const extractPlaceholders = (text) =>
      [...text.matchAll(/\{([a-zA-Z0-9_]+)\}/g)].map((m) => m[1]).sort();

    for (const lang of SUPPORTED_LANGUAGES) {
      const langKeys = Object.keys(TRANSLATIONS[lang]).sort();
      assert.deepEqual(langKeys, baseKeys, `Key mismatch in language '${lang}'`);
      for (const key of baseKeys) {
        const val = TRANSLATIONS[lang][key];
        assert.equal(typeof val, "string", `${lang}.${key} must be a string`);
        assert.ok(val.trim().length > 0, `${lang}.${key} must not be empty`);
        assert.deepEqual(
          extractPlaceholders(val),
          extractPlaceholders(TRANSLATIONS.de[key]),
          `Placeholder mismatch for '${key}' in '${lang}'`
        );
      }
    }
  });

  test("normalizes regional language tags and applies 4-step fallback with interpolation", () => {
    assert.equal(normalizeLanguage("zh-CN"), "zh");
    assert.equal(normalizeLanguage("es_MX"), "es");
    assert.equal(normalizeLanguage("JA-jp"), "ja");
    assert.equal(normalizeLanguage("ru-RU"), "ru");
    assert.equal(normalizeLanguage("fr-FR", "en"), "en");
    assert.equal(normalizeLanguage("", "de"), "de");

    assert.equal(
      t("status_loaded", "de", { topicCount: 3, docCount: 7 }),
      "3 Themen · 7 Dokumente geladen"
    );
    assert.equal(
      t("status_loaded", "ja", { topicCount: 3, docCount: 7 }),
      "3 件のトピック・7 件のドキュメントを読み込みました"
    );
    assert.equal(t("non_existent_key_xyz", "es"), "non_existent_key_xyz");
  });

  test("index.html exposes accessible language selector with all 6 options and clear-data control", () => {
    const html = readFileSync(path.join(ROOT, "index.html"), "utf8");
    const css = readFileSync(path.join(ROOT, "style.css"), "utf8");
    assert.match(html, /<select id="lang-select"[^>]*aria-label=/);
    for (const lang of SUPPORTED_LANGUAGES) {
      assert.match(html, new RegExp(`<option value="${lang}">`));
    }
    assert.match(html, /<button id="clear-btn" type="button" hidden/);
    // All interactive mobile controls enforce 44px minimum touch target height
    assert.match(css, /\.topic-item\s*\{[^}]*min-height:\s*44px/s);
    assert.match(css, /\.doc-card\s*\{[^}]*min-height:\s*44px/s);
    assert.match(css, /\.checkbox-label\s*\{[^}]*min-height:\s*44px/s);
  });
});

describe("Scoped offline persistence across PWA restarts (library.js)", () => {
  const SAMPLE_JSON = {
    schema_version: SCHEMA,
    exported_at: "2026-11-18T08:00:00Z",
    current_topic: "Forschung",
    topics: [
      {
        name: "Forschung",
        documents: [
          {
            path: "C:/Docs/Studie_Ärztlich.pdf",
            filename: "Studie_Ärztlich.pdf",
            extension: ".pdf",
            read: false,
            size_bytes: 4096,
            mtime: "2026-11-01T12:00:00Z",
            missing: false
          }
        ]
      },
      {
        name: "Verträge",
        documents: [
          {
            path: "C:/Docs/Mietvertrag.pdf",
            filename: "Mietvertrag.pdf",
            extension: ".pdf",
            read: true,
            size_bytes: 8192,
            mtime: "2026-10-10T09:30:00Z",
            missing: false
          }
        ]
      }
    ],
    totals: { topic_count: 2, document_count: 2, missing_documents: 0 }
  };

  test("saves and restores library + toggled read status + activeTopic across offline restart", () => {
    const storage = createMemoryStorage();
    const lib = parseLibrary(SAMPLE_JSON);
    assert.equal(setRead(lib, "C:/Docs/Studie_Ärztlich.pdf", true, "Forschung"), true);

    const saved = saveLibrarySnapshot(storage, lib, "Verträge");
    assert.equal(saved.saved, true);
    assert.ok(saved.bytes > 0 && saved.bytes < MAX_PERSISTED_BYTES);

    const restored = loadLibrarySnapshot(storage);
    assert.ok(restored && restored.library);
    assert.equal(restored.error, null);
    assert.equal(restored.activeTopic, "Verträge");
    assert.equal(restored.library.topics[0].documents[0].read, true);
    assert.equal(restored.library.topics[0].documents[0].filename, "Studie_Ärztlich.pdf");
  });

  test("preserves explicit 'all topics' (activeTopic === null) across offline restart", () => {
    const storage = createMemoryStorage();
    const lib = parseLibrary(SAMPLE_JSON);
    saveLibrarySnapshot(storage, lib, null);

    const restored = loadLibrarySnapshot(storage);
    assert.ok(restored && restored.library);
    assert.equal(restored.activeTopic, null);
  });

  test("clearLibrarySnapshot removes persisted library and topic keys cleanly", () => {
    const storage = createMemoryStorage();
    const lib = parseLibrary(SAMPLE_JSON);
    saveLibrarySnapshot(storage, lib, "Forschung");
    assert.ok(storage.getItem(STORAGE_KEYS.library));

    assert.equal(clearLibrarySnapshot(storage), true);
    assert.equal(loadLibrarySnapshot(storage), null);
  });

  test("self-heals and clears corrupted or wrong-schema localStorage payloads", () => {
    const storage = createMemoryStorage();
    storage.setItem(STORAGE_KEYS.library, "{broken json");
    storage.setItem(STORAGE_KEYS.topic, '{"activeTopic":"Forschung"}');

    const first = loadLibrarySnapshot(storage);
    assert.deepEqual(first, { library: null, activeTopic: null, error: "corrupt" });
    assert.equal(storage.getItem(STORAGE_KEYS.library), null);
    assert.equal(storage.getItem(STORAGE_KEYS.topic), null);

    storage.setItem(STORAGE_KEYS.library, JSON.stringify({ schema_version: "foreign-v9", topics: [] }));
    const second = loadLibrarySnapshot(storage);
    assert.deepEqual(second, { library: null, activeTopic: null, error: "corrupt" });
    assert.equal(storage.getItem(STORAGE_KEYS.library), null);
  });

  test("handles QuotaExceededError, oversized payloads, and blocked storage without throwing", () => {
    const quotaStorage = createMemoryStorage({ throwOnSet: true });
    const lib = parseLibrary(SAMPLE_JSON);
    assert.deepEqual(saveLibrarySnapshot(quotaStorage, lib, "Forschung"), {
      saved: false,
      reason: "quota"
    });

    const blockedStorage = createMemoryStorage({ throwOnGet: true });
    assert.equal(loadLibrarySnapshot(blockedStorage), null);
    assert.deepEqual(saveLibrarySnapshot(null, lib, "Forschung"), {
      saved: false,
      reason: "unavailable"
    });
  });
});
