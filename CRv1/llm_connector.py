"""
LLM Connector Module
------------------
Handles integration with the Gemini LLM API for generating insights.
"""

import json
import requests
import pandas as pd


def get_gemini_insights(processed_data, complexity_metrics, student_id=None, api_key=None, selected_course=None, selected_teacher=None):
    """
    Get insights from Gemini LLM based on course data and complexity metrics.
    
    Args:
        processed_data (pd.DataFrame): Processed course data
        complexity_metrics (dict): Dictionary of course complexity metrics
        student_id (str, optional): Student ID for personalized insights
        api_key (str): Gemini API key
        selected_course (str, optional): Specific course selected by the student
        selected_teacher (str, optional): Specific teacher selected by the student
        
    Returns:
        dict: Dictionary of insights from Gemini LLM
    """
    if not api_key:
        print("Warning: No API key provided for Gemini LLM")
        return {"error": "No API key provided"}
    
    # Prepare data for the prompt
    prompt_data = prepare_prompt_data(processed_data, complexity_metrics, student_id, selected_course, selected_teacher)
    
    # Generate the prompt
    prompt = generate_prompt(prompt_data)
    
    # Call Gemini API
    try:
        insights = call_gemini_api(prompt, api_key, prompt_data)
        return insights
    except Exception as e:
        print(f"Error calling Gemini API: {str(e)}")
        return {"error": str(e)}


def prepare_prompt_data(processed_data, complexity_metrics, student_id=None, selected_course=None, selected_teacher=None):
    """
    Prepare data to be included in the Gemini prompt.
    
    Args:
        processed_data (pd.DataFrame): Processed course data
        complexity_metrics (dict): Course complexity metrics
        student_id (str, optional): Student ID for personalized insights
        selected_course (str, optional): Specific course selected by the student
        selected_teacher (str, optional): Specific teacher selected by the student
        
    Returns:
        dict: Data to be included in the prompt
    """
    # Get summary statistics for the prompt
    prompt_data = {
        "courses": [],
        "student_info": None
    }
    
    # Store selected course and teacher in prompt data
    prompt_data["selected_course"] = selected_course
    prompt_data["selected_teacher"] = selected_teacher
    
    # Process each course
    for course_id, metrics in complexity_metrics.items():
        # Skip courses that don't match the selected course if one is specified
        if selected_course and course_id != selected_course:
            continue
            
        course_info = {
            "course_id": course_id,
            "complexity": {
                "score": metrics["overall_complexity"]["complexity_score"],
                "category": metrics["overall_complexity"]["category"],
                "most_difficult_unit": metrics["overall_complexity"]["most_difficult_unit"],
                "easiest_unit": metrics["overall_complexity"]["easiest_unit"]
            },
            "units": len(metrics["unit_metrics"]),
            "teachers": list(metrics["teacher_metrics"].keys()),
            "avg_completion_time": metrics["course_metrics"]["avg_total_completion_time"],
            "min_completion_time": metrics["course_metrics"]["min_total_completion_time"],
            "max_completion_time": metrics["course_metrics"]["max_total_completion_time"]
        }
        
        # Add teacher-specific info if a teacher is selected
        if selected_teacher and selected_teacher in metrics["teacher_metrics"]:
            teacher_data = metrics["teacher_metrics"][selected_teacher]
            course_info["selected_teacher"] = {
                "name": selected_teacher,
                "efficiency_score": teacher_data["efficiency_score"],
                "avg_total_time": teacher_data["avg_total_time"]
            }
        
        prompt_data["courses"].append(course_info)
    
    # Add student-specific data if provided
    if student_id and student_id in processed_data["student_id"].values:
        student_df = processed_data[processed_data["student_id"] == student_id]
        
        # Get student's history
        student_courses = student_df["course_number"].unique()
        
        student_info = {
            "student_id": student_id,
            "completed_courses": student_courses.tolist(),
            "performance_metrics": {}
        }
        
        # Calculate how the student compares to average in completed courses
        for course in student_courses:
            course_df = processed_data[processed_data["course_number"] == course]
            student_course_df = student_df[student_df["course_number"] == course]
            
            if not student_course_df.empty:
                avg_course_time = course_df["total_time"].mean()
                student_time = student_course_df["total_time"].iloc[0]
                
                # Calculate relative performance (1.0 means average, < 1.0 means faster than average)
                relative_performance = student_time / avg_course_time if avg_course_time > 0 else 1.0
                
                student_info["performance_metrics"][course] = {
                    "total_time": student_time,
                    "relative_performance": relative_performance,
                    "percentile": (course_df["total_time"] > student_time).mean() * 100
                }
        
        prompt_data["student_info"] = student_info
    
    return prompt_data


def generate_prompt(prompt_data):
    """
    Generate a prompt for the Gemini LLM.
    
    Args:
        prompt_data (dict): Structured data for the prompt
        
    Returns:
        str: Formatted prompt for Gemini
    """
    # Get selected course if specified
    selected_course = None
    selected_teacher = None
    
    # Check for selected course and teacher in prompt_data
    if 'selected_course' in prompt_data and prompt_data['selected_course']:
        selected_course = prompt_data['selected_course']
    if 'selected_teacher' in prompt_data and prompt_data['selected_teacher']:
        selected_teacher = prompt_data['selected_teacher']
    
    # Filter courses if a specific one is selected
    if selected_course:
        filtered_courses = [course for course in prompt_data["courses"] if course["course_id"] == selected_course]
    else:
        filtered_courses = prompt_data["courses"]
    
    courses_json = json.dumps(filtered_courses, indent=2)
    
    # Base prompt
    prompt = f"""
    You are an educational advisor AI that helps students understand course complexity and provides confidence estimates.
    
    Here is data about {"the selected course" if selected_course else "courses"}, complexity, and completion times:
    ```json
    {courses_json}
    ```
    """
    
    # Add teacher-specific context if provided
    if selected_course and selected_teacher:
        prompt += f"""
    The student has specifically selected professor {selected_teacher} for course {selected_course}.
        """
    
    # Request specific insights
    prompt += f"""
    Based on this data, please provide:
    
    1. A numerical confidence score from 0-100 for a new student taking {"this course" if selected_course else "each course"} (higher means more confidence)
    2. A brief explanation of {"the course's" if selected_course else "each course's"} complexity and what makes it challenging or easy
    3. Tips for students to succeed, particularly focusing on the most difficult units
    4. Realistic expectations for how long {"the course" if selected_course else "each course"} might take to complete
    
    IMPORTANT: Begin your response with "Confidence Score: X" where X is a number between 0-100. This is critical for our system to function properly.
    
    For example:
    Confidence Score: 75
    
    The course complexity is moderate...
    
    Then continue with the rest of your analysis and recommendations.
    """
    
    # Add student-specific prompt if available
    if prompt_data["student_info"]:
        student_json = json.dumps(prompt_data["student_info"], indent=2)
        prompt += f"""
        
        Additionally, here is information about a specific student:
        ```json
        {student_json}
        ```
        
        Please also provide:
        
        4. A personalized confidence estimate for this student for each course
        5. Specific advice based on their performance in previous courses
        6. Whether they might need additional support for any particular units
        """
    
    return prompt


def call_gemini_api(prompt, api_key, prompt_data=None):
    """
    Call the Gemini API with the generated prompt.
    
    Args:
        prompt (str): Prompt for Gemini
        api_key (str): Gemini API key
        prompt_data (dict, optional): Original prompt data for reference
        
    Returns:
        dict: Parsed response from Gemini
    """
    print("\n===== GEMINI API DEBUG =====")
    print(f"API Key (first 5 chars): {api_key[:5]}...")
    
    # Updated to use the Gemini 2.0 Flash API endpoint
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # Format the request based on the provided example
    data = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }
    
    print(f"API URL: {api_url.replace(api_key, 'API_KEY_HIDDEN')}")
    print(f"Prompt length: {len(prompt)} characters")
    print(f"First 100 chars of prompt: {prompt[:100]}...")
    
    try:
        print("Sending request to Gemini API...")
        response = requests.post(api_url, headers=headers, json=data)
        
        print(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"ERROR: API request failed: {response.text}")
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
        
        response_data = response.json()
        print(f"Response data keys: {list(response_data.keys())}")
        print("API request successful")
    except Exception as e:
        print(f"Exception during API call: {str(e)}")
        raise
    
    # Extract the text from the response
    try:
        print("Extracting text from response...")
        # The response format may vary based on the API version, handle both possibilities
        if "candidates" in response_data:
            print("Found 'candidates' in response")
            text_response = response_data["candidates"][0]["content"]["parts"][0]["text"]
        elif "content" in response_data:
            print("Found 'content' in response")
            text_response = response_data["content"]["parts"][0]["text"]
        else:
            # Extract any text content from the response
            import json
            print(f"Unexpected response format. Response keys: {list(response_data.keys())}")
            print(f"Full response: {json.dumps(response_data, indent=2)[:500]}...")
            # Try to find any text in the response
            text_response = str(response_data)
            if len(text_response) > 1000:
                text_response = text_response[:1000] + "... (truncated)"
        
        print(f"Extracted text length: {len(text_response)} characters")
        print(f"First 100 chars: {text_response[:100]}...")
        
        # Process the response into a structured format
        insights = {
            "course_insights": {},
            "student_insights": None,
            "raw_response": text_response
        }
        
        # Extract confidence score - improved pattern matching
        import re
        print("Extracting confidence score...")
        
        # Multiple patterns to try for confidence scores
        patterns = [
            r'confidence\s*score\s*(?:is|of|:)\s*(\d+)',  # "confidence score is 75" or "confidence score: 80"
            r'confidence\s*(?:rating|level|estimate)\s*(?:is|of|:)\s*(\d+)',  # "confidence level is 75"
            r'confidence\s*(?:would be|at)\s*(\d+)',  # "confidence would be 75"
            r'(\d+)%\s*confidence',  # "75% confidence"
            r'confidence\s*(?:of|is)\s*(\d+)%',  # "confidence of 75%"
            r'(\d+)\s*(?:out of|\/)\s*100',  # "75 out of 100"
            r'(\d+)%'  # Any percentage as last resort
        ]
        
        # Try each pattern until we find a match
        confidence_score = None
        for i, pattern in enumerate(patterns):
            matches = re.findall(pattern, text_response, re.IGNORECASE)
            if matches:
                confidence_score = min(100, max(0, int(matches[0])))
                print(f"Found confidence score {confidence_score} using pattern {i+1}: {pattern}")
                break
        
        # If no match found, calculate based on complexity if possible
        if confidence_score is None:
            print("No confidence score found in text, trying to extract from complexity...")
            # Try to find a complexity value in the text
            complexity_match = re.search(r'complex(?:ity)?[^\n.]*?(\d+)', text_response, re.IGNORECASE)
            if complexity_match:
                complexity_value = int(complexity_match.group(1))
                confidence_score = max(0, min(100, 100 - complexity_value * 0.7))
                print(f"Calculated confidence score {confidence_score} from complexity value {complexity_value}")
            else:
                # Default fallback
                confidence_score = 50
                print(f"No complexity value found either. Using default confidence score: {confidence_score}")
        
        insights["confidence_score"] = round(confidence_score, 1)
        print(f"Final confidence score: {insights['confidence_score']}")
        
        # Extract course insights - for each course mentioned
        selected_course = prompt_data.get('selected_course')
        
        if selected_course:
            # Focus on the selected course
            course_insights = {
                "complexity": "Unknown",
                "confidence": "Moderate",
                "recommendation": "",
                "estimated_completion": ""
            }
            
            # Look for complexity level
            complexity_match = re.search(r'complex(?:ity)?[^\n.]*?(easy|moderate|challenging|difficult|very difficult)', text_response, re.IGNORECASE)
            if complexity_match:
                course_insights["complexity"] = complexity_match.group(1).title()
            
            # Extract recommendation - often comes after "tips" or "recommendation" 
            recommendation_match = re.search(r'(?:recommend(?:ation)?s?|tips?)[^\n]*?\n(.*?)(?:\n\n|\Z)', text_response, re.IGNORECASE | re.DOTALL)
            if recommendation_match:
                course_insights["recommendation"] = recommendation_match.group(1).strip()
            
            # Extract time estimate
            time_match = re.search(r'(?:take|complete|finish)[^\n]*?(\d+[\.,]?\d*\s*(?:hour|hr|minute|min)s?)', text_response, re.IGNORECASE)
            if time_match:
                course_insights["estimated_completion"] = time_match.group(1)
            
            insights["course_insights"][selected_course] = course_insights
        
        # Extract difficult unit
        difficult_unit_match = re.search(r'(?:difficult|challenging)(?:\s*unit)?[^\n.]*?(unit\d+)', text_response, re.IGNORECASE)
        if difficult_unit_match:
            insights["most_difficult_unit"] = difficult_unit_match.group(1)
        
        return insights
        
    except (KeyError, IndexError) as e:
        raise Exception(f"Unexpected API response format: {str(e)}")
