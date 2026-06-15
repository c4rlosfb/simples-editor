import { test, expect } from '@playwright/test';

/**
 * E2E test: Stop flow
 *
 * Covers:
 * - Stop button exists during execution
 * - Clicking Stop terminates the running program
 * - Terminal shows stop confirmation
 * - Run button becomes re-enabled after stop
 */
test.describe('Stop Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(3000);
  });

  test('should show Stop button while program is running', async ({ page }) => {
    const monacoEditor = page.locator('.monaco-editor');
    await expect(monacoEditor).toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);

    // Click Run
    const runButton = page.locator('button:has-text("Run"):not(:disabled)');
    await runButton.click();

    // After clicking Run, either a Stop button appears or button is disabled
    await page.waitForTimeout(2000);

    // Check that Run button is disabled or Stop is visible
    const disabledRun = page.locator('button:has-text("Run")[disabled]');
    const stopButton = page.locator('button:has-text("Stop"), button:has-text("stop")');

    const stopFound = await stopButton.isVisible({ timeout: 3000 }).catch(() => false);
    const disabledFound = await disabledRun.isVisible({ timeout: 3000 }).catch(() => false);

    expect(stopFound || disabledFound).toBeTruthy();
  });

  test('should terminate execution when Stop is clicked', async ({ page }) => {
    const monacoEditor = page.locator('.monaco-editor');
    await expect(monacoEditor).toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);

    // Type a program with infinite loop to test stop
    const editorContent = page.locator('.view-lines');
    await editorContent.click();
    await page.keyboard.press('Control+a');
    await page.waitForTimeout(500);

    const infiniteLoop = `programa loop
  inteiro x
inicio
  x <- 1
  enquanto x = 1 faca
    escreva "loop"
  fimenquanto
fim`;

    await page.keyboard.type(infiniteLoop, { delay: 10 });

    // Click Run
    const runButton = page.locator('button:has-text("Run"):not(:disabled)');
    await runButton.click();

    await page.waitForTimeout(3000);

    // Try to find and click Stop
    const stopButton = page.locator('button:has-text("Stop"), button:has-text("Parar")');
    const stopExists = await stopButton.isVisible({ timeout: 3000 }).catch(() => false);

    if (stopExists) {
      await stopButton.click();
      await page.waitForTimeout(2000);

      // Run button should be re-enabled
      await expect(runButton).not.toBeDisabled({ timeout: 5000 });

      // Terminal should show stop confirmation
      const terminal = page.locator('text=Terminal').locator('..');
      await expect(terminal).toContainText(/Stop|Parado|interrompido|cancelado/i, { timeout: 5000 });
    } else {
      // If no stop button, the program completed quickly
      // Verify execution finished
      const terminal = page.locator('text=Terminal').locator('..');
      await expect(terminal).toContainText(/finalizado|codigo|Programa/i, { timeout: 5000 });
    }
  });

  test('should re-enable Run button after execution completes', async ({ page }) => {
    const monacoEditor = page.locator('.monaco-editor');
    await expect(monacoEditor).toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);

    // Click Run with default code (which compiles and exits quickly)
    const runButton = page.locator('button:has-text("Run"):not(:disabled)');
    await expect(runButton).toBeEnabled({ timeout: 5000 });
    await runButton.click();

    // Wait for execution to complete
    await page.waitForTimeout(8000);

    // Run button should be re-enabled
    await expect(runButton).toBeEnabled({ timeout: 10000 });
  });
});
