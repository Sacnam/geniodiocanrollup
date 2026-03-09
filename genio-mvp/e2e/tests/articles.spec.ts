import { test, expect } from '@playwright/test';

test.describe('Article Reading', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'demo@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
    await page.waitForURL(/\/dashboard/);
  });

  test('articles display with delta score badges', async ({ page }) => {
    await page.goto('/articles');
    
    await expect(page.locator('[data-testid="article-card"]')).toHaveCount.greaterThan(0);
    await expect(page.locator('[data-testid="delta-badge"]')).toBeVisible();
  });

  test('user can mark article as read', async ({ page }) => {
    await page.goto('/articles');
    
    const firstArticle = page.locator('[data-testid="article-card"]').first();
    await firstArticle.click();
    
    await page.click('[data-testid="mark-read-button"]');
    
    await expect(page.locator('[data-testid="read-indicator"]')).toBeVisible();
  });

  test('search filters articles', async ({ page }) => {
    await page.goto('/articles');
    
    await page.fill('[data-testid="search-input"]', 'AI');
    await page.press('[data-testid="search-input"]', 'Enter');
    
    // All visible articles should contain "AI"
    const articles = await page.locator('[data-testid="article-title"]').allTextContents();
    for (const title of articles) {
      expect(title.toLowerCase()).toContain('ai');
    }
  });

  test('article detail shows summary', async ({ page }) => {
    await page.goto('/articles');
    
    await page.locator('[data-testid="article-card"]').first().click();
    
    await expect(page.locator('[data-testid="article-summary"]')).toBeVisible();
    await expect(page.locator('[data-testid="article-content"]')).toBeVisible();
  });
});
