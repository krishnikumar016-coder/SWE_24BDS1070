import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Settings, RefreshCw, Activity, CheckCircle2, ShieldCheck, Database } from 'lucide-react';

export default function AdminDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [dataQuality, setDataQuality] = useState(null);
  const [loading, setLoading] = useState(true);
  const [retraining, setRetraining] = useState(false);

  useEffect(() => {
    loadAdminData();
  }, []);

  const loadAdminData = async () => {
    setLoading(true);
    try {
      const [mRes, dqRes] = await Promise.all([
        api.getModelMetrics().catch(() => null),
        api.getDataQuality().catch(() => null)
      ]);
      setMetrics(mRes);
      setDataQuality(dqRes);
    } catch (err) {
      console.error("Error loading Admin data:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRetrain = async () => {
    setRetraining(true);
    try {
      const res = await api.retrainModel();
      alert("Model retraining completed successfully!");
      loadAdminData();
    } catch (err) {
      alert("Retraining failed: " + err.message);
    } finally {
      setRetraining(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 py-12 text-center text-slate-400">
        <Settings className="w-8 h-8 animate-spin mx-auto text-purple-400 mb-2" />
        Loading Admin Ops & ML Metrics...
      </div>
    );
  }

  const ablation = metrics?.metrics || {};

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="glass-card p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Settings className="w-5 h-5 text-purple-400" />
            Admin Control & ML Ops Dashboard
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Manage user roles, questionnaire config, trigger ML retraining, and inspect calibration standards.
          </p>
        </div>

        <button
          onClick={handleRetrain}
          disabled={retraining}
          className="px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs flex items-center gap-2 shadow-lg shadow-purple-600/20 transition disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${retraining ? 'animate-spin' : ''}`} />
          {retraining ? 'Retraining LightGBM...' : 'Trigger Model Retrain'}
        </button>
      </div>

      {/* Model Ablation Study Comparison Table */}
      <div className="glass-card p-6 rounded-2xl space-y-4">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <Activity className="w-4 h-4 text-purple-400" />
          Model Evaluation Metrics & Ablation Comparison
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900 text-slate-400 uppercase font-semibold">
              <tr>
                <th className="p-3">Model Architecture</th>
                <th className="p-3">ROC-AUC</th>
                <th className="p-3">PR-AUC</th>
                <th className="p-3">F1-Score</th>
                <th className="p-3">Brier Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-200">
              {Object.entries(ablation).map(([name, m]) => (
                <tr key={name} className={name.includes('Monotonic') ? 'bg-purple-950/20 font-bold' : ''}>
                  <td className="p-3">{name}</td>
                  <td className="p-3 text-sky-400">{m?.roc_auc ?? 'N/A'}</td>
                  <td className="p-3 text-indigo-400">{m?.pr_auc ?? 'N/A'}</td>
                  <td className="p-3 text-purple-400">{m?.f1_score ?? 'N/A'}</td>
                  <td className="p-3 text-slate-400">{m?.brier_score ?? 'N/A'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Early Warning Lead Time Analysis */}
      {metrics?.metrics?.lead_time && (
        <div className="glass-card p-6 rounded-2xl space-y-3 border-l-4 border-purple-500">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
            Early-Warning Lead-Time Analysis
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Mean Lead Time</div>
              <div className="text-xl font-bold text-purple-400 mt-1">
                {metrics.metrics.lead_time.mean_lead_time_windows} windows (~{metrics.metrics.lead_time.lead_time_weeks} weeks)
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Median Lead Time</div>
              <div className="text-xl font-bold text-purple-400 mt-1">
                {metrics.metrics.lead_time.median_lead_time_windows} windows
              </div>
            </div>

            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Eval High-Risk Cohort</div>
              <div className="text-xl font-bold text-slate-200 mt-1">
                {metrics.metrics.lead_time.eval_sample_count} employees
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Data Quality & CBI Norm Calibration Checks */}
      {dataQuality && (
        <div className="glass-card p-6 rounded-2xl space-y-4">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            Data Quality & Published CBI Norm Calibration
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
              <div className="font-semibold text-slate-200">Database Record Counts</div>
              <div className="text-slate-400">Total Users: <strong className="text-slate-200">{dataQuality.db_users_count}</strong></div>
              <div className="text-slate-400">Total Assessments: <strong className="text-slate-200">{dataQuality.db_assessments_count}</strong></div>
              <div className="text-emerald-400 pt-1 font-medium">{dataQuality.data_minimization_check}</div>
            </div>

            {dataQuality.cbi_norm_calibration && (
              <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-2">
                <div className="font-semibold text-slate-200">CBI Literature Norm Calibration Check</div>
                <div className="text-slate-400">Personal Mean: <strong className="text-slate-200">{dataQuality.cbi_norm_calibration.personal_mean}</strong> (Target ~32)</div>
                <div className="text-slate-400">Work Mean: <strong className="text-slate-200">{dataQuality.cbi_norm_calibration.work_mean}</strong> (Target ~33)</div>
                <div className="text-slate-400">High Risk % (&ge;50): <strong className="text-slate-200">{dataQuality.cbi_norm_calibration.high_risk_pct}%</strong> (Target 15-25%)</div>
                <div className="pt-1 text-emerald-400 font-bold">
                  {dataQuality.cbi_norm_calibration.calibrated_pass ? 'PASSED - Matched Literature Norms' : 'CALIBRATION CHECK'}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
