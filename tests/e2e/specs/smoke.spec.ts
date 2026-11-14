import { expect, test, type Page } from "@playwright/test";
import * as allure from "allure-js-commons";

test.beforeEach(async () => {
  await allure.suite(process.env.RUN_TYPE ?? "smoke");
  for (const [name, value] of Object.entries({
    run_type: process.env.RUN_TYPE ?? "smoke",
    environment: process.env.REPORT_ENV ?? process.env.APP_ENV ?? "local",
    git_sha: process.env.GIT_SHA ?? "dev",
    working_tree: process.env.WORKING_TREE ?? "unknown",
    release_version: process.env.RELEASE_VERSION ?? "unreleased",
  })) await allure.label(name, value);
});

async function login(page: Page, ready = true) {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Войти в Workspace" })).toBeVisible();
  await page.getByLabel("Пароль", { exact: true }).fill("demo-workspace");
  await page.getByRole("button", { name: "Войти", exact: true }).click();
  if (ready) await expect(page.getByTestId("space-D-03")).toBeVisible();
}

test("login, keyboard selection and real map @smoke @mobile", async ({ page }, info) => {
  await login(page);
  await expect(page.locator("g[data-resource]")).toHaveCount(27);
  await expect(page.getByRole("list", { name: "Легенда статусов" })).toBeVisible();
  await page.getByTestId("space-D-03").focus();
  await page.getByTestId("space-D-03").press("Enter");
  await expect(page.getByRole("heading", { name: "FreeDesk D-03" })).toBeVisible();
  await expect(page.getByTestId("space-D-03")).toHaveAttribute("aria-pressed", "true");
  await page.screenshot({ path: info.outputPath(`office-map-${info.project.name}.png`), fullPage: true });
  await page.getByRole("button", { name: "Закрыть карточку места" }).click();
});

test("calendar follows actual D-03 windows and shows both bookings @smoke @mobile", async ({ page }) => {
  await login(page);
  const desk = page.getByTestId("space-D-03");
  await expect(desk).toHaveAttribute("data-status", "booked");
  await page.getByRole("button", { name: "12:00–14:00", exact: true }).click();
  await expect(desk).toHaveAttribute("data-status", "free");
  await page.getByRole("button", { name: "14:00–16:00", exact: true }).click();
  await expect(desk).toHaveAttribute("data-status", "booked");
  await page.getByRole("button", { name: "09:00–17:00", exact: true }).click();
  await expect(desk).toHaveAttribute("aria-label", /2 брони/);
  await desk.click();
  const details = page.getByRole("dialog").or(page.getByRole("complementary", { name: "Детали места" }));
  await expect(details.getByRole("heading", { name: "2 брони в этом интервале" })).toBeVisible();
  await expect(details.getByText("10:00–12:00 МСК", { exact: true })).toBeVisible();
  await expect(details.getByText("14:00–16:00 МСК", { exact: true })).toBeVisible();
});

test("floor switch loads the second API plan @smoke @mobile", async ({ page }) => {
  await login(page);
  await page.getByLabel("Этаж", { exact: true }).selectOption("floor-3");
  await expect(page.getByTestId("space-D-31")).toBeVisible();
  await expect(page.locator("g[data-resource]")).toHaveCount(14);
  await expect(page.getByTestId("space-D-03")).toHaveCount(0);
  await page.getByLabel("Этаж", { exact: true }).selectOption("floor-2");
  await expect(page.getByTestId("space-D-07")).toHaveAttribute("data-status", "dedicated");
  await expect(page.locator("g[data-resource]")).toHaveCount(27);
});

test("type and availability filters have an honest empty state @smoke @mobile", async ({ page }) => {
  await login(page);
  await page.getByLabel("FreeDesk", { exact: true }).uncheck();
  await expect(page.getByTestId("space-D-03")).toHaveCount(0);
  await expect(page.getByTestId("space-D-07")).toBeVisible();
  await page.getByLabel("Постоянные места", { exact: true }).uncheck();
  await page.getByLabel("Переговорные", { exact: true }).uncheck();
  await expect(page.getByRole("heading", { name: "Нет мест по выбранным фильтрам" })).toBeVisible();
  await page.getByRole("button", { name: "Сбросить фильтры" }).click();
  await expect(page.getByTestId("space-D-03")).toBeVisible();
  await page.getByLabel("Только свободные", { exact: true }).check();
  await expect(page.getByTestId("space-D-03")).toHaveCount(0);
  await expect(page.getByTestId("space-D-02")).toHaveAttribute("data-status", "free");
});

test("date changes availability and invalid intervals hide old data @smoke @mobile", async ({ page }) => {
  await login(page);
  await page.getByLabel("Дата", { exact: true }).fill("2026-11-17");
  await expect(page.getByTestId("space-D-03")).toHaveAttribute("data-status", "free");
  await page.getByLabel("Окончание", { exact: true }).fill("09:00");
  await expect(page.getByRole("alert")).toContainText("окончание должно быть позже начала");
  await expect(page.locator("g[data-resource]")).toHaveCount(0);
});

test("map API failure hides availability and can be retried @smoke @mobile", async ({ page }) => {
  let fail = true;
  await page.route("**/api/v1/spaces?**", route => {
    if (fail) { fail = false; return route.fulfill({ status: 503, json: { error: { message: "Сервис временно недоступен" } } }); }
    return route.continue();
  });
  await login(page, false);
  await expect(page.getByRole("heading", { name: "Не удалось загрузить план" })).toBeVisible();
  await expect(page.locator("g[data-resource]")).toHaveCount(0);
  await page.getByRole("button", { name: "Повторить загрузку" }).click();
  await expect(page.getByTestId("space-D-03")).toBeVisible();
});

test("a delayed old period never replaces the selected period @regression @mobile", async ({ page }) => {
  let release!: () => void, finish!: () => void;
  const held = new Promise<void>(resolve => { release = resolve; });
  const finished = new Promise<void>(resolve => { finish = resolve; });
  let delayed = false;
  await page.route("**/api/v1/spaces?**", async route => {
    const start = new URL(route.request().url()).searchParams.get("from") ?? "";
    if (!delayed && start.includes("T10:00")) {
      delayed = true;
      try { const response = await route.fetch(); await held; await route.fulfill({ response }); }
      catch { /* The application intentionally aborts superseded requests. */ }
      finally { finish(); }
    } else await route.continue();
  });
  try {
    await login(page, false);
    await expect.poll(() => delayed).toBe(true);
    await page.getByRole("button", { name: "12:00–14:00", exact: true }).click();
    await expect(page.getByTestId("space-D-03")).toHaveAttribute("data-status", "free");
  } finally { release(); }
  await finished;
  await expect(page.getByTestId("space-D-03")).toHaveAttribute("data-status", "free");
});

test("session expiry returns to login with an explanation @smoke @mobile", async ({ page }) => {
  await login(page);
  await page.route("**/api/v1/spaces?**", route => route.fulfill({ status: 401, json: { error: { message: "Сессия завершена" } } }));
  await page.getByRole("button", { name: "14:00–16:00", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Войти в Workspace" })).toBeVisible();
  await expect(page.getByRole("status")).toContainText("Сессия завершена");
});

test("logout revokes the browser session @smoke @mobile", async ({ page }) => {
  await login(page);
  await page.getByRole("button", { name: "Выйти", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Войти в Workspace" })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { name: "Войти в Workspace" })).toBeVisible();
});

test("assistant outage leaves the real map usable @smoke @mobile", async ({ page }) => {
  await page.route("**/api/v1/assistant/**", route => route.abort("failed"));
  await login(page);
  const assistantReachable = await page.evaluate(() => fetch("/api/v1/assistant/healthz").then(response => response.ok).catch(() => false));
  expect(assistantReachable).toBe(false);
  await page.getByRole("button", { name: "12:00–14:00", exact: true }).click();
  await expect(page.getByTestId("space-D-03")).toHaveAttribute("data-status", "free");
});

test("zoom, pointer pan and fit change the interactive SVG @smoke", async ({ page }) => {
  await login(page);
  await page.getByRole("button", { name: "Увеличить масштаб" }).click();
  await expect(page.getByTestId("map-viewport")).toHaveAttribute("data-scale", "1.25");
  const transform = page.getByTestId("map-transform"), before = await transform.getAttribute("transform");
  const box = await page.getByTestId("map-viewport").boundingBox();
  expect(box).not.toBeNull();
  await page.mouse.move(box!.x + 30, box!.y + box!.height - 35);
  await page.mouse.down(); await page.mouse.move(box!.x + 100, box!.y + box!.height - 65, { steps: 5 }); await page.mouse.up();
  await expect(transform).not.toHaveAttribute("transform", before!);
  await page.getByRole("button", { name: "Показать весь этаж" }).click();
  await expect(transform).toHaveAttribute("transform", "translate(0 0) scale(1)");
  const svg = page.getByRole("group", { name: "Интерактивный план этажа" });
  await svg.focus(); await svg.press("ArrowRight");
  await expect(transform).not.toHaveAttribute("transform", "translate(0 0) scale(1)");
  await svg.press("Home");
  await expect(transform).toHaveAttribute("transform", "translate(0 0) scale(1)");
});

test("swagger and readiness remain routed @smoke", async ({ request }) => {
  expect((await request.get("/api/openapi.json")).ok()).toBeTruthy();
  expect((await request.get("/api/v1/assistant/openapi.json")).ok()).toBeTruthy();
  const ready = await request.get("/api/v1/readyz");
  expect(ready.status()).toBe(200);
  expect((await ready.json()).checks.postgres).toBe(true);
});
