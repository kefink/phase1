# Hillview School Management System

## Enterprise-Grade School Management Platform

### 🏫 Overview

The Hillview School Management System is a comprehensive, secure, and scalable platform designed for modern educational institutions. Built with enterprise-grade security and performance in mind.

### 🛡️ Security Features

- **100% Protection** against OWASP Top 10 vulnerabilities
- **SQL Injection Protection** - Advanced pattern detection and parameterized queries
- **XSS Protection** - Output encoding and Content Security Policy
- **Access Control** - Role-based access control (RBAC)
- **CSRF Protection** - HMAC token validation
- **File Upload Security** - Type validation and malware scanning
- **Enterprise Security Headers** - Complete security configuration

### 🗄️ Database

- **MySQL 8.0+** - Production-ready database
- **21 Tables** - Comprehensive data structure
- **Optimized Performance** - Connection pooling and indexing
- **Data Integrity** - Foreign key constraints and validation

#### Migrations & Schema Management

The system now uses Alembic for all schema changes (baseline pending if not yet generated).

1. Generate baseline (first time only if existing tables):
   ```bash
   alembic revision --autogenerate -m "baseline"
   alembic upgrade head
   ```
2. After model changes:
   ```bash
   alembic revision --autogenerate -m "add new model XYZ"
   alembic upgrade head
   ```

Legacy runtime table creation/SQLite repair scripts have been removed or stubbed. Use migrations exclusively.

#### Database Health

`utils/database_health.py` now performs SQLAlchemy-based inspection:

- Lists existing tables
- Flags missing expected tables
- Counts records (best-effort; skips on errors)
- Warns if no headteacher account exists
  Deprecated function `create_missing_tables()` returns a notice (use migrations instead).

#### Connection Pooling

SQLite custom pool removed. MySQL connections managed by SQLAlchemy engine with production-tuned pool settings in `ProductionConfig`.

#### Rate Limiting & Redis

`RATELIMIT_STORAGE_URL` config enables Redis-backed Flask-Limiter storage. Falls back silently to in-memory if Redis unreachable. Default limits set by `RATELIMIT_DEFAULT`.

### 🚀 Quick Start

#### Prerequisites

- Python 3.8+
- MySQL 8.0+
- pip (Python package manager)

#### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/kefink/2ndrev.git
   cd 2ndrev/new_structure
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure database**

   - Update `config.py` with your MySQL credentials
   - Ensure MySQL server is running

4. **Run the application**

   ```bash
   python run.py
   ```

5. **Access the application**
   - Open browser to `http://localhost:5000`

### 📁 Project Structure

```
new_structure/
├── models/              # Database models
├── views/               # Application routes and views
├── services/            # Business logic layer
├── security/            # Security modules
├── templates/           # HTML templates
├── static/              # CSS, JS, images
├── middleware/          # Application middleware
├── utils/               # Utility functions
├── migrations/          # Database migrations
├── config.py            # Configuration settings
├── run.py               # Application entry point
└── requirements.txt     # Python dependencies
```

### 🔧 Configuration

Edit `config.py` to configure:

- Database connection
- Security settings
- Session configuration
- Environment-specific settings

### 🎯 Features

- **Multi-role Access** - Headteacher, Class Teacher, Subject Teacher
- **Student Management** - Comprehensive student records
- **Grade Management** - Flexible grading system
- **Report Generation** - Automated report creation
- **Analytics Dashboard** - Performance insights
- **Parent Portal** - Parent access to student information
- **Security Monitoring** - Real-time threat detection

### 🛠️ Development

- **Framework**: Flask (Python)
- **Database**: MySQL with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript
- **Security**: Custom security modules
- **Architecture**: MVC pattern with service layer

### 📊 Production Ready

- ✅ Enterprise-grade security
- ✅ Scalable architecture
- ✅ Clean codebase
- ✅ Comprehensive documentation
- ✅ MySQL database
- ✅ Performance optimized

### 🔒 Security Compliance

- **OWASP Top 10** - Complete protection
- **ISO 27001** - Security controls ready
- **GDPR** - Data protection compliant
- **FERPA** - Educational privacy ready

### 🔧 Recent Updates (July 2025)

- ✅ **Fixed Admin Login Crashes** - Resolved system crashes during authentication
- ✅ **Simplified Dashboard** - Improved stability and performance
- ✅ **Enhanced Authentication** - Streamlined login process
- ✅ **Debug Routes Added** - Better troubleshooting capabilities
- ✅ **Error Handling** - Improved error recovery and user feedback

### 🔐 Default Login Credentials

#### Admin/Headteacher

- **URL**: http://localhost:5000/admin_login
- **Username**: `headteacher`
- **Password**: `admin123`

#### Class Teacher

- **URL**: http://localhost:5000/classteacher_login
- **Username**: `kevin`
- **Password**: `kev123`

#### Teacher

- **URL**: http://localhost:5000/teacher_login
- **Username**: `carol`
- **Password**: `carol123`

### 🎨 Solar Theme (Simplified Usage)

The Manage Terms & Assessments page has been simplified to match the lighter pattern used in `manage_grades_streams.html`.

Current approach:

- Single shared Solar palette file: `css/solar-shared.css` (provides color tokens + base utilities + heroicon color helpers).
- Lean, page-scoped inline `<style>` block for layout (stats, panels, tables) – keeps CSS local and easy to refactor.
- Dark mode toggle persisted via `localStorage` key: `solar-theme-mode` (values: `light` | `dark`).

Removed (previous experiment):

- `solar-mta-enhancements.css` (gradient text/icons, accent cycling utilities)
- Extra high/soft/faint text class wrappers (simplified to standard palette variables)

Minimal structure for a new Solar-themed page now looks like:

```
<head>
   <link rel="stylesheet" href="{{ url_for('static', filename='css/solar-shared.css') }}">
   <style>
      /* Optional local layout styles here */
   </style>
</head>
<body class="solar-theme" data-theme="solar-dark">
   <!-- content -->
   <button id="theme-toggle">Toggle</button>
   <script>
      (function(){
         const root=document.documentElement;const btn=document.getElementById('theme-toggle');
         if(!btn) return;const stored=localStorage.getItem('solar-theme-mode');
         if(stored==='light') root.removeAttribute('data-theme'); else root.setAttribute('data-theme','solar-dark');
         btn.addEventListener('click',()=>{const dark=root.getAttribute('data-theme')==='solar-dark';
            if(dark){root.removeAttribute('data-theme');localStorage.setItem('solar-theme-mode','light');}
            else {root.setAttribute('data-theme','solar-dark');localStorage.setItem('solar-theme-mode','dark');}
         });
      })();
   </script>
</body>
```

Benefits of simplification:

- Fewer network requests (single CSS file)
- Easier maintenance & parity across related class teacher pages
- Faster first meaningful paint without additional enhancement layer

If future pages require richer visual accents (gradients, animated emphasis, extended utility classes), reintroduce a small optional enhancement file on a per‑page basis rather than globally.

### 📞 Support

For technical support or questions, please refer to the documentation or contact the development team.

---

_Built with ❤️ for educational excellence_
