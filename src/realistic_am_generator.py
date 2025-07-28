"""
Realistic CFA Level III AM Question Generator
Generates questions with sub-parts (A, B, C, D) and complete model solutions
"""

import random
import json
import os
from typing import Dict, List, Tuple
import openai

def extract_chapter_content(cfa_content: Dict, topic: str, max_chars: int = 6000) -> Tuple[str, str]:
    """Extract focused chapter content for a specific topic"""
    
    if not cfa_content or 'all_text' not in cfa_content:
        return "Sample CFA content", topic
    
    full_text = cfa_content['all_text']
    
    # Topic-specific chapter indicators
    chapter_indicators = {
        "Portfolio Management": [
            "investment policy statement", "strategic asset allocation", "portfolio objectives",
            "investment constraints", "liquidity requirements", "time horizon", "tax considerations"
        ],
        "Asset Allocation": [
            "asset allocation", "mean-variance optimization", "black-litterman", "resampled efficiency",
            "risk budgeting", "factor-based allocation", "liability-driven investing"
        ],
        "Portfolio Construction": [
            "portfolio construction", "security selection", "factor models", "multifactor models",
            "alpha transport", "portable alpha", "completion portfolios", "core-satellite"
        ],
        "Risk Management": [
            "risk management", "value at risk", "expected shortfall", "stress testing",
            "derivatives", "hedging strategies", "currency hedging", "interest rate risk"
        ],
        "Performance Management": [
            "performance evaluation", "attribution analysis", "benchmark selection",
            "risk-adjusted returns", "sharpe ratio", "information ratio", "tracking error"
        ]
    }
    
    # Find content sections that match the topic
    keywords = chapter_indicators.get(topic, [])
    best_content = ""
    best_score = 0
    
    # Try multiple random positions to find topic-relevant content
    for _ in range(15):
        start_pos = random.randint(0, max(0, len(full_text) - max_chars))
        chunk = full_text[start_pos:start_pos + max_chars]
        
        # Score based on keyword frequency
        score = 0
        chunk_lower = chunk.lower()
        for keyword in keywords:
            score += chunk_lower.count(keyword.lower()) * len(keyword)
        
        if score > best_score:
            best_score = score
            best_content = chunk
    
    # Clean up the content
    sentences = best_content.split('.')
    if len(sentences) > 3:
        best_content = '.'.join(sentences[1:-1]) + '.'
    
    return best_content, topic

def generate_realistic_am_question(cfa_content: Dict, topic: str, question_number: int) -> Dict:
    """Generate a realistic AM question with sub-parts and model solutions"""
    
    # Extract chapter-specific content
    chapter_content, detected_topic = extract_chapter_content(cfa_content, topic, 6000)
    
    # Define sub-question structures based on point allocation
    sub_structures = [
        {"parts": ["A", "B", "C"], "points": [6, 6, 6], "total": 18},
        {"parts": ["A", "B", "C", "D"], "points": [4, 4, 4, 3], "total": 15},
        {"parts": ["A", "B"], "points": [6, 6], "total": 12},
        {"parts": ["A", "B", "C"], "points": [4, 4, 4], "total": 12}
    ]
    
    structure = random.choice(sub_structures)
    
    prompt = f"""
Based on this CFA Level III {detected_topic} content, create a realistic AM session constructed response question.

Chapter Content: {chapter_content}

Create a question that follows the EXACT CFA Level III AM format:
1. Main scenario/case study
2. Sub-questions {', '.join(structure['parts'])} with points {structure['points']}
3. Each sub-question builds progressively on the scenario
4. Complete model solutions based on the provided content

Return ONLY a JSON object with this structure:
{{
    "question_id": "AM_{question_number}_{detected_topic.replace(' ', '_')}",
    "topic": "{detected_topic}",
    "total_points": {structure['total']},
    "main_scenario": "Detailed case study scenario based on the chapter content",
    "sub_questions": [
        {{
            "part": "A",
            "points": {structure['points'][0]},
            "question": "First sub-question based on main scenario",
            "model_solution": "Complete step-by-step solution with calculations and explanations from the book content",
            "key_concepts": ["concept1", "concept2"],
            "grading_rubric": ["point1 (2 points)", "point2 (2 points)", "point3 (2 points)"]
        }},
        {{
            "part": "B", 
            "points": {structure['points'][1]},
            "question": "Second sub-question that builds on part A with additional information",
            "additional_info": "New information or scenario development for part B",
            "model_solution": "Complete solution for part B based on book content",
            "key_concepts": ["concept3", "concept4"],
            "grading_rubric": ["point1 (2 points)", "point2 (2 points)", "point3 (2 points)"]
        }}{"," if len(structure['parts']) > 2 else ""}
        {f'''{{
            "part": "C",
            "points": {structure['points'][2] if len(structure['points']) > 2 else 0},
            "question": "Third sub-question with further scenario development",
            "additional_info": "Additional context or new scenario element for part C",
            "model_solution": "Complete solution for part C from book content",
            "key_concepts": ["concept5", "concept6"],
            "grading_rubric": ["point1 (2 points)", "point2 (2 points)", "point3 (2 points)"]
        }}''' if len(structure['parts']) > 2 else ""}{"," if len(structure['parts']) > 3 else ""}
        {f'''{{
            "part": "D",
            "points": {structure['points'][3] if len(structure['points']) > 3 else 0},
            "question": "Final sub-question that ties everything together",
            "additional_info": "Final scenario element or conclusion requirement",
            "model_solution": "Complete final solution based on book content",
            "key_concepts": ["concept7", "concept8"],
            "grading_rubric": ["point1 (1 point)", "point2 (1 point)", "point3 (1 point)"]
        }}''' if len(structure['parts']) > 3 else ""}
    ]
}}

IMPORTANT: 
- Model solutions must be complete answers that could be found in the CFA books
- Each solution should reference specific concepts from the provided content
- Sub-questions should build progressively (B uses A's answer, C uses A+B, etc.)
- Grading rubrics should be specific and actionable
"""

    try:
        response = openai.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        
        # Clean response
        raw_response = response.choices[0].message.content.strip()
        if raw_response.startswith('```json'):
            raw_response = raw_response[7:]
        if raw_response.endswith('```'):
            raw_response = raw_response[:-3]
        raw_response = raw_response.strip()
        
        question_data = json.loads(raw_response)
        
        # Add metadata
        question_data['content_source'] = f"{detected_topic} chapter content"
        question_data['structure_type'] = f"{len(structure['parts'])} parts, {structure['total']} points"
        
        return question_data
        
    except Exception as e:
        print(f"Error generating realistic AM question: {str(e)}")
        return None

def grade_am_sub_question(sub_question: Dict, student_answer: str, part_letter: str) -> Dict:
    """Grade a specific sub-question part with complete model solution comparison"""
    
    if not student_answer.strip():
        return {
            "score": 0,
            "max_points": sub_question.get('points', 0),
            "feedback": "No answer provided",
            "model_solution": sub_question.get('model_solution', 'No model solution available'),
            "comparison": "Cannot compare - no student answer provided"
        }
    
    model_solution = sub_question.get('model_solution', '')
    grading_rubric = sub_question.get('grading_rubric', [])
    key_concepts = sub_question.get('key_concepts', [])
    max_points = sub_question.get('points', 0)
    
    prompt = f"""
Grade this CFA Level III AM sub-question part {part_letter}.

Question: {sub_question.get('question', '')}
Model Solution: {model_solution}
Key Concepts: {', '.join(key_concepts)}
Grading Rubric: {'; '.join(grading_rubric)}
Max Points: {max_points}

Student Answer: {student_answer}

Provide detailed grading with:
1. Point-by-point comparison with model solution
2. Specific feedback on what was correct/incorrect
3. Complete model solution for reference
4. Specific areas for improvement

Return ONLY a JSON object:
{{
    "score": [0-{max_points}],
    "max_points": {max_points},
    "detailed_feedback": "Point-by-point analysis of the student's answer",
    "model_solution": "Complete model solution from CFA curriculum",
    "points_breakdown": [
        {{"criterion": "First grading point", "earned": 2, "possible": 2, "comment": "explanation"}},
        {{"criterion": "Second grading point", "earned": 1, "possible": 2, "comment": "explanation"}}
    ],
    "key_concepts_covered": ["concept1", "concept2"],
    "key_concepts_missing": ["concept3"],
    "improvement_areas": ["specific area 1", "specific area 2"]
}}
"""
    
    try:
        response = openai.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800
        )
        
        raw_response = response.choices[0].message.content.strip()
        if raw_response.startswith('```json'):
            raw_response = raw_response[7:]
        if raw_response.endswith('```'):
            raw_response = raw_response[:-3]
        raw_response = raw_response.strip()
        
        return json.loads(raw_response)
        
    except Exception as e:
        return {
            "score": 0,
            "max_points": max_points,
            "detailed_feedback": f"Error grading answer: {str(e)}",
            "model_solution": model_solution,
            "points_breakdown": [],
            "improvement_areas": ["Unable to grade due to technical error"]
        }

# Test function
if __name__ == "__main__":
    print("Testing realistic AM question generator...")
    
    # Test chapter content extraction
    sample_content = {
        'all_text': "Portfolio management involves strategic asset allocation decisions based on investment policy statements. The investment manager must consider client objectives, constraints, and risk tolerance when developing appropriate asset allocation strategies..."
    }
    
    content, topic = extract_chapter_content(sample_content, "Portfolio Management")
    print(f"Extracted content for {topic}: {content[:100]}...")
    
    print("Realistic AM generator ready!")
