/**
 * Patient Portal Dashboard
 * Author: Patient Experience & Clinical Operations Team
 *
 * Visual hierarchy:
 * 1. Warm greeting and reassurance
 * 2. Prominent emergency-first button
 * 3. Upcoming appointment card
 * 4. Primary actions: Care Assistant, Book Doctor, Prescriptions, Billing
 * 5. Recent prescriptions & medical documents
 */

import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Appointment, Prescription } from '../types';
import {
  Calendar,
  Video,
  FileText,
  MessageSquare,
  Stethoscope,
  Receipt,
  AlertCircle,
  Clock,
  ArrowRight,
  Download,
  CreditCard,
  CheckCircle,
} from 'lucide-react';

export const PatientDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const handleDownloadPdf = async (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    setDownloadingId(id);
    try {
      await api.prescriptions.downloadPdf(id);
    } catch {
      window.open(api.prescriptions.getPdfDownloadUrl(id), '_blank');
    } finally {
      setDownloadingId(null);
    }
  };

  useEffect(() => {
    const loadDashboardData = async () => {
      setIsLoading(true);
      try {
        const [apptRes, rxRes]: any = await Promise.all([
          api.appointments.list(),
          api.prescriptions.list(),
        ]);
        if (apptRes?.data) setAppointments(apptRes.data);
        if (rxRes?.data) setPrescriptions(rxRes.data);
      } catch {
        // Fallback
      } finally {
        setIsLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  // Upcoming confirmed or in-progress appointment
  const nextAppointment = appointments.find(
    (a) => a.status === 'confirmed' || a.status === 'in_progress' || a.status === 'rescheduled'
  );

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* 1. Header Greeting & Emergency Button */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Welcome, {user?.first_name || 'Patient'}
          </h1>
          <p className="text-sm text-slate-600">
            How can we support your health today?
          </p>
        </div>

        {/* Immediate Emergency Action */}
        <Link
          to="/emergency"
          className="inline-flex items-center gap-2 bg-red-50 hover:bg-red-100 text-red-700 border border-red-200 font-bold px-4 py-2 rounded-xl text-xs transition shadow-xs"
        >
          <AlertCircle className="w-4 h-4 text-red-600" />
          <span>I Need Urgent Help</span>
        </Link>
      </div>

      {/* 2. Upcoming Appointment Hero Card */}
      {nextAppointment ? (
        <div className="bg-gradient-to-r from-teal-800 to-teal-950 text-white rounded-3xl p-6 sm:p-8 shadow-sm space-y-4">
          <div className="flex flex-wrap items-center justify-between gap-2 text-xs font-semibold uppercase tracking-wider text-teal-300">
            <span className="flex items-center gap-1.5">
              <Clock className="w-4 h-4" /> Next Upcoming Consultation
            </span>
            <span className="bg-teal-700/60 text-white px-2.5 py-0.5 rounded-full border border-teal-600">
              {nextAppointment.status.toUpperCase()}
            </span>
          </div>

          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6 pt-2">
            <div className="space-y-1">
              <h2 className="text-xl sm:text-2xl font-bold">
                Dr. {nextAppointment.doctor.user.full_name}
              </h2>
              <p className="text-teal-200 text-sm">
                {nextAppointment.doctor.specialization?.name || 'General Physician'} &bull; Reason: {nextAppointment.reason_for_visit}
              </p>
              <p className="text-xs text-teal-300 flex items-center gap-2 pt-1 font-mono">
                <Calendar className="w-3.5 h-3.5" />
                <span>Date: {nextAppointment.scheduled_date} at {nextAppointment.scheduled_time}</span>
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {nextAppointment.payment_status === 'pending' && (
                <Link
                  to="/invoices"
                  className="bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold px-4 py-2.5 rounded-xl text-xs transition flex items-center gap-1.5 shadow-xs"
                >
                  <CreditCard className="w-4 h-4" />
                  <span>Pay Fee (₹{nextAppointment.consultation_fee})</span>
                </Link>
              )}

              <Link
                to={`/consultation/${nextAppointment.id}`}
                className="bg-white hover:bg-teal-50 text-teal-900 font-extrabold px-5 py-2.5 rounded-xl text-xs transition flex items-center gap-2 shadow-xs"
              >
                <Video className="w-4 h-4 text-teal-700" />
                <span>Enter Video Room</span>
              </Link>
            </div>
          </div>
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-2xl p-6 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center shrink-0">
              <Calendar className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-sm">No Appointments Scheduled</h3>
              <p className="text-xs text-slate-500">Book a consultation with a verified clinician anytime.</p>
            </div>
          </div>
          <Link
            to="/doctors"
            className="bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs px-4 py-2 rounded-xl transition shrink-0"
          >
            Find Doctor
          </Link>
        </div>
      )}

      {/* 3. Primary Navigation Tiles */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Link
          to="/ai-care"
          className="bg-white border border-slate-200 hover:border-teal-600 rounded-2xl p-5 shadow-xs transition group space-y-3"
        >
          <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center group-hover:bg-teal-600 group-hover:text-white transition">
            <MessageSquare className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-sm group-hover:text-teal-700 transition">
              AI Care Assistant
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed pt-1">
              Check symptoms and explore guided care pathways.
            </p>
          </div>
        </Link>

        <Link
          to="/doctors"
          className="bg-white border border-slate-200 hover:border-teal-600 rounded-2xl p-5 shadow-xs transition group space-y-3"
        >
          <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-800 flex items-center justify-center group-hover:bg-teal-600 group-hover:text-white transition">
            <Stethoscope className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-sm group-hover:text-teal-700 transition">
              Book a Doctor
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed pt-1">
              Select verified specialists across 6 clinical fields.
            </p>
          </div>
        </Link>

        <Link
          to="/prescriptions"
          className="bg-white border border-slate-200 hover:border-teal-600 rounded-2xl p-5 shadow-xs transition group space-y-3"
        >
          <div className="w-10 h-10 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center group-hover:bg-teal-600 group-hover:text-white transition">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-sm group-hover:text-teal-700 transition">
              My Prescriptions
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed pt-1">
              Download certified doctor-signed Rx PDF files.
            </p>
          </div>
        </Link>

        <Link
          to="/invoices"
          className="bg-white border border-slate-200 hover:border-teal-600 rounded-2xl p-5 shadow-xs transition group space-y-3"
        >
          <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-800 flex items-center justify-center group-hover:bg-teal-600 group-hover:text-white transition">
            <Receipt className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-sm group-hover:text-teal-700 transition">
              Billing & Receipts
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed pt-1">
              View payment receipts and consultation invoices.
            </p>
          </div>
        </Link>
      </div>

      {/* 4. Recent Prescriptions List */}
      <section className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <FileText className="w-4 h-4 text-teal-600" />
            Recent Digital Prescriptions
          </h2>
          <Link to="/prescriptions" className="text-xs font-semibold text-teal-700 hover:underline">
            View All &rarr;
          </Link>
        </div>

        {prescriptions.length === 0 ? (
          <p className="text-xs text-slate-500 py-4 text-center">
            No prescriptions issued yet. Your doctor will provide one after your consultation.
          </p>
        ) : (
          <div className="divide-y divide-slate-100">
            {prescriptions.slice(0, 3).map((rx) => (
              <div key={rx.id} className="py-3 flex items-center justify-between gap-4">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-sm text-slate-900">{rx.diagnosis}</span>
                    <span className="bg-emerald-50 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded border border-emerald-200">
                      SIGNED
                    </span>
                  </div>
                  <p className="text-xs text-slate-500">
                    Dr. {rx.doctor.user.full_name} &bull; {rx.items.length} prescribed medication(s)
                  </p>
                </div>

                <a
                  href={api.prescriptions.getPdfDownloadUrl(rx.id)}
                  onClick={(e) => handleDownloadPdf(e, rx.id)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-700 font-semibold text-xs px-3 py-1.5 rounded-lg transition cursor-pointer"
                >
                  <Download className={`w-3.5 h-3.5 ${downloadingId === rx.id ? 'animate-bounce' : ''}`} />
                  <span>{downloadingId === rx.id ? 'Generating...' : 'Download PDF'}</span>
                </a>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
