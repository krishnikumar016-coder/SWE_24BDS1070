import React, { useState, useEffect } from 'react';
import { api } from '../api';
import {
  Users, Sliders, Shield, AlertCircle, CheckCircle2, Lock, Eye, BarChart3, X, Activity, Heart
} from 'lucide-react';

export default function HRDashboard() {
  const [aggregates, setAggregates] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(true);

  // Simulator State
  const [simForm, setSimForm] = useState({
    overtime_hours: 8,
    avg_weekly_hours: 45,
    workload_index: 0.75,
    wfh_days_ratio: 0.2,
    leave_days_taken: 0
  });
  const [simResult, setSimResult] = useState(null);
  const [simulating, setSimulating] = useState(false);

  // Individual View Modal State
  const [selectedEmp, setSelectedEmp] = useState(null);
  const [empData, setEmpData] = useState(null);
  const [fetchingEmp, setFetchingEmp] = useState(false);

  useEffect(() => {
    loadHRData();
  }, []);

  const loadHRData = async () => {
    setLoading(true);
    try {
      const [aggData, empDataList] = await Promise.all([
        api.getDepartmentAggregates().catch(() => []),
        api.getEmployeesList().catch(() => [])
      ]);
      setAggregates(aggData);
      setEmployees(empDataList);
    } catch (err) {
      console.error("Error loading HR dashboard:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleRunSimulation = async () => {
    setSimulating(true);
    try {
      const res = await api.simulateIntervention(simForm);
      setSimResult(res);
    } catch (err) {
      alert("Simulation failed: " + err.message);
    } finally {
      setSimulating(false);
    }
  };

  const handleViewIndividual = async (emp) => {
    if (!emp.hr_data_sharing_opt_in) {
      alert("Privacy Restriction: Employee has NOT opted in to sharing individual data.");
      return;
    }
    setSelectedEmp(emp);
    setFetchingEmp(true);
    try {
      const data = await api.getIndividualEmployeeData(emp.id);
      setEmpData(data);
    } catch (err) {
      alert("Failed to load employee details: " + err.message);
    } finally {
      setFetchingEmp(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-16 text-center text-slate-400">
        <Users className="w-8 h-8 animate-spin mx-auto text-sky-400 mb-3" />
        Loading HR Overview...
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8 space-y-8">
      {/* 1. Header */}
      <div className="glass-card p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4 border-l-4 border-sky-500">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <Users className="w-5 h-5 text-sky-400" />
            HR Department Well-Being Overview
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Department-level averages are shown for team privacy • Teams with fewer than 5 members are hidden for confidentiality.
          </p>
        </div>
      </div>

      {/* 2. Department Averages & Risk Distribution */}
      <div className="space-y-4">
        <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-sky-400" />
          Department Burnout Overview
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {aggregates.map((dept) => (
            <div key={dept.department_id} className="glass-card p-5 rounded-2xl space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-200">{dept.department_name}</span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-semibold">
                  {dept.sample_size} People
                </span>
              </div>

              {dept.is_suppressed ? (
                <div className="p-3.5 rounded-xl bg-slate-900 border border-amber-500/30 text-amber-300 text-xs space-y-1">
                  <div className="flex items-center gap-1.5 font-semibold text-amber-400">
                    <Shield className="w-4 h-4" />
                    Hidden for Privacy
                  </div>
                  <p className="text-[11px] text-amber-200/80">Group size is under 5. Data hidden to protect individual identity.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  <div>
                    <div className="text-2xl font-extrabold text-white">
                      {dept.avg_composite_score}
                      <span className="text-xs text-slate-400 font-normal"> / 100</span>
                    </div>
                    <div className="text-[10px] text-slate-400">Average Burnout Score</div>
                  </div>

                  {dept.risk_tier_percentages && (
                    <div className="space-y-1">
                      <div className="flex justify-between text-[10px] font-semibold">
                        <span className="text-rose-400">High: {dept.risk_tier_percentages.High}%</span>
                        <span className="text-amber-400">Mod: {dept.risk_tier_percentages.Moderate}%</span>
                        <span className="text-emerald-400">Low: {dept.risk_tier_percentages.Low}%</span>
                      </div>
                      <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden flex">
                        <div className="bg-rose-500 h-full" style={{ width: `${dept.risk_tier_percentages.High}%` }}></div>
                        <div className="bg-amber-500 h-full" style={{ width: `${dept.risk_tier_percentages.Moderate}%` }}></div>
                        <div className="bg-emerald-500 h-full" style={{ width: `${dept.risk_tier_percentages.Low}%` }}></div>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* 3. What-If Workload Adjuster Simulator */}
      <div className="glass-card p-6 rounded-2xl space-y-6">
        <div>
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Sliders className="w-4 h-4 text-indigo-400" />
            Workload Policy Adjustment Simulator
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            See how reducing overtime or adding leave days lowers predicted burnout risk for your team.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Sliders */}
          <div className="space-y-4 text-xs">
            <div>
              <div className="flex justify-between font-semibold text-slate-300 mb-1">
                <span>Weekly Overtime Hours</span>
                <span className="text-sky-400 font-bold">{simForm.overtime_hours} hrs/week</span>
              </div>
              <input
                type="range"
                min="0"
                max="20"
                step="1"
                value={simForm.overtime_hours}
                onChange={(e) => setSimForm({ ...simForm, overtime_hours: parseFloat(e.target.value) })}
                className="w-full accent-sky-500"
              />
            </div>

            <div>
              <div className="flex justify-between font-semibold text-slate-300 mb-1">
                <span>Total Weekly Hours</span>
                <span className="text-sky-400 font-bold">{simForm.avg_weekly_hours} hrs/week</span>
              </div>
              <input
                type="range"
                min="35"
                max="60"
                step="1"
                value={simForm.avg_weekly_hours}
                onChange={(e) => setSimForm({ ...simForm, avg_weekly_hours: parseFloat(e.target.value) })}
                className="w-full accent-sky-500"
              />
            </div>

            <div>
              <div className="flex justify-between font-semibold text-slate-300 mb-1">
                <span>Workload Capacity Target</span>
                <span className="text-sky-400 font-bold">{Math.round(simForm.workload_index * 100)}% capacity</span>
              </div>
              <input
                type="range"
                min="0.3"
                max="1.0"
                step="0.05"
                value={simForm.workload_index}
                onChange={(e) => setSimForm({ ...simForm, workload_index: parseFloat(e.target.value) })}
                className="w-full accent-sky-500"
              />
            </div>

            <div>
              <div className="flex justify-between font-semibold text-slate-300 mb-1">
                <span>Scheduled Rest / Leave Days</span>
                <span className="text-sky-400 font-bold">{simForm.leave_days_taken} days</span>
              </div>
              <input
                type="range"
                min="0"
                max="10"
                step="1"
                value={simForm.leave_days_taken}
                onChange={(e) => setSimForm({ ...simForm, leave_days_taken: parseFloat(e.target.value) })}
                className="w-full accent-sky-500"
              />
            </div>

            <button
              onClick={handleRunSimulation}
              disabled={simulating}
              className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs shadow-lg shadow-indigo-600/20 transition"
            >
              {simulating ? 'Calculating Estimated Impact...' : 'Simulate Risk Change'}
            </button>
          </div>

          {/* Simulation Output Card */}
          <div className="p-6 rounded-2xl bg-slate-900 border border-slate-800 flex flex-col justify-between space-y-4">
            {simResult ? (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <div className="text-[10px] text-slate-400 uppercase font-semibold">Current High Risk Chance</div>
                    <div className="text-2xl font-bold text-slate-200 mt-1">
                      {(simResult.baseline_risk_prob * 100).toFixed(1)}%
                    </div>
                  </div>

                  <div className="p-4 rounded-xl bg-slate-950 border border-slate-800">
                    <div className="text-[10px] text-slate-400 uppercase font-semibold">After Adjustment</div>
                    <div className="text-2xl font-extrabold text-sky-400 mt-1">
                      {(simResult.simulated_risk_prob * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>

                <div className="p-3.5 rounded-xl bg-sky-950/40 border border-sky-500/30 flex items-center justify-between text-xs">
                  <span className="font-semibold text-slate-200">Expected Risk Change:</span>
                  <span className={`font-bold text-sm ${simResult.risk_delta <= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {simResult.risk_delta <= 0 ? '' : '+'}{(simResult.risk_delta * 100).toFixed(1)}%
                  </span>
                </div>

                <p className="text-[11px] text-slate-400 italic">
                  * Note: Estimates show statistical associations based on past trends, not guaranteed causal outcomes.
                </p>
              </div>
            ) : (
              <div className="text-center my-auto py-12 text-slate-500 text-xs">
                Move sliders above and click "Simulate Risk Change" to see expected improvements.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 4. Individual Access Directory */}
      <div className="glass-card p-6 rounded-2xl space-y-4">
        <div>
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
            <Lock className="w-4 h-4 text-emerald-400" />
            Opted-In Employee Directory
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Employees who have explicitly granted permission to share their individual well-being scores with HR.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-900 text-slate-400 uppercase font-semibold">
              <tr>
                <th className="p-3">Employee Name</th>
                <th className="p-3">Email</th>
                <th className="p-3">Department</th>
                <th className="p-3">Consent Status</th>
                <th className="p-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800 text-slate-200">
              {employees.map((emp) => (
                <tr key={emp.id} className="hover:bg-slate-900/50">
                  <td className="p-3 font-semibold text-slate-100">{emp.full_name}</td>
                  <td className="p-3 text-slate-400">{emp.email}</td>
                  <td className="p-3">{emp.department_name}</td>
                  <td className="p-3">
                    <span className={`px-2.5 py-0.5 rounded text-[10px] font-semibold ${
                      emp.hr_data_sharing_opt_in ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/30' : 'bg-slate-800 text-slate-400'
                    }`}>
                      {emp.hr_data_sharing_opt_in ? 'Opted IN' : 'Opted OUT (Private)'}
                    </span>
                  </td>
                  <td className="p-3 text-right">
                    <button
                      onClick={() => handleViewIndividual(emp)}
                      disabled={!emp.hr_data_sharing_opt_in}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                        emp.hr_data_sharing_opt_in
                          ? 'bg-sky-600 hover:bg-sky-500 text-white shadow'
                          : 'bg-slate-800 text-slate-500 cursor-not-allowed'
                      }`}
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 5. INDIVIDUAL EMPLOYEE DETAILS MODAL */}
      {selectedEmp && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="glass-card max-w-2xl w-full p-6 rounded-2xl shadow-2xl space-y-6 relative max-h-[90vh] overflow-y-auto">
            <button
              onClick={() => { setSelectedEmp(null); setEmpData(null); }}
              className="absolute top-4 right-4 p-2 rounded-xl bg-slate-800 text-slate-400 hover:text-white"
            >
              <X className="w-5 h-5" />
            </button>

            <div>
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-500/30">
                  Consent Opted IN
                </span>
                <span className="text-xs text-slate-400">{selectedEmp.department_name}</span>
              </div>
              <h3 className="text-xl font-bold text-slate-100 mt-1">{selectedEmp.full_name}</h3>
              <p className="text-xs text-slate-400">{selectedEmp.email}</p>
            </div>

            {fetchingEmp ? (
              <div className="py-12 text-center text-slate-400 text-xs">
                <Activity className="w-6 h-6 animate-spin mx-auto text-sky-400 mb-2" />
                Retrieving confidential well-being metrics...
              </div>
            ) : empData && empData.assessments && empData.assessments.length > 0 ? (
              <div className="space-y-4">
                {/* Latest Scores */}
                {(() => {
                  const latest = empData.assessments[empData.assessments.length - 1];
                  return (
                    <div className="space-y-4">
                      <div className="p-4 rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-between">
                        <div>
                          <div className="text-[10px] uppercase font-semibold text-slate-400">Latest Burnout Score</div>
                          <div className="text-3xl font-extrabold text-white mt-0.5">
                            {latest.composite_score} <span className="text-xs font-normal text-slate-400">/ 100</span>
                          </div>
                        </div>
                        <span className={`px-3 py-1 rounded-full text-xs font-bold ${
                          latest.risk_category === 'High' ? 'bg-rose-950 text-rose-300 border border-rose-500/40' :
                          latest.risk_category === 'Moderate' ? 'bg-amber-950 text-amber-300 border border-amber-500/40' :
                          'bg-emerald-950 text-emerald-300 border border-emerald-500/40'
                        }`}>
                          {latest.risk_category} Risk
                        </span>
                      </div>

                      <div className="grid grid-cols-3 gap-3 text-center">
                        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                          <div className="text-[10px] text-slate-400 uppercase">Physical</div>
                          <div className="text-lg font-bold text-sky-300">{latest.personal_score}</div>
                        </div>
                        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                          <div className="text-[10px] text-slate-400 uppercase">Work</div>
                          <div className="text-lg font-bold text-indigo-300">{latest.work_score}</div>
                        </div>
                        <div className="p-3 rounded-xl bg-slate-900 border border-slate-800">
                          <div className="text-[10px] text-slate-400 uppercase">Client</div>
                          <div className="text-lg font-bold text-purple-300">{latest.client_score ?? 'N/A'}</div>
                        </div>
                      </div>
                    </div>
                  );
                })()}

                {/* History Table */}
                <div className="space-y-2">
                  <h4 className="text-xs font-bold text-slate-300 uppercase">Assessment History</h4>
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-900 text-slate-400 font-semibold">
                        <tr>
                          <th className="p-2">Date</th>
                          <th className="p-2">Composite Score</th>
                          <th className="p-2">Risk Level</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-800 text-slate-200">
                        {empData.assessments.map((a) => (
                          <tr key={a.id}>
                            <td className="p-2 text-slate-400">{new Date(a.timestamp).toLocaleDateString()}</td>
                            <td className="p-2 font-bold text-sky-300">{a.composite_score}</td>
                            <td className="p-2">{a.risk_category}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-8 text-center text-slate-400 text-xs">
                No completed assessments recorded for this employee.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
