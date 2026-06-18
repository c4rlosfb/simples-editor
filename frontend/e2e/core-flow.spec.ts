import { test, expect } from '@playwright/test';

test.describe('Simples Editor', () => {
  test('página carrega com título', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page).toHaveTitle(/SIMPLES/i);
  });

  test('header com Simples Editor está visível', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('h1').first()).toContainText('Simples Editor');
  });

  test('toolbar tem botão Compilar', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('button', { name: /Compilar/ })).toBeVisible({ timeout: 10000 });
  });

  test('toolbar tem botão Limpar', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    await expect(page.getByRole('button', { name: 'Limpar' })).toBeVisible({ timeout: 10000 });
  });
});
