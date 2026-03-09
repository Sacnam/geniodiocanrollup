import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('user can register', async ({ page }) => {
    await page.goto('/register');
    
    await page.fill('[data-testid="email-input"]', `test${Date.now()}@example.com`);
    await page.fill('[data-testid="password-input"]', 'SecurePass123!');
    await page.fill('[data-testid="first-name-input"]', 'Test');
    await page.fill('[data-testid="last-name-input"]', 'User');
    
    await page.click('[data-testid="register-button"]');
    
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
  });

  test('user can login', async ({ page }) => {
    await page.goto('/login');
    
    await page.fill('[data-testid="email-input"]', 'demo@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
    
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('protected routes redirect to login', async ({ page }) => {
    await page.goto('/feeds');
    await expect(page).toHaveURL(/\/login/);
  });

  test('user can logout', async ({ page }) => {
    // Login first
    await page.goto('/login');
    await page.fill('[data-testid="email-input"]', 'demo@example.com');
    await page.fill('[data-testid="password-input"]', 'password123');
    await page.click('[data-testid="login-button"]');
    
    // Logout
    await page.click('[data-testid="user-menu"]');
    await page.click('[data-testid="logout-button"]');
    
    await expect(page).toHaveURL('/login');
  });
});
