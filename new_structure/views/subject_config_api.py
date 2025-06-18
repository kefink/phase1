"""
Subject Configuration API endpoints
Handles flexible subject configuration for English and Kiswahili
"""

from flask import Blueprint, request, jsonify, render_template, session
from ..services.flexible_subject_service import FlexibleSubjectService
from .admin import admin_required
import json

subject_config_api = Blueprint('subject_config_api', __name__)

@subject_config_api.route('/subject-configuration')
@admin_required
def subject_configuration_page():
    """Display subject configuration management page."""
    try:
        # Get all configurations directly from MySQL database
        import mysql.connector
        import json
        import os

        # Load MySQL credentials
        creds_path = os.path.join('mysql_migration', 'mysql_credentials.json')
        if not os.path.exists(creds_path):
            return f"""
            <div style="text-align: center; padding: 50px; font-family: Arial, sans-serif;">
                <h2 style="color: #dc3545;">Database Error</h2>
                <p>MySQL credentials not found: {creds_path}</p>
                <a href="javascript:history.back()" style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Go Back</a>
            </div>
            """, 500

        with open(creds_path, 'r') as f:
            creds = json.load(f)

        connection_params = {
            'host': creds['host'],
            'database': creds['database_name'],
            'user': creds['username'],
            'password': creds['password'],
            'port': creds['port']
        }

        conn = mysql.connector.connect(**connection_params)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                subject_name,
                education_level,
                is_composite,
                component_1_name,
                component_1_weight,
                component_2_name,
                component_2_weight
            FROM subject_configuration
            ORDER BY subject_name, education_level
        """)

        configurations = []
        for row in cursor.fetchall():
            configurations.append({
                'subject_name': row[0],
                'education_level': row[1],
                'is_composite': bool(row[2]),
                'component_1_name': row[3],
                'component_1_weight': row[4],
                'component_2_name': row[5],
                'component_2_weight': row[6]
            })

        conn.close()

        print(f"Loaded {len(configurations)} configurations")

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

        # Direct MySQL database update
        import mysql.connector
        import json
        import os

        # Load MySQL credentials
        creds_path = os.path.join('mysql_migration', 'mysql_credentials.json')
        if not os.path.exists(creds_path):
            return jsonify({
                'success': False,
                'message': 'MySQL credentials not found'
            }), 500

        with open(creds_path, 'r') as f:
            creds = json.load(f)

        connection_params = {
            'host': creds['host'],
            'database': creds['database_name'],
            'user': creds['username'],
            'password': creds['password'],
            'port': creds['port']
        }

        conn = mysql.connector.connect(**connection_params)
        cursor = conn.cursor()

        # Get current configuration
        cursor.execute("""
            SELECT component_1_name, component_1_weight, component_2_name, component_2_weight
            FROM subject_configuration
            WHERE LOWER(subject_name) = LOWER(%s) AND education_level = %s
        """, (subject_name, education_level))

        config = cursor.fetchone()

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
            component_1_name = config[0]
            component_1_weight = config[1]
            component_2_name = config[2]
            component_2_weight = config[3]

        # Update configuration (MySQL syntax)
        cursor.execute("""
            INSERT INTO subject_configuration
            (subject_name, education_level, is_composite, component_1_name, component_1_weight,
             component_2_name, component_2_weight)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            is_composite = VALUES(is_composite),
            component_1_name = VALUES(component_1_name),
            component_1_weight = VALUES(component_1_weight),
            component_2_name = VALUES(component_2_name),
            component_2_weight = VALUES(component_2_weight),
            updated_at = CURRENT_TIMESTAMP
        """, (subject_name.lower(), education_level, is_composite,
              component_1_name, component_1_weight, component_2_name, component_2_weight))

        # Update actual subjects in database (MySQL syntax)
        cursor.execute("""
            UPDATE subject
            SET is_composite = %s
            WHERE LOWER(name) LIKE CONCAT('%%', %s, '%%') AND education_level = %s
        """, (is_composite, subject_name.lower(), education_level))

        # Get subject IDs that match
        cursor.execute("""
            SELECT id FROM subject
            WHERE LOWER(name) LIKE CONCAT('%%', %s, '%%') AND education_level = %s
        """, (subject_name.lower(), education_level))

        subject_ids = [row[0] for row in cursor.fetchall()]

        # Update components for each matching subject
        for subject_id in subject_ids:
            # Remove existing components (MySQL syntax)
            cursor.execute("DELETE FROM subject_component WHERE subject_id = %s", (subject_id,))

            if is_composite:
                # Add new components
                if component_1_name:
                    cursor.execute("""
                        INSERT INTO subject_component (subject_id, name, weight)
                        VALUES (%s, %s, %s)
                    """, (subject_id, component_1_name, component_1_weight))

                if component_2_name:
                    cursor.execute("""
                        INSERT INTO subject_component (subject_id, name, weight)
                        VALUES (%s, %s, %s)
                    """, (subject_id, component_2_name, component_2_weight))

        conn.commit()
        conn.close()

        print(f"Successfully updated {len(subject_ids)} subjects")

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
    """Save all configurations (mainly for UI feedback)."""
    try:
        return jsonify({
            'success': True,
            'message': 'All configurations are automatically saved'
        })
    
    except Exception as e:
        print(f"Error in save all configurations: {e}")
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@subject_config_api.route('/api/subject-info/<subject_name>/<education_level>')
def get_subject_info():
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
