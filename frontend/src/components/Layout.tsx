import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { Upload, BarChart3, Settings, AlertTriangle } from 'lucide-react';

const Layout: React.FC = () => {
    const navItems = [
        { to: '/', icon: Upload, label: 'Upload Video' },
        { to: '/analytics', icon: BarChart3, label: 'Analytics' },
        { to: '/blacklist', icon: AlertTriangle, label: 'Blacklist' },
        { to: '/settings', icon: Settings, label: 'Settings' },
    ];

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 animate-fadeIn">
            {/* Header */}
            <header className="bg-white/80 backdrop-blur-sm shadow-lg border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        <div className="flex items-center">
                            <h1 className="text-xl font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                                🚗 Vehicle Detection Dashboard
                            </h1>
                        </div>
                    </div>
                </div>
            </header>

            <div className="flex">
                {/* Sidebar */}
                <nav className="w-64 bg-white/80 backdrop-blur-sm shadow-lg h-[calc(100vh-4rem)] border-r border-gray-200 animate-slideIn">
                    <div className="p-4">
                        <ul className="space-y-2">
                            {navItems.map((item, index) => (
                                <li key={item.to} style={{ animationDelay: `${index * 0.1}s` }} className="animate-fadeIn">
                                    <NavLink
                                        to={item.to}
                                        className={({ isActive }) =>
                                            `flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all duration-300 hover:shadow-lg hover:-translate-y-1 ${isActive
                                                ? 'bg-blue-100 text-blue-700 shadow-md transform scale-105 border-l-4 border-blue-500'
                                                : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 hover:shadow-md'
                                            }`
                                        }
                                    >
                                        <item.icon className="mr-3 h-5 w-5" />
                                        {item.label}
                                    </NavLink>
                                </li>
                            ))}
                        </ul>
                    </div>
                </nav>

                {/* Main Content */}
                <main className="flex-1 p-6 bg-gradient-to-br from-blue-50 to-indigo-100">
                    <div className="animate-fadeIn max-w-7xl mx-auto">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    );
};

export default Layout;
