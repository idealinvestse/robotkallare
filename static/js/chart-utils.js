/**
 * Chart utility functions for GDial dashboard
 * Uses Chart.js for visualization
 */

// Colors for consistent chart styling
const chartColors = {
  primary: '#2e5bff',
  primaryLight: 'rgba(46, 91, 255, 0.2)',
  success: '#34c759',
  successLight: 'rgba(52, 199, 89, 0.2)',
  warning: '#ff9500',
  warningLight: 'rgba(255, 149, 0, 0.2)',
  danger: '#ff3b30',
  dangerLight: 'rgba(255, 59, 48, 0.2)',
  info: '#007aff',
  infoLight: 'rgba(0, 122, 255, 0.2)',
  gray: '#adb5bd',
  grayLight: 'rgba(173, 181, 189, 0.2)',
};

// Common chart options
const commonChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false,
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      titleFont: {
        family: "'Inter', 'Segoe UI', 'Roboto', Arial, sans-serif",
        size: 14,
        weight: 600,
      },
      bodyFont: {
        family: "'Inter', 'Segoe UI', 'Roboto', Arial, sans-serif",
        size: 13,
      },
      padding: 12,
      cornerRadius: 8,
      caretSize: 6,
    },
  },
  animation: {
    duration: 1000,
    easing: 'easeOutQuart',
  },
};

// Specific chart configurations
const chartConfigs = {
  doughnut: {
    cutout: '70%',
    borderWidth: 0,
    plugins: {
      tooltip: {
        callbacks: {
          label: function(context) {
            const label = context.label || '';
            const value = context.raw || 0;
            const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
            const percentage = Math.round((value / total) * 100);
            return `${label}: ${value} (${percentage}%)`;
          }
        }
      }
    }
  },
  bar: {
    scales: {
      x: {
        grid: {
          display: false,
        },
        ticks: {
          font: {
            family: "'Inter', 'Segoe UI', 'Roboto', Arial, sans-serif",
            size: 12,
          },
        },
      },
      y: {
        beginAtZero: true,
        ticks: {
          font: {
            family: "'Inter', 'Segoe UI', 'Roboto', Arial, sans-serif",
            size: 12,
          },
          stepSize: 10,
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
          drawBorder: false,
        },
      },
    },
  },
  line: {
    elements: {
      line: {
        tension: 0.3, // Smoother curves
      },
      point: {
        radius: 4,
        hitRadius: 10,
        hoverRadius: 6,
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
        ticks: {
          font: {
            family: "'Inter', 'Segoe UI', 'Roboto', Arial, sans-serif",
            size: 12,
          },
        },
      },
      y: {
        beginAtZero: true,
        ticks: {
          font: {
            family: "'Inter', 'Segoe UI', 'Roboto', Arial, sans-serif",
            size: 12,
          },
          stepSize: 10,
        },
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
          drawBorder: false,
        },
      },
    },
  },
};

/**
 * Create and return a preconfigured chart instance
 * @param {string} type - Chart type (bar, line, doughnut, etc.)
 * @param {HTMLElement} ctx - Canvas context
 * @param {Object} data - Chart data
 * @param {Object} additionalOptions - Additional chart options
 * @returns {Chart} Chart instance
 */
function createChart(type, ctx, data, additionalOptions = {}) {
  const chartTypeOptions = chartConfigs[type] || {};
  
  const options = {
    ...commonChartOptions,
    ...chartTypeOptions,
    ...additionalOptions,
  };
  
  return new Chart(ctx, {
    type: type,
    data: data,
    options: options,
  });
}

/**
 * Create call stats chart (doughnut)
 * @param {HTMLElement} ctx - Canvas context
 * @param {Object} stats - Call statistics
 * @returns {Chart} Chart instance
 */
function createCallStatsChart(ctx, stats) {
  const data = {
    labels: ['Completed', 'No Answer', 'Manual Handling', 'Errors'],
    datasets: [{
      data: [
        stats.completed || 0,
        stats.no_answer || 0,
        stats.manual || 0,
        stats.error || 0
      ],
      backgroundColor: [
        chartColors.success,
        chartColors.warning,
        chartColors.info,
        chartColors.danger
      ],
      hoverBackgroundColor: [
        chartColors.success,
        chartColors.warning,
        chartColors.info,
        chartColors.danger
      ],
    }]
  };
  
  return createChart('doughnut', ctx, data);
}

/**
 * Create weekly activity chart (bar)
 * @param {HTMLElement} ctx - Canvas context
 * @param {Array} data - Weekly call data
 * @returns {Chart} Chart instance
 */
function createWeeklyCallsChart(ctx, data) {
  const chartData = {
    labels: data.labels,
    datasets: [{
      label: 'Calls',
      data: data.values,
      backgroundColor: chartColors.primaryLight,
      borderColor: chartColors.primary,
      borderWidth: 2,
      borderRadius: 5,
    }]
  };
  
  return createChart('bar', ctx, chartData);
}

/**
 * Create success rate chart (line)
 * @param {HTMLElement} ctx - Canvas context
 * @param {Array} data - Success rate data
 * @returns {Chart} Chart instance
 */
function createSuccessRateChart(ctx, data) {
  const chartData = {
    labels: data.labels,
    datasets: [{
      label: 'Success Rate (%)',
      data: data.values,
      backgroundColor: chartColors.successLight,
      borderColor: chartColors.success,
      fill: true,
      borderWidth: 2,
    }]
  };
  
  return createChart('line', ctx, chartData);
}

/**
 * Create comparison chart (grouped bar)
 * @param {HTMLElement} ctx - Canvas context
 * @param {Object} data - Comparison data
 * @returns {Chart} Chart instance
 */
function createComparisonChart(ctx, data) {
  const chartData = {
    labels: data.labels,
    datasets: [
      {
        label: 'Voice Calls',
        data: data.callValues,
        backgroundColor: chartColors.primary,
        borderRadius: 5,
      },
      {
        label: 'SMS Messages',
        data: data.smsValues,
        backgroundColor: chartColors.info,
        borderRadius: 5,
      }
    ]
  };
  
  return createChart('bar', ctx, chartData, {
    plugins: {
      legend: {
        display: true,
        position: 'top',
        labels: {
          font: {
            family: "'Inter', 'Segoe UI', 'Roboto', Arial, sans-serif",
            size: 12,
          },
          padding: 20,
          usePointStyle: true,
          pointStyle: 'circle',
        }
      }
    },
  });
}

/**
 * Create real-time activity chart
 * @param {HTMLElement} ctx - Canvas context
 * @param {Array} initialData - Initial data points
 * @returns {Chart} Chart instance
 */
function createRealtimeChart(ctx, initialData = []) {
  // Create labels for the last 10 minutes
  const labels = [];
  for (let i = 9; i >= 0; i--) {
    const date = new Date();
    date.setMinutes(date.getMinutes() - i);
    labels.push(date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
  }
  
  // Create dataset with initial data
  const data = initialData.length === 10 ? initialData : Array(10).fill(0);
  
  const chartData = {
    labels: labels,
    datasets: [{
      label: 'Activity',
      data: data,
      backgroundColor: chartColors.infoLight,
      borderColor: chartColors.info,
      borderWidth: 2,
      fill: true,
      pointRadius: 3,
    }]
  };
  
  const chart = createChart('line', ctx, chartData);
  
  // Return the chart with an update function to add new data points
  chart.updateRealtime = function(newValue) {
    // Remove the first data point and add the new one
    this.data.datasets[0].data.shift();
    this.data.datasets[0].data.push(newValue);
    
    // Update the labels (time)
    const now = new Date();
    this.data.labels.shift();
    this.data.labels.push(now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }));
    
    this.update();
  };
  
  return chart;
}

/**
 * Get a random value for demo purposes
 * @param {number} min - Minimum value
 * @param {number} max - Maximum value
 * @returns {number} Random value
 */
function getRandomValue(min, max) {
  return Math.floor(Math.random() * (max - min + 1) + min);
}

/**
 * Update chart with mock data for demo purposes
 * @param {Chart} chart - Chart instance
 * @param {string} type - Chart type
 */
function updateChartWithMockData(chart, type) {
  if (type === 'realtime') {
    // Update every 3 seconds with random data
    setInterval(() => {
      chart.updateRealtime(getRandomValue(0, 25));
    }, 3000);
  }
}

/**
 * Format number with thousands separator
 * @param {number} num - Number to format
 * @returns {string} Formatted number
 */
function formatNumber(num) {
  return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1 ');
}

/**
 * Calculate percentage
 * @param {number} part - Part value
 * @param {number} total - Total value
 * @returns {string} Formatted percentage
 */
function calculatePercentage(part, total) {
  if (total === 0) return '0%';
  return Math.round((part / total) * 100) + '%';
}

// Export utility functions
window.GDialCharts = {
  colors: chartColors,
  createCallStatsChart,
  createWeeklyCallsChart,
  createSuccessRateChart,
  createComparisonChart,
  createRealtimeChart,
  updateChartWithMockData,
  formatNumber,
  calculatePercentage
};