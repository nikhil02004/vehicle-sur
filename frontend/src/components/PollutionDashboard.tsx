import React, { useState, useEffect } from 'react';
import { MapPin, TrendingUp, Car, Activity, Calendar, AlertCircle } from 'lucide-react';
import api from '../services/api';

interface PollutionData {
  location: string;
  date: string;
  total_pollution: number;
  vehicles_passed: number;
  avg_speed: number;
  pollution_level: 'Low' | 'Medium' | 'High';
}

interface PollutionSummary {
  summary: {
    total_locations: number;
    total_emissions: number;
    total_vehicles: number;
    overall_avg_speed: number;
    latest_data_date: string;
  };
  top_locations: Array<{
    location: string;
    total_pollution: number;
    total_vehicles: number;
    avg_speed: number;
  }>;
  daily_trends: Array<{
    date: string;
    daily_pollution: number;
    daily_vehicles: number;
  }>;
}

const PollutionDashboard: React.FC = () => {
  const [pollutionData, setPollutionData] = useState<PollutionData[]>([]);
  const [summary, setSummary] = useState<PollutionSummary | null>(null);
  const [selectedLocation, setSelectedLocation] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadPollutionData();
    loadSummaryData();
  }, []);

  const loadPollutionData = async () => {
    try {
      setIsLoading(true);
      const token = localStorage.getItem('token');
      const response = await api.get('/pollution/locations', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPollutionData(response.data);
    } catch (err) {
      setError('Failed to load pollution data');
      console.error('Error loading pollution data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const loadSummaryData = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await api.get('/pollution/summary', {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSummary(response.data);
    } catch (err) {
      console.error('Error loading summary data:', err);
    }
  };

  const getPollutionLevelColor = (level: string) => {
    switch (level) {
      case 'Low': return 'text-green-600 bg-green-100';
      case 'Medium': return 'text-yellow-600 bg-yellow-100';
      case 'High': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const formatNumber = (num: number | null | undefined) => {
    if (num === null || num === undefined || isNaN(num)) {
      return '0.0';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toFixed(1);
  };

  const filteredData = selectedLocation === 'all'
    ? pollutionData
    : pollutionData.filter(item => item.location === selectedLocation);

  const uniqueLocations = Array.from(new Set(pollutionData.map(item => item.location)));

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 flex items-center">
              <Activity className="mr-3 h-8 w-8 text-green-600" />
              Pollution Monitoring Dashboard
            </h1>
            <p className="text-gray-600 mt-2">Track vehicle emissions and air quality by location</p>
          </div>
          <div className="flex items-center space-x-4">
            <select
              value={selectedLocation}
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="all">All Locations</option>
              {uniqueLocations.map(location => (
                <option key={location} value={location}>
                  {location.charAt(0).toUpperCase() + location.slice(1)}
                </option>
              ))}
            </select>
            <button
              onClick={() => { loadPollutionData(); loadSummaryData(); }}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && summary.summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Locations</p>
                <p className="text-2xl font-bold text-gray-900">{summary.summary.total_locations || 0}</p>
              </div>
              <MapPin className="h-8 w-8 text-blue-600" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Emissions</p>
                <p className="text-2xl font-bold text-gray-900">{formatNumber(summary.summary.total_emissions)}g</p>
              </div>
              <Activity className="h-8 w-8 text-red-600" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Total Vehicles</p>
                <p className="text-2xl font-bold text-gray-900">{summary.summary.total_vehicles || 0}</p>
              </div>
              <Car className="h-8 w-8 text-green-600" />
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Avg Speed</p>
                <p className="text-2xl font-bold text-gray-900">{formatNumber(summary.summary.overall_avg_speed)} km/h</p>
              </div>
              <TrendingUp className="h-8 w-8 text-purple-600" />
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top Polluting Locations */}
        {summary && summary.top_locations && summary.top_locations.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <AlertCircle className="mr-2 h-5 w-5 text-red-600" />
              Top Polluting Locations
            </h2>
            <div className="space-y-3">
              {summary.top_locations.map((location, index) => (
                <div key={location.location} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center">
                    <span className="flex items-center justify-center w-6 h-6 bg-red-100 text-red-800 text-sm font-bold rounded-full mr-3">
                      {index + 1}
                    </span>
                    <div>
                      <p className="font-medium text-gray-900 capitalize">{location.location}</p>
                      <p className="text-sm text-gray-600">{location.total_vehicles} vehicles</p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-red-600">{formatNumber(location.total_pollution)}g</p>
                    <p className="text-sm text-gray-600">{formatNumber(location.avg_speed)} km/h avg</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Recent Daily Trends */}
        {summary && summary.daily_trends && summary.daily_trends.length > 0 && (
          <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center">
              <Calendar className="mr-2 h-5 w-5 text-blue-600" />
              Daily Trends (Last 7 Days)
            </h2>
            <div className="space-y-3">
              {summary.daily_trends.map((trend) => (
                <div key={trend.date} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <p className="font-medium text-gray-900">{new Date(trend.date).toLocaleDateString()}</p>
                    <p className="text-sm text-gray-600">{trend.daily_vehicles} vehicles</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-blue-600">{formatNumber(trend.daily_pollution)}g</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* No Data Message */}
        {summary && (!summary.top_locations || summary.top_locations.length === 0) && (!summary.daily_trends || summary.daily_trends.length === 0) && (
          <div className="bg-white rounded-xl shadow-lg p-8 border border-gray-200 text-center">
            <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No Pollution Data Available</h3>
            <p className="text-gray-600">Upload some videos to start tracking pollution data for different locations.</p>
          </div>
        )}
      </div>

      {/* Detailed Location Data */}
      <div className="bg-white rounded-xl shadow-lg border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center">
            <MapPin className="mr-2 h-5 w-5 text-green-600" />
            Location Pollution Data
            {selectedLocation !== 'all' && (
              <span className="ml-2 px-2 py-1 bg-blue-100 text-blue-800 text-sm rounded-full capitalize">
                {selectedLocation}
              </span>
            )}
          </h2>
        </div>

        {error && (
          <div className="p-4 bg-red-50 border-l-4 border-red-400">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Location</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Pollution Level</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Emissions</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Vehicles</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Avg Speed</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredData.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-4 text-center text-gray-500">
                    No pollution data available
                  </td>
                </tr>
              ) : (
                filteredData.map((item, index) => (
                  <tr key={`${item.location}-${item.date}-${index}`} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="font-medium text-gray-900 capitalize">{item.location}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {new Date(item.date).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${getPollutionLevelColor(item.pollution_level)}`}>
                        {item.pollution_level}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {formatNumber(item.total_pollution)}g
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {item.vehicles_passed}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                      {formatNumber(item.avg_speed)} km/h
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default PollutionDashboard;