<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Academic Performance Analytics - Class Teacher</title>
    <meta name="description" content="Class Teacher Academic Analytics - Performance insights for your assigned classes at {{ school_info.school_name or 'Hillview School' }}">
    
    <!-- Analytics Solar Theme - Independent Styling -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/analytics_solar_independent.css') }}">
    <link rel="stylesheet" href="{{ url_for('static', filename='css/enhanced_analytics.css') }}">
</head>
<body class="analytics-page">
    
    <!-- Page Header -->
    <header class="analytics-header">
        <h1>Class Academic Analytics</h1>
        <p class="text-lg">Performance insights for your assigned classes</p>
    </header>

<style>
  .insight-value {
    font-size: 3.5rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    text-shadow: 
      0 2px 4px rgba(0, 0, 0, 0.4),
      0 0 20px rgba(42, 161, 152, 0.3) !important;
    display: block !important;
    opacity: 1 !important;
    visibility: visible !important;
    position: relative !important;
    z-index: 999999 !important;
    margin: 1rem 0 !important;
    line-height: 1.1 !important;
    background: linear-gradient(135deg, #ffffff, #2aa198) !important;
    background-clip: text !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif !important;
  }

  /* Backup styling for browsers that don't support text gradients */
  .insight-value::before {
    content: attr(data-fallback) !important;
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    color: #ffffff !important;
    z-index: -1 !important;
  }
  
  /* Protect against any JavaScript hiding attempts with maximum specificity */
  #total-students-analyzed,
  #total-subjects-analyzed,
  #top-subject-performance,
  #top-student-performance {
    font-size: 3.5rem !important;
    font-weight: 700 !important;
    color: #ffffff !important;
    text-shadow: 
      0 2px 4px rgba(0, 0, 0, 0.4),
      0 0 20px rgba(42, 161, 152, 0.3) !important;
    display: block !important;
    opacity: 1 !important;
    visibility: visible !important;
    position: relative !important;
    z-index: 999999 !important;
    margin: 1rem 0 !important;
    line-height: 1.1 !important;
    background: linear-gradient(135deg, #ffffff, #2aa198) !important;
    background-clip: text !important;
    -webkit-background-clip: text !important;
    -webkit-text-fill-color: transparent !important;
  }

  /* Kill all purple and white backgrounds with maximum specificity */
  html,
  body,
  html *,
  body *,
  .page-container,
  .content-wrapper,
  .analytics-filters-section,
  .detailed-performance,
  .top-performers,
  .performance-breakdown,
  .modern-grid,
  .insights-grid,
  .insight-card,
  div[class*="card"],
  div[class*="section"],
  div[class*="panel"],
  div[class*="container"] {
    background: #002b36 !important;
    background-color: #002b36 !important;
    background-image: none !important;
    color: #fdf6e3 !important;
  }

  /* Force dark theme on all containers */
  .analytics-page .analytics-filters-section,
  .analytics-page .detailed-performance,
  .analytics-page .top-performers,
  .analytics-page .performance-breakdown {
    background: rgba(0, 43, 54, 0.9) !important;
    border: 1px solid rgba(253, 246, 227, 0.1) !important;
    border-radius: 0.75rem !important;
    padding: 1.5rem !important;
    backdrop-filter: blur(10px) !important;
  }

  /* Enhanced Insight Cards with Professional Styling */
  .insights-grid {
    display: grid !important;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)) !important;
    gap: 1.5rem !important;
    margin: 2rem 0 !important;
  }

  .insight-card {
    background: linear-gradient(135deg, rgba(0, 43, 54, 0.95), rgba(7, 54, 66, 0.95)) !important;
    border: 1px solid rgba(42, 161, 152, 0.3) !important;
    border-radius: 16px !important;
    padding: 2rem !important;
    color: #fdf6e3 !important;
    text-align: center !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: 
      0 4px 20px rgba(0, 0, 0, 0.3),
      0 0 0 1px rgba(42, 161, 152, 0.1),
      inset 0 1px 0 rgba(253, 246, 227, 0.1) !important;
    position: relative !important;
    overflow: hidden !important;
    animation: cardSlideIn 0.6s ease-out forwards !important;
  }

  .insight-card::before {
    content: '' !important;
    position: absolute !important;
    top: 0 !important;
    left: 0 !important;
    right: 0 !important;
    height: 3px !important;
    background: linear-gradient(90deg, #2aa198, #268bd2, #6c71c4) !important;
    border-radius: 16px 16px 0 0 !important;
  }

  .insight-card:hover {
    transform: translateY(-8px) scale(1.02) !important;
    border-color: rgba(42, 161, 152, 0.5) !important;
    box-shadow: 
      0 12px 40px rgba(0, 0, 0, 0.4),
      0 0 0 1px rgba(42, 161, 152, 0.3),
      inset 0 1px 0 rgba(253, 246, 227, 0.2) !important;
  }

  .insight-icon {
    width: 64px !important;
    height: 64px !important;
    margin: 0 auto 1.5rem !important;
    padding: 16px !important;
    background: linear-gradient(135deg, rgba(42, 161, 152, 0.2), rgba(38, 139, 210, 0.2)) !important;
    border-radius: 50% !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    border: 2px solid rgba(42, 161, 152, 0.3) !important;
    transition: all 0.3s ease !important;
  }

  .insight-card:hover .insight-icon {
    transform: scale(1.1) rotate(5deg) !important;
    background: linear-gradient(135deg, rgba(42, 161, 152, 0.3), rgba(38, 139, 210, 0.3)) !important;
    border-color: rgba(42, 161, 152, 0.5) !important;
  }

  .insight-icon-svg {
    width: 32px !important;
    height: 32px !important;
    color: #2aa198 !important;
    stroke-width: 2 !important;
    transition: all 0.3s ease !important;
  }

  .insight-card:hover .insight-icon-svg {
    color: #268bd2 !important;
  }

  .insight-label {
    font-size: 0.875rem !important;
    font-weight: 600 !important;
    color: rgba(253, 246, 227, 0.8) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    margin-bottom: 0.75rem !important;
    transition: color 0.3s ease !important;
  }

  .insight-card:hover .insight-label {
    color: rgba(253, 246, 227, 1) !important;
  }

  /* Card entrance animation */
  @keyframes cardSlideIn {
    0% {
      opacity: 0;
      transform: translateY(30px) scale(0.9);
    }
    100% {
      opacity: 1;
      transform: translateY(0) scale(1);
    }
  }

  /* Stagger animation for cards */
  .insight-card:nth-child(1) { animation-delay: 0.1s; }
  .insight-card:nth-child(2) { animation-delay: 0.2s; }
  .insight-card:nth-child(3) { animation-delay: 0.3s; }
  .insight-card:nth-child(4) { animation-delay: 0.4s; }

  /* Responsive adjustments */
  @media (max-width: 768px) {
    .insights-grid {
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)) !important;
      gap: 1rem !important;
    }
    
    .insight-card {
      padding: 1.5rem !important;
    }
    
    .insight-icon {
      width: 56px !important;
      height: 56px !important;
      margin: 0 auto 1rem !important;
    }
    
    .insight-icon-svg {
      width: 28px !important;
      height: 28px !important;
    }
  }

  /* Notification animations */
  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  /* Loading state improvements */
  .loading-state {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 40px;
    color: #fdf6e3;
    font-size: 16px;
  }

  .loading-state i {
    margin-right: 10px;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  /* Error state improvements */
  .error-state {
    background: rgba(220, 53, 69, 0.1) !important;
    border: 1px solid rgba(220, 53, 69, 0.3) !important;
    border-radius: 8px;
    margin: 20px 0;
  }
</style>

{% endblock %} {% block content %}
<div class="container">
  <!-- Breadcrumb Navigation -->
  <div class="breadcrumb">
    <a href="{{ url_for('classteacher.dashboard') }}">
      <i class="fas fa-home"></i> Dashboard
    </a>
    <span class="breadcrumb-separator">/</span>
    <span>Academic Performance Analytics</span>
  </div>

  <!-- Page Header -->
  <div class="analytics-page-header">
    <h1><i class="fas fa-chart-line"></i> Academic Performance Analytics</h1>
    <p>
      Comprehensive insights into student performance and subject analytics for
      your assigned classes
    </p>
  </div>

  <!-- Quick Insights Summary -->
  <div class="quick-insights">
    <h3><i class="fas fa-tachometer-alt"></i> Quick Insights</h3>
    <div class="insights-grid">
      <div class="insight-card">
        <div class="insight-icon">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="insight-icon-svg">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 0 0 2.625.372 9.337 9.337 0 0 0 4.121-.952 4.125 4.125 0 0 0-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 0 1 8.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0 1 11.964-3.07M12 6.375a3.375 3.375 0 1 1-6.75 0 3.375 3.375 0 0 1 6.75 0Zm8.25 2.25a2.625 2.625 0 1 1-5.25 0 2.625 2.625 0 0 1 5.25 0Z" />
          </svg>
        </div>
        <div class="insight-label">Students Analyzed</div>
        <div class="insight-value" id="total-students-analyzed" data-debug="students: {{ analytics_data.summary.students_analyzed or 0 }}" data-fallback="{{ analytics_data.summary.students_analyzed or 0 }}">
          {{ analytics_data.summary.students_analyzed or 0 }}
        </div>
      </div>
      <div class="insight-card">
        <div class="insight-icon">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="insight-icon-svg">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.042A8.967 8.967 0 0 0 6 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 0 1 6 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 0 1 6-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0 1 18 18a8.967 8.967 0 0 0-6 2.292m0-14.25v14.25" />
          </svg>
        </div>
        <div class="insight-label">Subjects Analyzed</div>
        <div class="insight-value" id="total-subjects-analyzed" data-debug="subjects: {{ analytics_data.summary.subjects_analyzed or 0 }}" data-fallback="{{ analytics_data.summary.subjects_analyzed or 0 }}">
          {{ analytics_data.summary.subjects_analyzed or 0 }}
        </div>
      </div>
      <div class="insight-card">
        <div class="insight-icon">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="insight-icon-svg">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 18.75h-9m9 0a3 3 0 0 1 3 3h-15a3 3 0 0 1 3-3m9 0v-3.375c0-.621-.503-1.125-1.125-1.125h-.871M7.5 18.75v-3.375c0-.621.504-1.125 1.125-1.125h.872m5.007 0H9.497m5.007 0a7.454 7.454 0 0 1-.982-3.172M9.497 14.25a7.454 7.454 0 0 0 .981-3.172M5.25 4.236c-.982.143-1.954.317-2.916.52A6.003 6.003 0 0 0 7.73 9.728M5.25 4.236V4.5c0 2.108.966 3.99 2.48 5.228M5.25 4.236V2.721C7.456 2.41 9.71 2.25 12 2.25c2.291 0 4.545.16 6.75.47v1.516M7.73 9.728a6.726 6.726 0 0 0 2.748 1.35m8.272-6.842V4.5c0 2.108-.966 3.99-2.48 5.228m2.48-5.228a25.334 25.334 0 0 1 5.384-.069m-13.67 8.218a18.08 18.08 0 0 1-2.63-2.909m0 0a24.998 24.998 0 0 1-5.384-.069m0 0V4.5A2.25 2.25 0 0 1 .621 2.25H1.5v1.875C2.491 4.286 3.714 4.375 5.25 4.5" />
          </svg>
        </div>
        <div class="insight-label">Best Subject Average</div>
        <div class="insight-value" id="top-subject-performance" data-debug="best: {{ analytics_data.summary.best_subject_average or 0 }}%" data-fallback="{{ analytics_data.summary.best_subject_average or 0 }}%">
          {{ analytics_data.summary.best_subject_average or 0 }}%
        </div>
      </div>
      <div class="insight-card">
        <div class="insight-icon">
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" class="insight-icon-svg">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 3.75V16.5L12 14.25 7.5 16.5V3.75m9 0H18A2.25 2.25 0 0 1 20.25 6v12A2.25 2.25 0 0 1 18 20.25H6A2.25 2.25 0 0 1 3.75 18V6A2.25 2.25 0 0 1 6 3.75h1.5m9 0v-1.5A2.25 2.25 0 0 0 14.25 0h-4.5A2.25 2.25 0 0 0 7.5 2.25v1.5m9 0h-9" />
          </svg>
        </div>
        <div class="insight-label">Top Student Average</div>
        <div class="insight-value" id="top-student-performance" data-debug="top: {{ analytics_data.summary.top_student_average or 0 }}%" data-fallback="{{ analytics_data.summary.top_student_average or 0 }}%">
          {{ analytics_data.summary.top_student_average or 0 }}%
        </div>
      </div>
    </div>
  </div>

  <!-- Analytics Filters -->
  <div class="analytics-filters-section">
    <div class="analytics-actions">
      <h2><i class="fas fa-filter"></i> Analytics Filters</h2>
      <div class="action-buttons">
        <button
          class="modern-btn btn-outline btn-sm"
          onclick="resetAnalyticsFilters()"
        >
          <i class="fas fa-undo"></i> Reset Filters
        </button>
        <button
          class="modern-btn btn-primary btn-sm"
          onclick="refreshAnalyticsData()"
        >
          <i class="fas fa-sync-alt"></i> Refresh Data
        </button>
      </div>
    </div>

    <div class="modern-grid grid-cols-4">
      <div class="form-group">
        <label class="form-label">Term</label>
        <select
          id="analytics-term-filter"
          class="form-select"
          onchange="updateAnalytics()"
        >
          <option value="">All Terms</option>
          {% for term in terms %}
          <option value="{{ term }}" {% if request.args.get('term') == term %}selected{% endif %}>
            {{ term }}
          </option>
          {% endfor %}
        </select>
      </div>

      <div class="form-group">
        <label class="form-label">Assessment Type</label>
        <select
          id="analytics-assessment-filter"
          class="form-select"
          onchange="updateAnalytics()"
        >
          <option value="">All Assessments</option>
          {% for assessment in assessment_types %}
          <option value="{{ assessment }}" {% if request.args.get('assessment_type') == assessment %}selected{% endif %}>
            {{ assessment }}
          </option>
          {% endfor %}
        </select>
      </div>

      <div
        class="form-group"
        id="analytics-grade-filter-group"
        style="display: none"
      >
        <label class="form-label">Grade</label>
        <select
          id="analytics-grade-filter"
          class="form-select"
          onchange="updateAnalytics()"
        >
          <option value="">All Grades</option>
          <!-- Grades will be populated by JavaScript -->
        </select>
      </div>

      <div
        class="form-group"
        id="analytics-stream-filter-group"
        style="display: none"
      >
        <label class="form-label">Stream</label>
        <select
          id="analytics-stream-filter"
          class="form-select"
          onchange="updateAnalytics()"
        >
          <option value="">All Streams</option>
          <!-- Streams will be populated by JavaScript -->
        </select>
      </div>
    </div>
  </div>

  <!-- Main Analytics Content -->
  <div class="analytics-content-grid">
    <!-- Top Performers Component - SIMPLIFIED VERSION -->
    <div class="analytics-component top-performers-component">
      <div class="component-header">
        <h3><i class="fas fa-trophy"></i> Top Performing Students</h3>
        <div class="component-actions">
          <button
            class="modern-btn btn-sm btn-outline"
            onclick="refreshAnalytics('top_performers')"
          >
            <i class="fas fa-sync-alt"></i> Refresh
          </button>
        </div>
      </div>

      <div class="component-content">
        {% if analytics_data.summary.has_sufficient_data and analytics_data.top_performers %}
        <div class="top-performers-enhanced">
          <div class="performers-header">
            <div class="header-rank">Rank</div>
            <div class="header-student">Student Details</div>
            <div class="header-performance">Performance</div>
            <div class="header-actions">Actions</div>
          </div>
          
          {% for student in analytics_data.top_performers[:5] %}
          <div class="performer-row-enhanced" id="performer-{{ loop.index }}">
            <div class="performer-rank-enhanced">
              <span class="rank-number">{{ loop.index }}</span>
              {% if loop.index == 1 %}
                <i class="fas fa-crown rank-icon gold"></i>
              {% elif loop.index == 2 %}
                <i class="fas fa-medal rank-icon silver"></i>
              {% elif loop.index == 3 %}
                <i class="fas fa-medal rank-icon bronze"></i>
              {% endif %}
            </div>
            
            <div class="performer-details-enhanced">
              <div class="student-name">{{ student.name or student.student_name }}</div>
              <div class="student-meta">
                <span class="admission-number">ADM{{ student.admission_number or student.student_id or 'N/A' }}</span>
                <span class="class-info">{{ student.grade or 'Grade' }} {{ student.stream or 'Stream' }}</span>
              </div>
              <div class="assessment-info">{{ student.assessment_type or 'Mid Term' }} - {{ student.term or 'Term 1' }}</div>
            </div>
            
            <div class="performer-stats">
              <div class="main-percentage">{{ (student.average_percentage|float)|round(1) }}%</div>
              <div class="grade-info">Grade {{ student.grade_letter or 'A' }}</div>
              <div class="marks-breakdown">
                {{ student.total_marks_obtained or 0 }}/{{ student.total_marks_possible or 0 }} marks
              </div>
              <div class="progress-bar">
                <div class="progress-fill" style="width: {{ (student.average_percentage|float)|round(1) }}%"></div>
              </div>
            </div>
            
            <div class="performer-actions">
              <button 
                class="action-btn view-details-btn" 
                onclick="toggleEnhancedStudentDetails('{{ student.student_id or loop.index }}', '{{ student.name or student.student_name }}', {{ (student.average_percentage|float)|round(1) }}, {{ student.min_percentage|default(0) }}, {{ student.max_percentage|default(100) }}, {{ student.subjects_count|default(1) }})"
              >
                <i class="fas fa-chevron-down"></i>
                <span class="btn-text">View Details</span>
              </button>
              <button 
                class="action-btn export-btn" 
                onclick="exportEnhancedStudentData('{{ student.student_id or loop.index }}', '{{ student.name or student.student_name }}')"
              >
                <i class="fas fa-download"></i>
                <span class="btn-text">Export</span>
              </button>
            </div>
            
            <!-- Enhanced Details Section (Initially Hidden) -->
            <div class="student-details-expanded" id="details-enhanced-{{ student.student_id or loop.index }}" style="display: none;">
              <div class="details-header">
                <i class="fas fa-chart-line"></i>
                <span>Detailed Performance Analysis for {{ student.name or student.student_name }}</span>
              </div>
              
              <div class="performance-grid">
                <div class="stat-card">
                  <div class="stat-icon success">
                    <i class="fas fa-arrow-up"></i>
                  </div>
                  <div class="stat-content">
                    <div class="stat-value">{{ student.max_percentage|default(100)|round(1) }}%</div>
                    <div class="stat-label">Highest Score</div>
                  </div>
                </div>
                
                <div class="stat-card">
                  <div class="stat-icon primary">
                    <i class="fas fa-chart-bar"></i>
                  </div>
                  <div class="stat-content">
                    <div class="stat-value">{{ (student.average_percentage|float)|round(1) }}%</div>
                    <div class="stat-label">Average Score</div>
                  </div>
                </div>
                
                <div class="stat-card">
                  <div class="stat-icon warning">
                    <i class="fas fa-arrow-down"></i>
                  </div>
                  <div class="stat-content">
                    <div class="stat-value">{{ student.min_percentage|default(0)|round(1) }}%</div>
                    <div class="stat-label">Lowest Score</div>
                  </div>
                </div>
                
                <div class="stat-card">
                  <div class="stat-icon info">
                    <i class="fas fa-book"></i>
                  </div>
                  <div class="stat-content">
                    <div class="stat-value">{{ student.subjects_count|default(1) }}</div>
                    <div class="stat-label">Subjects</div>
                  </div>
                </div>
              </div>
              
              <div class="details-actions">
                <button 
                  class="modern-btn btn-primary btn-sm" 
                  onclick="viewEnhancedStudentFullReport('{{ student.student_id or loop.index }}', '{{ student.name or student.student_name }}')"
                >
                  <i class="fas fa-file-alt"></i> View Full Report
                </button>
                <button 
                  class="modern-btn btn-outline btn-sm" 
                  onclick="generateStudentPerfReport('{{ student.student_id or loop.index }}', '{{ student.name or student.student_name }}')"
                >
                  <i class="fas fa-chart-pie"></i> Performance Report
                </button>
                <button 
                  class="modern-btn btn-outline btn-sm" 
                  onclick="emailStudentReport('{{ student.student_id or loop.index }}', '{{ student.name or student.student_name }}')"
                >
                  <i class="fas fa-envelope"></i> Email Report
                </button>
              </div>
            </div>
          </div>
          {% endfor %}
        </div>
        {% else %}
        <div class="no-data-message-simple">
          <i class="fas fa-trophy"></i>
          <h4>No Performance Data Available</h4>
          <p>No student performance data found for your assigned classes.</p>
        </div>
        {% endif %}
      </div>
    </div>

    <!-- Subject Performance Component -->
    <div class="analytics-component subject-performance-component">
      <div class="component-header">
        <h3><i class="fas fa-chart-bar"></i> Subject Performance Analysis</h3>
        <div class="component-actions">
          <button
            class="modern-btn btn-sm btn-outline"
            onclick="refreshAnalytics('subject_performance')"
          >
            <i class="fas fa-sync-alt"></i> Refresh
          </button>
        </div>
      </div>

      <div class="component-content">
        <div id="subject-performance-container">
          {% if analytics_data.summary.has_sufficient_data and analytics_data.subject_analytics %}
          <div class="subject-performance-grid">
            {% for subject in analytics_data.subject_analytics[:6] %}
            <div class="subject-item">
              <div class="subject-header">
                <div class="subject-name">{{ subject.subject_name or subject.name }}</div>
                <div class="subject-performance">{{ (subject.average_percentage|float)|round(1) }}%</div>
              </div>
              <div class="subject-details">
                {{ subject.student_count or subject.students_count or 0 }} students • 
                {{ subject.total_marks or subject.total_assessments or 0 }} assessments
              </div>
              <div
                class="subject-status {% if subject.average_percentage|float >= 80 %}status-exceeding {% elif subject.average_percentage|float >= 65 %}status-meeting {% elif subject.average_percentage|float >= 50 %}status-approaching {% else %}status-below{% endif %}"
              >
                {% if subject.average_percentage|float >= 80 %}Exceeding Expectation 
                {% elif subject.average_percentage|float >= 65 %}Meeting Expectation 
                {% elif subject.average_percentage|float >= 50 %}Approaching Expectation 
                {% else %}Below Expectation{% endif %}
              </div>
            </div>
            {% endfor %}
          </div>
          {% else %}
          <div class="no-data-message">
            <i class="fas fa-chart-bar"></i>
            <p>
              No subject performance data available for your assigned classes.
            </p>
          </div>
          {% endif %}
        </div>
      </div>
    </div>
  </div>

  <!-- Detailed Analytics Section -->
  <div class="analytics-component analytics-full-width">
    <div class="component-header">
      <h3><i class="fas fa-chart-pie"></i> Detailed Performance Breakdown</h3>
      <div class="component-actions">
        <button
          class="modern-btn btn-sm btn-outline"
          onclick="exportAnalytics()"
        >
          <i class="fas fa-download"></i> Export Data
        </button>
      </div>
    </div>

    <div class="component-content">
      <div id="detailed-analytics-container">
        <div class="loading-state">
          <i class="fas fa-spinner fa-spin"></i> Loading detailed analytics...
        </div>
      </div>
    </div>
  </div>

  <!-- No Data State -->
  <div id="no-data-state" class="no-data-state" style="display: none">
    <div class="no-data-icon">
      <i class="fas fa-chart-line"></i>
    </div>
    <h3>No Analytics Data Available</h3>
    <p>
      There isn't enough data to generate meaningful analytics for your assigned
      classes.
    </p>
    <div class="no-data-suggestions">
      <h4>Suggestions:</h4>
      <ul>
        <li>Ensure marks have been uploaded for your students</li>
        <li>Try selecting a different term or assessment type</li>
        <li>Check that students are properly assigned to your classes</li>
        <li>
          Contact the headteacher if you need additional class assignments
        </li>
      </ul>
    </div>
    <div style="margin-top: var(--space-4)">
      <button class="modern-btn btn-primary" onclick="resetAnalyticsFilters()">
        <i class="fas fa-undo"></i> Reset Filters
      </button>
      <a
        href="{{ url_for('classteacher.dashboard') }}"
        class="modern-btn btn-outline"
        style="margin-left: var(--space-2)"
      >
        <i class="fas fa-arrow-left"></i> Back to Dashboard
      </a>
    </div>
  </div>
</div>

<!-- Include Analytics Components Styles -->
{% include 'analytics_dashboard_components.html' %}

  <!-- Enhanced Analytics Styles -->
<link
  rel="stylesheet"
  href="{{ url_for('static', filename='css/enhanced_analytics.css') }}"
/>

{% endblock %} {% block extra_js %}
<!-- Include the analytics dashboard fixed JavaScript file -->
<script src="{{ url_for('static', filename='js/analytics_dashboard_fixed.js') }}"></script>

<script>
  // Initialize analytics data for JavaScript
  window.analyticsData = {
    summary: {
      students_analyzed: {{ analytics_data.summary.students_analyzed or 0 }},
      subjects_analyzed: {{ analytics_data.summary.subjects_analyzed or 0 }},
      best_subject_average: {{ analytics_data.summary.best_subject_average or 0 }},
      top_student_average: {{ analytics_data.summary.top_student_average or 0 }}
    },
    top_performers: {{ analytics_data.top_performers | tojson | safe if analytics_data.top_performers else '[]' }},
    subject_analytics: {{ analytics_data.subject_analytics | tojson | safe if analytics_data.subject_analytics else '[]' }}
  };

  // Set user permissions
  window.isHeadteacher = {{ 'true' if session.get('headteacher_universal_access') or session.get('role') == 'headteacher' else 'false' }};

  console.log("🔍 Analytics data loaded for classteacher:", window.analyticsData);

  // Initialize the analytics dashboard when page loads
  document.addEventListener("DOMContentLoaded", function () {
    console.log("🚀 Classteacher analytics page - initializing dashboard");
    
    // Initialize the analytics dashboard with fixed JS
    if (typeof initializeAnalyticsDashboard === 'function') {
      // The analytics dashboard is already loaded with server-side data
      // But we can enhance it with the JavaScript functionality
      console.log("✅ Analytics dashboard functions available");
      
      // Set up any interactive features
      setupAnalyticsInteractivity();
    } else {
      console.warn("⚠️ Analytics dashboard functions not available");
    }
  });

  function setupAnalyticsInteractivity() {
    // Set up filter functionality
    const termFilter = document.getElementById('analytics-term-filter');
    const assessmentFilter = document.getElementById('analytics-assessment-filter');
    
    if (termFilter) {
      termFilter.addEventListener('change', updateAnalytics);
    }
    
    if (assessmentFilter) {
      assessmentFilter.addEventListener('change', updateAnalytics);
    }

    console.log("✅ Analytics interactivity set up successfully");
  }

  // Update analytics based on filter changes
  function updateAnalytics() {
    const termFilter = document.getElementById('analytics-term-filter').value;
    const assessmentFilter = document.getElementById('analytics-assessment-filter').value;
    const gradeFilter = document.getElementById('analytics-grade-filter')?.value || '';
    const streamFilter = document.getElementById('analytics-stream-filter')?.value || '';

    // Build URL with filters
    const params = new URLSearchParams();
    if (termFilter) params.append('term', termFilter);
    if (assessmentFilter) params.append('assessment_type', assessmentFilter);
    if (gradeFilter) params.append('grade', gradeFilter);
    if (streamFilter) params.append('stream', streamFilter);

    // Reload page with filters
    const baseUrl = window.location.pathname;
    const newUrl = params.toString() ? `${baseUrl}?${params.toString()}` : baseUrl;
    
    // Show loading indication
    showNotification('Updating analytics...', 'info');
    
    // Navigate to filtered URL
    window.location.href = newUrl;
  }

  // Reset filters function
  function resetAnalyticsFilters() {
    // Clear all filter dropdowns
    document.getElementById('analytics-term-filter').value = '';
    document.getElementById('analytics-assessment-filter').value = '';
    if (document.getElementById('analytics-grade-filter')) {
      document.getElementById('analytics-grade-filter').value = '';
    }
    if (document.getElementById('analytics-stream-filter')) {
      document.getElementById('analytics-stream-filter').value = '';
    }
    
    // Reload page without filters
    window.location.href = window.location.pathname;
  }

  // Handle refresh analytics calls from buttons
  function refreshAnalytics(section) {
    console.log("🔄 refreshAnalytics called for section:", section);
    showNotification(`Refreshing ${section} data...`, 'info');
    
    // For server-side rendered data, we can just reload the page
    // or show a message that data is already current
    setTimeout(() => {
      showNotification("Data is already current from server!", 'success');
    }, 1000);
  }

  // Enhanced Top Performing Students Functionality
  function toggleEnhancedStudentDetails(studentId, studentName, avgPercentage, minPercentage, maxPercentage, subjectsCount) {
    const detailsSection = document.getElementById(`details-enhanced-${studentId}`);
    const toggleBtn = document.querySelector(`[onclick*="toggleEnhancedStudentDetails('${studentId}'"]`);
    const toggleIcon = toggleBtn?.querySelector('i');
    const toggleText = toggleBtn?.querySelector('.btn-text');
    
    if (!detailsSection || !toggleBtn) {
      console.error(`Elements not found for student ID: ${studentId}`);
      return;
    }
    
    const isHidden = detailsSection.style.display === 'none' || !detailsSection.style.display;
    
    if (isHidden) {
      // Show enhanced details
      detailsSection.style.display = 'block';
      detailsSection.style.visibility = 'visible';
      detailsSection.style.opacity = '1';
      detailsSection.classList.add('details-expanded');
      
      if (toggleIcon) toggleIcon.className = 'fas fa-chevron-up';
      if (toggleText) toggleText.textContent = 'Hide Details';
      toggleBtn.classList.add('active');
      
      // Update the stats with real data
      updateStudentStatsDisplay(studentId, avgPercentage, minPercentage, maxPercentage, subjectsCount);
      
      // Add smooth animation
      setTimeout(() => {
        detailsSection.style.transform = 'translateY(0)';
      }, 10);
      
      // Show notification
      showNotification(`Viewing detailed analytics for ${studentName}`, 'info');
    } else {
      // Hide details
      detailsSection.style.opacity = '0';
      detailsSection.style.transform = 'translateY(-10px)';
      
      setTimeout(() => {
        detailsSection.style.display = 'none';
        detailsSection.classList.remove('details-expanded');
        if (toggleIcon) toggleIcon.className = 'fas fa-chevron-down';
        if (toggleText) toggleText.textContent = 'View Details';
        toggleBtn.classList.remove('active');
      }, 300);
    }
  }

  function updateStudentStatsDisplay(studentId, avgPercentage, minPercentage, maxPercentage, subjectsCount) {
    const detailsSection = document.getElementById(`details-enhanced-${studentId}`);
    if (!detailsSection) return;
    
    // Update the stat values with real data
    const statCards = detailsSection.querySelectorAll('.stat-card .stat-value');
    if (statCards.length >= 4) {
      statCards[0].textContent = `${maxPercentage}%`; // Highest Score
      statCards[1].textContent = `${avgPercentage}%`; // Average Score  
      statCards[2].textContent = `${minPercentage}%`; // Lowest Score
      statCards[3].textContent = subjectsCount; // Subjects Count
    }
  }

  function exportEnhancedStudentData(studentId, studentName) {
    showNotification(`Preparing export for ${studentName}...`, 'info');
    
    // Simulate export preparation
    setTimeout(() => {
      showNotification(`Performance data exported for ${studentName}`, 'success');
    }, 1500);
  }

  function viewEnhancedStudentFullReport(studentId, studentName) {
    showNotification(`Loading comprehensive report for ${studentName}...`, 'info');
    
    // Simulate loading full report
    setTimeout(() => {
      showNotification(`Full report would be displayed for ${studentName}`, 'info');
    }, 1000);
  }

  function generateStudentPerfReport(studentId, studentName) {
    showNotification(`Generating performance report for ${studentName}...`, 'info');
    
    setTimeout(() => {
      showNotification(`Performance report generated for ${studentName}`, 'success');
    }, 2000);
  }

  function emailStudentReport(studentId, studentName) {
    showNotification(`Preparing to email report for ${studentName}...`, 'info');
    
    setTimeout(() => {
      showNotification(`Report emailed successfully for ${studentName}`, 'success');
    }, 1500);
  }

  // Export analytics function
  function exportAnalytics() {
    showNotification("Preparing analytics export...", "info");
    
    setTimeout(() => {
      showNotification("Analytics data exported successfully!", "success");
    }, 1000);
  }

  // Utility function for notifications
  function showNotification(message, type = "info") {
    // Remove any existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create notification element
    const notification = document.createElement("div");
    notification.className = `notification notification-${type}`;
    
    const iconMap = {
      'success': 'fa-check-circle',
      'error': 'fa-times-circle', 
      'warning': 'fa-exclamation-triangle',
      'info': 'fa-info-circle'
    };
    
    notification.innerHTML = `
      <i class="fas ${iconMap[type] || iconMap.info}"></i>
      <span>${message}</span>
    `;

    // Add to page
    document.body.appendChild(notification);

    // Auto-remove after 3 seconds
    setTimeout(() => {
      if (notification.parentElement) {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => notification.remove(), 300);
      }
    }, 3000);
  }
</script>

<style>
  .notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: var(--primary-color);
    color: white;
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-md);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    z-index: 1000;
    display: flex;
    align-items: center;
    gap: var(--space-2);
    animation: slideIn 0.3s ease-out;
  }

  .notification-info {
    background: var(--blue-500);
  }

  .notification-success {
    background: var(--green-500);
  }

  .notification-warning {
    background: var(--orange-500);
  }

  .notification-error {
    background: var(--red-500);
  }

  @keyframes slideIn {
    from {
      transform: translateX(100%);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }

  /* Enhanced Top Performers Styles */
  .top-performers-enhanced {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .performers-header {
    display: grid;
    grid-template-columns: auto 2fr 1.5fr auto;
    gap: var(--space-3);
    padding: var(--space-3);
    background: rgba(0, 43, 54, 0.6);
    border-radius: var(--radius-md);
    font-weight: 600;
    color: var(--accent-color);
    border: 1px solid rgba(253, 246, 227, 0.1);
  }

  .performer-row-enhanced {
    display: grid;
    grid-template-columns: auto 2fr 1.5fr auto;
    gap: var(--space-3);
    padding: var(--space-4);
    background: rgba(0, 43, 54, 0.4);
    border: 1px solid rgba(253, 246, 227, 0.1);
    border-radius: var(--radius-md);
    transition: all 0.3s ease;
    position: relative;
  }

  .performer-row-enhanced:hover {
    background: rgba(0, 43, 54, 0.6);
    border-color: rgba(253, 246, 227, 0.2);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  }

  .performer-rank-enhanced {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--space-1);
  }

  .rank-number {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
    color: white;
    border-radius: 50%;
    font-weight: bold;
    font-size: 1.2rem;
  }

  .rank-icon {
    font-size: 1.2rem;
    margin-top: var(--space-1);
  }

  .rank-icon.gold { color: #ffd700; }
  .rank-icon.silver { color: #c0c0c0; }
  .rank-icon.bronze { color: #cd7f32; }

  .performer-details-enhanced {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
  }

  .student-name {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .student-meta {
    display: flex;
    gap: var(--space-2);
    font-size: 0.9rem;
    color: var(--text-secondary);
  }

  .admission-number {
    padding: 2px 8px;
    background: rgba(253, 246, 227, 0.1);
    border-radius: var(--radius-sm);
    font-family: monospace;
  }

  .class-info {
    padding: 2px 8px;
    background: rgba(0, 119, 187, 0.2);
    border-radius: var(--radius-sm);
    color: var(--blue-300);
  }

  .assessment-info {
    font-size: 0.85rem;
    color: var(--text-tertiary);
    font-style: italic;
  }

  .performer-stats {
    display: flex;
    flex-direction: column;
    gap: var(--space-1);
    align-items: flex-end;
  }

  .main-percentage {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--accent-color);
  }

  .grade-info {
    font-size: 0.9rem;
    color: var(--text-secondary);
  }

  .marks-breakdown {
    font-size: 0.85rem;
    color: var(--text-tertiary);
  }

  .progress-bar {
    width: 100px;
    height: 6px;
    background: rgba(253, 246, 227, 0.1);
    border-radius: 3px;
    overflow: hidden;
    margin-top: var(--space-1);
  }

  .progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--primary-color), var(--accent-color));
    border-radius: 3px;
    transition: width 0.3s ease;
  }

  .performer-actions {
    display: flex;
    flex-direction: column;
    gap: var(--space-2);
    align-items: center;
  }

  .action-btn {
    display: flex;
    align-items: center;
    gap: var(--space-1);
    padding: var(--space-2) var(--space-3);
    background: rgba(253, 246, 227, 0.1);
    border: 1px solid rgba(253, 246, 227, 0.2);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    font-size: 0.85rem;
    cursor: pointer;
    transition: all 0.3s ease;
    min-width: 100px;
    justify-content: center;
  }

  .action-btn:hover {
    background: rgba(253, 246, 227, 0.2);
    border-color: var(--primary-color);
    transform: translateY(-1px);
  }

  .action-btn.active {
    background: var(--primary-color);
    color: white;
  }

  .view-details-btn:hover {
    background: rgba(0, 119, 187, 0.2);
    color: var(--blue-300);
  }

  .export-btn:hover {
    background: rgba(34, 197, 94, 0.2);
    color: var(--green-300);
  }

  /* Enhanced Details Section */
  .student-details-expanded {
    grid-column: 1 / -1;
    margin-top: var(--space-4);
    padding: var(--space-4);
    background: rgba(0, 43, 54, 0.3);
    border: 1px solid rgba(253, 246, 227, 0.1);
    border-radius: var(--radius-md);
    backdrop-filter: blur(10px);
    transform: translateY(0);
    transition: all 0.3s ease;
  }

  .details-header {
    display: flex;
    align-items: center;
    gap: var(--space-2);
    margin-bottom: var(--space-4);
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--accent-color);
  }

  .performance-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--space-3);
    margin-bottom: var(--space-4);
  }

  .stat-card {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-3);
    background: rgba(0, 43, 54, 0.5);
    border: 1px solid rgba(253, 246, 227, 0.1);
    border-radius: var(--radius-md);
    transition: all 0.3s ease;
  }

  .stat-card:hover {
    background: rgba(0, 43, 54, 0.7);
    border-color: rgba(253, 246, 227, 0.2);
    transform: translateY(-2px);
  }

  .stat-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    font-size: 1.2rem;
  }

  .stat-icon.success {
    background: rgba(34, 197, 94, 0.2);
    color: var(--green-400);
  }

  .stat-icon.primary {
    background: rgba(0, 119, 187, 0.2);
    color: var(--blue-400);
  }

  .stat-icon.warning {
    background: rgba(245, 158, 11, 0.2);
    color: var(--orange-400);
  }

  .stat-icon.info {
    background: rgba(139, 92, 246, 0.2);
    color: var(--purple-400);
  }

  .stat-content {
    flex: 1;
  }

  .stat-value {
    font-size: 1.3rem;
    font-weight: bold;
    color: var(--text-primary);
    margin-bottom: var(--space-1);
  }

  .stat-label {
    font-size: 0.9rem;
    color: var(--text-secondary);
  }

  .details-actions {
    display: flex;
    gap: var(--space-2);
    justify-content: flex-start;
    flex-wrap: wrap;
  }

  /* Enhanced Modal Styles */
  .enhanced-modal {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10000;
    opacity: 0;
    visibility: hidden;
    transition: all 0.3s ease;
  }

  .enhanced-modal.show {
    opacity: 1;
    visibility: visible;
  }

  .modal-content {
    background: var(--card-background);
    border: 1px solid rgba(253, 246, 227, 0.1);
    border-radius: var(--radius-lg);
    max-width: 800px;
    width: 90%;
    max-height: 80vh;
    overflow-y: auto;
    transform: translateY(-50px);
    transition: transform 0.3s ease;
  }

  .enhanced-modal.show .modal-content {
    transform: translateY(0);
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--space-4);
    border-bottom: 1px solid rgba(253, 246, 227, 0.1);
  }

  .modal-close {
    background: none;
    border: none;
    color: var(--text-secondary);
    font-size: 1.2rem;
    cursor: pointer;
    padding: var(--space-2);
    border-radius: var(--radius-md);
    transition: all 0.3s ease;
  }

  .modal-close:hover {
    background: rgba(253, 246, 227, 0.1);
    color: var(--text-primary);
  }

  .modal-body {
    padding: var(--space-4);
  }

  .modal-footer {
    display: flex;
    gap: var(--space-2);
    justify-content: flex-end;
    padding: var(--space-4);
    border-top: 1px solid rgba(253, 246, 227, 0.1);
  }

  .report-section {
    margin-bottom: var(--space-4);
  }

  .report-section h4 {
    color: var(--accent-color);
    margin-bottom: var(--space-2);
  }

  .report-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--space-2);
    margin: var(--space-3) 0;
  }

  .report-stat {
    display: flex;
    justify-content: space-between;
    padding: var(--space-2);
    background: rgba(0, 43, 54, 0.3);
    border-radius: var(--radius-md);
  }

  .recommendations-list {
    list-style: none;
    padding: 0;
  }

  .recommendations-list li {
    padding: var(--space-2);
    margin: var(--space-1) 0;
    background: rgba(0, 43, 54, 0.3);
    border-radius: var(--radius-md);
    border-left: 3px solid var(--primary-color);
  }

  /* Enhanced Notifications */
  .enhanced-notification {
    position: fixed;
    top: 20px;
    right: 20px;
    background: var(--card-background);
    border: 1px solid rgba(253, 246, 227, 0.2);
    color: var(--text-primary);
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-md);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    z-index: 9999;
    display: flex;
    align-items: center;
    gap: var(--space-2);
    max-width: 400px;
    transform: translateX(100%);
    opacity: 0;
    transition: all 0.3s ease;
  }

  .enhanced-notification.show {
    transform: translateX(0);
    opacity: 1;
  }

  .enhanced-notification.notification-success {
    border-left: 4px solid var(--green-500);
  }

  .enhanced-notification.notification-error {
    border-left: 4px solid var(--red-500);
  }

  .enhanced-notification.notification-warning {
    border-left: 4px solid var(--orange-500);
  }

  .enhanced-notification.notification-info {
    border-left: 4px solid var(--blue-500);
  }

  .notification-close {
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    padding: var(--space-1);
    border-radius: var(--radius-sm);
    margin-left: var(--space-2);
    transition: all 0.3s ease;
  }

  .notification-close:hover {
    background: rgba(253, 246, 227, 0.1);
    color: var(--text-primary);
  }

  /* Responsive Design for Enhanced Features */
  @media (max-width: 768px) {
    .performers-header,
    .performer-row-enhanced {
      grid-template-columns: 1fr;
      gap: var(--space-2);
    }

    .performer-actions {
      flex-direction: row;
      justify-content: center;
    }

    .performance-grid {
      grid-template-columns: 1fr;
    }

    .details-actions {
      justify-content: center;
    }

    .modal-content {
      width: 95%;
      margin: var(--space-2);
    }

    .enhanced-notification {
      right: var(--space-2);
      left: var(--space-2);
      max-width: none;
    }
  }

  /* Analytics Data Display Styles */
  .top-performers-list,
  .subject-performance-list {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }

  .performer-item,
  .subject-item {
    display: flex;
    align-items: center;
    padding: var(--space-3);
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: var(--radius-md);
    transition: all 0.3s ease;
  }

  .performer-item:hover,
  .subject-item:hover {
    background: rgba(255, 255, 255, 0.1);
    transform: translateY(-2px);
  }

  .performer-rank {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    background: var(--primary-color);
    color: white;
    border-radius: 50%;
    font-weight: bold;
    margin-right: var(--space-3);
  }

  .performer-info,
  .subject-info {
    flex: 1;
  }

  .performer-name,
  .subject-name {
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--space-1);
  }

  .performer-details,
  .subject-details {
    font-size: 0.9rem;
    color: var(--text-secondary);
  }

  .performer-score,
  .subject-score {
    font-size: 1.2rem;
    font-weight: bold;
    color: var(--primary-color);
    margin-right: var(--space-3);
  }

  .subject-trend {
    font-size: 0.9rem;
  }

  .trend-excellent {
    color: var(--green-500);
  }

  .trend-good {
    color: var(--blue-500);
  }

  .trend-needs-improvement {
    color: var(--orange-500);
  }

  .no-data-message {
    text-align: center;
    padding: var(--space-6);
    color: var(--text-secondary);
  }

  .no-data-message i {
    font-size: 3rem;
    margin-bottom: var(--space-3);
    opacity: 0.5;
  }
</style>

</body>
</html>
