import { test, expect } from '@playwright/test';

/**
 * E2E test: Run flow
 *
 * Covers:
 * - Run button is visible
 * - Clicking Run compiles the code
 * - NASM panel shows generated assembly
 * - Terminal shows output
 */
test.describe('Run Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(3000);
  });

  test('should display the Run button in the toolbar', async ({ page }) => {
    const runButton = page.locator('button:has-text("Run"):not(:disabled)');
    await expect(runButton).toBeVisible({ timeout: 10000 });
  });

  test('should disable Run button during execution', async ({ page }) => {
    const runButton = page.locator('button:has-text("Run")');
    await expect(runButton).toBeVisible({ timeout: 10000 });
    await expect(runButton).not.toBeDisabled();

    // Click Run
    await runButton.click();

    // Button should show "Executando..." or be disabled
    await expect(page.locator('button:has-text("Executando")')).toBeVisible({ timeout: 5000 });
  });

  test('should show NASM assembly after successful compilation', async ({ page }) => {
    const monacoEditor = page.locator('.monaco-editor');
    await expect(monacoEditor).toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);

    // Click Run
    const runButton = page.locator('button:has-text("Run"):not(:disabled)');
    await runButton.click();

    // Wait for compilation to complete
    await page.waitForTimeout(5000);

    // NASM panel should now have assembly code
    const nasmPanel = page.locator('text=NASM x86').locator('..');
    const nasmContent = page.locator('.monaco-editor').last();
    await expect(nasmContent).toContainText('section .data', { timeout: 10000 });
  });

  test('should show compilation output in terminal', async ({ page }) => {
    const monacoEditor = page.locator('.monaco-editor');
    await expect(monacoEditor).toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);

    // Click Run
    const runButton = page.locator('button:has-text("Run"):not(:disabled)');
    await runButton.click();

    // Wait for execution
    await page.waitForTimeout(5000);

    // Terminal should show status messages
    const terminal = page.locator('text=Terminal').locator('..');
    await expect(terminal).toContainText('Compilando', { timeout: 10000 });
  });

  test('should show error in terminal for invalid code', async ({ page }) => {
    const monacoEditor = page.locator('.monaco-editor');
    await expect(monacoEditor).toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);

    // Clear editor and type invalid code
    const editorContent = page.locator('.view-lines');
    await editorContent.click();
    await page.keyboard.press('Control+a');
    await page.waitForTimeout(500);
    await page.keyboard.type('codigo invalido', { delay: 10 });

    // Click Run
    const runButton = page.locator('button:has-text("Run"):not(:disabled)');
    await runButton.click();

    // Wait for response
    await page.waitForTimeout(5000);

    // Should show an error
    const terminal = page.locator('text=Terminal').locator('..');
    await expect(terminal).toContainText(/Erro|erro/i, { timeout: 10000 });
  });
});
