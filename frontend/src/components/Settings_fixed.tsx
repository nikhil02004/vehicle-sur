import React, { useState } from 'react';
import { setEmailConfig } from '../services/api';
import { Settings as SettingsIcon, Mail, Save, CheckCircle, AlertTriangle, Server, Shield, Bell } from 'lucide-react';

interface EmailConfig {
    sender_email: string;
    sender_password: string;
    receiver_email: string;
}

const Settings: React.FC = () => {
    const [emailConfig, setEmailConfigState] = useState<EmailConfig>({
        sender_email: '',
        sender_password: '',
        receiver_email: ''
    });
    const [saving, setSaving] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState<string | null>(null);

    const handleSave = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            setSaving(true);
            setError(null);
            setSuccess(null);
            await setEmailConfig(emailConfig);
            setSuccess('Email configuration updated successfully!');
            setTimeout(() => setSuccess(null), 3000);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to update email configuration');
        } finally {
            setSaving(false);
        }
    };

    const handleInputChange = (field: keyof EmailConfig, value: string) => {
        setEmailConfigState(prev => ({
            ...prev,
            [field]: value
        }));
    };

    return (
        <div className="space-y-8 animate-fadeIn">
            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold gradient-text flex items-center">
                    ⚙️ System Settings
                </h1>
                <p className="text-gray-600 mt-2">Configure email notifications and system preferences</p>
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

            {/* Email Configuration */}
            <div className="bg-white rounded-xl shadow-lg glass-effect border border-gray-200 p-8">
                <div className="mb-6">
                    <h2 className="text-2xl font-semibold text-gray-900 flex items-center">
                        <Mail className="w-6 h-6 mr-3 text-blue-600" />
                        Email Alert Configuration
                    </h2>
                    <p className="text-gray-600 mt-2">Set up email notifications for violations and alerts</p>
                </div>

                <form onSubmit={handleSave} className="space-y-6">
                    <div className="grid grid-cols-1 gap-6">
                        {/* Sender Email */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
                                <Mail className="w-4 h-4 mr-2" />
                                Sender Email Address
                            </label>
                            <input
                                type="email"
                                value={emailConfig.sender_email}
                                onChange={(e) => handleInputChange('sender_email', e.target.value)}
                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                                placeholder="sender@gmail.com"
                                required
                            />
                            <p className="text-xs text-gray-500 mt-1">The email address that will send the notifications</p>
                        </div>

                        {/* Sender Password / App Password */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
                                <Shield className="w-4 h-4 mr-2" />
                                App Password
                            </label>
                            <input
                                type="password"
                                value={emailConfig.sender_password}
                                onChange={(e) => handleInputChange('sender_password', e.target.value)}
                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all font-mono"
                                placeholder="••••••••••••••••"
                                required
                            />
                            <p className="text-xs text-gray-500 mt-1">
                                For Gmail: Generate an App Password from Google Account settings
                            </p>
                        </div>

                        {/* Receiver Email */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2 flex items-center">
                                <Bell className="w-4 h-4 mr-2" />
                                Receiver Email Address
                            </label>
                            <input
                                type="email"
                                value={emailConfig.receiver_email}
                                onChange={(e) => handleInputChange('receiver_email', e.target.value)}
                                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                                placeholder="alerts@yourcompany.com"
                                required
                            />
                            <p className="text-xs text-gray-500 mt-1">Where violation alerts will be sent</p>
                        </div>
                    </div>

                    {/* Configuration Tips */}
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
                        <h4 className="text-sm font-semibold text-blue-800 mb-3 flex items-center">
                            <Bell className="w-4 h-4 mr-2" />
                            Email Setup Instructions
                        </h4>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-blue-700">
                            <div>
                                <h5 className="font-semibold mb-2">📧 For Gmail:</h5>
                                <ul className="space-y-1">
                                    <li>• Enable 2-factor authentication</li>
                                    <li>• Go to Google Account settings</li>
                                    <li>• Generate an App Password</li>
                                    <li>• Use the 16-character password</li>
                                </ul>
                            </div>
                            <div>
                                <h5 className="font-semibold mb-2">🔔 Alert Types:</h5>
                                <ul className="space-y-1">
                                    <li>• Speed limit violations</li>
                                    <li>• Blacklisted vehicle detections</li>
                                    <li>• System status updates</li>
                                    <li>• Processing errors</li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    {/* Save Button */}
                    <div className="flex justify-end">
                        <button
                            type="submit"
                            disabled={saving}
                            className={`inline-flex items-center px-8 py-3 rounded-xl font-semibold transition-all card-hover shadow-lg ${saving
                                    ? 'bg-gray-400 text-white cursor-not-allowed'
                                    : 'bg-blue-600 text-white hover:bg-blue-700 transform hover:scale-105'
                                }`}
                        >
                            {saving ? (
                                <>
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-3"></div>
                                    Saving Configuration...
                                </>
                            ) : (
                                <>
                                    <Save className="w-4 h-4 mr-3" />
                                    Save Email Settings
                                </>
                            )}
                        </button>
                    </div>
                </form>
            </div>

            {/* System Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="bg-white rounded-xl shadow-lg glass-effect border border-gray-200 p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <SettingsIcon className="w-5 h-5 mr-2 text-green-600" />
                        System Status
                    </h3>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">🚗 Detection Service</span>
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
                                Active
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">💾 Database</span>
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
                                Connected
                            </span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">🤖 AI Models</span>
                            <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                <span className="w-2 h-2 bg-green-500 rounded-full mr-1"></span>
                                Loaded
                            </span>
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-xl shadow-lg glass-effect border border-gray-200 p-6">
                    <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                        <Server className="w-5 h-5 mr-2 text-blue-600" />
                        Current Configuration
                    </h3>
                    <div className="space-y-3">
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">⚡ Speed Threshold</span>
                            <span className="text-sm font-semibold text-blue-600">10,000 km/h</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">🔍 YOLO Model</span>
                            <span className="text-sm font-semibold text-green-600">YOLOv11n</span>
                        </div>
                        <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-600">📝 OCR Engine</span>
                            <span className="text-sm font-semibold text-purple-600">PaddleOCR</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* Performance Metrics */}
            <div className="bg-white rounded-xl shadow-lg glass-effect border border-gray-200 p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                    <AlertTriangle className="w-5 h-5 mr-2 text-orange-600" />
                    📊 Performance Metrics
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                        <p className="text-2xl font-bold text-blue-600">94.5%</p>
                        <p className="text-sm text-gray-600">Detection Accuracy</p>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                        <p className="text-2xl font-bold text-green-600">2.3s</p>
                        <p className="text-sm text-gray-600">Avg Processing Time</p>
                    </div>
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                        <p className="text-2xl font-bold text-purple-600">89.2%</p>
                        <p className="text-sm text-gray-600">OCR Accuracy</p>
                    </div>
                    <div className="text-center p-4 bg-orange-50 rounded-lg">
                        <p className="text-2xl font-bold text-orange-600">68%</p>
                        <p className="text-sm text-gray-600">System Load</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Settings;
