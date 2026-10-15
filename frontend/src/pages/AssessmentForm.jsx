import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Activity, CheckCircle2, ArrowRight, ArrowLeft, AlertCircle } from 'lucide-react';

export default function AssessmentForm({ onFinished }) {
  const [config, setConfig] = useState(null);
  const [items, setItems] = useState([]);
  const [answers, setAnswers] = useState({});
  const [indicators, setIndicators] = useState({
    avg_weekly_hours: 40,
    overtime_hours: 0,
    overtime_days: 0,
    leave_days_taken: 0,
    days_since_last_leave: 30,
    wfh_days_ratio: 0.2,
    workload_index: 0.5,
    meeting_hours: 5
  });
  const [step, setStep] = useState(0); // Step 0 = Objective Indicators, Step 1+ = Questionnaire Pages
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      const data = await api.getAssessmentConfig();
      setConfig(data);
      setItems(data.items || []);
    } catch (err) {
      alert("Failed to load questionnaire config.");
    } finally {
      setLoading(false);
    }
  };

  const handleIndicatorChange = (field, val) => {
    setIndicators(prev => ({ ...prev, [field]: parseFloat(val) || 0 }));
  };

  const handleAnswerChange = (itemId, option) => {
    setAnswers(prev => ({ ...prev, [itemId]: option }));
  };

  const PAGE_SIZE = 5;
  const totalPages = Math.ceil(items.length / PAGE_SIZE);

  const getCurrentPageItems = () => {
    if (step === 0) return [];
    const startIndex = (step - 1) * PAGE_SIZE;
    return items.slice(startIndex, startIndex + PAGE_SIZE);
  };

  const isCurrentPageComplete = () => {
    if (step === 0) return true;
    const pageItems = getCurrentPageItems();
    return pageItems.every(it => answers[it.id] !== undefined);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    try {
      // 1. Submit objective indicators
      await api.submitIndicators(indicators).catch(() => {});

      // 2. Submit CBI answers
      const answersPayload = Object.entries(answers).map(([item_id, raw_answer]) => ({
        item_id,
        raw_answer
      }));

      const res = await api.submitAssessment(answersPayload);
      setResult(res);
    } catch (err) {
      alert("Failed to submit assessment: " + err.message);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center text-slate-400">
        <Activity className="w-8 h-8 animate-spin mx-auto text-sky-400 mb-2" />
        Preparing Copenhagen Burnout Inventory questionnaire...
      </div>
    );
  }

  if (result) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12">
        <div className="glass-card p-8 rounded-2xl text-center space-y-6">
          <div className="inline-flex p-3 rounded-2xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <CheckCircle2 className="w-10 h-10" />
          </div>

          <div>
            <h2 className="text-2xl font-bold text-slate-100">Assessment Completed</h2>
            <p className="text-xs text-slate-400 mt-1">Your responses have been validated and scored using the official CBI formula.</p>
          </div>

          <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
            <div className="text-xs text-slate-400 uppercase tracking-wider font-semibold">Calculated Composite Index</div>
            <div className="text-4xl font-extrabold text-sky-300">
              {result.composite_score} <span className="text-sm font-normal text-slate-400">/ 100</span>
            </div>
            <span className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${
              result.risk_category === 'High' ? 'bg-rose-950 text-rose-300 border border-rose-500/40' :
              result.risk_category === 'Moderate' ? 'bg-amber-950 text-amber-300 border border-amber-500/40' :
              'bg-emerald-950 text-emerald-300 border border-emerald-500/40'
            }`}>
              {result.risk_category} Risk Category
            </span>
          </div>

          <button
            onClick={onFinished}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white font-semibold text-sm transition"
          >
            Return to Dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      {/* Questionnaire Header */}
      <div className="glass-card p-6 rounded-2xl space-y-2">
        <h2 className="text-xl font-bold text-slate-100">Copenhagen Burnout Inventory (CBI)</h2>
        <p className="text-xs text-slate-400">
          Source: Borritz & Kristensen (2004), National Research Centre for Working Environment, Denmark.
        </p>

        {/* Progress Bar */}
        <div className="pt-2">
          <div className="flex justify-between text-[11px] text-slate-400 font-semibold mb-1">
            <span>Progress: Step {step + 1} of {totalPages + 1}</span>
            <span>{Math.round(((step + 1) / (totalPages + 1)) * 100)}%</span>
          </div>
          <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
            <div
              className="bg-gradient-to-r from-sky-500 to-indigo-500 h-full rounded-full transition-all duration-300"
              style={{ width: `${((step + 1) / (totalPages + 1)) * 100}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Step 0: Objective Indicators */}
      {step === 0 && (
        <div className="glass-card p-6 rounded-2xl space-y-6">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
            Step 1: Objective Non-Invasive Indicators (Past 2 Weeks)
          </h3>
          <p className="text-xs text-slate-400">
            Please enter your objective work metrics. (Design Principle: Non-invasive metrics only. No message or screen monitoring).
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Average Weekly Hours</label>
              <input
                type="number"
                value={indicators.avg_weekly_hours}
                onChange={(e) => handleIndicatorChange('avg_weekly_hours', e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Weekly Overtime Hours</label>
              <input
                type="number"
                value={indicators.overtime_hours}
                onChange={(e) => handleIndicatorChange('overtime_hours', e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Leave Days Taken</label>
              <input
                type="number"
                step="0.5"
                value={indicators.leave_days_taken}
                onChange={(e) => handleIndicatorChange('leave_days_taken', e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Days Since Last Vacation/Leave</label>
              <input
                type="number"
                value={indicators.days_since_last_leave}
                onChange={(e) => handleIndicatorChange('days_since_last_leave', e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Work From Home Ratio (0.0 to 1.0)</label>
              <input
                type="number"
                step="0.1"
                min="0"
                max="1"
                value={indicators.wfh_days_ratio}
                onChange={(e) => handleIndicatorChange('wfh_days_ratio', e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 mb-1">Workload Capacity Index (0.0 to 1.0)</label>
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={indicators.workload_index}
                onChange={(e) => handleIndicatorChange('workload_index', e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-slate-900 border border-slate-700 text-slate-100 text-sm"
              />
            </div>
          </div>

          <div className="pt-4 flex justify-end">
            <button
              onClick={() => setStep(1)}
              className="px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs flex items-center gap-1.5"
            >
              Continue to Questionnaire <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Steps 1+: CBI Questionnaire Pages */}
      {step > 0 && (
        <div className="glass-card p-6 rounded-2xl space-y-6">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider">
            Questions (Page {step} of {totalPages})
          </h3>

          <div className="space-y-6">
            {getCurrentPageItems().map((item) => (
              <div key={item.id} className="p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3">
                <div className="text-sm font-medium text-slate-200">
                  <span className="text-sky-400 font-bold mr-2">[{item.id}]</span>
                  {item.text}
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-5 gap-2">
                  {item.options.map((opt) => (
                    <button
                      key={opt}
                      type="button"
                      onClick={() => handleAnswerChange(item.id, opt)}
                      className={`p-2.5 rounded-xl text-xs font-semibold transition text-center border ${
                        answers[item.id] === opt
                          ? 'bg-sky-600 border-sky-400 text-white shadow'
                          : 'bg-slate-950 border-slate-800 text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="pt-4 flex items-center justify-between">
            <button
              onClick={() => setStep(step - 1)}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold text-xs flex items-center gap-1.5"
            >
              <ArrowLeft className="w-4 h-4" /> Previous
            </button>

            {step < totalPages ? (
              <button
                onClick={() => setStep(step + 1)}
                disabled={!isCurrentPageComplete()}
                className="px-5 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-semibold text-xs flex items-center gap-1.5 disabled:opacity-40"
              >
                Next Page <ArrowRight className="w-4 h-4" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={!isCurrentPageComplete() || submitting}
                className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs shadow-lg shadow-emerald-600/20 transition disabled:opacity-40"
              >
                {submitting ? 'Calculating CBI Scores...' : 'Submit Assessment'}
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
