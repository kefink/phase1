"""
Flexible Subject Configuration Service
Handles case-insensitive subject matching and composite/non-composite toggles
"""

from ..extensions import db
from ..models.academic import Subject, SubjectComponent
from sqlalchemy import text
from typing import Dict, List, Optional, Tuple

class FlexibleSubjectService:
    """Service for managing flexible subject configurations."""
    
    @staticmethod
    def get_subject_configuration(subject_name: str, education_level: str) -> Optional[Dict]:
        """
        Get subject configuration for a given subject and education level.
        Case-insensitive subject matching.
        """
        try:
            # Use the main database connection
            with db.engine.connect() as conn:
                # Get configuration (case-insensitive)
                result = conn.execute(text("""
                    SELECT
                        subject_name,
                        education_level,
                        is_composite,
                        component_1_name,
                        component_1_weight,
                        component_2_name,
                        component_2_weight
                    FROM subject_configuration
                    WHERE LOWER(subject_name) = LOWER(:subject_name) AND education_level = :education_level
                """), {"subject_name": subject_name, "education_level": education_level})

                config = result.fetchone()

                if config:
                    return {
                        'subject_name': config[0],
                        'education_level': config[1],
                        'is_composite': bool(config[2]),
                        'component_1_name': config[3],
                        'component_1_weight': config[4],
                        'component_2_name': config[5],
                        'component_2_weight': config[6]
                    }

                return None

        except Exception as e:
            print(f"Error getting subject configuration: {e}")
            return None
    
    @staticmethod
    def is_subject_composite(subject_name: str, education_level: str) -> bool:
        """Check if a subject is configured as composite."""
        config = FlexibleSubjectService.get_subject_configuration(subject_name, education_level)
        return config['is_composite'] if config else False
    
    @staticmethod
    def get_subject_components(subject_name: str, education_level: str) -> List[Dict]:
        """Get components for a composite subject."""
        config = FlexibleSubjectService.get_subject_configuration(subject_name, education_level)
        
        if not config or not config['is_composite']:
            return []
        
        components = []
        
        if config['component_1_name']:
            components.append({
                'name': config['component_1_name'],
                'weight': config['component_1_weight']
            })
        
        if config['component_2_name']:
            components.append({
                'name': config['component_2_name'],
                'weight': config['component_2_weight']
            })
        
        return components
    
    @staticmethod
    def update_subject_configuration(subject_name: str, education_level: str,
                                   is_composite: bool, component_1_name: str = None,
                                   component_1_weight: float = 50.0, component_2_name: str = None,
                                   component_2_weight: float = 50.0) -> bool:
        """Update subject configuration and sync with Subject model."""
        try:
            with db.engine.connect() as conn:
                # Check if configuration exists
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM subject_configuration
                    WHERE subject_name = :subject_name AND education_level = :education_level
                """), {
                    "subject_name": subject_name.lower(),
                    "education_level": education_level
                })

                exists = result.fetchone()[0] > 0

                if exists:
                    # Update existing configuration
                    conn.execute(text("""
                        UPDATE subject_configuration SET
                        is_composite = :is_composite,
                        component_1_name = :component_1_name,
                        component_1_weight = :component_1_weight,
                        component_2_name = :component_2_name,
                        component_2_weight = :component_2_weight,
                        updated_at = CURRENT_TIMESTAMP
                        WHERE subject_name = :subject_name AND education_level = :education_level
                    """), {
                        "subject_name": subject_name.lower(),
                        "education_level": education_level,
                        "is_composite": is_composite,
                        "component_1_name": component_1_name,
                        "component_1_weight": component_1_weight,
                        "component_2_name": component_2_name,
                        "component_2_weight": component_2_weight
                    })
                else:
                    # Insert new configuration
                    conn.execute(text("""
                        INSERT INTO subject_configuration
                        (subject_name, education_level, is_composite, component_1_name, component_1_weight,
                         component_2_name, component_2_weight, updated_at)
                        VALUES (:subject_name, :education_level, :is_composite, :component_1_name, :component_1_weight,
                                :component_2_name, :component_2_weight, CURRENT_TIMESTAMP)
                    """), {
                        "subject_name": subject_name.lower(),
                        "education_level": education_level,
                        "is_composite": is_composite,
                        "component_1_name": component_1_name,
                        "component_1_weight": component_1_weight,
                        "component_2_name": component_2_name,
                        "component_2_weight": component_2_weight
                    })

                # Update actual subjects in database using more compatible SQL
                # Try multiple matching strategies for case-insensitive matching
                subject_patterns = [
                    subject_name.upper(),  # Try uppercase first (most likely in your DB)
                    subject_name.lower(),  # exact lowercase match
                    subject_name.title(),  # Title case (English, Kiswahili)
                    f"%{subject_name.upper()}%",  # uppercase contains
                    f"%{subject_name.lower()}%",  # lowercase contains
                    f"%{subject_name.title()}%"   # title case contains
                ]

                updated_subjects = 0
                subject_ids = []

                for pattern in subject_patterns:
                    # Update subjects
                    result = conn.execute(text("""
                        UPDATE subject
                        SET is_composite = :is_composite
                        WHERE LOWER(name) LIKE LOWER(:pattern) AND education_level = :education_level
                    """), {
                        "is_composite": is_composite,
                        "pattern": pattern,
                        "education_level": education_level
                    })

                    updated_subjects += result.rowcount

                    # Get matching subject IDs
                    result = conn.execute(text("""
                        SELECT id, name FROM subject
                        WHERE LOWER(name) LIKE LOWER(:pattern) AND education_level = :education_level
                    """), {
                        "pattern": pattern,
                        "education_level": education_level
                    })

                    for row in result.fetchall():
                        if row[0] not in [s[0] for s in subject_ids]:  # avoid duplicates
                            subject_ids.append((row[0], row[1]))

                    if subject_ids:  # If we found matches, stop trying other patterns
                        break

                print(f"📊 Updated {updated_subjects} subjects, found {len(subject_ids)} subject IDs: {[s[1] for s in subject_ids]}")

                # Update components for each matching subject
                for subject_id, _ in subject_ids:
                    # Remove existing components
                    conn.execute(text("DELETE FROM subject_component WHERE subject_id = :subject_id"),
                               {"subject_id": subject_id})

                    if is_composite:
                        # Add new components
                        if component_1_name:
                            conn.execute(text("""
                                INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
                                VALUES (:subject_id, :name, :weight, 100)
                            """), {
                                "subject_id": subject_id,
                                "name": component_1_name,
                                "weight": component_1_weight
                            })

                        if component_2_name:
                            conn.execute(text("""
                                INSERT INTO subject_component (subject_id, name, weight, max_raw_mark)
                                VALUES (:subject_id, :name, :weight, 100)
                            """), {
                                "subject_id": subject_id,
                                "name": component_2_name,
                                "weight": component_2_weight
                            })

                conn.commit()
                print(f"✅ Successfully updated {subject_name} configuration and {len(subject_ids)} subject records")

                if len(subject_ids) == 0:
                    print(f"⚠️ Warning: No subjects found matching '{subject_name}' in '{education_level}'")

                return True

        except Exception as e:
            print(f"❌ Error updating subject configuration for {subject_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    @staticmethod
    def get_all_configurations() -> List[Dict]:
        """Get all subject configurations."""
        try:
            with db.engine.connect() as conn:
                result = conn.execute(text("""
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
                """))

                configs = []
                for row in result.fetchall():
                    configs.append({
                        'subject_name': row[0],
                        'education_level': row[1],
                        'is_composite': bool(row[2]),
                        'component_1_name': row[3],
                        'component_1_weight': row[4],
                        'component_2_name': row[5],
                        'component_2_weight': row[6]
                    })

                return configs
            
        except Exception as e:
            print(f"Error getting all configurations: {e}")
            return []
    
    @staticmethod
    def detect_subject_type(subject_name: str) -> str:
        """Detect subject type from name (case-insensitive)."""
        subject_lower = subject_name.lower()
        
        if 'english' in subject_lower:
            return 'english'
        elif 'kiswahili' in subject_lower or 'kiswahili' in subject_lower:
            return 'kiswahili'
        else:
            return 'other'
    
    @staticmethod
    def get_subject_info_for_frontend(subject_name: str, education_level: str) -> Dict:
        """Get subject information formatted for frontend use."""
        subject_type = FlexibleSubjectService.detect_subject_type(subject_name)
        
        if subject_type in ['english', 'kiswahili']:
            config = FlexibleSubjectService.get_subject_configuration(subject_type, education_level)
            
            if config and config['is_composite']:
                return {
                    'is_composite': True,
                    'subject_type': subject_type,
                    'components': FlexibleSubjectService.get_subject_components(subject_type, education_level),
                    'config': config
                }
        
        return {
            'is_composite': False,
            'subject_type': subject_type,
            'components': [],
            'config': None
        }
    
    @staticmethod
    def toggle_composite_mode(subject_name: str, education_level: str) -> bool:
        """Toggle composite mode for a subject."""
        config = FlexibleSubjectService.get_subject_configuration(subject_name, education_level)
        
        if not config:
            return False
        
        new_composite_status = not config['is_composite']
        
        return FlexibleSubjectService.update_subject_configuration(
            subject_name, education_level, new_composite_status,
            config['component_1_name'], config['component_1_weight'],
            config['component_2_name'], config['component_2_weight']
        )
