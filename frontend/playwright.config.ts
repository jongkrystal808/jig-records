import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/visual",
  fullyParallel: true,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: "line",
  expect: {
    toHaveScreenshot: {
      animations: "disabled",
      caret: "hide",
      maxDiffPixelRatio: 0.005
    }
  },
  use: {
    ...devices["Desktop Chrome"],
    baseURL: "http://127.0.0.1:5173",
    colorScheme: "light",
    locale: "zh-TW",
    reducedMotion: "reduce",
    trace: "retain-on-failure"
  },
  projects: [
    { name: "tablet-1024", use: { viewport: { width: 1024, height: 900 } } },
    { name: "notebook-1366", use: { viewport: { width: 1366, height: 900 } } },
    { name: "desktop-1920", use: { viewport: { width: 1920, height: 1080 } } }
  ],
  webServer: {
    command: "npm run dev",
    url: "http://127.0.0.1:5173",
    reuseExistingServer: !process.env.CI,
    timeout: 120_000
  }
});
