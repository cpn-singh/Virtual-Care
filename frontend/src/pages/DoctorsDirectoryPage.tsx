/**
 * Doctor Directory & Specialist Search
 * Author: Patient Care Operations Team
 *
 * Allows patients to find verified clinicians by specialty, location, or name.
 */

import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { Doctor, Specialization } from '../types';
import {
  Search,
  Stethoscope,
  Star,
  Clock,
  ShieldCheck,
  Calendar,
  MapPin,
  Filter,
  AlertCircle,
} from 'lucide-react';
import { Modal } from '../components/Modal';
import { useAuth } from '../context/AuthContext';

export const DoctorsDirectoryPage: React.FC = () => {
  const { user } = useAuth();
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [specializations, setSpecializations] = useState<Specialization[]>([]);
  const [selectedSpec, setSelectedSpec] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [fetchError, setFetchError] = useState<string>('');

  // Booking Modal State
  const [bookingDoctor, setBookingDoctor] = useState<Doctor | null>(null);
  const [bookDate, setBookDate] = useState<string>('');
  const [bookTime, setBookTime] = useState<string>('10:00');
  const [bookReason, setBookReason] = useState<string>('');
  const [bookingError, setBookingError] = useState<string>('');
  const [bookingSuccess, setBookingSuccess] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const loadData = async () => {
    setIsLoading(true);
    setFetchError('');
    try {
      const [docRes, specRes]: any = await Promise.all([
        api.doctors.list({
          search: searchQuery || undefined,
          specialization: selectedSpec || undefined,
        }),
        api.doctors.getSpecializations(),
      ]);

      if (docRes?.data) setDoctors(docRes.data);
      if (specRes?.data) setSpecializations(specRes.data);
    } catch (err: any) {
      setFetchError(err.message || 'Unable to connect to the medical server. Please ensure the backend is reachable.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [selectedSpec]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    loadData();
  };

  const handleOpenBooking = (doctor: Doctor) => {
    setBookingDoctor(doctor);
    setBookingError('');
    setBookingSuccess('');
    // Default date to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    setBookDate(tomorrow.toISOString().split('T')[0]);
  };

  const handleConfirmBooking = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!user) {
      setBookingError('Please sign in or create a patient account to book an appointment.');
      return;
    }
    if (!bookingDoctor) return;

    setIsSubmitting(true);
    setBookingError('');
    try {
      await api.appointments.book({
        doctor_id: bookingDoctor.id,
        scheduled_date: bookDate,
        scheduled_time: bookTime,
        reason_for_visit: bookReason || 'General medical consultation',
      });
      setBookingSuccess('Appointment confirmed! You can access the consultation room from your dashboard.');
      setTimeout(() => {
        setBookingDoctor(null);
      }, 2000);
    } catch (err: any) {
      setBookingError(err.message || 'Could not schedule appointment. Please try another time.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* 1. Header & Search Filters */}
      <div className="space-y-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Find Verified Doctors & Specialists
          </h1>
          <p className="text-sm text-slate-600">
            Consult virtually with board-certified physicians from the comfort of your home.
          </p>
        </div>

        {/* Search input */}
        <form onSubmit={handleSearch} className="flex gap-2 max-w-xl">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              placeholder="Search by doctor name or condition..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full text-sm pl-10 pr-4 py-2.5 border border-slate-300 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
            />
          </div>
          <button
            type="submit"
            className="bg-teal-600 hover:bg-teal-700 text-white font-semibold text-xs px-5 py-2.5 rounded-xl transition"
          >
            Search
          </button>
        </form>

        {/* Specialization Filter Pills */}
        <div className="flex flex-wrap items-center gap-2 pt-2">
          <button
            onClick={() => setSelectedSpec('')}
            className={`text-xs font-semibold px-3 py-1.5 rounded-full transition ${
              selectedSpec === ''
                ? 'bg-teal-700 text-white'
                : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
            }`}
          >
            All Specialties
          </button>
          {specializations.map((spec) => (
            <button
              key={spec.id}
              onClick={() => setSelectedSpec(spec.slug)}
              className={`text-xs font-semibold px-3 py-1.5 rounded-full transition ${
                selectedSpec === spec.slug
                  ? 'bg-teal-700 text-white'
                  : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-100'
              }`}
            >
              {spec.name}
            </button>
          ))}
        </div>
      </div>

      {/* Network / Connection Error Banner */}
      {fetchError && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-2xl flex items-center justify-between text-xs font-semibold">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-500 shrink-0" />
            <span>{fetchError}</span>
          </div>
          <button
            onClick={() => loadData()}
            className="bg-red-100 hover:bg-red-200 text-red-800 px-3 py-1 rounded-lg transition"
          >
            Retry
          </button>
        </div>
      )}

      {/* 2. Doctor Cards Grid */}
      {isLoading ? (
        <div className="text-center py-16 text-slate-500 text-sm">Loading doctors directory...</div>
      ) : doctors.length === 0 ? (
        <div className="text-center py-16 bg-white border border-slate-200 rounded-2xl p-8 space-y-3">
          <Stethoscope className="w-10 h-10 text-slate-400 mx-auto" />
          <h2 className="text-base font-bold text-slate-900">No doctors match your criteria</h2>
          <p className="text-xs text-slate-500">Try clearing the specialization or searching another keyword.</p>
          <button
            onClick={() => {
              setSelectedSpec('');
              setSearchQuery('');
            }}
            className="text-xs text-teal-700 font-bold underline"
          >
            Reset Filters
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {doctors.map((doc) => (
            <div
              key={doc.id}
              className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs hover:shadow-md transition flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <h2 className="text-lg font-bold text-slate-900">Dr. {doc.user.full_name}</h2>
                    <span className="inline-block bg-teal-50 text-teal-800 text-xs font-semibold px-2 py-0.5 rounded-md border border-teal-200 mt-1">
                      {doc.specialization?.name || 'General Physician'}
                    </span>
                  </div>
                  <div className="flex items-center gap-1 text-amber-500 bg-amber-50 px-2 py-0.5 rounded text-xs font-bold shrink-0">
                    <Star className="w-3.5 h-3.5 fill-amber-400" />
                    <span>{doc.rating}</span>
                  </div>
                </div>

                <div className="text-xs text-slate-600 space-y-1">
                  <p>
                    <strong>Qualifications:</strong> {doc.qualifications}
                  </p>
                  <p>
                    <strong>Experience:</strong> {doc.experience_years} years clinical practice
                  </p>
                  {doc.city && (
                    <p className="flex items-center gap-1 text-slate-500">
                      <MapPin className="w-3 h-3" /> {doc.city}
                    </p>
                  )}
                </div>

                {doc.bio && (
                  <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed pt-1">
                    {doc.bio}
                  </p>
                )}
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-500 uppercase font-semibold">Consultation Fee</span>
                  <div className="text-base font-black text-slate-900">₹{doc.consultation_fee}</div>
                </div>

                <button
                  onClick={() => handleOpenBooking(doc)}
                  className="bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs px-4 py-2.5 rounded-xl transition shadow-xs flex items-center gap-1.5"
                >
                  <Calendar className="w-3.5 h-3.5" />
                  <span>Book Consult</span>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 3. Appointment Booking Modal */}
      {bookingDoctor && (
        <Modal
          isOpen={!!bookingDoctor}
          onClose={() => setBookingDoctor(null)}
          title={`Book Appointment with Dr. ${bookingDoctor.user.full_name}`}
        >
          <form onSubmit={handleConfirmBooking} className="space-y-4">
            <div className="bg-teal-50 p-3 rounded-lg text-xs text-teal-900">
              <span className="font-bold">{bookingDoctor.specialization?.name || 'Consultation'}</span> &bull; Fee:{' '}
              <strong>₹{bookingDoctor.consultation_fee}</strong> (Payable before video call)
            </div>

            {bookingError && (
              <div className="bg-red-50 text-red-700 p-3 rounded-lg text-xs font-semibold">{bookingError}</div>
            )}
            {bookingSuccess && (
              <div className="bg-emerald-50 text-emerald-800 p-3 rounded-lg text-xs font-semibold">
                {bookingSuccess}
              </div>
            )}

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Select Date</label>
                <input
                  type="date"
                  value={bookDate}
                  onChange={(e) => setBookDate(e.target.value)}
                  required
                  className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Select Time Slot</label>
                <select
                  value={bookTime}
                  onChange={(e) => setBookTime(e.target.value)}
                  className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500 bg-white"
                >
                  <option value="09:30">09:30 AM</option>
                  <option value="10:00">10:00 AM</option>
                  <option value="11:30">11:30 AM</option>
                  <option value="14:00">02:00 PM</option>
                  <option value="15:30">03:30 PM</option>
                  <option value="17:00">05:00 PM</option>
                </select>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Reason for Visit / Symptoms</label>
              <textarea
                rows={3}
                placeholder="Briefly describe what you'd like to discuss with the doctor..."
                value={bookReason}
                onChange={(e) => setBookReason(e.target.value)}
                required
                className="w-full text-xs border border-slate-300 rounded-lg p-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setBookingDoctor(null)}
                className="px-4 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-100 rounded-lg"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting || !!bookingSuccess}
                className="bg-teal-600 hover:bg-teal-700 disabled:bg-slate-400 text-white font-bold text-xs px-5 py-2 rounded-lg transition"
              >
                {isSubmitting ? 'Confirming...' : 'Confirm Appointment'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};
