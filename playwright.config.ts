/** Three-engine real service/native acceptance by Jason Stys; variables: docs/CODE_INDEX.md.
 * POWER_BASE_URL optionally targets only the explicitly started owned downloaded application.
 */
import { defineConfig, devices } from "@playwright/test";
const python =
  process.env.PYTHON ?? (process.platform === "win32" ? ".venv/Scripts/python.exe" : "python");
const externalBaseURL = process.env.POWER_BASE_URL;
export default defineConfig({
  testDir: "tests",
  testMatch: "ui.spec.ts",
  workers: 1,
  retries: 0,
  timeout: 30000,
  reporter: "list",
  use: {
    baseURL: externalBaseURL ?? "http://127.0.0.1:8885",
    trace: "off",
    screenshot: "off",
    video: "off",
    reducedMotion: "reduce",
  },
  ...(externalBaseURL
    ? {}
    : {
        webServer: {
          command: `"${python}" -m powerlab serve --port 8885 --no-browser`,
          url: "http://127.0.0.1:8885/api/health",
          reuseExistingServer: false,
          timeout: 20000,
        },
      }),
  projects: [
    { name: "chromium", use: { ...devices["Desktop Chrome"] } },
    { name: "firefox", use: { ...devices["Desktop Firefox"] } },
    { name: "webkit", use: { ...devices["Desktop Safari"] } },
  ],
});
