"""
AI-powered question generation for CFA Level III mock exams
"""
import json
import random
from typing import List, Dict, Optional
from openai import OpenAI
from config.topics import TOPIC_WEIGHTS, QUESTION_TYPES, DIFFICULTY_LEVELS
import os
from dotenv import load_dotenv

load_dotenv()

class CFAQuestionGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        
    def generate_constructed_response_question(self, chunk: Dict, difficulty: str = "Level_2") -> Dict:
        """Generate AM session constructed response question"""
        
        prompt = f"""
        You are a CFA Level III exam question writer. Based on the following content chunk, create ONE high-quality constructed response question that matches the real CFA Level III AM session format.

        Content Topic: {chunk['topic']}
        Content: {chunk['content'][:1500]}...

        Requirements:
        1. Create a realistic scenario-based question (like a case study)
        2. The question should require 15-20 minutes to answer
        3. Include specific numerical data where appropriate
        4. Difficulty level: {difficulty} - {DIFFICULTY_LEVELS[difficulty]['description']}
        5. Follow CFA Institute writing style and terminology
        6. Include 3-5 sub-questions (parts A, B, C, etc.)

        Format your response as JSON:
        {{
            "question_id": "unique_id",
            "topic": "{chunk['topic']}",
            "difficulty": "{difficulty}",
            "scenario": "Background scenario text",
            "sub_questions": [
                {{"part": "A", "question": "Question text", "points": 6}},
                {{"part": "B", "question": "Question text", "points": 8}},
                {{"part": "C", "question": "Question text", "points": 6}}
            ],
            "total_points": 20,
            "estimated_time_minutes": 18,
            "answer_key": [
                {{"part": "A", "answer": "Detailed answer with bullet points", "rubric": "Grading criteria"}},
                {{"part": "B", "answer": "Detailed answer with bullet points", "rubric": "Grading criteria"}},
                {{"part": "C", "answer": "Detailed answer with bullet points", "rubric": "Grading criteria"}}
            ],
            "learning_objectives": ["LO1", "LO2", "LO3"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000
            )
            
            question_data = json.loads(response.choices[0].message.content)
            question_data["type"] = "constructed_response"
            question_data["session"] = "AM"
            question_data["source_chunk"] = chunk["chunk_id"]
            
            return question_data
            
        except Exception as e:
            print(f"Error generating constructed response question: {str(e)}")
            return None
    
    def generate_item_set_question(self, chunk: Dict, difficulty: str = "Level_2") -> Dict:
        """Generate PM session item set with 3 MCQs"""
        
        prompt = f"""
        You are a CFA Level III exam question writer. Based on the following content chunk, create ONE item set with 3 multiple choice questions that matches the real CFA Level III PM session format.

        Content Topic: {chunk['topic']}
        Content: {chunk['content'][:1500]}...

        Requirements:
        1. Create a realistic vignette (case study scenario)
        2. Follow with exactly 3 multiple choice questions
        3. Each question should have 4 options (A, B, C, D)
        4. Questions should build on the vignette and each other
        5. Difficulty level: {difficulty} - {DIFFICULTY_LEVELS[difficulty]['description']}
        6. Follow CFA Institute writing style and terminology
        7. Include calculations where appropriate

        Format your response as JSON:
        {{
            "item_set_id": "unique_id",
            "topic": "{chunk['topic']}",
            "difficulty": "{difficulty}",
            "vignette": "Background scenario/case study text",
            "questions": [
                {{
                    "question_number": 1,
                    "question_text": "Question 1 text",
                    "options": {{
                        "A": "Option A text",
                        "B": "Option B text", 
                        "C": "Option C text",
                        "D": "Option D text"
                    }},
                    "correct_answer": "B",
                    "explanation": "Detailed explanation of why B is correct and others are wrong",
                    "points": 6
                }},
                {{
                    "question_number": 2,
                    "question_text": "Question 2 text",
                    "options": {{
                        "A": "Option A text",
                        "B": "Option B text",
                        "C": "Option C text", 
                        "D": "Option D text"
                    }},
                    "correct_answer": "C",
                    "explanation": "Detailed explanation of why C is correct and others are wrong",
                    "points": 6
                }},
                {{
                    "question_number": 3,
                    "question_text": "Question 3 text",
                    "options": {{
                        "A": "Option A text",
                        "B": "Option B text",
                        "C": "Option C text",
                        "D": "Option D text"
                    }},
                    "correct_answer": "A",
                    "explanation": "Detailed explanation of why A is correct and others are wrong", 
                    "points": 6
                }}
            ],
            "total_points": 18,
            "estimated_time_minutes": 15,
            "learning_objectives": ["LO1", "LO2", "LO3"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2500
            )
            
            question_data = json.loads(response.choices[0].message.content)
            question_data["type"] = "item_set"
            question_data["session"] = "PM"
            question_data["source_chunk"] = chunk["chunk_id"]
            
            return question_data
            
        except Exception as e:
            print(f"Error generating item set question: {str(e)}")
            return None
    
    def generate_questions(self, chunk: Dict, question_type: str = "constructed") -> Dict:
        """
        Main function to generate questions as specified in requirements
        """
        if question_type == "constructed":
            return self.generate_constructed_response_question(chunk)
        elif question_type == "item_set":
            return self.generate_item_set_question(chunk)
        else:
            raise ValueError("question_type must be 'constructed' or 'item_set'")
    
    def generate_questions_for_topic(self, topic_chunks: List[Dict], question_type: str, 
                                   num_questions: int) -> List[Dict]:
        """Generate multiple questions for a specific topic"""
        questions = []
        
        # Randomly sample chunks to avoid repetition
        selected_chunks = random.sample(topic_chunks, min(num_questions, len(topic_chunks)))
        
        for chunk in selected_chunks:
            # Vary difficulty levels
            difficulty = random.choices(
                list(DIFFICULTY_LEVELS.keys()),
                weights=[DIFFICULTY_LEVELS[d]["weight"] for d in DIFFICULTY_LEVELS.keys()]
            )[0]
            
            if question_type == "constructed":
                question = self.generate_constructed_response_question(chunk, difficulty)
            else:
                question = self.generate_item_set_question(chunk, difficulty)
            
            if question:
                questions.append(question)
        
        return questions
    
    def save_questions_to_json(self, questions: List[Dict], filename: str):
        """Save generated questions to JSON file"""
        os.makedirs("data/generated_questions", exist_ok=True)
        filepath = f"data/generated_questions/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(questions, f, indent=2, ensure_ascii=False)
        
        print(f"Saved {len(questions)} questions to {filepath}")
    
    def load_questions_from_json(self, filename: str) -> List[Dict]:
        """Load questions from JSON file"""
        filepath = f"data/generated_questions/{filename}"
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            return questions
        except FileNotFoundError:
            print(f"File not found: {filepath}")
            return []
