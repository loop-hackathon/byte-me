import React, { useState } from 'react';
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { User, LogOut } from 'lucide-react';

export default function MainLayout() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [showProfileMenu, setShowProfileMenu] = useState(false);

  const navigation = [
    { name: 'Overview', path: '/dashboard' },
    { name: 'Cost', path: '/dashboard/cost' },
    { name: 'Resource Efficiency', path: '/dashboard/efficiency' },
    { name: 'App Health', path: '/dashboard/health' },
    { name: 'Incidents', path: '/dashboard/incidents' },
    { name: 'Releases', path: '/dashboard/releases' },
  ];

  const isActive = (path: string) => {
    if (path === '/dashboard') {
      return location.pathname === '/dashboard';
    }
    return location.pathname.startsWith(path);
  };

  const getUserInitials = () => {
    if (user?.name) {
      return user.name
        .split(' ')
        .map(n => n[0])
        .join('')
        .toUpperCase()
        .slice(0, 2);
    }
    return user?.email?.[0]?.toUpperCase() || 'U';
  };

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-[#020204] text-slate-300">
      {/* Background Effects */}
      <div className="fixed inset-0 z-[-1] overflow-hidden pointer-events-none">
        <div className="absolute top-[-10%] left-1/2 -translate-x-1/2 w-[120%] h-[800px] bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-blue-900/20 via-[#020204]/80 to-transparent blur-[80px]"></div>
      </div>

      {/* Navigation Bar */}
      <nav className="fixed top-0 z-50 w-full border-b border-white/5 bg-[#030508]/60 backdrop-blur-xl">
        <div className="flex max-w-7xl mx-auto px-6 py-4 items-center justify-between">
          {/* Logo */}
          <Link to="/dashboard" className="flex items-center gap-2 group">
            <div className="flex text-xs font-bold text-black bg-gradient-to-br from-cyan-400 to-blue-600 w-8 h-8 rounded items-center justify-center">
              C
            </div>
            <span className="text-sm font-semibold text-white tracking-tight">CloudHelm</span>
          </Link>

          {/* Navigation Links */}
          <div className="hidden md:flex items-center gap-6">
            {navigation.map((item) => (
              <Link
                key={item.path}
                to={item.path}
                className={`text-sm font-medium transition-colors ${
                  isActive(item.path)
                    ? 'text-cyan-400'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {item.name}
              </Link>
            ))}
          </div>

          {/* Profile Menu */}
          <div className="relative">
            <button
              onClick={() => setShowProfileMenu(!showProfileMenu)}
              className="w-10 h-10 rounded-full bg-gradient-to-br from-cyan-400 to-blue-600 text-white flex items-center justify-center font-medium hover:shadow-[0_0_20px_rgba(34,211,238,0.4)] transition-all"
            >
              {getUserInitials()}
            </button>

            {/* Dropdown Menu */}
            {showProfileMenu && (
              <>
                {/* Backdrop */}
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setShowProfileMenu(false)}
                ></div>

                {/* Menu */}
                <div className="absolute right-0 mt-2 w-56 bg-[#030508]/95 backdrop-blur-xl border border-white/10 rounded-lg shadow-xl z-50 overflow-hidden">
                  {/* User Info */}
                  <div className="px-4 py-3 border-b border-white/5">
                    <p className="text-sm font-medium text-slate-100 truncate">
                      {user?.name || user?.email || 'User'}
                    </p>
                    <p className="text-xs text-slate-500 capitalize mt-0.5">
                      {user?.provider || 'Account'}
                    </p>
                  </div>

                  {/* Menu Items */}
                  <div className="py-1">
                    <button
                      onClick={() => {
                        setShowProfileMenu(false);
                        // Navigate to profile page when implemented
                      }}
                      className="w-full flex items-center gap-3 px-4 py-2 text-sm text-slate-400 hover:text-slate-100 hover:bg-white/5 transition-colors"
                    >
                      <User className="w-4 h-4" />
                      Profile
                    </button>
                    <button
                      onClick={handleLogout}
                      className="w-full flex items-center gap-3 px-4 py-2 text-sm text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      Sign Out
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="pt-16">
        <Outlet />
      </div>
    </div>
  );
}
