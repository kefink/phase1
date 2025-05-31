"""
Enhanced Grade Report Generation Service
Handles multiple streams and generates both individual stream reports and consolidated grade reports.
"""
from ..models.academic import Grade, Stream, Subject, Term, AssessmentType, Student, Mark
from ..models.user import Teacher
from ..models.assignment import TeacherSubjectAssignment
from ..extensions import db
from ..services import get_class_report_data
from ..services.report_service import generate_class_report_pdf_from_html
from ..services.staff_assignment_service import StaffAssignmentService
import os
import tempfile
import zipfile
from datetime import datetime
from flask import render_template_string


class GradeReportService:
    """Service for generating comprehensive grade-level reports with multiple streams."""

    @staticmethod
    def get_grade_streams_status(grade_name, term, assessment_type):
        """
        Get the status of all streams in a grade for report generation.

        Returns:
            dict: Status information for each stream in the grade
        """
        try:
            # Get grade object
            grade = Grade.query.filter_by(name=grade_name).first()
            if not grade:
                return {"error": "Grade not found"}

            # Get all streams for this grade
            streams = Stream.query.filter_by(grade_id=grade.id).order_by(Stream.name).all()

            if not streams:
                return {"error": "No streams found for this grade"}

            # Get term and assessment type objects
            term_obj = Term.query.filter_by(name=term).first()
            assessment_type_obj = AssessmentType.query.filter_by(name=assessment_type).first()

            if not (term_obj and assessment_type_obj):
                return {"error": "Invalid term or assessment type"}

            grade_data = {
                'grade': grade_name,
                'term': term,
                'assessment_type': assessment_type,
                'streams': [],
                'total_streams': len(streams),
                'streams_with_marks': 0,
                'total_students': 0,
                'students_with_marks': 0,
                'can_generate_reports': False
            }

            for stream in streams:
                # Get students in this stream
                students = Student.query.filter_by(stream_id=stream.id).all()
                total_students = len(students)

                # Check if stream has marks
                students_with_marks = 0
                if students:
                    # Count students who have at least one mark for this term/assessment
                    students_with_marks = db.session.query(Student.id).join(Mark).filter(
                        Student.stream_id == stream.id,
                        Mark.term_id == term_obj.id,
                        Mark.assessment_type_id == assessment_type_obj.id
                    ).distinct().count()

                has_marks = students_with_marks > 0
                completion_percentage = (students_with_marks / total_students * 100) if total_students > 0 else 0

                stream_info = {
                    'id': stream.id,
                    'name': stream.name,
                    'display_name': f"Stream {stream.name}",
                    'total_students': total_students,
                    'students_with_marks': students_with_marks,
                    'completion_percentage': completion_percentage,
                    'has_marks': has_marks,
                    'can_generate_report': has_marks and completion_percentage >= 50  # At least 50% completion
                }

                grade_data['streams'].append(stream_info)
                grade_data['total_students'] += total_students
                grade_data['students_with_marks'] += students_with_marks

                if has_marks:
                    grade_data['streams_with_marks'] += 1

            # Determine if grade-level reports can be generated
            grade_data['can_generate_reports'] = grade_data['streams_with_marks'] > 0
            grade_data['overall_completion'] = (grade_data['students_with_marks'] / grade_data['total_students'] * 100) if grade_data['total_students'] > 0 else 0

            return grade_data

        except Exception as e:
            print(f"Error getting grade streams status: {str(e)}")
            return {"error": str(e)}

    @staticmethod
    def generate_individual_stream_report(grade_name, stream_name, term, assessment_type):
        """
        Generate a report for a single stream.

        Returns:
            str: Path to generated PDF file or None if failed
        """
        try:
            # Use existing class report generation
            from ..services import get_class_report_data

            # Get class report data
            class_data = get_class_report_data(grade_name, f"Stream {stream_name}", term, assessment_type)

            if class_data.get("error"):
                print(f"Error getting class data: {class_data['error']}")
                return None

            # Get staff information
            staff_info = StaffAssignmentService.get_report_staff_info(grade_name, f"Stream {stream_name}")

            # Generate PDF using existing service
            pdf_file = generate_class_report_pdf_from_html(
                grade_name,
                f"Stream {stream_name}",
                term,
                assessment_type,
                class_data["class_data"],
                class_data["stats"],
                class_data["total_marks"],
                class_data["subjects"],
                class_data.get("education_level", ""),
                class_data.get("subject_averages", {}),
                class_data.get("class_average", 0),
                staff_info=staff_info
            )

            return pdf_file

        except Exception as e:
            print(f"Error generating individual stream report: {str(e)}")
            return None

    @staticmethod
    def generate_consolidated_grade_report(grade_name, term, assessment_type, selected_streams=None):
        """
        Generate a consolidated report for an entire grade combining all streams.

        Args:
            grade_name: Name of the grade
            term: Term name
            assessment_type: Assessment type name
            selected_streams: List of stream names to include (None for all)

        Returns:
            str: Path to generated PDF file or None if failed
        """
        try:
            # Get grade streams status
            grade_status = GradeReportService.get_grade_streams_status(grade_name, term, assessment_type)

            if 'error' in grade_status:
                print(f"Error getting grade status: {grade_status['error']}")
                return None

            # Filter streams if specific ones are selected
            streams_to_include = grade_status['streams']
            if selected_streams:
                streams_to_include = [s for s in streams_to_include if s['name'] in selected_streams]

            # Only include streams that have marks
            streams_with_marks = [s for s in streams_to_include if s['has_marks']]

            if not streams_with_marks:
                print("No streams with marks found for consolidated report")
                return None

            # Collect data from all streams
            consolidated_data = {
                'grade': grade_name,
                'term': term,
                'assessment_type': assessment_type,
                'streams': [],
                'all_students': [],
                'subjects': set(),
                'total_students': 0,
                'grade_statistics': {}
            }

            # Process each stream
            for stream_info in streams_with_marks:
                stream_name = stream_info['name']

                # Get class report data for this stream
                class_data = get_class_report_data(grade_name, f"Stream {stream_name}", term, assessment_type)

                if not class_data.get("error"):
                    stream_data = {
                        'name': stream_name,
                        'display_name': f"Stream {stream_name}",
                        'students': class_data["class_data"],
                        'stats': class_data["stats"],
                        'subjects': class_data["subjects"],
                        'class_average': class_data.get("class_average", 0),
                        'total_students': len(class_data["class_data"])
                    }

                    consolidated_data['streams'].append(stream_data)
                    consolidated_data['all_students'].extend(class_data["class_data"])
                    consolidated_data['subjects'].update(class_data["subjects"])
                    consolidated_data['total_students'] += len(class_data["class_data"])

            # Convert subjects set to list
            consolidated_data['subjects'] = list(consolidated_data['subjects'])

            # Calculate grade-level statistics
            consolidated_data['grade_statistics'] = GradeReportService._calculate_grade_statistics(consolidated_data)

            # Generate consolidated PDF
            pdf_file = GradeReportService._generate_consolidated_pdf(consolidated_data)

            return pdf_file

        except Exception as e:
            print(f"Error generating consolidated grade report: {str(e)}")
            return None

    @staticmethod
    def _calculate_grade_statistics(consolidated_data):
        """Calculate statistics for the entire grade."""
        try:
            stats = {
                'total_students': consolidated_data['total_students'],
                'total_streams': len(consolidated_data['streams']),
                'subjects': consolidated_data['subjects'],
                'subject_averages': {},
                'grade_average': 0,
                'stream_averages': {},
                'top_performers': [],
                'subject_performance': {}
            }

            if not consolidated_data['all_students']:
                return stats

            # Calculate subject averages across all streams
            for subject in consolidated_data['subjects']:
                subject_marks = []
                for student in consolidated_data['all_students']:
                    if subject in student.get('marks', {}):
                        mark = student['marks'][subject]
                        if mark and mark > 0:
                            subject_marks.append(mark)

                if subject_marks:
                    stats['subject_averages'][subject] = round(sum(subject_marks) / len(subject_marks), 2)

            # Calculate overall grade average
            all_averages = [student.get('average_percentage', 0) for student in consolidated_data['all_students']]
            if all_averages:
                stats['grade_average'] = round(sum(all_averages) / len(all_averages), 2)

            # Calculate stream averages
            for stream in consolidated_data['streams']:
                stream_averages = [student.get('average_percentage', 0) for student in stream['students']]
                if stream_averages:
                    stats['stream_averages'][stream['name']] = round(sum(stream_averages) / len(stream_averages), 2)

            # Find top performers (top 10% or minimum 5 students)
            sorted_students = sorted(
                consolidated_data['all_students'],
                key=lambda x: x.get('average_percentage', 0),
                reverse=True
            )
            top_count = max(5, len(sorted_students) // 10)  # Top 10% or minimum 5
            stats['top_performers'] = sorted_students[:top_count]

            return stats

        except Exception as e:
            print(f"Error calculating grade statistics: {str(e)}")
            return {}

    @staticmethod
    def _generate_consolidated_pdf(consolidated_data):
        """Generate PDF for consolidated grade report."""
        try:
            # Create HTML content for the consolidated report
            html_template = GradeReportService._get_consolidated_report_template()

            # Render the template
            html_content = render_template_string(
                html_template,
                **consolidated_data
            )

            # Generate PDF
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Grade_{consolidated_data['grade']}_Consolidated_Report_{consolidated_data['term']}_{consolidated_data['assessment_type']}_{timestamp}.pdf"
            temp_dir = tempfile.gettempdir()
            pdf_path = os.path.join(temp_dir, filename)

            # Use pdfkit to generate PDF
            try:
                import pdfkit
                options = {
                    'page-size': 'A4',
                    'orientation': 'Portrait',
                    'margin-top': '0.75in',
                    'margin-right': '0.75in',
                    'margin-bottom': '0.75in',
                    'margin-left': '0.75in',
                    'encoding': 'UTF-8',
                    'no-outline': None,
                    'enable-local-file-access': True
                }
                pdfkit.from_string(html_content, pdf_path, options=options)
                return pdf_path
            except Exception as e:
                print(f"PDF generation failed: {e}")
                return None

        except Exception as e:
            print(f"Error generating consolidated PDF: {str(e)}")
            return None

    @staticmethod
    def generate_batch_grade_reports(grade_name, term, assessment_type, include_individual=True, include_consolidated=True, selected_streams=None):
        """
        Generate batch reports for a grade including individual stream reports and consolidated report.

        Args:
            grade_name: Name of the grade
            term: Term name
            assessment_type: Assessment type name
            include_individual: Whether to include individual stream reports
            include_consolidated: Whether to include consolidated grade report
            selected_streams: List of stream names to include (None for all)

        Returns:
            str: Path to ZIP file containing all reports or None if failed
        """
        try:
            # Get grade streams status
            grade_status = GradeReportService.get_grade_streams_status(grade_name, term, assessment_type)

            if 'error' in grade_status:
                print(f"Error getting grade status: {grade_status['error']}")
                return None

            # Filter streams if specific ones are selected
            streams_to_include = grade_status['streams']
            if selected_streams:
                streams_to_include = [s for s in streams_to_include if s['name'] in selected_streams]

            # Only include streams that have marks
            streams_with_marks = [s for s in streams_to_include if s['has_marks']]

            if not streams_with_marks:
                print("No streams with marks found for batch report generation")
                return None

            # Create ZIP file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"Grade_{grade_name}_Reports_{term}_{assessment_type}_{timestamp}.zip"
            temp_dir = tempfile.gettempdir()
            zip_path = os.path.join(temp_dir, zip_filename)

            successful_reports = 0
            failed_reports = 0

            with zipfile.ZipFile(zip_path, 'w') as zipf:
                # Generate individual stream reports
                if include_individual:
                    for stream_info in streams_with_marks:
                        try:
                            stream_name = stream_info['name']
                            print(f"📄 Generating report for Stream {stream_name}...")

                            pdf_file = GradeReportService.generate_individual_stream_report(
                                grade_name, stream_name, term, assessment_type
                            )

                            if pdf_file and os.path.exists(pdf_file):
                                report_filename = f"Stream_{stream_name}_Report.pdf"
                                zipf.write(pdf_file, report_filename)
                                successful_reports += 1
                                print(f"✅ Generated report for Stream {stream_name}")

                                # Clean up individual file
                                try:
                                    os.remove(pdf_file)
                                except:
                                    pass
                            else:
                                failed_reports += 1
                                print(f"⚠️ Failed to generate report for Stream {stream_name}")

                        except Exception as e:
                            failed_reports += 1
                            print(f"❌ Error generating report for Stream {stream_name}: {str(e)}")

                # Generate consolidated grade report
                if include_consolidated:
                    try:
                        print(f"📊 Generating consolidated grade report...")

                        consolidated_pdf = GradeReportService.generate_consolidated_grade_report(
                            grade_name, term, assessment_type, [s['name'] for s in streams_with_marks]
                        )

                        if consolidated_pdf and os.path.exists(consolidated_pdf):
                            consolidated_filename = f"Grade_{grade_name}_Consolidated_Report.pdf"
                            zipf.write(consolidated_pdf, consolidated_filename)
                            successful_reports += 1
                            print(f"✅ Generated consolidated grade report")

                            # Clean up consolidated file
                            try:
                                os.remove(consolidated_pdf)
                            except:
                                pass
                        else:
                            failed_reports += 1
                            print(f"⚠️ Failed to generate consolidated grade report")

                    except Exception as e:
                        failed_reports += 1
                        print(f"❌ Error generating consolidated report: {str(e)}")

            print(f"📊 Batch generation complete: {successful_reports} successful, {failed_reports} failed")

            if successful_reports == 0:
                return None

            return zip_path

        except Exception as e:
            print(f"Error generating batch grade reports: {str(e)}")
            return None

    @staticmethod
    def _get_consolidated_report_template():
        """Get HTML template for consolidated grade report."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Grade {{ grade }} Consolidated Report</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .report-container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 20px;
        }
        .school-name {
            font-size: 24px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }
        .report-title {
            font-size: 20px;
            color: #34495e;
            margin-bottom: 10px;
        }
        .report-details {
            font-size: 14px;
            color: #7f8c8d;
        }
        .summary-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .summary-card {
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .summary-number {
            font-size: 28px;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .summary-label {
            font-size: 14px;
            opacity: 0.9;
        }
        .streams-section {
            margin-bottom: 30px;
        }
        .section-title {
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 15px;
            border-bottom: 2px solid #ecf0f1;
            padding-bottom: 5px;
        }
        .streams-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .stream-card {
            border: 1px solid #bdc3c7;
            border-radius: 8px;
            padding: 15px;
            background: #f8f9fa;
        }
        .stream-header {
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }
        .stream-stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            font-size: 14px;
        }
        .stat-item {
            display: flex;
            justify-content: space-between;
        }
        .subjects-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }
        .subjects-table th,
        .subjects-table td {
            border: 1px solid #bdc3c7;
            padding: 8px;
            text-align: center;
        }
        .subjects-table th {
            background: #34495e;
            color: white;
            font-weight: bold;
        }
        .subjects-table tr:nth-child(even) {
            background: #f8f9fa;
        }
        .top-performers {
            margin-top: 20px;
        }
        .performers-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        .performer-card {
            background: linear-gradient(135deg, #27ae60, #229954);
            color: white;
            padding: 15px;
            border-radius: 8px;
        }
        .performer-name {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .performer-details {
            font-size: 14px;
            opacity: 0.9;
        }
        @media print {
            body { background: white; }
            .report-container { box-shadow: none; }
        }
    </style>
</head>
<body>
    <div class="report-container">
        <div class="header">
            <div class="school-name">KIRIMA PRIMARY SCHOOL</div>
            <div class="report-title">Grade {{ grade }} Consolidated Report</div>
            <div class="report-details">
                {{ term }} - {{ assessment_type }} - Academic Year {{ "2024" }}
                <br>Generated on {{ moment().format('MMMM Do YYYY, h:mm:ss a') }}
            </div>
        </div>

        <div class="summary-section">
            <div class="summary-card">
                <div class="summary-number">{{ grade_statistics.total_students }}</div>
                <div class="summary-label">Total Students</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{{ grade_statistics.total_streams }}</div>
                <div class="summary-label">Streams</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{{ "%.1f"|format(grade_statistics.grade_average) }}%</div>
                <div class="summary-label">Grade Average</div>
            </div>
            <div class="summary-card">
                <div class="summary-number">{{ grade_statistics.subjects|length }}</div>
                <div class="summary-label">Subjects</div>
            </div>
        </div>

        <div class="streams-section">
            <div class="section-title">Stream Performance Overview</div>
            <div class="streams-grid">
                {% for stream in streams %}
                <div class="stream-card">
                    <div class="stream-header">{{ stream.display_name }}</div>
                    <div class="stream-stats">
                        <div class="stat-item">
                            <span>Students:</span>
                            <span>{{ stream.total_students }}</span>
                        </div>
                        <div class="stat-item">
                            <span>Average:</span>
                            <span>{{ "%.1f"|format(grade_statistics.stream_averages.get(stream.name, 0)) }}%</span>
                        </div>
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>

        <div class="subjects-section">
            <div class="section-title">Subject Performance Analysis</div>
            <table class="subjects-table">
                <thead>
                    <tr>
                        <th>Subject</th>
                        <th>Grade Average</th>
                        {% for stream in streams %}
                        <th>{{ stream.display_name }}</th>
                        {% endfor %}
                    </tr>
                </thead>
                <tbody>
                    {% for subject in subjects %}
                    <tr>
                        <td><strong>{{ subject }}</strong></td>
                        <td>{{ "%.1f"|format(grade_statistics.subject_averages.get(subject, 0)) }}%</td>
                        {% for stream in streams %}
                        <td>
                            {% set stream_avg = stream.stats.subject_averages.get(subject, 0) %}
                            {{ "%.1f"|format(stream_avg) }}%
                        </td>
                        {% endfor %}
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>

        <div class="top-performers">
            <div class="section-title">Top Performers (Grade {{ grade }})</div>
            <div class="performers-list">
                {% for performer in grade_statistics.top_performers[:10] %}
                <div class="performer-card">
                    <div class="performer-name">{{ performer.student }}</div>
                    <div class="performer-details">
                        Average: {{ "%.1f"|format(performer.average_percentage) }}%
                        | Total: {{ performer.total_marks }}/{{ performer.total_possible_marks }}
                    </div>
                </div>
                {% endfor %}
            </div>
        </div>
    </div>
</body>
</html>
        """
