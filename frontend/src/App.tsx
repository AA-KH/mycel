import {
  Navigate,
  Route,
  BrowserRouter as Router,
  Routes,
} from "react-router-dom";

import AdminAuthWrapper from "@components/AdminAuthWrapper";
import "./App.css";
import AdminPage from "./pages/AdminPage";
import DashboardPage from "./pages/DashboardPage";
import HomePage from "./pages/HomePage";
import LoginPage from "./pages/LoginPage";
import OfficePage from "./pages/OfficePage";
import RealEstateDemoPage from "./pages/RealEstateDemoPage";
import CompanyBuilderDemoPage from "./pages/CompanyBuilderDemoPage";
import ArmorIQPage from "./pages/ArmorIQPage";
import { useAuth } from "./contexts/AuthContext";

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isLoading, isAuthenticated } = useAuth();

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-screen bg-background">
        <div className="bg-white/95 backdrop-blur-sm p-8 rounded-2xl text-center border border-gray-200/40 shadow-2xl">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

import { RealtimeProvider } from "./providers/RealtimeProvider";

const App = () => {
  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <RealtimeProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <HomePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/office"
            element={
              <ProtectedRoute>
                <OfficePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/company-builder"
            element={
              <ProtectedRoute>
                <CompanyBuilderDemoPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/real-estate"
            element={
              <ProtectedRoute>
                <RealEstateDemoPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/armoriq"
            element={
              <ProtectedRoute>
                <ArmorIQPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin"
            element={
              <ProtectedRoute>
                <AdminAuthWrapper>
                  <AdminPage />
                </AdminAuthWrapper>
              </ProtectedRoute>
            }
          />
        </Routes>
      </RealtimeProvider>
    </Router>
  );
};

export default App;
