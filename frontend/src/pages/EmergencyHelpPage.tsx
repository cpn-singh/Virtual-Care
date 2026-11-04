/**
 * Emergency Help & Nearby Emergency Facilities
 * Author: Clinical Safety & Emergency Response Team
 *
 * CRITICAL PATIENT SAFETY PAGE:
 * Available instantly without requiring user sign-in or payment.
 * Provides immediate click-to-call actions for National Emergency (112)
 * and Ambulance (108), followed by geolocation-assisted hospital discovery.
 */

import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Hospital } from '../types';
import {
  PhoneCall,
  AlertTriangle,
  MapPin,
  Navigation,
  Search,
  ExternalLink,
  ShieldAlert,
  Clock,
  Activity,
} from 'lucide-react';

export const EmergencyHelpPage: React.FC = () => {
  const [hospitals, setHospitals] = useState<Hospital[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [locationStatus, setLocationStatus] = useState<string>('');
  const [cityInput, setCityInput] = useState<string>('');
  const [errorMsg, setErrorMsg] = useState<string>('');

  const fetchHospitals = async (lat?: number | null, lon?: number | null, city?: string) => {
    setIsLoading(true);
    setErrorMsg('');
    try {
      const response: any = await api.hospitals.getNearby({
        latitude: lat,
        longitude: lon,
        city: city || undefined,
      });
      if (response?.data?.hospitals) {
        setHospitals(response.data.hospitals);
      }
    } catch (err: any) {
      setErrorMsg('Could not fetch hospital list. Please dial 112 immediately.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch of default verified emergency facilities
    fetchHospitals();
  }, []);

  const handleUseLocation = () => {
    if (!navigator.geolocation) {
      setLocationStatus('Geolocation is not supported by your browser. Please search by city below.');
      return;
    }

    setLocationStatus('Requesting GPS location...');
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setLocationStatus('Location detected! Sorting nearby emergency departments by distance.');
        fetchHospitals(pos.coords.latitude, pos.coords.longitude);
      },
      (err) => {
        setLocationStatus('Location access was denied or timed out. You can enter your city manually below.');
      },
      { timeout: 10000, enableHighAccuracy: true }
    );
  };

  const handleCitySearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!cityInput.trim()) return;
    fetchHospitals(null, null, cityInput.trim());
  };

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-10">
      {/* 1. Critical Emergency Alert Banner */}
      <div className="bg-red-700 text-white rounded-2xl p-6 sm:p-8 shadow-md space-y-6">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 rounded-xl bg-white/10 flex items-center justify-center shrink-0">
            <ShieldAlert className="w-7 h-7 text-amber-300" />
          </div>
          <div className="space-y-1">
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              Emergency Medical Guidance
            </h1>
            <p className="text-red-100 text-sm sm:text-base leading-relaxed">
              If you or someone near you has acute, life-threatening symptoms, <strong>do not wait</strong> for an
              online doctor consultation or chat. Contact emergency services right away.
            </p>
          </div>
        </div>

        {/* Large Touch Targets for Direct Dialing (>44px height) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <a
            href="tel:112"
            className="flex items-center justify-center gap-3 bg-white text-red-700 hover:bg-red-50 font-black text-lg py-4 px-6 rounded-xl transition shadow-md active:scale-98"
          >
            <PhoneCall className="w-6 h-6 text-red-600 animate-pulse" />
            <span>Call 112 (National Emergency)</span>
          </a>
          <a
            href="tel:108"
            className="flex items-center justify-center gap-3 bg-amber-400 text-slate-950 hover:bg-amber-300 font-black text-lg py-4 px-6 rounded-xl transition shadow-md active:scale-98"
          >
            <PhoneCall className="w-6 h-6 text-slate-900" />
            <span>Call 108 (Ambulance Service)</span>
          </a>
        </div>

        <p className="text-xs text-red-200 text-center">
          * Note: Virtual Care does not automatically dispatch an ambulance. Dialing the numbers above connects directly
          to public emergency dispatchers.
        </p>
      </div>

      {/* 2. Red-Flag Symptoms Checker */}
      <section className="bg-amber-50 border border-amber-200 rounded-xl p-6 space-y-4">
        <div className="flex items-center gap-2 text-amber-900 font-bold text-base">
          <AlertTriangle className="w-5 h-5 text-amber-600" />
          <span>When should you seek immediate emergency care?</span>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs text-amber-950">
          <div className="flex items-start gap-2 bg-white/70 p-3 rounded-lg border border-amber-200/60">
            <Activity className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <span>
              <strong>Heart Attack Symptoms:</strong> Severe, crushing chest pain radiating to left arm, back, or jaw.
            </span>
          </div>
          <div className="flex items-start gap-2 bg-white/70 p-3 rounded-lg border border-amber-200/60">
            <Activity className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <span>
              <strong>Stroke Signs:</strong> Sudden facial drooping, arm weakness, or slurred, unintelligible speech.
            </span>
          </div>
          <div className="flex items-start gap-2 bg-white/70 p-3 rounded-lg border border-amber-200/60">
            <Activity className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <span>
              <strong>Respiratory Failure:</strong> Gasping for breath, inability to speak full sentences, choking.
            </span>
          </div>
          <div className="flex items-start gap-2 bg-white/70 p-3 rounded-lg border border-amber-200/60">
            <Activity className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />
            <span>
              <strong>Severe Trauma:</strong> Heavy uncontrolled bleeding, suspected poisoning, or sudden unresponsiveness.
            </span>
          </div>
        </div>
      </section>

      {/* 3. Nearby Emergency Hospitals Finder */}
      <section className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <MapPin className="w-5 h-5 text-teal-600" />
              Verified 24/7 Emergency Hospitals
            </h2>
            <p className="text-xs text-slate-600">
              Locate nearby physical hospitals with 24-hour trauma units and emergency departments.
            </p>
          </div>

          <button
            onClick={handleUseLocation}
            className="inline-flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs px-4 py-2.5 rounded-lg transition shadow-xs"
          >
            <Navigation className="w-4 h-4" />
            <span>Use My GPS Location</span>
          </button>
        </div>

        {locationStatus && (
          <div className="text-xs font-medium text-teal-800 bg-teal-50 border border-teal-200 p-3 rounded-lg">
            {locationStatus}
          </div>
        )}

        {/* Manual City Search Fallback */}
        <form onSubmit={handleCitySearch} className="flex gap-2 max-w-md">
          <input
            type="text"
            placeholder="Search by city (e.g. Mumbai, Delhi, Bengaluru)..."
            value={cityInput}
            onChange={(e) => setCityInput(e.target.value)}
            className="flex-1 text-sm border border-slate-300 rounded-lg px-3.5 py-2 focus:outline-none focus:ring-2 focus:ring-teal-500"
          />
          <button
            type="submit"
            className="bg-slate-800 hover:bg-slate-900 text-white font-semibold text-xs px-4 py-2 rounded-lg transition flex items-center gap-1.5"
          >
            <Search className="w-3.5 h-3.5" />
            <span>Search</span>
          </button>
        </form>

        {errorMsg && (
          <div className="bg-red-50 text-red-700 p-3 rounded-lg text-xs font-semibold">{errorMsg}</div>
        )}

        {/* Hospitals List */}
        {isLoading ? (
          <div className="text-center py-12 text-slate-500 text-sm">Locating emergency hospitals...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {hospitals.map((h) => (
              <div
                key={h.id}
                className="bg-white border border-slate-200 rounded-xl p-5 shadow-xs space-y-4 flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-bold text-slate-900 text-base">{h.name}</h3>
                    {h.distance_km !== undefined && h.distance_km < 900 && (
                      <span className="bg-teal-50 text-teal-800 text-[11px] font-bold px-2 py-0.5 rounded-full shrink-0 border border-teal-200">
                        {h.distance_km} km away
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{h.address}, {h.city}</p>

                  <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px]">
                    <span className="inline-flex items-center gap-1 text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded font-semibold border border-emerald-200">
                      <Clock className="w-3 h-3" /> 24/7 Emergency
                    </span>
                    {h.has_trauma_center && (
                      <span className="text-slate-700 bg-slate-100 px-2 py-0.5 rounded font-medium">
                        Trauma Centre
                      </span>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-100">
                  <a
                    href={`tel:${h.emergency_phone || h.phone_number}`}
                    className="flex items-center justify-center gap-1.5 bg-red-50 hover:bg-red-100 text-red-700 font-bold text-xs py-2 rounded-lg transition border border-red-200"
                  >
                    <PhoneCall className="w-3.5 h-3.5" />
                    <span>Call ER</span>
                  </a>
                  {h.directions_link && (
                    <a
                      href={h.directions_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center justify-center gap-1.5 bg-slate-50 hover:bg-slate-100 text-slate-700 font-semibold text-xs py-2 rounded-lg transition border border-slate-200"
                    >
                      <ExternalLink className="w-3.5 h-3.5" />
                      <span>Directions</span>
                    </a>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
