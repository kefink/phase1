"""
Class Structure Detection Service for intelligent handling of single classes vs. streamed classes.
Provides unified interface for headteacher universal access to all class functions.
"""
from ..models.academic import Grade, Stream, Student, Mark
from ..extensions import db
from sqlalchemy import func

class ClassStructureService:
    """Service for detecting and managing class structures intelligently."""
    
    @staticmethod
    def get_school_structure():
        """
        Get complete school structure with intelligent class/stream detection.
        
        Returns:
            Dictionary with comprehensive school structure information
        """
        try:
            grades = Grade.query.all()
            structure = {
                'grades': [],
                'total_classes': 0,
                'uses_streams': False,
                'mixed_structure': False,  # Some grades have streams, others don't
                'structure_summary': {}
            }
            
            single_class_grades = 0
            streamed_grades = 0
            
            for grade in grades:
                streams = Stream.query.filter_by(grade_id=grade.id).all()
                student_count = Student.query.join(Stream).filter(Stream.grade_id == grade.id).count()
                
                grade_info = {
                    'id': grade.id,
                    'name': grade.name,
                    'education_level': getattr(grade, 'education_level', 'primary'),
                    'type': 'single_class' if len(streams) <= 1 else 'multi_stream',
                    'stream_count': len(streams),
                    'streams': [],
                    'student_count': student_count,
                    'has_data': student_count > 0
                }
                
                # Process streams
                for stream in streams:
                    stream_students = Student.query.filter_by(stream_id=stream.id).count()
                    grade_info['streams'].append({
                        'id': stream.id,
                        'name': stream.name,
                        'student_count': stream_students,
                        'display_name': f"{grade.name} {stream.name}" if len(streams) > 1 else grade.name
                    })
                
                # Count structure types
                if len(streams) <= 1:
                    single_class_grades += 1
                else:
                    streamed_grades += 1
                    structure['uses_streams'] = True
                
                structure['grades'].append(grade_info)
                structure['total_classes'] += len(streams)
            
            # Determine if school has mixed structure
            structure['mixed_structure'] = single_class_grades > 0 and streamed_grades > 0
            
            # Create structure summary
            structure['structure_summary'] = {
                'total_grades': len(grades),
                'single_class_grades': single_class_grades,
                'streamed_grades': streamed_grades,
                'total_streams': sum(len(g['streams']) for g in structure['grades']),
                'structure_type': ClassStructureService._determine_structure_type(
                    single_class_grades, streamed_grades
                )
            }
            
            return structure
            
        except Exception as e:
            print(f"Error getting school structure: {e}")
            return {
                'grades': [],
                'total_classes': 0,
                'uses_streams': False,
                'mixed_structure': False,
                'structure_summary': {}
            }
    
    @staticmethod
    def _determine_structure_type(single_class_grades, streamed_grades):
        """Determine the overall structure type of the school."""
        if single_class_grades == 0 and streamed_grades == 0:
            return 'empty'
        elif single_class_grades > 0 and streamed_grades == 0:
            return 'single_class_only'
        elif single_class_grades == 0 and streamed_grades > 0:
            return 'streamed_only'
        else:
            return 'mixed_structure'
    
    @staticmethod
    def get_class_display_name(grade_name, stream_name=None):
        """
        Get appropriate display name for a class based on structure.
        
        Args:
            grade_name: Name of the grade
            stream_name: Name of the stream (optional)
            
        Returns:
            Formatted display name
        """
        if not stream_name or stream_name.lower() in ['main', 'default']:
            return grade_name
        return f"{grade_name} {stream_name}"
    
    @staticmethod
    def get_grade_structure(grade_name):
        """
        Get structure information for a specific grade.
        
        Args:
            grade_name: Name of the grade
            
        Returns:
            Dictionary with grade structure information
        """
        try:
            grade = Grade.query.filter_by(name=grade_name).first()
            if not grade:
                return None
            
            streams = Stream.query.filter_by(grade_id=grade.id).all()
            
            return {
                'grade_id': grade.id,
                'grade_name': grade.name,
                'is_single_class': len(streams) <= 1,
                'stream_count': len(streams),
                'streams': [
                    {
                        'id': s.id,
                        'name': s.name,
                        'display_name': ClassStructureService.get_class_display_name(grade.name, s.name),
                        'student_count': Student.query.filter_by(stream_id=s.id).count()
                    }
                    for s in streams
                ],
                'total_students': Student.query.join(Stream).filter(Stream.grade_id == grade.id).count()
            }
            
        except Exception as e:
            print(f"Error getting grade structure: {e}")
            return None
    
    @staticmethod
    def get_all_classes_for_selection():
        """
        Get all classes formatted for selection dropdowns.
        Handles both single classes and streamed classes.
        
        Returns:
            List of class options for UI selection
        """
        try:
            structure = ClassStructureService.get_school_structure()
            classes = []
            
            for grade in structure['grades']:
                if grade['type'] == 'single_class':
                    # Single class - use grade name only
                    classes.append({
                        'value': f"{grade['name']}",
                        'label': grade['name'],
                        'grade_id': grade['id'],
                        'stream_id': grade['streams'][0]['id'] if grade['streams'] else None,
                        'type': 'single_class',
                        'student_count': grade['student_count']
                    })
                else:
                    # Multiple streams - list each stream
                    for stream in grade['streams']:
                        classes.append({
                            'value': f"{grade['name']}|{stream['name']}",
                            'label': stream['display_name'],
                            'grade_id': grade['id'],
                            'stream_id': stream['id'],
                            'type': 'stream',
                            'student_count': stream['student_count']
                        })
            
            return classes
            
        except Exception as e:
            print(f"Error getting classes for selection: {e}")
            return []
    
    @staticmethod
    def parse_class_identifier(class_identifier):
        """
        Parse a class identifier into grade and stream components.
        
        Args:
            class_identifier: String like "Grade 1" or "Grade 1|A"
            
        Returns:
            Tuple of (grade_name, stream_name)
        """
        if '|' in class_identifier:
            grade_name, stream_name = class_identifier.split('|', 1)
            return grade_name.strip(), stream_name.strip()
        else:
            # Single class - find the default stream
            grade = Grade.query.filter_by(name=class_identifier.strip()).first()
            if grade:
                stream = Stream.query.filter_by(grade_id=grade.id).first()
                return grade.name, stream.name if stream else 'Main'
            return class_identifier.strip(), None
    
    @staticmethod
    def get_class_statistics():
        """
        Get comprehensive statistics about all classes.
        
        Returns:
            Dictionary with class statistics
        """
        try:
            structure = ClassStructureService.get_school_structure()
            
            stats = {
                'total_grades': len(structure['grades']),
                'total_classes': structure['total_classes'],
                'total_students': sum(g['student_count'] for g in structure['grades']),
                'structure_type': structure['structure_summary']['structure_type'],
                'grade_breakdown': [],
                'performance_summary': {}
            }
            
            # Add detailed breakdown
            for grade in structure['grades']:
                grade_stats = {
                    'grade_name': grade['name'],
                    'type': grade['type'],
                    'stream_count': grade['stream_count'],
                    'student_count': grade['student_count'],
                    'streams': grade['streams']
                }
                stats['grade_breakdown'].append(grade_stats)
            
            return stats
            
        except Exception as e:
            print(f"Error getting class statistics: {e}")
            return {}
