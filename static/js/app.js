/**
 * AttendX - Main Application Controller (Integrated)
 * Full-stack coordination between browser UI and Flask REST API.
 * Zero mock data: all records and statistical testing reflect live SQLite data.
 */

const App = (() => {
  // Client UI State
  let currentFilter = 'all';
  let currentSearch = '';
  let currentSort = 'roll_number';
  let sortDirection = 'asc';
  let currentPage = 1;
  const pageSize = 8;
  let studentToDelete = null;

  // Helper for attendance classification styling
  function getAttendanceGroup(attendance) {
    if (attendance >= 80) return { key: 'high', label: 'High (≥80%)', badgeClass: 'badge-high' };
    if (attendance >= 60) return { key: 'medium', label: 'Medium (60-80%)', badgeClass: 'badge-medium' };
    return { key: 'low', label: 'Low (<60%)', badgeClass: 'badge-low' };
  }

  // ---------------------------------------------------------------------------
  // 1. Dashboard: Fetch & Render Live Database Metrics
  // ---------------------------------------------------------------------------
  async function loadDashboard() {
    const res = await API.getDashboard();
    if (!res.ok) {
      UI.showToast(res.error, 'error');
      return;
    }

    const data = res.data;
    const totalStudents = data.total_students;
    const highCount = data.groups.high || 0;
    const medCount = data.groups.medium || 0;
    const lowCount = data.groups.low || 0;

    // Update Top Stat Cards
    const totalEl = document.getElementById('stat-total-students');
    const attEl = document.getElementById('stat-avg-attendance');
    const marksEl = document.getElementById('stat-avg-marks');
    const highEl = document.getElementById('stat-group-high');
    const medEl = document.getElementById('stat-group-medium');
    const lowEl = document.getElementById('stat-group-low');

    if (totalEl) totalEl.textContent = totalStudents;
    if (attEl) attEl.textContent = `${data.avg_attendance}%`;
    if (marksEl) marksEl.textContent = data.avg_marks;

    if (highEl) {
      const pct = totalStudents ? ((highCount / totalStudents) * 100).toFixed(0) : 0;
      highEl.textContent = `${highCount} (${pct}%)`;
    }
    if (medEl) {
      const pct = totalStudents ? ((medCount / totalStudents) * 100).toFixed(0) : 0;
      medEl.textContent = `${medCount} (${pct}%)`;
    }
    if (lowEl) {
      const pct = totalStudents ? ((lowCount / totalStudents) * 100).toFixed(0) : 0;
      lowEl.textContent = `${lowCount} (${pct}%)`;
    }

    // Render Live Charts
    Charts.renderScatterPlot('chart-scatter', data.scatter_points);
    Charts.renderGroupBarChart('chart-groups', data.group_averages);
  }

  // ---------------------------------------------------------------------------
  // 2. Student Records: Live Search, Filter, Sort, Pagination
  // ---------------------------------------------------------------------------
  async function loadStudents() {
    const tbody = document.getElementById('students-table-body');
    const countBadge = document.getElementById('students-count-badge');
    const paginationInfo = document.getElementById('pagination-info');
    const prevBtn = document.getElementById('prev-page-btn');
    const nextBtn = document.getElementById('next-page-btn');

    if (!tbody) return;

    tbody.innerHTML = `
      <tr>
        <td colspan="6" style="text-align:center; padding: 2.5rem; color: var(--text-muted);">
          <div style="display:flex; align-items:center; justify-content:center; gap:0.75rem;">
            <span class="spinner"></span>
            <span style="font-size:0.9rem;">Loading student observations from database...</span>
          </div>
        </td>
      </tr>
    `;

    const res = await API.getStudents({
      search: currentSearch,
      group: currentFilter,
      sort_by: currentSort,
      sort_dir: sortDirection,
      page: currentPage,
      page_size: pageSize
    });

    if (!res.ok) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align:center; padding: 2.5rem; color: var(--status-danger);">
            <div style="font-weight:600; margin-bottom:0.25rem;">Failed to retrieve records</div>
            <div style="font-size:0.85rem;">${UI.escapeHTML(res.error)}</div>
          </td>
        </tr>
      `;
      return;
    }

    const { students, total_count } = res.data;
    const totalPages = Math.ceil(total_count / pageSize) || 1;

    if (currentPage > totalPages) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;

    if (countBadge) countBadge.textContent = `${total_count} Records`;
    if (paginationInfo) paginationInfo.textContent = `Page ${currentPage} of ${totalPages} (${total_count} Total)`;
    if (prevBtn) prevBtn.disabled = currentPage <= 1;
    if (nextBtn) nextBtn.disabled = currentPage >= totalPages;

    if (students.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6">
            <div class="empty-state">
              <svg class="empty-state-icon" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"/>
              </svg>
              <div class="empty-state-title">No student observations found</div>
              <div class="empty-state-desc">Try clearing your search term, changing the attendance tier filter, or uploading a CSV dataset.</div>
            </div>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = '';
    students.forEach((s) => {
      const group = getAttendanceGroup(s.attendance_percentage);
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong style="font-family:var(--font-mono); font-weight:600;">${UI.escapeHTML(s.roll_number)}</strong></td>
        <td>${UI.escapeHTML(s.name)}</td>
        <td>
          <div style="display:flex; align-items:center; gap:0.5rem;">
            <span>${Number(s.attendance_percentage).toFixed(1)}%</span>
            <div style="flex:1; max-width:60px; height:6px; background:#e2e8f0; border-radius:3px; overflow:hidden;">
              <div style="width:${Math.min(100, s.attendance_percentage)}%; height:100%; background: ${s.attendance_percentage >= 80 ? 'var(--group-high)' : s.attendance_percentage >= 60 ? 'var(--group-med)' : 'var(--group-low)'};"></div>
            </div>
          </div>
        </td>
        <td><strong>${Number(s.marks).toFixed(1)}</strong> / 100</td>
        <td><span class="badge ${group.badgeClass}">${group.label}</span></td>
        <td>
          <div style="display:flex; gap:0.5rem;">
            <button class="btn btn-secondary btn-sm" onclick="App.openEditStudentModal(${s.id})" title="Edit Student">Edit</button>
            <button class="btn btn-danger btn-sm" onclick="App.confirmDeleteStudent(${s.id}, '${UI.escapeHTML(s.name)}', '${UI.escapeHTML(s.roll_number)}')" title="Delete Student">Delete</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  // ---------------------------------------------------------------------------
  // 3. Add & Edit Student Modal Operations
  // ---------------------------------------------------------------------------
  function openAddStudentModal() {
    document.getElementById('student-modal-title').textContent = 'Add New Student';
    document.getElementById('student-id-field').value = '';
    const rollField = document.getElementById('student-roll-field');
    rollField.value = '';
    rollField.disabled = false;
    document.getElementById('student-name-field').value = '';
    document.getElementById('student-attendance-field').value = '';
    document.getElementById('student-marks-field').value = '';
    UI.openModal('student-form-modal');
  }

  async function openEditStudentModal(id) {
    const res = await API.getStudent(id);
    if (!res.ok) {
      UI.showToast(res.error, 'error');
      return;
    }

    const student = res.data.student;
    document.getElementById('student-modal-title').textContent = 'Edit Student Details';
    document.getElementById('student-id-field').value = student.id;
    const rollField = document.getElementById('student-roll-field');
    rollField.value = student.roll_number;
    rollField.disabled = true; // Roll number is permanent identifier
    document.getElementById('student-name-field').value = student.name;
    document.getElementById('student-attendance-field').value = student.attendance_percentage;
    document.getElementById('student-marks-field').value = student.marks;
    UI.openModal('student-form-modal');
  }

  async function handleSaveStudent(e) {
    e.preventDefault();
    const idField = document.getElementById('student-id-field').value;
    const roll = document.getElementById('student-roll-field').value.trim();
    const name = document.getElementById('student-name-field').value.trim();
    const attendance = parseFloat(document.getElementById('student-attendance-field').value);
    const marks = parseFloat(document.getElementById('student-marks-field').value);

    // Client boundary checks
    if (!name || isNaN(attendance) || isNaN(marks) || (!idField && !roll)) {
      UI.showToast('Please complete all fields with valid numbers.', 'error');
      return;
    }

    if (attendance < 0 || attendance > 100) {
      UI.showToast('Attendance percentage must be between 0.0 and 100.0%.', 'error');
      return;
    }

    if (marks < 0 || marks > 100) {
      UI.showToast('Examination marks must be between 0.0 and 100.0.', 'error');
      return;
    }

    const payload = {
      name: name,
      attendance_percentage: attendance,
      marks: marks
    };
    if (!idField) {
      payload.roll_number = roll;
    }

    let res;
    if (idField) {
      res = await API.updateStudent(idField, payload);
    } else {
      res = await API.createStudent(payload);
    }

    if (!res.ok) {
      const errDetails = res.details?.errors;
      if (errDetails) {
        const firstErr = Object.values(errDetails)[0];
        UI.showToast(firstErr, 'error');
      } else {
        UI.showToast(res.error, 'error');
      }
      return;
    }

    UI.showToast(idField ? `Updated record for ${name}.` : `Student ${name} successfully registered.`, 'success');
    UI.closeModal('student-form-modal');
    refreshAll();
  }

  // ---------------------------------------------------------------------------
  // 4. Delete Student Operations
  // ---------------------------------------------------------------------------
  function confirmDeleteStudent(id, name, roll) {
    studentToDelete = { id, name, roll };
    const labelEl = document.getElementById('delete-student-name');
    if (labelEl) labelEl.textContent = `${name} (${roll})`;
    UI.openModal('delete-confirm-modal');
  }

  async function executeDeleteStudent() {
    if (!studentToDelete) return;
    const res = await API.deleteStudent(studentToDelete.id);
    if (!res.ok) {
      UI.showToast(res.error, 'error');
      return;
    }

    UI.showToast(`Deleted student record for ${studentToDelete.name}.`, 'warning');
    studentToDelete = null;
    UI.closeModal('delete-confirm-modal');
    refreshAll();
  }

  // ---------------------------------------------------------------------------
  // 5. CSV File Upload to Flask Backend
  // ---------------------------------------------------------------------------
  async function handleCSVFile(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith('.csv')) {
      UI.showToast('Invalid file format. Please upload a standard .csv file.', 'error');
      return;
    }

    UI.showToast('Uploading and parsing dataset...', 'info');

    const res = await API.uploadCSV(file);
    const statusCard = document.getElementById('upload-status-card');
    const summaryStats = document.getElementById('upload-summary-stats');
    const rejectionContainer = document.getElementById('upload-rejections-container');
    const rejectionsTbody = document.getElementById('upload-rejections-body');

    if (!res.ok) {
      UI.showToast(res.error, 'error');
      return;
    }

    const result = res.data;

    // Display Status Card
    if (statusCard) statusCard.style.display = 'block';
    if (summaryStats) {
      summaryStats.innerHTML = `
        <div class="stat-highlight-box">
          <span class="stat-highlight-title">Total Records Parsed</span>
          <span class="stat-highlight-val">${result.total_rows}</span>
        </div>
        <div class="stat-highlight-box" style="border-left: 3px solid var(--status-success);">
          <span class="stat-highlight-title">Successfully Inserted</span>
          <span class="stat-highlight-val" style="color:var(--status-success);">${result.inserted_count}</span>
        </div>
        <div class="stat-highlight-box" style="border-left: 3px solid var(--status-danger);">
          <span class="stat-highlight-title">Rejected Rows</span>
          <span class="stat-highlight-val" style="color:var(--status-danger);">${result.rejected_count}</span>
        </div>
      `;
    }

    if (rejectionContainer && rejectionsTbody) {
      if (result.rejected_rows && result.rejected_rows.length > 0) {
        rejectionContainer.style.display = 'block';
        rejectionsTbody.innerHTML = '';
        result.rejected_rows.forEach(r => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td>Row ${r.row}</td>
            <td><strong>${UI.escapeHTML(r.roll_number || 'N/A')}</strong></td>
            <td style="color:var(--status-danger); font-weight:500;">${UI.escapeHTML(r.reason)}</td>
          `;
          rejectionsTbody.appendChild(tr);
        });
      } else {
        rejectionContainer.style.display = 'none';
      }
    }

    UI.showToast(result.message, result.inserted_count > 0 ? 'success' : 'warning');
    if (result.inserted_count > 0) {
      refreshAll();
    }
  }

  // ---------------------------------------------------------------------------
  // 6. Statistical Analysis: Render Live SciPy Results
  // ---------------------------------------------------------------------------
  async function loadStatisticalAnalysis() {
    const res = await API.getStatisticalAnalysis();
    if (!res.ok) {
      UI.showToast(res.error, 'error');
      return;
    }

    const data = res.data;

    if (data.status === 'insufficient_data' || data.status === 'constant_variance') {
      const container = document.getElementById('stats-group-table-body');
      if (container) {
        container.innerHTML = `
          <tr>
            <td colspan="6" style="text-align:center; padding:2rem; color:var(--status-danger);">
              ${UI.escapeHTML(data.message)}
            </td>
          </tr>
        `;
      }
      return;
    }

    // Pearson Correlation
    const pR = document.getElementById('stats-pearson-r');
    const pP = document.getElementById('stats-pearson-p');
    const pCI = document.getElementById('stats-pearson-ci');
    const sampleN = document.getElementById('stats-sample-n');

    if (pR) pR.textContent = (data.pearson.r >= 0 ? '+' : '') + data.pearson.r.toFixed(3);
    if (pP) pP.textContent = data.pearson.p_value < 0.0001 ? 'p < 0.0001' : `p = ${data.pearson.p_value.toFixed(4)}`;
    if (pCI) pCI.textContent = `[${data.pearson.ci_95[0]}, ${data.pearson.ci_95[1]}]`;
    if (sampleN) sampleN.textContent = data.sample_size;

    const pStrength = document.getElementById('stats-pearson-strength');
    const pSig = document.getElementById('stats-pearson-sig');
    const pInterp = document.getElementById('stats-pearson-interp');
    if (pStrength) pStrength.textContent = `Strength: ${data.pearson.strength}`;
    if (pSig) pSig.textContent = data.pearson.significant ? 'Statistically Significant (\u03b1=0.05)' : 'Not Significant (\u03b1=0.05)';
    if (pInterp) pInterp.textContent = data.pearson.interpretation;

    // Spearman Correlation
    const spearmanVal = document.getElementById('stats-spearman-rho');
    const spearmanP = document.getElementById('stats-spearman-p');
    if (spearmanVal) spearmanVal.textContent = (data.spearman.rho >= 0 ? '+' : '') + data.spearman.rho.toFixed(3);
    if (spearmanP) spearmanP.textContent = data.spearman.p_value < 0.0001 ? 'p < 0.0001' : `p = ${data.spearman.p_value.toFixed(4)}`;

    // Update Dashboard Quick Summary Cards
    const dashR = document.getElementById('dash-summary-r');
    const dashRSub = document.getElementById('dash-summary-r-sub');
    const dashRho = document.getElementById('dash-summary-rho');
    const dashRhoSub = document.getElementById('dash-summary-rho-sub');
    const dashAnova = document.getElementById('dash-summary-anova');
    const dashAnovaSub = document.getElementById('dash-summary-anova-sub');

    if (dashR) dashR.textContent = (data.pearson.r >= 0 ? '+' : '') + data.pearson.r.toFixed(3);
    if (dashRSub) dashRSub.textContent = `${data.pearson.strength} linear association (${data.pearson.p_value < 0.001 ? 'p < 0.001' : 'p = ' + data.pearson.p_value.toFixed(3)})`;
    if (dashRho) dashRho.textContent = (data.spearman.rho >= 0 ? '+' : '') + data.spearman.rho.toFixed(3);
    if (dashRhoSub) dashRhoSub.textContent = `Monotonic rank correlation (${data.spearman.p_value < 0.001 ? 'p < 0.001' : 'p = ' + data.spearman.p_value.toFixed(3)})`;
    if (dashAnova && data.anova) {
      dashAnova.textContent = data.anova.significant ? 'Significant (p < 0.05)' : 'Not Significant';
      dashAnovaSub.textContent = data.anova.interpretation;
    }

    // Attendance Groups Breakdown Table
    const groupTbody = document.getElementById('stats-group-table-body');
    if (groupTbody && data.groups) {
      groupTbody.innerHTML = '';
      const order = ['low', 'medium', 'high'];
      const badges = {
        low: 'badge-low',
        medium: 'badge-medium',
        high: 'badge-high'
      };

      order.forEach(key => {
        const grp = data.groups[key];
        const stats = grp.stats || { mean: 0, median: 0, std: 0, min: 0, max: 0 };
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td><span class="badge ${badges[key]}">${UI.escapeHTML(grp.label)}</span></td>
          <td>${grp.count} (${grp.percentage}%)</td>
          <td><strong>${stats.mean.toFixed(1)}</strong></td>
          <td>${stats.median.toFixed(1)}</td>
          <td>${stats.std.toFixed(1)}</td>
          <td>${stats.min.toFixed(1)} &ndash; ${stats.max.toFixed(1)}</td>
        `;
        groupTbody.appendChild(tr);
      });
    }

    // Levene's Test (Homogeneity of Variance)
    if (data.assumptions && data.assumptions.homogeneity_of_variance) {
      const lev = data.assumptions.homogeneity_of_variance;
      const levStat = document.getElementById('levene-stat');
      const levP = document.getElementById('levene-p-val');
      const levVerdict = document.getElementById('levene-verdict');

      if (levStat) levStat.textContent = `W = ${lev.statistic}`;
      if (levP) levP.textContent = `p = ${lev.p_value}`;
      if (levVerdict) levVerdict.textContent = lev.interpretation;
    }

    // ANOVA Results
    if (data.anova) {
      const anova = data.anova;
      const anovaBadge = document.getElementById('anova-test-badge');
      const anovaF = document.getElementById('anova-f-stat');
      const anovaDf = document.getElementById('anova-df-stat');
      const anovaP = document.getElementById('anova-p-val');
      const anovaVerdict = document.getElementById('anova-verdict');

      if (anovaBadge) anovaBadge.textContent = anova.test_name;
      if (anovaF) anovaF.textContent = `F = ${anova.f_statistic}`;
      if (anovaDf) anovaDf.textContent = `(df1 = ${anova.df1}, df2 = ${anova.df2})`;
      if (anovaP) anovaP.textContent = anova.p_value < 0.0001 ? 'p < 0.0001' : `p = ${anova.p_value.toFixed(4)}`;
      if (anovaVerdict) anovaVerdict.textContent = anova.interpretation;

      // Post-Hoc Pairwise Table
      const posthocMethod = document.getElementById('posthoc-method-name');
      const posthocTbody = document.getElementById('posthoc-table-body');

      if (anova.post_hoc && anova.post_hoc.comparisons) {
        if (posthocMethod) posthocMethod.textContent = anova.post_hoc.method;
        if (posthocTbody) {
          posthocTbody.innerHTML = '';
          anova.post_hoc.comparisons.forEach(c => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td><strong>${UI.escapeHTML(c.comparison)}</strong></td>
              <td>${c.mean_diff > 0 ? '+' : ''}${c.mean_diff}</td>
              <td>[${c.ci_95[0]}, ${c.ci_95[1]}]</td>
              <td>${c.p_value < 0.0001 ? '< 0.0001' : c.p_value}</td>
              <td>
                <span class="badge ${c.significant ? 'badge-high' : 'badge-neutral'}">
                  ${c.significant ? 'Yes (Significant)' : 'No'}
                </span>
              </td>
            `;
            posthocTbody.appendChild(tr);
          });
        }
      } else if (posthocTbody) {
        posthocTbody.innerHTML = `
          <tr>
            <td colspan="5" style="text-align:center; padding:1.5rem; color:var(--text-muted);">
              Overall ANOVA is not statistically significant or groups have insufficient samples; post-hoc pairwise testing omitted.
            </td>
          </tr>
        `;
      }
    }
  }

  // ---------------------------------------------------------------------------
  // 7. CSV Export (Direct Download from Flask Stream)
  // ---------------------------------------------------------------------------
  function exportStudentsCSV() {
    window.location.href = API.getExportCSVUrl();
    UI.showToast('Streaming student dataset from database...', 'info');
  }

  // ---------------------------------------------------------------------------
  // 8. Refresh Coordinator
  // ---------------------------------------------------------------------------
  function refreshAll() {
    loadDashboard();
    loadStudents();
    loadStatisticalAnalysis();
  }

  // ---------------------------------------------------------------------------
  // 9. Event Listeners & Bootstrapping
  // ---------------------------------------------------------------------------
  function init() {
    UI.initModals();
    UI.initNavigation();

    // Student Search, Filter, Sort
    const searchInput = document.getElementById('student-search-input');
    if (searchInput) {
      let debounceTimeout;
      searchInput.addEventListener('input', (e) => {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => {
          currentSearch = e.target.value.trim();
          currentPage = 1;
          loadStudents();
        }, 250);
      });
    }

    const groupFilter = document.getElementById('student-group-filter');
    if (groupFilter) {
      groupFilter.addEventListener('change', (e) => {
        currentFilter = e.target.value;
        currentPage = 1;
        loadStudents();
      });
    }

    const sortSelect = document.getElementById('student-sort-select');
    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        const parts = e.target.value.split('-');
        currentSort = parts[0];
        sortDirection = parts[1] || 'asc';
        loadStudents();
      });
    }

    const prevPageBtn = document.getElementById('prev-page-btn');
    if (prevPageBtn) {
      prevPageBtn.addEventListener('click', () => {
        if (currentPage > 1) {
          currentPage--;
          loadStudents();
        }
      });
    }

    const nextPageBtn = document.getElementById('next-page-btn');
    if (nextPageBtn) {
      nextPageBtn.addEventListener('click', () => {
        currentPage++;
        loadStudents();
      });
    }

    // Modal Forms
    const studentForm = document.getElementById('student-form');
    if (studentForm) {
      studentForm.addEventListener('submit', handleSaveStudent);
    }

    const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
    if (confirmDeleteBtn) {
      confirmDeleteBtn.addEventListener('click', executeDeleteStudent);
    }

    // CSV File Upload Listeners
    const fileInput = document.getElementById('csv-file-input');
    const dropzone = document.getElementById('upload-dropzone');

    if (fileInput && dropzone) {
      dropzone.addEventListener('click', () => fileInput.click());
      fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
          handleCSVFile(e.target.files[0]);
        }
      });

      ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          dropzone.classList.add('dragover');
        });
      });

      ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, (e) => {
          e.preventDefault();
          dropzone.classList.remove('dragover');
        });
      });

      dropzone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        if (dt.files.length > 0) {
          handleCSVFile(dt.files[0]);
        }
      });
    }

    // Reports export button
    const exportBtnReport = document.getElementById('export-report-csv-btn');
    if (exportBtnReport) {
      exportBtnReport.addEventListener('click', exportStudentsCSV);
    }

    // Initial Live Data Load
    refreshAll();
  }

  return {
    init,
    openAddStudentModal,
    openEditStudentModal,
    confirmDeleteStudent,
    exportStudentsCSV,
    loadStatisticalAnalysis,
    refreshAll
  };
})();

// Attach to window for global access
window.App = App;

// Bootstrap application on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  App.init();
});
