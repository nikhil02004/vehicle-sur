import React, { useState, useEffect } from 'react';
import { getAnalytics } from '../services/api';
import { Analytics as AnalyticsType } from '../services/api';
import { BarChart3, Users, AlertTriangle, TrendingUp, RefreshCw, Car } from 'lucide-react';

const Analytics: React.FC = () => {
    const [analytics, setAnalytics] = useState<AnalyticsType | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchAnalytics = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await getAnalytics();
            setAnalytics(data);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to load analytics');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAnalytics();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64 animate-fadeIn">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading analytics...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6 animate-fadeIn">
                <div className="flex items-center justify-between">
                    <div className="flex items-center">
                        <AlertTriangle className="h-6 w-6 text-red-500 mr-3" />
                        <p className="text-red-700 font-medium">{error}</p>
                    </div>
                    <button
                        onClick={fetchAnalytics}
                        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-all card-hover"
                    >
                        Retry
                    </button>
                </div>
            </div>
        );
    }

    const stats = [
        {
            title: 'Total Vehicles',
            value: analytics?.total_vehicles || 0,
            icon: Car,
            color: 'bg-blue-500',
            bgColor: 'bg-blue-50',
            textColor: 'text-blue-700'
        },
        {
            title: 'Speed Violations',
            value: analytics?.speed_violations || 0,
            icon: TrendingUp,
            color: 'bg-red-500',
            bgColor: 'bg-red-50',
            textColor: 'text-red-700'
        },
        {
            title: 'Blacklisted Vehicles',
            value: analytics?.blacklisted_detections || 0,
            icon: AlertTriangle,
            color: 'bg-orange-500',
            bgColor: 'bg-orange-50',
            textColor: 'text-orange-700'
        },
        {
            title: 'Active Sessions',
            value: Math.floor(Math.random() * 10) + 1, // Demo data
            icon: Users,
            color: 'bg-green-500',
            bgColor: 'bg-green-50',
            textColor: 'text-green-700'
        }
    ];

    return (
        <div className="space-y-8 animate-fadeIn">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold gradient-text">📊 Analytics Dashboard</h1>
                    <p className="text-gray-600 mt-2">Monitor vehicle detection and violation statistics</p>
                </div>
                <button
                    onClick={fetchAnalytics}
                    className="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all card-hover shadow-lg"
                >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Refresh Data
                </button>
            </div>

            {/* Enhanced Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {stats.map((stat, index) => (
                    <div
                        key={stat.title}
                        className={`${stat.bgColor} rounded-xl p-6 glass-effect card-hover animate-fadeIn border border-gray-200 shadow-lg`}
                        style={{ animationDelay: `${index * 0.1}s` }}
                    >
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-gray-600 mb-1">{stat.title}</p>
                                <p className={`text-3xl font-bold ${stat.textColor}`}>{stat.value.toLocaleString()}</p>
                            </div>
                            <div className={`${stat.color} p-3 rounded-xl shadow-lg`}>
                                <stat.icon className="h-6 w-6 text-white" />
                            </div>
                        </div>
                        <div className="mt-4">
                            <div className={`h-2 bg-gray-200 rounded-full overflow-hidden`}>
                                <div
                                    className={`h-full ${stat.color} rounded-full animate-pulse`}
                                    style={{ width: `${Math.min((stat.value / 100) * 100, 100)}%` }}
                                ></div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {/* Enhanced Top Violators */}
            <div className="bg-white rounded-xl shadow-lg glass-effect border border-gray-200 p-8 card-hover">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                        🏆 Top Speed Violators
                    </h2>
                    <BarChart3 className="h-6 w-6 text-gray-400" />
                </div>

                {analytics?.top_violators && analytics.top_violators.length > 0 ? (
                    <div className="overflow-hidden rounded-lg border border-gray-200">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Rank
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        License Plate
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Max Speed (km/h)
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Violations
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Status
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {analytics.top_violators.map((violator, index) => (
                                    <tr
                                        key={violator.license_plate}
                                        className="hover:bg-gray-50 transition-colors animate-fadeIn"
                                        style={{ animationDelay: `${index * 0.1}s` }}
                                    >
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold text-white ${index === 0 ? 'bg-yellow-500' :
                                                        index === 1 ? 'bg-gray-400' :
                                                            index === 2 ? 'bg-orange-400' : 'bg-blue-500'
                                                    }`}>
                                                    {index + 1}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm font-bold text-gray-900 bg-gray-100 px-3 py-1 rounded-lg inline-block">
                                                {violator.license_plate}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm font-semibold text-red-600">
                                                {violator.max_speed.toFixed(1)} km/h
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                                {violator.violation_count} violations
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                                                ⚠️ High Risk
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="text-center py-12">
                        <BarChart3 className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                        <p className="text-gray-500 text-lg">No violation data available</p>
                        <p className="text-sm text-gray-400 mt-2">Process some videos to see analytics</p>
                    </div>
                )}
            </div>

            {/* Additional Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white rounded-xl shadow-lg glass-effect border border-gray-200 p-6 card-hover">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        📈 Detection Accuracy
                    </h3>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Vehicle Detection</span>
                            <span className="text-sm font-semibold text-green-600">94.5%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                            <div className="bg-green-500 h-2 rounded-full" style={{ width: '94.5%' }}></div>
                        </div>

                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">License Plate OCR</span>
                            <span className="text-sm font-semibold text-blue-600">89.2%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                            <div className="bg-blue-500 h-2 rounded-full" style={{ width: '89.2%' }}></div>
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-xl shadow-lg glass-effect border border-gray-200 p-6 card-hover">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        ⏱️ Processing Performance
                    </h3>
                    <div className="space-y-4">
                        <div>
                            <div className="flex justify-between items-center mb-1">
                                <span className="text-sm text-gray-600">Avg. Processing Time</span>
                                <span className="text-sm font-semibold text-purple-600">2.3 min/video</span>
                            </div>
                        </div>
                        <div>
                            <div className="flex justify-between items-center mb-1">
                                <span className="text-sm text-gray-600">System Load</span>
                                <span className="text-sm font-semibold text-orange-600">68%</span>
                            </div>
                            <div className="w-full bg-gray-200 rounded-full h-2">
                                <div className="bg-orange-500 h-2 rounded-full" style={{ width: '68%' }}></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Analytics;
