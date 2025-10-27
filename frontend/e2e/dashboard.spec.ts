import { test, expect } from '@playwright/test';

test.describe('Dashboard', () => {
  test('should load and display the dashboard', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Dashboard')).toBeVisible();
  });

  test('should have navigation sidebar', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Site Monitor')).toBeVisible();
    await expect(page.getByText('Sites')).toBeVisible();
    await expect(page.getByText('Debug Console')).toBeVisible();
    await expect(page.getByText('SLA Reports')).toBeVisible();
    await expect(page.getByText('Settings')).toBeVisible();
  });

  test('should navigate to Sites page', async ({ page }) => {
    await page.goto('/');
    await page.getByText('Sites').click();
    await expect(page.url()).toContain('/sites');
  });

  test('should navigate to Debug Console', async ({ page }) => {
    await page.goto('/');
    await page.getByText('Debug Console').click();
    await expect(page.url()).toContain('/debug');
  });

  test('should navigate to SLA Reports', async ({ page }) => {
    await page.goto('/');
    await page.getByText('SLA Reports').click();
    await expect(page.url()).toContain('/sla');
  });

  test('should navigate to Settings', async ({ page }) => {
    await page.goto('/');
    await page.getByText('Settings').click();
    await expect(page.url()).toContain('/settings');
  });
});
