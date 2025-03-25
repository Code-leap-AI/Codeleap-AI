"""
Analysis Engine Module
---------------------
Performs analysis on course data to determine complexity metrics.
"""

import pandas as pd
import numpy as np


def analyze_course_complexity(df, course_id=None):
    """
    Analyze course complexity based on completion time data.
    
    Args:
        df (pd.DataFrame): Preprocessed course data
        course_id (str, optional): Specific course to analyze
        
    Returns:
        dict: Dictionary of complexity metrics by course
    """
    # Filter for specific course if provided
    if course_id:
        df = df[df['course_number'] == course_id].copy()
        if df.empty:
            print(f"Warning: No data found for course {course_id}")
            return {}
    
    # Get all courses to analyze
    courses = df['course_number'].unique()
    
    # Dictionary to store results for each course
    complexity_metrics = {}
    
    for course in courses:
        course_df = df[df['course_number'] == course]
        
        # Get unit time columns
        unit_cols = [col for col in course_df.columns if col.startswith('unit') and col.endswith('_time')]
        
        # Course-level metrics
        course_metrics = {
            'num_students': len(course_df),
            'num_units': len(unit_cols),
            'avg_total_completion_time': course_df['total_time'].mean(),
            'median_total_completion_time': course_df['total_time'].median(),
            'std_total_completion_time': course_df['total_time'].std(),
            'min_total_completion_time': course_df['total_time'].min(),
            'max_total_completion_time': course_df['total_time'].max(),
        }
        
        # Unit-level metrics
        unit_metrics = {}
        for unit in unit_cols:
            unit_name = unit.replace('_time', '')
            unit_data = course_df[unit].dropna()
            
            unit_metrics[unit_name] = {
                'mean_time': unit_data.mean(),
                'median_time': unit_data.median(),
                'min_time': unit_data.min(),
                'max_time': unit_data.max(),
                'std_time': unit_data.std(),
                # Estimate of difficulty based on time and consistency
                'difficulty_score': calculate_difficulty_score(unit_data)
            }
        
        # Teacher-level metrics
        teacher_metrics = {}
        for teacher in course_df['teacher_name'].unique():
            teacher_df = course_df[course_df['teacher_name'] == teacher]
            
            teacher_metrics[teacher] = {
                'num_students': len(teacher_df),
                'avg_total_time': teacher_df['total_time'].mean(),
                'avg_time_per_unit': {
                    unit: teacher_df[unit].mean() 
                    for unit in unit_cols
                },
                # Calculate efficiency score (lower is better)
                'efficiency_score': teacher_df['total_time'].mean() / course_metrics['avg_total_completion_time']
            }
        
        # Store all metrics for this course
        complexity_metrics[course] = {
            'course_metrics': course_metrics,
            'unit_metrics': unit_metrics,
            'teacher_metrics': teacher_metrics,
            # Calculate overall complexity score
            'overall_complexity': calculate_overall_complexity(course_metrics, unit_metrics)
        }
    
    return complexity_metrics


def calculate_difficulty_score(time_series):
    """
    Calculate difficulty score for a unit based on completion times.
    Higher score means more difficult.
    
    Args:
        time_series (pd.Series): Series of unit completion times
        
    Returns:
        float: Difficulty score from 0-100
    """
    if len(time_series) < 2:
        return 50.0  # Default middle value if not enough data
    
    # Factors that influence difficulty:
    # 1. Average time (higher = more difficult)
    # 2. Variance (higher = more inconsistent, can indicate difficulty)
    
    mean_time = time_series.mean()
    std_dev = time_series.std()
    
    # Coefficient of variation (normalized standard deviation)
    cv = std_dev / mean_time if mean_time > 0 else 0
    
    # Normalize mean_time to a 0-100 scale
    # Assumption: 4 hours is a full day's worth of work on a unit
    # Adjust this normalization based on your expected time scales
    normalized_time = min(100, (mean_time / 240) * 100)
    
    # Combine factors (70% weight on time, 30% on consistency)
    difficulty_score = (0.7 * normalized_time) + (0.3 * min(100, cv * 100))
    
    return round(difficulty_score, 1)


def calculate_overall_complexity(course_metrics, unit_metrics):
    """
    Calculate overall course complexity based on various metrics.
    
    Args:
        course_metrics (dict): Course-level metrics
        unit_metrics (dict): Unit-level metrics
        
    Returns:
        dict: Overall complexity score and category
    """
    # Average the difficulty scores of all units
    unit_difficulties = [metrics['difficulty_score'] for metrics in unit_metrics.values()]
    avg_difficulty = np.mean(unit_difficulties) if unit_difficulties else 50
    
    # Consider variation between units
    unit_difficulty_std = np.std(unit_difficulties) if len(unit_difficulties) > 1 else 0
    
    # Adjust complexity based on number of units
    num_units = course_metrics['num_units']
    units_factor = min(1.5, max(0.5, num_units / 5))  # Scale from 0.5 to 1.5 based on number of units
    
    # Calculate final complexity score
    complexity_score = avg_difficulty * units_factor
    
    # Determine complexity category
    if complexity_score < 30:
        category = "Easy"
    elif complexity_score < 60:
        category = "Moderate"
    elif complexity_score < 80:
        category = "Challenging"
    else:
        category = "Very Difficult"
    
    return {
        'complexity_score': round(complexity_score, 1),
        'category': category,
        'most_difficult_unit': max(unit_metrics.items(), key=lambda x: x[1]['difficulty_score'])[0],
        'easiest_unit': min(unit_metrics.items(), key=lambda x: x[1]['difficulty_score'])[0],
        'units_factor': units_factor
    }
