import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import Layout from './components/Layout';
import UploadVideo from './components/UploadVideo';
import Analytics from './components/Analytics';
import PollutionDashboard from './components/PollutionDashboard';
import BlacklistManager from './components/BlacklistManager';
import Settings from './components/Settings';
import Login from './components/Login';
import Signup from './components/Signup';
import Dashboard from './components/Dashboard';
import UserDashboard from './components/UserDashboard';
import ProtectedRoute from './components/ProtectedRoute';

function App() {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            {/* Public routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />

            {/* Protected routes */}
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />

            <Route path="/user-dashboard" element={
              <ProtectedRoute>
                <UserDashboard />
              </ProtectedRoute>
            } />

            {/* Main app routes with authentication */}
            <Route path="/" element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }>
              <Route index element={<Navigate to="/dashboard" replace />} />
              <Route path="upload" element={<UploadVideo />} />
              <Route path="analytics" element={<Analytics />} />
              <Route path="pollution" element={
                <ProtectedRoute requireAdmin={true}>
                  <PollutionDashboard />
                </ProtectedRoute>
              } />
              <Route path="blacklist" element={
                <ProtectedRoute requireAdmin={true}>
                  <BlacklistManager />
                </ProtectedRoute>
              } />
              <Route path="settings" element={
                <ProtectedRoute requireAdmin={true}>
                  <Settings />
                </ProtectedRoute>
              } />
            </Route>

            {/* Redirect all other routes to dashboard */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  );
}

export default App;
