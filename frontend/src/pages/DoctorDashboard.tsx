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
import { Appointment, PrescriptionItem } from '../types';
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
} from 'lucide-react';
import { Modal } from '../components/Modal';

export const DoctorDashboard: React.FC = () => {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);

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
    loadDoctorData();
  }, []);

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
          Conduct authorized video encounters, record clinical observations, and sign digital prescriptions.
        </p>
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
