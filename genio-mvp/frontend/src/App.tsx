import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { Navigation } from './components/Navigation';
import { ErrorBoundary } from './components/ErrorBoundary';
import { useAuth } from './hooks/useAuth';

// Pages - using default imports
import ArticlesPage from './pages/Articles';
import BriefPage from './pages/Brief';
import FeedsPage from './pages/Feeds';
import LibraryPage from './pages/LibraryPage';
import LabPageAdvanced from './pages/LabPageAdvanced';
import LoginPage from './pages/Login';
import RegisterPage from './pages/Register';
import SettingsPage from './pages/SettingsPage';
import ReadingListPage from './pages/ReadingListPage';
import ScoutPage from './pages/ScoutPage';
import { ForgotPasswordPage } from './pages/ForgotPassword';
import { ResetPasswordPage } from './pages/ResetPassword';
import { OnboardingWizard } from './components/OnboardingWizard';

// Create Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Protected layout with navigation
const ProtectedLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Navigation />
      <main className="flex-1 overflow-auto w-full md:ml-64">
        {children}
      </main>
    </div>
  );
};

// Protected route wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return isAuthenticated ? (
    <ProtectedLayout>{children}</ProtectedLayout>
  ) : (
    <Navigate to="/login" replace />
  );
};

// Public route wrapper
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return !isAuthenticated ? <>{children}</> : <Navigate to="/feeds" replace />;
};

// App Routes
const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <LoginPage />
          </PublicRoute>
        }
      />
      <Route
        path="/register"
        element={
          <PublicRoute>
            <RegisterPage />
          </PublicRoute>
        }
      />
      <Route
        path="/forgot-password"
        element={
          <PublicRoute>
            <ForgotPasswordPage />
          </PublicRoute>
        }
      />
      <Route
        path="/reset-password"
        element={
          <PublicRoute>
            <ResetPasswordPage />
          </PublicRoute>
        }
      />
      <Route
        path="/onboarding"
        element={
          <ProtectedRoute>
            <OnboardingWizard />
          </ProtectedRoute>
        }
      />

      {/* Protected Routes */}
      <Route
        path="/feeds"
        element={
          <ProtectedRoute>
            <FeedsPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/articles"
        element={
          <ProtectedRoute>
            <ArticlesPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/brief"
        element={
          <ProtectedRoute>
            <BriefPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/library"
        element={
          <ProtectedRoute>
            <LibraryPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/reading-list"
        element={
          <ProtectedRoute>
            <ReadingListPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/lab"
        element={
          <ProtectedRoute>
            <LabPageAdvanced />
          </ProtectedRoute>
        }
      />
      <Route
        path="/scout"
        element={
          <ProtectedRoute>
            <ScoutPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <SettingsPage />
          </ProtectedRoute>
        }
      />

      {/* Default redirect */}
      <Route path="/" element={<Navigate to="/feeds" replace />} />
      <Route path="*" element={<Navigate to="/feeds" replace />} />
    </Routes>
  );
};

// Main App
const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <ThemeProvider>
        <QueryClientProvider client={queryClient}>
          <BrowserRouter>
            <AuthProvider>
              <AppRoutes />
            </AuthProvider>
          </BrowserRouter>
          <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
      </ThemeProvider>
    </ErrorBoundary>
  );
};

export default App;
