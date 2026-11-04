/**
 * Core Data Models and Domain Interfaces
 * Maintained by the Frontend Engineering Team.
 *
 * Designed to be clean, intuitive, and easy for beginners to understand.
 */

export type UserRole = 'patient' | 'doctor' | 'admin';

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  phone_number?: string;
  role: UserRole;
  is_email_verified: boolean;
  date_joined: string;
}

export interface Specialization {
  id: string;
  name: string;
  slug: string;
  description: string;
  icon_name: string;
}

export interface Doctor {
  id: string;
  user: User;
  specialization?: Specialization;
  license_number?: string;
  qualifications: string;
  experience_years: number;
  bio: string;
  city: string;
  consultation_fee: string;
  is_verified: boolean;
  is_available_for_telehealth: boolean;
  rating: string | number;
  total_consultations: number;
}

export interface DoctorAvailability {
  id: string;
  day_of_week: number;
  day_name: string;
  start_time: string;
  end_time: string;
  is_active: boolean;
}

export interface PatientProfile {
  id: string;
  user: User;
  date_of_birth?: string;
  gender: string;
  blood_group: string;
  address?: string;
  city?: string;
  allergies?: string;
  chronic_conditions?: string;
  current_medications?: string;
  emergency_contact_name?: string;
  emergency_contact_phone?: string;
  emergency_contact_relation?: string;
  consent_ai_triage: boolean;
}

export type AppointmentStatus =
  | 'pending'
  | 'confirmed'
  | 'in_progress'
  | 'completed'
  | 'cancelled'
  | 'rescheduled';

export type PaymentStatus = 'pending' | 'paid' | 'refunded' | 'waived';

export interface Appointment {
  id: string;
  patient: PatientProfile;
  doctor: Doctor;
  scheduled_date: string;
  scheduled_time: string;
  duration_minutes: number;
  status: AppointmentStatus;
  payment_status: PaymentStatus;
  consultation_fee: string;
  reason_for_visit: string;
  patient_symptoms_summary?: string;
  cancellation_reason?: string;
  created_at: string;
}

export interface ClinicalNote {
  id: string;
  chief_complaint: string;
  clinical_observations: string;
  diagnosis_summary: string;
  treatment_advice: string;
  created_at: string;
}

export interface Consultation {
  id: string;
  appointment: Appointment;
  room_id: string;
  status: 'waiting' | 'active' | 'completed' | 'disconnected';
  started_at?: string;
  ended_at?: string;
  clinical_note?: ClinicalNote;
}

export interface PrescriptionItem {
  id?: string;
  medicine_name: string;
  formulation: string;
  strength: string;
  dose: string;
  frequency: string;
  duration: string;
  instructions: string;
}

export interface Prescription {
  id: string;
  patient: PatientProfile;
  doctor: Doctor;
  appointment?: string;
  consultation?: string;
  status: 'draft' | 'issued' | 'amended' | 'cancelled';
  diagnosis: string;
  doctor_notes?: string;
  version: number;
  issued_at?: string;
  items: PrescriptionItem[];
  created_at: string;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  patient_name: string;
  doctor_name: string;
  consultation_fee: string;
  tax_amount: string;
  total_amount: string;
  status: 'paid' | 'refunded';
  created_at: string;
}

export interface Hospital {
  id: string;
  name: string;
  address: string;
  city: string;
  state?: string;
  phone_number: string;
  emergency_phone: string;
  latitude?: number;
  longitude?: number;
  has_emergency_room: boolean;
  has_trauma_center: boolean;
  has_icu: boolean;
  is_24_7: boolean;
  distance_km?: number;
  directions_link?: string;
}

export interface AIMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  category?: string;
  urgency?: string;
  emergency_action_required?: boolean;
  recommended_next_step?: string;
  detected_medicines?: any[];
  detected_lab_findings?: any[];
  draft_prescription?: any[];
  can_book_in_chat?: boolean;
  recommended_doctor?: any;
  created_at?: string;
}
