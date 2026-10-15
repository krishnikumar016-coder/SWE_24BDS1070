const BASE_URL = '/api';

export function getAuthToken() {
  return localStorage.getItem('token');
}

export function setAuthToken(token) {
  localStorage.setItem('token', token);
}

export function clearAuthToken() {
  localStorage.removeItem('token');
}

async function request(endpoint, options = {}) {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  const config = {
    ...options,
    headers,
  };

  const response = await fetch(`${BASE_URL}${endpoint}`, config);
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || 'API request failed');
  }

  return response.json();
}

export const api = {
  // Auth
  login: (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    return fetch(`${BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData,
    }).then(res => {
      if (!res.ok) throw new Error('Invalid credentials');
      return res.json();
    });
  },
  register: (userData) => request('/auth/register', { method: 'POST', body: JSON.stringify(userData) }),
  getMe: () => request('/auth/me'),
  toggleConsent: (optIn) => request('/auth/consent', { method: 'POST', body: JSON.stringify({ hr_data_sharing_opt_in: optIn }) }),
  exportData: () => request('/auth/export-data'),
  deleteData: () => request('/auth/delete-data', { method: 'DELETE' }),

  // Assessments
  getAssessmentConfig: () => request('/assessments/config'),
  submitAssessment: (answers) => request('/assessments', { method: 'POST', body: JSON.stringify({ answers }) }),
  getAssessmentHistory: () => request('/assessments/history'),
  getLatestAssessment: () => request('/assessments/latest'),

  // Objective Indicators
  submitIndicators: (indicators) => request('/indicators', { method: 'POST', body: JSON.stringify(indicators) }),

  // Alerts
  getMyAlerts: () => request('/alerts/me'),
  updateAlertStatus: (id, status) => request(`/alerts/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),

  // Interventions
  getMyInterventions: () => request('/interventions/me'),
  updateInterventionStatus: (id, status) => request(`/interventions/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),
  getInterventionEffectiveness: () => request('/interventions/effectiveness'),

  // Simulator
  simulateIntervention: (simData) => request('/simulator/simulate', { method: 'POST', body: JSON.stringify(simData) }),

  // HR
  getDepartmentAggregates: () => request('/hr/department-aggregates'),
  getEmployeesList: () => request('/hr/employees'),
  getIndividualEmployeeData: (id) => request(`/hr/employee/${id}`),
  getBiasCheck: () => request('/hr/bias-check'),

  // Admin
  retrainModel: () => request('/admin/retrain', { method: 'POST' }),
  getModelMetrics: () => request('/admin/model-metrics'),
  getDataQuality: () => request('/admin/data-quality'),
};
