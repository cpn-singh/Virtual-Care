/**
 * User Registration Page
 * Author: Security & Frontend Team
 *
 * Captures name, email, password, and role selection.
 * Automatically initiates the 6-digit email OTP verification process.
 */

import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { ArrowRight } from 'lucide-react';

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    email: '',
    phoneNumber: '',
    password: '',
  });
  const [errorMsg, setErrorMsg] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');
    setIsLoading(true);

    try {
      await api.auth.register({
        first_name: formData.firstName,
        last_name: formData.lastName,
        email: formData.email,
        phone_number: formData.phoneNumber,
        password: formData.password,
        role: 'patient',
      });

      // Redirect immediately to OTP verification screen with email in query parameter
      navigate(`/verify-otp?email=${encodeURIComponent(formData.email.trim().toLowerCase())}`);
    } catch (err: any) {
      const detail = err.errors?.email?.[0] || err.errors?.password?.[0] || err.message;
      setErrorMsg(detail || 'Registration could not be completed. Please review your details.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-12">
      <div className="bg-white border border-slate-200 rounded-3xl p-8 shadow-sm space-y-6">
        <div className="text-center space-y-2">
          <div className="w-12 h-12 bg-teal-600 rounded-2xl flex items-center justify-center text-white mx-auto shadow-sm overflow-hidden p-1.5">
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
          <h1 className="text-2xl font-bold text-slate-900">Create your account</h1>
          <p className="text-xs text-slate-500">
            Join Care Connect to connect with doctors and manage your clinical consultations.
          </p>
        </div>

        {errorMsg && (
          <div className="bg-red-50 text-red-700 p-3 rounded-xl text-xs font-semibold">{errorMsg}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="bg-teal-50/70 border border-teal-200/70 rounded-xl p-3 text-xs text-teal-900 flex items-center justify-between">
            <span className="font-semibold">Patient Account Registration</span>
            <span className="text-[10px] bg-teal-200/60 text-teal-800 font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">
              Patients Only
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">First Name</label>
              <input
                type="text"
                required
                value={formData.firstName}
                onChange={(e) => setFormData({ ...formData, firstName: e.target.value })}
                className="w-full text-xs border border-slate-300 rounded-xl p-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500"
                placeholder="Aarav"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Last Name</label>
              <input
                type="text"
                required
                value={formData.lastName}
                onChange={(e) => setFormData({ ...formData, lastName: e.target.value })}
                className="w-full text-xs border border-slate-300 rounded-xl p-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500"
                placeholder="Mehta"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Email Address</label>
            <input
              type="email"
              required
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full text-xs border border-slate-300 rounded-xl p-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500"
              placeholder="name@example.com"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Mobile Phone (Optional)</label>
            <input
              type="tel"
              value={formData.phoneNumber}
              onChange={(e) => setFormData({ ...formData, phoneNumber: e.target.value })}
              className="w-full text-xs border border-slate-300 rounded-xl p-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500"
              placeholder="+91 98765 43210"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Password</label>
            <input
              type="password"
              required
              minLength={8}
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full text-xs border border-slate-300 rounded-xl p-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500"
              placeholder="Minimum 8 characters"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-teal-600 hover:bg-teal-700 disabled:bg-slate-300 text-white font-bold py-3 rounded-xl transition text-sm flex items-center justify-center gap-2 shadow-xs"
          >
            <span>{isLoading ? 'Creating Account...' : 'Continue to Email Verification'}</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </form>

        <div className="pt-2 text-center text-xs text-slate-600 space-y-2">
          <div>
            Already have an account?{' '}
            <Link to="/login" className="text-teal-700 font-bold hover:underline">
              Sign In
            </Link>
          </div>
          <div className="pt-2 border-t border-slate-100 text-[11px] text-slate-500">
            Healthcare Practitioner? Clinician profiles are provisioned directly by Platform Administrators.
          </div>
        </div>
      </div>
    </div>
  );
};
