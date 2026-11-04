/**
 * Global Footer Component
 * Author: Frontend Engineering Team
 *
 * Emphasizes clinical disclaimers, emergency helplines, and transparency.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { HeartPulse, Phone, ShieldCheck, MapPin } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-300 pt-12 pb-8 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 pb-10 border-b border-slate-800">
          {/* Col 1: Brand & Purpose */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-teal-500 flex items-center justify-center text-slate-950 font-bold">
                <HeartPulse className="w-5 h-5 text-slate-900" />
              </div>
              <span className="text-lg font-bold text-white tracking-tight">VirtualCare</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed">
              Safe, accessible telemedicine bridging patients with verified clinicians.
              Equipped with an intelligent safety triage layer that never compromises on emergency escalation.
            </p>
            <div className="flex items-center gap-2 text-xs text-teal-400 font-medium">
              <ShieldCheck className="w-4 h-4" />
              <span>Telemedicine Practice Compliant</span>
            </div>
          </div>

          {/* Col 2: Patient Navigation */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-3">Quick Navigation</h4>
            <ul className="space-y-2 text-xs">
              <li>
                <Link to="/doctors" className="hover:text-white transition">
                  Find Verified Doctors
                </Link>
              </li>
              <li>
                <Link to="/ai-care" className="hover:text-white transition">
                  AI Symptom Care Assistant
                </Link>
              </li>
              <li>
                <Link to="/emergency" className="hover:text-white transition text-red-400 font-semibold">
                  Emergency Help & ER Directory
                </Link>
              </li>
              <li>
                <Link to="/how-it-works" className="hover:text-white transition">
                  How Virtual Care Works
                </Link>
              </li>
            </ul>
          </div>

          {/* Col 3: Clinical Governance */}
          <div>
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-3">Governance & Security</h4>
            <ul className="space-y-2 text-xs">
              <li>
                <span className="text-slate-400">Triage Safety Protocol v1.0.4</span>
              </li>
              <li>
                <span className="text-slate-400">Doctor Verification Guarantee</span>
              </li>
              <li>
                <span className="text-slate-400">End-to-End Encrypted WebRTC Calls</span>
              </li>
              <li>
                <span className="text-slate-400">Tamper-Evident Digital Prescriptions</span>
              </li>
            </ul>
          </div>

          {/* Col 4: Emergency Contacts */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-white uppercase tracking-wider mb-1">Emergency Numbers</h4>
            <p className="text-xs text-slate-400">For acute life-threatening emergencies:</p>
            <div className="space-y-1.5 text-xs">
              <div className="flex items-center gap-2 font-mono text-red-400 bg-red-950/50 p-2 rounded border border-red-900/60">
                <Phone className="w-3.5 h-3.5 text-red-400" />
                <span>National Emergency: <strong>112</strong></span>
              </div>
              <div className="flex items-center gap-2 font-mono text-amber-400 bg-amber-950/40 p-2 rounded border border-amber-900/50">
                <Phone className="w-3.5 h-3.5 text-amber-400" />
                <span>Ambulance Services: <strong>108</strong></span>
              </div>
            </div>
            <Link
              to="/emergency"
              className="inline-flex items-center gap-1.5 text-xs text-teal-400 hover:text-teal-300 underline"
            >
              <MapPin className="w-3 h-3" />
              Find nearest physical hospitals
            </Link>
          </div>
        </div>

        {/* Legal Disclaimer Box */}
        <div className="pt-6 text-[11px] text-slate-500 leading-relaxed text-center max-w-4xl mx-auto space-y-2">
          <p>
            <strong>Important Clinical Disclaimer:</strong> The AI Care Assistant is an educational navigation tool and
            does NOT provide formal medical diagnoses, write prescriptions, or replace a clinical consultation. Digital
            prescriptions can only be formulated and certified by licensed, verified clinicians following an authorized
            consultation. If you or someone around you is experiencing chest pain, difficulty breathing, or stroke symptoms,
            please immediately contact emergency services at 112.
          </p>
          <p>&copy; {new Date().getFullYear()} Virtual Care Health Platform. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};
