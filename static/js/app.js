/**
 * AttendX - Main Application Controller
 * Handles student management, state, mock CSV upload, and statistical preview
 */

// =============================================================================
// [PREVIEW / UI MOCK DATA FOR PHASE 2 FRONTEND DESIGN]
// NOTE: This temporary dataset is provided exclusively to demonstrate UI layouts,
// tables, and responsive charts during Phase 2. It will be replaced with live
// SQLite database queries via the Flask REST API in Phase 5.
// =============================================================================
const PREVIEW_DATASET = [
  { id: 1, roll_number: "CS2026-001", name: "Aarav Sharma", attendance_percentage: 92.5, marks: 88.0 },
  { id: 2, roll_number: "CS2026-002", name: "Ananya Iyer", attendance_percentage: 84.0, marks: 81.5 },
  { id: 3, roll_number: "CS2026-003", name: "Rohan Verma", attendance_percentage: 67.5, marks: 62.0 },
  { id: 4, roll_number: "CS2026-004", name: "Priya Nair", attendance_percentage: 95.0, marks: 91.0 },
  { id: 5, roll_number: "CS2026-005", name: "Kabir Mehta", attendance_percentage: 54.0, marks: 49.0 },
  { id: 6, roll_number: "CS2026-006", name: "Diya Patel", attendance_percentage: 78.5, marks: 74.0 },
  { id: 7, roll_number: "CS2026-007", name: "Siddharth Rao", attendance_percentage: 88.0, marks: 83.5 },
  { id: 8, roll_number: "CS2026-008", name: "Sneha Kulkarni", attendance_percentage: 48.0, marks: 42.0 },
  { id: 9, roll_number: "CS2026-009", name: "Aditya Joshi", attendance_percentage: 72.0, marks: 68.0 },
  { id: 10, roll_number: "CS2026-010", name: "Ishaan Gupta", attendance_percentage: 61.5, marks: 59.0 },
  { id: 11, roll_number: "CS2026-011", name: "Rhea Deshmukh", attendance_percentage: 96.0, marks: 94.0 },
  { id: 12, roll_number: "CS2026-012", name: "Varun Pillai", attendance_percentage: 74.0, marks: 71.0 },
  { id: 13, roll_number: "CS2026-013", name: "Meera Sen", attendance_percentage: 86.5, marks: 79.0 },
  { id: 14, roll_number: "CS2026-014", name: "Aryan Reddy", attendance_percentage: 51.0, marks: 45.0 },
  { id: 15, roll_number: "CS2026-015", name: "Tanvi Bhatt", attendance_percentage: 81.0, marks: 77.5 },
  { id: 16, roll_number: "CS2026-016", name: "Kunal Ghosh", attendance_percentage: 69.0, marks: 64.0 },
  { id: 17, roll_number: "CS2026-017", name: "Pooja Hegde", attendance_percentage: 90.0, marks: 86.0 },
  { id: 18, roll_number: "CS2026-018", name: "Nikhil Menon", attendance_percentage: 58.5, marks: 53.0 },
  { id: 19, roll_number: "CS2026-019", name: "Shreya Saxena", attendance_percentage: 83.5, marks: 80.0 },
  { id: 20, roll_number: "CS2026-020", name: "Gaurav Malhotra", attendance_percentage: 42.0, marks: 38.0 },
  { id: 21, roll_number: "CS2026-021", name: "Avani Trivedi", attendance_percentage: 97.0, marks: 93.0 },
  { id: 22, roll_number: "CS2026-022", name: "Rahul Choudhury", attendance_percentage: 76.0, marks: 70.0 },
  { id: 23, roll_number: "CS2026-023", name: "Simran Kaur", attendance_percentage: 89.0, marks: 85.0 },
  { id: 24, roll_number: "CS2026-024", name: "Devansh Nambiar", attendance_percentage: 63.0, marks: 60.0 },
  { id: 25, roll_number: "CS2026-025", name: "Bhavna Mishra", attendance_percentage: 55.0, marks: 50.0 },
  { id: 26, roll_number: "CS2026-026", name: "Harsh Vardhan", attendance_percentage: 82.0, marks: 76.0 },
  { id: 27, roll_number: "CS2026-027", name: "Kritika Roy", attendance_percentage: 91.0, marks: 89.0 },
  { id: 28, roll_number: "CS2026-028", name: "Alok Pandey", attendance_percentage: 45.0, marks: 40.0 },
  { id: 29, roll_number: "CS2026-029", name: "Neha Agarwal", attendance_percentage: 77.0, marks: 72.0 },
  { id: 30, roll_number: "CS2026-030", name: "Vikram Singhania", attendance_percentage: 85.0, marks: 82.0 }
];

const App = (() => {
  // State
  let students = [...PREVIEW_DATASET];
  let currentFilter = 'all';
  let currentSearch = '';
  let currentSort = 'roll_number';
  let sortDirection = 'asc';
  let currentPage = 1;
  const pageSize = 8;
  let studentToDelete = null;

  // Helpers
  function getAttendanceGroup(attendance) {
    if (attendance >= 80) return { key: 'high', label: 'High (≥80%)', badgeClass: 'badge-high' };
    if (attendance >= 60) return { key: 'medium', label: 'Medium (60-80%)', badgeClass: 'badge-medium' };
    return { key: 'low', label: 'Low (<60%)', badgeClass: 'badge-low' };
  }

  // ---------------------------------------------------------------------------
  // 1. Dashboard Metrics & Visualizations
  // ---------------------------------------------------------------------------
  function updateDashboard() {
    const totalStudents = students.length;
    const totalAttendance = students.reduce((acc, s) => acc + s.attendance_percentage, 0);
    const totalMarks = students.reduce((acc, s) => acc + s.marks, 0);

    const avgAttendance = totalStudents ? (totalAttendance / totalStudents).toFixed(1) : '0.0';
    const avgMarks = totalStudents ? (totalMarks / totalStudents).toFixed(1) : '0.0';

    const highCount = students.filter(s => s.attendance_percentage >= 80).length;
    const medCount = students.filter(s => s.attendance_percentage >= 60 && s.attendance_percentage < 80).length;
    const lowCount = students.filter(s => s.attendance_percentage < 60).length;

    // Update DOM Stat Cards
    const totalEl = document.getElementById('stat-total-students');
    const attEl = document.getElementById('stat-avg-attendance');
    const marksEl = document.getElementById('stat-avg-marks');
    const highEl = document.getElementById('stat-group-high');
    const medEl = document.getElementById('stat-group-medium');
    const lowEl = document.getElementById('stat-group-low');

    if (totalEl) totalEl.textContent = totalStudents;
    if (attEl) attEl.textContent = `${avgAttendance}%`;
    if (marksEl) marksEl.textContent = avgMarks;
    if (highEl) highEl.textContent = `${highCount} (${((highCount/totalStudents)*100 || 0).toFixed(0)}%)`;
    if (medEl) medEl.textContent = `${medCount} (${((medCount/totalStudents)*100 || 0).toFixed(0)}%)`;
    if (lowEl) lowEl.textContent = `${lowCount} (${((lowCount/totalStudents)*100 || 0).toFixed(0)}%)`;

    // Render Charts
    Charts.renderScatterPlot('chart-scatter', students);
    Charts.renderGroupBarChart('chart-groups', students);
  }

  // ---------------------------------------------------------------------------
  // 2. Student Management: Filter, Sort, Pagination, Render Table
  // ---------------------------------------------------------------------------
  function getFilteredStudents() {
    return students.filter(s => {
      // Group filter
      if (currentFilter !== 'all') {
        const group = getAttendanceGroup(s.attendance_percentage).key;
        if (group !== currentFilter) return false;
      }
      // Search filter
      if (currentSearch) {
        const query = currentSearch.toLowerCase();
        const matchRoll = s.roll_number.toLowerCase().includes(query);
        const matchName = s.name.toLowerCase().includes(query);
        if (!matchRoll && !matchName) return false;
      }
      return true;
    }).sort((a, b) => {
      let valA = a[currentSort];
      let valB = b[currentSort];
      if (typeof valA === 'string') {
        return sortDirection === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
      }
      return sortDirection === 'asc' ? valA - valB : valB - valA;
    });
  }

  function renderStudentTable() {
    const tbody = document.getElementById('students-table-body');
    const countBadge = document.getElementById('students-count-badge');
    const paginationInfo = document.getElementById('pagination-info');
    const prevBtn = document.getElementById('prev-page-btn');
    const nextBtn = document.getElementById('next-page-btn');

    if (!tbody) return;

    const filtered = getFilteredStudents();
    const totalRecords = filtered.length;
    const totalPages = Math.ceil(totalRecords / pageSize) || 1;

    if (currentPage > totalPages) currentPage = totalPages;
    if (currentPage < 1) currentPage = 1;

    const startIdx = (currentPage - 1) * pageSize;
    const pageData = filtered.slice(startIdx, startIdx + pageSize);

    if (countBadge) countBadge.textContent = `${totalRecords} Records`;
    if (paginationInfo) paginationInfo.textContent = `Page ${currentPage} of ${totalPages} (${totalRecords} Total)`;
    if (prevBtn) prevBtn.disabled = currentPage <= 1;
    if (nextBtn) nextBtn.disabled = currentPage >= totalPages;

    if (pageData.length === 0) {
      tbody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align:center; padding: 2.5rem; color: var(--text-muted);">
            <div style="font-size: 1.1rem; font-weight: 500; margin-bottom: 0.5rem;">No student records found</div>
            <div style="font-size: 0.85rem;">Try adjusting your search criteria or filter settings.</div>
          </td>
        </tr>
      `;
      return;
    }

    tbody.innerHTML = '';
    pageData.forEach((s) => {
      const group = getAttendanceGroup(s.attendance_percentage);
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong style="font-family:var(--font-mono); font-weight:600;">${UI.escapeHTML(s.roll_number)}</strong></td>
        <td>${UI.escapeHTML(s.name)}</td>
        <td>
          <div style="display:flex; align-items:center; gap:0.5rem;">
            <span>${s.attendance_percentage.toFixed(1)}%</span>
            <div style="flex:1; max-width:60px; height:6px; background:#e2e8f0; border-radius:3px; overflow:hidden;">
              <div style="width:${Math.min(100, s.attendance_percentage)}%; height:100%; background: ${s.attendance_percentage >= 80 ? 'var(--group-high)' : s.attendance_percentage >= 60 ? 'var(--group-med)' : 'var(--group-low)'};"></div>
            </div>
          </div>
        </td>
        <td><strong>${s.marks.toFixed(1)}</strong> / 100</td>
        <td><span class="badge ${group.badgeClass}">${group.label}</span></td>
        <td>
          <div style="display:flex; gap:0.5rem;">
            <button class="btn btn-secondary btn-sm" onclick="App.openEditStudentModal(${s.id})" title="Edit Student">Edit</button>
            <button class="btn btn-danger btn-sm" onclick="App.confirmDeleteStudent(${s.id})" title="Delete Student">Delete</button>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    });
  }

  // ---------------------------------------------------------------------------
  // 3. Add & Edit Student Modal Management
  // ---------------------------------------------------------------------------
  function openAddStudentModal() {
    document.getElementById('student-modal-title').textContent = 'Add New Student';
    document.getElementById('student-id-field').value = '';
    document.getElementById('student-roll-field').value = '';
    document.getElementById('student-roll-field').disabled = false;
    document.getElementById('student-name-field').value = '';
    document.getElementById('student-attendance-field').value = '';
    document.getElementById('student-marks-field').value = '';
    UI.openModal('student-form-modal');
  }

  function openEditStudentModal(id) {
    const student = students.find(s => s.id === id);
    if (!student) return;

    document.getElementById('student-modal-title').textContent = 'Edit Student Details';
    document.getElementById('student-id-field').value = student.id;
    document.getElementById('student-roll-field').value = student.roll_number;
    document.getElementById('student-roll-field').disabled = true; // Roll number immutable in edit
    document.getElementById('student-name-field').value = student.name;
    document.getElementById('student-attendance-field').value = student.attendance_percentage;
    document.getElementById('student-marks-field').value = student.marks;
    UI.openModal('student-form-modal');
  }

  function handleSaveStudent(e) {
    e.preventDefault();
    const idField = document.getElementById('student-id-field').value;
    const roll = document.getElementById('student-roll-field').value.trim();
    const name = document.getElementById('student-name-field').value.trim();
    const attendance = parseFloat(document.getElementById('student-attendance-field').value);
    const marks = parseFloat(document.getElementById('student-marks-field').value);

    // Validation
    if (!roll || !name || isNaN(attendance) || isNaN(marks)) {
      UI.showToast('Please complete all required fields with valid numbers.', 'error');
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

    if (idField) {
      // Edit existing
      const existing = students.find(s => s.id === parseInt(idField));
      if (existing) {
        existing.name = name;
        existing.attendance_percentage = attendance;
        existing.marks = marks;
        UI.showToast(`Updated record for ${name} (${roll}).`, 'success');
      }
    } else {
      // Add new: check roll uniqueness
      if (students.some(s => s.roll_number.toLowerCase() === roll.toLowerCase())) {
        UI.showToast(`Roll number "${roll}" already exists in the system.`, 'error');
        return;
      }

      const newId = students.length ? Math.max(...students.map(s => s.id)) + 1 : 1;
      students.unshift({
        id: newId,
        roll_number: roll,
        name: name,
        attendance_percentage: attendance,
        marks: marks
      });
      UI.showToast(`Student ${name} added successfully.`, 'success');
    }

    UI.closeModal('student-form-modal');
    renderStudentTable();
    updateDashboard();
    updateStatisticalAnalysis();
  }

  // ---------------------------------------------------------------------------
  // 4. Delete Student Confirmation
  // ---------------------------------------------------------------------------
  function confirmDeleteStudent(id) {
    const student = students.find(s => s.id === id);
    if (!student) return;
    studentToDelete = student;

    document.getElementById('delete-student-name').textContent = `${student.name} (${student.roll_number})`;
    UI.openModal('delete-confirm-modal');
  }

  function executeDeleteStudent() {
    if (!studentToDelete) return;
    students = students.filter(s => s.id !== studentToDelete.id);
    UI.showToast(`Deleted student ${studentToDelete.name}.`, 'warning');
    studentToDelete = null;
    UI.closeModal('delete-confirm-modal');

    renderStudentTable();
    updateDashboard();
    updateStatisticalAnalysis();
  }

  // ---------------------------------------------------------------------------
  // 5. Client-Side CSV Upload Preview (Simulates Phase 3 Backend Validator)
  // ---------------------------------------------------------------------------
  function parseCSVLine(text) {
    const lines = text.split(/\r?\n/).filter(line => line.trim().length > 0);
    if (lines.length < 2) return { error: 'CSV file is empty or missing data rows.' };

    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    const required = ['roll_number', 'name', 'attendance_percentage', 'marks'];
    const missing = required.filter(r => !headers.includes(r));

    if (missing.length > 0) {
      return { error: `Missing required column(s): ${missing.join(', ')}` };
    }

    const rollIdx = headers.indexOf('roll_number');
    const nameIdx = headers.indexOf('name');
    const attIdx = headers.indexOf('attendance_percentage');
    const marksIdx = headers.indexOf('marks');

    const validRows = [];
    const rejectedRows = [];

    for (let i = 1; i < lines.length; i++) {
      const parts = lines[i].split(',').map(p => p.trim());
      const rowNum = i + 1;

      if (parts.length < headers.length) {
        rejectedRows.push({ row: rowNum, reason: 'Row has missing columns' });
        continue;
      }

      const roll = parts[rollIdx];
      const name = parts[nameIdx];
      const attendance = parseFloat(parts[attIdx]);
      const marks = parseFloat(parts[marksIdx]);

      if (!roll || !name) {
        rejectedRows.push({ row: rowNum, roll: roll || 'N/A', reason: 'Missing name or roll number' });
        continue;
      }

      if (isNaN(attendance) || attendance < 0 || attendance > 100) {
        rejectedRows.push({ row: rowNum, roll: roll, reason: `Invalid attendance value: ${parts[attIdx]}` });
        continue;
      }

      if (isNaN(marks) || marks < 0 || marks > 100) {
        rejectedRows.push({ row: rowNum, roll: roll, reason: `Invalid marks value: ${parts[marksIdx]}` });
        continue;
      }

      validRows.push({
        roll_number: roll,
        name: name,
        attendance_percentage: attendance,
        marks: marks
      });
    }

    return { validRows, rejectedRows, total: lines.length - 1 };
  }

  function handleCSVFile(file) {
    if (!file) return;
    if (!file.name.endsWith('.csv')) {
      UI.showToast('Please select a valid .csv file.', 'error');
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target.result;
      const result = parseCSVLine(content);

      const statusCard = document.getElementById('upload-status-card');
      const summaryStats = document.getElementById('upload-summary-stats');
      const rejectionContainer = document.getElementById('upload-rejections-container');
      const rejectionsTbody = document.getElementById('upload-rejections-body');

      if (result.error) {
        UI.showToast(result.error, 'error');
        return;
      }

      // Add valid rows ensuring roll uniqueness
      let added = 0;
      let dupes = 0;
      result.validRows.forEach(row => {
        if (students.some(s => s.roll_number.toLowerCase() === row.roll_number.toLowerCase())) {
          result.rejectedRows.push({ row: '-', roll: row.roll_number, reason: 'Duplicate roll number already exists' });
          dupes++;
        } else {
          const newId = students.length ? Math.max(...students.map(s => s.id)) + 1 : 1;
          students.push({ id: newId, ...row });
          added++;
        }
      });

      // Display Status Card
      if (statusCard) statusCard.style.display = 'block';
      if (summaryStats) {
        summaryStats.innerHTML = `
          <div class="stat-highlight-box">
            <span class="stat-highlight-title">Total Records Parsed</span>
            <span class="stat-highlight-val">${result.total}</span>
          </div>
          <div class="stat-highlight-box" style="border-left: 3px solid var(--status-success);">
            <span class="stat-highlight-title">Successfully Imported</span>
            <span class="stat-highlight-val" style="color:var(--status-success);">${added}</span>
          </div>
          <div class="stat-highlight-box" style="border-left: 3px solid var(--status-danger);">
            <span class="stat-highlight-title">Rejected Rows</span>
            <span class="stat-highlight-val" style="color:var(--status-danger);">${result.rejectedRows.length}</span>
          </div>
        `;
      }

      if (rejectionContainer && rejectionsTbody) {
        if (result.rejectedRows.length > 0) {
          rejectionContainer.style.display = 'block';
          rejectionsTbody.innerHTML = '';
          result.rejectedRows.forEach(r => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
              <td>Row ${r.row}</td>
              <td>${UI.escapeHTML(r.roll || 'N/A')}</td>
              <td style="color:var(--status-danger); font-weight:500;">${UI.escapeHTML(r.reason)}</td>
            `;
            rejectionsTbody.appendChild(tr);
          });
        } else {
          rejectionContainer.style.display = 'none';
        }
      }

      UI.showToast(`Import completed: ${added} records added, ${result.rejectedRows.length} rejected.`, added > 0 ? 'success' : 'warning');
      renderStudentTable();
      updateDashboard();
      updateStatisticalAnalysis();
    };

    reader.readAsText(file);
  }

  // ---------------------------------------------------------------------------
  // 6. Statistical Analysis Preview (Calculated dynamically from current state)
  // ---------------------------------------------------------------------------
  function calculateStats(arr) {
    const n = arr.length;
    if (n === 0) return { mean: 0, median: 0, std: 0, min: 0, max: 0 };
    const sorted = [...arr].sort((a, b) => a - b);
    const sum = sorted.reduce((a, b) => a + b, 0);
    const mean = sum / n;
    const median = n % 2 === 0 ? (sorted[n/2 - 1] + sorted[n/2]) / 2 : sorted[Math.floor(n/2)];
    const variance = sorted.reduce((acc, v) => acc + Math.pow(v - mean, 2), 0) / (n > 1 ? n - 1 : 1);
    const std = Math.sqrt(variance);
    return {
      mean: Number(mean.toFixed(2)),
      median: Number(median.toFixed(2)),
      std: Number(std.toFixed(2)),
      min: Number(sorted[0].toFixed(1)),
      max: Number(sorted[n - 1].toFixed(1))
    };
  }

  function calculatePearson(xArr, yArr) {
    const n = xArr.length;
    if (n < 3) return { r: 0, pVal: 1, ciLower: 0, ciUpper: 0 };

    const xMean = xArr.reduce((a, b) => a + b, 0) / n;
    const yMean = yArr.reduce((a, b) => a + b, 0) / n;

    let num = 0, denX = 0, denY = 0;
    for (let i = 0; i < n; i++) {
      const dx = xArr[i] - xMean;
      const dy = yArr[i] - yMean;
      num += dx * dy;
      denX += dx * dx;
      denY += dy * dy;
    }

    const r = (denX === 0 || denY === 0) ? 0 : num / Math.sqrt(denX * denY);

    // Approximate t-stat and 95% CI
    const t = r * Math.sqrt((n - 2) / Math.max(0.0001, 1 - r * r));
    const z = 0.5 * Math.log((1 + r) / Math.max(0.0001, 1 - r));
    const seZ = 1 / Math.sqrt(n - 3);
    const zLower = z - 1.96 * seZ;
    const zUpper = z + 1.96 * seZ;
    const ciLower = (Math.exp(2 * zLower) - 1) / (Math.exp(2 * zLower) + 1);
    const ciUpper = (Math.exp(2 * zUpper) - 1) / (Math.exp(2 * zUpper) + 1);

    // Approximate two-tailed p-value
    const pVal = Math.abs(t) > 3.5 ? 0.0001 : Math.abs(t) > 2.0 ? 0.045 : 0.25;

    return {
      r: Number(r.toFixed(3)),
      pVal: pVal < 0.001 ? '< 0.001' : pVal.toFixed(3),
      ciLower: Number(ciLower.toFixed(3)),
      ciUpper: Number(ciUpper.toFixed(3))
    };
  }

  function updateStatisticalAnalysis() {
    const attArr = students.map(s => s.attendance_percentage);
    const marksArr = students.map(s => s.marks);

    const attStats = calculateStats(attArr);
    const marksStats = calculateStats(marksArr);
    const pearson = calculatePearson(attArr, marksArr);

    // Group breakdown
    const low = students.filter(s => s.attendance_percentage < 60).map(s => s.marks);
    const med = students.filter(s => s.attendance_percentage >= 60 && s.attendance_percentage < 80).map(s => s.marks);
    const high = students.filter(s => s.attendance_percentage >= 80).map(s => s.marks);

    const lowStats = calculateStats(low);
    const medStats = calculateStats(med);
    const highStats = calculateStats(high);

    // Update DOM values in Analysis section
    const pearsonR = document.getElementById('stats-pearson-r');
    const pearsonP = document.getElementById('stats-pearson-p');
    const pearsonCI = document.getElementById('stats-pearson-ci');
    const sampleN = document.getElementById('stats-sample-n');

    if (pearsonR) pearsonR.textContent = pearson.r;
    if (pearsonP) pearsonP.textContent = `p = ${pearson.pVal}`;
    if (pearsonCI) pearsonCI.textContent = `[${pearson.ciLower}, ${pearson.ciUpper}]`;
    if (sampleN) sampleN.textContent = students.length;

    // Group Table
    const groupTableBody = document.getElementById('stats-group-table-body');
    if (groupTableBody) {
      groupTableBody.innerHTML = `
        <tr>
          <td><span class="badge badge-low">Low (&lt;60%)</span></td>
          <td>${low.length}</td>
          <td><strong>${lowStats.mean}</strong></td>
          <td>${lowStats.median}</td>
          <td>${lowStats.std}</td>
          <td>${lowStats.min} - ${lowStats.max}</td>
        </tr>
        <tr>
          <td><span class="badge badge-medium">Medium (60-80%)</span></td>
          <td>${med.length}</td>
          <td><strong>${medStats.mean}</strong></td>
          <td>${medStats.median}</td>
          <td>${medStats.std}</td>
          <td>${medStats.min} - ${medStats.max}</td>
        </tr>
        <tr>
          <td><span class="badge badge-high">High (≥80%)</span></td>
          <td>${high.length}</td>
          <td><strong>${highStats.mean}</strong></td>
          <td>${highStats.median}</td>
          <td>${highStats.std}</td>
          <td>${highStats.min} - ${highStats.max}</td>
        </tr>
      `;
    }
  }

  // ---------------------------------------------------------------------------
  // 7. CSV Download & Export
  // ---------------------------------------------------------------------------
  function exportStudentsCSV() {
    const headers = ['id', 'roll_number', 'name', 'attendance_percentage', 'marks'];
    const rows = students.map(s => [s.id, `"${s.roll_number}"`, `"${s.name}"`, s.attendance_percentage, s.marks].join(','));
    const csvContent = 'data:text/csv;charset=utf-8,' + [headers.join(','), ...rows].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `attendx_student_records_${new Date().toISOString().slice(0,10)}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    UI.showToast('Student dataset exported successfully.', 'success');
  }

  // ---------------------------------------------------------------------------
  // 8. Initialization & Event Binding
  // ---------------------------------------------------------------------------
  function init() {
    UI.initModals();
    UI.initNavigation();

    // Student Management Listeners
    const searchInput = document.getElementById('student-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        currentSearch = e.target.value;
        currentPage = 1;
        renderStudentTable();
      });
    }

    const groupFilter = document.getElementById('student-group-filter');
    if (groupFilter) {
      groupFilter.addEventListener('change', (e) => {
        currentFilter = e.target.value;
        currentPage = 1;
        renderStudentTable();
      });
    }

    const sortSelect = document.getElementById('student-sort-select');
    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        const [field, dir] = e.target.value.split('-');
        currentSort = field;
        sortDirection = dir || 'asc';
        renderStudentTable();
      });
    }

    const prevPageBtn = document.getElementById('prev-page-btn');
    if (prevPageBtn) {
      prevPageBtn.addEventListener('click', () => {
        if (currentPage > 1) {
          currentPage--;
          renderStudentTable();
        }
      });
    }

    const nextPageBtn = document.getElementById('next-page-btn');
    if (nextPageBtn) {
      nextPageBtn.addEventListener('click', () => {
        currentPage++;
        renderStudentTable();
      });
    }

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

      // Drag and drop events
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

    // Export button listeners
    const exportBtn = document.getElementById('export-csv-btn');
    if (exportBtn) {
      exportBtn.addEventListener('click', exportStudentsCSV);
    }

    const exportBtnReport = document.getElementById('export-report-csv-btn');
    if (exportBtnReport) {
      exportBtnReport.addEventListener('click', exportStudentsCSV);
    }

    // Initial Renders
    updateDashboard();
    renderStudentTable();
    updateStatisticalAnalysis();
  }

  return {
    init,
    openAddStudentModal,
    openEditStudentModal,
    confirmDeleteStudent,
    exportStudentsCSV
  };
})();

// Bootstrap application on DOM ready
document.addEventListener('DOMContentLoaded', () => {
  App.init();
});

