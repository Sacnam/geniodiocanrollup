import { test, expect } from '@playwright/test';

test.describe('Feed Management', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'demo@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
    await page.waitForURL(/\/dashboard/);
  });

  test('user can add a feed', async ({ page }) => {
    await page.goto('/feeds');
    
    await page.click('[data-testid="add-feed-button"]');
    await page.fill('[data-testid="feed-url-input"]', 'https://news.ycombinator.com/rss');
    await page.fill('[data-testid="feed-category-input"]', 'Technology');
    await page.click('[data-testid="save-feed-button"]');
    
    await expect(page.locator('[data-testid="feed-item"]')).toContainText('Hacker News');
  });

  test('user can delete a feed', async ({ page }) => {
    await page.goto('/feeds');
    
    const initialCount = await page.locator('[data-testid="feed-item"]').count();
    
    await page.click('[data-testid="feed-item"] >> [data-testid="delete-button"]').first();
    await page.click('[data-testid="confirm-delete"]');
    
    await expect(page.locator('[data-testid="feed-item"]')).toHaveCount(initialCount - 1);
  });

  test('user can import OPML', async ({ page }) => {
    await page.goto('/feeds');
    
    await page.click('[data-testid="import-opml-button"]');
    
    // Upload test OPML file
    const fileInput = page.locator('[data-testid="opml-file-input"]');
    await fileInput.setInputFiles('fixtures/test-feeds.opml');
    
    await page.click('[data-testid="import-submit"]');
    
    await expect(page.locator('[data-testid="import-progress"]')).toBeVisible();
    await expect(page.locator('[data-testid="import-success"]')).toBeVisible({ timeout: 30000 });
  });
});
