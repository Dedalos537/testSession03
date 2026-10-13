// Verifica que los <script> inline del HTML compilen (error de sintaxis = pipeline en rojo).
import { readFileSync } from "node:fs";
import vm from "node:vm";

const file = process.argv[2] ?? "index.html";
const html = readFileSync(file, "utf8");
const scripts = [...html.matchAll(/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g)].map(m => m[1]);
if (!scripts.length) { console.error(`No hay scripts inline en ${file}`); process.exit(1); }
let failed = 0;
scripts.forEach((code, i) => {
  try { new vm.Script(code, { filename: `${file}#script${i + 1}` }); console.log(`OK  script #${i + 1} (${code.length} chars)`); }
  catch (e) { failed++; console.error(`ERR script #${i + 1}: ${e.message}`); }
});
process.exit(failed ? 1 : 0);
