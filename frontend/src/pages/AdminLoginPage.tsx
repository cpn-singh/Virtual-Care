/**
 * Dedicated Platform Administration Sign In Page
 * Author: Platform Operations & Security Team
 *
 * Route: /admin and /admin/login
 * Restricted gateway for system administrators to manage clinical credentialing,
 * doctor verification, and platform governance.
 */

import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, Lock, ArrowRight, AlertCircle, ArrowLeft } from 'lucide-react';

export const AdminLoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  // If already authenticated as admin, jump straight to the dashboard
  useEffect(() => {
    if (user && user.role === 'admin') {
      navigate('/admin/dashboard', { replace: true });
    }
  }, [user, navigate]);

  const handleAdminLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setIsLoading(true);

    try {
      const response: any = await api.auth.login({
        email: email.trim().toLowerCase(),
        password: password,
      });

      if (response?.data?.token && response?.data?.user) {
        const loggedUser = response.data.user;
        if (loggedUser.role !== 'admin') {
          setErrorMsg('Access Denied: This portal requires Platform Administrator credentials.');
          return;
        }

        login(response.data.token, loggedUser);
        navigate('/admin/dashboard', { replace: true });
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Invalid administrator email or password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[82vh] flex items-center justify-center px-4 py-12 bg-slate-900/5">
      <div className="w-full max-w-md bg-white border border-slate-200 rounded-3xl p-8 shadow-sm space-y-6">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="w-14 h-14 bg-slate-900 text-teal-400 rounded-2xl flex items-center justify-center mx-auto shadow-sm border border-slate-800">
            <ShieldCheck className="w-7 h-7" />
          </div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Admin Portal Sign In</h1>
          <p className="text-xs text-slate-500 leading-relaxed">
            Restricted access gateway for platform administrators.
          </p>
        </div>

        {/* Security Warning Notice */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-2xl p-3.5 text-xs text-slate-600 flex items-center gap-2.5">
          <Lock className="w-4 h-4 text-slate-500 shrink-0" />
          <span className="text-[11px] leading-relaxed">
            Authorized Personnel Only. All access attempts and administrative operations are cryptographically audited.
          </span>
        </div>

        {errorMsg && (
          <div className="bg-red-50 text-red-700 border border-red-200 p-3 rounded-xl text-xs font-semibold flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleAdminLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Administrator Email</label>
            <input
              type="email"
              required
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-teal-500 font-mono"
              placeholder="admin@example.com"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full text-xs border border-slate-300 rounded-xl p-3 focus:outline-none focus:ring-2 focus:ring-teal-500 font-mono"
              placeholder="Enter admin password"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-slate-900 hover:bg-slate-800 disabled:bg-slate-400 text-white font-bold py-3.5 rounded-xl transition text-xs flex items-center justify-center gap-2 shadow-xs cursor-pointer"
          >
            <Lock className="w-4 h-4 text-teal-400" />
            <span>{isLoading ? 'Authenticating Admin...' : 'Authenticate & Enter Dashboard'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        {/* Footer Navigation */}
        <div className="pt-2 text-center text-xs text-slate-500 border-t border-slate-100 flex items-center justify-between">
          <Link to="/" className="text-slate-600 hover:text-teal-700 flex items-center gap-1 transition">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Patient Home</span>
          </Link>
          <Link to="/login" className="text-teal-700 font-bold hover:underline">
            General Sign In
          </Link>
        </div>
      </div>
    </div>
  );
};
