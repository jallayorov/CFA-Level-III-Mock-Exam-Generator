"""
Enhanced CFA Level III Mock Exam Generator
Combines simple text-based approach with full exam features:
- Live JavaScript timer
- Answer input and persistence  
- AI grading and evaluation
- Session management
"""

import streamlit as st
import json
import os
import openai
from datetime import datetime, timedelta
import uuid
import time

# Try to import the enhanced question generator and text loader
try:
    from src.simple_text_loader import load_cfa_text_content, get_content_summary
    from src.enhanced_question_generator import (
        generate_unique_questions_from_text, 
        get_topic_distribution_summary,
        CFA_TOPIC_WEIGHTS
    )
    TEXT_LOADER_AVAILABLE = True
except ImportError as e:
    TEXT_LOADER_AVAILABLE = False
    st.error(f"❌ Enhanced question generator not available: {e}")

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

# Session persistence functions
def ensure_session_dirs():
    """Ensure session directories exist"""
    os.makedirs("data/exam_sessions", exist_ok=True)

def save_session_state():
    """Save current session state to file"""
    if 'session_id' not in st.session_state:
        return
    
    ensure_session_dirs()
    session_file = f"data/exam_sessions/{st.session_state.session_id}.json"
    
    session_data = {
        'session_id': st.session_state.session_id,
        'exam_mode': st.session_state.get('exam_mode', 'practice'),
        'timer_start': st.session_state.get('timer_start', None),
        'timer_duration': st.session_state.get('timer_duration', 180),
        'am_questions': st.session_state.get('am_questions', []),
        'pm_questions': st.session_state.get('pm_questions', []),
        'am_answers': st.session_state.get('am_answers', {}),
        'pm_answers': st.session_state.get('pm_answers', {}),
        'exam_submitted': st.session_state.get('exam_submitted', False),
        'results': st.session_state.get('results', {}),
        'last_updated': datetime.now().isoformat()
    }
    
    try:
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
    except Exception as e:
        st.error(f"Error saving session: {e}")

def load_session_state():
    """Load session state from file"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())[:8]
    
    session_file = f"data/exam_sessions/{st.session_state.session_id}.json"
    
    if os.path.exists(session_file):
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Restore session state
            for key, value in session_data.items():
                if key != 'session_id':  # Don't overwrite session_id
                    st.session_state[key] = value
                    
        except Exception as e:
            st.error(f"Error loading session: {e}")

# Remove old function - now using enhanced generator from imported module

def grade_am_answer(question, answer):
    """Grade AM constructed response using AI"""
    if not answer.strip():
        return {"score": 0, "feedback": "No answer provided"}
    
    prompt = f"""
Grade this CFA Level III AM constructed response answer.

Question: {question.get('question', '')}
Answer Guidance: {question.get('answer_guidance', '')}
Student Answer: {answer}
Total Points: {question.get('points', 15)}

Provide a JSON response with:
{{
    "score": [0-{question.get('points', 15)}],
    "feedback": "Detailed feedback on the answer",
    "key_points_covered": ["point1", "point2"],
    "areas_for_improvement": ["area1", "area2"]
}}
"""
    
    try:
        response = openai.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        
        raw_response = response.choices[0].message.content.strip()
        if raw_response.startswith('```json'):
            raw_response = raw_response[7:]
        if raw_response.endswith('```'):
            raw_response = raw_response[:-3]
        raw_response = raw_response.strip()
        
        return json.loads(raw_response)
        
    except Exception as e:
        return {"score": 0, "feedback": f"Error grading answer: {str(e)}"}

def display_timer():
    """Display live JavaScript timer"""
    if 'timer_start' not in st.session_state or not st.session_state.timer_start:
        return
    
    # Calculate remaining time
    start_time = datetime.fromisoformat(st.session_state.timer_start)
    duration = st.session_state.get('timer_duration', 180)  # 3 hours default
    end_time = start_time + timedelta(minutes=duration)
    
    # JavaScript timer
    timer_html = f"""
    <div style="position: fixed; top: 10px; right: 10px; background: #ff4b4b; color: white; padding: 10px; border-radius: 5px; z-index: 1000; font-weight: bold;">
        <div id="timer">⏱️ Loading...</div>
    </div>
    
    <script>
    function updateTimer() {{
        const endTime = new Date("{end_time.isoformat()}");
        const now = new Date();
        const timeLeft = endTime - now;
        
        if (timeLeft <= 0) {{
            document.getElementById('timer').innerHTML = '⏰ TIME UP!';
            return;
        }}
        
        const hours = Math.floor(timeLeft / (1000 * 60 * 60));
        const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);
        
        document.getElementById('timer').innerHTML = 
            `⏱️ ${{hours.toString().padStart(2, '0')}}:${{minutes.toString().padStart(2, '0')}}:${{seconds.toString().padStart(2, '0')}}`;
    }}
    
    updateTimer();
    setInterval(updateTimer, 1000);
    </script>
    """
    
    st.components.v1.html(timer_html, height=0)

def main():
    st.title("🎓 CFA Level III Mock Exam Generator")
    st.subheader("Enhanced Text-Based System with Full Exam Features! 🚀")
    
    # Initialize session
    load_session_state()
    
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
            
            # Display timer if exam is active
            if st.session_state.get('exam_mode') == 'timed':
                display_timer()
            
            # Sidebar for exam controls
            with st.sidebar:
                st.header("🎯 Exam Controls")
                
                # Session info
                st.info(f"📝 Session: {st.session_state.session_id}")
                
                # Exam mode selection
                exam_mode = st.selectbox(
                    "Exam Mode:",
                    ["practice", "timed"],
                    index=0 if st.session_state.get('exam_mode', 'practice') == 'practice' else 1
                )
                st.session_state.exam_mode = exam_mode
                
                if exam_mode == "timed":
                    duration = st.slider("Timer (minutes):", 60, 240, 180)
                    st.session_state.timer_duration = duration
                    
                    if st.button("🚀 Start Timed Exam"):
                        st.session_state.timer_start = datetime.now().isoformat()
                        st.session_state.exam_submitted = False
                        save_session_state()
                        st.rerun()
                
                # Progress indicator
                if st.session_state.get('am_questions') or st.session_state.get('pm_questions'):
                    st.write("📊 Progress:")
                    am_count = len(st.session_state.get('am_answers', {}))
                    pm_count = len(st.session_state.get('pm_answers', {}))
                    st.write(f"AM Answers: {am_count}")
                    st.write(f"PM Answers: {pm_count}")
                
                # CFA Topic Weights
                st.write("🎯 CFA Level III Topic Weights:")
                for topic, weight in CFA_TOPIC_WEIGHTS.items():
                    st.write(f"  {topic}: {weight*100:.0f}%")
                
                # Current topic distribution
                if st.session_state.get('am_questions') or st.session_state.get('pm_questions'):
                    st.write("📈 Current Question Topics:")
                    all_questions = []
                    if st.session_state.get('am_questions'):
                        all_questions.extend(st.session_state.am_questions)
                    if st.session_state.get('pm_questions'):
                        all_questions.extend(st.session_state.pm_questions)
                    
                    if all_questions:
                        topic_dist = get_topic_distribution_summary(all_questions)
                        for topic, count in topic_dist.items():
                            st.write(f"  {topic}: {count} questions")
                
                # Auto-save indicator
                if st.button("💾 Save Progress"):
                    save_session_state()
                    st.success("✅ Progress saved!")
            
            # Main exam interface
            tab1, tab2, tab3 = st.tabs(["🌅 AM Session", "🌆 PM Session", "📊 Results"])
            
            with tab1:
                st.subheader("AM Session - Constructed Response")
                
                if st.button("Generate AM Questions", key="gen_am"):
                    with st.spinner("🤖 Generating diverse AM questions from your CFA books..."):
                        am_questions = generate_unique_questions_from_text("AM", cfa_content, 4)
                        if am_questions:
                            st.session_state.am_questions = am_questions
                            
                            # Show topic distribution
                            topic_dist = get_topic_distribution_summary(am_questions)
                            st.success(f"✅ Generated 4 AM questions across topics: {', '.join(topic_dist.keys())}")
                            
                            save_session_state()
                            st.rerun()
                
                # Display AM questions
                if st.session_state.get('am_questions'):
                    for i, question in enumerate(st.session_state.am_questions):
                        st.write(f"### Question {i+1}")
                        st.write(question.get('question', 'No question'))
                        st.write(f"**Points:** {question.get('points', 15)}")
                        st.write(f"**Topic:** {question.get('topic', 'Unknown')}")
                        
                        # Answer input
                        answer_key = f"am_answer_{i}"
                        if 'am_answers' not in st.session_state:
                            st.session_state.am_answers = {}
                        
                        answer = st.text_area(
                            f"Your Answer for Question {i+1}:",
                            value=st.session_state.am_answers.get(answer_key, ""),
                            height=150,
                            key=f"am_input_{i}"
                        )
                        
                        # Save answer on change
                        if answer != st.session_state.am_answers.get(answer_key, ""):
                            st.session_state.am_answers[answer_key] = answer
                            save_session_state()
                        
                        # Grade button
                        if st.button(f"Grade Question {i+1}", key=f"grade_am_{i}"):
                            if answer.strip():
                                with st.spinner("🤖 AI grading your answer..."):
                                    grade_result = grade_am_answer(question, answer)
                                    st.session_state[f"am_grade_{i}"] = grade_result
                                    save_session_state()
                            else:
                                st.warning("Please provide an answer first.")
                        
                        # Show grade if available
                        if f"am_grade_{i}" in st.session_state:
                            grade = st.session_state[f"am_grade_{i}"]
                            score = grade.get('score', 0)
                            max_points = question.get('points', 15)
                            
                            if score >= max_points * 0.7:
                                st.success(f"🎉 Score: {score}/{max_points}")
                            elif score >= max_points * 0.5:
                                st.warning(f"⚠️ Score: {score}/{max_points}")
                            else:
                                st.error(f"❌ Score: {score}/{max_points}")
                            
                            st.info(f"**Feedback:** {grade.get('feedback', 'No feedback')}")
                        
                        st.divider()
            
            with tab2:
                st.subheader("PM Session - Item Sets")
                
                if st.button("Generate PM Item Sets", key="gen_pm"):
                    with st.spinner("🤖 Generating diverse PM item sets from your CFA books..."):
                        pm_questions = generate_unique_questions_from_text("PM", cfa_content, 2)
                        if pm_questions:
                            st.session_state.pm_questions = pm_questions
                            
                            # Show topic distribution
                            topic_dist = get_topic_distribution_summary(pm_questions)
                            st.success(f"✅ Generated 2 PM item sets across topics: {', '.join(topic_dist.keys())}")
                            
                            save_session_state()
                            st.rerun()
                
                # Display PM questions
                if st.session_state.get('pm_questions'):
                    for item_idx, item_set in enumerate(st.session_state.pm_questions):
                        st.write(f"### Item Set {item_idx + 1}")
                        st.write("**Vignette:**")
                        st.write(item_set.get('vignette', 'No vignette'))
                        
                        for q_idx, question in enumerate(item_set.get('questions', [])):
                            question_key = f"pm_{item_idx}_{q_idx}"
                            
                            st.write(f"**Question {q_idx + 1}:** {question.get('question', '')}")
                            
                            # Initialize PM answers
                            if 'pm_answers' not in st.session_state:
                                st.session_state.pm_answers = {}
                            
                            # Radio button for answer selection
                            selected = st.radio(
                                f"Select answer:",
                                question.get('options', ['A. No options', 'B. Available', 'C. Yet']),
                                key=f"pm_radio_{item_idx}_{q_idx}",
                                index=0 if question_key not in st.session_state.pm_answers else 
                                      question.get('options', ['A.']).index(st.session_state.pm_answers.get(question_key, 'A.'))
                            )
                            
                            # Save answer
                            if selected != st.session_state.pm_answers.get(question_key):
                                st.session_state.pm_answers[question_key] = selected
                                save_session_state()
                            
                            # Show explanation button
                            if st.button(f"Show Explanation", key=f"pm_exp_{item_idx}_{q_idx}"):
                                correct = question.get('correct', 'A')
                                explanation = question.get('explanation', 'No explanation')
                                if selected.startswith(correct):
                                    st.success(f"✅ Correct! {explanation}")
                                else:
                                    st.error(f"❌ Incorrect. Correct answer: {correct}. {explanation}")
                        
                        st.divider()
            
            with tab3:
                st.subheader("📊 Exam Results & Performance")
                
                if st.session_state.get('am_questions') or st.session_state.get('pm_questions'):
                    
                    # Calculate scores
                    am_total_score = 0
                    am_max_score = 0
                    pm_correct = 0
                    pm_total = 0
                    
                    # AM scores
                    for i, question in enumerate(st.session_state.get('am_questions', [])):
                        am_max_score += question.get('points', 15)
                        if f"am_grade_{i}" in st.session_state:
                            am_total_score += st.session_state[f"am_grade_{i}"].get('score', 0)
                    
                    # PM scores
                    for item_idx, item_set in enumerate(st.session_state.get('pm_questions', [])):
                        for q_idx, question in enumerate(item_set.get('questions', [])):
                            pm_total += 1
                            question_key = f"pm_{item_idx}_{q_idx}"
                            selected = st.session_state.get('pm_answers', {}).get(question_key, '')
                            correct = question.get('correct', 'A')
                            if selected.startswith(correct):
                                pm_correct += 1
                    
                    # Display results
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("AM Score", f"{am_total_score}/{am_max_score}", 
                                f"{(am_total_score/am_max_score*100):.1f}%" if am_max_score > 0 else "0%")
                    
                    with col2:
                        st.metric("PM Score", f"{pm_correct}/{pm_total}",
                                f"{(pm_correct/pm_total*100):.1f}%" if pm_total > 0 else "0%")
                    
                    # Overall performance
                    if am_max_score > 0 and pm_total > 0:
                        overall_score = (am_total_score/am_max_score + pm_correct/pm_total) / 2
                        if overall_score >= 0.7:
                            st.success(f"🎉 Excellent Performance: {overall_score*100:.1f}%")
                        elif overall_score >= 0.5:
                            st.warning(f"⚠️ Good Effort: {overall_score*100:.1f}%")
                        else:
                            st.error(f"📚 Keep Studying: {overall_score*100:.1f}%")
                
                else:
                    st.info("Generate questions first to see results here.")
        
        else:
            st.error("❌ Failed to load CFA content")
            st.info("💡 Make sure the text files are in data/cfa_text_content/")
    
    else:
        st.error("❌ Text loader not available")

if __name__ == "__main__":
    main()
