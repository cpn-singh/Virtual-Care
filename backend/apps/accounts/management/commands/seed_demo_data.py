"""
Seed Synthetic Demo Data for Virtual Care Platform
Author: Telehealth Platform Core Team

Command: python manage.py seed_demo_data

Generates safe, synthetic demo accounts, specializations, verified clinicians,
availability schedules, hospitals, and sample clinical encounters.
All data is clearly labelled for synthetic staging and development use only.
"""

from datetime import date, time, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import User
from apps.patients.models import PatientProfile
from apps.doctors.models import Specialization, DoctorProfile, DoctorAvailability
from apps.appointments.models import Appointment
from apps.consultations.models import Consultation, ClinicalNote
from apps.prescriptions.models import Prescription, PrescriptionItem
from apps.billing.models import Payment, Invoice
from apps.hospitals.models import Hospital
from common.roles import UserRole


class Command(BaseCommand):
    help = "Seeds synthetic demo data for local testing and developer onboarding."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding synthetic demo data..."))

        # 1. Platform Admin
        admin_user, created = User.objects.get_or_create(
            email="admin@example.com",
            defaults={
                "first_name": "Platform",
                "last_name": "Admin",
                "role": UserRole.ADMIN,
                "is_staff": True,
                "is_superuser": True,
                "is_email_verified": True,
            }
        )
        if created:
            admin_user.set_password("AdminPass123!")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created Admin: admin@example.com / AdminPass123!"))

        # 2. Demo Patient
        patient_user, created = User.objects.get_or_create(
            email="patient@example.com",
            defaults={
                "first_name": "Aarav",
                "last_name": "Mehta",
                "phone_number": "+91 98765 43210",
                "role": UserRole.PATIENT,
                "is_email_verified": True,
            }
        )
        if created:
            patient_user.set_password("PatientPass123!")
            patient_user.save()
            self.stdout.write(self.style.SUCCESS("Created Patient: patient@example.com / PatientPass123!"))

        patient_profile, _ = PatientProfile.objects.get_or_create(
            user=patient_user,
            defaults={
                "date_of_birth": date(1995, 6, 15),
                "gender": "male",
                "blood_group": "B+",
                "city": "Mumbai",
                "allergies": "Penicillin (Mild Rash)",
                "emergency_contact_name": "Sunita Mehta",
                "emergency_contact_phone": "+91 98765 00000",
                "emergency_contact_relation": "Mother",
            }
        )

        # 3. Specializations
        specs_data = [
            ("General Medicine", "general-medicine", "Primary care, fevers, colds, fatigue, chronic symptom reviews.", "Stethoscope"),
            ("Cardiology", "cardiology", "Heart health, hypertension monitoring, lipid care, chest discomfort evaluation.", "HeartPulse"),
            ("Dermatology", "dermatology", "Skin rashes, acne, hair fall, dermatitis, allergies.", "Sparkles"),
            ("Pediatrics", "pediatrics", "Infant and child wellness, childhood immunizations, growth guidance.", "Baby"),
            ("Orthopedics", "orthopedics", "Joint pain, knee osteoarthritis, back stiffness, sports injuries.", "Activity"),
            ("Psychiatry & Wellness", "psychiatry", "Anxiety, depression, stress management, sleep support.", "Brain"),
        ]

        specializations = {}
        for name, slug, desc, icon in specs_data:
            spec, _ = Specialization.objects.get_or_create(
                slug=slug,
                defaults={"name": name, "description": desc, "icon_name": icon}
            )
            specializations[slug] = spec

        # 4. Verified Doctors
        doctors_data = [
            {
                "email": "doctor@example.com",
                "first_name": "Ananya",
                "last_name": "Sharma",
                "spec_slug": "general-medicine",
                "qualifications": "MBBS, MD (Internal Medicine - AIIMS)",
                "license": "MCI-48291",
                "experience": 9,
                "city": "New Delhi",
                "fee": 500.00,
                "bio": "Senior Consultant in Internal Medicine with 9+ years of clinical and virtual triage experience.",
                "rating": 4.95,
            },
            {
                "email": "dr.rajesh@example.com",
                "first_name": "Rajesh",
                "last_name": "Varma",
                "spec_slug": "cardiology",
                "qualifications": "MBBS, MD, DM (Cardiology - KEM)",
                "license": "MMC-31849",
                "experience": 15,
                "city": "Mumbai",
                "fee": 900.00,
                "bio": "Cardiologist specializing in preventive heart health, hypertension control, and lifestyle medicine.",
                "rating": 4.98,
            },
            {
                "email": "dr.priya@example.com",
                "first_name": "Priya",
                "last_name": "Nair",
                "spec_slug": "dermatology",
                "qualifications": "MBBS, DVD, MD (Dermatology)",
                "license": "KMC-77120",
                "experience": 7,
                "city": "Bengaluru",
                "fee": 600.00,
                "bio": "Board-certified dermatologist focusing on inflammatory skin conditions, acne, and telehealth consultations.",
                "rating": 4.92,
            },
            {
                "email": "dr.vikram@example.com",
                "first_name": "Vikram",
                "last_name": "Sen",
                "spec_slug": "pediatrics",
                "qualifications": "MBBS, DCH, MD (Pediatrics)",
                "license": "WBMC-92041",
                "experience": 12,
                "city": "Kolkata",
                "fee": 550.00,
                "bio": "Empathetic pediatrician passionate about child developmental milestones, nutrition, and pediatric care.",
                "rating": 4.96,
            },
        ]

        created_doctors = []
        for d in doctors_data:
            doc_user, u_created = User.objects.get_or_create(
                email=d["email"],
                defaults={
                    "first_name": d["first_name"],
                    "last_name": d["last_name"],
                    "role": UserRole.DOCTOR,
                    "is_email_verified": True,
                }
            )
            if u_created:
                doc_user.set_password("DoctorPass123!")
                doc_user.save()

            doc_profile, _ = DoctorProfile.objects.get_or_create(
                user=doc_user,
                defaults={
                    "specialization": specializations.get(d["spec_slug"]),
                    "qualifications": d["qualifications"],
                    "license_number": d["license"],
                    "experience_years": d["experience"],
                    "city": d["city"],
                    "consultation_fee": d["fee"],
                    "bio": d["bio"],
                    "rating": d["rating"],
                    "is_verified": True,
                    "is_available_for_telehealth": True,
                }
            )
            created_doctors.append(doc_profile)

            # Weekly availability slots (Monday through Saturday)
            for day in range(6):
                DoctorAvailability.objects.get_or_create(
                    doctor=doc_profile,
                    day_of_week=day,
                    start_time=time(9, 0),
                    end_time=time(13, 0),
                    defaults={"slot_duration_minutes": 30, "is_active": True}
                )
                DoctorAvailability.objects.get_or_create(
                    doctor=doc_profile,
                    day_of_week=day,
                    start_time=time(14, 0),
                    end_time=time(18, 0),
                    defaults={"slot_duration_minutes": 30, "is_active": True}
                )

        self.stdout.write(self.style.SUCCESS("Created Doctors: doctor@example.com / DoctorPass123!"))

        # 5. Verified Emergency Hospitals
        hospitals_data = [
            ("All India Institute of Medical Sciences (AIIMS)", "Sri Aurobindo Marg, Ansari Nagar", "New Delhi", "Delhi", "+91 11 2658 8500", "112", 28.5672, 77.2100),
            ("Safdarjung Hospital Emergency Trauma Centre", "Ring Road, Opposite AIIMS", "New Delhi", "Delhi", "+91 11 2616 5060", "112", 28.5701, 77.2081),
            ("King Edward Memorial (KEM) Hospital", "Acharya Donde Marg, Parel", "Mumbai", "Maharashtra", "+91 22 2410 7000", "112", 19.0024, 72.8427),
            ("Lilavati Hospital & Research Centre", "A-791, Bandra Reclamation, Bandra West", "Mumbai", "Maharashtra", "+91 22 2675 1000", "112", 19.0514, 72.8288),
            ("Victoria Hospital Emergency Department", "Fort Road, near City Market", "Bengaluru", "Karnataka", "+91 80 2670 1150", "112", 12.9625, 77.5746),
            ("Manipal Hospital 24/7 Emergency", "98, HAL Old Airport Road, Kodihalli", "Bengaluru", "Karnataka", "+91 80 2502 4444", "112", 12.9592, 77.6534),
            ("Apollo Hospitals Emergency Trauma Care", "Greams Lane, 21 Greams Road, Thousand Lights", "Chennai", "Tamil Nadu", "+91 44 2829 0200", "112", 13.0604, 80.2505),
            ("Nizam's Institute of Medical Sciences (NIMS)", "Punjagutta", "Hyderabad", "Telangana", "+91 40 2348 9000", "112", 17.4265, 78.4528),
        ]

        for name, addr, city, state, phone, er_phone, lat, lon in hospitals_data:
            Hospital.objects.get_or_create(
                name=name,
                defaults={
                    "address": addr,
                    "city": city,
                    "state": state,
                    "phone_number": phone,
                    "emergency_phone": er_phone,
                    "latitude": lat,
                    "longitude": lon,
                    "has_emergency_room": True,
                    "has_trauma_center": True,
                    "is_24_7": True,
                }
            )

        # 6. Sample Completed Appointment & Digital Prescription
        primary_doctor = created_doctors[0]
        sample_date = timezone.now().date() + timedelta(days=1)
        appt, appt_created = Appointment.objects.get_or_create(
            patient=patient_profile,
            doctor=primary_doctor,
            scheduled_date=sample_date,
            scheduled_time=time(10, 30),
            defaults={
                "reason_for_visit": "Persistent mild cough and sore throat for 3 days",
                "patient_symptoms_summary": "Intake: Dry cough, throat tickle, no chest pain, no shortness of breath.",
                "consultation_fee": primary_doctor.consultation_fee,
                "status": Appointment.STATUS_CONFIRMED,
                "payment_status": Appointment.PAYMENT_PAID,
            }
        )

        if appt_created:
            # Payment & Invoice
            payment, _ = Payment.objects.get_or_create(
                appointment=appt,
                patient=patient_profile,
                defaults={
                    "amount": primary_doctor.consultation_fee,
                    "currency": "INR",
                    "order_id": f"demo_order_{appt.id.hex[:8]}",
                    "transaction_id": f"demo_pay_{appt.id.hex[:8]}",
                    "idempotency_key": f"demo_key_{appt.id.hex[:8]}",
                    "status": Payment.STATUS_PAID,
                    "verified_at": timezone.now(),
                }
            )

            Invoice.objects.get_or_create(
                payment=payment,
                defaults={
                    "invoice_number": f"INV-2026-DEMO-001",
                    "patient_name": patient_user.full_name,
                    "doctor_name": f"Dr. {primary_doctor.user.full_name}",
                    "consultation_fee": primary_doctor.consultation_fee,
                    "tax_amount": 0.00,
                    "total_amount": primary_doctor.consultation_fee,
                    "status": Invoice.STATUS_PAID,
                }
            )

            # Sample Consultation & Issued Prescription
            consultation, _ = Consultation.objects.get_or_create(
                appointment=appt,
                defaults={
                    "room_id": f"room-{appt.id.hex[:8]}",
                    "status": Consultation.STATUS_COMPLETED,
                    "started_at": timezone.now() - timedelta(minutes=25),
                    "ended_at": timezone.now() - timedelta(minutes=5),
                }
            )

            ClinicalNote.objects.get_or_create(
                consultation=consultation,
                doctor=primary_doctor,
                defaults={
                    "chief_complaint": "Sore throat and dry hacking cough for 3 days",
                    "clinical_observations": "Pharynx mildly hyperemic, no tonsillar exudate. Clear lungs bilaterally.",
                    "diagnosis_summary": "Acute viral pharyngitis / upper respiratory tract infection",
                    "treatment_advice": "Steam inhalation twice daily, warm salt-water gargles, adequate oral hydration.",
                }
            )

            rx, rx_created = Prescription.objects.get_or_create(
                patient=patient_profile,
                doctor=primary_doctor,
                appointment=appt,
                consultation=consultation,
                defaults={
                    "status": Prescription.STATUS_ISSUED,
                    "diagnosis": "Acute Viral Pharyngitis & Upper Respiratory Irritation",
                    "doctor_notes": "Warm salt-water gargles 3 times a day. If fever exceeds 101°F or persists over 48 hours, contact the clinic.",
                    "issued_at": timezone.now(),
                }
            )
            if rx_created:
                PrescriptionItem.objects.create(
                    prescription=rx,
                    medicine_name="Paracetamol",
                    formulation="Tablet",
                    strength="650 mg",
                    dose="1 tablet",
                    frequency="As needed every 6 hours (Max 3/day)",
                    duration="3 days",
                    instructions="Take after food if fever or sore throat pain persists."
                )
                PrescriptionItem.objects.create(
                    prescription=rx,
                    medicine_name="Warm Saline & Lozenges",
                    formulation="Lozenges",
                    strength="Standard",
                    dose="1 lozenge",
                    frequency="Every 4-6 hours",
                    duration="5 days",
                    instructions="Dissolve slowly in mouth."
                )

        self.stdout.write(self.style.SUCCESS("Successfully seeded synthetic demo data!"))
