import { test, expect } from "@playwright/test";
import { readFileSync } from "node:fs";

test.beforeEach(async ({ page }) => {
  // Fuentes externas bloqueadas: la página debe funcionar sin red (fallback silencioso).
  await page.route(/fonts\.(googleapis|gstatic)\.com/, r => r.abort());
});

test("muestra el rótulo de simulación persistente", async ({ page }) => {
  await page.goto("/");
  const banner = page.locator(".sim-banner");
  await expect(banner).toContainText("Simulación");
  await expect(banner).toContainText("no es telemetría real");
  await page.mouse.wheel(0, 2000);
  await expect(banner).toBeInViewport();
});

test("no tiene errores de consola ni scroll horizontal", async ({ page }) => {
  const errors = [];
  page.on("pageerror", e => errors.push(e.message));
  page.on("console", m => { if (m.type() === "error" && !/fonts\.(googleapis|gstatic)\.com/.test(m.location().url)) errors.push(m.text()); });
  await page.goto("/");
  await page.waitForTimeout(2500);
  expect(errors).toEqual([]);
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - innerWidth);
  expect(overflow).toBeLessThanOrEqual(0);
});

test("genera lecturas y actualiza dashboard, gauge y consola", async ({ page }) => {
  await page.goto("/");
  await page.locator("#sInt").fill("0.5");
  await expect(page.locator("#bufMeta")).not.toHaveText("30 lecturas", { timeout: 5000 });
  await expect(page.locator("#gNum")).toHaveText(/^-?\d+\.\d$/);
  await expect(page.locator("#tMax")).toContainText("°C");
  await expect(page.locator("#logE")).toContainText("PUBLISH");
  await page.locator("#tabI").click();
  await expect(page.locator("#logI")).toBeVisible();
  await expect(page.locator("#logI")).toContainText("temperature=");
});

test("QoS 2 produce el handshake PUBREC/PUBREL/PUBCOMP", async ({ page }) => {
  await page.goto("/");
  await page.locator("#sInt").fill("0.5");
  await page.locator('.seg button[data-qos="2"]').click();
  await expect(page.locator("#qosHelp")).toContainText("exactamente una vez");
  await expect(page.locator("#logE")).toContainText("PUBCOMP", { timeout: 5000 });
});

test("pausar detiene la generación y reanudar la continúa", async ({ page }) => {
  await page.goto("/");
  await page.locator("#sInt").fill("0.5");
  await page.locator("#bPause").click();
  await expect(page.locator("#runLabel")).toHaveText("En pausa");
  const before = await page.locator("#bufMeta").textContent();
  await page.waitForTimeout(1500);
  await expect(page.locator("#bufMeta")).toHaveText(before);
  await page.locator("#bPause").click();
  await expect(page.locator("#bufMeta")).not.toHaveText(before, { timeout: 5000 });
});

test("el pico térmico lleva el estado a crítico", async ({ page }) => {
  await page.goto("/");
  await page.locator("#sBase").fill("30");
  await page.locator("#sInt").fill("0.5");
  await page.locator("#bSpike").click();
  await expect(page.locator("#status")).toHaveClass(/crit/, { timeout: 5000 });
  await expect(page.locator("#logE")).toContainText("pico térmico");
});

test("exporta CSV y JSON marcados como simulados", async ({ page }) => {
  await page.goto("/");
  const [csv] = await Promise.all([page.waitForEvent("download"), page.locator("#bCsv").click()]);
  expect(csv.suggestedFilename()).toMatch(/^lecturas-simuladas-.*\.csv$/);
  const csvText = readFileSync(await csv.path(), "utf8").trim().split("\n");
  expect(csvText[0]).toBe("timestamp_iso,temperature_c,humidity_pct,qos,msg_id,spike,origen");
  expect(csvText.length).toBeGreaterThanOrEqual(30);
  expect(csvText[1].endsWith(",simulado")).toBe(true);

  const [json] = await Promise.all([page.waitForEvent("download"), page.locator("#bJson").click()]);
  const data = JSON.parse(readFileSync(await json.path(), "utf8"));
  expect(data.aviso).toMatch(/sintéticos/);
  expect(data.lecturas.length).toBeGreaterThanOrEqual(30);
  expect(data.lecturas[0]).toHaveProperty("temperature");
});
