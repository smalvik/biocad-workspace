import { expect, test } from "@playwright/test";
import * as allure from "allure-js-commons";

test.beforeEach(async () => {
  await allure.suite(process.env.RUN_TYPE ?? "smoke");
  for (const [name, value] of Object.entries({
    run_type: process.env.RUN_TYPE ?? "smoke",
    environment: process.env.APP_ENV ?? "local",
    git_sha: process.env.GIT_SHA ?? "dev",
    working_tree: process.env.WORKING_TREE ?? "unknown",
    release_version: process.env.RELEASE_VERSION ?? "unreleased",
  })) await allure.label(name, value);
});

test.describe("@smoke stack", () => {
  test("web loads and both backends are reachable through the proxy @smoke @mobile", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("BIOCAD Workspace")).toBeVisible();
    await expect(page.getByTestId("booking-status")).toContainText("ok");
    await expect(page.getByTestId("assistant-status")).toContainText("ok");
  });

  test("assistant failure leaves the page and booking service available @smoke @mobile", async ({ page }) => {
    await page.route("**/api/v1/assistant/healthz", route => route.fulfill({ status: 503 }));
    await page.goto("/");
    await expect(page.getByTestId("assistant-status")).toContainText("down");
    await expect(page.getByTestId("booking-status")).toContainText("ok");
    await expect(page.getByRole("heading", { name: "Каркас приложения" })).toBeVisible();
  });

  test("swagger UIs are routed @smoke", async ({ request }) => {
    const booking = await request.get("/api/openapi.json");
    expect(booking.ok()).toBeTruthy();
    const assistant = await request.get("/api/v1/assistant/openapi.json");
    expect(assistant.ok()).toBeTruthy();
    const ready = await request.get("/api/v1/readyz");
    expect(ready.status()).toBe(200);
    expect((await ready.json()).checks.postgres).toBe(true);
  });
});
