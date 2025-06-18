"""
Background Task Processing for Hillview School Management System
Implements async processing for resource-intensive operations
"""

import os
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from functools import wraps
import json
import threading
from queue import Queue, Empty
from concurrent.futures import ThreadPoolExecutor
import sqlite3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskStatus:
    """Task status constants"""
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'
    RETRY = 'retry'

class SimpleTaskQueue:
    """
    Simple in-memory task queue for background processing
    Falls back when Redis/Celery is not available
    """
    
    def __init__(self, max_workers: int = 4):
        self.queue = Queue()
        self.results = {}
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running = True
        self.workers = []
        self._start_workers()
        logger.info(f"✅ Simple task queue initialized with {max_workers} workers")
    
    def _start_workers(self):
        """Start background worker threads"""
        for i in range(self.max_workers):
            worker = threading.Thread(target=self._worker, daemon=True)
            worker.start()
            self.workers.append(worker)
    
    def _worker(self):
        """Worker thread function"""
        while self.running:
            try:
                task = self.queue.get(timeout=1)
                if task is None:
                    break
                
                task_id = task['id']
                self.results[task_id]['status'] = TaskStatus.RUNNING
                self.results[task_id]['started_at'] = datetime.now()
                
                try:
                    # Execute the task
                    func = task['func']
                    args = task.get('args', ())
                    kwargs = task.get('kwargs', {})
                    
                    result = func(*args, **kwargs)
                    
                    self.results[task_id].update({
                        'status': TaskStatus.SUCCESS,
                        'result': result,
                        'completed_at': datetime.now()
                    })
                    logger.info(f"✅ Task {task_id} completed successfully")
                    
                except Exception as e:
                    self.results[task_id].update({
                        'status': TaskStatus.FAILED,
                        'error': str(e),
                        'completed_at': datetime.now()
                    })
                    logger.error(f"❌ Task {task_id} failed: {e}")
                
                finally:
                    self.queue.task_done()
                    
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Worker error: {e}")
    
    def enqueue(self, func, *args, **kwargs) -> str:
        """
        Enqueue a task for background processing
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Task ID
        """
        task_id = f"task_{int(time.time() * 1000)}_{id(func)}"
        
        task = {
            'id': task_id,
            'func': func,
            'args': args,
            'kwargs': kwargs,
            'created_at': datetime.now()
        }
        
        self.results[task_id] = {
            'status': TaskStatus.PENDING,
            'created_at': datetime.now(),
            'task_name': func.__name__
        }
        
        self.queue.put(task)
        logger.info(f"📋 Task {task_id} ({func.__name__}) enqueued")
        return task_id
    
    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task result by ID"""
        return self.results.get(task_id)
    
    def get_status(self, task_id: str) -> Optional[str]:
        """Get task status by ID"""
        result = self.results.get(task_id)
        return result['status'] if result else None
    
    def cleanup_old_results(self, max_age_hours: int = 24):
        """Clean up old task results"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = []
        
        for task_id, result in self.results.items():
            if result.get('completed_at', result['created_at']) < cutoff:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.results[task_id]
        
        if to_remove:
            logger.info(f"🧹 Cleaned up {len(to_remove)} old task results")
    
    def shutdown(self):
        """Shutdown the task queue"""
        self.running = False
        for _ in self.workers:
            self.queue.put(None)
        self.executor.shutdown(wait=True)

# Global task queue instance
task_queue = SimpleTaskQueue()

def background_task(func):
    """
    Decorator to make a function run as a background task
    
    Usage:
        @background_task
        def generate_report(class_id, assessment_type):
            # Long-running task
            return result
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        return task_queue.enqueue(func, *args, **kwargs)
    
    # Add synchronous version
    wrapper.sync = func
    return wrapper

# Background task functions for school operations
@background_task
def generate_class_report(class_id: str, stream: str, assessment_type: str, 
                         user_id: str = None) -> Dict[str, Any]:
    """
    Generate comprehensive class report in background
    
    Args:
        class_id: Class identifier
        stream: Class stream
        assessment_type: Type of assessment
        user_id: User requesting the report
        
    Returns:
        Report generation result
    """
    logger.info(f"🔄 Generating report for class {class_id}-{stream}, assessment: {assessment_type}")
    
    try:
        # Import here to avoid circular imports
        from database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get students in the class
        cursor.execute(
            "SELECT * FROM students WHERE class = ? AND stream = ? ORDER BY name",
            (class_id, stream)
        )
        students = cursor.fetchall()
        
        # Get marks for the assessment
        marks_data = []
        for student in students:
            cursor.execute(
                """SELECT m.*, s.subject_name 
                   FROM marks m 
                   JOIN subjects s ON m.subject_id = s.id 
                   WHERE m.student_id = ? AND m.assessment_type = ?""",
                (student['id'], assessment_type)
            )
            student_marks = cursor.fetchall()
            marks_data.append({
                'student': dict(student),
                'marks': [dict(mark) for mark in student_marks]
            })
        
        conn.close()
        
        # Simulate report generation processing time
        time.sleep(2)  # Remove in production
        
        result = {
            'class_id': class_id,
            'stream': stream,
            'assessment_type': assessment_type,
            'student_count': len(students),
            'marks_count': sum(len(data['marks']) for data in marks_data),
            'generated_at': datetime.now().isoformat(),
            'generated_by': user_id,
            'report_data': marks_data
        }
        
        logger.info(f"✅ Report generated for {len(students)} students")
        return result
        
    except Exception as e:
        logger.error(f"❌ Report generation failed: {e}")
        raise

@background_task
def calculate_analytics(class_id: str = None, assessment_type: str = None) -> Dict[str, Any]:
    """
    Calculate comprehensive analytics in background
    
    Args:
        class_id: Specific class ID (optional)
        assessment_type: Specific assessment type (optional)
        
    Returns:
        Analytics calculation result
    """
    logger.info(f"🔄 Calculating analytics for class: {class_id}, assessment: {assessment_type}")
    
    try:
        from database import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query based on parameters
        where_conditions = []
        params = []
        
        if class_id:
            where_conditions.append("s.class = ?")
            params.append(class_id)
        
        if assessment_type:
            where_conditions.append("m.assessment_type = ?")
            params.append(assessment_type)
        
        where_clause = " AND ".join(where_conditions)
        if where_clause:
            where_clause = "WHERE " + where_clause
        
        # Calculate comprehensive analytics
        query = f"""
            SELECT 
                s.class,
                s.stream,
                m.assessment_type,
                sub.subject_name,
                COUNT(m.id) as total_marks,
                AVG(m.total_marks) as average_marks,
                MIN(m.total_marks) as min_marks,
                MAX(m.total_marks) as max_marks,
                COUNT(DISTINCT s.id) as student_count
            FROM students s
            JOIN marks m ON s.id = m.student_id
            JOIN subjects sub ON m.subject_id = sub.id
            {where_clause}
            GROUP BY s.class, s.stream, m.assessment_type, sub.subject_name
            ORDER BY s.class, s.stream, sub.subject_name
        """
        
        cursor.execute(query, params)
        analytics_data = cursor.fetchall()
        
        # Process analytics data
        processed_analytics = {}
        for row in analytics_data:
            class_key = f"{row['class']}-{row['stream']}"
            if class_key not in processed_analytics:
                processed_analytics[class_key] = {
                    'class': row['class'],
                    'stream': row['stream'],
                    'subjects': {},
                    'total_students': row['student_count']
                }
            
            subject_key = row['subject_name']
            processed_analytics[class_key]['subjects'][subject_key] = {
                'total_marks': row['total_marks'],
                'average_marks': round(row['average_marks'], 2),
                'min_marks': row['min_marks'],
                'max_marks': row['max_marks']
            }
        
        conn.close()
        
        # Simulate processing time
        time.sleep(1)  # Remove in production
        
        result = {
            'calculated_at': datetime.now().isoformat(),
            'class_count': len(processed_analytics),
            'analytics': processed_analytics
        }
        
        logger.info(f"✅ Analytics calculated for {len(processed_analytics)} classes")
        return result
        
    except Exception as e:
        logger.error(f"❌ Analytics calculation failed: {e}")
        raise

@background_task
def export_data(export_type: str, class_id: str = None, format: str = 'xlsx') -> Dict[str, Any]:
    """
    Export data in background
    
    Args:
        export_type: Type of data to export (students, marks, reports)
        class_id: Specific class ID (optional)
        format: Export format (xlsx, csv, pdf)
        
    Returns:
        Export result with file path
    """
    logger.info(f"🔄 Exporting {export_type} data for class: {class_id}, format: {format}")
    
    try:
        from database import get_db_connection
        import os
        
        # Create exports directory if it doesn't exist
        export_dir = os.path.join('static', 'exports')
        os.makedirs(export_dir, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{export_type}_{class_id or 'all'}_{timestamp}.{format}"
        filepath = os.path.join(export_dir, filename)
        
        # Simulate export processing
        time.sleep(3)  # Remove in production
        
        # Create dummy file for demonstration
        with open(filepath, 'w') as f:
            f.write(f"Export of {export_type} data\n")
            f.write(f"Generated at: {datetime.now()}\n")
            f.write(f"Class: {class_id or 'All'}\n")
            f.write(f"Format: {format}\n")
        
        result = {
            'export_type': export_type,
            'class_id': class_id,
            'format': format,
            'filename': filename,
            'filepath': filepath,
            'file_size': os.path.getsize(filepath),
            'exported_at': datetime.now().isoformat()
        }
        
        logger.info(f"✅ Data exported to {filename}")
        return result
        
    except Exception as e:
        logger.error(f"❌ Data export failed: {e}")
        raise

@background_task
def send_notification_email(recipient: str, subject: str, message: str) -> Dict[str, Any]:
    """
    Send notification email in background
    
    Args:
        recipient: Email recipient
        subject: Email subject
        message: Email message
        
    Returns:
        Email sending result
    """
    logger.info(f"📧 Sending email to {recipient}: {subject}")
    
    try:
        # Simulate email sending
        time.sleep(2)  # Remove in production
        
        # In production, integrate with actual email service
        # For now, just log the email
        logger.info(f"Email sent to {recipient}")
        
        result = {
            'recipient': recipient,
            'subject': subject,
            'sent_at': datetime.now().isoformat(),
            'status': 'sent'
        }
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Email sending failed: {e}")
        raise

def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
    """Get status of a background task"""
    return task_queue.get_result(task_id)

def cleanup_old_tasks():
    """Clean up old task results"""
    task_queue.cleanup_old_results()

# Periodic cleanup function
def start_periodic_cleanup():
    """Start periodic cleanup of old tasks"""
    def cleanup_worker():
        while True:
            time.sleep(3600)  # Run every hour
            cleanup_old_tasks()
    
    cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    cleanup_thread.start()
    logger.info("🧹 Started periodic task cleanup")

# Initialize periodic cleanup
start_periodic_cleanup()

if __name__ == "__main__":
    # Test background tasks
    print("Testing background task system...")
    
    # Test report generation
    task_id = generate_class_report("Grade 1", "A", "CAT 1", "test_user")
    print(f"Report generation task ID: {task_id}")
    
    # Wait and check status
    time.sleep(3)
    result = get_task_status(task_id)
    print(f"Task result: {result}")
    
    # Test analytics calculation
    analytics_task_id = calculate_analytics()
    print(f"Analytics task ID: {analytics_task_id}")
    
    # Shutdown
    task_queue.shutdown()
