"""
Display Utilities Module
----------------------
Functions for displaying analysis results to the user.
"""

import textwrap


def display_results(complexity_metrics, insights, visualize=False):
    """
    Display analysis results in a readable format.
    
    Args:
        complexity_metrics (dict): Course complexity metrics
        insights (dict): Insights from Gemini LLM
        visualize (bool): Whether to generate visualizations
    """
    # Display basic metrics for each course
    for course_id, metrics in complexity_metrics.items():
        print(f"\n{'='*60}")
        print(f"Course: {course_id}")
        print(f"{'='*60}")
        
        # Overall complexity
        complexity = metrics['overall_complexity']
        print(f"Complexity Category: {complexity['category']} (Score: {complexity['complexity_score']})")
        print(f"Most Difficult Unit: {complexity['most_difficult_unit']}")
        print(f"Easiest Unit: {complexity['easiest_unit']}")
        
        # Course metrics
        course_data = metrics['course_metrics']
        print(f"\nNumber of Students: {course_data['num_students']}")
        print(f"Number of Units: {course_data['num_units']}")
        print(f"Average Completion Time: {course_data['avg_total_completion_time']:.1f} minutes")
        print(f"Time Range: {course_data['min_total_completion_time']:.1f} - {course_data['max_total_completion_time']:.1f} minutes")
        
        # Unit details
        print("\nUnit Details:")
        print(f"{'Unit':<10} {'Difficulty':<12} {'Avg Time (min)':<15} {'Time Range':<20}")
        print("-" * 60)
        
        for unit, unit_data in metrics['unit_metrics'].items():
            difficulty_str = f"{unit_data['difficulty_score']:.1f}/100"
            avg_time = f"{unit_data['mean_time']:.1f}"
            time_range = f"{unit_data['min_time']:.1f} - {unit_data['max_time']:.1f}"
            print(f"{unit:<10} {difficulty_str:<12} {avg_time:<15} {time_range:<20}")
        
        # Teacher comparison
        if len(metrics['teacher_metrics']) > 1:
            print("\nTeacher Comparison:")
            print(f"{'Teacher':<15} {'Students':<10} {'Avg Time (min)':<15} {'Efficiency':<10}")
            print("-" * 60)
            
            for teacher, teacher_data in metrics['teacher_metrics'].items():
                efficiency = f"{teacher_data['efficiency_score']:.2f}"
                efficiency_indicator = "✓" if float(efficiency) < 1.0 else "✗"
                avg_time = f"{teacher_data['avg_total_time']:.1f}"
                print(f"{teacher:<15} {teacher_data['num_students']:<10} {avg_time:<15} {efficiency:<10} {efficiency_indicator}")
    
    # Display Gemini insights
    if 'error' not in insights:
        print(f"\n{'='*60}")
        print("Gemini LLM Insights")
        print(f"{'='*60}")
        
        if 'raw_response' in insights:
            wrapped_text = textwrap.fill(insights['raw_response'], width=80)
            print(wrapped_text)
    else:
        print(f"\nError getting LLM insights: {insights['error']}")
    
    # Generate visualizations if requested
    if visualize:
        try:
            # This would be implemented with matplotlib or another visualization library
            print("\nGenerating visualizations (placeholder)...")
            # generate_visualizations(complexity_metrics)
        except ImportError:
            print("\nVisualization requires matplotlib. Install with 'pip install matplotlib'")
