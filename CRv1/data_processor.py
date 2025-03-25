"""
Data Processor Module
--------------------
Handles loading and preprocessing of course data from CSV files.
"""

import pandas as pd
import numpy as np
from pathlib import Path


def load_course_data(file_path):
    """
    Load course data from a CSV file.
    
    Args:
        file_path (str or Path): Path to the CSV file
        
    Returns:
        pd.DataFrame: Loaded data or empty DataFrame if loading fails
    """
    try:
        # Assume CSV has headers: course_number, teacher_name, student_id, unit1_time, unit2_time, etc.
        df = pd.read_csv(file_path)
        
        # Basic validation
        required_cols = ['course_number', 'teacher_name', 'student_id']
        if not all(col in df.columns for col in required_cols):
            print(f"Error: CSV must contain columns {required_cols}")
            return pd.DataFrame()
        
        # Check if we have at least one unit completion time column
        unit_cols = [col for col in df.columns if col.startswith('unit') and col.endswith('_time')]
        if not unit_cols:
            print("Error: No unit completion time columns found (expected format: 'unitX_time')")
            return pd.DataFrame()
            
        return df
        
    except Exception as e:
        print(f"Error loading data: {str(e)}")
        return pd.DataFrame()


def preprocess_data(df):
    """
    Preprocess the raw course data.
    
    Args:
        df (pd.DataFrame): Raw course data
        
    Returns:
        pd.DataFrame: Processed data with additional metrics
    """
    # Create a copy to avoid modifying the original
    processed_df = df.copy()
    
    # Identify unit time columns
    unit_cols = [col for col in processed_df.columns if col.startswith('unit') and col.endswith('_time')]
    
    # Convert time columns to numeric, coercing errors to NaN
    for col in unit_cols:
        processed_df[col] = pd.to_numeric(processed_df[col], errors='coerce')
    
    # Calculate total completion time per student
    processed_df['total_time'] = processed_df[unit_cols].sum(axis=1)
    
    # Calculate average time per unit for each student
    processed_df['avg_time_per_unit'] = processed_df[unit_cols].mean(axis=1)
    
    # Standardize teacher names (lowercase, strip whitespace)
    processed_df['teacher_name'] = processed_df['teacher_name'].str.strip().str.lower()
    
    # Convert course numbers to string to handle alphanumeric course IDs
    processed_df['course_number'] = processed_df['course_number'].astype(str)
    
    # Flag potential outliers (students taking significantly longer or shorter than average)
    for course in processed_df['course_number'].unique():
        course_mask = processed_df['course_number'] == course
        
        for col in unit_cols:
            col_mean = processed_df.loc[course_mask, col].mean()
            col_std = processed_df.loc[course_mask, col].std()
            
            # Mark as outlier if more than 2 standard deviations from mean
            outlier_col = f"{col}_outlier"
            processed_df.loc[course_mask, outlier_col] = np.abs(
                processed_df.loc[course_mask, col] - col_mean) > 2 * col_std
    
    return processed_df
