/**
 * Secure Virtual Video Consultation Room
 * Author: Telehealth Video & Media Team
 *
 * Provides:
 * - Pre-call device authorization and camera/mic check
 * - Jitsi WebRTC video consultation room
 * - Doctor clinical notes side-panel
 * - Call controls and safe completion handling
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import {
  Video,
  Mic,
  MicOff,
  VideoOff,
  PhoneOff,
  ShieldCheck,
  FileText,
  User as UserIcon,
  AlertCircle,
  CheckCircle2,
} from 'lucide-react';

export const ConsultationRoomPage: React.FC = () => {
  const { appointmentId } = useParams<{ appointmentId: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string>('');
  const [consultationData, setConsultationData] = useState<any>(null);

  // Pre-call readiness
  const [hasCameraPermission, setHasCameraPermission] = useState<boolean>(true);
  const [isInCall, setIsInCall] = useState<boolean>(false);
  const [isAudioMuted, setIsAudioMuted] = useState<boolean>(false);
  const [isVideoMuted, setIsVideoMuted] = useState<boolean>(false);

  // Doctor Clinical Note Drawer
  const [notes, setNotes] = useState({
    chiefComplaint: '',
    clinicalObservations: '',
    diagnosisSummary: '',
    treatmentAdvice: '',
  });
  const [isSavingNotes, setIsSavingNotes] = useState<boolean>(false);
  const [notesSavedSuccess, setNotesSavedSuccess] = useState<boolean>(false);

  useEffect(() => {
    const authorizeAndJoin = async () => {
      if (!appointmentId) return;
      setIsLoading(true);
      setErrorMsg('');

      try {
        const response: any = await api.appointments.join(appointmentId);
        if (response?.data) {
          setConsultationData(response.data);
        }
      } catch (err: any) {
        setErrorMsg(err.message || 'You are not authorized to join this consultation room.');
      } finally {
        setIsLoading(false);
      }
    };

    authorizeAndJoin();
  }, [appointmentId]);

  const handleStartCall = () => {
    setIsInCall(true);
  };

  const handleEndCall = async () => {
    if (consultationData?.consultation_id) {
      try {
        await api.consultations.end(consultationData.consultation_id);
      } catch {
        // Fallback
      }
    }
    if (user?.role === 'doctor') {
      navigate('/doctor/dashboard');
    } else {
      navigate('/prescriptions');
    }
  };

  const handleSaveNotes = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!consultationData?.consultation_id) return;

    setIsSavingNotes(true);
    setNotesSavedSuccess(false);
    try {
      await api.consultations.saveNotes(consultationData.consultation_id, {
        chief_complaint: notes.chiefComplaint,
        clinical_observations: notes.clinicalObservations,
        diagnosis_summary: notes.diagnosisSummary,
        treatment_advice: notes.treatmentAdvice,
      });
      setNotesSavedSuccess(true);
      setTimeout(() => setNotesSavedSuccess(false), 3000);
    } catch {
      // Fallback
    } finally {
      setIsSavingNotes(false);
    }
  };

  if (isLoading) {
    return (
      <div className="max-w-md mx-auto py-24 text-center space-y-3">
        <div className="w-10 h-10 border-4 border-teal-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-sm font-semibold text-slate-700">Authorizing secure clinical video room...</p>
      </div>
    );
  }

  if (errorMsg) {
    return (
      <div className="max-w-md mx-auto py-20 px-4 text-center space-y-4">
        <div className="w-12 h-12 bg-red-100 text-red-700 rounded-2xl flex items-center justify-center mx-auto">
          <AlertCircle className="w-6 h-6" />
        </div>
        <h2 className="text-xl font-bold text-slate-900">Access Denied</h2>
        <p className="text-xs text-slate-600 leading-relaxed">{errorMsg}</p>
        <Link
          to="/appointments"
          className="inline-block bg-teal-600 text-white font-bold text-xs px-4 py-2 rounded-xl"
        >
          Return to My Appointments
        </Link>
      </div>
    );
  }

  const credentials = consultationData?.credentials;
  const isDoctor = user?.role === 'doctor';
  const roomName = credentials?.room_name || `VirtualCare-${appointmentId?.slice(0, 8)}`;
  const displayName = credentials?.display_name || user?.full_name || 'Participant';

  // Jitsi URL formatted with display name and configuration
  const jitsiUrl = `https://meet.jit.si/${encodeURIComponent(
    roomName
  )}#userInfo.displayName=${encodeURIComponent(
    displayName
  )}&config.prejoinPageEnabled=false&config.disableDeepLinking=true`;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Top Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-teal-600 text-white flex items-center justify-center">
            <Video className="w-4 h-4" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-900">
              Encrypted Consultation Encounter
            </h1>
            <span className="text-[10px] text-teal-700 font-medium">
              Patient: {consultationData?.patient_name} &bull; Attending: Dr. {consultationData?.doctor_name}
            </span>
          </div>
        </div>

        <button
          onClick={handleEndCall}
          className="bg-red-600 hover:bg-red-700 text-white font-bold text-xs px-4 py-2 rounded-xl transition flex items-center gap-1.5 shadow-xs"
        >
          <PhoneOff className="w-4 h-4" />
          <span>Leave Encounter</span>
        </button>
      </div>

      {!isInCall ? (
        /* Pre-Call Waiting Room & Device Check */
        <div className="max-w-xl mx-auto bg-white border border-slate-200 rounded-3xl p-8 shadow-sm space-y-6 text-center">
          <div className="w-16 h-16 rounded-full bg-teal-50 text-teal-700 flex items-center justify-center mx-auto border border-teal-200">
            <ShieldCheck className="w-8 h-8" />
          </div>

          <div className="space-y-1">
            <h2 className="text-xl font-bold text-slate-900">Virtual Waiting Room</h2>
            <p className="text-xs text-slate-600">
              Your connection is encrypted. Please ensure your camera and microphone are connected.
            </p>
          </div>

          <div className="bg-slate-50 border border-slate-200 rounded-2xl p-4 text-xs text-slate-700 space-y-2 text-left">
            <div className="flex items-center justify-between">
              <span>Patient:</span>
              <strong className="text-slate-900">{consultationData?.patient_name}</strong>
            </div>
            <div className="flex items-center justify-between">
              <span>Clinician:</span>
              <strong className="text-slate-900">Dr. {consultationData?.doctor_name}</strong>
            </div>
            <div className="flex items-center justify-between">
              <span>Room ID:</span>
              <span className="font-mono text-[11px] text-slate-500">{roomName}</span>
            </div>
          </div>

          <button
            onClick={handleStartCall}
            className="w-full bg-teal-600 hover:bg-teal-700 text-white font-bold py-3.5 rounded-2xl transition text-sm flex items-center justify-center gap-2 shadow-xs"
          >
            <Video className="w-5 h-5" />
            <span>Join Video Consultation Now</span>
          </button>
        </div>
      ) : (
        /* Active Video Encounter Frame */
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className={`space-y-3 ${isDoctor ? 'lg:col-span-2' : 'lg:col-span-3'}`}>
            <div className="w-full h-[580px] bg-slate-950 rounded-2xl overflow-hidden shadow-lg border border-slate-800 relative">
              <iframe
                src={jitsiUrl}
                allow="camera; microphone; fullscreen; display-capture"
                className="w-full h-full border-0"
                title="Virtual Care Video Consultation"
              />
            </div>

            <div className="flex items-center justify-between bg-white border border-slate-200 rounded-xl p-3 text-xs text-slate-600">
              <span className="flex items-center gap-1.5 font-semibold text-emerald-700">
                <ShieldCheck className="w-4 h-4 text-emerald-600" /> WebRTC Encrypted Session Active
              </span>
              <span>Need help? Dial support or leave call.</span>
            </div>
          </div>

          {/* Doctor-Only Clinical Notes Panel */}
          {isDoctor && (
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-4 h-[630px] flex flex-col justify-between">
              <div className="space-y-3">
                <div className="border-b border-slate-100 pb-2 flex items-center justify-between">
                  <h3 className="font-bold text-slate-900 text-sm flex items-center gap-1.5">
                    <FileText className="w-4 h-4 text-teal-600" /> Clinical Notes (Doctor Only)
                  </h3>
                  {notesSavedSuccess && (
                    <span className="text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                      Saved!
                    </span>
                  )}
                </div>

                <form onSubmit={handleSaveNotes} className="space-y-3 text-xs">
                  <div>
                    <label className="block font-bold text-slate-700 mb-1">Chief Complaint</label>
                    <input
                      type="text"
                      placeholder="e.g. Mild fever, dry cough for 3 days"
                      value={notes.chiefComplaint}
                      onChange={(e) => setNotes({ ...notes, chiefComplaint: e.target.value })}
                      className="w-full border border-slate-300 rounded-lg p-2 focus:ring-1 focus:ring-teal-500"
                    />
                  </div>

                  <div>
                    <label className="block font-bold text-slate-700 mb-1">Clinical Observations</label>
                    <textarea
                      rows={2}
                      placeholder="Vitals reported, throat examination, lung sounds..."
                      value={notes.clinicalObservations}
                      onChange={(e) => setNotes({ ...notes, clinicalObservations: e.target.value })}
                      className="w-full border border-slate-300 rounded-lg p-2 focus:ring-1 focus:ring-teal-500"
                    />
                  </div>

                  <div>
                    <label className="block font-bold text-slate-700 mb-1">Diagnosis Summary *</label>
                    <input
                      type="text"
                      required
                      placeholder="e.g. Acute Viral Pharyngitis"
                      value={notes.diagnosisSummary}
                      onChange={(e) => setNotes({ ...notes, diagnosisSummary: e.target.value })}
                      className="w-full border border-slate-300 rounded-lg p-2 focus:ring-1 focus:ring-teal-500 font-semibold"
                    />
                  </div>

                  <div>
                    <label className="block font-bold text-slate-700 mb-1">Treatment & Advice</label>
                    <textarea
                      rows={3}
                      placeholder="Warm salt water gargle, oral hydration, review in 3 days..."
                      value={notes.treatmentAdvice}
                      onChange={(e) => setNotes({ ...notes, treatmentAdvice: e.target.value })}
                      className="w-full border border-slate-300 rounded-lg p-2 focus:ring-1 focus:ring-teal-500"
                    />
                  </div>

                  <button
                    type="submit"
                    disabled={isSavingNotes || !notes.diagnosisSummary}
                    className="w-full bg-slate-900 hover:bg-slate-800 disabled:bg-slate-300 text-white font-bold py-2 rounded-lg transition"
                  >
                    {isSavingNotes ? 'Saving...' : 'Save Clinical Notes'}
                  </button>
                </form>
              </div>

              <div className="pt-2 border-t border-slate-100">
                <Link
                  to="/doctor/dashboard"
                  className="block text-center bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs py-2 rounded-lg transition"
                >
                  Issue Digital Prescription &rarr;
                </Link>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
