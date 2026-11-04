/**
 * Billing, Payments & Invoices Screen
 * Author: Financial Systems & Billing Operations Team
 */

import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Invoice, Appointment } from '../types';
import { Receipt, CreditCard, CheckCircle2, Clock, AlertCircle } from 'lucide-react';

export const InvoicesPage: React.FC = () => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [pendingAppointments, setPendingAppointments] = useState<Appointment[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [processingApptId, setProcessingApptId] = useState<string | null>(null);
  const [paymentSuccessMsg, setPaymentSuccessMsg] = useState<string>('');

  const loadBillingData = async () => {
    setIsLoading(true);
    try {
      const [invRes, apptRes]: any = await Promise.all([
        api.billing.getInvoices(),
        api.appointments.list(),
      ]);

      if (invRes?.data) setInvoices(invRes.data);
      if (apptRes?.data) {
        // Find appointments where payment is pending
        const pending = apptRes.data.filter(
          (a: Appointment) => a.payment_status === 'pending' && a.status !== 'cancelled'
        );
        setPendingAppointments(pending);
      }
    } catch {
      // Fallback
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadBillingData();
  }, []);

  const handlePayNow = async (appt: Appointment) => {
    setProcessingApptId(appt.id);
    setPaymentSuccessMsg('');
    try {
      // 1. Create payment order with trusted server pricing
      const orderRes: any = await api.billing.createOrder(appt.id);
      const orderId = orderRes?.data?.order_id;

      // 2. Settle payment via server verification
      await api.billing.verifyPayment(orderId, `pay_sim_${Date.now()}`);

      setPaymentSuccessMsg(`Payment of ₹${appt.consultation_fee} confirmed! Invoice generated.`);
      loadBillingData();
    } catch {
      // Fallback
    } finally {
      setProcessingApptId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      <div className="border-b border-slate-200 pb-4 space-y-1">
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
          Billing & Invoices
        </h1>
        <p className="text-xs text-slate-600">
          Transparent consultation payments and verifiable tax invoices.
        </p>
      </div>

      {paymentSuccessMsg && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-900 p-4 rounded-xl text-xs font-semibold flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>{paymentSuccessMsg}</span>
        </div>
      )}

      {/* 1. Pending Consultation Payments */}
      {pendingAppointments.length > 0 && (
        <section className="bg-amber-50/70 border border-amber-200 rounded-2xl p-6 space-y-4">
          <div className="flex items-center gap-2 text-amber-900 font-bold text-sm">
            <Clock className="w-4 h-4 text-amber-600" />
            <span>Pending Consultation Fees ({pendingAppointments.length})</span>
          </div>

          <div className="space-y-3">
            {pendingAppointments.map((appt) => (
              <div
                key={appt.id}
                className="bg-white border border-amber-200/80 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="space-y-1 text-xs">
                  <span className="font-bold text-slate-900 text-sm">
                    Consultation with Dr. {appt.doctor.user.full_name}
                  </span>
                  <p className="text-slate-500">
                    {appt.doctor.specialization?.name || 'General Physician'} &bull; {appt.scheduled_date} at{' '}
                    {appt.scheduled_time}
                  </p>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className="text-[10px] text-slate-400 uppercase font-semibold">Amount</span>
                    <div className="text-base font-black text-slate-900">₹{appt.consultation_fee}</div>
                  </div>

                  <button
                    onClick={() => handlePayNow(appt)}
                    disabled={processingApptId === appt.id}
                    className="bg-teal-600 hover:bg-teal-700 disabled:bg-slate-300 text-white font-bold text-xs px-4 py-2.5 rounded-xl transition flex items-center gap-1.5 shadow-xs"
                  >
                    <CreditCard className="w-4 h-4" />
                    <span>{processingApptId === appt.id ? 'Processing...' : 'Pay Fee (Sandbox)'}</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* 2. Paid Invoices List */}
      <section className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        <h2 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
          <Receipt className="w-4 h-4 text-teal-600" />
          <span>Payment History & Receipts</span>
        </h2>

        {isLoading ? (
          <div className="text-center py-12 text-slate-500 text-sm">Loading billing records...</div>
        ) : invoices.length === 0 ? (
          <p className="text-xs text-slate-500 py-6 text-center">No payment transactions recorded yet.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs divide-y divide-slate-200">
              <thead className="bg-slate-50 font-bold text-slate-700">
                <tr>
                  <th className="p-3">Invoice #</th>
                  <th className="p-3">Doctor</th>
                  <th className="p-3">Date</th>
                  <th className="p-3">Fee</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {invoices.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50/60 transition">
                    <td className="p-3 font-mono font-bold text-teal-800">{inv.invoice_number}</td>
                    <td className="p-3 font-medium text-slate-900">{inv.doctor_name}</td>
                    <td className="p-3 text-slate-500">{new Date(inv.created_at).toLocaleDateString()}</td>
                    <td className="p-3 font-bold text-slate-900">₹{inv.total_amount}</td>
                    <td className="p-3">
                      <span className="bg-emerald-50 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded border border-emerald-200 uppercase">
                        {inv.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
};
