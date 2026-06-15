import { test, expect } from '@playwright/test';

/**
 * E2E test: Edit flow
 *
 * Covers:
 * - Editor loads with default SIMPLES code
 * - Code can be typed/modified
 * - Syntax highlighting is applied to keywords
 * - Monaco editor is interactive
 */
test.describe('Edit Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    // Wait for the editor to load
    await page.waitForTimeout(3000);
  });

  test('should display the editor panel with default code', async ({ page }) => {
    // Editor panel should be visible
    const editorHeader = page.locator('text=Editor SIMPLES');
    await expect(editorHeader).toBeVisible({ timeout: 10000 });

    // Monaco editor should be present
    const monacoEditor = page.locator('.monaco-editor');
    await expect(monacoEditor).toBeVisible({ timeout: 15000 });
  });

  test('should display default SIMPLES program code', async ({ page }) => {
    const monacoEditor = page.locator('.monaco-editor');

    // Wait for Monaco to fully load
    await expect(monacoEditor).toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);

    // Default code should contain SIMPLES keywords
    const editorContent = page.locator('.view-lines');
    await expect(editorContent).toContainText('programa', { timeout: 5000 });
    await expect(editorContent).toContainText('inicio', { timeout: 5000 });
    await expect(editorContent).toContainText('fim', { timeout: 5000 });
  });

  test('should allow editing code in the editor', async ({ page }) => {
    const monacoEditor = page.locator('.monaco-editor');

    await expect(monacoEditor).toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);

    // Click on the editor to focus it
    const editorContent = page.locator('.view-lines');
    await editorContent.click();

    // Monaco uses contenteditable, try typing
    await page.keyboard.press('Control+a');
    await page.waitForTimeout(500);

    // Type new code
    const newCode = 'programa teste\n  inteiro x\ninicio\n  x <- 10\n  escreva x\nfim';
    await page.keyboard.type(newCode, { delay: 20 });

    // Verify the new code is in the editor
    await expect(editorContent).toContainText('programa teste', { timeout: 5000 });
  });

  test('should highlight SIMPLES keywords with different colors', async ({ page }) => {
    const monacoEditor = page.locator('.monaco-editor');
    await expect(monacoEditor).toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);

    // Keywords should be styled with CSS classes
    // Monaco applies 'mtk' classes to tokens
    const keywordElements = page.locator('.mtk7, .mtk8, .mtk9, .mtk10');
    const count = await keywordElements.count();
    expect(count).toBeGreaterThan(0);
  });

  test('should display three-panel layout', async ({ page }) => {
    await page.waitForTimeout(2000);

    // All three panels should be present
    await expect(page.locator('text=Editor SIMPLES')).toBeVisible();
    await expect(page.locator('text=NASM x86')).toBeVisible();
    await expect(page.locator('text=Terminal')).toBeVisible();
  });

  test('should show line numbers in the editor', async ({ page }) => {
    const monacoEditor = page.locator('.monaco-editor');
    await expect(monacoEditor).toBeVisible({ timeout: 15000 });
    await page.waitForTimeout(2000);

    // Line numbers should be visible
    const lineNumbers = page.locator('.line-numbers');
    const count = await lineNumbers.count();
    expect(count).toBeGreaterThan(0);
  });
});
