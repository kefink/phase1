"""
Subject Configuration API endpoints
Handles flexible subject configuration for English and Kiswahili
"""

from flask import Blueprint, request, jsonify, render_template
from ..services.flexible_subject_service import FlexibleSubjectService
from .admin import admin_required
from ..extensions import db
from sqlalchemy import text

subject_config_api = Blueprint('subject_config_api', __name__)

@subject_config_api.route('/test-buttons')
def test_buttons():
    """Test page for debugging button issues."""
    try:
        with open('test_buttons.html', 'r') as f:
            return f.read()
    except:
        return """
        <h1>Button Test</h1>
        <button onclick="alert('Test!')">Test Alert</button>
        <button onclick="fetch('/api/subject-config/all').then(r=>r.json()).then(d=>alert('API works: ' + d.configurations.length))">Test API</button>
        """

@subject_config_api.route('/debug-subject-config')
def debug_subject_config():
    """Debug route to check subject configuration and Subject model sync."""
    try:
        with db.engine.connect() as conn:
            # Check subject_configuration table
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM subject_configuration"))
                config_count = result.fetchone()[0]

                result = conn.execute(text("SELECT * FROM subject_configuration"))
                config_rows = result.fetchall()

                # Check Subject model records
                result = conn.execute(text("""
                    SELECT id, name, education_level, is_composite
                    FROM subject
                    ORDER BY name, education_level
                """))
                all_subject_rows = result.fetchall()

                result = conn.execute(text("""
                    SELECT id, name, education_level, is_composite
                    FROM subject
                    WHERE LOWER(name) LIKE '%english%' OR LOWER(name) LIKE '%kiswahili%'
                    ORDER BY name, education_level
                """))
                subject_rows = result.fetchall()

                # Check SubjectComponent records
                result = conn.execute(text("""
                    SELECT sc.id, sc.subject_id, sc.name, sc.weight, s.name as subject_name
                    FROM subject_component sc
                    JOIN subject s ON sc.subject_id = s.id
                    WHERE LOWER(s.name) LIKE '%english%' OR LOWER(s.name) LIKE '%kiswahili%'
                    ORDER BY s.name, sc.name
                """))
                component_rows = result.fetchall()

                return f"""
                <h2>Subject Configuration Debug</h2>
                <h3>Configuration Table ({config_count} records)</h3>
                <pre>{config_rows}</pre>

                <h3>All Subject Records ({len(all_subject_rows)} total)</h3>
                <pre>{all_subject_rows}</pre>

                <h3>English/Kiswahili Subject Records ({len(subject_rows)} records)</h3>
                <pre>{subject_rows}</pre>

                <h3>Subject Component Records ({len(component_rows)} records)</h3>
                <pre>{component_rows}</pre>

                <p><a href="/subject-configuration">Go to Subject Configuration</a></p>
                <p><a href="/debug-subjects-list">List All Subjects</a></p>
                """

            except Exception as e:
                return f"Database error: {e}"
    except Exception as e:
        return f"Error: {e}"

@subject_config_api.route('/debug-subjects-list')
def debug_subjects_list():
    """Debug route to list all subjects in a readable format."""
    try:
        from ..models.academic import Subject

        subjects = Subject.query.all()

        html = "<h2>All Subjects in Database</h2><table border='1' style='border-collapse: collapse;'>"
        html += "<tr style='background: #f0f0f0;'><th style='padding: 8px; border: 1px solid #ccc;'>ID</th><th style='padding: 8px; border: 1px solid #ccc;'>Name</th><th style='padding: 8px; border: 1px solid #ccc;'>Education Level</th><th style='padding: 8px; border: 1px solid #ccc;'>Is Composite</th></tr>"

        for subject in subjects:
            html += f"<tr><td style='padding: 8px; border: 1px solid #ccc;'>{subject.id}</td><td style='padding: 8px; border: 1px solid #ccc;'><strong>'{subject.name}'</strong></td><td style='padding: 8px; border: 1px solid #ccc;'>{subject.education_level}</td><td style='padding: 8px; border: 1px solid #ccc;'>{subject.is_composite}</td></tr>"

        html += "</table>"

        # Add search for English/Kiswahili subjects
        english_subjects = Subject.query.filter(Subject.name.ilike('%english%')).all()
        kiswahili_subjects = Subject.query.filter(Subject.name.ilike('%kiswahili%')).all()

        html += f"<h3>English Subjects Found: {len(english_subjects)}</h3>"
        for s in english_subjects:
            html += f"<p>- ID: {s.id}, Name: '<strong>{s.name}</strong>', Level: {s.education_level}, Composite: {s.is_composite}</p>"

        html += f"<h3>Kiswahili Subjects Found: {len(kiswahili_subjects)}</h3>"
        for s in kiswahili_subjects:
            html += f"<p>- ID: {s.id}, Name: '<strong>{s.name}</strong>', Level: {s.education_level}, Composite: {s.is_composite}</p>"

        html += "<p><a href='/subject-configuration'>Go to Subject Configuration</a></p>"
        html += "<p><a href='/create-missing-subjects'>Create Missing English/Kiswahili Subjects</a></p>"

        return html

    except Exception as e:
        return f"Error: {e}"

@subject_config_api.route('/create-missing-subjects')
def create_missing_subjects():
    """Create missing English and Kiswahili subjects for testing."""
    try:
        from ..models.academic import Subject
        from ..extensions import db

        created_subjects = []
        education_levels = ['upper_primary', 'junior_secondary']
        subjects_to_create = [
            ('ENGLISH', 'english'),
            ('KISWAHILI', 'kiswahili'),
            ('English', 'english'),
            ('Kiswahili', 'kiswahili')
        ]

        for subject_name, _ in subjects_to_create:
            for education_level in education_levels:
                # Check if subject already exists
                existing = Subject.query.filter(
                    Subject.name.ilike(subject_name),
                    Subject.education_level == education_level
                ).first()

                if not existing:
                    # Create new subject
                    new_subject = Subject(
                        name=subject_name,
                        education_level=education_level,
                        is_composite=False  # Will be updated by configuration
                    )
                    db.session.add(new_subject)
                    created_subjects.append(f"{subject_name} - {education_level}")

        if created_subjects:
            db.session.commit()
            message = f"✅ Created {len(created_subjects)} subjects: {', '.join(created_subjects)}"
        else:
            message = "ℹ️ All subjects already exist"

        html = f"<h2>Create Missing Subjects Result</h2>"
        html += f"<p>{message}</p>"
        html += "<p><a href='/debug-subjects-list'>View All Subjects</a></p>"
        html += "<p><a href='/subject-configuration'>Go to Subject Configuration</a></p>"

        return html

    except Exception as e:
        return f"Error creating subjects: {e}"

def create_subject_configuration_table():
    """Create the subject_configuration table if it doesn't exist."""
    try:
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS subject_configuration (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subject_name VARCHAR(100) NOT NULL,
            education_level VARCHAR(50) NOT NULL,
            is_composite BOOLEAN DEFAULT FALSE,
            component_1_name VARCHAR(100),
            component_1_weight DECIMAL(5,2) DEFAULT 50.00,
            component_2_name VARCHAR(100),
            component_2_weight DECIMAL(5,2) DEFAULT 50.00,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            UNIQUE KEY unique_subject_level (subject_name, education_level)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
        with db.engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
        print("✅ Subject configuration table created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating table: {e}")
        return False

def initialize_default_configurations():
    """Initialize default configurations for ONLY English and Kiswahili."""
    try:
        # Clear any existing configurations first to ensure only English and Kiswahili
        with db.engine.connect() as conn:
            conn.execute(text("DELETE FROM subject_configuration"))
            conn.commit()

        # Only English and Kiswahili configurations for Upper Primary and Junior Secondary
        default_configs = [
            # English configurations - Grammar (60%) + Composition (40%)
            ('english', 'upper_primary', True, 'Grammar', 60.0, 'Composition', 40.0),
            ('english', 'junior_secondary', True, 'Grammar', 60.0, 'Composition', 40.0),
            # Kiswahili configurations - Lugha (50%) + Insha (50%)
            ('kiswahili', 'upper_primary', True, 'Lugha', 50.0, 'Insha', 50.0),
            ('kiswahili', 'junior_secondary', True, 'Lugha', 50.0, 'Insha', 50.0)
        ]

        insert_sql = """
        INSERT INTO subject_configuration
        (subject_name, education_level, is_composite, component_1_name, component_1_weight, component_2_name, component_2_weight)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """

        with db.engine.connect() as conn:
            for config in default_configs:
                conn.execute(text(insert_sql), config)
            conn.commit()

        print(f"✅ Initialized {len(default_configs)} configurations (English & Kiswahili only)")
        return True
    except Exception as e:
        print(f"❌ Error initializing configurations: {e}")
        return False

@subject_config_api.route('/subject-configuration')
@admin_required
def subject_configuration_page():
    """Display subject configuration management page."""
    try:
        # Only Upper Primary and Junior Secondary configurations (no Lower Primary)
        configurations = [
            # Upper Primary configurations
            {
                'subject_name': 'english',
                'education_level': 'upper_primary',
                'is_composite': True,
                'component_1_name': 'Grammar',
                'component_1_weight': 60.0,
                'component_2_name': 'Composition',
                'component_2_weight': 40.0
            },
            {
                'subject_name': 'kiswahili',
                'education_level': 'upper_primary',
                'is_composite': True,
                'component_1_name': 'Lugha',
                'component_1_weight': 50.0,
                'component_2_name': 'Insha',
                'component_2_weight': 50.0
            },
            # Junior Secondary configurations
            {
                'subject_name': 'english',
                'education_level': 'junior_secondary',
                'is_composite': True,
                'component_1_name': 'Grammar',
                'component_1_weight': 60.0,
                'component_2_name': 'Composition',
                'component_2_weight': 40.0
            },
            {
                'subject_name': 'kiswahili',
                'education_level': 'junior_secondary',
                'is_composite': True,
                'component_1_name': 'Lugha',
                'component_1_weight': 50.0,
                'component_2_name': 'Insha',
                'component_2_weight': 50.0
            }
        ]

        print(f"✅ Loaded {len(configurations)} configurations (English & Kiswahili only)")

        return render_template('subject_configuration.html',
                             configurations=configurations,
                             school_name="School Management System")



    except Exception as e:
        print(f"Error loading subject configuration page: {e}")
        import traceback
        traceback.print_exc()
        # Return a simple error response instead of template
        return f"""
        <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
            <h2 style="color: #dc3545;">Configuration Error</h2>
            <p>Failed to load subject configuration page.</p>
            <p style="color: #6c757d;">Error: {str(e)}</p>
            <a href="javascript:history.back()" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go Back</a>
        </div>
        """, 500

@subject_config_api.route('/api/subject-config/toggle', methods=['POST'])
@admin_required
def toggle_composite_mode():
    """Toggle composite mode for a subject."""
    try:
        data = request.get_json()
        subject_name = data.get('subject_name')
        education_level = data.get('education_level')
        is_composite = data.get('is_composite')

        print(f"Toggle request: {subject_name}, {education_level}, {is_composite}")

        if not all([subject_name, education_level, is_composite is not None]):
            return jsonify({
                'success': False,
                'message': 'Missing required parameters'
            }), 400

        # Get current configuration
        config = FlexibleSubjectService.get_subject_configuration(subject_name, education_level)

        if not config:
            # Create default configuration
            if subject_name.lower() == 'english':
                component_1_name = 'Grammar'
                component_1_weight = 60.0
                component_2_name = 'Composition'
                component_2_weight = 40.0
            elif subject_name.lower() == 'kiswahili':
                component_1_name = 'Lugha'
                component_1_weight = 50.0
                component_2_name = 'Insha'
                component_2_weight = 50.0
            else:
                component_1_name = 'Component 1'
                component_1_weight = 50.0
                component_2_name = 'Component 2'
                component_2_weight = 50.0
        else:
            component_1_name = config['component_1_name']
            component_1_weight = config['component_1_weight']
            component_2_name = config['component_2_name']
            component_2_weight = config['component_2_weight']

        # Update configuration using the service
        success = FlexibleSubjectService.update_subject_configuration(
            subject_name, education_level, is_composite,
            component_1_name, component_1_weight,
            component_2_name, component_2_weight
        )

        if not success:
            return jsonify({
                'success': False,
                'message': 'Failed to update configuration'
            }), 500

        print(f"Successfully updated configuration for {subject_name}")

        return jsonify({
            'success': True,
            'message': f'{subject_name.title()} configuration updated successfully'
        })

    except Exception as e:
        print(f"Error toggling composite mode: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@subject_config_api.route('/api/subject-config/update-component', methods=['POST'])
@admin_required
def update_component_weight():
    """Update component weight for a composite subject."""
    try:
        data = request.get_json()
        subject_name = data.get('subject_name')
        education_level = data.get('education_level')
        component_number = data.get('component_number')
        weight = data.get('weight')

        if not all([subject_name, education_level, component_number, weight is not None]):
            return jsonify({
                'success': False,
                'message': 'Missing required parameters'
            }), 400

        # Get current configuration
        config = FlexibleSubjectService.get_subject_configuration(subject_name, education_level)

        if not config:
            return jsonify({
                'success': False,
                'message': 'Configuration not found'
            }), 404

        # Update the appropriate component weight
        if component_number == 1:
            component_1_weight = weight
            component_2_weight = config['component_2_weight']
        elif component_number == 2:
            component_1_weight = config['component_1_weight']
            component_2_weight = weight
        else:
            return jsonify({
                'success': False,
                'message': 'Invalid component number'
            }), 400
        
        # Update configuration
        success = FlexibleSubjectService.update_subject_configuration(
            subject_name, education_level, config['is_composite'],
            config['component_1_name'], component_1_weight,
            config['component_2_name'], component_2_weight
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Component weight updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update component weight'
            }), 500
    
    except Exception as e:
        print(f"Error updating component weight: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@subject_config_api.route('/api/subject-config/save-all', methods=['POST'])
@admin_required
def save_all_configurations():
    """Save all configurations and sync with Subject table."""
    try:
        print("📝 Save All Configurations called")

        # Get all current configurations
        configurations = FlexibleSubjectService.get_all_configurations()
        print(f"📊 Found {len(configurations)} configurations")

        # Sync with Subject table
        from ..models.academic import Subject
        from ..extensions import db

        updated_count = 0
        for config in configurations:
            if config['is_composite']:
                print(f"🔄 Syncing {config['subject_name']} ({config['education_level']}) with Subject table")

                # Try multiple matching strategies for subject names
                subject_name = config['subject_name'].lower()
                education_level = config['education_level']

                # Strategy 1: Exact match (case-insensitive)
                subjects = Subject.query.filter(
                    Subject.name.ilike(subject_name),
                    Subject.education_level == education_level
                ).all()

                # Strategy 2: Contains match if exact doesn't work
                if not subjects:
                    subjects = Subject.query.filter(
                        Subject.name.ilike(f"%{subject_name}%"),
                        Subject.education_level == education_level
                    ).all()

                # Strategy 3: Try uppercase version
                if not subjects:
                    subjects = Subject.query.filter(
                        Subject.name.ilike(subject_name.upper()),
                        Subject.education_level == education_level
                    ).all()

                # Strategy 4: Try with contains uppercase
                if not subjects:
                    subjects = Subject.query.filter(
                        Subject.name.ilike(f"%{subject_name.upper()}%"),
                        Subject.education_level == education_level
                    ).all()

                print(f"🔍 Found {len(subjects)} subjects matching '{subject_name}' in {education_level}")

                for subject in subjects:
                    print(f"📝 Checking subject: '{subject.name}' (current composite: {subject.is_composite})")
                    if not subject.is_composite:
                        subject.is_composite = True
                        updated_count += 1
                        print(f"✅ Updated {subject.name} ({subject.education_level}) to composite")
                    else:
                        print(f"ℹ️ {subject.name} already marked as composite")

        if updated_count > 0:
            db.session.commit()
            print(f"💾 Committed {updated_count} subject updates")

        # Check if subjects are already composite
        from ..models.academic import Subject
        english_subjects = Subject.query.filter(Subject.name.ilike('%english%')).all()
        kiswahili_subjects = Subject.query.filter(Subject.name.ilike('%kiswahili%')).all()

        already_composite_count = sum(1 for s in english_subjects + kiswahili_subjects if s.is_composite)
        total_target_subjects = len(english_subjects) + len(kiswahili_subjects)

        # Create detailed message
        if updated_count > 0:
            message = f'✅ SUCCESS! {len(configurations)} configurations saved, {updated_count} subjects updated to composite. English and Kiswahili will now show as composite in marks upload.'
        elif already_composite_count > 0:
            message = f'✅ ALREADY CONFIGURED! {len(configurations)} configurations saved. Found {already_composite_count}/{total_target_subjects} English/Kiswahili subjects already marked as composite. Your composite subjects should work in marks upload!'
        else:
            message = f'⚠️ {len(configurations)} configurations saved, but no English/Kiswahili subjects found in database. Please check if subjects exist.'

        return jsonify({
            'success': True,
            'message': message,
            'configurations_count': len(configurations),
            'subjects_updated': updated_count,
            'debug_info': f'Processed {len(configurations)} configurations, updated {updated_count} subjects'
        })

    except Exception as e:
        print(f"❌ Error in save all configurations: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@subject_config_api.route('/api/subject-info/<subject_name>/<education_level>')
def get_subject_info(subject_name, education_level):
    """Get subject information for frontend (case-insensitive)."""
    try:
        subject_info = FlexibleSubjectService.get_subject_info_for_frontend(subject_name, education_level)

        return jsonify({
            'success': True,
            'subject': subject_info
        })

    except Exception as e:
        print(f"Error getting subject info: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@subject_config_api.route('/api/check-composite/<subject_name>/<education_level>')
def check_if_composite(subject_name, education_level):
    """Check if a subject is configured as composite for the teacher interface."""
    try:
        # Use the FlexibleSubjectService to check if subject is composite
        is_composite = FlexibleSubjectService.is_subject_composite(subject_name, education_level)

        if is_composite:
            # Get the component configuration
            components = FlexibleSubjectService.get_subject_components(subject_name, education_level)
            config = FlexibleSubjectService.get_subject_configuration(subject_name, education_level)

            return jsonify({
                'success': True,
                'is_composite': True,
                'subject_type': FlexibleSubjectService.detect_subject_type(subject_name),
                'components': components,
                'config': config
            })
        else:
            return jsonify({
                'success': True,
                'is_composite': False,
                'subject_type': FlexibleSubjectService.detect_subject_type(subject_name),
                'components': [],
                'config': None
            })

    except Exception as e:
        print(f"Error checking if subject is composite: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@subject_config_api.route('/api/subject-config/detect-type/<subject_name>')
def detect_subject_type(subject_name):
    """Detect subject type (english, kiswahili, other) - case insensitive."""
    try:
        subject_type = FlexibleSubjectService.detect_subject_type(subject_name)
        
        return jsonify({
            'success': True,
            'subject_type': subject_type,
            'is_configurable': subject_type in ['english', 'kiswahili']
        })
    
    except Exception as e:
        print(f"Error detecting subject type: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@subject_config_api.route('/api/subject-config/all')
def get_all_configurations():
    """Get all subject configurations."""
    try:
        configurations = FlexibleSubjectService.get_all_configurations()
        
        return jsonify({
            'success': True,
            'configurations': configurations
        })
    
    except Exception as e:
        print(f"Error getting all configurations: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500
