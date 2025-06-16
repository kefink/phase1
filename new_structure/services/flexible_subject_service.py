"""
Flexible Subject Configuration Service
Handles case-insensitive subject matching and composite/non-composite toggles
"""

from ..extensions import db
from ..models.academic import Subject, SubjectComponent
import sqlite3
import os
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
            # Connect to database directly for configuration lookup
            db_path = 'kirima_primary.db'
            if not os.path.exists(db_path):
                return None
                
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get configuration (case-insensitive)
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
                WHERE LOWER(subject_name) = LOWER(?) AND education_level = ?
            """, (subject_name, education_level))
            
            config = cursor.fetchone()
            conn.close()
            
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
        """Update subject configuration."""
        try:
            db_path = 'kirima_primary.db'
            if not os.path.exists(db_path):
                return False
                
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Update configuration
            cursor.execute("""
                INSERT OR REPLACE INTO subject_configuration 
                (subject_name, education_level, is_composite, component_1_name, component_1_weight, 
                 component_2_name, component_2_weight, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """, (subject_name.lower(), education_level, is_composite, 
                  component_1_name, component_1_weight, component_2_name, component_2_weight))
            
            # Update actual subjects in database
            cursor.execute("""
                UPDATE subject 
                SET is_composite = ? 
                WHERE LOWER(name) LIKE '%' || ? || '%' AND education_level = ?
            """, (is_composite, subject_name.lower(), education_level))
            
            # Get subject IDs that match
            cursor.execute("""
                SELECT id FROM subject 
                WHERE LOWER(name) LIKE '%' || ? || '%' AND education_level = ?
            """, (subject_name.lower(), education_level))
            
            subject_ids = [row[0] for row in cursor.fetchall()]
            
            # Update components for each matching subject
            for subject_id in subject_ids:
                # Remove existing components
                cursor.execute("DELETE FROM subject_component WHERE subject_id = ?", (subject_id,))
                
                if is_composite:
                    # Add new components
                    if component_1_name:
                        cursor.execute("""
                            INSERT INTO subject_component (subject_id, name, weight) 
                            VALUES (?, ?, ?)
                        """, (subject_id, component_1_name, component_1_weight))
                    
                    if component_2_name:
                        cursor.execute("""
                            INSERT INTO subject_component (subject_id, name, weight) 
                            VALUES (?, ?, ?)
                        """, (subject_id, component_2_name, component_2_weight))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"Error updating subject configuration: {e}")
            return False
    
    @staticmethod
    def get_all_configurations() -> List[Dict]:
        """Get all subject configurations."""
        try:
            db_path = 'kirima_primary.db'
            if not os.path.exists(db_path):
                return []
                
            conn = sqlite3.connect(db_path)
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
            
            configs = []
            for row in cursor.fetchall():
                configs.append({
                    'subject_name': row[0],
                    'education_level': row[1],
                    'is_composite': bool(row[2]),
                    'component_1_name': row[3],
                    'component_1_weight': row[4],
                    'component_2_name': row[5],
                    'component_2_weight': row[6]
                })
            
            conn.close()
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
