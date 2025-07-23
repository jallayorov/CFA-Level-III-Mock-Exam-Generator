"""
Grading engine for CFA Level III mock exams
"""
import json
from typing import List, Dict, Optional, Tuple
from openai import OpenAI
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

class CFAGradingEngine:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
    
    def grade_pm_session(self, answer_sheet: Dict, solutions: Dict) -> Dict:
        """Automatically grade PM (multiple choice) session"""
        total_questions = len(answer_sheet["answers"])
        correct_answers = 0
        total_points = 0
        earned_points = 0
        
        graded_answers = []
        topic_performance = {}
        
        # Match answers with solutions
        solution_questions = {}
        for item_set in solutions["questions"]:
            for i, mcq in enumerate(item_set.get("questions", [])):
                question_key = f"{item_set.get('item_set_id')}_{i+1}"
                solution_questions[question_key] = {
                    "correct_answer": mcq["correct_answer"],
                    "explanation": mcq["explanation"],
                    "points": mcq["points"],
                    "topic": item_set.get("topic")
                }
        
        # Grade each answer
        for i, student_answer in enumerate(answer_sheet["answers"]):
            question_num = student_answer["question_number"]
            item_set_id = student_answer["item_set_id"]
            selected = student_answer["selected_answer"].upper()
            
            # Find corresponding solution
            question_key = f"{item_set_id}_{question_num}"
            if question_key in solution_questions:
                solution = solution_questions[question_key]
                correct = solution["correct_answer"].upper()
                points = solution["points"]
                topic = solution["topic"]
                
                is_correct = (selected == correct)
                points_earned = points if is_correct else 0
                
                if is_correct:
                    correct_answers += 1
                
                total_points += points
                earned_points += points_earned
                
                # Track topic performance
                if topic not in topic_performance:
                    topic_performance[topic] = {"correct": 0, "total": 0, "points_earned": 0, "points_possible": 0}
                
                topic_performance[topic]["total"] += 1
                topic_performance[topic]["points_possible"] += points
                if is_correct:
                    topic_performance[topic]["correct"] += 1
                    topic_performance[topic]["points_earned"] += points_earned
                
                graded_answers.append({
                    "question_number": question_num,
                    "topic": topic,
                    "selected_answer": selected,
                    "correct_answer": correct,
                    "is_correct": is_correct,
                    "points_earned": points_earned,
                    "points_possible": points,
                    "explanation": solution["explanation"]
                })
        
        # Calculate percentages
        overall_percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        accuracy_percentage = (correct_answers / total_questions * 100) if total_questions > 0 else 0
        
        # Calculate topic percentages
        for topic in topic_performance:
            perf = topic_performance[topic]
            perf["percentage"] = (perf["points_earned"] / perf["points_possible"] * 100) if perf["points_possible"] > 0 else 0
            perf["accuracy"] = (perf["correct"] / perf["total"] * 100) if perf["total"] > 0 else 0
        
        return {
            "session": "PM",
            "graded_at": datetime.now().isoformat(),
            "overall_score": {
                "points_earned": earned_points,
                "points_possible": total_points,
                "percentage": round(overall_percentage, 1),
                "accuracy": round(accuracy_percentage, 1)
            },
            "topic_performance": topic_performance,
            "detailed_answers": graded_answers,
            "summary": {
                "total_questions": total_questions,
                "correct_answers": correct_answers,
                "passing_score": 70,  # Typical CFA passing threshold
                "result": "PASS" if overall_percentage >= 70 else "FAIL"
            }
        }
    
    def grade_am_question_with_ai(self, student_answer: str, model_answer: Dict, 
                                 rubric: str, topic: str) -> Dict:
        """Use AI to grade a single AM constructed response question"""
        
        prompt = f"""
        You are a CFA Level III exam grader. Grade the following student answer against the model answer and rubric.

        Topic: {topic}
        
        Model Answer: {model_answer.get('answer', '')}
        
        Grading Rubric: {rubric}
        
        Student Answer: {student_answer}
        
        Instructions:
        1. Compare the student answer to the model answer
        2. Apply the grading rubric strictly
        3. Award partial credit where appropriate
        4. Provide specific feedback on what was correct/incorrect
        5. Be consistent with CFA grading standards
        
        Respond in JSON format:
        {{
            "points_earned": <number>,
            "points_possible": <number>,
            "percentage": <percentage>,
            "feedback": "Detailed feedback explaining the grade",
            "strengths": ["What the student did well"],
            "areas_for_improvement": ["What needs improvement"],
            "key_concepts_missed": ["Important concepts not addressed"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Lower temperature for consistent grading
                max_tokens=800
            )
            
            grading_result = json.loads(response.choices[0].message.content)
            return grading_result
            
        except Exception as e:
            print(f"Error in AI grading: {str(e)}")
            return {
                "points_earned": 0,
                "points_possible": model_answer.get("points", 0),
                "percentage": 0,
                "feedback": "Error occurred during grading",
                "strengths": [],
                "areas_for_improvement": ["Unable to grade due to technical error"],
                "key_concepts_missed": []
            }
    
    def grade_am_session(self, answer_sheet: Dict, solutions: Dict, 
                        use_ai_grading: bool = True) -> Dict:
        """Grade AM (constructed response) session"""
        total_points = 0
        earned_points = 0
        topic_performance = {}
        graded_answers = []
        
        # Create solution lookup
        solution_lookup = {}
        for question in solutions["questions"]:
            question_id = question.get("question_id")
            solution_lookup[question_id] = question
        
        # Grade each question
        for student_question in answer_sheet["answers"]:
            question_id = student_question["question_id"]
            topic = student_question["topic"]
            
            if question_id in solution_lookup:
                solution_question = solution_lookup[question_id]
                question_total_points = 0
                question_earned_points = 0
                
                graded_sub_answers = []
                
                # Grade each sub-question
                for sub_answer in student_question["sub_answers"]:
                    part = sub_answer["part"]
                    student_text = sub_answer["answer"]
                    points_possible = sub_answer["points_allocated"]
                    
                    # Find corresponding model answer
                    model_sub_answer = None
                    for model_answer in solution_question.get("answer_key", []):
                        if model_answer["part"] == part:
                            model_sub_answer = model_answer
                            break
                    
                    if model_sub_answer and use_ai_grading:
                        # Use AI grading
                        grading_result = self.grade_am_question_with_ai(
                            student_text, 
                            model_sub_answer, 
                            model_sub_answer.get("rubric", ""),
                            topic
                        )
                        points_earned = grading_result["points_earned"]
                        feedback = grading_result["feedback"]
                    else:
                        # Manual grading placeholder (requires human input)
                        points_earned = 0  # Default to 0, requires manual override
                        feedback = "Manual grading required"
                    
                    question_total_points += points_possible
                    question_earned_points += points_earned
                    
                    graded_sub_answers.append({
                        "part": part,
                        "student_answer": student_text,
                        "points_earned": points_earned,
                        "points_possible": points_possible,
                        "feedback": feedback,
                        "model_answer": model_sub_answer.get("answer", "") if model_sub_answer else ""
                    })
                
                total_points += question_total_points
                earned_points += question_earned_points
                
                # Track topic performance
                if topic not in topic_performance:
                    topic_performance[topic] = {"points_earned": 0, "points_possible": 0}
                
                topic_performance[topic]["points_earned"] += question_earned_points
                topic_performance[topic]["points_possible"] += question_total_points
                
                graded_answers.append({
                    "question_number": student_question["question_number"],
                    "question_id": question_id,
                    "topic": topic,
                    "points_earned": question_earned_points,
                    "points_possible": question_total_points,
                    "percentage": round((question_earned_points / question_total_points * 100), 1) if question_total_points > 0 else 0,
                    "sub_answers": graded_sub_answers
                })
        
        # Calculate overall performance
        overall_percentage = (earned_points / total_points * 100) if total_points > 0 else 0
        
        # Calculate topic percentages
        for topic in topic_performance:
            perf = topic_performance[topic]
            perf["percentage"] = (perf["points_earned"] / perf["points_possible"] * 100) if perf["points_possible"] > 0 else 0
        
        return {
            "session": "AM",
            "graded_at": datetime.now().isoformat(),
            "grading_method": "AI-assisted" if use_ai_grading else "Manual",
            "overall_score": {
                "points_earned": earned_points,
                "points_possible": total_points,
                "percentage": round(overall_percentage, 1)
            },
            "topic_performance": topic_performance,
            "detailed_answers": graded_answers,
            "summary": {
                "total_questions": len(graded_answers),
                "passing_score": 70,
                "result": "PASS" if overall_percentage >= 70 else "FAIL"
            }
        }
    
    def grade_exam(self, user_answers: Dict, mode: str, rubric: Optional[Dict] = None) -> Dict:
        """
        Main grading function as specified in requirements
        """
        # Load solutions
        exam_id = user_answers.get("exam_id")
        solutions_path = f"exams/{exam_id}_solutions.json"
        
        try:
            with open(solutions_path, 'r', encoding='utf-8') as f:
                solutions = json.load(f)
        except FileNotFoundError:
            return {"error": f"Solutions file not found: {solutions_path}"}
        
        if mode == "PM":
            return self.grade_pm_session(user_answers, solutions)
        elif mode == "AM":
            return self.grade_am_session(user_answers, solutions, use_ai_grading=True)
        else:
            return {"error": f"Invalid mode: {mode}. Must be 'AM' or 'PM'"}
    
    def save_grading_results(self, grading_results: Dict, exam_id: str):
        """Save grading results to file"""
        os.makedirs("exams/results", exist_ok=True)
        
        session = grading_results["session"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"exams/results/{exam_id}_{session}_results_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(grading_results, f, indent=2, ensure_ascii=False)
        
        print(f"Grading results saved: {filename}")
        return filename
    
    def generate_performance_report(self, grading_results: Dict) -> str:
        """Generate a formatted performance report"""
        session = grading_results["session"]
        overall = grading_results["overall_score"]
        topics = grading_results["topic_performance"]
        
        report = f"""
CFA Level III {session} Session - Performance Report
{'='*50}

Overall Performance:
- Score: {overall['points_earned']}/{overall['points_possible']} ({overall['percentage']}%)
- Result: {grading_results['summary']['result']}

Topic Breakdown:
"""
        
        for topic, perf in topics.items():
            if session == "PM":
                report += f"- {topic}: {perf['points_earned']}/{perf['points_possible']} ({perf['percentage']:.1f}%) - {perf['correct']}/{perf['total']} correct\n"
            else:
                report += f"- {topic}: {perf['points_earned']}/{perf['points_possible']} ({perf['percentage']:.1f}%)\n"
        
        report += f"\nGraded on: {grading_results['graded_at']}\n"
        
        return report
