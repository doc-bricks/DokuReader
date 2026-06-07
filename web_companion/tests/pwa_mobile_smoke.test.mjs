import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { buildDemoLibrary, SCHEMA } from "../library.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(__dirname, "..");

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
  assert.deepEqual(sizes, ["192x192", "512x512"]);

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
    "./icons/dokureader-companion-512.png"
  ]) {
    assert.match(sw, new RegExp(asset.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")));
  }
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
