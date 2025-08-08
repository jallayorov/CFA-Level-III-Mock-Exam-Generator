"""
Original CFA Question Generator
Uses book content as knowledge base to create original exam scenarios
(not copying book examples, but testing the same concepts)
"""

import random
import json
import os
from typing import Dict, List, Tuple
import openai

def extract_concepts_from_content(cfa_content: Dict, topic: str, max_chars: int = 4000) -> Tuple[str, List[str]]:
    """Extract key concepts and principles from book content (not examples)"""
    
    if not cfa_content or 'all_text' not in cfa_content:
        return "Sample concepts", ["portfolio management", "risk assessment"]
    
    full_text = cfa_content['all_text']
    
    # Topic-specific concept indicators
    concept_patterns = {
        "Portfolio Management": [
            "investment policy statement", "strategic asset allocation", "investment objectives",
            "investment constraints", "liquidity requirements", "time horizon", "risk tolerance",
            "return requirements", "tax considerations", "regulatory constraints", "unique circumstances"
        ],
        "Asset Allocation": [
            "mean-variance optimization", "efficient frontier", "capital allocation line",
            "risk budgeting", "factor-based allocation", "black-litterman model",
            "resampled efficiency", "liability-driven investing", "tactical allocation"
        ],
        "Portfolio Construction": [
            "factor models", "multifactor models", "alpha transport", "portable alpha",
            "core-satellite approach", "completion portfolios", "tracking error",
            "information ratio", "active share", "security selection"
        ],
        "Risk Management": [
            "value at risk", "expected shortfall", "stress testing", "scenario analysis",
            "derivatives", "hedging strategies", "currency hedging", "interest rate risk",
            "credit risk", "operational risk", "model risk"
        ],
        "Performance Management": [
            "performance attribution", "benchmark selection", "risk-adjusted returns",
            "sharpe ratio", "information ratio", "treynor ratio", "jensen's alpha",
            "appraisal ratio", "GIPS standards", "performance evaluation"
        ],
        "Ethics & Professional Standards": [
            "fiduciary duty", "conflicts of interest", "disclosure requirements",
            "fair dealing", "loyalty", "prudence", "client confidentiality",
            "material nonpublic information", "research objectivity", "suitability"
        ]
    }
    
    # Find content sections that contain concept definitions/explanations
    keywords = concept_patterns.get(topic, [])
    best_content = ""
    best_score = 0
    
    # Try multiple random positions to find concept-rich content
    for _ in range(10):
        start_pos = random.randint(0, max(0, len(full_text) - max_chars))
        chunk = full_text[start_pos:start_pos + max_chars]
        
        # Score based on concept keyword frequency
        score = 0
        chunk_lower = chunk.lower()
        found_concepts = []
        
        for keyword in keywords:
            count = chunk_lower.count(keyword.lower())
            if count > 0:
                score += count * len(keyword)
                found_concepts.append(keyword)
        
        if score > best_score:
            best_score = score
            best_content = chunk
            key_concepts = found_concepts[:6]  # Top 6 concepts
    
    # Clean up the content
    sentences = best_content.split('.')
    if len(sentences) > 3:
        best_content = '.'.join(sentences[1:-1]) + '.'
    
    return best_content, key_concepts if 'key_concepts' in locals() else keywords[:6]

def generate_original_am_question(cfa_content: Dict, topic: str, question_number: int) -> Dict:
    """Generate original AM question based on concepts (not copying book examples)"""
    
    # Extract concepts from the book content
    concept_content, key_concepts = extract_concepts_from_content(cfa_content, topic, 4000)
    
    # Define sub-question structures
    sub_structures = [
        {"parts": ["A", "B", "C"], "points": [6, 6, 6], "total": 18},
        {"parts": ["A", "B", "C", "D"], "points": [4, 4, 4, 3], "total": 15},
        {"parts": ["A", "B"], "points": [6, 6], "total": 12},
        {"parts": ["A", "B", "C"], "points": [4, 4, 4], "total": 12}
    ]
    
    structure = random.choice(sub_structures)
    
    prompt = f"""
You are a CFA Level III exam question writer. Based on the {topic} concepts below, create an ORIGINAL exam question.

Key Concepts from CFA Curriculum: {', '.join(key_concepts)}
Reference Content (for concepts only): {concept_content[:1500]}

IMPORTANT INSTRUCTIONS:
1. DO NOT copy any examples from the reference content
2. CREATE an original scenario/case study that tests the same concepts
3. Assume the candidate has NO ACCESS to any books during the exam
4. The question should be standalone with all necessary information provided
5. Test understanding of the concepts, not memorization of book examples

Create a realistic AM session question with this structure:
- Main scenario: Original case study (pension fund, endowment, individual client, etc.)
- Sub-questions {', '.join(structure['parts'])} with points {structure['points']}
- Each part should build on the previous parts
- Include all data/information needed to solve the question

Return ONLY a JSON object:
{{
    "question_id": "AM_{question_number}_{topic.replace(' ', '_')}",
    "topic": "{topic}",
    "total_points": {structure['total']},
    "main_scenario": "ORIGINAL case study scenario with all necessary data and context",
    "sub_questions": [
        {{
            "part": "A",
            "points": {structure['points'][0]},
            "question": "First sub-question testing {topic} concepts",
            "model_solution": "Complete step-by-step solution with calculations and reasoning",
            "key_concepts": {key_concepts[:2]},
            "grading_rubric": ["specific grading point (X points)", "another grading point (Y points)"]
        }},
        {{
            "part": "B", 
            "points": {structure['points'][1]},
            "question": "Second sub-question building on part A",
            "additional_info": "New information or scenario development for part B",
            "model_solution": "Complete solution for part B",
            "key_concepts": {key_concepts[2:4] if len(key_concepts) > 2 else key_concepts[:2]},
            "grading_rubric": ["specific grading point (X points)", "another grading point (Y points)"]
        }}{"," if len(structure['parts']) > 2 else ""}
        {f'''{{
            "part": "C",
            "points": {structure['points'][2] if len(structure['points']) > 2 else 0},
            "question": "Third sub-question with further development",
            "additional_info": "Additional context for part C",
            "model_solution": "Complete solution for part C",
            "key_concepts": {key_concepts[4:6] if len(key_concepts) > 4 else key_concepts[:2]},
            "grading_rubric": ["specific grading point (X points)", "another grading point (Y points)"]
        }}''' if len(structure['parts']) > 2 else ""}{"," if len(structure['parts']) > 3 else ""}
        {f'''{{
            "part": "D",
            "points": {structure['points'][3] if len(structure['points']) > 3 else 0},
            "question": "Final sub-question tying everything together",
            "additional_info": "Final scenario element",
            "model_solution": "Complete final solution",
            "key_concepts": {key_concepts[-2:] if len(key_concepts) > 1 else key_concepts},
            "grading_rubric": ["specific grading point (X points)", "another grading point (Y points)"]
        }}''' if len(structure['parts']) > 3 else ""}
    ]
}}

Remember: Create ORIGINAL scenarios that test the concepts, not copy book examples!
"""

    try:
        response = openai.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,  # Higher creativity for original scenarios
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
        question_data['content_source'] = f"Original scenario based on {topic} concepts"
        question_data['structure_type'] = f"{len(structure['parts'])} parts, {structure['total']} points"
        question_data['generation_type'] = "original_scenario"
        
        return question_data
        
    except Exception as e:
        print(f"Error generating original AM question: {str(e)}")
        return None

def generate_original_pm_itemset(cfa_content: Dict, topic: str, itemset_number: int) -> Dict:
    """Generate original PM item set based on concepts (not copying book examples)"""
    
    # Extract concepts from the book content
    concept_content, key_concepts = extract_concepts_from_content(cfa_content, topic, 4000)
    
    prompt = f"""
You are a CFA Level III exam question writer. Based on the {topic} concepts below, create an ORIGINAL PM item set.

Key Concepts from CFA Curriculum: {', '.join(key_concepts)}
Reference Content (for concepts only): {concept_content[:1500]}

IMPORTANT INSTRUCTIONS:
1. DO NOT copy any examples from the reference content
2. CREATE an original vignette/case study that tests the same concepts
3. Assume the candidate has NO ACCESS to any books during the exam
4. The vignette should be standalone with all necessary information
5. Create 6 multiple choice questions that test understanding of the concepts

Create a realistic PM item set:
- Original vignette: New case study scenario
- 6 multiple choice questions testing {topic} concepts
- Each question should have 3 options (A, B, C)
- Include detailed explanations for why each answer is correct/incorrect

Return ONLY a JSON object:
{{
    "vignette": "ORIGINAL case study vignette with all necessary data and context for {topic}",
    "item_set_id": "PM_{itemset_number}_{topic.replace(' ', '_')}",
    "topic": "{topic}",
    "generation_type": "original_scenario",
    "questions": [
        {{
            "question_id": "PM_{itemset_number}_Q1",
            "question": "Question 1 testing {topic} concept",
            "options": ["A. First option", "B. Second option", "C. Third option"],
            "correct": "A",
            "explanation": "Detailed explanation of why A is correct and B/C are wrong"
        }},
        {{
            "question_id": "PM_{itemset_number}_Q2",
            "question": "Question 2 testing {topic} concept",
            "options": ["A. First option", "B. Second option", "C. Third option"],
            "correct": "B",
            "explanation": "Detailed explanation of why B is correct and A/C are wrong"
        }},
        {{
            "question_id": "PM_{itemset_number}_Q3",
            "question": "Question 3 testing {topic} concept",
            "options": ["A. First option", "B. Second option", "C. Third option"],
            "correct": "C",
            "explanation": "Detailed explanation of why C is correct and A/B are wrong"
        }},
        {{
            "question_id": "PM_{itemset_number}_Q4",
            "question": "Question 4 testing {topic} concept",
            "options": ["A. First option", "B. Second option", "C. Third option"],
            "correct": "A",
            "explanation": "Detailed explanation of why A is correct and B/C are wrong"
        }},
        {{
            "question_id": "PM_{itemset_number}_Q5",
            "question": "Question 5 testing {topic} concept",
            "options": ["A. First option", "B. Second option", "C. Third option"],
            "correct": "B",
            "explanation": "Detailed explanation of why B is correct and A/C are wrong"
        }},
        {{
            "question_id": "PM_{itemset_number}_Q6",
            "question": "Question 6 testing {topic} concept",
            "options": ["A. First option", "B. Second option", "C. Third option"],
            "correct": "C",
            "explanation": "Detailed explanation of why C is correct and A/B are wrong"
        }}
    ]
}}

Remember: Create ORIGINAL vignettes and questions that test the concepts, not copy book examples!
"""

    try:
        response = openai.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,  # Higher creativity for original scenarios
            max_tokens=2200
        )
        
        # Clean response
        raw_response = response.choices[0].message.content.strip()
        if raw_response.startswith('```json'):
            raw_response = raw_response[7:]
        if raw_response.endswith('```'):
            raw_response = raw_response[:-3]
        raw_response = raw_response.strip()
        
        itemset_data = json.loads(raw_response)
        
        # Add metadata
        itemset_data['content_source'] = f"Original scenario based on {topic} concepts"
        itemset_data['generation_type'] = "original_scenario"
        
        return itemset_data
        
    except Exception as e:
        print(f"Error generating original PM item set: {str(e)}")
        return None

# Test function
if __name__ == "__main__":
    print("Testing original question generator...")
    
    # Test concept extraction
    sample_content = {
        'all_text': "Strategic asset allocation is the process of determining the optimal long-term mix of asset classes. The investment policy statement defines investment objectives and constraints. Risk tolerance and return requirements are key considerations..."
    }
    
    content, concepts = extract_concepts_from_content(sample_content, "Portfolio Management")
    print(f"Extracted concepts for Portfolio Management: {concepts}")
    
    print("Original question generator ready!")
