/**
 * Appointments Management Screen
 * Author: Patient Care Operations Team
 *
 * View scheduled, active, and past appointments with cancellation and join links.
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { Appointment } from '../types';
import {
  Calendar,
  Clock,
  Video,
  XCircle,
  CreditCard,
  AlertCircle,
  CheckCircle2,
  Stethoscope,
} from 'lucide-react';
import { Modal } from '../components/Modal';

export const AppointmentsPage: React.FC = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Cancel Modal State
  const [cancelTarget, setCancelTarget] = useState<Appointment | null>(null);
  const [cancelReason, setCancelReason] = useState<string>('');
  const [isCancelling, setIsCancelling] = useState<boolean>(false);

  const loadAppointments = async () => {
    setIsLoading(true);
    try {
      const res: any = await api.appointments.list();
      if (res?.data) {
        setAppointments(res.data);
      }
    } catch {
      // Fallback
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAppointments();
  }, []);

  const handleCancelSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cancelTarget) return;

    setIsCancelling(true);
    try {
      await api.appointments.cancel(cancelTarget.id, cancelReason);
      setCancelTarget(null);
      setCancelReason('');
      loadAppointments();
    } catch {
      // Fallback
    } finally {
      setIsCancelling(false);
    }
  };

  const filteredAppointments = appointments.filter((a) => {
    if (filter === 'all') return true;
    return a.status === filter;
  });

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">My Consultations</h1>
          <p className="text-xs text-slate-600">Track scheduled appointments and access video consultation rooms.</p>
        </div>

        <Link
          to="/doctors"
          className="bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs px-4 py-2 rounded-xl transition shadow-xs"
        >
          Book New Consultation
        </Link>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap gap-2 text-xs font-semibold">
        {['all', 'confirmed', 'in_progress', 'completed', 'cancelled'].map((tab) => (
          <button
            key={tab}
            onClick={() => setFilter(tab)}
            className={`px-3 py-1.5 rounded-full capitalize transition ${
              filter === tab
                ? 'bg-slate-900 text-white'
                : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'
            }`}
          >
            {tab.replace('_', ' ')}
          </button>
        ))}
      </div>

      {isLoading ? (
        <div className="text-center py-16 text-slate-500 text-sm">Loading appointments...</div>
      ) : filteredAppointments.length === 0 ? (
        <div className="text-center py-16 bg-white border border-slate-200 rounded-2xl p-8 space-y-3">
          <Calendar className="w-10 h-10 text-slate-400 mx-auto" />
          <h3 className="font-bold text-slate-900 text-base">No appointments found</h3>
          <p className="text-xs text-slate-500">You do not have any consultations under this status.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredAppointments.map((appt) => {
            const isJoinable = appt.status === 'confirmed' || appt.status === 'in_progress' || appt.status === 'rescheduled';
            return (
              <div
                key={appt.id}
                className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6"
              >
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-base text-slate-900">
                      Dr. {appt.doctor.user.full_name}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                        appt.status === 'confirmed'
                          ? 'bg-teal-50 text-teal-800 border border-teal-200'
                          : appt.status === 'completed'
                          ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                          : appt.status === 'cancelled'
                          ? 'bg-red-50 text-red-800 border border-red-200'
                          : 'bg-slate-100 text-slate-800'
                      }`}
                    >
                      {appt.status.replace('_', ' ')}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600">
                    <strong>Specialty:</strong> {appt.doctor.specialization?.name || 'General Medicine'} &bull;{' '}
                    <strong>Reason:</strong> {appt.reason_for_visit}
                  </p>

                  <div className="flex flex-wrap items-center gap-4 text-xs text-slate-500 pt-1 font-mono">
                    <span className="flex items-center gap-1.5">
                      <Calendar className="w-3.5 h-3.5 text-teal-600" />
                      {appt.scheduled_date}
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-teal-600" />
                      {appt.scheduled_time} ({appt.duration_minutes} min)
                    </span>
                    <span>
                      Fee: <strong>₹{appt.consultation_fee}</strong> (
                      <span className={appt.payment_status === 'paid' ? 'text-emerald-700 font-bold' : 'text-amber-700'}>
                        {appt.payment_status.toUpperCase()}
                      </span>
                      )
                    </span>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2 shrink-0">
                  {appt.payment_status === 'pending' && appt.status !== 'cancelled' && (
                    <Link
                      to="/invoices"
                      className="bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold px-3.5 py-2 rounded-xl text-xs transition flex items-center gap-1.5"
                    >
                      <CreditCard className="w-3.5 h-3.5" />
                      <span>Pay Fee</span>
                    </Link>
                  )}

                  {isJoinable && (
                    <Link
                      to={`/consultation/${appt.id}`}
                      className="bg-teal-600 hover:bg-teal-700 text-white font-bold px-4 py-2 rounded-xl text-xs transition flex items-center gap-1.5 shadow-xs"
                    >
                      <Video className="w-3.5 h-3.5" />
                      <span>Enter Video Call</span>
                    </Link>
                  )}

                  {appt.status === 'confirmed' && (
                    <button
                      onClick={() => setCancelTarget(appt)}
                      className="text-xs text-red-600 hover:bg-red-50 border border-red-200 px-3 py-2 rounded-xl font-semibold transition"
                    >
                      Cancel
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Cancel Modal */}
      {cancelTarget && (
        <Modal
          isOpen={!!cancelTarget}
          onClose={() => setCancelTarget(null)}
          title="Cancel Consultation Appointment"
        >
          <form onSubmit={handleCancelSubmit} className="space-y-4">
            <p className="text-xs text-slate-600">
              Are you sure you want to cancel your consultation with{' '}
              <strong>Dr. {cancelTarget.doctor.user.full_name}</strong> scheduled for{' '}
              <strong>{cancelTarget.scheduled_date} at {cancelTarget.scheduled_time}</strong>?
            </p>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Reason for Cancellation</label>
              <textarea
                rows={2}
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                placeholder="Schedule conflict, symptoms resolved, etc."
                className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setCancelTarget(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Keep Appointment
              </button>
              <button
                type="submit"
                disabled={isCancelling}
                className="bg-red-600 hover:bg-red-700 text-white font-bold text-xs px-4 py-2 rounded-lg transition"
              >
                {isCancelling ? 'Cancelling...' : 'Confirm Cancellation'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
