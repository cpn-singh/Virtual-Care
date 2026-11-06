/**
 * Unified API Client for Virtual Care Telemedicine
 * Maintained by the Frontend Engineering Team.
 *
 * Provides typed, clean HTTP methods with automatic Bearer token injection
 * and descriptive error propagation.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

class ApiService {
  private getToken(): string | null {
    return localStorage.getItem('vc_auth_token');
  }

  public setToken(token: string) {
    localStorage.setItem('vc_auth_token', token);
  }

  public clearToken() {
    localStorage.removeItem('vc_auth_token');
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      Accept: 'application/json',
      'Bypass-Tunnel-Reminder': 'true',
      'ngrok-skip-browser-warning': 'true',
      ...(options.headers as Record<string, string>),
    };

    // If body is NOT FormData, default to application/json
    if (!(options.body instanceof FormData)) {
      headers['Content-Type'] = 'application/json';
    }

    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        const errorMessage = data?.message || data?.detail || 'An unexpected error occurred.';
        const errorObj = new Error(errorMessage) as any;
        errorObj.status = response.status;
        errorObj.errors = data?.errors || {};
        throw errorObj;
      }

      return data;
    } catch (err: any) {
      // If server unreachable
      if (err.name === 'TypeError' && err.message.includes('fetch')) {
        const netErr = new Error('Could not connect to the telehealth server. Please ensure the backend is running.') as any;
        netErr.status = 0;
        throw netErr;
      }
      throw err;
    }
  }

  // --- Auth Endpoints ---
  public auth = {
    register: (payload: any) => this.request<any>('/auth/register/', { method: 'POST', body: JSON.stringify(payload) }),
    verifyOtp: (payload: { email: string; otp: string; purpose?: string }) =>
      this.request<any>('/auth/verify-email-otp/', { method: 'POST', body: JSON.stringify(payload) }),
    resendOtp: (payload: { email: string; purpose?: string }) =>
      this.request<any>('/auth/resend-email-otp/', { method: 'POST', body: JSON.stringify(payload) }),
    getDevOtp: (email: string) =>
      this.request<any>(`/auth/dev-otp/?email=${encodeURIComponent(email)}`),
    login: (payload: any) => this.request<any>('/auth/login/', { method: 'POST', body: JSON.stringify(payload) }),
    logout: () => this.request<any>('/auth/logout/', { method: 'POST' }),
    passwordResetRequest: (email: string) =>
      this.request<any>('/auth/password-reset/request/', { method: 'POST', body: JSON.stringify({ email }) }),
    passwordResetConfirm: (payload: any) =>
      this.request<any>('/auth/password-reset/confirm/', { method: 'POST', body: JSON.stringify(payload) }),
    getMe: () => this.request<any>('/auth/me/'),
  };

  // --- Patient Endpoints ---
  public patients = {
    getMyProfile: () => this.request<any>('/patients/me/'),
    updateMyProfile: (data: any) => this.request<any>('/patients/me/', { method: 'PATCH', body: JSON.stringify(data) }),
  };

  // --- Doctor Endpoints ---
  public doctors = {
    list: (params?: { search?: string; specialization?: string; city?: string }) => {
      const query = new URLSearchParams();
      if (params) {
        if (params.search && params.search.trim()) query.set('search', params.search.trim());
        if (params.specialization && params.specialization.trim()) query.set('specialization', params.specialization.trim());
        if (params.city && params.city.trim()) query.set('city', params.city.trim());
      }
      const q = query.toString();
      return this.request<any>(`/doctors/${q ? `?${q}` : ''}`);
    },
    getSpecializations: () => this.request<any>('/doctors/specializations/'),
    get: (id: string) => this.request<any>(`/doctors/${id}/`),
    getAvailability: (id: string) => this.request<any>(`/doctors/${id}/availability/`),
    getMyProfile: () => this.request<any>('/doctors/me/profile/'),
    updateMyProfile: (data: any) => this.request<any>('/doctors/me/profile/', { method: 'PATCH', body: JSON.stringify(data) }),
    addAvailability: (data: any) => this.request<any>('/doctors/me/availability/', { method: 'POST', body: JSON.stringify(data) }),
    adminCreate: (payload: any) =>
      this.request<any>('/doctors/admin-create/', { method: 'POST', body: JSON.stringify(payload) }),
  };

  // --- Appointment Endpoints ---
  public appointments = {
    list: () => this.request<any>('/appointments/'),
    get: (id: string) => this.request<any>(`/appointments/${id}/`),
    book: (payload: any) => this.request<any>('/appointments/', { method: 'POST', body: JSON.stringify(payload) }),
    cancel: (id: string, reason?: string) =>
      this.request<any>(`/appointments/${id}/cancel/`, { method: 'POST', body: JSON.stringify({ reason }) }),
    reschedule: (id: string, date: string, time: string) =>
      this.request<any>(`/appointments/${id}/reschedule/`, {
        method: 'POST',
        body: JSON.stringify({ scheduled_date: date, scheduled_time: time }),
      }),
    join: (id: string) => this.request<any>(`/appointments/${id}/join/`, { method: 'POST' }),
  };

  // --- Consultation Endpoints ---
  public consultations = {
    get: (id: string) => this.request<any>(`/consultations/${id}/`),
    end: (id: string) => this.request<any>(`/consultations/${id}/end/`, { method: 'POST' }),
    saveNotes: (id: string, notes: any) =>
      this.request<any>(`/consultations/${id}/notes/`, { method: 'POST', body: JSON.stringify(notes) }),
  };

  // --- AI Care Triage Endpoints ---
  public aiCare = {
    createSession: () => this.request<any>('/ai-care/sessions/', { method: 'POST' }),
    sendMessage: (sessionId: string, message: string, file?: File | null) => {
      if (file) {
        const formData = new FormData();
        formData.append('message', message);
        formData.append('file', file);
        return this.request<any>(`/ai-care/sessions/${sessionId}/messages/`, {
          method: 'POST',
          body: formData,
        });
      }
      return this.request<any>(`/ai-care/sessions/${sessionId}/messages/`, {
        method: 'POST',
        body: JSON.stringify({ message }),
      });
    },
    getHandoff: (sessionId: string) => this.request<any>(`/ai-care/sessions/${sessionId}/handoff/`, { method: 'POST' }),
  };

  // --- Emergency & Hospital Endpoints ---
  public hospitals = {
    getNearby: (payload: { latitude?: number | null; longitude?: number | null; city?: string }) =>
      this.request<any>('/hospitals/nearby/', { method: 'POST', body: JSON.stringify(payload) }),
  };

  // --- Prescription Endpoints ---
  public prescriptions = {
    list: () => this.request<any>('/prescriptions/'),
    get: (id: string) => this.request<any>(`/prescriptions/${id}/`),
    create: (payload: any) => this.request<any>('/prescriptions/', { method: 'POST', body: JSON.stringify(payload) }),
    getPdfDownloadUrl: (id: string) => {
      const token = localStorage.getItem('vc_auth_token');
      const query = token ? `?token=${encodeURIComponent(token)}` : '';
      return `${API_BASE_URL}/prescriptions/${id}/pdf/${query}`;
    },
    downloadPdf: async (id: string, filename?: string) => {
      const token = localStorage.getItem('vc_auth_token');
      const headers: Record<string, string> = {
        'Bypass-Tunnel-Reminder': 'true',
      };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      const response = await fetch(`${API_BASE_URL}/prescriptions/${id}/pdf/`, { headers });
      if (!response.ok) {
        throw new Error('Failed to download prescription PDF.');
      }
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename || `Prescription-${id.slice(0, 8)}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    },
  };

  // --- Billing & Invoices ---
  public billing = {
    createOrder: (appointmentId: string) =>
      this.request<any>('/payments/create-order/', { method: 'POST', body: JSON.stringify({ appointment_id: appointmentId }) }),
    verifyPayment: (orderId: string, transactionId?: string) =>
      this.request<any>('/payments/verify/', {
        method: 'POST',
        body: JSON.stringify({ order_id: orderId, transaction_id: transactionId }),
      }),
    getPayments: () => this.request<any>('/payments/'),
    getInvoices: () => this.request<any>('/invoices/'),
    getInvoice: (id: string) => this.request<any>(`/invoices/${id}/`),
  };

  // --- Notifications ---
  public notifications = {
    list: () => this.request<any>('/notifications/'),
    markAllRead: () => this.request<any>('/notifications/', { method: 'POST' }),
  };
}

export const api = new ApiService();
