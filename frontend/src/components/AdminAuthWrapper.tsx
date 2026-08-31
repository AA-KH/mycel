import { useAuth } from "../contexts/AuthContext";
import {
  faExclamationTriangle,
  faTimes,
} from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import React, { useEffect, useState } from "react";
import AdminLayout from "./AdminLayout";

interface AdminAuthWrapperProps {
  children: React.ReactNode;
}

const AdminAuthWrapper: React.FC<AdminAuthWrapperProps> = ({ children }) => {
  const { isAuthenticated, isLoading, logout, user } = useAuth();
  const [isAdmin, setIsAdmin] = useState(false);
  const [isCheckingAdmin, setIsCheckingAdmin] = useState(true);

  const checkAdminStatus = async () => {
    if (!isAuthenticated) {
      setIsCheckingAdmin(false);
      return;
    }
    // Check if user is admin
    setIsAdmin(!!user?.is_admin);
    setIsCheckingAdmin(false);
  };

  useEffect(() => {
    if (isAuthenticated) {
      checkAdminStatus();
    } else {
      setIsCheckingAdmin(false);
    }
  }, [isAuthenticated]);

  // Loading state
  if (isLoading || isCheckingAdmin) {
    return (
      <div className="relative flex justify-center items-center min-h-screen overflow-hidden">
        <div className="absolute inset-0 bg-slate-900"></div>
        <div className="relative bg-white/95 backdrop-blur-sm p-8 rounded-2xl text-center border border-gray-200/40 shadow-2xl">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-gray-600">Verifying admin permissions...</p>
        </div>
      </div>
    );
  }

  // Not logged in state
  if (!isAuthenticated) {
    return (
      <div className="relative flex justify-center items-center min-h-screen overflow-hidden">
        <div className="absolute inset-0 bg-slate-900"></div>
        <div className="relative bg-white/95 backdrop-blur-sm p-8 rounded-2xl text-center border border-gray-200/40 shadow-2xl max-w-md">
          <div className="w-16 h-16 bg-green-700 rounded-full mx-auto mb-4 flex items-center justify-center">
            <FontAwesomeIcon
              icon={faExclamationTriangle}
              className="w-8 h-8 text-white"
            />
          </div>
          <h1 className="text-2xl font-semibold text-gray-800 mb-2">
            Login Required
          </h1>
          <p className="text-gray-600 mb-6">Please log in to access the admin panel</p>
          <button
            onClick={() => (window.location.href = "/")}
            className="bg-green-700 hover:bg-green-800 text-white px-6 py-2 rounded-lg transition-colors cursor-pointer"
          >
            Go to Login Page
          </button>
        </div>
      </div>
    );
  }

  // Non-admin state
  if (!isAdmin) {
    return (
      <div className="relative flex justify-center items-center min-h-screen overflow-hidden">
        <div className="absolute inset-0 bg-slate-900"></div>
        <div className="relative bg-white/95 backdrop-blur-sm p-8 rounded-2xl text-center border border-gray-200/40 shadow-2xl max-w-md">
          <div className="w-16 h-16 bg-green-700 rounded-full mx-auto mb-4 flex items-center justify-center">
            <FontAwesomeIcon icon={faTimes} className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-2xl font-semibold text-gray-800 mb-2">
            Access Denied
          </h1>
          <p className="text-gray-600 mb-6">You do not have admin permissions to access this page</p>
          <div className="flex gap-3 justify-center">
            <button
              onClick={() => (window.location.href = "/dashboard")}
              className="bg-green-700 hover:bg-green-800 text-white px-4 py-2 rounded-lg transition-colors cursor-pointer"
            >
              Back to Home
            </button>
            <button
              onClick={() => logout()}
              className="bg-gray-500 hover:bg-gray-600 text-white px-4 py-2 rounded-lg transition-colors cursor-pointer"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    );
  }

  return <AdminLayout>{children}</AdminLayout>;
};

export default AdminAuthWrapper;
