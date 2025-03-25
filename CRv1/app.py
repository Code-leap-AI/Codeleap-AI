from flask import Flask, render_template, request, jsonify
import os
import pandas as pd
import json
from data_processor import load_course_data, preprocess_data
from analysis_engine import analyze_course_complexity
from llm_connector import get_gemini_insights

app = Flask(__name__)

# Global variables to store data
DATA_FILE = 'course_complexity_data.csv'
processed_data = None
complexity_metrics = None

def load_data():
    """Load and process the course data"""
    global processed_data, complexity_metrics
    
    print("\n===== LOADING COURSE DATA =====")
    
    if not os.path.exists(DATA_FILE):
        print(f"Data file {DATA_FILE} not found, generating sample data...")
        from generate_sample_csv import save_course_data
        save_course_data(DATA_FILE)
    
    print(f"Loading data from {DATA_FILE}...")
    raw_data = load_course_data(DATA_FILE)
    
    if raw_data.empty:
        print("ERROR: Failed to load data - empty DataFrame returned")
        return
    
    print(f"Data loaded successfully. Shape: {raw_data.shape}")
    print(f"Columns: {raw_data.columns.tolist()}")
    print(f"Course numbers: {raw_data['course_number'].unique().tolist()}")
    print(f"Number of teachers: {raw_data['teacher_name'].nunique()}")
    
    print("Preprocessing data...")
    processed_data = preprocess_data(raw_data)
    
    print("Analyzing course complexity...")
    complexity_metrics = analyze_course_complexity(processed_data)
    
    print(f"Completed analysis for {len(complexity_metrics)} courses")
    for course, metrics in complexity_metrics.items():
        complexity = metrics['overall_complexity']['complexity_score']
        category = metrics['overall_complexity']['category']
        print(f"  - {course}: Complexity {complexity:.1f} ({category})")
        
    print("Data loading and analysis complete\n")

@app.route('/')
def index():
    """Render the main page"""
    courses = []
    teachers_by_course = {}
    
    if processed_data is not None:
        # Get unique courses
        courses = processed_data['course_number'].unique().tolist()
        
        # Get teachers by course
        for course in courses:
            course_data = processed_data[processed_data['course_number'] == course]
            teachers = course_data['teacher_name'].unique().tolist()
            teachers_by_course[course] = teachers
    
    return render_template('index.html', 
                         courses=courses, 
                         teachers_by_course=json.dumps(teachers_by_course))

@app.route('/get_confidence', methods=['POST'])
def get_confidence():
    """Calculate confidence score based on selection"""
    student_name = request.form.get('student_name')
    course_id = request.form.get('course')
    teacher_name = request.form.get('teacher')
    
    # Basic validation
    if not student_name or not course_id or not teacher_name:
        return jsonify({
            'success': False,
            'message': 'Please fill in all fields'
        })
    
    # Generate a student ID for new students
    student_id = f"NEW_{student_name.replace(' ', '_').upper()}"
    
    # Get API key from environment or use a placeholder
    api_key = os.environ.get('GEMINI_API_KEY')
    
    if not api_key:
        print("\n" + "="*80)
        print("WARNING: GEMINI_API_KEY not set. Using fallback mode without AI recommendations.")
        print("To set the API key, use: export GEMINI_API_KEY=your_api_key_here")
        print("="*80 + "\n")
    
    if api_key:
        # Get insights from Gemini
        insights = get_gemini_insights(
            processed_data, 
            complexity_metrics, 
            student_id=student_id, 
            api_key=api_key,
            selected_course=course_id,
            selected_teacher=teacher_name
        )
    else:
        # Create a fallback response if no API key is available
        course_data = complexity_metrics.get(course_id, {})
        overall_complexity = course_data.get('overall_complexity', {})
        complexity_score = overall_complexity.get('complexity_score', 50)
        category = overall_complexity.get('category', 'Moderate')
        
        # Calculate confidence score (inverse of complexity - higher complexity = lower confidence)
        # Add some minor randomization to avoid all courses having the same score
        import random
        base_confidence = max(0, min(100, 100 - complexity_score * 0.7))
        # Vary by +/- 5% for more natural-looking scores
        confidence_score = max(0, min(100, base_confidence + random.uniform(-5, 5)))
        
        insights = {
            'confidence_score': round(confidence_score, 1),
            'course_insights': {
                course_id: {
                    'complexity': category,
                    'confidence': 'Moderate',
                    'recommendation': f"Based on the course complexity ({category}), we estimate a moderate confidence level. Focus on steady progress through each unit.",
                    'estimated_completion': f"Estimated completion time: {course_data.get('course_metrics', {}).get('avg_total_completion_time', 0)/60:.1f} hours"
                }
            },
            'most_difficult_unit': overall_complexity.get('most_difficult_unit', 'Unknown'),
            'raw_response': 'Note: For more detailed insights, please configure a Gemini API key.'
        }
    
    return jsonify({
        'success': True,
        'student_name': student_name,
        'course': course_id,
        'teacher': teacher_name,
        'insights': insights
    })

if __name__ == '__main__':
    # Load data on startup
    load_data()
    
    # Run the app
    app.run(debug=True)
