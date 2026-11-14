/**
 * Doctor Clinical Portal Dashboard
 * Author: Clinical Operations Team
 *
 * Clinician-only interface:
 * - Patient appointment schedule
 * - Video room entry
 * - Digital prescription formulation & signing
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';
import { Appointment, PrescriptionItem, Doctor } from '../types';
import {
  Calendar,
  Video,
  FileCheck2,
  Stethoscope,
  Plus,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Clock,
  User as UserIcon,
  MessageSquare,
  Smartphone,
  ExternalLink,
  Send,
  BellRing,
} from 'lucide-react';
import { Modal } from '../components/Modal';

export const DoctorDashboard: React.FC = () => {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [doctorProfile, setDoctorProfile] = useState<Doctor | null>(null);

  // WhatsApp Notification Settings State
  const [whatsappNumber, setWhatsappNumber] = useState<string>('');
  const [whatsappEnabled, setWhatsappEnabled] = useState<boolean>(true);
  const [isSavingWhatsApp, setIsSavingWhatsApp] = useState<boolean>(false);
  const [whatsAppFeedback, setWhatsAppFeedback] = useState<{ type: 'success' | 'error'; text: string; link?: string } | null>(null);
  const [activeAlertLoadingId, setActiveAlertLoadingId] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<string | null>(null);

  // Prescription Authoring Modal State
  const [activeApptForRx, setActiveApptForRx] = useState<Appointment | null>(null);
  const [diagnosis, setDiagnosis] = useState('');
  const [doctorNotes, setDoctorNotes] = useState('');
  const [items, setItems] = useState<PrescriptionItem[]>([
    {
      medicine_name: 'Paracetamol',
      formulation: 'Tablet',
      strength: '650 mg',
      dose: '1 tablet',
      frequency: 'Twice daily after food',
      duration: '3 days',
      instructions: 'Take with warm water',
    },
  ]);
  const [isSubmittingRx, setIsSubmittingRx] = useState(false);
  const [rxSuccessMsg, setRxSuccessMsg] = useState('');
  const [rxErrorMsg, setRxErrorMsg] = useState('');

  const loadDoctorData = async () => {
    setIsLoading(true);
    try {
      const [apptRes, profileRes]: [any, any] = await Promise.allSettled([
        api.appointments.list(),
        api.doctors.getMyProfile(),
      ]).then((results) => [
        results[0].status === 'fulfilled' ? results[0].value : null,
        results[1].status === 'fulfilled' ? results[1].value : null,
      ]);

      if (apptRes?.data) {
        setAppointments(apptRes.data);
      }
      if (profileRes?.data) {
        setDoctorProfile(profileRes.data);
        setWhatsappNumber(profileRes.data.whatsapp_number || profileRes.data.effective_whatsapp_number || '');
        setWhatsappEnabled(profileRes.data.whatsapp_notifications_enabled ?? true);
      }
    } catch {
      // Fallback
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDoctorData();
  }, []);

  const handleSaveWhatsAppPreferences = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSavingWhatsApp(true);
    setWhatsAppFeedback(null);
    try {
      const res: any = await api.doctors.updateMyProfile({
        whatsapp_number: whatsappNumber,
        whatsapp_notifications_enabled: whatsappEnabled,
      });
      if (res?.data) {
        setDoctorProfile(res.data);
      }
      setWhatsAppFeedback({
        type: 'success',
        text: 'WhatsApp notification preferences updated successfully!',
      });
    } catch (err: any) {
      setWhatsAppFeedback({
        type: 'error',
        text: err.message || 'Failed to update WhatsApp preferences.',
      });
    } finally {
      setIsSavingWhatsApp(false);
    }
  };

  const handleSendTestWhatsApp = async () => {
    setIsSavingWhatsApp(true);
    setWhatsAppFeedback(null);
    try {
      const res: any = await api.notifications.testWhatsApp(whatsappNumber);
      const link = res?.data?.wa_link;
      setWhatsAppFeedback({
        type: 'success',
        text: `Test alert dispatched to ${whatsappNumber || doctorProfile?.effective_whatsapp_number || 'your registered phone'}!`,
        link,
      });
    } catch (err: any) {
      setWhatsAppFeedback({
        type: 'error',
        text: err.message || 'Failed to dispatch test WhatsApp notification.',
      });
    } finally {
      setIsSavingWhatsApp(false);
    }
  };

  const handleSendAppointmentWhatsApp = async (apptId: string, alertType: 'appointment' | 'video_call') => {
    setActiveAlertLoadingId(`${apptId}-${alertType}`);
    setActionNotice(null);
    try {
      const res: any = await api.appointments.sendWhatsAppAlert(apptId, alertType);
      const waLink = res?.data?.wa_link;
      const recipient = res?.data?.recipient;
      setActionNotice(
        alertType === 'video_call'
          ? `Video call alert sent to ${recipient}! Tap WhatsApp link to view.`
          : `Appointment details sent to ${recipient} via WhatsApp!`
      );
      if (waLink) {
        window.open(waLink, '_blank', 'noopener,noreferrer');
      }
    } catch (err: any) {
      setActionNotice(err.message || 'Failed to send WhatsApp alert.');
    } finally {
      setActiveAlertLoadingId(null);
    }
  };

  const handleAddItem = () => {
    setItems([
      ...items,
      {
        medicine_name: '',
        formulation: 'Tablet',
        strength: '500 mg',
        dose: '1 tablet',
        frequency: 'Twice daily after meals',
        duration: '5 days',
        instructions: '',
      },
    ]);
  };

  const handleRemoveItem = (index: number) => {
    setItems(items.filter((_, i) => i !== index));
  };

  const handleItemChange = (index: number, field: keyof PrescriptionItem, val: string) => {
    const updated = [...items];
    updated[index] = { ...updated[index], [field]: val };
    setItems(updated);
  };

  const handleCreatePrescription = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeApptForRx) return;

    setIsSubmittingRx(true);
    setRxErrorMsg('');
    setRxSuccessMsg('');

    try {
      await api.prescriptions.create({
        appointment_id: activeApptForRx.id,
        patient_id: activeApptForRx.patient.id,
        diagnosis,
        doctor_notes: doctorNotes,
        items,
      });

      setRxSuccessMsg('Prescription certified and signed! Available for patient download.');
      setTimeout(() => {
        setActiveApptForRx(null);
        setRxSuccessMsg('');
        setDiagnosis('');
        setDoctorNotes('');
      }, 2000);
    } catch (err: any) {
      setRxErrorMsg(err.message || 'Could not issue prescription. Please check fields.');
    } finally {
      setIsSubmittingRx(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Header */}
      <div className="border-b border-slate-200 pb-4 space-y-1">
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
          <Stethoscope className="w-6 h-6 text-teal-600" />
          <span>Doctor Consultation Portal: Dr. {user?.full_name}</span>
        </h1>
        <p className="text-xs text-slate-600">
          Conduct authorized video encounters, record clinical observations, and receive real-time WhatsApp alerts.
        </p>
      </div>

      {/* Action Notification Banner */}
      {actionNotice && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-900 px-4 py-3 rounded-2xl text-xs font-semibold flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{actionNotice}</span>
          </div>
          <button
            onClick={() => setActionNotice(null)}
            className="text-emerald-700 hover:text-emerald-900 text-xs font-bold"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* WhatsApp Clinician Notifications Configuration Card */}
      <div className="bg-gradient-to-br from-emerald-50/70 via-white to-teal-50/50 border border-emerald-200/80 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-emerald-100 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="p-2 bg-emerald-600 text-white rounded-xl shadow-xs">
              <MessageSquare className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <span>WhatsApp Notification Center</span>
                <span className="inline-flex items-center gap-1 bg-emerald-100 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded-full border border-emerald-300">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  {whatsappEnabled ? 'Automated Alerts Enabled' : 'Alerts Disabled'}
                </span>
              </h2>
              <p className="text-xs text-slate-600">
                Receive instant WhatsApp alerts for <strong>new patient bookings</strong> and <strong>incoming video calls</strong>.
              </p>
            </div>
          </div>
        </div>

        <form onSubmit={handleSaveWhatsAppPreferences} className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
          <div className="md:col-span-5 space-y-1">
            <label className="block text-xs font-bold text-slate-700 flex items-center gap-1.5">
              <Smartphone className="w-3.5 h-3.5 text-emerald-600" />
              <span>Doctor WhatsApp Number (with Country Code)</span>
            </label>
            <input
              type="tel"
              value={whatsappNumber}
              onChange={(e) => setWhatsappNumber(e.target.value)}
              placeholder="e.g. +91 98765 43210"
              className="w-full text-xs font-mono font-medium border border-slate-300 rounded-xl px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500 shadow-2xs"
            />
          </div>

          <div className="md:col-span-4 flex items-center gap-2.5 py-2">
            <input
              type="checkbox"
              id="waToggle"
              checked={whatsappEnabled}
              onChange={(e) => setWhatsappEnabled(e.target.checked)}
              className="w-4 h-4 text-emerald-600 rounded border-slate-300 focus:ring-emerald-500"
            />
            <label htmlFor="waToggle" className="text-xs font-semibold text-slate-700 cursor-pointer">
              Enable WhatsApp Alerts for Appointments & Video Calls
            </label>
          </div>

          <div className="md:col-span-3 flex items-center gap-2">
            <button
              type="submit"
              disabled={isSavingWhatsApp}
              className="flex-1 bg-emerald-700 hover:bg-emerald-800 disabled:bg-slate-300 text-white font-bold text-xs px-3.5 py-2 rounded-xl transition shadow-xs text-center"
            >
              {isSavingWhatsApp ? 'Saving...' : 'Save Phone'}
            </button>
            <button
              type="button"
              onClick={handleSendTestWhatsApp}
              disabled={isSavingWhatsApp}
              className="bg-white hover:bg-emerald-50 text-emerald-800 border border-emerald-300 font-bold text-xs px-3.5 py-2 rounded-xl transition shadow-xs flex items-center gap-1"
              title="Send a sample WhatsApp alert to test integration"
            >
              <Send className="w-3 h-3" />
              <span>Test</span>
            </button>
          </div>
        </form>

        {whatsAppFeedback && (
          <div
            className={`p-3 rounded-xl text-xs font-medium flex items-center justify-between gap-3 ${
              whatsAppFeedback.type === 'success'
                ? 'bg-emerald-100/70 border border-emerald-300 text-emerald-900'
                : 'bg-red-50 border border-red-200 text-red-800'
            }`}
          >
            <div className="flex items-center gap-2">
              {whatsAppFeedback.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              ) : (
                <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
              )}
              <span>{whatsAppFeedback.text}</span>
            </div>
            {whatsAppFeedback.link && (
              <a
                href={whatsAppFeedback.link}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-emerald-700 text-white font-bold text-[11px] px-3 py-1 rounded-lg flex items-center gap-1 hover:bg-emerald-800 shrink-0"
              >
                <span>Open in WhatsApp</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            )}
          </div>
        )}
      </div>

      {/* Appointments List */}
      <section className="space-y-4">
        <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
          <Calendar className="w-4 h-4 text-teal-600" />
          <span>Patient Appointments ({appointments.length})</span>
        </h2>

        {isLoading ? (
          <div className="text-center py-12 text-slate-500 text-sm">Loading patient queue...</div>
        ) : appointments.length === 0 ? (
          <div className="text-center py-12 bg-white border border-slate-200 rounded-2xl p-6 text-slate-500 text-xs">
            No patient appointments scheduled today.
          </div>
        ) : (
          <div className="space-y-4">
            {appointments.map((appt) => (
              <div
                key={appt.id}
                className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6"
              >
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-base text-slate-900">
                      {appt.patient.user.full_name}
                    </span>
                    <span className="bg-teal-50 text-teal-800 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase border border-teal-200">
                      {appt.status.replace('_', ' ')}
                    </span>
                  </div>

                  <p className="text-xs text-slate-600">
                    <strong>Reason:</strong> {appt.reason_for_visit}
                  </p>

                  {appt.patient_symptoms_summary && (
                    <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-xs text-slate-700">
                      <strong className="text-teal-800">Pre-Consult Intake Summary:</strong>{' '}
                      {appt.patient_symptoms_summary}
                    </div>
                  )}

                  <div className="text-xs text-slate-500 font-mono flex items-center gap-4">
                    <span>Date: {appt.scheduled_date} at {appt.scheduled_time}</span>
                    <span>Fee: ₹{appt.consultation_fee} ({appt.payment_status.toUpperCase()})</span>
                  </div>
                </div>

                <div className="flex flex-wrap items-center gap-2 shrink-0">
                  <Link
                    to={`/consultation/${appt.id}`}
                    className="bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs px-4 py-2 rounded-xl transition flex items-center gap-1.5 shadow-xs"
                  >
                    <Video className="w-3.5 h-3.5" />
                    <span>Join Video Room</span>
                  </Link>

                  <button
                    onClick={() => handleSendAppointmentWhatsApp(appt.id, 'video_call')}
                    disabled={activeAlertLoadingId === `${appt.id}-video_call`}
                    className="bg-emerald-600 hover:bg-emerald-700 disabled:bg-slate-300 text-white font-bold text-xs px-3.5 py-2 rounded-xl transition flex items-center gap-1.5 shadow-xs"
                    title="Send instant video call room link to Doctor's WhatsApp"
                  >
                    <MessageSquare className="w-3.5 h-3.5" />
                    <span>
                      {activeAlertLoadingId === `${appt.id}-video_call` ? 'Sending...' : 'WhatsApp Call Alert'}
                    </span>
                  </button>

                  {appt.doctor_whatsapp_link && (
                    <a
                      href={appt.doctor_whatsapp_link}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 font-bold text-xs px-3 py-2 rounded-xl transition flex items-center gap-1 shadow-2xs"
                      title="Open appointment details in WhatsApp"
                    >
                      <ExternalLink className="w-3.5 h-3.5 text-emerald-700" />
                      <span>Chat</span>
                    </a>
                  )}

                  <button
                    onClick={() => {
                      setActiveApptForRx(appt);
                      setDiagnosis(appt.reason_for_visit);
                    }}
                    className="bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs px-4 py-2 rounded-xl transition flex items-center gap-1.5 shadow-xs"
                  >
                    <FileCheck2 className="w-3.5 h-3.5" />
                    <span>Issue Prescription</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Prescription Modal */}
      {activeApptForRx && (
        <Modal
          isOpen={!!activeApptForRx}
          onClose={() => setActiveApptForRx(null)}
          title={`Issue Digital Prescription for ${activeApptForRx.patient.user.full_name}`}
          maxWidth="lg"
        >
          <form onSubmit={handleCreatePrescription} className="space-y-4 text-xs">
            {rxErrorMsg && (
              <div className="bg-red-50 text-red-700 p-3 rounded-lg font-semibold">{rxErrorMsg}</div>
            )}
            {rxSuccessMsg && (
              <div className="bg-emerald-50 text-emerald-800 p-3 rounded-lg font-semibold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>{rxSuccessMsg}</span>
              </div>
            )}

            <div>
              <label className="block font-bold text-slate-700 mb-1">Clinical Diagnosis *</label>
              <input
                type="text"
                required
                value={diagnosis}
                onChange={(e) => setDiagnosis(e.target.value)}
                placeholder="e.g. Acute Upper Respiratory Tract Infection"
                className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500 font-semibold"
              />
            </div>

            {/* Prescribed Items Dynamic Table */}
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="font-bold text-slate-700">Prescribed Medications</label>
                <button
                  type="button"
                  onClick={handleAddItem}
                  className="text-teal-700 hover:text-teal-800 font-bold flex items-center gap-1 text-[11px]"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add Medicine</span>
                </button>
              </div>

              <div className="space-y-2.5">
                {items.map((item, idx) => (
                  <div
                    key={idx}
                    className="bg-slate-50 border border-slate-200 rounded-xl p-3 grid grid-cols-1 sm:grid-cols-6 gap-2 items-center"
                  >
                    <div className="sm:col-span-2">
                      <input
                        type="text"
                        required
                        placeholder="Medicine name"
                        value={item.medicine_name}
                        onChange={(e) => handleItemChange(idx, 'medicine_name', e.target.value)}
                        className="w-full text-xs border border-slate-300 rounded-md p-1.5 bg-white font-medium"
                      />
                    </div>
                    <div>
                      <input
                        type="text"
                        placeholder="Strength (500mg)"
                        value={item.strength}
                        onChange={(e) => handleItemChange(idx, 'strength', e.target.value)}
                        className="w-full text-xs border border-slate-300 rounded-md p-1.5 bg-white"
                      />
                    </div>
                    <div>
                      <input
                        type="text"
                        placeholder="Frequency"
                        value={item.frequency}
                        onChange={(e) => handleItemChange(idx, 'frequency', e.target.value)}
                        className="w-full text-xs border border-slate-300 rounded-md p-1.5 bg-white"
                      />
                    </div>
                    <div>
                      <input
                        type="text"
                        placeholder="Duration (5 days)"
                        value={item.duration}
                        onChange={(e) => handleItemChange(idx, 'duration', e.target.value)}
                        className="w-full text-xs border border-slate-300 rounded-md p-1.5 bg-white"
                      />
                    </div>
                    <div className="flex justify-end">
                      {items.length > 1 && (
                        <button
                          type="button"
                          onClick={() => handleRemoveItem(idx)}
                          className="p-1.5 text-red-500 hover:text-red-700 hover:bg-red-50 rounded"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <label className="block font-bold text-slate-700 mb-1">Dietary Advice & Instructions</label>
              <textarea
                rows={2}
                value={doctorNotes}
                onChange={(e) => setDoctorNotes(e.target.value)}
                placeholder="Warm water gargles, light meals, review in 3 days if fever persists..."
                className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setActiveApptForRx(null)}
                className="px-4 py-2 font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmittingRx || !diagnosis}
                className="bg-teal-600 hover:bg-teal-700 disabled:bg-slate-300 text-white font-bold px-5 py-2 rounded-lg transition"
              >
                {isSubmittingRx ? 'Signing...' : 'Sign & Issue Prescription'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
