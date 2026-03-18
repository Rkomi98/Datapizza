import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";

const APP_URL = "http://127.0.0.1:8501";
const OUTPUT_DIR = path.resolve("datapizza_dashboard_rag/docs/screenshots");

async function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function main() {
  await fs.mkdir(OUTPUT_DIR, { recursive: true });

  const browser = await chromium.launch({
    channel: "chrome",
    headless: true,
  });

  const context = await browser.newContext({
    viewport: { width: 1600, height: 1200 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();

  await page.goto(APP_URL, { waitUntil: "domcontentloaded", timeout: 120000 });
  await page.getByText("Mondadori Datapizza Dashboard").waitFor({ timeout: 120000 });
  await wait(2500);

  await page.screenshot({
    path: path.join(OUTPUT_DIR, "01-dashboard-overview.png"),
    fullPage: true,
  });

  await page.getByRole("tab", { name: "RAG" }).click();
  await page.getByText("Interroga il dataset attivo").waitFor({ timeout: 30000 });
  await wait(1500);

  const input = page.getByPlaceholder("Fai una domanda sul dataset attivo");
  await input.fill("Quanto ha venduto Focus a dicembre?");
  await input.press("Enter");

  await page.getByText("Fonte e anteprima CSV").waitFor({ timeout: 180000 });
  await wait(2000);

  await page.screenshot({
    path: path.join(OUTPUT_DIR, "02-rag-question-and-answer.png"),
    fullPage: true,
  });

  await page.getByText("Fonte e anteprima CSV").click();
  await wait(1200);

  await page.screenshot({
    path: path.join(OUTPUT_DIR, "03-source-reference-expanded.png"),
    fullPage: true,
  });

  await page.getByRole("tab", { name: "Monitoring" }).click();
  await page.getByText("Monitoring locale").waitFor({ timeout: 30000 });
  await wait(1500);

  await page.screenshot({
    path: path.join(OUTPUT_DIR, "04-monitoring-tab.png"),
    fullPage: true,
  });

  await browser.close();
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
