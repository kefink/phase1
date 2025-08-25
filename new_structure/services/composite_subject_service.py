"""
Composite Subject Service - Handles the new component-as-independent-subject architecture
"""

from typing import List, Dict, Optional, Tuple
from ..models.academic import Subject, Mark, Student, Term, AssessmentType
from ..extensions import db


class CompositeSubjectService:
    """Service for handling composite subjects and their components."""
    
    @staticmethod
    def get_subjects_for_upload(education_level: str) -> List[Subject]:
        """
        Get subjects available for marks upload, including component subjects.
        
        Args:
            education_level: The education level (e.g., 'primary', 'junior secondary')
            
        Returns:
            List of subjects sorted appropriately (components grouped by parent)
        """
        # Get all subjects for this education level
        all_subjects = Subject.query.filter_by(education_level=education_level).all()
        
        # Filter subjects: include regular subjects and component subjects, exclude old composite subjects
        subjects = []
        for subject in all_subjects:
            # Include regular subjects (not composite, not component)
            if not subject.is_composite and not subject.is_component:
                subjects.append(subject)
            # Include component subjects (new architecture)
            elif subject.is_component:
                subjects.append(subject)
            # Skip old composite subjects (they're replaced by components)
        
        # Sort subjects: components grouped by parent, then alphabetically
        def sort_key(subject):
            if subject.is_component:
                # Group components by parent: "English Grammar" -> "English_Grammar"
                return f"{subject.composite_parent}_{subject.name}"
            else:
                # Regular subjects: "Mathematics" -> "Mathematics"
                return subject.name
        
        subjects.sort(key=sort_key)
        return subjects
    
    @staticmethod
    def get_composite_subject_mark(student_id: int, composite_name: str, 
                                 term_id: int, assessment_type_id: int,
                                 education_level: str) -> Optional[Dict]:
        """
        Calculate combined mark for a composite subject from its component marks.
        
        Args:
            student_id: ID of the student
            composite_name: Name of the composite subject (e.g., 'English', 'Kiswahili')
            term_id: ID of the term
            assessment_type_id: ID of the assessment type
            education_level: Education level for the subject
            
        Returns:
            Dictionary with component marks and total, or None if no marks found
        """
        # Get component subjects for this composite
        component_subjects = Subject.query.filter_by(
            composite_parent=composite_name,
            education_level=education_level,
            is_component=True
        ).all()
        
        if not component_subjects:
            return None
        
        component_marks = {}
        total_weighted_mark = 0
        total_weight = 0
        has_any_marks = False
        
        for component in component_subjects:
            # Get mark for this component
            mark = Mark.query.filter_by(
                student_id=student_id,
                subject_id=component.id,
                term_id=term_id,
                assessment_type_id=assessment_type_id
            ).first()
            
            if mark:
                component_marks[component.name] = {
                    'raw_mark': mark.raw_mark,
                    'max_raw_mark': mark.max_raw_mark,
                    'percentage': mark.percentage,
                    'weight': component.component_weight
                }
                
                # Add to weighted total
                total_weighted_mark += mark.percentage * component.component_weight
                total_weight += component.component_weight
                has_any_marks = True
            else:
                component_marks[component.name] = {
                    'raw_mark': 0,
                    'max_raw_mark': 100,
                    'percentage': 0,
                    'weight': component.component_weight
                }
        
        # Always return results even if some components are missing
        # This allows partial composite subject display
        if not has_any_marks:
            # If no components have marks, return None
            return None

        # Calculate combined percentage from available components
        combined_percentage = total_weighted_mark / total_weight if total_weight > 0 else 0
        
        return {
            'components': component_marks,
            'combined_percentage': combined_percentage,
            'total_weight': total_weight
        }
    
    @staticmethod
    def get_all_composite_subjects(education_level: str) -> List[str]:
        """
        Get list of all composite subject names for an education level.
        
        Args:
            education_level: The education level
            
        Returns:
            List of composite subject names
        """
        # Get unique composite parent names
        component_subjects = Subject.query.filter_by(
            education_level=education_level,
            is_component=True
        ).all()
        
        composite_names = list(set(
            subject.composite_parent 
            for subject in component_subjects 
            if subject.composite_parent
        ))
        
        return sorted(composite_names)
    
    @staticmethod
    def is_component_subject(subject_id: int) -> bool:
        """Check if a subject is a component subject."""
        subject = Subject.query.get(subject_id)
        return subject and subject.is_component
    
    @staticmethod
    def get_component_display_name(subject: Subject) -> str:
        """
        Get display name for a component subject.
        
        Args:
            subject: The subject object
            
        Returns:
            Formatted display name (e.g., "English Grammar", "Kiswahili Lugha")
        """
        if not subject.is_component:
            return subject.name
        
        # For component subjects, the name already includes the parent
        # e.g., "English Grammar", "Kiswahili Lugha"
        return subject.name
    
    @staticmethod
    def get_subject_group_info(subject: Subject) -> Dict:
        """
        Get grouping information for a subject (for UI organization).
        
        Args:
            subject: The subject object
            
        Returns:
            Dictionary with group information
        """
        if subject.is_component:
            return {
                'is_component': True,
                'parent': subject.composite_parent,
                'weight': subject.component_weight,
                'group_label': f"{subject.composite_parent} Components"
            }
        else:
            return {
                'is_component': False,
                'parent': None,
                'weight': 1.0,
                'group_label': "Regular Subjects"
            }
    
    @staticmethod
    def validate_component_marks(component_marks: Dict[str, float], 
                               composite_name: str, education_level: str) -> Tuple[bool, str]:
        """
        Validate component marks for a composite subject.
        
        Args:
            component_marks: Dictionary of component names to marks
            composite_name: Name of the composite subject
            education_level: Education level
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Get expected components
        expected_components = Subject.query.filter_by(
            composite_parent=composite_name,
            education_level=education_level,
            is_component=True
        ).all()
        
        expected_names = {comp.name for comp in expected_components}
        provided_names = set(component_marks.keys())
        
        # Check if all expected components are provided
        missing_components = expected_names - provided_names
        if missing_components:
            return False, f"Missing marks for: {', '.join(missing_components)}"
        
        # Check for unexpected components
        extra_components = provided_names - expected_names
        if extra_components:
            return False, f"Unexpected components: {', '.join(extra_components)}"
        
        # Validate mark values
        for comp_name, mark in component_marks.items():
            if not isinstance(mark, (int, float)) or mark < 0:
                return False, f"Invalid mark for {comp_name}: {mark}"
        
        return True, ""
    
    @staticmethod
    def migrate_legacy_composite_mark(legacy_mark: Mark) -> List[Mark]:
        """
        Migrate a legacy composite mark to component marks.
        This is used during the transition period.
        
        Args:
            legacy_mark: The legacy composite subject mark
            
        Returns:
            List of new component marks created
        """
        # This would be implemented if we need to migrate existing data
        # For now, we'll handle this in the migration script
        pass
