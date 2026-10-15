import React, { useState, useEffect } from 'react';
import { api } from '../api';
import {
  Activity, AlertTriangle, ShieldCheck, Heart, Clock, CheckCircle2,
  Lock, Download, Trash2, ArrowUpRight, Sparkles, UserCheck, RefreshCw
} from 'lucide-react';

export default function EmployeeDashboard({ user, onTakeAssessment, onUserUpdated }) {
  const [latestAssessment, setLatestAssessment] = useState(null);
  const [alerts, setAlerts] = useState([]);
  const [interventions, setInterventions] = useState([]);
  const [consentOptIn, setConsentOptIn] = useState(user?.current_consent || false);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const [latestData, alertsData, interData] = await Promise.all([
        api.getLatestAssessment().catch(() => null),
        api.getMyAlerts().catch(() => []),
        api.getMyInterventions().catch(() => [])
      ]);
      setLatestAssessment(latestData);
      setAlerts(alertsData);
      setInterventions(interData);
    } catch (err) {
      console.error("Error loading employee dashboard:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleConsentToggle = async () => {
    const nextState = !consentOptIn;
    try {
      await api.toggleConsent(nextState);
      setConsentOptIn(nextState);
      if (onUserUpdated) onUserUpdated();
    } catch (err) {
      alert("Failed to update privacy sharing settings.");
    }
  };

  const handleUpdateIntervention = async (id, newStatus) => {
    try {
      await api.updateInterventionStatus(id, newStatus);
      setInterventions(prev => prev.map(i => i.id === id ? { ...i, status: newStatus } : i));
    } catch (err) {
      alert("Failed to update action status.");
    }
  };

  const handleExportData = async () => {
    setExporting(true);
    try {
      const data = await api.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `my_burnout_data_${user.email}.json`;
      a.click();
    } catch (err) {
      alert("Failed to export data.");
    } finally {
      setExporting(false);
    }
  };

  const handleDeleteData = async () => {
    if (window.confirm("Are you sure? This will permanently delete your account and assessment records.")) {
      try {
        await api.deleteData();
        alert("Your records have been deleted.");
        window.location.reload();
      } catch (err) {
        alert("Failed to delete records.");
      }
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-16 text-center text-slate-400">
        <Activity className="w-8 h-8 animate-spin mx-auto text-sky-400 mb-3" />
        Loading your well-being overview...
      </div>
    );
  }

  const activeUrgentAlert = alerts.find(a => a.severity === 'Urgent' && a.status === 'open');

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-6">
      {/* 1. Header Banner */}
      <div className="glass-card p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 border-l-4 border-sky-500">
        <div>
          <h2 className="text-xl font-bold text-slate-100">Welcome back, {user.full_name}</h2>
          <p className="text-xs text-slate-400 mt-1">
            Personal Well-Being Summary • Next assessment recommended in <strong>14 days</strong>
          </p>
        </div>

        <button
          onClick={onTakeAssessment}
          className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white font-semibold text-xs shadow-lg shadow-sky-500/20 transition flex items-center gap-2"
        >
          <Activity className="w-4 h-4" />
          Retake Assessment
        </button>
      </div>

      {/* 2. Urgent Supportive Alert */}
      {activeUrgentAlert && (
        <div className="p-5 rounded-2xl bg-rose-950/80 border border-rose-500/50 text-rose-100 shadow-xl space-y-2">
          <div className="flex items-center gap-2 text-rose-400 font-bold text-sm">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            <span>Support & Well-Being Alert</span>
          </div>
          <p className="text-xs text-rose-200 leading-relaxed">
            Your recent scores show high fatigue. Please consider taking time for rest or reaching out to an Employee Assistance Program (EAP) or counselor.
          </p>
          <div className="text-[11px] text-rose-300/70 italic">
            * This tool is a confidential screening aid, not a diagnostic or evaluation tool.
          </div>
        </div>
      )}

      {/* 3. Overall Burnout Status Summary */}
      {latestAssessment ? (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="glass-card p-5 rounded-2xl space-y-2 border-t-2 border-sky-400">
            <div className="text-xs text-slate-400 font-semibold uppercase">Overall Burnout Score</div>
            <div className="text-3xl font-extrabold text-white">
              {latestAssessment.composite_score ?? 'N/A'}
              <span className="text-xs text-slate-400 font-normal"> / 100</span>
            </div>
            <div>
              <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-bold ${
                latestAssessment.risk_category === 'High' ? 'bg-rose-950 text-rose-300 border border-rose-500/40' :
                latestAssessment.risk_category === 'Moderate' ? 'bg-amber-950 text-amber-300 border border-amber-500/40' :
                'bg-emerald-950 text-emerald-300 border border-emerald-500/40'
              }`}>
                {latestAssessment.risk_category} Risk Tier
              </span>
            </div>
          </div>

          <div className="glass-card p-5 rounded-2xl space-y-2">
            <div className="text-xs text-slate-400 font-semibold uppercase">Physical Fatigue</div>
            <div className="text-2xl font-bold text-sky-300">
              {latestAssessment.personal_score ?? 'N/A'}
              <span className="text-xs text-slate-400 font-normal"> / 100</span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-sky-500 h-full rounded-full" style={{ width: `${latestAssessment.personal_score || 0}%` }}></div>
            </div>
          </div>

          <div className="glass-card p-5 rounded-2xl space-y-2">
            <div className="text-xs text-slate-400 font-semibold uppercase">Work Strain</div>
            <div className="text-2xl font-bold text-indigo-300">
              {latestAssessment.work_score ?? 'N/A'}
              <span className="text-xs text-slate-400 font-normal"> / 100</span>
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-indigo-500 h-full rounded-full" style={{ width: `${latestAssessment.work_score || 0}%` }}></div>
            </div>
          </div>

          <div className="glass-card p-5 rounded-2xl space-y-2">
            <div className="text-xs text-slate-400 font-semibold uppercase">Client Strain</div>
            <div className="text-2xl font-bold text-purple-300">
              {latestAssessment.client_score !== null ? latestAssessment.client_score : 'N/A'}
              {latestAssessment.client_score !== null && <span className="text-xs text-slate-400 font-normal"> / 100</span>}
            </div>
            <div className="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
              <div className="bg-purple-500 h-full rounded-full" style={{ width: `${latestAssessment.client_score || 0}%` }}></div>
            </div>
          </div>
        </div>
      ) : (
        <div className="glass-card p-8 rounded-2xl text-center space-y-3">
          <Activity className="w-10 h-10 text-sky-400 mx-auto" />
          <h3 className="text-base font-bold text-slate-200">No Assessment Found</h3>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Take your quick 5-minute well-being assessment to get clear insights and recommendations.
          </p>
          <button
            onClick={onTakeAssessment}
            className="px-4 py-2 rounded-xl bg-sky-600 text-white font-semibold text-xs"
          >
            Start Assessment Now
          </button>
        </div>
      )}

      {/* 4. Two Main Focused Sections: Factors & Preventive Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Key Drivers */}
        <div className="glass-card p-6 rounded-2xl space-y-4">
          <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-sky-400" />
            Main Factors Contributing to Your Fatigue
          </h3>

          <div className="space-y-3 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
              <div className="font-semibold text-slate-200 text-xs flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-sky-400"></span>
                Weekly Overtime & Extended Hours
              </div>
              <p className="text-slate-400 text-[11px]">
                Working beyond standard weekly hours increases physical and emotional fatigue over time.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
              <div className="font-semibold text-slate-200 text-xs flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-indigo-400"></span>
                High Task Workload Pressure
              </div>
              <p className="text-slate-400 text-[11px]">
                Operating near maximum task capacity reduces focus periods and recovery time.
              </p>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-900 border border-slate-800 space-y-1">
              <div className="font-semibold text-slate-200 text-xs flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-purple-400"></span>
                Days Worked Without Extended Leave
              </div>
              <p className="text-slate-400 text-[11px]">
                Sustained periods without taking vacation or rest breaks hinder recovery.
              </p>
            </div>
          </div>
        </div>

        {/* Personalized Preventive Actions */}
        <div className="glass-card p-6 rounded-2xl space-y-4">
          <h3 className="text-sm font-bold text-slate-200 flex items-center gap-2">
            <Heart className="w-4 h-4 text-rose-400" />
            Recommended Preventive Actions for You
          </h3>

          {interventions.length > 0 ? (
            <div className="space-y-3">
              {interventions.map((item) => (
                <div key={item.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-100">{item.title}</span>
                    <span className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                      item.status === 'completed' ? 'bg-emerald-950 text-emerald-300' :
                      item.status === 'accepted' ? 'bg-sky-950 text-sky-300' : 'bg-slate-800 text-slate-400'
                    }`}>
                      {item.status.toUpperCase()}
                    </span>
                  </div>

                  <p className="text-[11px] text-slate-300">{item.description}</p>

                  {item.actions_json && (
                    <ul className="text-[11px] text-slate-400 list-disc list-inside space-y-0.5 pt-1">
                      {item.actions_json.map((act, idx) => (
                        <li key={idx}>{act}</li>
                      ))}
                    </ul>
                  )}

                  <div className="pt-2 flex items-center gap-2">
                    {item.status === 'suggested' && (
                      <button
                        onClick={() => handleUpdateIntervention(item.id, 'accepted')}
                        className="px-3 py-1 rounded-lg bg-sky-600 hover:bg-sky-500 text-white text-[11px] font-semibold transition"
                      >
                        Accept Action
                      </button>
                    )}

                    {item.status !== 'completed' && (
                      <button
                        onClick={() => handleUpdateIntervention(item.id, 'completed')}
                        className="px-3 py-1 rounded-lg bg-emerald-950 border border-emerald-500/40 text-emerald-300 hover:bg-emerald-900 text-[11px] font-semibold transition flex items-center gap-1"
                      >
                        <CheckCircle2 className="w-3 h-3" /> Mark Done
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-4 rounded-xl bg-slate-900 text-xs text-slate-400 text-center">
              No preventive actions active. Take an assessment to refresh recommendations.
            </div>
          )}
        </div>
      </div>

      {/* 5. Privacy Settings (Simplified & Clear) */}
      <div className="glass-card p-5 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-t border-slate-800">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
            <Lock className="w-4 h-4 text-sky-400" />
            <span>Private Data Sharing Control</span>
          </div>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Your data is private. HR only sees department averages (5+ people). Toggle ON if you wish to share your score with HR for workload support.
          </p>
        </div>

        <button
          onClick={handleConsentToggle}
          className={`px-4 py-2 rounded-xl text-xs font-semibold transition border ${
            consentOptIn
              ? 'bg-emerald-950 border-emerald-500/50 text-emerald-300 hover:bg-emerald-900'
              : 'bg-slate-800 border-slate-700 text-slate-300 hover:bg-slate-700'
          }`}
        >
          {consentOptIn ? 'Sharing with HR: ON' : 'Sharing with HR: OFF (Private)'}
        </button>
      </div>
    </div>
  );
}
