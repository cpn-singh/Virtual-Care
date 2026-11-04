# Virtual Care Platform API Reference

Base URL: `http://localhost:8000/api/v1/`  
Format: `application/json`

---

## 1. System Health

### Check Health & Readiness
`GET /api/v1/health/`  
**Auth:** None  
**Response:**
```json
{
  "status": "success",
  "message": "All services operational.",
  "data": {
    "status": "healthy",
    "service": "Virtual Care Telemedicine API",
    "version": "1.0.0",
    "safety_protocol": "1.0.4-CLINICAL"
  }
}
```

---

## 2. Authentication

### User Registration
`POST /api/v1/auth/register/`  
**Payload:**
```json
{
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "SecurePassword123!",
  "role": "patient",
  "phone_number": "+91 98765 43210"
}
```

### Verify Email OTP
`POST /api/v1/auth/verify-email-otp/`  
**Payload:**
```json
{
  "email": "user@example.com",
  "otp": "123456"
}
```

### Resend OTP
`POST /api/v1/auth/resend-email-otp/`  
**Payload:**
```json
{
  "email": "user@example.com"
}
```

### Login
`POST /api/v1/auth/login/`  
**Payload:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

### Get Current User Profile
`GET /api/v1/auth/me/`  
**Auth:** `Authorization: Bearer <token>`

---

## 3. Doctors & Specialties

### List Specializations
`GET /api/v1/doctors/specializations/`

### Search Verified Doctors
`GET /api/v1/doctors/?search=Ananya&specialization=general-medicine`

### Doctor Profile Detail
`GET /api/v1/doctors/<uuid:id>/`

### Doctor Availability Schedule
`GET /api/v1/doctors/<uuid:id>/availability/`

---

## 4. Appointments & Video Encounters

### List Appointments
`GET /api/v1/appointments/`  
**Auth:** `Authorization: Bearer <token>`

### Book Appointment
`POST /api/v1/appointments/`  
**Payload:**
```json
{
  "doctor_id": "<uuid:doctor_id>",
  "scheduled_date": "2026-11-06",
  "scheduled_time": "10:30:00",
  "reason_for_visit": "Persistent sore throat and fever for 2 days"
}
```

### Join Video Consultation Room
`POST /api/v1/appointments/<uuid:id>/join/`  
**Auth:** `Authorization: Bearer <token>`  
**Response:**
```json
{
  "status": "success",
  "data": {
    "consultation_id": "<uuid:consultation_id>",
    "appointment_id": "<uuid:appointment_id>",
    "credentials": {
      "room_name": "VirtualCare-...",
      "display_name": "Aarav Mehta",
      "server_url": "https://meet.jit.si"
    }
  }
}
```

---

## 5. AI Care Assistant & Emergency Locator

### Start Triage Session
`POST /api/v1/ai-care/sessions/`  
**Auth:** None required for emergency access

### Send Symptom Message
`POST /api/v1/ai-care/sessions/<uuid:id>/messages/`  
**Payload:**
```json
{
  "message": "I have been experiencing a mild dry cough and slight fatigue since yesterday."
}
```

### Find Nearby Emergency Hospitals
`POST /api/v1/hospitals/nearby/`  
**Payload:**
```json
{
  "latitude": 19.0760,
  "longitude": 72.8777,
  "city": "Mumbai"
}
```

---

## 6. Prescriptions & Invoices

### List Prescriptions
`GET /api/v1/prescriptions/`  
**Auth:** `Authorization: Bearer <token>`

### Download Official Prescription PDF
`GET /api/v1/prescriptions/<uuid:id>/pdf/`  
**Auth:** `Authorization: Bearer <token>`  
**Response:** `Content-Type: application/pdf`

### List Invoices
`GET /api/v1/invoices/`  
**Auth:** `Authorization: Bearer <token>`
