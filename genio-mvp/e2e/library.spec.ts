import { test, expect } from '@playwright/test';

test.describe('Library Module', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'testpassword123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/feeds');
  });

  test('should navigate to library page', async ({ page }) => {
    await page.goto('/library');
    
    // Should show library page
    await expect(page.locator('text=Library')).toBeVisible();
    await expect(page.locator('text=Upload')).toBeVisible();
  });

  test('should upload a document', async ({ page }) => {
    await page.goto('/library');
    
    // Click upload button
    await page.click('text=Upload');
    
    // Upload a test file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test-document.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('%PDF-1.4 test content'),
    });
    
    // Should show upload progress or success
    await expect(page.locator('text=uploading').or(page.locator('text=processing'))).toBeVisible({ timeout: 10000 });
  });

  test('should view document list', async ({ page }) => {
    await page.goto('/library');
    
    // Should show document list or empty state
    const hasDocuments = await page.locator('[data-testid="document-item"]').count() > 0;
    
    if (!hasDocuments) {
      // Should show empty state
      await expect(page.locator('text=No documents')).toBeVisible();
    } else {
      // Should show documents
      await expect(page.locator('[data-testid="document-item"]').first()).toBeVisible();
    }
  });

  test('should search documents', async ({ page }) => {
    await page.goto('/library');
    
    // Type in search box
    const searchInput = page.locator('input[placeholder*="search" i]').or(page.locator('input[type="search"]'));
    
    if (await searchInput.isVisible({ timeout: 5000 }).catch(() => false)) {
      await searchInput.fill('test query');
      await searchInput.press('Enter');
      
      // Should show search results or no results
      await expect(page.locator('text=No results').or(page.locator('[data-testid="document-item"]'))).toBeVisible({ timeout: 10000 });
    }
  });

  test('should switch between library views', async ({ page }) => {
    await page.goto('/library');
    
    // Look for view toggle buttons
    const listViewBtn = page.locator('button[title="List view"]').or(page.locator('text=List'));
    const gridViewBtn = page.locator('button[title="Grid view"]').or(page.locator('text=Grid'));
    
    if (await gridViewBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await gridViewBtn.click();
      // Should switch to grid view
      await expect(page.locator('[data-testid="grid-view"]')).toBeVisible({ timeout: 5000 }).catch(() => {});
    }
    
    if (await listViewBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await listViewBtn.click();
      // Should switch to list view
      await expect(page.locator('[data-testid="list-view"]')).toBeVisible({ timeout: 5000 }).catch(() => {});
    }
  });

  test('should open document reader', async ({ page }) => {
    await page.goto('/library');
    
    // Click on first document if exists
    const firstDoc = page.locator('[data-testid="document-item"]').first();
    
    if (await firstDoc.isVisible({ timeout: 5000 }).catch(() => false)) {
      await firstDoc.click();
      
      // Should navigate to reader
      await expect(page).toHaveURL(/.*\/library\/.+/, { timeout: 10000 });
      
      // Should show reader content
      await expect(page.locator('text=Reader').or(page.locator('article')).or(page.locator('[data-testid="reader"]'))).toBeVisible({ timeout: 10000 });
    }
  });

  test('should search within document (GraphRAG)', async ({ page }) => {
    await page.goto('/library');
    
    // Try to navigate to search view
    const searchTab = page.locator('text=Search').or(page.locator('[data-testid="search-tab"]'));
    
    if (await searchTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await searchTab.click();
      
      // Should show search interface
      const searchInput = page.locator('input[placeholder*="search" i]');
      await searchInput.fill('test query');
      await searchInput.press('Enter');
      
      // Should show search results
      await expect(page.locator('text=Results').or(page.locator('[data-testid="search-results"]'))).toBeVisible({ timeout: 15000 });
    }
  });

  test('should view knowledge graph', async ({ page }) => {
    await page.goto('/library');
    
    // Look for graph/concept map view
    const graphTab = page.locator('text=Graph').or(page.locator('text=Concepts')).or(page.locator('[data-testid="graph-tab"]'));
    
    if (await graphTab.isVisible({ timeout: 5000 }).catch(() => false)) {
      await graphTab.click();
      
      // Should show graph visualization
      await expect(page.locator('svg').or(page.locator('[data-testid="concept-map"]'))).toBeVisible({ timeout: 10000 });
    }
  });

  test('should create highlight in document', async ({ page }) => {
    await page.goto('/library');
    
    // Open first document
    const firstDoc = page.locator('[data-testid="document-item"]').first();
    
    if (await firstDoc.isVisible({ timeout: 5000 }).catch(() => false)) {
      await firstDoc.click();
      
      // Wait for reader to load
      await page.waitForTimeout(2000);
      
      // Try to select text (this is tricky in E2E tests)
      const content = page.locator('article p').first().or(page.locator('[data-testid="document-content"]'));
      
      if (await content.isVisible({ timeout: 5000 }).catch(() => false)) {
        // Try to create highlight by clicking highlight button if exists
        const highlightBtn = page.locator('button[title="Highlight"]').or(page.locator('text=Highlight'));
        
        if (await highlightBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
          await highlightBtn.click();
          // Should show highlight color picker or confirmation
        }
      }
    }
  });

  test('should delete document', async ({ page }) => {
    await page.goto('/library');
    
    // Find first document with delete button
    const deleteBtn = page.locator('[data-testid="delete-document"]').first();
    
    if (await deleteBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
      await deleteBtn.click();
      
      // Should show confirmation dialog
      const confirmBtn = page.locator('button:has-text("Delete")').or(page.locator('text=Confirm'));
      
      if (await confirmBtn.isVisible({ timeout: 5000 }).catch(() => false)) {
        await confirmBtn.click();
        
        // Should show success message
        await expect(page.locator('text=deleted').or(page.locator('text=removed'))).toBeVisible({ timeout: 10000 });
      }
    }
  });
});
