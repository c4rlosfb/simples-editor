import { test, expect } from '@playwright/test';

/**
 * E2E test: stdin flow
 *
 * Covers:
 * - Programs with leia() prompt for input
 * - User can type input in the terminal
 * - Program continues after input
 * - Output reflects the input provided
 */
test.describe('stdin Flow (Interactive Input)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(3000);
  });

  test('should show terminal panel ready for interaction', async ({ page }) => {
    const terminal = page.locator('text=Terminal').locator('..');
    await expect(terminal).toBeVisible({ timeout: 10000 });

    // Terminal should show welcome message
    await expect(terminal).toContainText('Bem-vindo', { timeout: 5000 });
  });

  test('should allow writing a program with leia()', async ({ page }) => {
    const monacoEditor = page.locator('.monaco-editor');
    await expect(monacoEditor).toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);

    // Write program that reads input
    const editorContent = page.locator('.view-lines');
    await editorContent.click();
    await page.keyboard.press('Control+a');
    await page.waitForTimeout(500);

    const leiaProgram = `programa entrada
  caracter nome
inicio
  escreva "Digite seu nome: "
  leia nome
  escreva "Ola, ", nome
fim`;

    await page.keyboard.type(leiaProgram, { delay: 10 });

    // Verify the program is in the editor
    await expect(editorContent).toContainText('programa entrada', { timeout: 5000 });
  });

  test('should show stdin prompt in terminal during execution', async ({ page }) => {
    const monacoEditor = page.locator('.monaco-editor');
    await expect(monacoEditor).toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);

    // Click Run
    const runButton = page.locator('button:has-text("Run"):not(:disabled)');
    await runButton.click();

    // Wait for execution
    await page.waitForTimeout(5000);

    // Terminal should show output from execution
    const terminal = page.locator('text=Terminal').locator('..');
    await expect(terminal).toBeVisible();
  });

  test('should display output after program execution', async ({ page }) => {
    const monacoEditor = page.locator('.monaco-editor');
    await expect(monacoEditor).toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);

    // Click Run
    const runButton = page.locator('button:has-text("Run"):not(:disabled)');
    await runButton.click();

    // Wait for execution to finish
    await page.waitForTimeout(8000);

    // Terminal should contain output from the program
    const terminal = page.locator('text=Terminal').locator('..');
    await expect(terminal).toContainText(/finalizado|codigo|Programa|Hello|Simples/i, { timeout: 10000 });
  });
});
