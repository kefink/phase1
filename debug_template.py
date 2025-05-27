"""
Script to debug the template rendering.
"""
from new_structure import create_app
from new_structure.models.academic import Subject, SubjectComponent, Grade, Stream, Term, AssessmentType, Student, Mark, ComponentMark
from new_structure.extensions import db
from flask import render_template_string

def debug_template():
    """Debug the template rendering."""
    app = create_app()
    with app.app_context():
        print("Debugging template rendering...")
        
        # Get a grade, stream, term, and assessment type
        grade = Grade.query.first()
        stream = Stream.query.filter_by(grade_id=grade.id).first()
        term = Term.query.first()
        assessment_type = AssessmentType.query.first()
        
        if not (grade and stream and term and assessment_type):
            print("Could not find grade, stream, term, or assessment type.")
            return
        
        print(f"Using Grade: {grade.level}, Stream: {stream.name}, Term: {term.name}, Assessment Type: {assessment_type.name}")
        
        # Get a student
        student = Student.query.filter_by(stream_id=stream.id).first()
        if not student:
            print("Could not find a student.")
            return
        
        print(f"Using Student: {student.name}, ID: {student.id}")
        
        # Get English and Kiswahili subjects
        english = Subject.query.filter_by(id=2).first()
        kiswahili = Subject.query.filter_by(id=7).first()
        
        if not (english and kiswahili):
            print("Could not find English or Kiswahili subjects.")
            return
        
        print(f"English: {english.name}, ID: {english.id}, Is Composite: {english.is_composite}")
        print(f"Kiswahili: {kiswahili.name}, ID: {kiswahili.id}, Is Composite: {kiswahili.is_composite}")
        
        # Get components
        english_components = english.get_components()
        kiswahili_components = kiswahili.get_components()
        
        print(f"English Components: {[comp.name for comp in english_components]}")
        print(f"Kiswahili Components: {[comp.name for comp in kiswahili_components]}")
        
        # Create a simple template to test rendering
        template = """
        <h1>Template Rendering Test</h1>
        
        <h2>English (ID: {{ english.id }}, Is Composite: {{ english.is_composite }})</h2>
        {% if english.is_composite %}
        <p>English is composite with components:</p>
        <ul>
            {% for component in english_components %}
            <li>{{ component.name }} (ID: {{ component.id }}, Weight: {{ component.weight }})</li>
            {% endfor %}
        </ul>
        {% else %}
        <p>English is not composite.</p>
        {% endif %}
        
        <h2>Kiswahili (ID: {{ kiswahili.id }}, Is Composite: {{ kiswahili.is_composite }})</h2>
        {% if kiswahili.is_composite %}
        <p>Kiswahili is composite with components:</p>
        <ul>
            {% for component in kiswahili_components %}
            <li>{{ component.name }} (ID: {{ component.id }}, Weight: {{ component.weight }})</li>
            {% endfor %}
        </ul>
        {% else %}
        <p>Kiswahili is not composite.</p>
        {% endif %}
        
        <h2>Testing if condition</h2>
        <p>english.is_composite == True: {{ english.is_composite == True }}</p>
        <p>kiswahili.is_composite == True: {{ kiswahili.is_composite == True }}</p>
        <p>english.is_composite is True: {{ english.is_composite is True }}</p>
        <p>kiswahili.is_composite is True: {{ kiswahili.is_composite is True }}</p>
        """
        
        # Render the template
        rendered = render_template_string(
            template,
            english=english,
            english_components=english_components,
            kiswahili=kiswahili,
            kiswahili_components=kiswahili_components
        )
        
        print("\nRendered Template:")
        print(rendered)
        
        print("\nDebug completed.")

if __name__ == "__main__":
    debug_template()
