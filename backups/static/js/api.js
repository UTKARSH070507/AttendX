/**
 * AttendX - API Client Module
 * Communicates with Flask REST API endpoints via Fetch API.
 */

const API = (() => {
  // Dynamically determine backend URL:
  // When frontend is served from Live Server (e.g. http://127.0.0.1:5500), route API requests to Flask backend on port 5000.
  // When frontend is served directly by Flask (port 5000), use same-origin relative path '/api'.
  const getBaseUrl = () => {
    const origin = window.location.origin || '';
    const port = window.location.port;
    if (origin.includes(':5500') || (port && port !== '5000')) {
      const hostname = window.location.hostname || '127.0.0.1';
      return `http://${hostname}:5000/api`;
    }
    if (window.location.protocol === 'file:') {
      return 'http://127.0.0.1:5000/api';
    }
    return '/api';
  };

  const BASE_URL = getBaseUrl();

  async function request(endpoint, options = {}) {
    const url = `${BASE_URL}${endpoint}`;
    try {
      const response = await fetch(url, options);
      const isJson = response.headers.get('content-type')?.includes('application/json');
      const data = isJson ? await response.json() : await response.text();

      if (!response.ok) {
        let errorMsg = (isJson && (data.error || data.message));
        if (!errorMsg) {
          if (response.status === 404) {
            errorMsg = 'API endpoint not found (404). Please ensure the Flask backend server is running (python app.py).';
          } else {
            errorMsg = `Server returned status ${response.status}`;
          }
        }
        return {
          ok: false,
          status: response.status,
          error: errorMsg,
          details: data
        };
      }

      return {
        ok: true,
        status: response.status,
        data: data
      };
    } catch (err) {
      return {
        ok: false,
        status: 0,
        error: 'Unable to connect to AttendX server. Please ensure the backend is running.',
        details: err.message
      };
    }
  }

  // 1. Health Probe
  function checkHealth() {
    return request('/health');
  }

  // 2. Dashboard Metrics
  function getDashboard() {
    return request('/dashboard');
  }

  // 3. Student Management
  function getStudents(params = {}) {
    const query = new URLSearchParams();
    if (params.search) query.append('search', params.search);
    if (params.group && params.group !== 'all') query.append('group', params.group);
    if (params.sort_by) query.append('sort_by', params.sort_by);
    if (params.sort_dir) query.append('sort_dir', params.sort_dir);
    if (params.page) query.append('page', params.page);
    if (params.page_size) query.append('page_size', params.page_size);

    const queryString = query.toString() ? `?${query.toString()}` : '';
    return request(`/students${queryString}`);
  }

  function getStudent(id) {
    return request(`/students/${id}`);
  }

  function createStudent(studentData) {
    return request('/students', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(studentData)
    });
  }

  function updateStudent(id, studentData) {
    return request(`/students/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(studentData)
    });
  }

  function deleteStudent(id) {
    return request(`/students/${id}`, {
      method: 'DELETE'
    });
  }

  // 4. CSV Upload
  function uploadCSV(file) {
    const formData = new FormData();
    formData.append('file', file);
    return request('/upload', {
      method: 'POST',
      body: formData
    });
  }

  // 5. Statistical Analysis
  function getStatisticalAnalysis() {
    return request('/analyze');
  }

  // 6. Reports URL
  function getExportCSVUrl() {
    return `${BASE_URL}/reports/csv`;
  }

  return {
    checkHealth,
    getDashboard,
    getStudents,
    getStudent,
    createStudent,
    updateStudent,
    deleteStudent,
    uploadCSV,
    getStatisticalAnalysis,
    getExportCSVUrl
  };
})();

