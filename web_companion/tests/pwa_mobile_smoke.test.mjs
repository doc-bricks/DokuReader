import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { readFileSync } from "node:fs";

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
  assert.match(html, /apple-mobile-web-app-capable/);
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
