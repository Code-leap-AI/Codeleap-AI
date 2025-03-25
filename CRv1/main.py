#!/usr/bin/env python3
"""
Course Complexity Analyzer
--------------------------
Main entry point for the application that analyzes course complexity
based on historical student completion times and leverages Gemini LLM
for generating insights.
"""

import os
import argparse
from pathlib import Path

from data_processor import load_course_data, preprocess_data
from analysis_engine import analyze_course_complexity
from llm_connector import get_gemini_insights
from utils.display import display_results


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Course Complexity Analyzer')
    parser.add_argument('--data', '-d', type=str, required=True,
                        help='Path to the CSV file with course data')
    parser.add_argument('--student', '-s', type=str, default=None,
                        help='Student ID for personalized confidence estimation')
    parser.add_argument('--course', '-c', type=str, default=None,
                        help='Course number to analyze (if not set, analyzes all courses)')
    parser.add_argument('--visualize', '-v', action='store_true',
                        help='Generate visualizations of the analysis')
    parser.add_argument('--api-key', '-k', type=str, default=None,
                        help='Gemini API key (if not set, will look for GEMINI_API_KEY env variable)')
    
    return parser.parse_args()


def main():
    """Main function to run the course complexity analyzer."""
    args = parse_arguments()
    
    # Set up API key
    api_key = args.api_key or os.environ.get('GEMINI_API_KEY')
    if not api_key:
        print("Error: Gemini API key not provided. Set it with --api-key or GEMINI_API_KEY environment variable.")
        return
    
    # Check if data file exists
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Error: Data file {args.data} not found.")
        return
    
    print(f"Loading course data from {args.data}...")
    raw_data = load_course_data(data_path)
    
    if raw_data.empty:
        print("Error: No data found or unable to parse the CSV file.")
        return
    
    print("Preprocessing data...")
    processed_data = preprocess_data(raw_data)
    
    print("Analyzing course complexity...")
    course_id = args.course
    complexity_metrics = analyze_course_complexity(processed_data, course_id)
    
    # Get insights from Gemini LLM
    print("Generating insights using Gemini LLM...")
    student_id = args.student
    insights = get_gemini_insights(processed_data, complexity_metrics, student_id, api_key)
    
    # Display results
    print("\n--- Analysis Results ---")
    display_results(complexity_metrics, insights, args.visualize)
    
    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
