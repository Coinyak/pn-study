#!/usr/bin/env node
/**
 * Offline topic-jump validator for PN_study_split.html
 * Checks that moved (or sample) quiz ids land in their declared data-topic.
 *
 * Usage:
 *   node scripts/validate-topic-jumps.mjs
 *   node scripts/validate-topic-jumps.mjs --ids oe-filter,kshp-48
 *   node scripts/validate-topic-jumps.mjs --file ./PN_study_split.html
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");

const args = process.argv.slice(2);
const fileArg = args.includes("--file") ? args[args.indexOf("--file") + 1] : path.join(root, "PN_study_split.html");
const idsArg = args.includes("--ids") ? args[args.indexOf("--ids") + 1] : "";

const DEFAULT_MOVED = [
  "oe-filter","oe-hang","quizlet-pn-001","quizlet-pn-002","quizlet-pn-007","quizlet-pn-009",
  "quizlet-pn-014","quizlet-pn-020","quizlet-pn-026","quizlet-pn-040","quizlet-pn-041",
  "quizlet-pn-042","quizlet-pn-052","kshp-05","kshp-13","kshp-28","kshp-48","kshp-51",
  "kshp-54","quizlet-iib-019","quizlet-iib-034","quizlet-iib-048","quizlet-home-ns-009",
  "quizlet-home-ns-010","oep-bcscp-q-034","oep-bcscp-q-060","oep-bcscp-q-064",
  "nbnsc-cnsc-sample-02","nbnsc-cnsc-sample-03","nbnsc-cnsc-sample-06","nbnsc-cnsc-sample-07",
  "quizlet-home-ns-003","medex-019","cnsc-nutrition-support-027","bcnsp-004","bcnsp-005",
  "bcnsp-012","bcnsp-017","bcnsp-043","bcnsp-057","bcnsp-066","bcnsp-088","bcnsp-090",
  "cnsc-nutrition-support-045","cnsc-nutrition-support-046","cnsc-nutrition-support-049",
  "cnsc-nutrition-support-050","cnsc-nutrition-support-055","cnsc-nutrition-support-059",
  "allaccess-010","bcnsp-041","bcnsp-029","cnsc-nutrition-support-081","bcnsp-003",
  "bcnsp-019","bcnsp-056","bcnsp-063","rxk-4_1-3","rxk-4_1-6","quizlet-iib-042",
];

const html = fs.readFileSync(fileArg, "utf8");
const qs = JSON.parse(html.match(/const QUESTIONS\s*=\s*(\[[\s\S]*?\]);\s*\n/)[1]);
const hints = JSON.parse(html.match(/const CORE_HINTS\s*=\s*(\{[\s\S]*?\});\s*\n/)[1].replace(/,\s*}/g, "}").replace(/,\s*]/g, "]"));
const skip = new Set(JSON.parse(html.match(/const CORE_SKIP\s*=\s*new Set\((\[.*?\])\)/s)[1]));

const secRe = /<section class="sec" data-topic="([^"]+)" id="([^"]+)">([\s\S]*?)<\/section>/g;
const secs = [];
let m;
while ((m = secRe.exec(html))) secs.push({ topic: m[1], id: m[2], body: m[3] });

function strip(t) {
  return t.replace(/<[^>]+>/g, "").replace(/\s+/g, " ").trim();
}
function nodesFor(sec) {
  const out = [];
  for (const [re, tag] of [
    [/<li\b[^>]*>([\s\S]*?)<\/li>/g, "LI"],
    [/<tr\b[^>]*>([\s\S]*?)<\/tr>/g, "TR"],
  ]) {
    let x;
    while ((x = re.exec(sec.body))) {
      const text = strip(x[1]);
      if (text) out.push({ tag, text, sec });
    }
  }
  return out;
}
const allNodes = secs.flatMap(nodesFor);
const norm = (s) => String(s || "").toLowerCase().replace(/\s+/g, " ");

const ids = idsArg ? idsArg.split(",").map((s) => s.trim()).filter(Boolean) : DEFAULT_MOVED;
const byId = Object.fromEntries(qs.map((q) => [q.id, q]));

let ok = 0, fail = 0, skipped = 0;
const failures = [];
for (const id of ids) {
  const q = byId[id];
  if (!q) { failures.push({ id, reason: "missing" }); fail++; continue; }
  if (skip.has(id)) { skipped++; continue; }
  const hintsFor = hints[id] || [];
  const top = norm(hintsFor[0] || q.needle || "");
  const topicNodes = allNodes.filter((n) => n.sec.topic === q.topic);
  const local = top ? topicNodes.filter((n) => norm(n.text).includes(top)) : [];
  const wide = top ? allNodes.filter((n) => norm(n.text).includes(top)) : [];
  if (local.length) { ok++; continue; }
  if (wide.length) {
    failures.push({ id, declared: q.topic, land: wide[0].sec.topic, hit: wide[0].text.slice(0, 80) });
    fail++;
  } else {
    failures.push({ id, declared: q.topic, reason: "no-hint-hit", hint: hintsFor[0] || q.needle });
    fail++;
  }
}

const summary = { file: fileArg, checked: ids.length, ok, fail, skipped, failures };
console.log(JSON.stringify(summary, null, 2));
process.exit(fail ? 1 : 0);
