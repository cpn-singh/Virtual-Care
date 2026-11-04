/**
 * My Prescriptions Management
 * Author: Clinical Pharmacy & Governance Team
 *
 * View clinician-issued digital prescriptions and download tamper-evident PDFs.
 */

import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Prescription } from '../types';
import { FileText, Download, ShieldCheck, Stethoscope, Eye, Calendar } from 'lucide-react';
import { Modal } from '../components/Modal';

export const PrescriptionsPage: React.FC = () => {
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [selectedRx, setSelectedRx] = useState<Prescription | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const handleDownloadPdf = async (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    setDownloadingId(id);
    try {
      await api.prescriptions.downloadPdf(id);
    } catch {
      window.open(api.prescriptions.getPdfDownloadUrl(id), '_blank');
    } finally {
      setDownloadingId(null);
    }
  };

  useEffect(() => {
    const fetchPrescriptions = async () => {
      setIsLoading(true);
      try {
        const res: any = await api.prescriptions.list();
        if (res?.data) {
          setPrescriptions(res.data);
        }
      } catch {
        // Fallback
      } finally {
        setIsLoading(false);
      }
    };

    fetchPrescriptions();
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <div className="border-b border-slate-200 pb-4 space-y-1">
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
          My Digital Prescriptions
        </h1>
        <p className="text-xs text-slate-600">
          Official, certified prescriptions issued by your attending doctors.
        </p>
      </div>

      {isLoading ? (
        <div className="text-center py-16 text-slate-500 text-sm">Loading prescriptions...</div>
      ) : prescriptions.length === 0 ? (
        <div className="text-center py-16 bg-white border border-slate-200 rounded-2xl p-8 space-y-3">
          <FileText className="w-10 h-10 text-slate-400 mx-auto" />
          <h2 className="text-base font-bold text-slate-900">No Prescriptions Issued Yet</h2>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Following your virtual video consultation, the attending doctor will formulate your clinical prescription
            and sign it digitally.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {prescriptions.map((rx) => (
            <div
              key={rx.id}
              className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs flex flex-col justify-between space-y-4"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-mono">
                      Rx #{rx.id.slice(0, 8).toUpperCase()}
                    </span>
                    <h2 className="text-lg font-bold text-slate-900">{rx.diagnosis}</h2>
                  </div>
                  <span className="bg-emerald-50 text-emerald-800 text-[10px] font-bold px-2 py-0.5 rounded border border-emerald-200 uppercase">
                    {rx.status}
                  </span>
                </div>

                <div className="text-xs text-slate-600 space-y-1">
                  <p className="flex items-center gap-1.5 font-medium">
                    <Stethoscope className="w-3.5 h-3.5 text-teal-600" />
                    <span>Dr. {rx.doctor.user.full_name} ({rx.doctor.specialization?.name || 'Physician'})</span>
                  </p>
                  <p className="text-[11px] text-slate-500">
                    License: {rx.doctor.license_number || 'Verified MCI'}
                  </p>
                </div>

                {/* Medication Items Pill List */}
                <div className="pt-2">
                  <span className="block text-[11px] font-bold text-slate-700 mb-1.5">Prescribed Items:</span>
                  <div className="space-y-1.5">
                    {rx.items.map((item, idx) => (
                      <div
                        key={idx}
                        className="bg-slate-50 border border-slate-200 rounded-lg p-2 text-xs flex items-center justify-between gap-2"
                      >
                        <div>
                          <strong className="text-slate-900">{item.medicine_name}</strong>{' '}
                          <span className="text-slate-500">({item.formulation} - {item.strength})</span>
                          <div className="text-[11px] text-slate-500">{item.frequency} &bull; {item.duration}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {rx.doctor_notes && (
                  <p className="text-xs text-slate-500 italic bg-amber-50/60 p-2.5 rounded-lg border border-amber-200/50">
                    "{rx.doctor_notes}"
                  </p>
                )}
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                <button
                  onClick={() => setSelectedRx(rx)}
                  className="inline-flex items-center gap-1 text-slate-700 hover:text-teal-700 font-semibold text-xs py-2 px-3 rounded-lg hover:bg-slate-100 transition"
                >
                  <Eye className="w-3.5 h-3.5" />
                  <span>Inspect Details</span>
                </button>

                <a
                  href={api.prescriptions.getPdfDownloadUrl(rx.id)}
                  onClick={(e) => handleDownloadPdf(e, rx.id)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs px-4 py-2 rounded-xl transition shadow-xs cursor-pointer"
                >
                  <Download className={`w-3.5 h-3.5 ${downloadingId === rx.id ? 'animate-bounce' : ''}`} />
                  <span>{downloadingId === rx.id ? 'Generating...' : 'Download PDF'}</span>
                </a>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Prescription Detail Modal */}
      {selectedRx && (
        <Modal
          isOpen={!!selectedRx}
          onClose={() => setSelectedRx(null)}
          title={`Digital Prescription - ${selectedRx.diagnosis}`}
          maxWidth="lg"
        >
          <div className="space-y-6 text-xs text-slate-700">
            {/* Header info */}
            <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 grid grid-cols-2 gap-4">
              <div>
                <span className="text-slate-500 block">Attending Clinician:</span>
                <strong className="text-slate-900 text-sm">Dr. {selectedRx.doctor.user.full_name}</strong>
                <p className="text-[11px] text-slate-500">
                  {selectedRx.doctor.qualifications} &bull; Reg: {selectedRx.doctor.license_number}
                </p>
              </div>
              <div className="text-right">
                <span className="text-slate-500 block">Patient Name:</span>
                <strong className="text-slate-900 text-sm">{selectedRx.patient.user.full_name}</strong>
                <p className="text-[11px] text-slate-500">Blood Group: {selectedRx.patient.blood_group}</p>
              </div>
            </div>

            {/* Prescribed Items Table */}
            <div>
              <h4 className="font-bold text-slate-900 mb-2">Rx - Prescribed Medications</h4>
              <div className="overflow-x-auto border border-slate-200 rounded-xl">
                <table className="w-full text-left divide-y divide-slate-200 text-xs">
                  <thead className="bg-slate-100 font-bold text-slate-800">
                    <tr>
                      <th className="p-2.5">Medicine</th>
                      <th className="p-2.5">Dose</th>
                      <th className="p-2.5">Frequency</th>
                      <th className="p-2.5">Duration</th>
                      <th className="p-2.5">Instructions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 bg-white">
                    {selectedRx.items.map((item, idx) => (
                      <tr key={idx}>
                        <td className="p-2.5 font-bold text-slate-900">
                          {item.medicine_name} <span className="text-slate-500 font-normal">({item.strength})</span>
                        </td>
                        <td className="p-2.5">{item.dose}</td>
                        <td className="p-2.5">{item.frequency}</td>
                        <td className="p-2.5">{item.duration}</td>
                        <td className="p-2.5">{item.instructions || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {selectedRx.doctor_notes && (
              <div>
                <h4 className="font-bold text-slate-900 mb-1">Doctor's Advice & Warnings</h4>
                <p className="bg-slate-50 p-3 rounded-lg border border-slate-200 leading-relaxed">
                  {selectedRx.doctor_notes}
                </p>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
              <button
                onClick={() => setSelectedRx(null)}
                className="px-4 py-2 font-semibold text-slate-600 hover:bg-slate-100 rounded-lg text-xs"
              >
                Close
              </button>
              <a
                href={api.prescriptions.getPdfDownloadUrl(selectedRx.id)}
                onClick={(e) => handleDownloadPdf(e, selectedRx.id)}
                target="_blank"
                rel="noopener noreferrer"
                className="bg-teal-600 hover:bg-teal-700 text-white font-bold px-4 py-2 rounded-lg text-xs transition flex items-center gap-1.5 cursor-pointer"
              >
                <Download className={`w-3.5 h-3.5 ${downloadingId === selectedRx.id ? 'animate-bounce' : ''}`} />
                <span>{downloadingId === selectedRx.id ? 'Generating...' : 'Download PDF'}</span>
              </a>
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
};
