# Virtual Care & AI-Assisted Telemedicine Platform

> **Maintained with ❤️ by the Telehealth Engineering & Clinical Governance Team**

Welcome to **Virtual Care**! This is a production-grade, highly accessible telemedicine platform engineered to connect patients with verified doctors, provide safe symptom care navigation, conduct encrypted video consultations, and issue certified digital prescriptions.

---

## 🌟 Key Features

1. **Patient Safety First & Emergency Routing:**
   - Prominent **"I Need Urgent Help"** button available on all screens without requiring login or payment.
   - Deterministic **Red-Flag Clinical Safety Protocol (v1.0.4)** intercepts chest pain, shortness of breath, and stroke signs *before* invoking any language model.
   - Instant 1-click dialing to National Emergency (`112`) and Ambulance (`108`).
   - Geolocation-assisted emergency department directory with offline manual city search fallback.

2. **Secure Authentication & Email OTP:**
   - Custom UUID user architecture with role-based access (Patient, Doctor, Administrator).
   - 6-digit numeric OTP verification; OTPs are hashed using **SHA-256** prior to database storage.
   - 60-second resend cooldown timer and brute-force attempt limits.

3. **Clinician Discovery & Appointment Booking:**
   - Search verified doctors across 6 specialties (General Medicine, Cardiology, Dermatology, Pediatrics, Orthopedics, Psychiatry).
   - Slot-based scheduling with transparent consultation fee display.

4. **Encrypted Video Consultation Rooms:**
   - Authorized pre-call waiting room and device check.
   - Integrated WebRTC / Jitsi Meet video rooms with call controls.
   - In-call clinical note-taking side panel for attending doctors.

5. **Clinician-Signed Digital Prescriptions:**
   - Strict clinical rule: AI **never** prescribes medications or diagnoses.
   - Attending doctors formulate structured prescriptions (medicine, formulation, strength, dose, frequency, duration, instructions).
   - Dynamic server-side PDF generation via ReportLab with digital certification.

6. **Transparent Billing & Invoices:**
   - Server-side fee calculation preventing client-side fee manipulation.
   - Idempotent payment processing and automatic tax invoice generation.

---

## 🚀 Quick Start Guide (For Beginners & Evaluators)

You can run both the backend and frontend locally in less than 2 minutes.

### 1. Start Backend (Django REST Framework)

Open a PowerShell terminal in the repository root:

```powershell
# 1. Navigate to backend
cd backend

# 2. Activate Python virtual environment
.\venv\Scripts\activate

# 3. Apply database migrations (SQLite is ready by default)
python manage.py migrate

# 4. Seed demo accounts, verified doctors, and hospitals
python manage.py seed_demo_data

# 5. Start development API server
python manage.py runserver
```

The API will be live at `http://localhost:8000/api/v1/health/`.

---

### 2. Start Frontend (React + Vite + Tailwind CSS)

Open a second terminal:

```powershell
# 1. Navigate to frontend
cd frontend

# 2. Start Vite development server
npm run dev
```

Open your browser to: **`http://localhost:3000`** (or `http://localhost:5173`).

---

## 🔑 Demo Accounts (Pre-Seeded & Ready)

For effortless testing, the database comes pre-seeded with synthetic accounts. You can also use the 1-click autofill buttons on the login screen:

| Role | Email | Password | Access Capabilities |
| :--- | :--- | :--- | :--- |
| **Patient** | `patient@example.com` | `PatientPass123!` | Book appointments, AI triage, video room, download prescriptions, view invoices |
| **Doctor** | `doctor@example.com` | `DoctorPass123!` | View patient appointments, enter video room, write clinical notes, issue prescriptions |
| **Admin** | `admin@example.com` | `AdminPass123!` | Operations dashboard, verify doctors, oversee clinical compliance |

---

## 🧪 Running Automated Tests

Run the backend test suite:

```powershell
cd backend
.\venv\Scripts\pytest
```

Verifies:
- API readiness & health check
- Registration, OTP generation, and validation lifecycle
- Deterministic AI red flag clinical safety gateway (emergency chest pain interception)
- Prescription PDF generation

---

## 📁 Repository Structure

```text
Virtual Care/
├── frontend/                     # React + Vite + Tailwind CSS
│   ├── src/
│   │   ├── components/           # Navbar, Footer, EmergencyBanner, Modal
│   │   ├── context/              # AuthContext (token & user state)
│   │   ├── pages/                # Patient, Doctor, Admin, and Public views
│   │   ├── services/             # Typed API client
│   │   └── types/                # Domain models & TypeScript interfaces
│   ├── package.json
│   └── vite.config.ts
│
├── backend/                      # Python + Django + Django REST Framework
│   ├── config/                   # settings.py, urls.py, wsgi.py
│   ├── apps/
│   │   ├── accounts/             # Custom User, SHA-256 EmailOTP, AuthToken
│   │   ├── patients/             # Patient profiles, allergies, emergency contacts
│   │   ├── doctors/              # Doctor profiles, specialties, availability
│   │   ├── appointments/         # Scheduling, lifecycle state machine
│   │   ├── consultations/        # WebRTC video room tokens & clinical notes
│   │   ├── ai_care/              # Protocol 1.0.4-CLINICAL red-flag engine
│   │   ├── hospitals/            # Nearby emergency hospital locator
│   │   ├── prescriptions/        # Clinician prescription authoring & PDF generator
│   │   ├── billing/              # Server-side pricing, payments, invoices
│   │   ├── notifications/        # User alerts
│   │   └── audit/                # Security & clinical audit trail
│   ├── tests/                    # Pytest test suite
│   ├── manage.py
│   └── requirements.txt
│
├── docs/
│   ├── API.md                    # Detailed API contract
│   ├── AI_SAFETY.md              # Clinical red flag protocol documentation
│   ├── SECURITY.md               # Encryption, anti-IDOR, and OTP hashing
│   └── DEPLOYMENT.md             # Production hosting with PostgreSQL and NGINX
│
└── README.md
```

---

## ⚖️ Clinical & Legal Notice

This application is configured for synthetic demonstration and clinical governance testing. Do not input real patient identifying health information without formal clinical governance and data protection sign-off.
