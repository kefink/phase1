#!/usr/bin/env python3
"""
Setup default assessment types in the database
"""
import sys
import os
sys.path.append('.')

from flask import Flask
from models.academic import AssessmentType
from extensions import db
from config import Config

def setup_assessment_types():
    """Create default assessment types if they don't exist"""
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    
    with app.app_context():
        print('Checking assessment types in database...')
        
        # Check if any assessment types exist
        existing_count = AssessmentType.query.count()
        print(f'Found {existing_count} existing assessment types')
        
        if existing_count == 0:
            print('Creating default assessment types...')
            defaults = [
                {'name': 'CAT 1', 'weight': 15.0, 'category': 'Continuous Assessment'},
                {'name': 'CAT 2', 'weight': 15.0, 'category': 'Continuous Assessment'},
                {'name': 'End Term Exam', 'weight': 70.0, 'category': 'Examinations'}
            ]
            
            for default in defaults:
                assessment = AssessmentType(
                    name=default['name'],
                    weight=default['weight'],
                    category=default['category'],
                    is_active=True
                )
                db.session.add(assessment)
                print(f"Added: {default['name']}")
            
            db.session.commit()
            print('✅ Default assessment types created successfully!')
        else:
            print('Assessment types already exist:')
            assessments = AssessmentType.query.all()
            for a in assessments:
                print(f'  - ID: {a.id}, Name: {a.name}, Weight: {a.weight}%, Active: {a.is_active}')

if __name__ == '__main__':
    setup_assessment_types()
