import React from 'react';
import { Activity, UserCheck, Lock, LogOut, Shield } from 'lucide-react';

export default function Navbar({ user, onLogout, activeTab, setActiveTab }) {
  return (
    <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-gradient-to-tr from-sky-600 to-indigo-600 shadow-lg shadow-sky-500/20">
            <Activity className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="font-bold text-slate-100 text-base leading-none">Burnout Early-Warning</h1>
            <p className="text-xs text-sky-400 font-medium mt-0.5">Closed-Loop Intervention System</p>
          </div>
        </div>

        {user && (
          <div className="flex items-center gap-4">
            {/* Role Navigation Tabs */}
            <nav className="flex items-center gap-1 bg-slate-800/80 p-1 rounded-xl border border-slate-700/50 text-xs sm:text-sm">
              {user.role === 'Employee' && (
                <>
                  <button
                    onClick={() => setActiveTab('dashboard')}
                    className={`px-3 py-1.5 rounded-lg font-medium transition ${
                      activeTab === 'dashboard' ? 'bg-sky-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    My Dashboard
                  </button>
                  <button
                    onClick={() => setActiveTab('assessment')}
                    className={`px-3 py-1.5 rounded-lg font-medium transition ${
                      activeTab === 'assessment' ? 'bg-sky-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Take Assessment
                  </button>
                </>
              )}

              {user.role === 'HR' && (
                <>
                  <button
                    onClick={() => setActiveTab('hr')}
                    className={`px-3 py-1.5 rounded-lg font-medium transition ${
                      activeTab === 'hr' ? 'bg-sky-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    HR Analytics & Simulator
                  </button>
                </>
              )}

              {user.role === 'Admin' && (
                <>
                  <button
                    onClick={() => setActiveTab('hr')}
                    className={`px-3 py-1.5 rounded-lg font-medium transition ${
                      activeTab === 'hr' ? 'bg-sky-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    HR Overview
                  </button>
                  <button
                    onClick={() => setActiveTab('admin')}
                    className={`px-3 py-1.5 rounded-lg font-medium transition ${
                      activeTab === 'admin' ? 'bg-purple-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    Admin & ML Ops
                  </button>
                </>
              )}
            </nav>

            {/* User Info & Role Badge */}
            <div className="hidden md:flex items-center gap-2 border-l border-slate-800 pl-4">
              <div className="text-right">
                <div className="text-xs font-semibold text-slate-200">{user.full_name}</div>
                <div className="text-[10px] text-slate-400 flex items-center gap-1 justify-end">
                  <span className="px-1.5 py-0.5 rounded bg-slate-800 text-sky-400 font-medium">
                    {user.role}
                  </span>
                  {user.role === 'Employee' && (
                    <span className={`px-1.5 py-0.5 rounded ${user.current_consent ? 'bg-emerald-950 text-emerald-400' : 'bg-slate-800 text-slate-400'}`}>
                      {user.current_consent ? 'HR Sharing: ON' : 'HR Sharing: OFF'}
                    </span>
                  )}
                </div>
              </div>
            </div>

            <button
              onClick={onLogout}
              className="p-2 rounded-lg bg-slate-800 hover:bg-rose-950/50 text-slate-400 hover:text-rose-400 transition border border-slate-700/50"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
