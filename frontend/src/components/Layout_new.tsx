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
        <div className="min-h-screen bg-gray-50 animate-fadeIn">
            {/* Header */}
            <header className="bg-white shadow-lg glass-effect border-b border-gray-200">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center h-16">
                        <div className="flex items-center">
                            <h1 className="text-xl font-semibold gradient-text animate-pulse">
                                🚗 Vehicle Detection Dashboard
                            </h1>
                        </div>
                    </div>
                </div>
            </header>

            <div className="flex">
                {/* Sidebar */}
                <nav className="w-64 bg-white shadow-lg glass-effect h-[calc(100vh-4rem)] border-r border-gray-200 animate-slideIn">
                    <div className="p-4">
                        <ul className="space-y-2">
                            {navItems.map((item, index) => (
                                <li key={item.to} style={{ animationDelay: `${index * 0.1}s` }} className="animate-fadeIn">
                                    <NavLink
                                        to={item.to}
                                        className={({ isActive }) =>
                                            `flex items-center px-4 py-3 text-sm font-medium rounded-xl transition-all card-hover ${isActive
                                                ? 'bg-blue-100 text-blue-700 shadow-lg transform scale-105 border-l-4 border-blue-500'
                                                : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900 hover:shadow-md hover:transform hover:scale-102'
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
                <main className="flex-1 p-6 bg-gray-50">
                    <div className="animate-fadeIn max-w-7xl mx-auto">
                        <Outlet />
                    </div>
                </main>
            </div>
        </div>
    );
};

export default Layout;
