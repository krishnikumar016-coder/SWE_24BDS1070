import React, { useState, useEffect } from 'react';
import { api, getAuthToken, clearAuthToken } from './api';
import DisclaimerBanner from './components/DisclaimerBanner';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import EmployeeDashboard from './pages/EmployeeDashboard';
import AssessmentForm from './pages/AssessmentForm';
import HRDashboard from './pages/HRDashboard';
import AdminDashboard from './pages/AdminDashboard';

export default function App() {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    checkCurrentUser();
  }, []);

  const checkCurrentUser = async () => {
    const token = getAuthToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const u = await api.getMe();
      setUser(u);
      if (u.role === 'HR') setActiveTab('hr');
      else if (u.role === 'Admin') setActiveTab('admin');
      else setActiveTab('dashboard');
    } catch (err) {
      clearAuthToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    clearAuthToken();
    setUser(null);
    setActiveTab('dashboard');
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400 text-sm">
        Initializing Burnout Early-Warning System...
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans flex flex-col justify-between">
      <div>
        <DisclaimerBanner />
        <Navbar
          user={user}
          onLogout={handleLogout}
          activeTab={activeTab}
          setActiveTab={setActiveTab}
        />

        <main>
          {!user ? (
            <Login onLoginSuccess={checkCurrentUser} />
          ) : (
            <>
              {activeTab === 'dashboard' && (
                <EmployeeDashboard
                  user={user}
                  onTakeAssessment={() => setActiveTab('assessment')}
                  onUserUpdated={checkCurrentUser}
                />
              )}

              {activeTab === 'assessment' && (
                <AssessmentForm
                  onFinished={() => {
                    setActiveTab('dashboard');
                    checkCurrentUser();
                  }}
                />
              )}

              {activeTab === 'hr' && <HRDashboard />}

              {activeTab === 'admin' && <AdminDashboard />}
            </>
          )}
        </main>
      </div>

      <footer className="border-t border-slate-800/80 bg-slate-950 py-6 text-center text-xs text-slate-400">
        <div className="max-w-7xl mx-auto px-4 space-y-1">
          <p>Employee Burnout Early-Warning and Intervention System MVP • Closed-Loop Personalized Aid</p>
          <p className="text-[11px] text-slate-500">
            Source: Copenhagen Burnout Inventory (Borritz & Kristensen 2004) • Screening Aid Only (Never Diagnostic)
          </p>
        </div>
      </footer>
    </div>
  );
}
