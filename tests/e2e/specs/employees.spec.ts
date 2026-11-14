import { expect, test, type Page } from "@playwright/test";
import * as allure from "allure-js-commons";

test.beforeEach(async () => {
  await allure.suite(process.env.RUN_TYPE ?? "smoke");
  for (const [name, value] of Object.entries({
    run_type: process.env.RUN_TYPE ?? "smoke",
    environment: process.env.REPORT_ENV ?? "local",
    git_sha: process.env.GIT_SHA ?? "dev",
    release_version: process.env.RELEASE_VERSION ?? "unreleased",
    working_tree: process.env.WORKING_TREE ?? "unknown",
  }))
    await allure.label(name, value);
});

async function login(page: Page) {
  await page.goto("/");
  await page.getByLabel("Пароль", { exact: true }).fill("demo-workspace");
  await page.getByRole("button", { name: "Войти", exact: true }).click();
  await expect(page.getByTestId("space-D-03")).toBeVisible();
}

function details(page: Page) {
  return page
    .getByRole("dialog")
    .or(page.getByRole("complementary", { name: /Детали (места|сотрудника)/ }));
}

async function search(page: Page, query: string) {
  const toggle = page.getByRole("button", { name: "Найти сотрудника" });
  if ((await toggle.getAttribute("aria-expanded")) !== "true")
    await toggle.click();
  await page
    .getByRole("searchbox", { name: "ФИО или отдел сотрудника" })
    .fill(query);
}

test("avatar changes follow four exact windows and the complete timeline @smoke @mobile", async ({
  page,
}, info) => {
  await login(page);
  const desk = page.getByTestId("space-D-03");
  await expect(desk).toHaveAttribute("aria-label", /Мария Соколова/);
  await expect(desk.locator('[data-person-id="e03"]')).toHaveCount(1);
  await desk.click();
  await expect(
    details(page).getByText("Мария Соколова", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Закрыть карточку места" }).click();
  await page.getByRole("button", { name: "12:00–14:00", exact: true }).click();
  await expect(desk).toHaveAttribute("data-status", "free");
  await expect(desk.locator("[data-person-id]")).toHaveCount(0);
  await desk.click();
  await expect(
    details(page).getByText("Следующая бронь", { exact: true }),
  ).toBeVisible();
  await expect(
    details(page).getByRole("img", { name: /Мария Соколова/ }),
  ).toHaveCount(0);
  await page.getByRole("button", { name: "Закрыть карточку места" }).click();
  await page.getByRole("button", { name: "14:00–16:00", exact: true }).click();
  await expect(desk).toHaveAttribute("aria-label", /Павел Громов/);
  await expect(desk.locator('[data-person-id="e04"]')).toHaveCount(1);
  await page.getByRole("button", { name: "09:00–17:00", exact: true }).click();
  await expect(desk.locator("[data-person-id]")).toHaveCount(2);
  await desk.click();
  const timeline = details(page).getByRole("region", {
    name: "Брони на выбранное время",
  });
  await expect(
    timeline.getByRole("heading", { name: "2 брони в этом интервале" }),
  ).toBeVisible();
  await expect(
    timeline.getByText("Мария Соколова", { exact: true }),
  ).toBeVisible();
  await expect(
    timeline.getByText("Павел Громов", { exact: true }),
  ).toBeVisible();
  await expect(
    timeline.getByText("10:00–12:00 МСК", { exact: true }),
  ).toBeVisible();
  await expect(
    timeline.getByText("14:00–16:00 МСК", { exact: true }),
  ).toBeVisible();
  expect(
    await timeline
      .locator("[data-person-id]")
      .evaluateAll((nodes) =>
        nodes.map((node) => node.getAttribute("data-person-id")),
      ),
  ).toEqual(["e03", "e04"]);
  await page.screenshot({
    path: info.outputPath(`employee-timeline-${info.project.name}.png`),
    fullPage: true,
  });
});

test("case-insensitive lookup selects permanent owner and can show available FreeDesk @smoke @mobile", async ({
  page,
}) => {
  await login(page);
  await search(page, "сМиРнО");
  await page
    .getByRole("button", {
      name: "Показать сотрудника Анна Смирнова",
      exact: true,
    })
    .click();
  await expect(page.getByTestId("space-D-07")).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(page.getByTestId("space-D-07")).toHaveAttribute(
    "data-status",
    "dedicated",
  );
  await expect(
    details(page).getByText("Анна Смирнова", { exact: true }),
  ).toBeVisible();
  await expect(
    details(page).getByText(/Бронирование недоступно/),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Показать свободные FreeDesk", exact: true })
    .click();
  await expect(
    page.getByLabel("Только свободные", { exact: true }),
  ).toBeChecked();
  await expect(page.getByTestId("space-D-07")).toHaveCount(0);
  expect(
    await page
      .locator("[data-resource]")
      .evaluateAll((nodes) =>
        nodes.every((node) => node.getAttribute("data-status") === "free"),
      ),
  ).toBe(true);
});

test("employee lookup changes floor and highlights the actual reservation @smoke @mobile", async ({
  page,
}, info) => {
  await login(page);
  await search(page, "Максим");
  await page
    .getByRole("button", {
      name: "Показать сотрудника Максим Николаев",
      exact: true,
    })
    .click();
  await expect(page.getByLabel("Этаж", { exact: true })).toHaveValue("floor-3");
  await expect(page.getByTestId("space-D-32")).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(
    details(page).getByText("Максим Николаев", { exact: true }),
  ).toBeVisible();
  await expect(
    details(page)
      .getByRole("region", { name: "Брони на выбранное время" })
      .getByText("10:00–12:00 МСК", { exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: info.outputPath(`employee-location-${info.project.name}.png`),
    fullPage: true,
  });
});

test("no booking in selected period is not presented as physical absence @smoke @mobile", async ({
  page,
}, info) => {
  await login(page);
  await page.getByRole("button", { name: "12:00–14:00", exact: true }).click();
  await search(page, "Мария");
  await page
    .getByRole("button", {
      name: "Показать сотрудника Мария Соколова",
      exact: true,
    })
    .click();
  await expect(
    details(page).getByRole("heading", { name: "Мария Соколова", exact: true }),
  ).toBeVisible();
  await expect(
    details(page).getByText(
      "Брони или закрепления на выбранный интервал не найдены.",
      { exact: true },
    ),
  ).toBeVisible();
  await expect(
    details(page).getByText(/Это не означает, что сотрудника нет в офисе/),
  ).toBeVisible();
  await expect(
    page.getByTestId("space-D-03").locator("[data-person-id]"),
  ).toHaveCount(0);
  await page
    .getByRole("button", { name: "Закрыть карточку сотрудника", exact: true })
    .click();
  if (info.project.name === "mobile")
    await expect(
      page.getByRole("button", { name: "Найти сотрудника" }),
    ).toBeFocused();
});

test("empty search and lookup outage recover without blocking map @smoke @mobile", async ({
  page,
}) => {
  let unavailable = true;
  await page.route("**/api/v1/employees?**", (route) =>
    unavailable
      ? route.fulfill({
          status: 503,
          contentType: "application/json",
          body: JSON.stringify({
            error: { message: "Поиск временно недоступен" },
          }),
        })
      : route.continue(),
  );
  await login(page);
  await search(page, "Мария");
  const directory = page.getByRole("region", {
    name: "Поиск сотрудников",
    exact: true,
  });
  await expect(directory.getByRole("alert")).toHaveText(
    /Поиск временно недоступен/,
  );
  await expect(page.getByTestId("space-D-03")).toHaveAttribute(
    "aria-label",
    /Мария Соколова/,
  );
  unavailable = false;
  await directory
    .getByRole("button", { name: "Повторить поиск", exact: true })
    .click();
  await expect(
    page.getByRole("button", {
      name: "Показать сотрудника Мария Соколова",
      exact: true,
    }),
  ).toBeVisible();
  await search(page, "Никого123");
  await expect(directory.getByText(/Сотрудники не найдены/)).toBeVisible();
});

test("missing fictional portrait falls back to initials on map and card @smoke @mobile", async ({
  page,
}) => {
  await page.route("**/demo-avatars/v1/e03.svg", (route) =>
    route.abort("failed"),
  );
  await login(page);
  const desk = page.getByTestId("space-D-03");
  await expect(desk.locator("image")).toHaveCount(0);
  await expect(desk.getByText("МС", { exact: true })).toBeVisible();
  await desk.click();
  await expect(
    details(page).getByRole("img", { name: /Мария Соколова/ }),
  ).toHaveText("МС");
});

test("closing a pending lookup prevents a late result from selecting an old place @smoke @mobile", async ({
  page,
}) => {
  let release!: () => void, received!: () => void, finished!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  const seen = new Promise<void>((resolve) => {
    received = resolve;
  });
  const complete = new Promise<void>((resolve) => {
    finished = resolve;
  });
  await page.route("**/api/v1/employees/e03/location?**", async (route) => {
    const response = await route.fetch();
    received();
    await gate;
    try {
      await route.fulfill({ response });
    } catch {
      /* The client is allowed to abort the cancelled lookup. */
    } finally {
      finished();
    }
  });
  await login(page);
  await search(page, "Мария");
  await page
    .getByRole("button", {
      name: "Показать сотрудника Мария Соколова",
      exact: true,
    })
    .click();
  await seen;
  await page
    .getByRole("button", { name: "Закрыть карточку сотрудника", exact: true })
    .click();
  await page.getByTestId("space-D-07").click();
  release();
  await complete;
  await expect(page.getByTestId("space-D-07")).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  await expect(page.getByTestId("space-D-03")).toHaveAttribute(
    "aria-pressed",
    "false",
  );
  await expect(
    details(page).getByRole("heading", { name: /Рабочее место D-07/ }),
  ).toBeVisible();
});
