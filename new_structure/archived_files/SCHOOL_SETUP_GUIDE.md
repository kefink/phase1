# 🏫 School Setup System - Complete Guide

## Overview

The Hillview MVP School Management System includes a comprehensive **School Setup System** that enables plug-and-play deployment for multiple schools. This system allows each school to configure their unique details, branding, and settings while maintaining a consistent codebase.

## ✨ Key Features

### 🎯 Plug-and-Play Deployment
- **Multi-school support**: One codebase, multiple school configurations
- **Dynamic updates**: School data updates across entire system automatically
- **Clean separation**: School-specific data separate from application logic

### 🔧 Configurable Elements
- **School Information**: Name, motto, vision, mission, contact details
- **Location Data**: Address, county, sub-county, ward, constituency
- **Registration Info**: Ministry codes, registration numbers, official details
- **Academic Settings**: Terms, grading system, assessment parameters
- **Branding**: Logo, colors, fonts, visual identity
- **Features**: Enable/disable system modules and capabilities

### 📊 Progress Tracking
- **Multi-step wizard**: Guided setup process with 6 distinct steps
- **Progress indicators**: Visual progress bars and completion status
- **Step validation**: Ensures proper configuration before proceeding

## 🗂️ System Architecture

### Database Tables

#### 1. `school_setup` (Main Configuration)
```sql
- school_name, school_motto, school_vision, school_mission
- school_address, postal_address, school_phone, school_email
- registration_number, ministry_code, county, sub_county
- current_academic_year, current_term, education_system
- grading_system, uses_streams, setup_completed
```

#### 2. `school_branding` (Visual Identity)
```sql
- logo_filename, primary_color, secondary_color, accent_color
- header_image, background_image, watermark_image
- primary_font, secondary_font, report_styles
```

#### 3. `school_customization` (Feature Configuration)
```sql
- enable_analytics, enable_parent_portal, enable_sms_notifications
- custom_student_fields, custom_teacher_fields
- ministry_integration, auto_backup_enabled
```

### Key Components

#### Models (`models/school_setup.py`)
- **SchoolSetup**: Main school configuration model
- **SchoolBranding**: Visual identity and branding settings
- **SchoolCustomization**: Feature toggles and customizations

#### Services (`services/school_config_service.py`)
- **EnhancedSchoolSetupService**: Advanced setup management
- **SchoolConfigService**: Basic configuration retrieval
- **Dynamic data access**: Real-time school information

#### Views (`views/school_setup.py`)
- **Multi-step wizard**: Guided setup process
- **Form handling**: Data validation and processing
- **Progress tracking**: Step completion monitoring

## 🚀 Getting Started

### 1. Initial Setup Check

Run the test script to verify functionality:
```bash
cd new_structure
python test_school_setup.py
```

### 2. Start the Application

```bash
cd new_structure
python run.py
```

### 3. Access School Setup

1. **Login as Headteacher**
   - Navigate to: `http://localhost:5000`
   - Use headteacher credentials

2. **Access Setup Wizard**
   - Visit: `http://localhost:5000/school-setup`
   - Or click "School Setup" in admin dashboard

### 4. Complete Setup Steps

#### Step 1: Basic Information
- School name, motto, vision, mission
- Contact details (phone, email, website)
- Physical and postal addresses

#### Step 2: Registration Information
- Registration number and ministry codes
- Location details (county, sub-county, ward)
- School type and category

#### Step 3: Academic Configuration
- Current academic year and term
- Number of terms per year
- Grading system (CBC, 8-4-4, etc.)
- Grade levels and stream usage

#### Step 4: Branding
- Upload school logo
- Set primary, secondary, and accent colors
- Configure visual elements

#### Step 5: Features
- Enable/disable system modules
- Configure notifications
- Set up integrations

#### Step 6: Review & Complete
- Review all configurations
- Complete setup process
- Activate system

## 🎨 Customization Options

### Visual Branding
- **Logo Upload**: Support for PNG, JPG, SVG formats
- **Color Scheme**: Primary, secondary, and accent colors
- **Typography**: Font selection for headers and body text
- **Report Styling**: Custom headers and footers

### Academic Configuration
- **Flexible Terms**: 2-4 terms per academic year
- **Grading Systems**: CBC, 8-4-4, custom scales
- **Assessment Types**: Configurable assessment categories
- **Grade Levels**: From PP1 to Grade 8/Form 4

### Feature Toggles
- **Analytics Dashboard**: Enable/disable analytics
- **Parent Portal**: Optional parent access
- **SMS Notifications**: Bulk messaging capability
- **Email Integration**: Automated communications
- **Ministry Integration**: Government reporting

## 🔄 Dynamic Updates

### System-Wide Integration
Once configured, school data automatically appears in:
- **All page headers**: School name and logo
- **Reports**: Letterheads and footers
- **Analytics**: School-specific branding
- **Communications**: Email signatures and SMS headers
- **User Interfaces**: Color schemes and styling

### Real-Time Updates
- Changes reflect immediately across all pages
- No application restart required
- Cached data automatically refreshes

## 🛠️ Technical Implementation

### Service Layer Integration
```python
# Get school information anywhere in the application
from services.school_config_service import SchoolConfigService

school_name = SchoolConfigService.get_school_name()
logo_path = SchoolConfigService.get_school_logo_path()
school_info = SchoolConfigService.get_school_info_dict()
```

### Template Integration
```html
<!-- School data available in all templates -->
<h1>{{ school_info.school_name }}</h1>
<img src="{{ school_info.logo_path }}" alt="School Logo">
<p style="color: {{ school_info.primary_color }}">Welcome</p>
```

### Database Access
```python
# Direct model access
from models.school_setup import SchoolSetup

setup = SchoolSetup.get_current_setup()
is_completed = setup.setup_completed
progress = setup.get_setup_progress()
```

## 🔐 Security & Permissions

### Access Control
- **Headteacher Only**: Full setup access and modification rights
- **Admin Users**: Read-only access to school information
- **Teachers**: No direct access to setup configuration

### Data Validation
- **Required Fields**: Essential information validation
- **Format Checking**: Email, phone, URL validation
- **File Upload**: Secure logo and image handling
- **SQL Injection**: Parameterized queries throughout

## 📱 Multi-School Deployment

### Deployment Strategy
1. **Single Codebase**: One application serves multiple schools
2. **Database Separation**: Each school has isolated data
3. **Configuration Management**: School-specific settings
4. **Branding Isolation**: Unique visual identity per school

### Scaling Considerations
- **Database Optimization**: Indexed school_id fields
- **Caching Strategy**: School-specific cache keys
- **File Management**: Organized logo and asset storage
- **Performance**: Optimized queries for multi-tenant access

## 🎯 Next Steps

After completing school setup:

1. **Staff Management**: Add teachers and administrative staff
2. **Student Enrollment**: Import or add student records
3. **Class Organization**: Set up grades, streams, and subjects
4. **Assessment Configuration**: Define assessment types and schedules
5. **Report Templates**: Customize report formats
6. **Analytics Setup**: Configure performance tracking
7. **Parent Portal**: Enable parent access if desired

## 🆘 Troubleshooting

### Common Issues

**Setup Not Accessible**
- Verify headteacher login credentials
- Check database connectivity
- Ensure school_setup table exists

**Progress Not Saving**
- Check form validation errors
- Verify database write permissions
- Review server logs for errors

**Branding Not Updating**
- Clear browser cache
- Check file upload permissions
- Verify image file formats

**Database Errors**
- Run database migration scripts
- Check table structure integrity
- Verify foreign key constraints

### Support Resources
- Check application logs in `logs/` directory
- Run diagnostic scripts in `test_school_setup.py`
- Review database structure with provided tools
- Contact system administrator for deployment issues

---

**🎉 Congratulations!** Your school setup system is now ready for plug-and-play deployment across multiple schools while maintaining a clean, organized codebase.
