# Security & Healthcare Privacy Architecture

**Maintained by:** Telehealth Security & Compliance Team  
**Compliance Standard:** Healthcare Data Protection & Telemedicine Practice Guidelines

---

## 1. Authentication & Identity Management

- **Custom UUID User Model:** Users (`User`) use secure UUID primary keys to prevent sequential ID enumeration attacks.
- **Email OTP Verification:**
  - 6-digit cryptographically secure numeric codes (`secrets.randbelow`).
  - **Zero Plaintext Storage:** OTPs are hashed using one-way SHA-256 (`hashlib.sha256`) before being written to the database.
  - **Cooldown Limits:** Enforces a 60-second cooldown between resend attempts to protect against SMS/email bombing.
  - **Brute-Force Protection:** Automatically invalidates any OTP after 5 failed attempts.
  - **Short Time-to-Live (TTL):** OTPs expire after 10 minutes.
- **Session Tokens (`AuthToken`):**
  - High-entropy 64-character hex tokens generated with `secrets.token_hex(32)`.
  - Stored with an explicit expiration date and updated `last_used_at` timestamp.
  - Easy revocation on logout or password reset.

---

## 2. Object-Level Access Control (Anti-IDOR)

Hiding buttons on the frontend is never treated as security. Every API endpoint enforces strict role and ownership checks:

- **Patients:** Can only view and download their own appointments, health profiles, prescriptions, and invoices.
- **Doctors:** Can only inspect medical records of patients with whom they have an active or confirmed consultation.
- **Administrators:** Sensitive patient clinical notes and prescriptions cannot be silently modified by platform administrators.
- **Prescription Integrity:** Only verified, licensed clinicians (`role='doctor'` and `is_verified=True`) can author and sign digital prescriptions. Patients have read-only access.

---

## 3. Financial Integrity & Billing Security

- **Server-Side Pricing:** Consultation fees are derived strictly from the verified doctor's database rate, never client-submitted values.
- **Idempotency Keys:** Unique idempotency keys are enforced on every payment order to prevent duplicate charges on network retries.
- **Immutable Invoices:** Payment confirmations automatically mint tamper-evident invoices (`Invoice`).

---

## 4. Protected Documents & PDF Generation

- **On-the-Fly Secure PDF Streaming:** Clinician-signed digital prescriptions are rendered dynamically using ReportLab and served over authorized HTTP responses (`GET /api/v1/prescriptions/{id}/pdf/`).
- Public media URLs are disabled for sensitive medical records.
