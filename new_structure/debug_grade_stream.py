#!/usr/bin/env python3
"""
Debug script to check grade-stream relationships in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extensions import db
from models.academic import Grade, Stream
from run import create_app

def debug_grade_stream_relationships():
    """Debug grade-stream relationships"""
    app = create_app()
    
    with app.app_context():
        print("🔍 DEBUG: Grade-Stream Relationship Analysis")
        print("=" * 50)
        
        # Get all grades
        grades = Grade.query.all()
        print(f"\n📚 All Grades ({len(grades)}):")
        for grade in grades:
            print(f"  - Grade ID: {grade.id}, Name: '{grade.name}'")
        
        # Get all streams
        streams = Stream.query.all()
        print(f"\n🏛️ All Streams ({len(streams)}):")
        for stream in streams:
            print(f"  - Stream ID: {stream.id}, Name: '{stream.name}', Grade ID: {stream.grade_id}")
        
        # Check specific problematic IDs
        print(f"\n🔍 Checking specific IDs:")
        
        # Check Grade ID 21
        grade_21 = Grade.query.get(21)
        if grade_21:
            print(f"✅ Grade ID 21 exists: '{grade_21.name}'")
            # Get streams for this grade
            streams_for_grade_21 = Stream.query.filter_by(grade_id=21).all()
            print(f"📋 Streams for Grade ID 21 ({len(streams_for_grade_21)}):")
            for stream in streams_for_grade_21:
                print(f"    - Stream ID: {stream.id}, Name: '{stream.name}'")
        else:
            print(f"❌ Grade ID 21 NOT FOUND")
        
        # Check Stream ID 44
        stream_44 = Stream.query.get(44)
        if stream_44:
            print(f"✅ Stream ID 44 exists: '{stream_44.name}', belongs to Grade ID: {stream_44.grade_id}")
            # Get the grade for this stream
            grade_for_stream_44 = Grade.query.get(stream_44.grade_id)
            if grade_for_stream_44:
                print(f"📚 Stream 44 belongs to Grade: '{grade_for_stream_44.name}' (ID: {grade_for_stream_44.id})")
            else:
                print(f"❌ Grade ID {stream_44.grade_id} for Stream 44 NOT FOUND")
        else:
            print(f"❌ Stream ID 44 NOT FOUND")
        
        # Check Grade 9 (which was selected in the form)
        print(f"\n🔍 Checking Grade 9:")
        grade_9 = Grade.query.filter_by(name='Grade 9').first()
        if grade_9:
            print(f"✅ Grade 9 exists: ID {grade_9.id}")
            streams_for_grade_9 = Stream.query.filter_by(grade_id=grade_9.id).all()
            print(f"📋 Streams for Grade 9 ({len(streams_for_grade_9)}):")
            for stream in streams_for_grade_9:
                print(f"    - Stream ID: {stream.id}, Name: '{stream.name}'")
        else:
            print(f"❌ Grade 9 NOT FOUND")
        
        print("\n" + "=" * 50)
        print("🎯 ANALYSIS COMPLETE")

if __name__ == "__main__":
    debug_grade_stream_relationships()
