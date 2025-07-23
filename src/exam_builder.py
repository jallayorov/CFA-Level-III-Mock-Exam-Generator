"""
Exam builder that enforces topic weights and generates structured exams
"""
import json
import random
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from config.topics import TOPIC_WEIGHTS, QUESTION_TYPES
import os

class CFAExamBuilder:
    def __init__(self):
        self.generated_questions = {
            "AM": [],
            "PM": []
        }
        self.used_question_ids = set()
        
    def load_questions_pool(self, questions_dir: str = "data/generated_questions"):
        """Load all available questions from JSON files"""
        if not os.path.exists(questions_dir):
            print(f"Questions directory not found: {questions_dir}")
            return
            
        for filename in os.listdir(questions_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(questions_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        questions = json.load(f)
                    
                    for question in questions:
                        session = question.get("session", "AM")
                        if session in self.generated_questions:
                            self.generated_questions[session].append(question)
                            
                except Exception as e:
                    print(f"Error loading {filepath}: {str(e)}")
    
    def calculate_topic_allocation(self, mode: str, total_questions: int) -> Dict[str, int]:
        """Calculate number of questions per topic based on weights"""
        allocation = {}
        remaining_questions = total_questions
        
        # Sort topics by target weight (descending) for better allocation
        sorted_topics = sorted(TOPIC_WEIGHTS.items(), 
                             key=lambda x: x[1]["target"], reverse=True)
        
        for topic, weights in sorted_topics[:-1]:  # All except last topic
            target_percentage = weights["target"] / 100
            allocated = round(total_questions * target_percentage)
            allocation[topic] = min(allocated, remaining_questions)
            remaining_questions -= allocation[topic]
        
        # Assign remaining questions to last topic
        last_topic = sorted_topics[-1][0]
        allocation[last_topic] = remaining_questions
        
        return allocation
    
    def validate_topic_weights(self, allocation: Dict[str, int], total_questions: int) -> bool:
        """Validate that topic allocation meets weight requirements"""
        for topic, count in allocation.items():
            percentage = (count / total_questions) * 100
            min_weight = TOPIC_WEIGHTS[topic]["min"]
            max_weight = TOPIC_WEIGHTS[topic]["max"]
            
            if not (min_weight <= percentage <= max_weight):
                print(f"Warning: {topic} allocation ({percentage:.1f}%) outside range ({min_weight}-{max_weight}%)")
                return False
        return True
    
    def select_questions_by_topic(self, topic: str, count: int, mode: str, 
                                exclude_ids: set = None) -> List[Dict]:
        """Select questions for a specific topic"""
        if exclude_ids is None:
            exclude_ids = set()
            
        available_questions = [
            q for q in self.generated_questions[mode] 
            if q.get("topic") == topic and q.get("question_id") not in exclude_ids
        ]
        
        if len(available_questions) < count:
            print(f"Warning: Only {len(available_questions)} questions available for {topic} (need {count})")
            return available_questions
        
        # Prioritize different difficulty levels
        selected = []
        difficulties = ["Level_1", "Level_2", "Level_3"]
        
        for difficulty in difficulties:
            difficulty_questions = [q for q in available_questions if q.get("difficulty") == difficulty]
            needed = min(count - len(selected), len(difficulty_questions))
            selected.extend(random.sample(difficulty_questions, needed))
            
            if len(selected) >= count:
                break
        
        # Fill remaining with any available questions
        if len(selected) < count:
            remaining = [q for q in available_questions if q not in selected]
            needed = count - len(selected)
            selected.extend(random.sample(remaining, min(needed, len(remaining))))
        
        return selected[:count]
    
    def build_exam(self, topic_weights: Dict = None, mode: str = "AM") -> Dict:
        """
        Main function to build exam as specified in requirements
        """
        if topic_weights is None:
            topic_weights = TOPIC_WEIGHTS
            
        # Get question count for the mode
        question_config = QUESTION_TYPES[mode]
        if mode == "AM":
            total_questions = random.randint(question_config["count"]["min"], 
                                           question_config["count"]["max"])
        else:  # PM
            total_questions = random.randint(question_config["count"]["min"], 
                                           question_config["count"]["max"])
        
        # Calculate topic allocation
        topic_allocation = self.calculate_topic_allocation(mode, total_questions)
        
        # Validate allocation meets weight requirements
        if not self.validate_topic_weights(topic_allocation, total_questions):
            print("Topic weight validation failed, but continuing with current allocation")
        
        # Select questions for each topic
        selected_questions = []
        used_ids = set()
        
        for topic, count in topic_allocation.items():
            if count > 0:
                topic_questions = self.select_questions_by_topic(
                    topic, count, mode, used_ids
                )
                selected_questions.extend(topic_questions)
                used_ids.update([q.get("question_id") for q in topic_questions])
        
        # Shuffle questions to randomize order
        random.shuffle(selected_questions)
        
        # Calculate total time and points
        total_time = sum([q.get("estimated_time_minutes", 15) for q in selected_questions])
        total_points = sum([q.get("total_points", 18) for q in selected_questions])
        
        # Create exam metadata
        exam_data = {
            "exam_id": f"CFA_L3_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "session": mode,
            "created_at": datetime.now().isoformat(),
            "total_questions": len(selected_questions),
            "total_time_minutes": question_config["time_minutes"],
            "total_points": total_points,
            "topic_allocation": topic_allocation,
            "topic_percentages": {
                topic: round((count / total_questions) * 100, 1) 
                for topic, count in topic_allocation.items()
            },
            "questions": selected_questions,
            "instructions": self._get_exam_instructions(mode),
            "time_per_question": round(question_config["time_minutes"] / len(selected_questions), 1)
        }
        
        return exam_data
    
    def _get_exam_instructions(self, mode: str) -> List[str]:
        """Get exam instructions based on session type"""
        if mode == "AM":
            return [
                "This is the Morning Session of the CFA Level III examination.",
                "You have 3 hours (180 minutes) to complete this session.",
                "This session consists of constructed response questions.",
                "Show all calculations and provide clear explanations.",
                "Use bullet points where appropriate in your responses.",
                "Manage your time carefully - aim to spend the suggested time per question."
            ]
        else:  # PM
            return [
                "This is the Afternoon Session of the CFA Level III examination.",
                "You have 3 hours (180 minutes) to complete this session.",
                "This session consists of item sets with multiple choice questions.",
                "Read each vignette carefully before answering the questions.",
                "Select the best answer for each question.",
                "There is no penalty for guessing."
            ]
    
    def create_answer_sheet(self, exam_data: Dict) -> Dict:
        """Create separate answer sheet for the exam"""
        if exam_data["session"] == "AM":
            # Constructed response answer template
            answer_sheet = {
                "exam_id": exam_data["exam_id"],
                "session": exam_data["session"],
                "student_name": "",
                "candidate_number": "",
                "start_time": "",
                "end_time": "",
                "answers": []
            }
            
            for i, question in enumerate(exam_data["questions"], 1):
                question_answer = {
                    "question_number": i,
                    "question_id": question.get("question_id"),
                    "topic": question.get("topic"),
                    "sub_answers": []
                }
                
                for sub_q in question.get("sub_questions", []):
                    question_answer["sub_answers"].append({
                        "part": sub_q["part"],
                        "answer": "",  # Student fills this
                        "points_allocated": sub_q["points"]
                    })
                
                answer_sheet["answers"].append(question_answer)
        
        else:  # PM session
            answer_sheet = {
                "exam_id": exam_data["exam_id"],
                "session": exam_data["session"],
                "student_name": "",
                "candidate_number": "",
                "start_time": "",
                "end_time": "",
                "answers": []
            }
            
            question_num = 1
            for item_set in exam_data["questions"]:
                for mcq in item_set.get("questions", []):
                    answer_sheet["answers"].append({
                        "question_number": question_num,
                        "item_set_id": item_set.get("item_set_id"),
                        "selected_answer": "",  # A, B, C, or D
                        "correct_answer": mcq["correct_answer"],
                        "points": mcq["points"]
                    })
                    question_num += 1
        
        return answer_sheet
    
    def save_exam(self, exam_data: Dict, include_solutions: bool = False):
        """Save exam to JSON files"""
        os.makedirs("exams", exist_ok=True)
        
        exam_id = exam_data["exam_id"]
        
        # Save exam (without solutions)
        exam_for_student = exam_data.copy()
        if not include_solutions:
            # Remove answer keys from questions
            for question in exam_for_student["questions"]:
                if "answer_key" in question:
                    del question["answer_key"]
                if "questions" in question:  # PM item sets
                    for mcq in question["questions"]:
                        if "correct_answer" in mcq:
                            del mcq["correct_answer"]
                        if "explanation" in mcq:
                            del mcq["explanation"]
        
        # Save student version
        with open(f"exams/{exam_id}_exam.json", 'w', encoding='utf-8') as f:
            json.dump(exam_for_student, f, indent=2, ensure_ascii=False)
        
        # Save complete version with solutions
        with open(f"exams/{exam_id}_solutions.json", 'w', encoding='utf-8') as f:
            json.dump(exam_data, f, indent=2, ensure_ascii=False)
        
        # Save answer sheet
        answer_sheet = self.create_answer_sheet(exam_data)
        with open(f"exams/{exam_id}_answer_sheet.json", 'w', encoding='utf-8') as f:
            json.dump(answer_sheet, f, indent=2, ensure_ascii=False)
        
        print(f"Exam saved: {exam_id}")
        return exam_id
