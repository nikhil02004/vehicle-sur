import React, { useState, useEffect } from 'react';
import { getBlacklist, addToBlacklist, removeFromBlacklist } from '../services/api';
import { BlacklistEntry } from '../services/api';
import { Shield, Plus, Trash2, Search, AlertTriangle, CheckCircle } from 'lucide-react';

const BlacklistManager: React.FC = () => {
    const [blacklist, setBlacklist] = useState<BlacklistEntry[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [newPlate, setNewPlate] = useState('');
    const [newReason, setNewReason] = useState('');
    const [adding, setAdding] = useState(false);
    const [searchTerm, setSearchTerm] = useState('');
    const [showAddForm, setShowAddForm] = useState(false);

    const fetchBlacklist = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await getBlacklist();
            setBlacklist(data);
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to load blacklist');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchBlacklist();
    }, []);

    const handleAddToBlacklist = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newPlate.trim()) return;

        try {
            setAdding(true);
            setError(null);
            await addToBlacklist(newPlate.trim(), newReason.trim() || 'No reason provided');
            setNewPlate('');
            setNewReason('');
            setShowAddForm(false);
            await fetchBlacklist();
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to add to blacklist');
        } finally {
            setAdding(false);
        }
    };

    const handleRemoveFromBlacklist = async (licensePlate: string) => {
        if (!window.confirm(`Are you sure you want to remove "${licensePlate}" from the blacklist?`)) {
            return;
        }

        try {
            setError(null);
            await removeFromBlacklist(licensePlate);
            await fetchBlacklist();
        } catch (err: any) {
            setError(err.response?.data?.error || 'Failed to remove from blacklist');
        }
    };

    const filteredBlacklist = blacklist.filter(entry =>
        entry.license_plate.toLowerCase().includes(searchTerm.toLowerCase()) ||
        entry.reason.toLowerCase().includes(searchTerm.toLowerCase())
    );

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64 animate-fadeIn">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading blacklist...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-fadeIn">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold gradient-text flex items-center">
                        🛡️ Blacklist Manager
                    </h1>
                    <p className="text-gray-600 mt-2">Manage vehicles that are flagged for violations</p>
                </div>
                <button
                    onClick={() => setShowAddForm(!showAddForm)}
                    className="inline-flex items-center px-6 py-3 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-all card-hover shadow-lg"
                >
                    <Plus className="w-4 h-4 mr-2" />
                    Add Vehicle
                </button>
            </div>

            {/* Error Display */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-xl p-4 animate-fadeIn">
                    <div className="flex items-center">
                        <AlertTriangle className="h-5 w-5 text-red-500 mr-3" />
                        <p className="text-red-700 font-medium">{error}</p>
                    </div>
                </div>
            )}

            {/* Enhanced Add Form */}
            {showAddForm && (
                <div className="bg-white rounded-xl shadow-lg glass-effect border border-gray-200 p-8 animate-fadeIn">
                    <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center">
                        <Plus className="w-5 h-5 mr-2 text-red-600" />
                        Add Vehicle to Blacklist
                    </h2>
                    <form onSubmit={handleAddToBlacklist} className="space-y-6">
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                                <label htmlFor="licensePlate" className="block text-sm font-medium text-gray-700 mb-2">
                                    License Plate Number *
                                </label>
                                <input
                                    type="text"
                                    id="licensePlate"
                                    value={newPlate}
                                    onChange={(e) => setNewPlate(e.target.value.toUpperCase())}
                                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all font-mono text-center text-lg font-bold"
                                    placeholder="ABC-1234"
                                    required
                                />
                            </div>
                            <div>
                                <label htmlFor="reason" className="block text-sm font-medium text-gray-700 mb-2">
                                    Reason for Blacklisting
                                </label>
                                <input
                                    type="text"
                                    id="reason"
                                    value={newReason}
                                    onChange={(e) => setNewReason(e.target.value)}
                                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-all"
                                    placeholder="e.g., Multiple speeding violations"
                                />
                            </div>
                        </div>
                        <div className="flex space-x-4">
                            <button
                                type="submit"
                                disabled={adding || !newPlate.trim()}
                                className={`inline-flex items-center px-6 py-3 rounded-lg font-semibold transition-all card-hover ${adding || !newPlate.trim()
                                        ? 'bg-gray-400 text-white cursor-not-allowed'
                                        : 'bg-red-600 text-white hover:bg-red-700 shadow-lg'
                                    }`}
                            >
                                {adding ? (
                                    <>
                                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                        Adding...
                                    </>
                                ) : (
                                    <>
                                        <Shield className="w-4 h-4 mr-2" />
                                        Add to Blacklist
                                    </>
                                )}
                            </button>
                            <button
                                type="button"
                                onClick={() => setShowAddForm(false)}
                                className="px-6 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-all card-hover"
                            >
                                Cancel
                            </button>
                        </div>
                    </form>
                </div>
            )}

            {/* Search and Stats */}
            <div className="bg-white rounded-xl shadow-lg glass-effect border border-gray-200 p-6">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between space-y-4 md:space-y-0">
                    <div className="relative flex-1 max-w-md">
                        <Search className="absolute left-3 top-3 h-5 w-5 text-gray-400" />
                        <input
                            type="text"
                            placeholder="Search by license plate or reason..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-all"
                        />
                    </div>
                    <div className="flex items-center space-x-6">
                        <div className="text-center">
                            <p className="text-2xl font-bold text-red-600">{blacklist.length}</p>
                            <p className="text-sm text-gray-600">Total Blacklisted</p>
                        </div>
                        <div className="text-center">
                            <p className="text-2xl font-bold text-blue-600">{filteredBlacklist.length}</p>
                            <p className="text-sm text-gray-600">Filtered Results</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Enhanced Blacklist Table */}
            <div className="bg-white rounded-xl shadow-lg glass-effect border border-gray-200 overflow-hidden">
                {filteredBlacklist.length > 0 ? (
                    <div className="overflow-x-auto">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        License Plate
                                    </th>
                                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Reason
                                    </th>
                                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Date Added
                                    </th>
                                    <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Status
                                    </th>
                                    <th className="px-6 py-4 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {filteredBlacklist.map((entry, index) => (
                                    <tr
                                        key={entry.license_plate}
                                        className="hover:bg-gray-50 transition-colors animate-fadeIn"
                                        style={{ animationDelay: `${index * 0.1}s` }}
                                    >
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="flex items-center">
                                                <div className="bg-red-100 text-red-800 px-3 py-2 rounded-lg font-mono font-bold text-sm">
                                                    {entry.license_plate}
                                                </div>
                                            </div>
                                        </td>
                                        <td className="px-6 py-4">
                                            <div className="text-sm text-gray-900 max-w-xs">
                                                {entry.reason || 'No reason provided'}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <div className="text-sm text-gray-500">
                                                {new Date(entry.created_at).toLocaleDateString()}
                                            </div>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800">
                                                <AlertTriangle className="w-3 h-3 mr-1" />
                                                Blacklisted
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                            <button
                                                onClick={() => handleRemoveFromBlacklist(entry.license_plate)}
                                                className="inline-flex items-center px-3 py-2 text-red-600 hover:text-red-900 hover:bg-red-50 rounded-lg transition-all card-hover"
                                                title="Remove from blacklist"
                                            >
                                                <Trash2 className="h-4 w-4" />
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className="text-center py-12">
                        {searchTerm ? (
                            <>
                                <Search className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                                <p className="text-gray-500 text-lg">No vehicles found matching "{searchTerm}"</p>
                                <p className="text-sm text-gray-400 mt-2">Try adjusting your search terms</p>
                            </>
                        ) : (
                            <>
                                <CheckCircle className="mx-auto h-12 w-12 text-green-400 mb-4" />
                                <p className="text-gray-500 text-lg">No vehicles in blacklist</p>
                                <p className="text-sm text-gray-400 mt-2">Add vehicles that need to be flagged</p>
                            </>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default BlacklistManager;
