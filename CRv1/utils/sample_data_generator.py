"""
Sample Data Generator
-------------------
Generates sample course data for testing the application.
"""

import pandas as pd
import numpy as np
import random
from pathlib import Path


def generate_sample_data(num_courses=3, num_students=30, num_units=5, num_teachers=2):
    """
    Generate sample course data for testing.
    
    Args:
        num_courses (int): Number of courses to generate
        num_students (int): Number of students per course
        num_units (int): Number of units per course
        num_teachers (int): Number of teachers per course
        
    Returns:
        pd.DataFrame: Generated data
    """
    # Define course difficulty levels
    course_difficulties = {
        'CS101': 30,  # Easy
        'CS201': 60,  # Moderate
        'CS301': 80,  # Challenging
        'MATH101': 40,  # Moderate-Easy
        'MATH201': 70,  # Challenging
        'PHYS101': 50,  # Moderate
    }
    
    # Use a subset of courses
    courses = list(course_difficulties.keys())[:num_courses]
    
    # Generate teacher names
    first_names = ['John', 'Sarah', 'Michael', 'Emma', 'David', 'Maria', 'Robert', 'Jennifer']
    teachers = random.sample(first_names, min(num_teachers, len(first_names)))
    
    # Generate data
    data = []
    
    for course in courses:
        base_difficulty = course_difficulties[course]
        
        # Generate different unit difficulties
        unit_difficulties = [
            max(10, min(100, base_difficulty + random.randint(-20, 20)))
            for _ in range(num_units)
        ]
        
        # Generate student data
        for i in range(num_students):
            student_id = f"S{1000 + i}"
            
            # Randomly assign a teacher
            teacher = random.choice(teachers)
            
            # Generate student-specific variation factor (some students are faster, some slower)
            student_factor = random.uniform(0.7, 1.3)
            
            # Generate unit completion times
            unit_times = {}
            for j, unit_diff in enumerate(unit_difficulties):
                # Base time based on difficulty (minutes)
                base_time = unit_diff * 1.5
                
                # Add variation
                variation = random.uniform(0.8, 1.2)
                
                # Final time calculation
                time = base_time * student_factor * variation
                
                unit_times[f"unit{j+1}_time"] = round(time, 1)
            
            # Create student record
            student_record = {
                'course_number': course,
                'teacher_name': teacher,
                'student_id': student_id,
                **unit_times
            }
            
            data.append(student_record)
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    return df


def save_sample_data(output_path='sample_course_data.csv', **kwargs):
    """
    Generate and save sample data to a CSV file.
    
    Args:
        output_path (str): Path to save the CSV file
        **kwargs: Arguments to pass to generate_sample_data()
        
    Returns:
        Path: Path to the saved file
    """
    df = generate_sample_data(**kwargs)
    
    # Create directory if it doesn't exist
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    
    print(f"Sample data generated and saved to {output_file}")
    print(f"Generated {len(df)} records across {df['course_number'].nunique()} courses")
    
    return output_file


if __name__ == "__main__":
    # When run directly, generate sample data
    save_sample_data(
        output_path='sample_course_data.csv',
        num_courses=5,
        num_students=50,
        num_units=6,
        num_teachers=3
    )
