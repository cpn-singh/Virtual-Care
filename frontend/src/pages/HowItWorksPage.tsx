/**
 * How Virtual Care Works
 * Author: Frontend Engineering Team
 */

import React from 'react';
import { Link } from 'react-router-dom';
import {
  MessageSquare,
  Stethoscope,
  Video,
  FileCheck2,
  ShieldAlert,
  ArrowRight,
  Clock,
  Lock,
} from 'lucide-react';

export const HowItWorksPage: React.FC = () => {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-12">
      <div className="text-center space-y-3 max-w-2xl mx-auto">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight">
          How Virtual Care Works
        </h1>
        <p className="text-sm sm:text-base text-slate-600 leading-relaxed">
          Designed from the ground up for clarity, patient safety, and clinical rigor.
        </p>
      </div>

      <div className="space-y-8">
        {[
          {
            step: '01',
            title: 'Pre-Triage & Safety Screening',
            desc: 'Start with our AI Care Assistant or go straight to doctor booking. If your symptoms suggest an emergency (like crushing chest pain or acute shortness of breath), our safety protocol stops ordinary onboarding and immediately surfaces emergency contacts and physical ER directions.',
            icon: ShieldAlert,
            tag: 'Deterministic Clinical Safety',
          },
          {
            step: '02',
            title: 'Choose a Verified Specialist',
            desc: 'Browse our directory of verified physicians, cardiologists, dermatologists, and pediatricians. Review their credentials, clinical experience, consultation fee, and available appointment slots before confirming.',
            icon: Stethoscope,
            tag: 'Licensed Clinicians Only',
          },
          {
            step: '03',
            title: 'Join Encrypted Video Consultation',
            desc: 'Enter your virtual waiting room with a pre-call camera and microphone check. Meet your doctor through a secure, encrypted peer-to-peer WebRTC video room right in your web browser. No complex software downloads needed.',
            icon: Video,
            tag: 'Encrypted & Confidential',
          },
          {
            step: '04',
            title: 'Receive Digital Prescription & Invoice',
            desc: 'After your consultation, the attending doctor generates an official digital prescription with structured medication dosages, usage frequency, and instructions. Download the certified PDF directly to your device.',
            icon: FileCheck2,
            tag: 'Legally Valid PDF Download',
          },
        ].map((item) => (
          <div
            key={item.step}
            className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-xs flex flex-col md:flex-row items-start gap-6"
          >
            <div className="w-14 h-14 rounded-2xl bg-teal-50 text-teal-700 flex items-center justify-center shrink-0 border border-teal-200">
              <item.icon className="w-7 h-7" />
            </div>
            <div className="space-y-2 flex-1">
              <div className="flex items-center gap-3">
                <span className="font-mono text-xs font-bold text-teal-700">{item.step}</span>
                <span className="bg-slate-100 text-slate-700 text-[10px] font-bold px-2 py-0.5 rounded-md uppercase">
                  {item.tag}
                </span>
              </div>
              <h2 className="text-xl font-bold text-slate-900">{item.title}</h2>
              <p className="text-sm text-slate-600 leading-relaxed">{item.desc}</p>
            </div>
          </div>
        ))}
      </div>

      <div className="text-center pt-6">
        <Link
          to="/doctors"
          className="inline-flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white font-bold px-6 py-3 rounded-xl transition shadow-xs text-sm"
        >
          <span>Find a Doctor Now</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
};
