"""
Simple CFA Level III Mock Exam Generator
Uses plain text instead of complex JSON - much simpler!
"""

import streamlit as st
import json
import os
import openai
from datetime import datetime
import uuid

# Try to import the simple text loader
try:
    from src.simple_text_loader import load_cfa_text_content, get_random_cfa_content, get_content_summary
    TEXT_LOADER_AVAILABLE = True
except ImportError:
    TEXT_LOADER_AVAILABLE = False
    st.error("❌ Simple text loader not available")

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

st.set_page_config(
    page_title="CFA Level III Mock Exam Generator",
    page_icon="🎓",
    layout="wide"
)

def generate_questions_from_text(session_type, cfa_content):
    """Generate questions using simple text content"""
    
    if not cfa_content:
        st.error("❌ No CFA content available for question generation")
        return None
    
    # Get random content for question generation
    content_chunk = get_random_cfa_content(cfa_content, max_chars=4000)
    
    if session_type == "AM":
        prompt = f"""
Based on this CFA Level III content, create 1 AM session constructed response question.

Content: {content_chunk}

Return ONLY a JSON object with this structure:
{{
    "question": "Detailed scenario and question text",
    "points": 15,
    "topic": "Portfolio Management",
    "answer_guidance": "Key points for grading"
}}
"""
    else:  # PM
        prompt = f"""
Based on this CFA Level III content, create 1 PM session item set with 3 multiple choice questions.

Content: {content_chunk}

Return ONLY a JSON object with this structure:
{{
    "vignette": "Case study scenario",
    "questions": [
        {{
            "question": "Question 1 text",
            "options": ["A. Option A", "B. Option B", "C. Option C"],
            "correct": "A",
            "explanation": "Why A is correct"
        }},
        {{
            "question": "Question 2 text", 
            "options": ["A. Option A", "B. Option B", "C. Option C"],
            "correct": "B",
            "explanation": "Why B is correct"
        }},
        {{
            "question": "Question 3 text",
            "options": ["A. Option A", "B. Option B", "C. Option C"], 
            "correct": "C",
            "explanation": "Why C is correct"
        }}
    ]
}}
"""
    
    try:
        response = openai.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000
        )
        
        # Clean response
        raw_response = response.choices[0].message.content.strip()
        if raw_response.startswith('```json'):
            raw_response = raw_response[7:]
        if raw_response.endswith('```'):
            raw_response = raw_response[:-3]
        raw_response = raw_response.strip()
        
        question_data = json.loads(raw_response)
        return question_data
        
    except Exception as e:
        st.error(f"❌ Error generating questions: {str(e)}")
        return None

def main():
    st.title("🎓 CFA Level III Mock Exam Generator")
    st.subheader("Simple Text-Based System - Much Faster! 🚀")
    
    # Load CFA content
    if TEXT_LOADER_AVAILABLE:
        if 'cfa_content' not in st.session_state:
            with st.spinner("📚 Loading CFA text content..."):
                st.session_state.cfa_content = load_cfa_text_content()
        
        cfa_content = st.session_state.cfa_content
        
        if cfa_content:
            # Show content summary
            summary = get_content_summary(cfa_content)
            st.success(f"✅ Loaded {summary['total_files']} CFA books ({summary['total_characters']:,} characters)")
            
            # Session selection
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🌅 AM Session")
                if st.button("Generate AM Question", key="am_btn"):
                    with st.spinner("🤖 Generating AM question from your CFA books..."):
                        am_question = generate_questions_from_text("AM", cfa_content)
                        if am_question:
                            st.session_state.am_question = am_question
                
                # Display AM question
                if 'am_question' in st.session_state:
                    q = st.session_state.am_question
                    st.write("**Question:**")
                    st.write(q.get('question', 'No question generated'))
                    st.write(f"**Points:** {q.get('points', 0)}")
                    st.write(f"**Topic:** {q.get('topic', 'Unknown')}")
                    
                    # Answer input
                    answer = st.text_area("Your Answer:", key="am_answer", height=150)
                    
                    if st.button("Show Answer Guidance", key="am_show"):
                        st.info(f"**Answer Guidance:** {q.get('answer_guidance', 'No guidance available')}")
            
            with col2:
                st.subheader("🌆 PM Session")
                if st.button("Generate PM Item Set", key="pm_btn"):
                    with st.spinner("🤖 Generating PM questions from your CFA books..."):
                        pm_questions = generate_questions_from_text("PM", cfa_content)
                        if pm_questions:
                            st.session_state.pm_questions = pm_questions
                
                # Display PM questions
                if 'pm_questions' in st.session_state:
                    q_set = st.session_state.pm_questions
                    st.write("**Vignette:**")
                    st.write(q_set.get('vignette', 'No vignette'))
                    
                    # Questions
                    for i, q in enumerate(q_set.get('questions', [])):
                        st.write(f"**Question {i+1}:** {q.get('question', '')}")
                        
                        # Options
                        selected = st.radio(
                            f"Select answer for Q{i+1}:",
                            q.get('options', ['A. No options', 'B. Available', 'C. Yet']),
                            key=f"pm_q{i}"
                        )
                        
                        # Show explanation button
                        if st.button(f"Show Explanation Q{i+1}", key=f"pm_exp{i}"):
                            correct = q.get('correct', 'A')
                            explanation = q.get('explanation', 'No explanation')
                            if selected.startswith(correct):
                                st.success(f"✅ Correct! {explanation}")
                            else:
                                st.error(f"❌ Incorrect. Correct answer: {correct}. {explanation}")
        
        else:
            st.error("❌ Failed to load CFA content")
            st.info("💡 Make sure the text files are in data/cfa_text_content/")
    
    else:
        st.error("❌ Text loader not available")
    
    # Footer
    st.markdown("---")
    st.markdown("**🎯 Simple Text-Based CFA Exam Generator - No Complex JSON!**")

if __name__ == "__main__":
    main()
