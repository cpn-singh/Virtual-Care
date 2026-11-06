/**
 * AI Care Navigation Assistant with Pharmacology & In-Chat Booking
 * Author: Clinical Safety & AI Governance Team
 *
 * Implements:
 * - Conversational multi-turn clinical symptom interview
 * - Real-time deterministic red-flag emergency screening (Protocol 1.0.4-CLINICAL)
 * - Multi-format medical document & image parser (PDF, DOC, Images, TXT)
 * - Pharmacology intelligence:
 *   * Detects medicines from text and uploaded prescriptions
 *   * Detects underlying diseases/conditions
 *   * Suggests equivalent alternatives with the same mechanism of action
 *   * Formulates draft structured prescriptions for doctor sign-off
 * - In-Chat 1-Click Appointment Booking with verified specialists
 */

import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { AIMessage } from '../types';
import {
  Send,
  AlertCircle,
  Bot,
  User as UserIcon,
  PhoneCall,
  Calendar,
  ShieldCheck,
  RefreshCw,
  ExternalLink,
  Paperclip,
  FileText,
  X,
  Pill,
  Activity,
  CheckCircle2,
  Clock,
  Star,
  Sparkles,
  Mic,
  MicOff,
  Volume2,
  Square,
  Languages,
} from 'lucide-react';

export const AICareAssistantPage: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [isSending, setIsSending] = useState<boolean>(false);
  const [isEmergency, setIsEmergency] = useState<boolean>(false);
  const [emergencyAlertText, setEmergencyAlertText] = useState<string>('');
  const [handoffSummary, setHandoffSummary] = useState<string | null>(null);

  // File Attachment State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // In-Chat Booking State
  const [bookingDate, setBookingDate] = useState<string>(() => {
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    return tomorrow.toISOString().split('T')[0];
  });
  const [bookingTime, setBookingTime] = useState<string>('10:00');
  const [bookingLoading, setBookingLoading] = useState<boolean>(false);
  const [bookedAppointmentId, setBookedAppointmentId] = useState<string | null>(null);
  const [bookingError, setBookingError] = useState<string>('');

  // Voice Input (Microphone) & Speech Synthesis (Audio Readout) State
  const [isListening, setIsListening] = useState<boolean>(false);
  const [speechLang, setSpeechLang] = useState<'hi-IN' | 'en-IN'>('hi-IN');
  const [speakingMessageId, setSpeakingMessageId] = useState<string | null>(null);
  const recognitionRef = useRef<any>(null);

  // Clean up speech synthesis & recognition on unmount
  useEffect(() => {
    return () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
    };
  }, []);

  const toggleListening = () => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. Please use Google Chrome, Edge, or Safari.');
      return;
    }

    if (isListening) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {}
      }
      setIsListening(false);
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = speechLang;

      recognition.onstart = () => {
        setIsListening(true);
      };

      recognition.onresult = (event: any) => {
        const transcript = Array.from(event.results)
          .map((result: any) => result[0].transcript)
          .join('');
        setInputMessage(transcript);
      };

      recognition.onerror = (event: any) => {
        console.warn('Speech recognition warning/error:', event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognition.start();
    } catch (err) {
      console.error('Failed to start speech recognition:', err);
      setIsListening(false);
    }
  };

  const toggleSpeak = (messageId: string, text: string) => {
    if (!('speechSynthesis' in window)) {
      alert('Text-to-speech audio is not supported in this browser.');
      return;
    }

    if (speakingMessageId === messageId) {
      window.speechSynthesis.cancel();
      setSpeakingMessageId(null);
      return;
    }

    window.speechSynthesis.cancel();
    setSpeakingMessageId(messageId);

    // Strip markdown formatting for clear natural voice
    const cleanSpeech = text
      .replace(/[#*•&bull;_`]/g, '')
      .replace(/🚨|⚠️|💊|🔬|💡|✅/g, '')
      .replace(/\n+/g, '. ')
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanSpeech);

    const isHindiText = /[\u0900-\u097F]/.test(cleanSpeech);
    utterance.lang = isHindiText ? 'hi-IN' : 'en-IN';
    utterance.rate = 0.95;

    const voices = window.speechSynthesis.getVoices();
    const matchingVoice = voices.find((v) =>
      isHindiText ? v.lang.includes('hi') : v.lang.includes('en-IN') || v.lang.includes('en')
    );
    if (matchingVoice) {
      utterance.voice = matchingVoice;
    }

    utterance.onend = () => setSpeakingMessageId(null);
    utterance.onerror = () => setSpeakingMessageId(null);

    window.speechSynthesis.speak(utterance);
  };

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const initSession = async () => {
    try {
      const res: any = await api.aiCare.createSession();
      if (res?.data?.id) {
        setSessionId(res.data.id);
        if (res.data.messages) {
          setMessages(res.data.messages);
        }
      }
    } catch {
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content:
            'Hello! I am your Virtual Care Assistant. How can I help you today? You can describe your symptoms or attach a medical document (Image, PDF, Word doc).',
        },
      ]);
    }
  };

  useEffect(() => {
    initSession();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isSending]);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
    }
  };

  const handleClearFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = inputMessage.trim();
    if ((!text && !selectedFile) || isSending || !sessionId) return;

    const fileToUpload = selectedFile;
    const userDisplay = fileToUpload
      ? `${text ? text + '\n' : ''}📎 Attached: ${fileToUpload.name}`
      : text;

    const userMsg: AIMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: userDisplay,
      created_at: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInputMessage('');
    handleClearFile();
    setIsSending(true);

    try {
      const res: any = await api.aiCare.sendMessage(sessionId, text, fileToUpload);
      const respData = res?.data?.response;

      if (respData) {
        const assistantMsg: AIMessage = {
          id: `bot-${Date.now()}`,
          role: 'assistant',
          content: respData.message,
          category: respData.category,
          urgency: respData.urgency,
          emergency_action_required: respData.emergency_action_required,
          recommended_next_step: respData.recommended_next_step,
          detected_medicines: respData.detected_medicines,
          detected_lab_findings: respData.detected_lab_findings,
          draft_prescription: respData.draft_prescription,
          can_book_in_chat: respData.can_book_in_chat,
          recommended_doctor: respData.recommended_doctor,
        };
        setMessages((prev) => [...prev, assistantMsg]);

        if (res.data.is_emergency || respData.emergency_action_required) {
          setIsEmergency(true);
          setEmergencyAlertText(respData.message);
        }
      }
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          role: 'assistant',
          content:
            'Our system encountered a temporary connection issue. If your symptoms are serious, please dial 112 immediately.',
        },
      ]);
    } finally {
      setIsSending(false);
    }
  };

  const handleInChatBooking = async (doctor: any) => {
    if (!user) {
      setBookingError('Please sign in or create an account to book your appointment.');
      return;
    }

    setBookingLoading(true);
    setBookingError('');
    try {
      // Gather symptom context from user messages
      const patientSummary = messages
        .filter((m) => m.role === 'user')
        .map((m) => m.content)
        .join('; ');

      const res: any = await api.appointments.book({
        doctor_id: doctor.id,
        scheduled_date: bookingDate,
        scheduled_time: bookingTime,
        reason_for_visit: `Consultation regarding symptom evaluation (${doctor.specialization})`,
        patient_symptoms_summary: patientSummary.slice(0, 500),
      });

      if (res?.data?.id) {
        setBookedAppointmentId(res.data.id);
      }
    } catch (err: any) {
      setBookingError(err.message || 'Could not schedule appointment. Please try again.');
    } finally {
      setBookingLoading(false);
    }
  };

  const handleGenerateHandoff = async () => {
    if (!sessionId) return;
    try {
      const res: any = await api.aiCare.getHandoff(sessionId);
      if (res?.data?.symptom_summary) {
        setHandoffSummary(res.data.symptom_summary);
      }
    } catch {
      setHandoffSummary('Intake summary prepared. You can share your symptoms directly during consultation.');
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 space-y-4">
      {/* 1. Constant Urgent Help Bar */}
      <div className="bg-red-50 border border-red-200 rounded-xl p-3 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-2 text-red-800 font-semibold">
          <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
          <span>If symptoms are getting worse or you feel in danger:</span>
        </div>
        <div className="flex items-center gap-2">
          <a
            href="tel:112"
            className="bg-red-600 hover:bg-red-700 text-white font-bold px-3 py-1 rounded-full transition flex items-center gap-1 shadow-xs"
          >
            <PhoneCall className="w-3 h-3" />
            Dial 112
          </a>
          <Link to="/emergency" className="text-red-700 underline font-medium">
            Emergency Care &rarr;
          </Link>
        </div>
      </div>

      {/* 2. Emergency Alert Overlay */}
      {isEmergency && (
        <div
          className="bg-red-700 text-white rounded-2xl p-6 sm:p-8 shadow-xl space-y-4 animate-in fade-in"
          role="alert"
        >
          <div className="flex items-start gap-3">
            <AlertCircle className="w-8 h-8 text-amber-300 shrink-0 mt-0.5" />
            <div className="space-y-2">
              <h2 className="text-xl sm:text-2xl font-black">CRITICAL CLINICAL ESCALATION</h2>
              <p className="text-sm leading-relaxed text-red-100 whitespace-pre-line">{emergencyAlertText}</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-3 pt-2">
            <a
              href="tel:112"
              className="bg-white text-red-700 font-black px-6 py-3 rounded-xl shadow-md text-sm hover:bg-red-50 transition flex items-center gap-2"
            >
              <PhoneCall className="w-4 h-4 text-red-600" />
              Call 112 Now
            </a>
            <Link
              to="/emergency"
              className="bg-red-900 text-white font-semibold px-5 py-3 rounded-xl text-sm hover:bg-red-950 transition border border-red-500 flex items-center gap-2"
            >
              <ExternalLink className="w-4 h-4" />
              Locate Nearest ER Hospital
            </Link>
          </div>
        </div>
      )}

      {/* 3. Main Chat Interface */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs flex flex-col h-[640px] overflow-hidden">
        {/* Chat Header */}
        <div className="px-6 py-3.5 border-b border-slate-200 bg-slate-50 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-teal-600 text-white flex items-center justify-center">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <h1 className="text-sm font-bold text-slate-900">Virtual Care Triage & Medicine Assistant</h1>
              <span className="text-[10px] text-teal-700 font-medium">Protocol v1.0.4 &bull; Pharmacology Engine</span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Link
              to="/doctors"
              className="inline-flex items-center gap-1.5 bg-white border border-slate-200 hover:border-teal-600 text-slate-700 hover:text-teal-700 text-xs font-semibold px-3 py-1.5 rounded-lg transition"
            >
              <Calendar className="w-3.5 h-3.5 text-teal-600" />
              <span>Doctor Directory</span>
            </Link>
          </div>
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5 bg-slate-50/50">
          {messages.map((msg) => {
            const isUser = msg.role === 'user';
            return (
              <div key={msg.id} className={`flex items-start gap-2.5 ${isUser ? 'flex-row-reverse' : ''}`}>
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs shrink-0 ${
                    isUser ? 'bg-slate-800 text-white' : 'bg-teal-600 text-white'
                  }`}
                >
                  {isUser ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                </div>

                <div
                  className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs sm:text-sm leading-relaxed whitespace-pre-line shadow-2xs space-y-3 ${
                    isUser
                      ? 'bg-slate-900 text-white rounded-tr-xs'
                      : msg.emergency_action_required
                      ? 'bg-red-50 text-red-900 border border-red-200 font-medium rounded-tl-xs'
                      : 'bg-white text-slate-800 border border-slate-200 rounded-tl-xs'
                  }`}
                >
                  <div>{msg.content}</div>

                  {/* Audio Listen Button for Assistant Messages */}
                  {!isUser && (
                    <div className="pt-1 flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => toggleSpeak(msg.id, msg.content)}
                        className="inline-flex items-center gap-1.5 text-[11px] text-teal-700 hover:text-teal-900 bg-teal-50 hover:bg-teal-100 px-2.5 py-1 rounded-lg transition font-medium border border-teal-200/60 shadow-2xs"
                        title={speakingMessageId === msg.id ? 'Stop audio / रोकें' : 'Listen aloud (आवाज में सुनें)'}
                      >
                        {speakingMessageId === msg.id ? (
                          <>
                            <Square className="w-3 h-3 text-red-600 fill-red-600 animate-pulse" />
                            <span className="text-red-700 font-bold">Stop Audio / रोकें</span>
                          </>
                        ) : (
                          <>
                            <Volume2 className="w-3.5 h-3.5 text-teal-600" />
                            <span>Listen in Audio / सुनें 🔊</span>
                          </>
                        )}
                      </button>
                    </div>
                  )}

                  {/* 1. Pharmacology & Medicine Detection Intelligence Card */}
                  {!isUser && msg.detected_medicines && msg.detected_medicines.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-slate-200 space-y-3">
                      <div className="flex items-center gap-1.5 font-bold text-teal-800 text-xs uppercase tracking-wider">
                        <Pill className="w-4 h-4 text-teal-600" />
                        <span>Pharmacology & Therapeutic Equivalents</span>
                      </div>

                      {msg.detected_medicines.map((med: any, i: number) => (
                        <div key={i} className="bg-teal-50/60 border border-teal-200 rounded-xl p-3 space-y-2">
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <strong className="text-slate-900 text-xs">{med.generic_name}</strong>
                              <div className="text-[11px] text-teal-900 font-semibold">
                                Indicated Disease: {med.primary_disease}
                              </div>
                            </div>
                            <span className="bg-white border border-teal-200 text-teal-800 text-[10px] font-bold px-2 py-0.5 rounded-full shrink-0">
                              {med.therapeutic_class}
                            </span>
                          </div>

                          <p className="text-[11px] text-slate-600 leading-relaxed">
                            <strong>Mechanism:</strong> {med.mechanism_of_action}
                          </p>

                          {/* Equivalent Medicines that do the same work */}
                          {med.equivalent_alternatives && med.equivalent_alternatives.length > 0 && (
                            <div className="pt-1 space-y-1">
                              <span className="block text-[11px] font-bold text-slate-700">
                                🔄 Equivalent Medicines with Same Therapeutic Action:
                              </span>
                              <div className="space-y-1">
                                {med.equivalent_alternatives.map((alt: any, j: number) => (
                                  <div
                                    key={j}
                                    className="bg-white p-2 rounded-lg border border-teal-100 text-[11px] space-y-0.5"
                                  >
                                    <div className="font-bold text-teal-800 flex items-center justify-between">
                                      <span>{alt.name}</span>
                                      <span className="text-[10px] font-medium text-slate-500">({alt.class})</span>
                                    </div>
                                    <p className="text-slate-600">{alt.how_it_works}</p>
                                    <p className="text-[10px] text-slate-500 italic">{alt.typical_use}</p>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* 2. Draft Prescription Table */}
                  {!isUser && msg.draft_prescription && msg.draft_prescription.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-slate-100 space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-slate-900 flex items-center gap-1.5">
                          <FileText className="w-3.5 h-3.5 text-teal-600" />
                          <span>Draft Prescription Summary for Doctor Review</span>
                        </span>
                        <span className="text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-medium">
                          Requires Clinician Sign-Off
                        </span>
                      </div>

                      <div className="overflow-x-auto border border-slate-200 rounded-lg">
                        <table className="w-full text-left text-[11px] divide-y divide-slate-200">
                          <thead className="bg-slate-100 font-bold text-slate-700">
                            <tr>
                              <th className="p-1.5">Medicine</th>
                              <th className="p-1.5">Form</th>
                              <th className="p-1.5">Frequency</th>
                              <th className="p-1.5">Duration</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-slate-100 bg-white">
                            {msg.draft_prescription.map((item: any, k: number) => (
                              <tr key={k}>
                                <td className="p-1.5 font-bold text-slate-900">{item.medicine_name}</td>
                                <td className="p-1.5">{item.formulation}</td>
                                <td className="p-1.5">{item.frequency}</td>
                                <td className="p-1.5">{item.duration}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}

                  {/* 3. In-Chat Interactive Appointment Booking Widget */}
                  {!isUser && msg.can_book_in_chat && msg.recommended_doctor && (
                    <div className="mt-4 pt-3 border-t-2 border-teal-500/30 bg-teal-50/70 p-4 rounded-xl border border-teal-200 space-y-3">
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex items-center gap-2">
                          <div className="w-9 h-9 rounded-full bg-teal-600 text-white flex items-center justify-center font-bold text-xs">
                            Dr
                          </div>
                          <div>
                            <h4 className="font-bold text-slate-900 text-xs sm:text-sm">
                              {msg.recommended_doctor.name}
                            </h4>
                            <span className="text-[11px] text-teal-800 font-semibold">
                              {msg.recommended_doctor.specialization} &bull; {msg.recommended_doctor.qualifications}
                            </span>
                          </div>
                        </div>

                        <div className="text-right">
                          <span className="text-[10px] text-slate-500 uppercase font-semibold">Fee</span>
                          <div className="text-xs sm:text-sm font-black text-slate-900">
                            ₹{msg.recommended_doctor.consultation_fee}
                          </div>
                        </div>
                      </div>

                      {bookingError && (
                        <div className="bg-red-50 text-red-700 p-2.5 rounded-lg text-xs font-semibold">
                          {bookingError}
                          {!user && (
                            <Link to="/login" className="block text-teal-700 underline mt-1">
                              Click here to sign in &rarr;
                            </Link>
                          )}
                        </div>
                      )}

                      {bookedAppointmentId ? (
                        <div className="bg-emerald-50 border border-emerald-200 text-emerald-900 p-3 rounded-lg text-xs space-y-2">
                          <div className="font-bold flex items-center gap-1.5">
                            <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                            <span>Appointment Confirmed for {bookingDate} at {bookingTime}!</span>
                          </div>
                          <p className="text-[11px] text-emerald-800">
                            Your symptom notes and document summary have been attached for the doctor's review.
                          </p>
                          <div className="pt-1 flex gap-2">
                            <Link
                              to={`/consultation/${bookedAppointmentId}`}
                              className="bg-emerald-700 hover:bg-emerald-800 text-white font-bold px-3 py-1.5 rounded-lg text-xs transition"
                            >
                              Enter Video Room
                            </Link>
                            <Link
                              to="/appointments"
                              className="bg-white border border-emerald-300 text-emerald-900 font-semibold px-3 py-1.5 rounded-lg text-xs"
                            >
                              View in My Appointments
                            </Link>
                          </div>
                        </div>
                      ) : (
                        <div className="space-y-2 pt-1">
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div>
                              <label className="block text-[11px] font-bold text-slate-700 mb-0.5">Date</label>
                              <input
                                type="date"
                                value={bookingDate}
                                onChange={(e) => setBookingDate(e.target.value)}
                                className="w-full border border-slate-300 rounded-lg p-1.5 bg-white text-xs"
                              />
                            </div>
                            <div>
                              <label className="block text-[11px] font-bold text-slate-700 mb-0.5">Time Slot</label>
                              <select
                                value={bookingTime}
                                onChange={(e) => setBookingTime(e.target.value)}
                                className="w-full border border-slate-300 rounded-lg p-1.5 bg-white text-xs"
                              >
                                <option value="10:00">10:00 AM</option>
                                <option value="11:30">11:30 AM</option>
                                <option value="14:00">02:00 PM</option>
                                <option value="16:00">04:00 PM</option>
                                <option value="17:30">05:30 PM</option>
                              </select>
                            </div>
                          </div>

                          <button
                            type="button"
                            onClick={() => handleInChatBooking(msg.recommended_doctor)}
                            disabled={bookingLoading}
                            className="w-full bg-teal-600 hover:bg-teal-700 disabled:bg-slate-300 text-white font-bold py-2 px-3 rounded-lg text-xs transition flex items-center justify-center gap-1.5 shadow-xs"
                          >
                            <Calendar className="w-3.5 h-3.5" />
                            <span>
                              {bookingLoading ? 'Scheduling...' : '1-Click Confirm Appointment with Specialist'}
                            </span>
                          </button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
          {isSending && (
            <div className="flex items-center gap-2 text-xs text-slate-500 italic pl-10">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-teal-600" />
              <span>Analyzing symptoms & medical documents...</span>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Selected File Chip preview before sending */}
        {selectedFile && (
          <div className="bg-teal-50 border-t border-teal-200 px-4 py-2 flex items-center justify-between text-xs text-teal-900">
            <div className="flex items-center gap-2 truncate">
              <FileText className="w-4 h-4 text-teal-700 shrink-0" />
              <span className="font-semibold truncate">{selectedFile.name}</span>
              <span className="text-[10px] text-teal-700 shrink-0">
                ({(selectedFile.size / 1024).toFixed(1)} KB)
              </span>
            </div>
            <button
              type="button"
              onClick={handleClearFile}
              className="p-1 text-slate-400 hover:text-red-600 rounded"
              title="Remove file"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Input Bar with Voice (Mic), Language Selector, and Attachment */}
        <form onSubmit={handleSendMessage} className="p-3 border-t border-slate-200 bg-white flex items-center gap-2">
          {/* Hidden File Input supporting PDF, DOC/DOCX, Images, TXT */}
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileSelect}
            accept=".pdf,.doc,.docx,.png,.jpg,.jpeg,.webp,.txt,.csv"
            className="hidden"
          />

          {/* Attachment Button */}
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            className="p-2.5 rounded-xl border border-slate-300 text-slate-600 hover:text-teal-700 hover:bg-slate-50 transition shrink-0"
            title="Attach medical report, medicine list, image or PDF"
          >
            <Paperclip className="w-4 h-4" />
          </button>

          {/* Language Toggle: EN / हिंदी */}
          <button
            type="button"
            onClick={() => setSpeechLang((prev) => (prev === 'hi-IN' ? 'en-IN' : 'hi-IN'))}
            className={`px-2.5 py-1.5 rounded-xl border text-xs font-bold transition shrink-0 flex items-center gap-1 shadow-2xs ${
              speechLang === 'hi-IN'
                ? 'bg-emerald-50 border-emerald-300 text-emerald-800'
                : 'bg-slate-50 border-slate-300 text-slate-700'
            }`}
            title="Toggle Speech Language: Hindi (हिंदी) or English"
          >
            <Languages className="w-3.5 h-3.5" />
            <span>{speechLang === 'hi-IN' ? 'हिंदी' : 'EN'}</span>
          </button>

          {/* Voice Input Microphone Button */}
          <button
            type="button"
            onClick={toggleListening}
            className={`p-2.5 rounded-xl border transition shrink-0 flex items-center justify-center ${
              isListening
                ? 'bg-red-500 text-white border-red-600 animate-pulse ring-4 ring-red-200 shadow-md'
                : 'border-slate-300 text-slate-600 hover:text-teal-700 hover:bg-teal-50'
            }`}
            title={
              isListening
                ? 'Listening... Click to stop (सुन रहा हूँ... रोकने के लिए क्लिक करें)'
                : `Click to speak in ${speechLang === 'hi-IN' ? 'Hindi (हिंदी में बोलें)' : 'English'}`
            }
          >
            {isListening ? <Mic className="w-4 h-4 animate-bounce" /> : <Mic className="w-4 h-4" />}
          </button>

          {/* Input text field */}
          <input
            type="text"
            placeholder={
              isListening
                ? speechLang === 'hi-IN'
                  ? '🎙️ सुन रहा हूँ... अब हिंदी में बोलिए...'
                  : '🎙️ Listening... Speak now in English...'
                : selectedFile
                ? 'Add a message or press Send to analyze this file...'
                : speechLang === 'hi-IN'
                ? 'लक्षण बताएं या दवाई का नाम पूछें (जैसे जुफेक्स, बुखार, खांसी)...'
                : 'Describe symptoms or mention medicines (e.g. Jufex, Metformin)...'
            }
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            disabled={isSending}
            className={`flex-1 text-xs sm:text-sm border rounded-xl px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-teal-500 disabled:bg-slate-100 transition ${
              isListening
                ? 'border-red-400 bg-red-50/40 text-red-950 placeholder-red-500 font-medium'
                : 'border-slate-300'
            }`}
          />

          <button
            type="submit"
            disabled={isSending || (!inputMessage.trim() && !selectedFile)}
            className="bg-teal-600 hover:bg-teal-700 disabled:bg-slate-300 text-white font-semibold px-4 py-2.5 rounded-xl transition flex items-center gap-1.5 text-xs sm:text-sm shrink-0"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline">Send</span>
          </button>
        </form>
      </div>

      {/* Clinical Transparency Note */}
      <div className="text-[11px] text-slate-500 text-center leading-relaxed">
        <ShieldCheck className="w-3.5 h-3.5 inline text-teal-600 mr-1" />
        Medical reports & medicine lists are analyzed for educational navigation.
        Only a verified doctor can confirm a diagnosis or issue a legally certified prescription.
      </div>
    </div>
  );
};
