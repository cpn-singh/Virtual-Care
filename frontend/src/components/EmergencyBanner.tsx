/**
 * Emergency Safety Banner
 * Author: Clinical Safety Team
 *
 * Placed at the top of critical workflows so patients experiencing
 * life-threatening distress can dial 112 or locate an emergency department with 1-click.
 */

import React from 'react';
import { Link } from 'react-router-dom';
import { PhoneCall, AlertTriangle } from 'lucide-react';

export const EmergencyBanner: React.FC = () => {
  return (
    <div className="bg-red-700 text-white px-4 py-2 text-sm shadow-inner" role="region" aria-label="Emergency warning">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 font-medium">
          <AlertTriangle className="w-4 h-4 shrink-0 text-amber-300" aria-hidden="true" />
          <span>
            Experiencing severe chest pain, stroke symptoms, or choking? <strong>Do not wait for a chat.</strong>
          </span>
        </div>
        <div className="flex items-center gap-3">
          <a
            href="tel:112"
            className="inline-flex items-center gap-1.5 bg-white text-red-700 font-bold px-3 py-1 rounded-full text-xs hover:bg-red-50 transition shadow-sm"
          >
            <PhoneCall className="w-3.5 h-3.5" />
            Dial 112 (Emergency)
          </a>
          <Link
            to="/emergency"
            className="underline text-xs hover:text-red-100 font-medium"
          >
            Find ER Hospitals &rarr;
          </Link>
        </div>
      </div>
    </div>
  );
};
