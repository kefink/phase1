# MySQL Migration Plan for Hillview School Management System

## 🎯 Migration Overview

This document outlines the comprehensive migration strategy from SQLite to MySQL with multi-tenant architecture for the Hillview School Management System.

## 📊 Current SQLite Schema Analysis

### Core Tables Identified:

1. **Academic Structure**

   - `grade` - Educational levels (Grade 1-9)
   - `stream` - Class divisions (A, B, etc.)
   - `term` - Academic terms
   - `assessment_type` - Exam types
   - `subject` - Subjects taught
   - `subject_component` - Subject components (for composite subjects)

2. **User Management**

   - `teacher` - Staff members with roles
   - `student` - Learners
   - `parent` - Parent portal users (newly added)

3. **Academic Operations**

   - `mark` - Student marks/grades
   - `teacher_subjects` - Teacher-subject assignments
   - `teacher_subject_assignment` - Detailed assignments
   - `parent_student` - Parent-child relationships

4. **System Configuration**

   - `school_configuration` - School settings
   - `school_setup` - School branding/setup
   - `class_teacher_permissions` - Permission system
   - `function_permissions` - Feature permissions
   - `permission_requests` - Permission workflow

5. **Parent Portal**
   - `parent_email_log` - Email tracking
   - `email_template` - Email templates

## 🏗️ Multi-Tenant Architecture Strategy

### Option 1: Schema-per-Tenant (Recommended)

- Each school gets its own database schema
- Better isolation and security
- Easier backup and maintenance per school
- Scalable for large deployments

### Option 2: Shared Schema with Tenant ID

- Single database with tenant_id columns
- More complex queries but easier management
- Better for smaller deployments

**Recommendation: Schema-per-Tenant for better isolation and scalability**

## 🔄 Migration Strategy

### Phase 1: MySQL Setup and Configuration

1. Install MySQL 8.0+ server
2. Create master database for tenant management
3. Set up connection pooling
4. Configure user permissions

### Phase 2: Schema Migration

1. Convert SQLite schema to MySQL
2. Handle data type differences
3. Add proper indexes and constraints
4. Implement foreign key relationships

### Phase 3: Data Migration

1. Export data from SQLite
2. Transform data for MySQL
3. Import with integrity checks
4. Validate data consistency

### Phase 4: Multi-Tenant Implementation

1. Create tenant management system
2. Implement dynamic database routing
3. Add tenant isolation middleware
4. Update application configuration

## 📋 Data Type Mapping

| SQLite Type | MySQL Type          | Notes                 |
| ----------- | ------------------- | --------------------- |
| INTEGER     | INT AUTO_INCREMENT  | Primary keys          |
| TEXT        | VARCHAR(255) / TEXT | Based on length       |
| REAL        | DECIMAL(10,2)       | For marks/percentages |
| BOOLEAN     | TINYINT(1)          | Boolean values        |
| TIMESTAMP   | DATETIME            | Timestamps            |
| BLOB        | LONGBLOB            | File storage          |

## 🚀 Performance Optimizations

### Indexing Strategy

- Primary keys on all tables
- Foreign key indexes
- Composite indexes for common queries
- Full-text search indexes for names

### Connection Management

- Connection pooling (10-20 connections per tenant)
- Read/write splitting for large deployments
- Query caching
- Prepared statements

## 🔒 Security Considerations

### Database Security

- Separate MySQL users per tenant
- Encrypted connections (SSL/TLS)
- Regular security updates
- Backup encryption

### Application Security

- Tenant isolation validation
- SQL injection prevention
- Input sanitization
- Audit logging

## 📦 Cloud Deployment Preparation

### Docker Configuration

- Multi-stage builds
- Environment-specific configs
- Health checks
- Volume management

### CI/CD Pipeline

- Automated testing
- Database migrations
- Zero-downtime deployments
- Rollback procedures

## 🎯 Success Metrics

### Performance Targets

- Page load time < 2 seconds
- Database query time < 100ms
- Support for 1000+ concurrent users
- 99.9% uptime

### Scalability Goals

- Support 100+ schools
- 10,000+ students per school
- Horizontal scaling capability
- Auto-scaling based on load

## 📅 Implementation Timeline

1. **Week 1**: MySQL setup and schema migration
2. **Week 2**: Data migration and validation
3. **Week 3**: Multi-tenant implementation
4. **Week 4**: Testing and optimization
5. **Week 5**: Cloud deployment preparation
6. **Week 6**: Production deployment

## 🔧 Tools and Technologies

### Migration Tools

- Custom Python migration scripts
- SQLAlchemy schema generation
- Data validation tools
- Performance testing tools

### Monitoring and Maintenance

- MySQL monitoring (Prometheus/Grafana)
- Application performance monitoring
- Log aggregation (ELK stack)
- Automated backups

## 📝 Quick Start Guide

### Prerequisites

1. MySQL 8.0+ server installed and running
2. Python 3.8+ with pip
3. Existing Hillview SQLite database

### Migration Steps

1. **Navigate to migration directory:**

   ```bash
   cd new_structure/mysql_migration
   ```

2. **Run complete migration:**

   ```bash
   python run_migration.py
   ```

3. **Follow prompts and provide MySQL root password when requested**

4. **Test the migrated system:**
   ```bash
   cd ..
   python run.py
   ```

### Manual Migration (Advanced)

If you prefer to run steps individually:

1. **MySQL Setup:**

   ```bash
   python mysql_setup.py
   ```

2. **Schema Migration:**

   ```bash
   python schema_migration.py
   ```

3. **Data Migration:**

   ```bash
   python data_migration.py
   ```

4. **Update Configuration:**

   ```bash
   python update_config.py
   ```

5. **Test Integration:**
   ```bash
   python test_mysql_integration.py
   ```

## 🔧 Troubleshooting

### Common Issues

1. **MySQL Connection Failed**

   - Ensure MySQL server is running
   - Check credentials and permissions
   - Verify network connectivity

2. **Schema Migration Errors**

   - Check MySQL user permissions
   - Ensure database exists
   - Review foreign key constraints

3. **Data Migration Issues**

   - Verify SQLite database integrity
   - Check data type compatibility
   - Review error logs for specific issues

4. **Flask Integration Problems**
   - Install required dependencies: `pip install -r requirements.txt`
   - Check configuration files
   - Verify environment variables

## 📞 Support

For issues or questions:

1. Check the troubleshooting section above
2. Review error logs and messages
3. Ensure all prerequisites are met
4. Test with a fresh MySQL installation if needed
