/**
 * Landing Page
 * Author: Frontend Engineering Team
 *
 * Designed with a calm, trustworthy healthcare aesthetic:
 * - Clear greeting: "How can we help you today?"
 * - Prominent, non-negotiable urgent-help action
 * - Large "Talk to our care assistant" action
 * - Large "Find a doctor" action
 */

import React from 'react';
import { Link } from 'react-router-dom';
import {
  Stethoscope,
  MessageSquare,
  AlertCircle,
  ShieldCheck,
  Video,
  FileText,
  Clock,
  HeartHandshake,
  CheckCircle2,
  ArrowRight,
} from 'lucide-react';

export const LandingPage: React.FC = () => {
  return (
    <div className="space-y-16 py-8">
      {/* 1. Hero Greeting Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6 pt-4">
        {/* Prominent Urgent Help Notice */}
        <div className="inline-flex items-center gap-2 bg-red-50 text-red-700 border border-red-200 px-4 py-1.5 rounded-full text-xs font-semibold shadow-xs">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>If you are in acute pain or distress:</span>
          <Link to="/emergency" className="underline font-bold hover:text-red-800">
            Click here for Emergency Help (112)
          </Link>
        </div>

        <h1 className="text-3xl sm:text-5xl font-extrabold text-slate-900 tracking-tight max-w-3xl mx-auto leading-tight">
          How can we help you feel better today?
        </h1>
        <p className="text-base sm:text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed">
          Connect safely with verified medical specialists for online consultations, receive clinician-signed digital
          prescriptions, and explore guided symptom triage with our AI care assistant.
        </p>

        {/* 2. Primary Patient Action Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto pt-6 text-left">
          {/* Action 1: AI Care Assistant */}
          <Link
            to="/ai-care"
            className="group relative bg-white border-2 border-teal-600/30 hover:border-teal-600 rounded-2xl p-6 sm:p-8 shadow-sm hover:shadow-md transition flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center group-hover:bg-teal-600 group-hover:text-white transition">
                <MessageSquare className="w-6 h-6" />
              </div>
              <h2 className="text-xl font-bold text-slate-900 group-hover:text-teal-700 transition">
                Talk to our Care Assistant
              </h2>
              <p className="text-sm text-slate-600 leading-relaxed">
                Describe your symptoms in plain language. We'll evaluate urgency, screen for emergency red flags, and
                guide you to the right specialty.
              </p>
            </div>
            <div className="mt-6 flex items-center gap-2 text-sm font-semibold text-teal-700">
              <span>Start symptom navigation</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>

          {/* Action 2: Find a Doctor */}
          <Link
            to="/doctors"
            className="group relative bg-white border-2 border-slate-200 hover:border-teal-600 rounded-2xl p-6 sm:p-8 shadow-sm hover:shadow-md transition flex flex-col justify-between"
          >
            <div className="space-y-3">
              <div className="w-12 h-12 rounded-xl bg-slate-100 text-slate-800 flex items-center justify-center group-hover:bg-teal-600 group-hover:text-white transition">
                <Stethoscope className="w-6 h-6" />
              </div>
              <h2 className="text-xl font-bold text-slate-900 group-hover:text-teal-700 transition">
                Find a Verified Doctor
              </h2>
              <p className="text-sm text-slate-600 leading-relaxed">
                Browse licensed physicians, cardiologists, dermatologists, and pediatricians. Schedule a convenient
                video consultation in minutes.
              </p>
            </div>
            <div className="mt-6 flex items-center gap-2 text-sm font-semibold text-slate-800 group-hover:text-teal-700">
              <span>View doctor directory</span>
              <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </Link>
        </div>
      </section>

      {/* 3. Core Safety Principles */}
      <section className="bg-slate-100/70 border-y border-slate-200/80 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-2xl mx-auto mb-10 space-y-2">
            <h3 className="text-xs font-bold text-teal-800 uppercase tracking-widest">Clinical Governance</h3>
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">Patient safety is our first priority</h2>
            <p className="text-sm text-slate-600">
              Our platform is built upon strict clinical boundaries and certified physician oversight.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-slate-900">Deterministic Red-Flag Protocol</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Chest pain, breathing distress, or stroke symptoms trigger instant emergency escalation and emergency
                number dispatch before any automated response.
              </p>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center">
                <FileText className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-slate-900">Doctor-Issued Prescriptions</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                The AI assistant never prescribes medications or modifies dosages. Only a verified, licensed doctor can
                issue and digitally sign a prescription.
              </p>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 space-y-3">
              <div className="w-10 h-10 rounded-lg bg-teal-50 text-teal-700 flex items-center justify-center">
                <Video className="w-5 h-5" />
              </div>
              <h3 className="font-bold text-slate-900">Encrypted Video Consultations</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Peer-to-peer encrypted clinical video encounters ensure your health consultations remain confidential,
                protected, and fully private.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* 4. How It Works Steps */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        <div className="text-center max-w-xl mx-auto space-y-2">
          <h2 className="text-2xl sm:text-3xl font-bold text-slate-900">Simple 4-Step Care Journey</h2>
          <p className="text-sm text-slate-600">From symptom onset to prescription delivery in one seamless workflow.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            {
              step: '1',
              title: 'Symptom Triage',
              desc: 'Use our AI care assistant to describe symptoms and receive structured care routing.',
            },
            {
              step: '2',
              title: 'Book a Doctor',
              desc: 'Select a verified specialist by fee, rating, and available appointment slot.',
            },
            {
              step: '3',
              title: 'Video Consultation',
              desc: 'Join your secure online consultation directly from your browser on phone or desktop.',
            },
            {
              step: '4',
              title: 'Digital Prescription',
              desc: 'Download your clinician-signed digital prescription PDF immediately after the call.',
            },
          ].map((item) => (
            <div key={item.step} className="bg-white border border-slate-200 rounded-xl p-6 relative space-y-2">
              <span className="w-8 h-8 rounded-full bg-teal-100 text-teal-800 font-extrabold flex items-center justify-center text-sm">
                {item.step}
              </span>
              <h3 className="font-bold text-slate-900 pt-2">{item.title}</h3>
              <p className="text-xs text-slate-600 leading-relaxed">{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* 5. Call to Action */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center bg-teal-700 text-white rounded-3xl p-8 sm:p-12 shadow-sm space-y-6">
        <h2 className="text-2xl sm:text-4xl font-extrabold tracking-tight">
          Ready to experience safe, accessible healthcare?
        </h2>
        <p className="text-teal-100 max-w-xl mx-auto text-sm sm:text-base leading-relaxed">
          Create a free account in 30 seconds. Verify your email with a secure code and start consulting with verified
          doctors today.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-4">
          <Link
            to="/register"
            className="bg-white text-teal-800 hover:bg-teal-50 font-bold px-6 py-3 rounded-xl transition shadow-sm text-sm"
          >
            Create Patient Account
          </Link>
          <Link
            to="/doctors"
            className="bg-teal-800 hover:bg-teal-900 text-white font-semibold px-6 py-3 rounded-xl transition border border-teal-600 text-sm"
          >
            Explore Doctors
          </Link>
        </div>
      </section>
    </div>
  );
};
