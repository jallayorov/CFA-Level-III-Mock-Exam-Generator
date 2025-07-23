"""
Export utilities for CFA mock exams (PDF and JSON formats)
"""
import json
import os
from typing import Dict, List
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime

class CFAExportUtils:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom styles for PDF generation"""
        self.styles.add(ParagraphStyle(
            name='CFATitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=1,  # Center alignment
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='CFASubtitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            spaceAfter=12,
            textColor=colors.darkblue
        ))
        
        self.styles.add(ParagraphStyle(
            name='CFAQuestion',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            leftIndent=0.25*inch
        ))
        
        self.styles.add(ParagraphStyle(
            name='CFAAnswer',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            leftIndent=0.5*inch,
            textColor=colors.darkgreen
        ))
    
    def export_exam_to_pdf(self, exam_data: Dict, include_solutions: bool = False) -> str:
        """Export exam to PDF format"""
        exam_id = exam_data["exam_id"]
        session = exam_data["session"]
        
        # Create filename
        suffix = "_with_solutions" if include_solutions else ""
        filename = f"exams/{exam_id}{suffix}.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(filename, pagesize=A4, 
                              rightMargin=0.75*inch, leftMargin=0.75*inch,
                              topMargin=1*inch, bottomMargin=1*inch)
        
        story = []
        
        # Title page
        story.append(Paragraph("CFA Institute", self.styles['CFATitle']))
        story.append(Paragraph(f"Level III {session} Session Mock Exam", self.styles['CFATitle']))
        story.append(Spacer(1, 0.5*inch))
        
        # Exam information
        info_data = [
            ["Exam ID:", exam_id],
            ["Session:", f"{session} ({'Morning' if session == 'AM' else 'Afternoon'})"],
            ["Time Allowed:", f"{exam_data['total_time_minutes']} minutes"],
            ["Total Questions:", str(exam_data['total_questions'])],
            ["Total Points:", str(exam_data['total_points'])],
            ["Date:", datetime.now().strftime("%B %d, %Y")]
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(info_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Instructions
        story.append(Paragraph("Instructions:", self.styles['CFASubtitle']))
        for instruction in exam_data.get("instructions", []):
            story.append(Paragraph(f"• {instruction}", self.styles['Normal']))
        
        story.append(PageBreak())
        
        # Questions
        if session == "AM":
            self._add_am_questions_to_story(story, exam_data["questions"], include_solutions)
        else:
            self._add_pm_questions_to_story(story, exam_data["questions"], include_solutions)
        
        # Build PDF
        doc.build(story)
        print(f"Exam exported to PDF: {filename}")
        return filename
    
    def _add_am_questions_to_story(self, story: List, questions: List[Dict], include_solutions: bool):
        """Add AM (constructed response) questions to PDF story"""
        for i, question in enumerate(questions, 1):
            # Question header
            story.append(Paragraph(f"Question {i} - {question.get('topic', 'General')} "
                                 f"({question.get('total_points', 0)} points)", 
                                 self.styles['CFASubtitle']))
            
            # Scenario
            if 'scenario' in question:
                story.append(Paragraph("Scenario:", self.styles['Heading3']))
                story.append(Paragraph(question['scenario'], self.styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
            
            # Sub-questions
            for sub_q in question.get('sub_questions', []):
                story.append(Paragraph(f"{sub_q['part']}. {sub_q['question']} ({sub_q['points']} points)",
                                     self.styles['CFAQuestion']))
                
                if include_solutions:
                    # Find corresponding answer
                    for answer in question.get('answer_key', []):
                        if answer['part'] == sub_q['part']:
                            story.append(Paragraph(f"Answer: {answer['answer']}", 
                                                 self.styles['CFAAnswer']))
                            break
                else:
                    # Add space for student answer
                    story.append(Spacer(1, 1*inch))
            
            if i < len(questions):
                story.append(PageBreak())
    
    def _add_pm_questions_to_story(self, story: List, item_sets: List[Dict], include_solutions: bool):
        """Add PM (item set) questions to PDF story"""
        question_num = 1
        
        for i, item_set in enumerate(item_sets, 1):
            # Item set header
            story.append(Paragraph(f"Item Set {i} - {item_set.get('topic', 'General')}", 
                                 self.styles['CFASubtitle']))
            
            # Vignette
            if 'vignette' in item_set:
                story.append(Paragraph(item_set['vignette'], self.styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
            
            # Questions
            for mcq in item_set.get('questions', []):
                story.append(Paragraph(f"{question_num}. {mcq['question_text']}", 
                                     self.styles['CFAQuestion']))
                
                # Options
                for option, text in mcq['options'].items():
                    story.append(Paragraph(f"   {option}. {text}", self.styles['Normal']))
                
                if include_solutions:
                    story.append(Paragraph(f"Correct Answer: {mcq['correct_answer']}", 
                                         self.styles['CFAAnswer']))
                    story.append(Paragraph(f"Explanation: {mcq['explanation']}", 
                                         self.styles['CFAAnswer']))
                
                story.append(Spacer(1, 0.15*inch))
                question_num += 1
            
            if i < len(item_sets):
                story.append(PageBreak())
    
    def export_exam_to_json(self, exam_data: Dict, format_type: str = "complete") -> str:
        """Export exam to JSON format"""
        exam_id = exam_data["exam_id"]
        
        if format_type == "student":
            # Remove solutions for student version
            clean_data = self._remove_solutions_from_exam(exam_data)
            filename = f"exams/{exam_id}_student.json"
        else:
            clean_data = exam_data
            filename = f"exams/{exam_id}_complete.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(clean_data, f, indent=2, ensure_ascii=False)
        
        print(f"Exam exported to JSON: {filename}")
        return filename
    
    def _remove_solutions_from_exam(self, exam_data: Dict) -> Dict:
        """Remove solutions from exam data for student version"""
        clean_data = exam_data.copy()
        clean_questions = []
        
        for question in clean_data["questions"]:
            clean_question = question.copy()
            
            # Remove answer keys from AM questions
            if "answer_key" in clean_question:
                del clean_question["answer_key"]
            
            # Remove solutions from PM questions
            if "questions" in clean_question:  # Item set
                clean_mcqs = []
                for mcq in clean_question["questions"]:
                    clean_mcq = mcq.copy()
                    if "correct_answer" in clean_mcq:
                        del clean_mcq["correct_answer"]
                    if "explanation" in clean_mcq:
                        del clean_mcq["explanation"]
                    clean_mcqs.append(clean_mcq)
                clean_question["questions"] = clean_mcqs
            
            clean_questions.append(clean_question)
        
        clean_data["questions"] = clean_questions
        return clean_data
    
    def export_results_to_pdf(self, grading_results: Dict, exam_data: Dict) -> str:
        """Export grading results to PDF"""
        exam_id = exam_data["exam_id"]
        session = grading_results["session"]
        filename = f"exams/results/{exam_id}_{session}_report.pdf"
        
        os.makedirs("exams/results", exist_ok=True)
        
        doc = SimpleDocTemplate(filename, pagesize=A4,
                              rightMargin=0.75*inch, leftMargin=0.75*inch,
                              topMargin=1*inch, bottomMargin=1*inch)
        
        story = []
        
        # Title
        story.append(Paragraph("CFA Level III Performance Report", self.styles['CFATitle']))
        story.append(Paragraph(f"{session} Session Results", self.styles['CFASubtitle']))
        story.append(Spacer(1, 0.3*inch))
        
        # Overall performance
        overall = grading_results["overall_score"]
        story.append(Paragraph("Overall Performance", self.styles['CFASubtitle']))
        
        overall_data = [
            ["Points Earned:", f"{overall['points_earned']}/{overall['points_possible']}"],
            ["Percentage:", f"{overall['percentage']}%"],
            ["Result:", grading_results['summary']['result']],
            ["Passing Score:", f"{grading_results['summary']['passing_score']}%"]
        ]
        
        overall_table = Table(overall_data, colWidths=[2*inch, 2*inch])
        overall_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(overall_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Topic performance
        story.append(Paragraph("Performance by Topic", self.styles['CFASubtitle']))
        
        topic_data = [["Topic", "Score", "Percentage"]]
        for topic, perf in grading_results["topic_performance"].items():
            topic_data.append([
                topic,
                f"{perf['points_earned']}/{perf['points_possible']}",
                f"{perf['percentage']:.1f}%"
            ])
        
        topic_table = Table(topic_data, colWidths=[3*inch, 1.5*inch, 1.5*inch])
        topic_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.beige, colors.white]),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(topic_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Detailed feedback (if available)
        if session == "AM" and "detailed_answers" in grading_results:
            story.append(PageBreak())
            story.append(Paragraph("Detailed Feedback", self.styles['CFASubtitle']))
            
            for answer in grading_results["detailed_answers"]:
                story.append(Paragraph(f"Question {answer['question_number']} - {answer['topic']}", 
                                     self.styles['Heading3']))
                story.append(Paragraph(f"Score: {answer['points_earned']}/{answer['points_possible']} "
                                     f"({answer['percentage']}%)", self.styles['Normal']))
                
                for sub_answer in answer.get("sub_answers", []):
                    if "feedback" in sub_answer and sub_answer["feedback"]:
                        story.append(Paragraph(f"Part {sub_answer['part']}: {sub_answer['feedback']}", 
                                             self.styles['Normal']))
                
                story.append(Spacer(1, 0.2*inch))
        
        doc.build(story)
        print(f"Results report exported to PDF: {filename}")
        return filename

def export_exam(exam_data: Dict, format: str = "pdf") -> str:
    """
    Main export function as specified in requirements
    """
    exporter = CFAExportUtils()
    
    if format.lower() == "pdf":
        return exporter.export_exam_to_pdf(exam_data, include_solutions=False)
    elif format.lower() == "json":
        return exporter.export_exam_to_json(exam_data, format_type="student")
    else:
        raise ValueError("Format must be 'pdf' or 'json'")
