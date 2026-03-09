import { describe, it, expect } from 'vitest';
import { render } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import App from './App';

// Test that App component renders without errors
// This catches import errors and TypeScript issues
describe('App Component', () => {
  it('should render without crashing', () => {
    // This test will fail at import/compile time if there are issues
    expect(() => {
      render(
        <QueryClientProvider client={new QueryClient()}>
          <BrowserRouter>
            <AuthProvider>
              <App />
            </AuthProvider>
          </BrowserRouter>
        </QueryClientProvider>
      );
    }).not.toThrow();
  });

  it('should have all required imports resolved', async () => {
    // Verify all page components can be imported
    const { default: ArticlesPage } = await import('./pages/Articles');
    const { default: BriefPage } = await import('./pages/Brief');
    const { default: FeedsPage } = await import('./pages/Feeds');
    const { default: LoginPage } = await import('./pages/Login');
    const { default: RegisterPage } = await import('./pages/Register');
    const { default: LibraryPage } = await import('./pages/LibraryPage');
    const { default: SettingsPage } = await import('./pages/SettingsPage');
    const { default: LabPageAdvanced } = await import('./pages/LabPageAdvanced');
    const { default: ReadingListPage } = await import('./pages/ReadingListPage');
    const { default: ScoutPage } = await import('./pages/ScoutPage');

    expect(ArticlesPage).toBeDefined();
    expect(BriefPage).toBeDefined();
    expect(FeedsPage).toBeDefined();
    expect(LoginPage).toBeDefined();
    expect(RegisterPage).toBeDefined();
    expect(LibraryPage).toBeDefined();
    expect(SettingsPage).toBeDefined();
    expect(LabPageAdvanced).toBeDefined();
    expect(ReadingListPage).toBeDefined();
    expect(ScoutPage).toBeDefined();
  });
});
