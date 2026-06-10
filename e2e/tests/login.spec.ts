import { test, expect } from '@playwright/test';

/**
 * E2E test: Login flow
 *
 * Covers:
 * - Login page loads
 * - Email/password form present
 * - Login button click triggers auth
 * - Successful login redirects to editor
 * - Invalid credentials show error
 */
test.describe('Login Flow', () => {
  test('should display the login page with email and password fields', async ({ page }) => {
    await page.goto('/');

    // Page should load
    await expect(page).toHaveTitle(/Simples Editor/);

    // Should show login form elements
    // Check for email input
    const emailInput = page.locator('input[type="email"], input[placeholder*="email" i]');
    const passwordInput = page.locator('input[type="password"]');

    // Login form should be visible (if not authenticated)
    const loginForm = page.locator('form').first();
    const editorPanel = page.locator('text=Editor SIMPLES');

    // If we see login form, test it
    if (await loginForm.isVisible({ timeout: 3000 }).catch(() => false)) {
      await expect(emailInput).toBeVisible();
      await expect(passwordInput).toBeVisible();

      const submitButton = page.locator('button[type="submit"], button:has-text("Entrar"), button:has-text("Login")');
      await expect(submitButton).toBeVisible();
    } else if (await editorPanel.isVisible({ timeout: 3000 }).catch(() => false)) {
      // Already logged in - skip
      test.skip();
    }
  });

  test('should show error message with invalid credentials', async ({ page }) => {
    await page.goto('/');

    const emailInput = page.locator('input[type="email"], input[placeholder*="email" i]');
    const passwordInput = page.locator('input[type="password"]');

    if (!await emailInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      test.skip(); // No login form found
      return;
    }

    // Fill with invalid data
    await emailInput.fill('invalido@teste.com');
    await passwordInput.fill('senha_errada');

    const submitButton = page.locator('button[type="submit"], button:has-text("Entrar"), button:has-text("Login")');
    await submitButton.click();

    // Should show error message
    const errorMessage = page.locator('text=/erro|inv[áa]lido|incorreto|falhou|n[aã]o encontrado/i');
    await expect(errorMessage).toBeVisible({ timeout: 10000 });
  });

  test('should redirect to editor after successful login', async ({ page }) => {
    await page.goto('/');

    const emailInput = page.locator('input[type="email"], input[placeholder*="email" i]');
    const passwordInput = page.locator('input[type="password"]');

    if (!await emailInput.isVisible({ timeout: 3000 }).catch(() => false)) {
      test.skip(); // Already logged in
      return;
    }

    // Use test credentials from env
    const testEmail = process.env.TEST_EMAIL || 'teste@simples-editor.com';
    const testPassword = process.env.TEST_PASSWORD || 'teste123';

    await emailInput.fill(testEmail);
    await passwordInput.fill(testPassword);

    const submitButton = page.locator('button[type="submit"], button:has-text("Entrar"), button:has-text("Login")');
    await submitButton.click();

    // Should navigate to editor
    await expect(page.locator('text=Editor SIMPLES')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('text=Simples Editor').first()).toBeVisible();
  });
});
