/**
 * AttendX - Visualizations & Chart.js Engine
 * Modular renderers for Scatter Plot and Group Comparisons
 */

const Charts = (() => {
  let scatterChartInstance = null;
  let barChartInstance = null;

  // Linear Regression Helper for Trendline: y = mx + c
  function calculateLinearRegression(points) {
    const n = points.length;
    if (n < 2) return null;

    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    points.forEach(p => {
      sumX += p.x;
      sumY += p.y;
      sumXY += p.x * p.y;
      sumX2 += p.x * p.x;
    });

    const denominator = (n * sumX2 - sumX * sumX);
    if (denominator === 0) return null;

    const slope = (n * sumXY - sumX * sumY) / denominator;
    const intercept = (sumY - slope * sumX) / n;

    // Generate trendline end points within domain
    const minX = Math.min(...points.map(p => p.x));
    const maxX = Math.max(...points.map(p => p.x));

    return [
      { x: minX, y: Math.max(0, Math.min(100, Number((slope * minX + intercept).toFixed(1)))) },
      { x: maxX, y: Math.max(0, Math.min(100, Number((slope * maxX + intercept).toFixed(1)))) }
    ];
  }

  // Determine Attendance Group Color
  function getPointColor(attendance) {
    if (attendance >= 80) return '#059669'; // Emerald
    if (attendance >= 60) return '#d97706'; // Amber
    return '#dc2626'; // Rose
  }

  // Render or Update Scatter Plot
  function renderScatterPlot(canvasId, students) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (scatterChartInstance) {
      scatterChartInstance.destroy();
      scatterChartInstance = null;
    }

    const points = (students || []).map(s => ({
      x: Number(s.x !== undefined ? s.x : s.attendance_percentage),
      y: Number(s.y !== undefined ? s.y : s.marks),
      name: s.name,
      roll_number: s.roll_number
    }));

    const pointColors = points.map(p => getPointColor(p.x));
    const trendlinePoints = calculateLinearRegression(points);

    const datasets = [
      {
        type: 'scatter',
        label: 'Student Records',
        data: points,
        backgroundColor: pointColors,
        borderColor: pointColors,
        pointRadius: 5,
        pointHoverRadius: 7,
        pointHoverBorderWidth: 2,
        pointHoverBorderColor: '#0f172a'
      }
    ];

    if (trendlinePoints) {
      datasets.push({
        type: 'line',
        label: 'Linear Trendline (OLS)',
        data: trendlinePoints,
        borderColor: '#2563eb',
        borderWidth: 2,
        borderDash: [5, 5],
        fill: false,
        pointRadius: 0,
        tension: 0
      });
    }

    scatterChartInstance = new Chart(ctx, {
      data: { datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 600 },
        plugins: {
          legend: {
            display: true,
            position: 'top',
            labels: {
              boxWidth: 12,
              font: { size: 12, family: 'system-ui' }
            }
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                if (context.dataset.type === 'line') {
                  return 'Fitted OLS Trendline';
                }
                const raw = context.raw;
                return [
                  `${raw.name} (${raw.roll_number})`,
                  `Attendance: ${raw.x}%`,
                  `Examination Marks: ${raw.y}`
                ];
              }
            }
          }
        },
        scales: {
          x: {
            title: {
              display: true,
              text: 'Attendance Percentage (%)',
              font: { weight: '600' }
            },
            min: 0,
            max: 100,
            grid: { color: '#f1f5f9' }
          },
          y: {
            title: {
              display: true,
              text: 'Examination Marks',
              font: { weight: '600' }
            },
            min: 0,
            max: 100,
            grid: { color: '#f1f5f9' }
          }
        }
      }
    });
  }

  // Render or Update Group Comparison Bar Chart
  function renderGroupBarChart(canvasId, inputData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (barChartInstance) {
      barChartInstance.destroy();
      barChartInstance = null;
    }

    let labels = [];
    let dataValues = [];
    let counts = [];

    if (Array.isArray(inputData) && inputData.length > 0 && inputData[0].avg_marks !== undefined) {
      // Direct group_averages array from /api/dashboard
      labels = inputData.map(g => `${g.group}\n(n=${g.count})`);
      dataValues = inputData.map(g => Number(g.avg_marks));
      counts = inputData.map(g => Number(g.count));
    } else {
      // Calculated from raw array
      const arr = inputData || [];
      const lowGroup = arr.filter(s => (s.attendance_percentage ?? s.x) < 60);
      const medGroup = arr.filter(s => (s.attendance_percentage ?? s.x) >= 60 && (s.attendance_percentage ?? s.x) < 80);
      const highGroup = arr.filter(s => (s.attendance_percentage ?? s.x) >= 80);

      const calcAvg = a => a.length ? Number((a.reduce((acc, curr) => acc + (curr.marks ?? curr.y), 0) / a.length).toFixed(1)) : 0;

      labels = [
        `Low (<60%)\n(n=${lowGroup.length})`,
        `Medium (60-80%)\n(n=${medGroup.length})`,
        `High (≥80%)\n(n=${highGroup.length})`
      ];
      dataValues = [calcAvg(lowGroup), calcAvg(medGroup), calcAvg(highGroup)];
      counts = [lowGroup.length, medGroup.length, highGroup.length];
    }

    barChartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Average Examination Marks',
          data: dataValues,
          backgroundColor: [
            'rgba(220, 38, 38, 0.85)',   // Rose
            'rgba(217, 119, 6, 0.85)',   // Amber
            'rgba(5, 150, 105, 0.85)'    // Emerald
          ],
          borderColor: [
            '#dc2626',
            '#d97706',
            '#059669'
          ],
          borderWidth: 1,
          borderRadius: 6,
          barPercentage: 0.55
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              afterLabel: (context) => {
                const idx = context.dataIndex;
                const sampleCount = counts[idx] !== undefined ? counts[idx] : 0;
                return `Group Sample Size: ${sampleCount} students`;
              }
            }
          }
        },
        scales: {
          y: {
            title: {
              display: true,
              text: 'Mean Examination Marks',
              font: { weight: '600' }
            },
            min: 0,
            max: 100,
            grid: { color: '#f1f5f9' }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  }

  return {
    renderScatterPlot,
    renderGroupBarChart
  };
})();

