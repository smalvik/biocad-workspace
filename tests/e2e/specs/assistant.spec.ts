import {
  expect,
  test as base,
  type Page,
  type TestInfo,
} from "@playwright/test";
import * as allure from "allure-js-commons";

const test = base.extend<{ created: string[] }>({
  created: async ({ page }, use) => {
    const ids: string[] = [];
    await use(ids);
    if (!ids.length) return;
    const login = await page.request.post("/api/v1/auth/login", {
      data: { username: "e01", password: "demo-workspace" },
    });
    expect(login.status()).toBe(200);
    const csrf = (await login.json()).csrf_token;
    for (const id of ids)
      expect(
        (
          await page.request.post(`/api/v1/bookings/${id}/cancel`, {
            headers: { "X-CSRF-Token": csrf },
          })
        ).status(),
      ).toBe(200);
  },
});
test.beforeEach(async ({ baseURL }) => {
  test.skip(
    !["web", "localhost", "127.0.0.1"].includes(new URL(baseURL!).hostname),
    "AI mutation checks require isolated infrastructure",
  );
  await allure.suite(process.env.RUN_TYPE ?? "smoke");
  await allure.feature(
    "Real MCP/RabbitMQ/PostgreSQL with scripted HTTP LLM fixture",
  );
  for (const [key, value] of Object.entries({
    run_type: process.env.RUN_TYPE ?? "smoke",
    environment: process.env.REPORT_ENV ?? "local",
    git_sha: process.env.GIT_SHA ?? "dev",
    working_tree: process.env.WORKING_TREE ?? "unknown",
    release_version: process.env.RELEASE_VERSION ?? "unreleased",
  }))
    await allure.label(key, value);
});
async function login(page: Page, info: TestInfo) {
  await page.goto("/");
  await page.getByLabel("Пароль", { exact: true }).fill("demo-workspace");
  await page.getByRole("button", { name: "Войти", exact: true }).click();
  await expect(page.getByTestId("space-D-15")).toBeVisible();
  let hash = 0;
  for (const char of info.testId + info.project.name)
    hash = (Math.imul(hash, 31) + char.charCodeAt(0)) | 0;
  const date = new Date(Date.now() + (4000 + ((hash >>> 0) % 3650)) * 86400000)
    .toISOString()
    .slice(0, 10);
  await page.getByLabel("Дата", { exact: true }).fill(date);
  await expect(page.getByTestId("space-D-15")).toHaveAttribute(
    "data-status",
    "free",
  );
  return date;
}
const chat = (page: Page) =>
  page.getByRole("dialog", { name: "AI-ассистент", exact: true });
async function ask(page: Page, text: string) {
  await page.getByRole("button", { name: "AI-ассистент", exact: true }).click();
  await chat(page).getByLabel("Запрос ассистенту").fill(text);
  await expect(
    chat(page).getByRole("button", { name: "Отправить", exact: true }),
  ).toBeDisabled();
  await chat(page).getByRole("checkbox").check();
  const response = page.waitForResponse((r) =>
    r.url().endsWith("/api/v1/assistant/chat"),
  );
  await chat(page)
    .getByRole("button", { name: "Отправить", exact: true })
    .click();
  return await response;
}

test("@mobile AI proposes through MCP and books only after explicit exact-slot confirmation", async ({
  page,
  created,
}, info) => {
  test.setTimeout(75000);
  const date = await login(page, info);
  const writes: string[] = [];
  page.on("request", (req) => {
    if (
      req.method() === "POST" &&
      /\/api\/v1\/(?:bookings$|assistant\/confirm$)/.test(req.url())
    )
      writes.push(req.url());
  });
  const response = await ask(
    page,
    "Найди переговорную на 6 человек на выбранные дату и время",
  );
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data.scripted_test).toBe(true);
  await expect(chat(page).getByTestId("assistant-model-status")).toHaveAttribute("data-state", "primary");
  expect(data.tools_used).toEqual(["get_availability", "propose_booking"]);
  expect(writes).toEqual([]);
  await expect(chat(page)).toContainText("Бронь ещё не создана");
  await chat(page)
    .getByRole("button", { name: "Показать предложение на плане" })
    .click();
  const proposal = page.getByRole("region", { name: "Предложение AI" });
  await expect(proposal).toContainText(data.proposal.selection.space_id);
  await expect(page.getByLabel("Дата", { exact: true })).toHaveValue(date);
  await expect(
    page.getByTestId(`space-${data.proposal.selection.space_id}`),
  ).toHaveAttribute("aria-pressed", "true");
  await info.attach(`AI proposal on map — ${info.project.name}`, {
    body: await page.screenshot({ fullPage: true }),
    contentType: "image/png",
  });
  await proposal
    .getByRole("button", { name: "Проверить предложение AI" })
    .click();
  const confirmation = page.getByRole("dialog", {
    name: "Подтверждение бронирования",
    exact: true,
  });
  await expect(confirmation).toContainText(data.proposal.selection.space_id);
  expect(writes).toEqual([]);
  const confirmed = page.waitForResponse((r) =>
    r.url().endsWith("/api/v1/assistant/confirm"),
  );
  await confirmation
    .getByRole("button", { name: "Подтвердить бронирование", exact: true })
    .click();
  const result = await confirmed;
  expect(result.status()).toBe(200);
  const booking = await result.json();
  created.push(booking.id);
  expect(booking.space_id).toBe(data.proposal.selection.space_id);
  expect(Date.parse(booking.start_at)).toBe(
    Date.parse(data.proposal.selection.start_at),
  );
  expect(Date.parse(booking.end_at)).toBe(
    Date.parse(data.proposal.selection.end_at),
  );
  expect(writes).toHaveLength(1);
  await expect(
    page.getByRole("dialog", { name: "Результат бронирования" }),
  ).toContainText("Бронь подтверждена");
});

test("@mobile provider outage leaves the manual booking flow usable", async ({
  page,
  created,
}, info) => {
  await login(page, info);
  const response = await ask(page, "сбой AI");
  expect(response.status()).toBe(503);
  await expect(chat(page).getByTestId("assistant-model-status")).toHaveAttribute("data-state", "unavailable");
  await expect(chat(page).getByRole("alert")).toContainText(
    "AI сейчас недоступен",
  );
  await chat(page).getByRole("button", { name: "Вернуться к плану" }).click();
  await page.getByTestId("space-D-15").click();
  await page.getByRole("button", { name: "Продолжить", exact: true }).click();
  const reply = page.waitForResponse(
    (r) =>
      r.url().endsWith("/api/v1/bookings") && r.request().method() === "POST",
  );
  await page
    .getByRole("dialog", { name: "Подтверждение бронирования" })
    .getByRole("button", { name: "Подтвердить бронирование", exact: true })
    .click();
  const result = await reply;
  expect(result.status()).toBe(201);
  created.push((await result.json()).id);
  await expect(
    page.getByRole("dialog", { name: "Результат бронирования" }),
  ).toContainText("Бронь подтверждена");
});

test("@mobile primary outage uses free fallback and only proposes until explicit confirmation", async ({ page }, info) => {
  await login(page, info);
  const response = await ask(page, "резерв AI: найди FreeDesk на выбранное время");
  expect(response.status()).toBe(200);
  const data = await response.json();
  expect(data.routing).toEqual({ state: "fallback", model: "test/fallback" });
  expect(data.provider_calls.every((call: { cost: number }) => call.cost === 0)).toBe(true);
  const status = chat(page).getByTestId("assistant-model-status");
  await expect(status).toHaveAttribute("data-state", "fallback");
  await expect(status).toContainText("Резервная модель; ответы могут содержать ошибки");
  await expect(chat(page)).toContainText("Бронь ещё не создана");
  await chat(page).getByRole("button", { name: "Вернуться к плану" }).click();
  await expect(page.getByTestId(`space-${data.proposal.selection.space_id}`)).toHaveAttribute("data-status", "free");
});

test("@mobile clarification creates no proposal and closing a pending chat ignores its late reply", async ({
  page,
}, info) => {
  await login(page, info);
  expect((await ask(page, "уточни")).status()).toBe(200);
  await expect(chat(page)).toContainText("Уточните, пожалуйста");
  await expect(
    chat(page).getByRole("button", { name: "Показать предложение на плане" }),
  ).toHaveCount(0);
  await chat(page).getByRole("button", { name: "Вернуться к плану" }).click();
  let release!: () => void;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route("**/api/v1/assistant/chat", async (route) => {
    await held;
    await route.abort().catch(() => {});
  });
  await page.getByRole("button", { name: "AI-ассистент", exact: true }).click();
  await chat(page).getByRole("checkbox").check();
  await chat(page).getByLabel("Запрос ассистенту").fill("Найди FreeDesk");
  await chat(page)
    .getByRole("button", { name: "Отправить", exact: true })
    .click();
  await expect(chat(page)).toContainText("Проверяем доступность");
  await chat(page).getByRole("button", { name: "Вернуться к плану" }).click();
  release();
  await expect(chat(page)).toHaveCount(0);
  await expect(
    page.getByRole("region", { name: "Предложение AI" }),
  ).toHaveCount(0);
  await page.getByTestId("space-D-15").click();
  await expect(
    page.getByRole("button", { name: "Продолжить", exact: true }),
  ).toBeEnabled();
});
