import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { readFileSync, existsSync } from "node:fs";

import { buildDemoLibrary, SCHEMA } from "../library.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");
const appSource = readFileSync(path.join(ROOT, "app.js"), "utf8");

async function read(relativePath) {
  return readFile(path.join(ROOT, relativePath), "utf8");
}

test("manifest exposes installable mobile metadata and icons", async () => {
  const manifest = JSON.parse(await read("manifest.webmanifest"));

  assert.equal(manifest.lang, "de");
  assert.equal(manifest.display, "standalone");
  assert.equal(manifest.start_url, "./");
  assert.equal(manifest.scope, "./");
  assert.ok(Array.isArray(manifest.display_override));
  assert.ok(manifest.display_override.includes("standalone"));

  const sizes = manifest.icons.map((icon) => icon.sizes);
  assert.ok(sizes.includes("192x192"), "192x192-Icon fehlt");
  assert.ok(sizes.includes("512x512"), "512x512-Icon fehlt");
  const hasMaskable = manifest.icons.some((icon) => icon.purpose === "maskable");
  assert.ok(hasMaskable, "Kein maskable-Icon gefunden");

  for (const icon of manifest.icons) {
    await readFile(path.join(ROOT, icon.src));
  }
});

test("index wires mobile shell metadata and icons", async () => {
  const html = await read("index.html");

  assert.match(html, /viewport-fit=cover/);
  assert.match(html, /name="theme-color"/);
  assert.doesNotMatch(html, /apple-mobile-web-app-capable/, "deprecated seit iOS 11.3 — entfernt");
  assert.match(html, /apple-touch-icon/);
  assert.match(html, /manifest\.webmanifest/);
});

test("service worker caches the full offline shell", async () => {
  const sw = await read("sw.js");

  for (const asset of [
    "./index.html",
    "./style.css",
    "./app.js",
    "./library.js",
    "./manifest.webmanifest",
    "./icons/dokureader-companion-180.png",
    "./icons/dokureader-companion-192.png",
    "./icons/Icon-192.png",
    "./icons/Icon-512.png",
    "./icons/Icon-maskable-192.png",
    "./icons/Icon-maskable-512.png"
  ]) {
    assert.match(sw, new RegExp(asset.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
  assert.ok(
    /caches\.match\([^)]*ignoreSearch\s*:\s*true/.test(sw),
    "caches.match muss { ignoreSearch: true } nutzen — Offline-Fail bei ?-URLs"
  );
});

test("app.js FileReader onerror handler vorhanden (Bug #4)", () => {
  const occurrences = (appSource.match(/reader\.onerror/g) || []).length;
  assert.ok(occurrences >= 2, "reader.onerror muss in beiden FileReader-Blöcken (fileInput + dropZone) gesetzt sein");
});

describe("iOS PWA-Härtung", () => {
  const html = readFileSync(path.join(ROOT, "index.html"), "utf8");
  const css = readFileSync(path.join(ROOT, "style.css"), "utf8");
  const sw = readFileSync(path.join(ROOT, "sw.js"), "utf8");

  test("viewport enthält viewport-fit=cover (Notch/Dynamic Island)", () => {
    assert.match(html, /viewport-fit=cover/);
  });

  test("apple-touch-icon zeigt auf dokureader-companion-180.png", () => {
    assert.match(html, /apple-touch-icon.*dokureader-companion-180\.png/s);
  });

  test("apple-mobile-web-app-title ist vorhanden", () => {
    assert.match(html, /apple-mobile-web-app-title/);
  });

  test("apple-mobile-web-app-status-bar-style ist vorhanden", () => {
    assert.match(html, /apple-mobile-web-app-status-bar-style/);
  });

  test("KEIN apple-mobile-web-app-capable (deprecated seit iOS 11.3)", () => {
    assert.doesNotMatch(html, /apple-mobile-web-app-capable/);
  });

  test("dokureader-companion-180.png existiert physisch in icons/", () => {
    assert.ok(existsSync(path.join(ROOT, "icons", "dokureader-companion-180.png")));
  });

  test("style.css enthält safe-area-inset-top", () => {
    assert.match(css, /safe-area-inset-top/);
  });

  test("style.css hat body mit env(safe-area-inset-bottom)", () => {
    assert.match(css, /safe-area-inset-bottom/);
  });

  test("sw.js enthält dokureader-companion-180.png in ASSETS", () => {
    assert.match(sw, /dokureader-companion-180\.png/);
  });
});

test("Bug #1 regression: Demo-Handler ruft loadLibrary(buildDemoLibrary()) nicht auf (Doppelparse-Bug)", () => {
  assert.doesNotMatch(
    appSource,
    /loadLibrary\(buildDemoLibrary\(\)\)/,
    "loadLibrary(buildDemoLibrary()) ist ein Doppelparse-Bug — Demo-Handler muss library direkt zuweisen"
  );
});

// BUG-W1 Regressionstest
test("BUG-W1 regression: sw.js fetch hat .catch() für Offline-Fallback", async () => {
  const sw = await read("sw.js");
  assert.ok(
    /fetch\(e\.request\)[\s\S]{0,100}\.catch\(/.test(sw),
    "BUG-W1: sw.js fetch muss .catch() für Offline-Fallback haben"
  );
  assert.ok(sw.includes("503"), "BUG-W1: Offline-Fallback muss HTTP 503 zurückgeben");
  const m = sw.match(/CACHE\s*=\s*["']dokureader-companion-v(\d+)["']/);
  assert.ok(m && parseInt(m[1]) >= 4, "CACHE muss auf v4+ gebumpt sein (nach BUG-W1-Fix)");
});

test("demo library stays compatible with the production schema", () => {
  const demo = buildDemoLibrary();

  assert.equal(demo.currentTopic, "Forschung");
  assert.equal(demo.totals.topic_count, 3);
  assert.ok(demo.topics.every((topic) => typeof topic.name === "string"));
  assert.ok(
    demo.topics
      .flatMap((topic) => topic.documents)
      .every((document) => document.extension.startsWith("."))
  );
  assert.equal(SCHEMA, "dokureader-library-v1");
});
