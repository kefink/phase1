"""
Fix Component Weights
Update component weights to proper proportions
"""

import pymysql

def fix_component_weights():
    """Fix component weights to be proper proportions."""
    try:
        connection = pymysql.connect(
            host='localhost',
            port=3306,
            user='root',
            password='@2494/lK',
            database='hillview_demo001'
        )
        cursor = connection.cursor()
        
        print('🔧 Fixing component weights...')
        
        # Update all component weights to 0.5 (50% each)
        cursor.execute('UPDATE subject_component SET weight = 0.5')
        updated = cursor.rowcount
        print(f'✅ Updated {updated} component weights to 0.5')
        
        # Update max_raw_mark to 50 for proper distribution
        cursor.execute('UPDATE subject_component SET max_raw_mark = 50')
        updated_marks = cursor.rowcount
        print(f'✅ Updated {updated_marks} component max marks to 50')
        
        connection.commit()
        
        # Verify
        cursor.execute('SELECT name, weight, max_raw_mark FROM subject_component ORDER BY name')
        components = cursor.fetchall()
        print('\nComponent weights:')
        for name, weight, max_mark in components:
            print(f'  - {name}: weight={weight}, max_mark={max_mark}')
        
        connection.close()
        print('\n✅ Component weights fixed!')
        return True
        
    except Exception as e:
        print(f'❌ Error: {e}')
        return False

if __name__ == '__main__':
    fix_component_weights()
