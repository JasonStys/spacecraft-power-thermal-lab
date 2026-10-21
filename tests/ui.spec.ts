/** Actual native/service/browser acceptance by Jason Stys; test/variable lines: docs/CODE_INDEX.md.
 * Normal tests require the real compiled C++ worker; only explicit error/hostile-response tests mock HTTP.
 */
import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("actual numerical evidence and interval replay", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  await expect(page.locator("#status")).toContainText("C++ and Python samples agree");
  await expect(page.locator("#time-label")).toHaveText("5 s (Δ 5 s)");
  await page.getByRole("button", { name: "Jump to end" }).click();
  await expect(page.locator("#time-label")).toContainText("1500 s");
  await page.getByRole("button", { name: "Previous interval", exact: true }).click();
  await expect(page.locator("#time-label")).toContainText("1495 s");
  await page.getByLabel("Display °C").check();
  await expect(page.getByLabel("Display °C")).toBeFocused();
  await expect(page.locator("#state")).toContainText("°C");
});
test("reserve-aware policy quantifies science sacrificed", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  await page.locator("#scenario").selectOption("extended-eclipse");
  await expect(page.locator("#status")).toContainText("Verified");
  await page.getByRole("button", { name: "Pin current result" }).click();
  await page.locator("#policy").selectOption("1");
  await expect(page.locator("#status")).toContainText("Verified");
  await expect(page.locator("#comparison")).toContainText("always requested");
  await expect(page.locator("#comparison")).toContainText("reserve-aware");
  await expect(page.locator("#comparison")).toContainText("Served science / Wh");
});
test("heater request is distinguished from actual power", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  await page.locator("#scenario").selectOption("heater-contention");
  await expect(page.locator("#status")).toContainText("Verified");
  await expect(page.locator("#state")).toContainText("Heater requested · 3.20 W actually served");
  await expect(
    page.locator("#allocation").getByRole("row").filter({ hasText: "Heater served" }),
  ).toContainText("3.2000");
  await page.locator("#heater").selectOption("0");
  await expect(page.locator("#status")).toContainText("Verified");
  await expect(page.locator("#state")).toContainText("Heater not requested");
});
test("all download formats preserve finite evidence and units", async ({ page, request }) => {
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  for (const name of ["JSON report ↓", "CSV report ↓", "HTML report ↓", "Input JSON ↓"]) {
    const href = await page.getByRole("link", { name, exact: true }).getAttribute("href");
    const response = await request.get(href!);
    expect(response.status()).toBe(200);
    expect(response.headers()["content-disposition"]).toContain("attachment");
    if (name.startsWith("JSON")) expect((await response.json()).samples.length).toBe(300);
    if (name.startsWith("CSV")) expect(await response.text()).toContain("temperature_k");
    if (name.startsWith("HTML")) expect(await response.text()).not.toContain("<script");
    if (name.startsWith("Input")) expect((await response.json()).config.battery_wh).toBe(40);
  }
});
test("preferences are opt-in and remove cleanly", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  expect(
    await page.evaluate(() => localStorage.getItem("power-thermal-preferences-v1")),
  ).toBeNull();
  await page.locator("#scenario").selectOption("hot-soak");
  await expect(page.locator("#status")).toContainText("Verified");
  await page.getByLabel("Remember these controls on this device").check();
  await page.reload();
  await expect(page.locator("#scenario")).toHaveValue("hot-soak");
  await expect(page.locator("#evidence")).toBeVisible();
  await page.getByLabel("Remember these controls on this device").uncheck();
  expect(
    await page.evaluate(() => localStorage.getItem("power-thermal-preferences-v1")),
  ).toBeNull();
});
test("failure hides stale results and retries without fabrication", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  await page.route("**/api/run?**", (r) => r.fulfill({ status: 500, body: "unavailable" }));
  await page.getByRole("button", { name: "Run experiment ↗" }).click();
  await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();
  await expect(page.locator("#evidence")).toBeHidden();
  await page.unroute("**/api/run?**");
  await page.getByRole("button", { name: "Try again" }).click();
  await expect(page.locator("#evidence")).toBeVisible();
  await page.route("**/api/run?**", (r) =>
    r.fulfill({ status: 200, contentType: "application/json", body: '{"schema":1}' }),
  );
  await page.getByRole("button", { name: "Run experiment ↗" }).click();
  await expect(page.getByRole("button", { name: "Try again" })).toBeVisible();
});
test("hostile returned labels are inert", async ({ page }) => {
  await page.route("**/api/run?**", async (route) => {
    const response = await route.fetch();
    const body = await response.json();
    body.provenance.source = '<img src=x onerror="alert(1)">';
    body.name = "<script>alert(1)</script>";
    await route.fulfill({ response, json: body });
  });
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  await expect(page.locator("#evidence")).toContainText("<img src=x");
  await page.getByRole("button", { name: "Pin current result" }).click();
  await expect(page.locator("#comparison")).toContainText("<script>");
  await expect(page.locator("#evidence img,#evidence script")).toHaveCount(0);
});
test("mobile layout keyboard and accessibility", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await expect(page.locator("#evidence")).toBeVisible();
  const size = await page.evaluate(() => ({
    width: innerWidth,
    scroll: document.documentElement.scrollWidth,
  }));
  expect(size.scroll).toBeLessThanOrEqual(size.width + 1);
  const region = page.getByRole("region", {
    name: "Selected interval power allocation",
    exact: true,
  });
  await region.focus();
  await expect(region).toBeFocused();
  expect(
    (await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze())
      .violations,
  ).toEqual([]);
});
