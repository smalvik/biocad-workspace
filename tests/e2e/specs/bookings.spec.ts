import {
  expect,
  test as base,
  request,
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
    expect(login.ok()).toBe(true);
    const csrf = (await login.json()).csrf_token;
    for (const id of new Set(ids))
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
    "Booking mutation tests require local/isolated infrastructure",
  );
  await allure.suite(process.env.RUN_TYPE ?? "smoke");
  for (const [key, value] of Object.entries({
    run_type: process.env.RUN_TYPE ?? "smoke",
    environment: process.env.REPORT_ENV ?? "local",
    git_sha: process.env.GIT_SHA ?? "dev",
    release_version: process.env.RELEASE_VERSION ?? "unreleased",
    working_tree: process.env.WORKING_TREE ?? "unknown",
  }))
    await allure.label(key, value);
});

async function login(page: Page) {
  await page.goto("/");
  await page.getByLabel("Пароль", { exact: true }).fill("demo-workspace");
  await page.getByRole("button", { name: "Войти", exact: true }).click();
  await expect(page.getByTestId("space-D-15")).toBeVisible();
}
function futureDate(info: TestInfo) {
  let hash = 0;
  for (const char of info.testId + info.project.name)
    hash = (Math.imul(hash, 31) + char.charCodeAt(0)) | 0;
  return new Date(Date.now() + (40 + ((hash >>> 0) % 3650)) * 86_400_000)
    .toISOString()
    .slice(0, 10);
}
async function choose(page: Page, info: TestInfo, resource = "D-15") {
  const date = futureDate(info);
  await page.getByLabel("Дата", { exact: true }).fill(date);
  await expect(page.getByTestId(`space-${resource}`)).toHaveAttribute(
    "data-status",
    "free",
  );
  await page.getByTestId(`space-${resource}`).click();
  await page.getByRole("button", { name: "Продолжить", exact: true }).click();
  return {
    space_id: resource,
    start_at: `${date}T10:00:00+03:00`,
    end_at: `${date}T12:00:00+03:00`,
  };
}
const confirmation = (page: Page) =>
  page.getByRole("dialog", { name: "Подтверждение бронирования", exact: true });
async function create(page: Page, ids: string[]) {
  const reply = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/bookings") &&
      response.request().method() === "POST",
  );
  await confirmation(page)
    .getByRole("button", { name: "Подтвердить бронирование", exact: true })
    .click();
  const response = await reply;
  expect(response.status()).toBe(201);
  expect(response.request().headers()["idempotency-key"]).toBeTruthy();
  expect(response.request().headers()["x-csrf-token"]).toBeTruthy();
  const booking = await response.json();
  ids.push(booking.id);
  await expect(
    page.getByRole("dialog", { name: "Результат бронирования" }),
  ).toContainText("Бронь подтверждена");
  return booking;
}

for (const resource of ["D-15", "M-03"])
  test(`explicit ${resource} confirmation, own list and cancellation update the real map @smoke @mobile`, async ({
    page,
    created,
  }, info) => {
    await login(page);
    let writes = 0;
    page.on("request", (req) => {
      if (req.url().endsWith("/api/v1/bookings") && req.method() === "POST")
        writes++;
    });
    await choose(page, info, resource);
    await expect(confirmation(page)).toContainText(resource);
    await expect(confirmation(page)).toContainText("Москва, Корпус А");
    await expect(confirmation(page)).toContainText("Этаж 2");
    await expect(confirmation(page)).toContainText("10:00–12:00 МСК");
    expect(writes).toBe(0);
    await confirmation(page)
      .getByRole("button", { name: "Вернуться к выбору" })
      .click();
    expect(writes).toBe(0);
    await page.getByTestId(`space-${resource}`).click();
    await page.getByRole("button", { name: "Продолжить", exact: true }).click();
    const booking = await create(page, created);
    expect(writes).toBe(1);
    await page.getByRole("button", { name: "Готово", exact: true }).click();
    await expect(page.getByTestId(`space-${resource}`)).toHaveAttribute(
      "data-status",
      "mine",
    );
    await page
      .getByRole("button", { name: "Мои бронирования", exact: true })
      .click();
    const list = page.getByRole("dialog", {
      name: "Мои бронирования",
      exact: true,
    });
    const row = list.locator(`[data-booking-id="${booking.id}"]`);
    await expect(row).toContainText("Этаж 2");
    await row
      .getByRole("button", { name: `Отменить бронь ${resource}`, exact: true })
      .click();
    await page
      .getByRole("dialog", { name: "Отменить бронирование?", exact: true })
      .getByRole("button", { name: "Сохранить бронь", exact: true })
      .click();
    await expect(row).toContainText("Подтверждена");
    await row
      .getByRole("button", { name: `Отменить бронь ${resource}`, exact: true })
      .click();
    await page
      .getByRole("button", { name: "Подтвердить отмену", exact: true })
      .click();
    await expect(
      list.getByText("Бронь отменена", { exact: true }),
    ).toBeVisible();
    await list.getByRole("button", { name: "Отменённые", exact: true }).click();
    await expect(row).toContainText("Отменена");
    await expect(
      row.getByRole("button", { name: /Отменить бронь/ }),
    ).toHaveCount(0);
    await page.screenshot({
      path: info.outputPath(
        `booking-cancelled-${resource}-${info.project.name}.png`,
      ),
      fullPage: true,
    });
    await list
      .getByRole("button", { name: "Закрыть: Мои бронирования", exact: true })
      .click();
    await expect(page.getByTestId(`space-${resource}`)).toHaveAttribute(
      "data-status",
      "free",
    );
  });

test("lost committed response survives reload and replays the same confirmation @regression @mobile", async ({
  page,
  created,
}, info) => {
  await login(page);
  const body = await choose(page, info);
  const attempts: { key: string; body: unknown }[] = [];
  let lost = true;
  await page.route("**/api/v1/bookings", async (route) => {
    if (route.request().method() !== "POST") return route.continue();
    attempts.push({
      key: route.request().headers()["idempotency-key"],
      body: route.request().postDataJSON(),
    });
    const response = await route.fetch();
    const booking = await response.json();
    if (response.ok()) created.push(booking.id);
    if (lost) {
      lost = false;
      expect(response.status()).toBe(201);
      await route.abort("failed");
    } else {
      expect(response.status()).toBe(200);
      await route.fulfill({ response });
    }
  });
  await confirmation(page)
    .getByRole("button", { name: "Подтвердить бронирование", exact: true })
    .click();
  await expect(confirmation(page).getByRole("alert")).toContainText(
    "Нет соединения",
  );
  await page.reload();
  await page
    .getByRole("button", { name: "Проверить незавершённое подтверждение" })
    .click();
  await expect(confirmation(page)).toContainText(body.space_id);
  await confirmation(page)
    .getByRole("button", { name: "Повторить подтверждение", exact: true })
    .click();
  await expect(
    page.getByRole("dialog", { name: "Результат бронирования" }),
  ).toContainText("Бронь подтверждена");
  expect(attempts).toHaveLength(2);
  expect(attempts[1]).toEqual(attempts[0]);
  expect(new Set(created).size).toBe(1);
});

test("another employee wins the slot and the real 409 refreshes occupancy @regression @mobile", async ({
  page,
  baseURL,
}, info) => {
  await login(page);
  const body = await choose(page, info);
  const other = await request.newContext({ baseURL });
  const loginReply = await other.post("/api/v1/auth/login", {
    data: { username: "e02", password: "demo-workspace" },
  });
  const csrf = (await loginReply.json()).csrf_token;
  const winner = await other.post("/api/v1/bookings", {
    data: body,
    headers: { "X-CSRF-Token": csrf, "Idempotency-Key": crypto.randomUUID() },
  });
  expect(winner.status()).toBe(201);
  const id = (await winner.json()).id;
  try {
    await confirmation(page)
      .getByRole("button", { name: "Подтвердить бронирование", exact: true })
      .click();
    await expect(confirmation(page).getByRole("alert")).toContainText(
      "Ресурс уже занят",
    );
    await confirmation(page)
      .getByRole("button", { name: "Вернуться к выбору" })
      .click();
    await expect(page.getByTestId("space-D-15")).toHaveAttribute(
      "data-status",
      "booked",
    );
  } finally {
    expect(
      (
        await other.post(`/api/v1/bookings/${id}/cancel`, {
          headers: { "X-CSRF-Token": csrf },
        })
      ).status(),
    ).toBe(200);
    await other.dispose();
  }
});

test("pending confirmation disables repeat clicks and cannot be dismissed @regression @mobile", async ({
  page,
  created,
}, info) => {
  await login(page);
  await choose(page, info);
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  let writes = 0;
  await page.route("**/api/v1/bookings", async (route) => {
    writes++;
    await gate;
    const response = await route.fetch();
    if (response.ok()) created.push((await response.json()).id);
    await route.fulfill({ response });
  });
  await confirmation(page)
    .getByRole("button", { name: "Подтвердить бронирование", exact: true })
    .click();
  const button = confirmation(page).getByRole("button", {
    name: "Проверяем подтверждение…",
    exact: true,
  });
  await expect(button).toBeDisabled();
  await button.evaluate((element) => (element as HTMLButtonElement).click());
  await page.keyboard.press("Escape");
  await expect(confirmation(page)).toBeVisible();
  expect(writes).toBe(1);
  release();
  await expect(
    page.getByRole("dialog", { name: "Результат бронирования" }),
  ).toContainText("Бронь подтверждена");
});

test("lost cancellation response can be retried without recreating the booking @regression @mobile", async ({
  page,
  created,
}, info) => {
  await login(page);
  await choose(page, info);
  const booking = await create(page, created);
  await page
    .getByRole("button", { name: "Посмотреть мои брони", exact: true })
    .click();
  await page
    .locator(`[data-booking-id="${booking.id}"]`)
    .getByRole("button", { name: "Отменить бронь D-15", exact: true })
    .click();
  let lost = true,
    attempts = 0;
  await page.route(`**/api/v1/bookings/${booking.id}/cancel`, async (route) => {
    attempts++;
    const response = await route.fetch();
    expect(response.status()).toBe(200);
    if (lost) {
      lost = false;
      await route.abort("failed");
    } else await route.fulfill({ response });
  });
  await page
    .getByRole("button", { name: "Подтвердить отмену", exact: true })
    .click();
  const dialog = page.getByRole("dialog", {
    name: "Отменить бронирование?",
    exact: true,
  });
  await expect(dialog.getByRole("alert")).toContainText("Нет соединения");
  await dialog
    .getByRole("button", { name: "Подтвердить отмену", exact: true })
    .click();
  await expect(dialog).toHaveCount(0);
  const list = page.getByRole("dialog", {
    name: "Мои бронирования",
    exact: true,
  });
  await list.getByRole("button", { name: "Отменённые", exact: true }).click();
  await expect(list.locator(`[data-booking-id="${booking.id}"]`)).toContainText(
    "Отменена",
  );
  expect(attempts).toBe(2);
});

test("own bookings handle empty and service failure states without blocking the map @smoke @mobile", async ({
  page,
}) => {
  await login(page);
  let unavailable = true;
  await page.route("**/api/v1/bookings/me", (route) =>
    unavailable
      ? route.fulfill({
          status: 503,
          json: { error: { message: "Список временно недоступен" } },
        })
      : route.fulfill({ json: { items: [] } }),
  );
  await page
    .getByRole("button", { name: "Мои бронирования", exact: true })
    .click();
  const list = page.getByRole("dialog", {
    name: "Мои бронирования",
    exact: true,
  });
  await expect(list.getByRole("alert")).toContainText(
    "Список временно недоступен",
  );
  unavailable = false;
  await list
    .getByRole("button", { name: "Повторить загрузку броней", exact: true })
    .click();
  await expect(
    list.getByText("У вас пока нет активных броней", { exact: true }),
  ).toBeVisible();
  await list.getByRole("button", { name: "Отменённые", exact: true }).click();
  await expect(
    list.getByText("Отменённых броней пока нет", { exact: true }),
  ).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(list).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Мои бронирования", exact: true }),
  ).toBeFocused();
  await expect(page.getByTestId("space-D-15")).toBeVisible();
});

test("dedicated and past intervals cannot offer a writable form; server 422 stays visible @regression @mobile", async ({
  page,
}, info) => {
  await login(page);
  await page.getByTestId("space-D-07").click();
  await expect(
    page.getByRole("button", { name: "Продолжить", exact: true }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Закрыть карточку места" }).click();
  await page.getByLabel("Дата", { exact: true }).fill("2020-01-01");
  await page.getByTestId("space-D-15").click();
  await expect(
    page.getByRole("button", { name: "Продолжить", exact: true }),
  ).toBeDisabled();
  await page.getByRole("button", { name: "Закрыть карточку места" }).click();
  await choose(page, info);
  await page.route("**/api/v1/bookings", (route) =>
    route.fulfill({
      status: 422,
      json: {
        error: {
          code: "VALIDATION_ERROR",
          message: "Начало бронирования должно быть в будущем",
        },
      },
    }),
  );
  await confirmation(page)
    .getByRole("button", { name: "Подтвердить бронирование", exact: true })
    .click();
  await expect(confirmation(page).getByRole("alert")).toContainText(
    "Начало бронирования должно быть в будущем",
  );
  await expect(
    page.getByRole("dialog", { name: "Результат бронирования" }),
  ).toHaveCount(0);
});
