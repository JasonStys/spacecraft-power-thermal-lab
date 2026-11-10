/** Jason Stys — actual extracted load-service review and independent interval-energy oracle.
 * Functions: owned journey; variables: heater shortfall, component Wh and exact JSON export.
 * Source lines: docs/CODE_INDEX.md. Synthetic educational power model, no spacecraft control.
 */
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { expect } from "@playwright/test";
import { runNativeJourney } from "./native_browser.mjs";

await runNativeJourney(async ({ page, request, outputDirectory }) => {
  await expect(page.locator("#evidence")).toBeVisible();
  await page.locator("#scenario").selectOption("heater-contention");
  await expect(page.locator("#state")).toContainText("Heater requested · 3.20 W actually served");
  const run = await (await request.get("api/run?scenario=heater-contention")).json();
  const heater = run.service.components.find((row) => row.name === "heater");
  assert.ok(Math.abs(heater.requested_wh - (6 * 600) / 3600) < 1e-8);
  assert.ok(Math.abs(heater.unserved_wh - ((6 - 3.2) * 600) / 3600) < 1e-8);
  assert.deepEqual(
    [
      heater.interruptions[0].start_s,
      heater.interruptions[0].end_s,
      heater.interruptions[0].right_censored,
    ],
    [0, 600, true],
  );
  const deficit = run.service.components.reduce((sum, row) => sum + row.unserved_wh, 0);
  assert.ok(Math.abs(deficit - run.totals.unserved_wh) < 1e-8);
  assert.deepEqual(run.service.science_shedding, []);
  await page.locator("#service-review summary").nth(1).click();
  await expect(page.locator("#service-review details").nth(1)).toContainText("unserved");
  const pending = page.waitForEvent("download");
  await page.getByRole("link", { name: "JSON report ↓", exact: true }).click();
  const download = await pending;
  const file = path.join(outputDirectory, "native-load-service.json");
  await download.saveAs(file);
  assert.deepEqual(JSON.parse(await readFile(file, "utf8")), run);
  await page.locator("#scenario").selectOption("extended-eclipse");
  await expect(page.locator("#status")).toContainText("Verified");
  await page.locator("#policy").selectOption("1");
  const response = await request.get("api/run?scenario=extended-eclipse&policy=1");
  const reserve = await response.json();
  assert.ok(reserve.service.science_shedding.length > 0);
  assert.ok(reserve.totals.science_shed_wh > 0);
  await expect(page.locator("#service-review")).toContainText("Intentional science shedding");
  assert.equal((await request.get("api/run?heater=99")).status(), 400);
});
