"""
Enhanced Composite Subject Service - Improved UX for component handling
Implements component-as-independent-subject with better report display
"""

from typing import List, Dict, Optional, Tuple
from ..models.academic import Subject, Mark, Student, Term, AssessmentType
from ..extensions import db


class EnhancedCompositeService:
    """Enhanced service for handling composite subjects with better UX."""
    
    # Define composite subject mappings
    COMPOSITE_MAPPINGS = {
        'English': {
            'components': ['English Grammar', 'English Composition'],
            'short_names': ['Grammar', 'Composition'],
            'weights': [0.6, 0.4]  # Grammar 60%, Composition 40%
        },
        'Kiswahili': {
            'components': ['Kiswahili Lugha', 'Kiswahili Insha'],
            'short_names': ['Lugha', 'Insha'],
            'weights': [0.6, 0.4]  # Lugha 60%, Insha 40%
        }
    }
    
    @staticmethod
    def get_subjects_for_upload(education_level: str) -> List[Subject]:
        """
        Get subjects available for marks upload, prioritizing component subjects.
        
        Args:
            education_level: The education level
            
        Returns:
            List of subjects, with component subjects shown individually
        """
        # Get all subjects for the education level
        all_subjects = Subject.query.filter_by(education_level=education_level).all()
        
        # Separate composite and component subjects
        component_subjects = [s for s in all_subjects if s.is_component]
        regular_subjects = [s for s in all_subjects if not s.is_composite and not s.is_component]
        
        # Return component subjects + regular subjects (exclude composite parents)
        return component_subjects + regular_subjects
    
    @staticmethod
    def get_composite_display_data(student_id: int, term_id: int, assessment_type_id: int, 
                                 education_level: str) -> Dict:
        """
        Get composite subject data for report display with proper column structure.
        
        Returns:
            Dictionary with composite subjects and their component data
        """
        composite_data = {}
        
        for composite_name, config in EnhancedCompositeService.COMPOSITE_MAPPINGS.items():
            component_data = {}
            total_weighted_score = 0
            total_weight = 0
            has_any_marks = False
            
            for i, component_name in enumerate(config['components']):
                # Find the component subject
                component_subject = Subject.query.filter_by(
                    name=component_name,
                    education_level=education_level,
                    is_component=True
                ).first()
                
                if component_subject:
                    # Get the mark for this component
                    mark = Mark.query.filter_by(
                        student_id=student_id,
                        subject_id=component_subject.id,
                        term_id=term_id,
                        assessment_type_id=assessment_type_id
                    ).first()
                    
                    short_name = config['short_names'][i]
                    weight = config['weights'][i]
                    
                    if mark and mark.percentage is not None:
                        component_data[short_name] = {
                            'mark': mark.raw_mark or 0,
                            'max_mark': mark.raw_total_marks or 100,
                            'percentage': mark.percentage,
                            'weight': weight
                        }
                        total_weighted_score += mark.percentage * weight
                        total_weight += weight
                        has_any_marks = True
                    else:
                        component_data[short_name] = {
                            'mark': 0,
                            'max_mark': 100,
                            'percentage': 0,
                            'weight': weight
                        }
            
            # Calculate composite total
            if has_any_marks and total_weight > 0:
                composite_total = total_weighted_score / total_weight
                composite_data[composite_name] = {
                    'components': component_data,
                    'total': composite_total,
                    'has_marks': True
                }
            else:
                composite_data[composite_name] = {
                    'components': component_data,
                    'total': 0,
                    'has_marks': False
                }
        
        return composite_data
    
    @staticmethod
    def get_report_subjects_structure(education_level: str) -> Dict:
        """
        Get the subject structure for reports, combining regular and composite subjects.
        
        Returns:
            Dictionary with subject display structure
        """
        # Get all regular subjects (non-composite, non-component)
        regular_subjects = Subject.query.filter_by(
            education_level=education_level,
            is_composite=False,
            is_component=False
        ).all()
        
        # Build the structure
        structure = {
            'regular_subjects': [s.name for s in regular_subjects],
            'composite_subjects': list(EnhancedCompositeService.COMPOSITE_MAPPINGS.keys()),
            'composite_configs': EnhancedCompositeService.COMPOSITE_MAPPINGS
        }
        
        return structure
    
    @staticmethod
    def ensure_component_subjects_exist(education_level: str):
        """
        Ensure all component subjects exist in the database.
        
        Args:
            education_level: The education level to create components for
        """
        for composite_name, config in EnhancedCompositeService.COMPOSITE_MAPPINGS.items():
            # Check if composite parent exists
            composite_subject = Subject.query.filter_by(
                name=composite_name,
                education_level=education_level
            ).first()
            
            if not composite_subject:
                # Create composite parent
                composite_subject = Subject(
                    name=composite_name,
                    education_level=education_level,
                    is_composite=True,
                    is_component=False
                )
                db.session.add(composite_subject)
            else:
                # Update existing to be composite
                composite_subject.is_composite = True
                composite_subject.is_component = False
            
            # Create component subjects
            for i, component_name in enumerate(config['components']):
                component_subject = Subject.query.filter_by(
                    name=component_name,
                    education_level=education_level
                ).first()
                
                if not component_subject:
                    component_subject = Subject(
                        name=component_name,
                        education_level=education_level,
                        is_composite=False,
                        is_component=True,
                        composite_parent=composite_name,
                        component_weight=config['weights'][i]
                    )
                    db.session.add(component_subject)
                else:
                    # Update existing to be component
                    component_subject.is_component = True
                    component_subject.is_composite = False
                    component_subject.composite_parent = composite_name
                    component_subject.component_weight = config['weights'][i]
        
        try:
            db.session.commit()
            print("✅ Component subjects ensured successfully")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error ensuring component subjects: {e}")
    
    @staticmethod
    def get_class_composite_data(grade: str, stream: str, term_id: int, 
                               assessment_type_id: int, education_level: str) -> Dict:
        """
        Get composite subject data for an entire class.
        
        Returns:
            Dictionary with all students' composite subject data
        """
        from ..models.academic import Student, Grade, Stream
        
        # Get the grade and stream objects
        grade_obj = Grade.query.filter_by(name=grade).first()
        stream_obj = Stream.query.filter_by(name=stream, grade_id=grade_obj.id).first() if grade_obj else None
        
        if not grade_obj or not stream_obj:
            return {}
        
        # Get all students in the class
        students = Student.query.filter_by(stream_id=stream_obj.id).all()
        
        class_composite_data = {}
        
        for student in students:
            student_data = EnhancedCompositeService.get_composite_display_data(
                student.id, term_id, assessment_type_id, education_level
            )
            class_composite_data[student.id] = student_data
        
        return class_composite_data
