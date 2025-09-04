import React, { useState } from 'react';
import { setThreshold } from '../services/api';
import { Settings as SettingsIcon, Gauge, Save, CheckCircle, AlertTriangle, Activity, Shield, Zap } from 'lucide-react';

const Settings: React.FC = () => {
    const [speedThreshold, setSpeedThresholdState] = useState<number>(80); // Default 80 km/h
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();

        if (speedThreshold <= 0 || speedThreshold > 10000) {
            setError('Speed threshold must be between 1 and 10000 km/h');
            return;
        }

        try {
            setSaving(true);
            setError(null);
            setSuccess(null);
            await setThreshold({ threshold: speedThreshold });
            setSuccess(`Speed threshold updated to ${speedThreshold} km/h successfully!`);
            setTimeout(() => setSuccess(null), 3000);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to update speed threshold');
        } finally {
            setSaving(false);
        }
    };

    const presetThresholds = [
        { value: 30, label: 'School Zone (30 km/h)', icon: '🏫' },
        { value: 50, label: 'City Roads (50 km/h)', icon: '🏙️' },
        { value: 80, label: 'Highway (80 km/h)', icon: '🛣️' },
        { value: 120, label: 'Expressway (120 km/h)', icon: '🚗' },
        { value: 200, label: 'High Speed (200 km/h)', icon: '🏎️' },
    ];

    return (
        <div className="space-y-8 animate-fadeIn">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent flex items-center">
                    ⚙️ System Settings
                </h1>
                <p className="text-gray-600 mt-2">Configure speed detection thresholds and system preferences</p>
            </div>

            {/* Success Message */}
            {success && (
                <div className="bg-green-50 border border-green-200 rounded-xl p-4 animate-fadeIn">
                    <div className="flex items-center">
                        <CheckCircle className="h-5 w-5 text-green-500 mr-3" />
                        <p className="text-green-700 font-medium">{success}</p>
                    </div>
                </div>
            )}

            {/* Error Message */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-4 animate-fadeIn">
                    <div className="flex items-center">
                        <AlertTriangle className="h-5 w-5 text-red-500 mr-3" />
                        <p className="text-red-700 font-medium">{error}</p>
                    </div>
                </div>
            )}

            {/* Speed Threshold Configuration */}
            <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow-lg border border-white/20 p-8">
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-semibold text-gray-900 flex items-center">
                        <Gauge className="w-6 h-6 mr-3 text-blue-600" />
                        Speed Threshold Configuration
                    </h2>
                    <div className="flex items-center space-x-2 bg-blue-50 px-4 py-2 rounded-lg">
                        <Zap className="w-4 h-4 text-blue-600" />
                        <span className="text-sm font-medium text-blue-700">Current: {speedThreshold} km/h</span>
                    </div>
                </div>

                <form onSubmit={handleSave} className="space-y-6">
                    {/* Custom Threshold Input */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
                                <Activity className="w-4 h-4 mr-2" />
                                Custom Speed Threshold (km/h)
                            </label>
                            <input
                                type="number"
                                value={speedThreshold}
                                onChange={(e) => setSpeedThresholdState(Number(e.target.value))}
                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all duration-200 text-lg font-semibold text-center"
                                placeholder="80"
                                min="1"
                                max="10000"
                                required
                            />
                            <p className="text-xs text-gray-500 mt-1">
                                Enter a value between 1 and 10,000 km/h
                            </p>
                        </div>

                        {/* Current Status */}
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <h4 className="text-sm font-semibold text-blue-800 mb-2 flex items-center">
                                <Shield className="w-4 h-4 mr-2" />
                                Detection Status
                            </h4>
                            <div className="space-y-2">
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-blue-700">Current Threshold</span>
                                    <span className="text-sm font-bold text-blue-800">{speedThreshold} km/h</span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-blue-700">System Status</span>
                                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                        <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
                                        Active
                                    </span>
                                </div>
                                <div className="flex justify-between items-center">
                                    <span className="text-sm text-blue-700">Email Alerts</span>
                                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                        <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
                                        Enabled
                                    </span>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Preset Thresholds */}
                    <div>
                        <h4 className="text-lg font-semibold text-gray-900 mb-4">Quick Presets</h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {presetThresholds.map((preset) => (
                                <button
                                    key={preset.value}
                                    type="button"
                                    onClick={() => setSpeedThresholdState(preset.value)}
                                    className={`p-4 rounded-lg border-2 transition-all duration-200 hover:shadow-lg hover:-translate-y-1 ${speedThreshold === preset.value
                                            ? 'border-blue-500 bg-blue-50 shadow-md'
                                            : 'border-gray-200 bg-white hover:border-blue-300'
                                        }`}
                                >
                                    <div className="text-center">
                                        <div className="text-2xl mb-2">{preset.icon}</div>
                                        <div className="text-lg font-bold text-gray-900">{preset.value} km/h</div>
                                        <div className="text-sm text-gray-600">{preset.label}</div>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Save Button */}
                    <div className="flex justify-end">
                        <button
                            type="submit"
                            disabled={saving}
                            className={`inline-flex items-center px-8 py-3 rounded-xl font-semibold transition-all duration-300 shadow-lg ${saving
                                    ? 'bg-gray-400 text-white cursor-not-allowed'
                                    : 'bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white transform hover:scale-105 hover:shadow-xl'
                                }`}
                        >
                            {saving ? (
                                <>
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-3"></div>
                                    Updating...
                                </>
                            ) : (
                                <>
                                    <Save className="w-4 h-4 mr-3" />
                                    Update Threshold
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>

            {/* System Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow-lg border border-white/20 p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <SettingsIcon className="w-5 h-5 mr-2 text-green-600" />
                        System Status
                    </h3>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Detection Service</span>
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
                                Active
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Database</span>
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
                                Connected
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Email Alerts</span>
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
                                Configured
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">Speed Threshold</span>
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                {speedThreshold} km/h
                            </span>
                        </div>
                    </div>
                </div>

                <div className="bg-white/90 backdrop-blur-sm rounded-xl shadow-lg border border-white/20 p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <AlertTriangle className="w-5 h-5 mr-2 text-orange-600" />
                        Detection Info
                    </h3>
                    <div className="space-y-4">
                        <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                            <h4 className="text-sm font-semibold text-orange-800 mb-2">📧 Email Notifications</h4>
                            <p className="text-xs text-orange-700">
                                Email alerts are automatically configured in the backend.
                                Violations exceeding the speed threshold will trigger instant notifications.
                            </p>
                        </div>
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                            <h4 className="text-sm font-semibold text-blue-800 mb-2">🎯 Detection Accuracy</h4>
                            <p className="text-xs text-blue-700">
                                The system uses YOLO object detection and PaddleOCR for high-precision
                                vehicle identification and license plate recognition.
                            </p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Settings;
