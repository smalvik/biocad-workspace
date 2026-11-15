import { test, expect } from '@playwright/test';

test('unpublished Allure paths return 404 instead of the application @mobile', async ({ page, request }) => {
  const redirect = await request.get('/allure', { maxRedirects: 0 });
  expect(redirect.status()).toBe(308);
  expect(redirect.headers()['location']).toMatch(/\/allure\/$/);
  const response = await page.goto('/allure/unpublished-version/index.html');
  expect(response?.status()).toBe(404);
  await expect(page.getByRole('heading', { name: '404 Not Found' })).toBeVisible();
  expect(response?.headers()['content-disposition']).toBe('inline');
});
