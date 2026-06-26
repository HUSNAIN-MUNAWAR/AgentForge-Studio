import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import { join, resolve } from "node:path";
import { existsSync } from "node:fs";

const APP_URL = process.env.APP_URL || "http://127.0.0.1:3000";
const API_URL = process.env.API_URL || process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
const OUT_DIR = resolve(process.cwd(), "..", "docs", "screenshots");
const VIEWPORT = { width: 1440, height: 1000 };

const chromeCandidates = [
  "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
  "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
  "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
];

async function getJSON(path) {
  const response = await fetch(`${API_URL}${path}`);
  if (!response.ok) {
    throw new Error(`GET ${path} failed with ${response.status}`);
  }
  return response.json();
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });

  const packs = await getJSON("/api/packs");
  const runs = await getJSON("/api/runs");
  const customerPack = packs.find((pack) => pack.name === "Customer Feedback Intelligence Team") || packs[0];
  const completedRun = runs.find((run) => run.status === "completed") || runs[0];
  const chromePath = chromeCandidates.find((candidate) => existsSync(candidate));

  const browser = await chromium.launch({
    headless: true,
    executablePath: chromePath,
  });
  const page = await browser.newPage({ viewport: VIEWPORT });

  const targets = [
    ["dashboard.png", "/"],
    ["templates.png", "/templates"],
    ["packs.png", "/packs"],
    ["pack-builder.png", `/packs/${customerPack.id}`],
    ["workflow.png", "/workflow"],
    ["runs.png", "/runs"],
    ["trace-viewer.png", `/traces?run=${completedRun.id}`],
    ["evaluation-lab.png", "/evals"],
    ["approval-queue.png", "/approvals"],
    ["tools.png", "/tools"],
    ["memory.png", "/memory"],
    ["settings.png", "/settings"],
  ];

  for (const [fileName, path] of targets) {
    const url = `${APP_URL}${path}`;
    await page.goto(url, { waitUntil: "networkidle", timeout: 60000 });
    await page.screenshot({
      path: join(OUT_DIR, fileName),
      fullPage: true,
      animations: "disabled",
    });
    console.log(`captured ${fileName}`);
  }

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
