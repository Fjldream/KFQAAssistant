import { mkdir, copyFile } from "node:fs/promises";
import path from "node:path";
import { context, build } from "esbuild";

const root = process.cwd();
const outdir = path.join(root, "docs", "public");
const outfile = path.join(outdir, "kingiask-widget.js");
const configSource = path.join(root, "helper-assistant.config.js");
const configTarget = path.join(outdir, "helper-assistant.config.js");
const watch = process.argv.includes("--watch");

const options = {
  entryPoints: [path.join(root, "widget", "src", "index.ts")],
  outfile,
  bundle: true,
  minify: true,
  sourcemap: false,
  format: "iife",
  target: ["es2019"],
  legalComments: "none"
};

async function copyConfig() {
  await mkdir(outdir, { recursive: true });
  await copyFile(configSource, configTarget);
}

if (watch) {
  await copyConfig();
  const buildContext = await context(options);
  await buildContext.watch();
  console.log("KingIAsk widget build watching...");
} else {
  await copyConfig();
  await build(options);
  console.log(`KingIAsk widget built: ${outfile}`);
}
