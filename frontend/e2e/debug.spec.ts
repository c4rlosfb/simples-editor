import { test } from '@playwright/test';
import * as fs from 'fs';

test('debug screenshot', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.waitForTimeout(3000);

  // Capture console errors
  page.on('console', msg => console.log(`CONSOLE: [${msg.type()}] ${msg.text()}`));
  page.on('pageerror', err => console.log(`PAGE ERROR: ${err.message}`));

  // Check what elements exist
  const html = await page.content();
  const bodyText = await page.evaluate(() => document.body.innerText.substring(0, 1000));

  console.log('=== BODY TEXT ===');
  console.log(bodyText);
  console.log('=== PAGE TITLE ===');
  console.log(await page.title());
  console.log('=== ELEMENTS ===');
  const els = await page.evaluate(() => {
    const buttons = document.querySelectorAll('button');
    const h1s = document.querySelectorAll('h1');
    const divs = document.querySelectorAll('[class*="editor"]');
    return {
      buttons: Array.from(buttons).map(b => b.textContent?.trim()),
      h1s: Array.from(h1s).map(h => h.textContent?.trim()),
      editorDivs: Array.from(divs).map(d => d.className),
      rootHTML: document.getElementById('root')?.innerHTML?.substring(0, 500),
    };
  });
  console.log(JSON.stringify(els, null, 2));

  // Screenshot
  await page.screenshot({ path: 'test-results/debug-screenshot.png', fullPage: true });
  console.log('Screenshot saved');
});
