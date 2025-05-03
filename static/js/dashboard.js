/**
 * GDial Dashboard JS
 * Modern dashboard interface with real-time updates and visualizations
 */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize charts when page loads
  initializeDashboard();
  
  // Add event listeners
  setupEventListeners();
  
  // Start periodic data refresh
  setupDataRefreshers();
});

/**
 * Initialize the dashboard with charts and data
 */
function initializeDashboard() {
  // Load initial data
  fetchDashboardData()
    .then(data => {
      // Update statistics
      updateStatCards(data.stats);
      
      // Initialize charts
      initializeCharts(data);
      
      // Update activity feed
      updateActivityFeed(data.recentCalls);
      
      // Update call logs table
      updateCallLogsTable(data.recentCalls);
    })
    .catch(error => {
      console.error('Error loading dashboard data:', error);
      showErrorNotification('Failed to load dashboard data');
    });
}

/**
 * Setup event listeners for dashboard interactions
 */
function setupEventListeners() {
  // Time range selectors
  document.querySelectorAll('.time-range-selector').forEach(selector => {
    selector.addEventListener('click', function(e) {
      e.preventDefault();
      
      // Remove active class from all selectors
      document.querySelectorAll('.time-range-selector').forEach(el => {
        el.classList.remove('active');
      });
      
      // Add active class to clicked selector
      this.classList.add('active');
      
      // Get the selected time range
      const timeRange = this.dataset.range;
      
      // Refresh data with selected time range
      refreshDashboardData(timeRange);
    });
  });
  
  // Refresh button
  const refreshBtn = document.getElementById('refreshDashboard');
  if (refreshBtn) {
    refreshBtn.addEventListener('click', function() {
      const activeTimeRange = document.querySelector('.time-range-selector.active');
      const timeRange = activeTimeRange ? activeTimeRange.dataset.range : 'today';
      
      refreshDashboardData(timeRange);
    });
  }
  
  // Chart type toggles
  document.querySelectorAll('.chart-type-toggle').forEach(toggle => {
    toggle.addEventListener('click', function() {
      const chartId = this.dataset.chartId;
      const chartType = this.dataset.chartType;
      
      // Toggle active class
      document.querySelectorAll(`.chart-type-toggle[data-chart-id="${chartId}"]`).forEach(el => {
        el.classList.remove('active');
      });
      this.classList.add('active');
      
      // Update chart type
      updateChartType(chartId, chartType);
    });
  });
}

/**
 * Setup periodic data refreshers
 */
function setupDataRefreshers() {
  // Refresh real-time chart every 5 seconds
  if (window.realtimeChart) {
    setInterval(() => {
      // For demo purposes, generate random values
      // In production, fetch actual real-time data
      const newValue = Math.floor(Math.random() * 20);
      window.realtimeChart.updateRealtime(newValue);
    }, 5000);
  }
  
  // Refresh all dashboard data every 30 seconds
  setInterval(() => {
    const activeTimeRange = document.querySelector('.time-range-selector.active');
    const timeRange = activeTimeRange ? activeTimeRange.dataset.range : 'today';
    
    refreshDashboardData(timeRange, true);
  }, 30000);
}

/**
 * Initialize all charts
 * @param {Object} data - Dashboard data
 */
function initializeCharts(data) {
  // Call Stats Chart (Doughnut)
  const callStatsCtx = document.getElementById('callStatsChart');
  if (callStatsCtx) {
    window.callStatsChart = GDialCharts.createCallStatsChart(callStatsCtx, data.stats);
  }
  
  // Weekly Calls Chart (Bar)
  const weeklyCallsCtx = document.getElementById('weeklyCallsChart');
  if (weeklyCallsCtx) {
    window.weeklyCallsChart = GDialCharts.createWeeklyCallsChart(weeklyCallsCtx, data.weeklyActivity);
  }
  
  // Success Rate Chart (Line)
  const successRateCtx = document.getElementById('successRateChart');
  if (successRateCtx) {
    window.successRateChart = GDialCharts.createSuccessRateChart(successRateCtx, data.successRate);
  }
  
  // Call vs SMS Comparison Chart (Grouped Bar)
  const comparisonCtx = document.getElementById('comparisonChart');
  if (comparisonCtx) {
    window.comparisonChart = GDialCharts.createComparisonChart(comparisonCtx, data.comparison);
  }
  
  // Real-time Activity Chart (Line)
  const realtimeCtx = document.getElementById('realtimeChart');
  if (realtimeCtx) {
    window.realtimeChart = GDialCharts.createRealtimeChart(realtimeCtx);
    GDialCharts.updateChartWithMockData(window.realtimeChart, 'realtime');
  }
}

/**
 * Update stat cards with latest data
 * @param {Object} stats - Latest statistics
 */
function updateStatCards(stats) {
  // Total Calls
  const totalCallsEl = document.getElementById('totalCallsValue');
  if (totalCallsEl) {
    totalCallsEl.textContent = GDialCharts.formatNumber(stats.total_calls || 0);
    
    // Update trend if available
    const trendEl = document.getElementById('totalCallsTrend');
    if (trendEl && stats.trends) {
      updateTrendIndicator(trendEl, stats.trends.total_calls || 0);
    }
  }
  
  // Completed Calls
  const completedCallsEl = document.getElementById('completedCallsValue');
  if (completedCallsEl) {
    completedCallsEl.textContent = GDialCharts.formatNumber(stats.completed || 0);
    
    // Calculate percentage
    const percentEl = document.getElementById('completedCallsPercent');
    if (percentEl) {
      const percent = GDialCharts.calculatePercentage(stats.completed || 0, stats.total_calls || 0);
      percentEl.textContent = percent;
    }
    
    // Update trend
    const trendEl = document.getElementById('completedCallsTrend');
    if (trendEl && stats.trends) {
      updateTrendIndicator(trendEl, stats.trends.completed || 0);
    }
  }
  
  // No Answer Calls
  const noAnswerCallsEl = document.getElementById('noAnswerCallsValue');
  if (noAnswerCallsEl) {
    noAnswerCallsEl.textContent = GDialCharts.formatNumber(stats.no_answer || 0);
    
    // Calculate percentage
    const percentEl = document.getElementById('noAnswerCallsPercent');
    if (percentEl) {
      const percent = GDialCharts.calculatePercentage(stats.no_answer || 0, stats.total_calls || 0);
      percentEl.textContent = percent;
    }
  }
  
  // Failed Calls
  const errorCallsEl = document.getElementById('errorCallsValue');
  if (errorCallsEl) {
    errorCallsEl.textContent = GDialCharts.formatNumber(stats.error || 0);
    
    // Calculate percentage
    const percentEl = document.getElementById('errorCallsPercent');
    if (percentEl) {
      const percent = GDialCharts.calculatePercentage(stats.error || 0, stats.total_calls || 0);
      percentEl.textContent = percent;
    }
  }
  
  // Last Activity
  const lastActivityEl = document.getElementById('lastActivityValue');
  if (lastActivityEl && stats.last_call) {
    lastActivityEl.textContent = formatDateTime(new Date(stats.last_call));
  }
}

/**
 * Update trend indicator with value
 * @param {HTMLElement} element - Trend element
 * @param {number} value - Trend value
 */
function updateTrendIndicator(element, value) {
  // Reset classes
  element.classList.remove('trend-up', 'trend-down');
  
  // Clear content
  element.innerHTML = '';
  
  if (value > 0) {
    // Positive trend
    element.classList.add('trend-up');
    element.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 19V5M5 12l7-7 7 7"/>
      </svg>
      ${value}% from previous period
    `;
  } else if (value < 0) {
    // Negative trend
    element.classList.add('trend-down');
    element.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M12 5v14M5 12l7 7 7-7"/>
      </svg>
      ${Math.abs(value)}% from previous period
    `;
  } else {
    // No change
    element.innerHTML = `No change from previous period`;
  }
}

/**
 * Update activity feed with recent calls
 * @param {Array} recentCalls - Recent calls data
 */
function updateActivityFeed(recentCalls) {
  const activityFeedEl = document.getElementById('activityFeed');
  if (!activityFeedEl || !recentCalls || recentCalls.length === 0) return;
  
  // Clear current content
  activityFeedEl.innerHTML = '';
  
  // Add activity items
  recentCalls.slice(0, 5).forEach(call => {
    const activityItem = document.createElement('div');
    activityItem.className = 'activity-item';
    
    // Determine icon based on status
    let iconSvg = '';
    let iconBgClass = '';
    
    switch (call.status) {
      case 'completed':
        iconSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>';
        iconBgClass = 'bg-success-light';
        break;
      case 'no-answer':
        iconSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="8" y1="12" x2="16" y2="12"></line></svg>';
        iconBgClass = 'bg-warning-light';
        break;
      case 'error':
        iconSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';
        iconBgClass = 'bg-danger-light';
        break;
      default:
        iconSvg = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15.05 5A5 5 0 0 1 19 8.95M15.05 1A9 9 0 0 1 23 8.94m-1 7.98v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>';
        iconBgClass = 'bg-info-light';
    }
    
    activityItem.innerHTML = `
      <div class="activity-icon ${iconBgClass}">
        ${iconSvg}
      </div>
      <div class="activity-content">
        <h4 class="activity-title">${call.contact_name || 'Unknown Contact'}</h4>
        <div class="activity-time">${formatDateTime(new Date(call.started_at))}</div>
        <div class="activity-details">
          <span class="status-badge status-${call.status}">${call.status}</span>
          ${call.phone_number ? `· ${call.phone_number}` : ''}
          ${call.digits ? `· DTMF: ${call.digits}` : ''}
        </div>
      </div>
    `;
    
    activityFeedEl.appendChild(activityItem);
  });
}

/**
 * Update call logs table with recent data
 * @param {Array} recentCalls - Recent calls data
 */
function updateCallLogsTable(recentCalls) {
  const tableBody = document.querySelector('#callLogsTable tbody');
  if (!tableBody || !recentCalls) return;
  
  // Clear current content
  tableBody.innerHTML = '';
  
  // Add table rows
  recentCalls.forEach(call => {
    const row = document.createElement('tr');
    
    row.innerHTML = `
      <td>${formatDateTime(new Date(call.started_at))}</td>
      <td>${call.contact_name || 'Unknown'}</td>
      <td>${call.phone_number || ''}</td>
      <td>${call.message ? call.message.name : ''}</td>
      <td><span class="status-badge status-${call.status}">${call.status}</span></td>
      <td>${call.digits || '-'}</td>
    `;
    
    tableBody.appendChild(row);
  });
}

/**
 * Update chart type (e.g., from bar to line)
 * @param {string} chartId - Chart container ID
 * @param {string} chartType - New chart type
 */
function updateChartType(chartId, chartType) {
  // Implementation depends on specific chart library
  // This is a placeholder for chart type switching functionality
  console.log(`Switching chart ${chartId} to type ${chartType}`);
}

/**
 * Refresh all dashboard data
 * @param {string} timeRange - Time range for data
 * @param {boolean} silent - Whether to show loading indicators
 */
function refreshDashboardData(timeRange = 'today', silent = false) {
  if (!silent) {
    // Show loading indicators
    document.querySelectorAll('.loading-indicator').forEach(el => {
      el.style.display = 'block';
    });
  }
  
  // Fetch updated data
  fetchDashboardData(timeRange)
    .then(data => {
      // Update statistics
      updateStatCards(data.stats);
      
      // Update charts
      updateCharts(data);
      
      // Update activity feed
      updateActivityFeed(data.recentCalls);
      
      // Update call logs table
      updateCallLogsTable(data.recentCalls);
      
      if (!silent) {
        // Hide loading indicators
        document.querySelectorAll('.loading-indicator').forEach(el => {
          el.style.display = 'none';
        });
        
        // Show success message
        showSuccessNotification('Dashboard data refreshed');
      }
    })
    .catch(error => {
      console.error('Error refreshing dashboard data:', error);
      
      if (!silent) {
        // Hide loading indicators
        document.querySelectorAll('.loading-indicator').forEach(el => {
          el.style.display = 'none';
        });
        
        // Show error message
        showErrorNotification('Failed to refresh dashboard data');
      }
    });
}

/**
 * Update all charts with new data
 * @param {Object} data - Dashboard data
 */
function updateCharts(data) {
  // Update Call Stats Chart
  if (window.callStatsChart && data.stats) {
    window.callStatsChart.data.datasets[0].data = [
      data.stats.completed || 0,
      data.stats.no_answer || 0,
      data.stats.manual || 0,
      data.stats.error || 0
    ];
    window.callStatsChart.update();
  }
  
  // Update Weekly Calls Chart
  if (window.weeklyCallsChart && data.weeklyActivity) {
    window.weeklyCallsChart.data.labels = data.weeklyActivity.labels;
    window.weeklyCallsChart.data.datasets[0].data = data.weeklyActivity.values;
    window.weeklyCallsChart.update();
  }
  
  // Update Success Rate Chart
  if (window.successRateChart && data.successRate) {
    window.successRateChart.data.labels = data.successRate.labels;
    window.successRateChart.data.datasets[0].data = data.successRate.values;
    window.successRateChart.update();
  }
  
  // Update Comparison Chart
  if (window.comparisonChart && data.comparison) {
    window.comparisonChart.data.labels = data.comparison.labels;
    window.comparisonChart.data.datasets[0].data = data.comparison.callValues;
    window.comparisonChart.data.datasets[1].data = data.comparison.smsValues;
    window.comparisonChart.update();
  }
}

/**
 * Fetch dashboard data from API
 * @param {string} timeRange - Time range for data
 * @returns {Promise} Promise with dashboard data
 */
async function fetchDashboardData(timeRange = 'today') {
  // For demo purposes, create mock data
  // In production, replace this with actual API call
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(generateMockDashboardData(timeRange));
    }, 500);
  });
  
  // Example of actual API call:
  // return fetch(`/api/dashboard?timeRange=${timeRange}`)
  //   .then(response => response.json());
}

/**
 * Generate mock dashboard data for demo
 * @param {string} timeRange - Time range for data
 * @returns {Object} Mock dashboard data
 */
function generateMockDashboardData(timeRange) {
  // Generate different data based on time range
  let multiplier = 1;
  
  switch (timeRange) {
    case 'week':
      multiplier = 7;
      break;
    case 'month':
      multiplier = 30;
      break;
    case 'year':
      multiplier = 365;
      break;
    default: // today
      multiplier = 1;
  }
  
  // Call statistics
  const completedCalls = Math.floor(45 * multiplier * (0.9 + Math.random() * 0.2));
  const noAnswerCalls = Math.floor(15 * multiplier * (0.9 + Math.random() * 0.2));
  const manualCalls = Math.floor(5 * multiplier * (0.9 + Math.random() * 0.2));
  const errorCalls = Math.floor(3 * multiplier * (0.9 + Math.random() * 0.2));
  const totalCalls = completedCalls + noAnswerCalls + manualCalls + errorCalls;
  
  // Generate weekly activity data
  const weeklyActivity = {
    labels: ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
    values: [
      Math.floor(Math.random() * 50 + 20),
      Math.floor(Math.random() * 50 + 30),
      Math.floor(Math.random() * 50 + 40),
      Math.floor(Math.random() * 50 + 25),
      Math.floor(Math.random() * 50 + 35),
      Math.floor(Math.random() * 30 + 10),
      Math.floor(Math.random() * 20 + 5)
    ]
  };
  
  // Generate success rate data
  const successRate = {
    labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
    values: [
      Math.floor(Math.random() * 15 + 65),
      Math.floor(Math.random() * 15 + 70),
      Math.floor(Math.random() * 15 + 75),
      Math.floor(Math.random() * 15 + 75)
    ]
  };
  
  // Generate comparison data
  const comparison = {
    labels: ['January', 'February', 'March', 'April', 'May', 'June'],
    callValues: [
      Math.floor(Math.random() * 100 + 200),
      Math.floor(Math.random() * 100 + 250),
      Math.floor(Math.random() * 100 + 300),
      Math.floor(Math.random() * 100 + 350),
      Math.floor(Math.random() * 100 + 400),
      Math.floor(Math.random() * 100 + 450)
    ],
    smsValues: [
      Math.floor(Math.random() * 50 + 100),
      Math.floor(Math.random() * 50 + 120),
      Math.floor(Math.random() * 50 + 140),
      Math.floor(Math.random() * 50 + 160),
      Math.floor(Math.random() * 50 + 180),
      Math.floor(Math.random() * 50 + 200)
    ]
  };
  
  // Generate recent calls
  const statuses = ['completed', 'no-answer', 'manual', 'error'];
  const recentCalls = [];
  
  for (let i = 0; i < 10; i++) {
    const date = new Date();
    date.setMinutes(date.getMinutes() - i * 30);
    
    recentCalls.push({
      id: `call-${i}`,
      contact_name: `Contact ${i + 1}`,
      phone_number: `+46 70 123 ${1000 + i}`,
      started_at: date.toISOString(),
      status: statuses[Math.floor(Math.random() * statuses.length)],
      digits: Math.random() > 0.7 ? `${Math.floor(Math.random() * 9) + 1}` : null,
      message: {
        name: `Emergency Message ${i % 3 + 1}`
      }
    });
  }
  
  return {
    stats: {
      total_calls: totalCalls,
      completed: completedCalls,
      no_answer: noAnswerCalls,
      manual: manualCalls,
      error: errorCalls,
      last_call: new Date().toISOString(),
      trends: {
        total_calls: Math.floor(Math.random() * 20 - 10),
        completed: Math.floor(Math.random() * 20)
      }
    },
    weeklyActivity,
    successRate,
    comparison,
    recentCalls
  };
}

/**
 * Format date and time for display
 * @param {Date} date - Date to format
 * @returns {string} Formatted date and time
 */
function formatDateTime(date) {
  if (!date) return '-';
  
  // Format options
  const options = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  };
  
  return date.toLocaleDateString(undefined, options);
}

/**
 * Show success notification
 * @param {string} message - Success message
 */
function showSuccessNotification(message) {
  const notification = document.createElement('div');
  notification.className = 'notification notification-success';
  notification.innerHTML = `
    <div class="notification-icon">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
        <polyline points="22 4 12 14.01 9 11.01"></polyline>
      </svg>
    </div>
    <div class="notification-message">${message}</div>
  `;
  
  document.body.appendChild(notification);
  
  // Animate in
  setTimeout(() => {
    notification.classList.add('show');
  }, 10);
  
  // Remove after 3 seconds
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 3000);
}

/**
 * Show error notification
 * @param {string} message - Error message
 */
function showErrorNotification(message) {
  const notification = document.createElement('div');
  notification.className = 'notification notification-error';
  notification.innerHTML = `
    <div class="notification-icon">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="12" y1="8" x2="12" y2="12"></line>
        <line x1="12" y1="16" x2="12.01" y2="16"></line>
      </svg>
    </div>
    <div class="notification-message">${message}</div>
  `;
  
  document.body.appendChild(notification);
  
  // Animate in
  setTimeout(() => {
    notification.classList.add('show');
  }, 10);
  
  // Remove after 5 seconds
  setTimeout(() => {
    notification.classList.remove('show');
    setTimeout(() => {
      notification.remove();
    }, 300);
  }, 5000);
}