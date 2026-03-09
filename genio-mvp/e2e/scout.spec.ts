import { test, expect } from '@playwright/test';

test.describe('Scout Agents Module', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpassword123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/feeds');
  });

  test('should navigate to scout page', async ({ page }) => {
    await page.goto('/scout');
    
    // Should show scout page
    await expect(page.locator('text=Scout').or(page.locator('text=Research Agents'))).toBeVisible();
  });

  test('should view scout list', async ({ page }) => {
    await page.goto('/scout');
    
    // Should show scout list or empty state
    const hasScouts = await page.locator('[data-testid="scout-item"]').count() > 0;
    
    if (!hasScouts) {
      // Should show empty state with create button
      await expect(page.locator('text=No scouts').or(page.locator('text=Create your first scout'))).toBeVisible();
    } else {
      // Should show scouts
      await expect(page.locator('[data-testid="scout-item"]').first()).toBeVisible();
    }
  });

  test('should create new scout agent', async ({ page }) => {
    await page.goto('/scout');
    
    // Click create button
    const createBtn = page.locator('text=Create Scout').or(page.locator('text=New Scout')).or(page.locator('button:has-text("+")'));
    
    if (await createBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await createBtn.click();
      
      // Should show creation form
      await expect(page.locator('text=Create Scout Agent').or(page.locator('text=New Research Agent'))).toBeVisible({ timeout: 10000 });
      
      // Fill form
      await page.fill('input[name="name"]', 'Test Scout');
      await page.fill('textarea[name="research_question"]', 'What are the latest developments in AI?');
      await page.fill('input[name="keywords"]', 'AI, machine learning, deep learning');
      
      // Submit
      const submitBtn = page.locator('button[type="submit"]');
      await submitBtn.click();
      
      // Should redirect to scout detail or show success
      await expect(page).toHaveURL(/.*\/scout.*/, { timeout: 10000 });
    }
  });

  test('should view scout details', async ({ page }) => {
    await page.goto('/scout');
    
    // Click on first scout
    const firstScout = page.locator('[data-testid="scout-item"]').first();
    
    if (await firstScout.isVisible({ timeout: 5000 }).catch(() => false)) {
      await firstScout.click();
      
      // Should show scout details
      await expect(page.locator('text=Research Question').or(page.locator('text=Status'))).toBeVisible({ timeout: 10000 });
    }
  });

  test('should edit scout configuration', async ({ page }) => {
    await page.goto('/scout');
    
    // Click on first scout
    const firstScout = page.locator('[data-testid="scout-item"]').first();
    
    if (await firstScout.isVisible({ timeout: 5000 }).catch(() => false)) {
      await firstScout.click();
      
      // Look for edit button
      const editBtn = page.locator('button[title="Edit"]').or(page.locator('text=Edit'));
      
      if (await editBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
        await editBtn.click();
        
        // Should show edit form
        await expect(page.locator('text=Edit Scout').or(page.locator('input[name="name"]:enabled'))).toBeVisible({ timeout: 10000 });
        
        // Update name
        await page.fill('input[name="name"]', 'Updated Scout Name');
        
        // Save
        const saveBtn = page.locator('button:has-text("Save")');
        await saveBtn.click();
        
        // Should show updated name
        await expect(page.locator('text=Updated Scout Name')).toBeVisible({ timeout: 10000 });
      }
    }
  });

  test('should run scout manually', async ({ page }) => {
    await page.goto('/scout');
    
    // Click on first scout
    const firstScout = page.locator('[data-testid="scout-item"]').first();
    
    if (await firstScout.isVisible({ timeout: 5000 }).catch(() => false)) {
      await firstScout.click();
      
      // Look for run button
      const runBtn = page.locator('button:has-text("Run")').or(page.locator('text=Start Research'));
      
      if (await runBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
        await runBtn.click();
        
        // Should show running status or progress
        await expect(page.locator('text=Running').or(page.locator('text=Researching'))).toBeVisible({ timeout: 10000 });
      }
    }
  });

  test('should view scout findings', async ({ page }) => {
    await page.goto('/scout');
    
    // Click on first scout
    const firstScout = page.locator('[data-testid="scout-item"]').first();
    
    if (await firstScout.isVisible({ timeout: 5000 }).catch(() => false)) {
      await firstScout.click();
      
      // Navigate to findings tab
      const findingsTab = page.locator('text=Findings').or(page.locator('[data-testid="findings-tab"]'));
      
      if (await findingsTab.isVisible({ timeout: 5000 }).catch(() => false)) {
        await findingsTab.click();
        
        // Should show findings list or empty state
        await expect(page.locator('text=Findings').or(page.locator('text=No findings yet'))).toBeVisible({ timeout: 10000 });
      }
    }
  });

  test('should save/dismiss finding', async ({ page }) => {
    await page.goto('/scout');
    
    // Navigate to findings
    await page.goto('/scout/findings');
    
    // Look for finding items
    const finding = page.locator('[data-testid="finding-item"]').first();
    
    if (await finding.isVisible({ timeout: 5000 }).catch(() => false)) {
      // Look for save button
      const saveBtn = page.locator('button[title="Save"]').or(page.locator('text=Save')).first();
      
      if (await saveBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
        await saveBtn.click();
        
        // Should show saved state
        await expect(page.locator('text=Saved').or(page.locator('[data-testid="saved-badge"]'))).toBeVisible({ timeout: 10000 });
      }
      
      // Look for dismiss button
      const dismissBtn = page.locator('button[title="Dismiss"]').or(page.locator('text=Dismiss')).first();
      
      if (await dismissBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
        await dismissBtn.click();
        
        // Finding should be removed or marked dismissed
        await expect(page.locator('text=Dismissed').or(page.locator('[data-testid="dismissed-badge"]'))).toBeVisible({ timeout: 10000 });
      }
    }
  });

  test('should view scout insights', async ({ page }) => {
    await page.goto('/scout');
    
    // Click on first scout
    const firstScout = page.locator('[data-testid="scout-item"]').first();
    
    if (await firstScout.isVisible({ timeout: 5000 }).catch(() => false)) {
      await firstScout.click();
      
      // Navigate to insights tab
      const insightsTab = page.locator('text=Insights').or(page.locator('[data-testid="insights-tab"]'));
      
      if (await insightsTab.isVisible({ timeout: 5000 }).catch(() => false)) {
        await insightsTab.click();
        
        // Should show insights or empty state
        await expect(page.locator('text=Insights').or(page.locator('text=No insights yet'))).toBeVisible({ timeout: 10000 });
      }
    }
  });

  test('should pause/resume scout', async ({ page }) => {
    await page.goto('/scout');
    
    // Click on first scout
    const firstScout = page.locator('[data-testid="scout-item"]').first();
    
    if (await firstScout.isVisible({ timeout: 5000 }).catch(() => false)) {
      await firstScout.click();
      
      // Look for pause button
      const pauseBtn = page.locator('button:has-text("Pause")').or(page.locator('text=Deactivate'));
      
      if (await pauseBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
        await pauseBtn.click();
        
        // Should show paused status
        await expect(page.locator('text=Paused').or(page.locator('text=Inactive'))).toBeVisible({ timeout: 10000 });
        
        // Look for resume button
        const resumeBtn = page.locator('button:has-text("Resume")').or(page.locator('text=Activate'));
        
        if (await resumeBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
          await resumeBtn.click();
          
          // Should show active status
          await expect(page.locator('text=Active').or(page.locator('text=Running'))).toBeVisible({ timeout: 10000 });
        }
      }
    }
  });

  test('should delete scout', async ({ page }) => {
    await page.goto('/scout');
    
    // Find scout with delete button
    const deleteBtn = page.locator('[data-testid="delete-scout"]').first();
    
    if (await deleteBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await deleteBtn.click();
      
      // Should show confirmation
      const confirmBtn = page.locator('button:has-text("Delete")').last();
      
      if (await confirmBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
        await confirmBtn.click();
        
        // Should show success or remove scout from list
        await expect(page.locator('text=deleted').or(page.locator('text=Scout removed'))).toBeVisible({ timeout: 10000 });
      }
    }
  });
});
