import React, { useState } from 'react';
import { api, setAuthToken } from '../api';
import { ShieldCheck, User, Users, Settings, Lock } from 'lucide-react';

export default function Login({ onLoginSuccess }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await api.login(email, password);
      setAuthToken(data.access_token);
      onLoginSuccess();
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const fillQuickLogin = (presetEmail, presetPass) => {
    setEmail(presetEmail);
    setPassword(presetPass);
  };

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center p-4">
      <div className="max-w-md w-full glass-card p-8 rounded-2xl shadow-2xl border border-slate-800 relative overflow-hidden">
        <div className="absolute -top-12 -right-12 w-32 h-32 bg-sky-500/10 rounded-full blur-2xl pointer-events-none"></div>

        <div className="text-center mb-8">
          <div className="inline-flex p-3 rounded-2xl bg-sky-500/10 border border-sky-500/20 text-sky-400 mb-3">
            <ShieldCheck className="w-8 h-8" />
          </div>
          <h2 className="text-2xl font-bold text-slate-100">Welcome Back</h2>
          <p className="text-xs text-slate-400 mt-1">Sign in to access your Burnout Early-Warning Portal</p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-950/60 border border-rose-500/30 text-rose-300 text-xs">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Work Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700/70 text-slate-100 text-sm focus:outline-none focus:border-sky-500 transition"
              placeholder="name@company.com"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700/70 text-slate-100 text-sm focus:outline-none focus:border-sky-500 transition"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-500 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg shadow-sky-600/20 transition disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>

        {/* Quick Demo Credentials Switcher */}
        <div className="mt-8 pt-6 border-t border-slate-800">
          <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-3 text-center">
            Quick Demo Login Accounts
          </p>
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => fillQuickLogin('employee1@company.com', 'emp123456')}
              className="p-2.5 rounded-xl bg-slate-900/80 hover:bg-sky-950/40 border border-slate-800 hover:border-sky-500/40 transition text-left group"
            >
              <div className="flex items-center gap-1.5 text-sky-400 font-semibold text-xs mb-0.5">
                <User className="w-3.5 h-3.5" />
                Employee
              </div>
              <div className="text-[10px] text-slate-400 group-hover:text-slate-300 truncate">John Dev</div>
            </button>

            <button
              onClick={() => fillQuickLogin('hr@company.com', 'hr123456')}
              className="p-2.5 rounded-xl bg-slate-900/80 hover:bg-sky-950/40 border border-slate-800 hover:border-sky-500/40 transition text-left group"
            >
              <div className="flex items-center gap-1.5 text-emerald-400 font-semibold text-xs mb-0.5">
                <Users className="w-3.5 h-3.5" />
                HR Manager
              </div>
              <div className="text-[10px] text-slate-400 group-hover:text-slate-300 truncate">Jane HR</div>
            </button>

            <button
              onClick={() => fillQuickLogin('admin@company.com', 'admin123')}
              className="p-2.5 rounded-xl bg-slate-900/80 hover:bg-purple-950/40 border border-slate-800 hover:border-purple-500/40 transition text-left group"
            >
              <div className="flex items-center gap-1.5 text-purple-400 font-semibold text-xs mb-0.5">
                <Settings className="w-3.5 h-3.5" />
                Admin
              </div>
              <div className="text-[10px] text-slate-400 group-hover:text-slate-300 truncate">Sys Admin</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
