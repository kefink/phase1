#!/usr/bin/env python3
"""Debug script to test streams functionality."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'new_structure'))

from new_structure.models.academic import Grade, Stream
from new_structure.extensions import db
import json

# Check if we can import the Flask app
try:
    from new_structure import create_app
    app = create_app()
    
    with app.app_context():
        print("=" * 50)
        print("STREAMS DEBUGGING")
        print("=" * 50)
        
        # Test 1: Check all grades and their IDs
        print("\n1. GRADES AND IDS:")
        grades = Grade.query.all()
        for grade in grades:
            print(f"   ID: {grade.id}, Name: '{grade.name}'")
        
        # Test 2: Check all streams for each grade
        print("\n2. STREAMS BY GRADE:")
        for grade in grades:
            streams = Stream.query.filter_by(grade_id=grade.id).all()
            print(f"   Grade {grade.name} (ID: {grade.id}):")
            for stream in streams:
                print(f"      - Stream ID: {stream.id}, Name: '{stream.name}'")
        
        # Test 3: Simulate grade mapping (what the API should return)
        print("\n3. GRADE MAPPING (what API should return):")
        grade_mapping = {grade.name: grade.id for grade in grades}
        print(json.dumps(grade_mapping, indent=2))
        
        # Test 4: Test specific grade ID lookups
        print("\n4. TESTING SPECIFIC LOOKUPS:")
        test_grades = ["Grade 1", "Grade 7", "Grade 8"]
        for grade_name in test_grades:
            grade = Grade.query.filter_by(name=grade_name).first()
            if grade:
                streams = Stream.query.filter_by(grade_id=grade.id).all()
                stream_data = [{'id': stream.id, 'name': stream.name} for stream in streams]
                print(f"   {grade_name} (ID: {grade.id}) -> {len(streams)} streams: {stream_data}")
        
        print("\n" + "=" * 50)
        print("DEBUG COMPLETE")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()