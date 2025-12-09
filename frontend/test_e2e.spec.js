const { test, expect } = require('@playwright/test');

const BASE_URL = process.env.BASE_URL || 'http://localhost:5500';

test('Homepage loads', async ({ page }) => {
  await page.goto(`${BASE_URL}/index.html`);
  await expect(page.locator('text=RuralAsist')).toBeVisible();
});

test('Chatbot opens and sends message', async ({ page }) => {
  await page.goto(`${BASE_URL}/chatbot_new.html`);
  await page.click('#send-btn');
  await page.fill('#chat-input', 'Hello');
  await page.click('#send-btn');
  await expect(page.locator('.msg.user-msg')).toContainText('Hello');
});

test('Report scam page loads', async ({ page }) => {
  await page.goto(`${BASE_URL}/report.html`);
  await expect(page.locator('text=Report a Scam')).toBeVisible();
});
