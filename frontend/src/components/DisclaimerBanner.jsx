import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

export default function DisclaimerBanner() {
  return (
    <div className="bg-amber-950/60 border-b border-amber-500/30 px-4 py-2 text-amber-200 text-xs sm:text-sm">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-2 flex-wrap">
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />
          <span>
            <strong>Screening & Support Aid Only:</strong> This system provides early well-being indicators and confidential preventive recommendations. It is <strong>NEVER a medical diagnostic tool</strong> and must not be used for performance evaluation, grading, or employment decisions.
          </span>
        </div>
        <div className="flex items-center gap-1 text-amber-400 font-medium text-xs bg-amber-900/50 px-2 py-0.5 rounded border border-amber-500/20">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>CBI Ground Truth Scored</span>
        </div>
      </div>
    </div>
  );
}
