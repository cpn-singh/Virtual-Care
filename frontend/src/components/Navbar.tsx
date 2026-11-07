/**
 * Primary Application Navbar
 * Maintained by the Frontend Engineering Team.
 *
 * Accessible, responsive, with prominent emergency access and role-aware navigation.
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Menu,
  X,
  User as UserIcon,
  LogOut,
  Calendar,
  FileText,
  AlertCircle,
  MessageSquare,
  Stethoscope,
  Receipt,
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleSignOut = () => {
    logout();
    navigate('/');
  };

  const getDashboardPath = () => {
    if (!user) return '/login';
    if (user.role === 'doctor') return '/doctor/dashboard';
    if (user.role === 'admin') return '/admin/dashboard';
    return '/patient/dashboard';
  };

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-10 h-10 rounded-xl bg-teal-600 flex items-center justify-center text-white shadow-sm group-hover:bg-teal-700 transition overflow-hidden">
              <img
                src="/logo.png"
                alt="Care Connect Logo"
                className="w-full h-full object-cover"
                onError={(e) => {
                  if (e.currentTarget.src.endsWith('/logo.png')) {
                    e.currentTarget.src = '/logo.svg';
                  } else {
                    (e.currentTarget as HTMLElement).style.display = 'none';
                  }
                }}
              />
            </div>
            <div>
              <span className="text-lg font-bold text-slate-900 tracking-tight">Care Connect</span>
              <span className="block text-[10px] font-medium text-teal-700 tracking-wide uppercase">
                Telemedicine Platform
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-6" aria-label="Main Navigation">
            <Link
              to="/doctors"
              className="text-sm font-medium text-slate-600 hover:text-teal-700 transition flex items-center gap-1.5"
            >
              <Stethoscope className="w-4 h-4 text-slate-400" />
              Find a Doctor
            </Link>
            <Link
              to="/ai-care"
              className="text-sm font-medium text-slate-600 hover:text-teal-700 transition flex items-center gap-1.5"
            >
              <MessageSquare className="w-4 h-4 text-teal-600" />
              AI Care Assistant
            </Link>
            <Link
              to="/how-it-works"
              className="text-sm font-medium text-slate-600 hover:text-teal-700 transition"
            >
              How It Works
            </Link>

            {/* Emergency Action */}
            <Link
              to="/emergency"
              className="inline-flex items-center gap-1.5 bg-red-50 text-red-700 hover:bg-red-100 border border-red-200 text-xs font-semibold px-3 py-1.5 rounded-full transition shadow-xs"
            >
              <AlertCircle className="w-3.5 h-3.5 text-red-600" />
              Emergency Help
            </Link>
          </nav>

          {/* Desktop User Actions */}
          <div className="hidden md:flex items-center gap-3">
            {user ? (
              <div className="flex items-center gap-3">
                <Link
                  to={getDashboardPath()}
                  className="inline-flex items-center gap-2 text-sm font-semibold text-slate-700 hover:text-teal-700 bg-slate-50 hover:bg-slate-100 px-3.5 py-2 rounded-lg border border-slate-200 transition"
                >
                  <UserIcon className="w-4 h-4 text-teal-600" />
                  <span>{user.first_name || 'My Portal'}</span>
                </Link>

                {user.role === 'patient' && (
                  <>
                    <Link
                      to="/appointments"
                      title="Appointments"
                      className="p-2 text-slate-600 hover:text-teal-700 hover:bg-slate-100 rounded-lg transition"
                    >
                      <Calendar className="w-4 h-4" />
                    </Link>
                    <Link
                      to="/prescriptions"
                      title="Prescriptions"
                      className="p-2 text-slate-600 hover:text-teal-700 hover:bg-slate-100 rounded-lg transition"
                    >
                      <FileText className="w-4 h-4" />
                    </Link>
                    <Link
                      to="/invoices"
                      title="Billing"
                      className="p-2 text-slate-600 hover:text-teal-700 hover:bg-slate-100 rounded-lg transition"
                    >
                      <Receipt className="w-4 h-4" />
                    </Link>
                  </>
                )}

                <button
                  onClick={handleSignOut}
                  title="Sign out"
                  className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="text-sm font-medium text-slate-700 hover:text-teal-700 px-3 py-2 rounded-lg transition"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="bg-teal-600 hover:bg-teal-700 text-white text-sm font-semibold px-4 py-2 rounded-lg transition shadow-xs"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex md:hidden items-center gap-2">
            <Link
              to="/emergency"
              className="bg-red-600 text-white text-xs font-bold px-2.5 py-1 rounded-md"
            >
              Urgent
            </Link>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-lg text-slate-700 hover:bg-slate-100"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-slate-200 bg-white px-4 pt-2 pb-6 space-y-3">
          <Link
            to="/emergency"
            onClick={() => setMobileMenuOpen(false)}
            className="flex items-center gap-2 bg-red-50 text-red-700 font-bold px-3 py-2.5 rounded-lg border border-red-200 text-sm"
          >
            <AlertCircle className="w-4 h-4 text-red-600" />
            I Need Urgent Emergency Help (112)
          </Link>

          <Link
            to="/doctors"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-md text-base font-medium text-slate-700 hover:bg-slate-50"
          >
            Find a Doctor
          </Link>
          <Link
            to="/ai-care"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-md text-base font-medium text-teal-700 hover:bg-teal-50"
          >
            AI Care Assistant
          </Link>
          <Link
            to="/how-it-works"
            onClick={() => setMobileMenuOpen(false)}
            className="block px-3 py-2 rounded-md text-base font-medium text-slate-700 hover:bg-slate-50"
          >
            How It Works
          </Link>

          <div className="pt-3 border-t border-slate-100">
            {user ? (
              <div className="space-y-2">
                <Link
                  to={getDashboardPath()}
                  onClick={() => setMobileMenuOpen(false)}
                  className="block w-full text-center bg-teal-600 text-white font-semibold py-2 rounded-lg text-sm"
                >
                  My Dashboard ({user.first_name || 'Account'})
                </Link>
                {user.role === 'patient' && (
                  <div className="grid grid-cols-3 gap-2 text-center text-xs text-slate-700">
                    <Link
                      to="/appointments"
                      onClick={() => setMobileMenuOpen(false)}
                      className="p-2 border rounded-md hover:bg-slate-50"
                    >
                      Appointments
                    </Link>
                    <Link
                      to="/prescriptions"
                      onClick={() => setMobileMenuOpen(false)}
                      className="p-2 border rounded-md hover:bg-slate-50"
                    >
                      Prescriptions
                    </Link>
                    <Link
                      to="/invoices"
                      onClick={() => setMobileMenuOpen(false)}
                      className="p-2 border rounded-md hover:bg-slate-50"
                    >
                      Billing
                    </Link>
                  </div>
                )}
                <button
                  onClick={() => {
                    handleSignOut();
                    setMobileMenuOpen(false);
                  }}
                  className="block w-full text-center text-red-600 hover:bg-red-50 font-medium py-2 rounded-lg text-sm border border-red-200 mt-2"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2">
                <Link
                  to="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block text-center border border-slate-300 text-slate-700 font-medium py-2 rounded-lg text-sm"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  onClick={() => setMobileMenuOpen(false)}
                  className="block text-center bg-teal-600 text-white font-semibold py-2 rounded-lg text-sm"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
};
