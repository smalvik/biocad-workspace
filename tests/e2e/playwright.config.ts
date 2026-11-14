import { defineConfig, devices } from "@playwright/test";

// BASE_URL: http://web inside compose, http://localhost:8080 from host,
// Deployment URLs are configured explicitly after WB-09.
export default defineConfig({
  testDir: "./specs",
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ["list"],
    ["html", { open: "never", outputFolder: "playwright-report" }],
    ["allure-playwright", { resultsDir: "allure-results" }],
  ],
  use: {
    baseURL: process.env.BASE_URL ?? "http://localhost:8080",
    locale: "ru-RU",
    timezoneId: "Europe/Moscow",
    // Authenticated flows must not store session cookies/CSRF in network traces.
    trace: "off",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "desktop", use: { ...devices["Desktop Chrome"] } },
    { name: "mobile", use: { ...devices["Pixel 7"] }, grep: /@mobile/ },
  ],
});
