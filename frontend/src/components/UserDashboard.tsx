import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

interface UserDashboardData {
  numberplate: string;
  times_passed: number;
  violations: number;
  is_blacklisted: boolean;
  avg_speed: number;
}

const UserDashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<UserDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const { token, user } = useAuth();

  const fetchDashboardData = async () => {
    try {
      const response = await fetch('http://localhost:5000/user-dashboard', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setDashboardData(data.data);
      } else {
        setError(data.error || 'Failed to fetch dashboard data');
      }
    } catch (error) {
      console.error('Dashboard fetch error:', error);
      setError('Network error. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchDashboardData();
    }
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900">
        <div className="text-white text-xl">Loading your dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900">
        <div className="text-center">
          <div className="text-red-400 text-lg mb-4">{error}</div>
          <button
            onClick={fetchDashboardData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900">
        <div className="text-white text-xl">No data available</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900 p-6">
      {/* Background decoration */}
      <div className="absolute inset-0">
        <div className="absolute top-0 -left-4 w-72 h-72 bg-purple-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div>
        <div className="absolute top-0 -right-4 w-72 h-72 bg-yellow-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-20 w-72 h-72 bg-pink-300 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-4000"></div>
      </div>

      <div className="relative max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">Vehicle Dashboard</h1>
          <div className="text-xl text-gray-300">
            Number Plate: <span className="font-mono font-bold text-blue-300">{dashboardData.numberplate}</span>
          </div>
        </div>

        {/* Dashboard Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Times Passed */}
          <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl shadow-2xl p-6">
            <div className="text-center">
              <div className="text-3xl mb-2">🚗</div>
              <div className="text-2xl font-bold text-white mb-1">{dashboardData.times_passed}</div>
              <div className="text-gray-300 text-sm">Times Passed</div>
            </div>
          </div>

          {/* Violations */}
          <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl shadow-2xl p-6">
            <div className="text-center">
              <div className="text-3xl mb-2">⚠️</div>
              <div className="text-2xl font-bold text-red-400 mb-1">{dashboardData.violations}</div>
              <div className="text-gray-300 text-sm">Violations</div>
            </div>
          </div>

          {/* Blacklist Status */}
          <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl shadow-2xl p-6">
            <div className="text-center">
              <div className="text-3xl mb-2">{dashboardData.is_blacklisted ? '🚫' : '✅'}</div>
              <div className={`text-2xl font-bold mb-1 ${dashboardData.is_blacklisted ? 'text-red-400' : 'text-green-400'}`}>
                {dashboardData.is_blacklisted ? 'Yes' : 'No'}
              </div>
              <div className="text-gray-300 text-sm">Blacklisted</div>
            </div>
          </div>

          {/* Average Speed */}
          <div className="backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl shadow-2xl p-6">
            <div className="text-center">
              <div className="text-3xl mb-2">🏎️</div>
              <div className="text-2xl font-bold text-blue-400 mb-1">{dashboardData.avg_speed}</div>
              <div className="text-gray-300 text-sm">Avg Speed (km/h)</div>
            </div>
          </div>
        </div>

        {/* Additional Info */}
        <div className="mt-8 backdrop-blur-xl bg-white/10 border border-white/20 rounded-2xl shadow-2xl p-6">
          <h2 className="text-2xl font-bold text-white mb-4 text-center">Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-gray-300">
            <div>
              <strong>Total Detections:</strong> {dashboardData.times_passed} times
            </div>
            <div>
              <strong>Compliance Rate:</strong> {
                dashboardData.times_passed > 0
                  ? Math.round(((dashboardData.times_passed - dashboardData.violations) / dashboardData.times_passed) * 100)
                  : 100
              }%
            </div>
            <div>
              <strong>Status:</strong>
              <span className={dashboardData.is_blacklisted ? 'text-red-400 ml-2' : 'text-green-400 ml-2'}>
                {dashboardData.is_blacklisted ? 'Blacklisted Vehicle' : 'Good Standing'}
              </span>
            </div>
            <div>
              <strong>Average Speed:</strong> {dashboardData.avg_speed} km/h
            </div>
          </div>
        </div>

        {/* Logout Button */}
        <div className="mt-8 text-center">
          <button
            onClick={() => {
              localStorage.removeItem('token');
              localStorage.removeItem('user');
              window.location.href = '/login';
            }}
            className="px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors duration-200"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
};

export default UserDashboard;