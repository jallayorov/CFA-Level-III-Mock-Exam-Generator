"""
Enhanced Question Generator with Topic Diversity and Uniqueness
Implements proper CFA Level III topic weighting and prevents duplicates
"""

import random
import json
import hashlib
from typing import Dict, List, Tuple
import os

# CFA Level III Topic Weights (based on official curriculum)
CFA_TOPIC_WEIGHTS = {
    "Portfolio Management": 0.35,  # 30-35%
    "Asset Allocation": 0.20,     # 15-20%
    "Portfolio Construction": 0.20, # 15-20%
    "Performance Management": 0.10, # 5-10%
    "Risk Management": 0.15       # 10-15%
}

# Keywords for topic classification
TOPIC_KEYWORDS = {
    "Portfolio Management": [
        "portfolio", "investment policy", "strategic asset allocation", "tactical allocation",
        "rebalancing", "investment objectives", "constraints", "liquidity needs",
        "time horizon", "tax considerations", "regulatory", "unique circumstances"
    ],
    "Asset Allocation": [
        "asset allocation", "strategic allocation", "tactical allocation", "mean reversion",
        "momentum", "asset classes", "correlation", "diversification", "optimization",
        "efficient frontier", "risk budgeting", "factor investing"
    ],
    "Portfolio Construction": [
        "portfolio construction", "security selection", "factor models", "alpha",
        "beta", "tracking error", "information ratio", "active management",
        "passive management", "indexing", "enhanced indexing", "factor tilting"
    ],
    "Performance Management": [
        "performance", "attribution", "benchmark", "tracking error", "information ratio",
        "sharpe ratio", "treynor ratio", "jensen's alpha", "appraisal ratio",
        "performance evaluation", "risk-adjusted returns", "GIPS"
    ],
    "Risk Management": [
        "risk management", "VaR", "value at risk", "expected shortfall", "stress testing",
        "scenario analysis", "derivatives", "hedging", "options", "futures",
        "swaps", "currency risk", "interest rate risk", "credit risk"
    ]
}

def classify_content_topic(content: str) -> str:
    """Classify content into CFA topics based on keyword frequency"""
    content_lower = content.lower()
    topic_scores = {}
    
    for topic, keywords in TOPIC_KEYWORDS.items():
        score = 0
        for keyword in keywords:
            score += content_lower.count(keyword.lower())
        topic_scores[topic] = score
    
    # Return topic with highest score, or Portfolio Management as default
    if max(topic_scores.values()) == 0:
        return "Portfolio Management"
    
    return max(topic_scores, key=topic_scores.get)

def get_content_by_topic(cfa_content: Dict, target_topic: str = None, max_chars: int = 4000) -> Tuple[str, str]:
    """Get content chunk classified by topic"""
    if not cfa_content or 'all_text' not in cfa_content:
        return "Sample CFA Level III content about portfolio management.", "Portfolio Management"
    
    full_text = cfa_content['all_text']
    
    # Try multiple random chunks to find one matching the target topic
    max_attempts = 10
    for attempt in range(max_attempts):
        # Get random starting position
        max_start = max(0, len(full_text) - max_chars)
        start_pos = random.randint(0, max_start)
        
        # Extract chunk
        chunk = full_text[start_pos:start_pos + max_chars]
        
        # Clean up chunk (remove partial sentences at start/end)
        sentences = chunk.split('.')
        if len(sentences) > 2:
            chunk = '.'.join(sentences[1:-1]) + '.'
        
        # Classify the chunk
        detected_topic = classify_content_topic(chunk)
        
        # If we have a target topic, try to match it
        if target_topic is None or detected_topic == target_topic or attempt == max_attempts - 1:
            return chunk, detected_topic
    
    # Fallback
    return chunk, detected_topic

def select_topics_for_exam(num_questions: int) -> List[str]:
    """Select topics for exam questions based on CFA weights"""
    topics = []
    topic_list = list(CFA_TOPIC_WEIGHTS.keys())
    weights = list(CFA_TOPIC_WEIGHTS.values())
    
    for _ in range(num_questions):
        selected_topic = random.choices(topic_list, weights=weights)[0]
        topics.append(selected_topic)
    
    return topics

def generate_content_hash(content: str) -> str:
    """Generate hash for content to track uniqueness"""
    return hashlib.md5(content.encode()).hexdigest()[:12]

def load_used_questions() -> set:
    """Load previously used question hashes"""
    used_file = "data/exam_sessions/used_questions.json"
    if os.path.exists(used_file):
        try:
            with open(used_file, 'r') as f:
                data = json.load(f)
                return set(data.get('used_hashes', []))
        except:
            pass
    return set()

def save_used_questions(used_hashes: set):
    """Save used question hashes"""
    os.makedirs("data/exam_sessions", exist_ok=True)
    used_file = "data/exam_sessions/used_questions.json"
    
    try:
        with open(used_file, 'w') as f:
            json.dump({'used_hashes': list(used_hashes)}, f)
    except Exception as e:
        print(f"Error saving used questions: {e}")

def generate_unique_questions_from_text(session_type: str, cfa_content: Dict, num_questions: int = 1) -> List[Dict]:
    """Generate unique questions with proper topic diversity"""
    
    if not cfa_content:
        return None
    
    # Load previously used questions
    used_hashes = load_used_questions()
    
    # Select topics based on CFA weights
    target_topics = select_topics_for_exam(num_questions)
    
    questions = []
    new_hashes = set()
    
    for i, target_topic in enumerate(target_topics):
        max_attempts = 5
        question_generated = False
        
        for attempt in range(max_attempts):
            # Get content for the target topic
            content_chunk, detected_topic = get_content_by_topic(cfa_content, target_topic, max_chars=4000)
            
            # Generate content hash
            content_hash = generate_content_hash(content_chunk)
            
            # Skip if we've used this content before
            if content_hash in used_hashes or content_hash in new_hashes:
                continue
            
            if session_type == "AM":
                prompt = f"""
Based on this CFA Level III content about {detected_topic}, create 1 AM session constructed response question.

Content: {content_chunk}

Create a question that specifically tests {detected_topic} concepts. Return ONLY a JSON object with this structure:
{{
    "question": "Detailed scenario and question text focusing on {detected_topic}",
    "points": 15,
    "topic": "{detected_topic}",
    "answer_guidance": "Key points for grading focusing on {detected_topic} concepts",
    "question_id": "AM_{i+1}_{detected_topic.replace(' ', '_')}",
    "content_hash": "{content_hash}"
}}
"""
            else:  # PM
                prompt = f"""
Based on this CFA Level III content about {detected_topic}, create 1 PM session item set with 3 multiple choice questions.

Content: {content_chunk}

Create questions that specifically test {detected_topic} concepts. Return ONLY a JSON object with this structure:
{{
    "vignette": "Case study scenario focusing on {detected_topic}",
    "item_set_id": "PM_{i+1}_{detected_topic.replace(' ', '_')}",
    "topic": "{detected_topic}",
    "content_hash": "{content_hash}",
    "questions": [
        {{
            "question_id": "PM_{i+1}_Q1",
            "question": "Question 1 text about {detected_topic}",
            "options": ["A. Option A", "B. Option B", "C. Option C"],
            "correct": "A",
            "explanation": "Why A is correct (relating to {detected_topic})"
        }},
        {{
            "question_id": "PM_{i+1}_Q2", 
            "question": "Question 2 text about {detected_topic}",
            "options": ["A. Option A", "B. Option B", "C. Option C"],
            "correct": "B",
            "explanation": "Why B is correct (relating to {detected_topic})"
        }},
        {{
            "question_id": "PM_{i+1}_Q3",
            "question": "Question 3 text about {detected_topic}",
            "options": ["A. Option A", "B. Option B", "C. Option C"],
            "correct": "C", 
            "explanation": "Why C is correct (relating to {detected_topic})"
        }}
    ]
}}
"""
            
            try:
                import openai
                response = openai.chat.completions.create(
                    model=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.8,  # Higher temperature for more variety
                    max_tokens=1200
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
                question_data['generated_topic'] = detected_topic
                question_data['target_topic'] = target_topic
                question_data['content_hash'] = content_hash
                
                questions.append(question_data)
                new_hashes.add(content_hash)
                question_generated = True
                break
                
            except Exception as e:
                print(f"Error generating question {i+1}, attempt {attempt+1}: {str(e)}")
                continue
        
        if not question_generated:
            print(f"Failed to generate unique question {i+1} for topic {target_topic}")
    
    # Save new hashes to prevent future duplicates
    if new_hashes:
        all_used_hashes = used_hashes.union(new_hashes)
        save_used_questions(all_used_hashes)
    
    return questions if questions else None

def get_topic_distribution_summary(questions: List[Dict]) -> Dict:
    """Get summary of topic distribution in generated questions"""
    topic_counts = {}
    
    for question in questions:
        topic = question.get('topic', question.get('generated_topic', 'Unknown'))
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    
    return topic_counts

# Test function
if __name__ == "__main__":
    print("Testing enhanced question generator...")
    
    # Test topic classification
    test_content = "Portfolio construction involves selecting securities to optimize risk and return while considering factor exposures and tracking error."
    topic = classify_content_topic(test_content)
    print(f"Classified topic: {topic}")
    
    # Test topic selection
    topics = select_topics_for_exam(6)
    print(f"Selected topics for 6 questions: {topics}")
    
    # Test uniqueness tracking
    used = load_used_questions()
    print(f"Currently used question hashes: {len(used)}")
