#!/usr/bin/env python3
"""
Generate Sample CSV
-----------------
Generates a sample CSV file with course data showing varying complexities.
"""

import pandas as pd
import numpy as np
import random
from pathlib import Path

def generate_course_data():
    """
    Generate a realistic sample dataset with varying course complexities.
    
    Returns:
        pd.DataFrame: Generated dataset
    """
    # Define courses with varying complexity characteristics
    courses = {
        'CS101': {
            'name': 'Introduction to Programming',
            'base_difficulty': 30,  # Easy
            'unit_variance': 10,    # Units are similarly challenging
            'time_base': 40,        # Base time in minutes for units
            'student_variance': 0.4  # High variance in student abilities (beginners)
        },
        'CS201': {
            'name': 'Data Structures',
            'base_difficulty': 65,  # Moderately challenging
            'unit_variance': 20,    # Some units much harder than others
            'time_base': 60,
            'student_variance': 0.3
        },
        'CS301': {
            'name': 'Algorithms',
            'base_difficulty': 85,  # Very challenging
            'unit_variance': 15,
            'time_base': 90,
            'student_variance': 0.25  # Lower variance (more advanced students)
        },
        'MATH101': {
            'name': 'College Algebra',
            'base_difficulty': 45,  # Moderate
            'unit_variance': 25,    # Some topics much more challenging
            'time_base': 50,
            'student_variance': 0.5  # High variance (mix of math abilities)
        },
        'PHYS201': {
            'name': 'Classical Mechanics',
            'base_difficulty': 75,  # Challenging
            'unit_variance': 15,
            'time_base': 70,
            'student_variance': 0.35
        }
    }
    
    # Define teachers with different teaching styles
    teachers = {
        'Smith': {'efficiency': 0.9, 'consistency': 0.85},  # Very good teacher
        'Johnson': {'efficiency': 1.1, 'consistency': 0.7},  # Average teacher
        'Williams': {'efficiency': 1.2, 'consistency': 0.6},  # Less effective teacher
        'Davis': {'efficiency': 0.95, 'consistency': 0.9},  # Good and consistent
        'Miller': {'efficiency': 1.0, 'consistency': 0.8}   # Average across the board
    }
    
    # Set up units - different number for different courses
    units_per_course = {
        'CS101': 5,
        'CS201': 6,
        'CS301': 7,
        'MATH101': 6,
        'PHYS201': 8
    }
    
    # Number of students per course
    students_per_course = {
        'CS101': 35,  # Intro course, more students
        'CS201': 28,
        'CS301': 20,  # Advanced course, fewer students
        'MATH101': 40,
        'PHYS201': 25
    }
    
    # Student academic profiles to make the data more realistic
    # Each group has its own performance characteristics
    student_profiles = [
        {'name': 'high_performer', 'factor': 0.7, 'weight': 0.2},  # 20% are high performers
        {'name': 'average', 'factor': 1.0, 'weight': 0.6},         # 60% are average
        {'name': 'struggling', 'factor': 1.4, 'weight': 0.15},     # 15% are struggling
        {'name': 'inconsistent', 'factor': 1.1, 'variance': 0.5, 'weight': 0.05}  # 5% are highly variable
    ]
    
    # Generate data
    data = []
    student_id_counter = 1000
    
    for course_id, course_info in courses.items():
        num_units = units_per_course[course_id]
        num_students = students_per_course[course_id]
        base_difficulty = course_info['base_difficulty']
        
        # Determine unit difficulties for this course
        unit_difficulties = []
        for i in range(num_units):
            # Create a difficulty curve that typically increases
            progression_factor = (i / (num_units - 1)) * 0.4 + 0.8  # 0.8 to 1.2 as units progress
            
            # Some randomness in unit difficulty
            unit_variance = random.uniform(-course_info['unit_variance'], course_info['unit_variance'])
            
            # Calculate unit difficulty
            unit_diff = base_difficulty * progression_factor + unit_variance
            unit_diff = max(20, min(95, unit_diff))  # Cap between 20-95
            
            unit_difficulties.append(unit_diff)
        
        # Assign teachers to this course (2-3 teachers per course)
        num_teachers = random.randint(2, 3)
        course_teachers = random.sample(list(teachers.keys()), num_teachers)
        
        # Create students and their performance
        for i in range(num_students):
            student_id = f"S{student_id_counter}"
            student_id_counter += 1
            
            # Randomly assign a teacher
            teacher_name = random.choice(course_teachers)
            teacher = teachers[teacher_name]
            
            # Determine student profile based on weighted probabilities
            profile = random.choices(
                population=[p['name'] for p in student_profiles],
                weights=[p['weight'] for p in student_profiles],
                k=1
            )[0]
            
            # Find the profile data
            profile_data = next(p for p in student_profiles if p['name'] == profile)
            
            # Base performance factor for this student
            student_factor = profile_data['factor']
            
            # Add some individual variation to the student
            student_variation = random.uniform(
                1 - course_info['student_variance'],
                1 + course_info['student_variance']
            )
            
            student_factor *= student_variation
            
            # Generate unit completion times
            unit_times = {}
            for j, unit_diff in enumerate(unit_difficulties):
                # Base time based on difficulty (minutes)
                base_time = unit_diff * (course_info['time_base'] / 50)  # Normalize to a reasonable time
                
                # Teacher influence
                teacher_effect = teacher['efficiency']
                
                # Add unit-specific variation (some students do better on certain units)
                unit_variation = random.uniform(
                    1 - (1 - teacher['consistency']), 
                    1 + (1 - teacher['consistency'])
                )
                
                # Calculate final time
                if profile == 'inconsistent':
                    # Inconsistent students have higher variance between units
                    extra_variance = random.uniform(
                        1 - profile_data.get('variance', 0),
                        1 + profile_data.get('variance', 0)
                    )
                    unit_variation *= extra_variance
                
                # Final time calculation
                time = base_time * student_factor * teacher_effect * unit_variation
                time = max(10, time)  # Minimum 10 minutes
                
                unit_times[f"unit{j+1}_time"] = round(time, 1)
            
            # Create student record
            student_record = {
                'course_number': course_id,
                'course_name': course_info['name'],
                'teacher_name': teacher_name,
                'student_id': student_id,
                **unit_times
            }
            
            data.append(student_record)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Remove course_name column to match expected format
    df = df.drop('course_name', axis=1)
    
    return df


def save_course_data(output_path='course_complexity_data.csv'):
    """Generate and save the course data to CSV"""
    df = generate_course_data()
    
    # Create directory if it doesn't exist
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    
    print(f"Sample course data generated and saved to {output_file}")
    print(f"Generated {len(df)} student records")
    print(f"Courses: {df['course_number'].nunique()}")
    print(f"Teachers: {df['teacher_name'].nunique()}")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    for course in df['course_number'].unique():
        course_df = df[df['course_number'] == course]
        
        # Get unit time columns
        unit_cols = [col for col in course_df.columns if col.startswith('unit') and col.endswith('_time')]
        
        # Calculate average time per unit
        unit_means = {unit: course_df[unit].mean() for unit in unit_cols}
        
        print(f"\n{course}:")
        print(f"  Students: {len(course_df)}")
        print(f"  Teachers: {course_df['teacher_name'].nunique()}")
        print(f"  Units: {len(unit_cols)}")
        print(f"  Average unit times (minutes):")
        for unit, mean_time in unit_means.items():
            print(f"    {unit}: {mean_time:.1f}")
    
    return output_file


if __name__ == "__main__":
    save_course_data()
