import streamlit as st
import json
import os
import pickle
from datetime import datetime, timedelta
import random
from pathlib import Path

# Import our PDF processor and content loader
try:
    import sys
    sys.path.append('.')
    from src.pdf_processor import CFAPDFProcessor
    from src.content_loader import load_preprocessed_content, ensure_chunks_by_topic, get_content_summary
    PDF_PROCESSOR_AVAILABLE = True
    CONTENT_LOADER_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    PDF_PROCESSOR_AVAILABLE = False
    CONTENT_LOADER_AVAILABLE = False

st.set_page_config(
    page_title="CFA Level III Mock Exam Generator",
    page_icon="📊",
    layout="wide"
)

# Directories
FINANCIAL_BOOKS_DIR = "financial books"
STORAGE_DIR = "data/exam_sessions"
PROCESSED_DIR = "data/processed"

# Ensure directories exist
os.makedirs(STORAGE_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

def get_session_id():
    """Get or create a unique session ID"""
    if 'session_id' not in st.session_state:
        st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
    return st.session_state.session_id

def save_session_data():
    """Save current session data to file for persistence"""
    session_id = get_session_id()
    session_file = f"{STORAGE_DIR}/{session_id}.json"
    
    session_data = {
        'session_id': session_id,
        'processed_content': st.session_state.get('processed_content'),
        'current_exam': st.session_state.get('current_exam'),
        'exam_started': st.session_state.get('exam_started', False),
        'start_time': st.session_state.get('start_time').isoformat() if st.session_state.get('start_time') else None,
        'user_answers': st.session_state.get('user_answers', {}),
        'exam_submitted': st.session_state.get('exam_submitted', False),
        'grading_results': st.session_state.get('grading_results'),
        'last_saved': datetime.now().isoformat()
    }
    
    try:
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        return True
    except Exception as e:
        st.error(f"Error saving session: {str(e)}")
        return False

def load_session_data():
    """Load session data from file"""
    session_id = get_session_id()
    session_file = f"{STORAGE_DIR}/{session_id}.json"
    
    if os.path.exists(session_file):
        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)
            
            # Restore session state
            for key, value in session_data.items():
                if key == 'start_time' and value:
                    st.session_state[key] = datetime.fromisoformat(value)
                elif key != 'last_saved' and value is not None:
                    st.session_state[key] = value
            
            return True
        except Exception as e:
            st.error(f"Error loading session: {str(e)}")
            return False
    return False

def initialize_session_state():
    """Initialize session state with persistence"""
    # Try to load existing session first
    if not load_session_data():
        # Initialize new session
        defaults = {
            'processed_content': None,
            'current_exam': None,
            'exam_started': False,
            'start_time': None,
            'user_answers': {},
            'exam_submitted': False,
            'grading_results': None
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

def get_pdf_files():
    """Get list of PDF files in financial books directory"""
    pdf_files = []
    if os.path.exists(FINANCIAL_BOOKS_DIR):
        for file in os.listdir(FINANCIAL_BOOKS_DIR):
            if file.lower().endswith('.pdf'):
                pdf_files.append(os.path.join(FINANCIAL_BOOKS_DIR, file))
    return pdf_files

def process_financial_books():
    """Process PDFs from financial books folder or load pre-processed content"""
    
    # Debug info for troubleshooting
    st.info(f"🔧 Debug: CONTENT_LOADER_AVAILABLE = {CONTENT_LOADER_AVAILABLE}")
    
    # First, try to load pre-processed compressed content (for cloud deployment)
    if CONTENT_LOADER_AVAILABLE:
        st.info("🔍 Checking for pre-processed CFA content...")
        
        # Check if compressed file exists
        import os
        compressed_file = "data/processed/financial_books_content.json.gz"
        file_exists = os.path.exists(compressed_file)
        st.info(f"📁 Compressed file exists: {file_exists} ({compressed_file})")
        
        if file_exists:
            try:
                preprocessed_content = load_preprocessed_content()
                
                if preprocessed_content:
                    st.success("📦 Found pre-processed CFA content from your books!")
                    
                    # Ensure proper format for question generation
                    preprocessed_content = ensure_chunks_by_topic(preprocessed_content)
                    
                    # Show content summary
                    summary = get_content_summary(preprocessed_content)
                    st.success(f"📚 Loaded {summary.get('total_files', 0)} books with {summary.get('total_chunks', 0)} chunks")
                    st.success(f"📊 Found {summary.get('topics', 0)} CFA topics with content")
                    
                    return preprocessed_content
                else:
                    st.warning("⚠️ Pre-processed content file found but failed to load")
            except Exception as e:
                st.error(f"❌ Error loading pre-processed content: {str(e)}")
        else:
            st.warning("⚠️ Compressed content file not found in cloud deployment")
    
    # If no pre-processed content, try local PDF processing
    pdf_files = get_pdf_files()
    
    if not pdf_files:
        st.error(f"❌ No PDF files found in '{FINANCIAL_BOOKS_DIR}' folder!")
        st.info("💡 For cloud deployment, your CFA books should be pre-processed and included in the repository.")
        return None
    
    # Check if already processed locally
    processed_file = f"{PROCESSED_DIR}/financial_books_content.json"
    if os.path.exists(processed_file):
        try:
            with open(processed_file, 'r') as f:
                existing_content = json.load(f)
            
            # Check if all current PDFs are included
            existing_files = set(existing_content.get('processed_files', []))
            current_files = set([os.path.basename(f) for f in pdf_files])
            
            if current_files.issubset(existing_files):
                st.info("📚 Using previously processed content from your financial books")
                return ensure_chunks_by_topic(existing_content)
        except:
            pass
    
    # Process PDFs locally
    st.info(f"📖 Processing {len(pdf_files)} CFA books from your financial books folder...")
    
    if PDF_PROCESSOR_AVAILABLE:
        try:
            from src.pdf_processor import ingest_pdfs
            with st.spinner("Processing your CFA books... This may take several minutes."):
                # Use ingest_pdfs to get proper chunks_by_topic format
                results = ingest_pdfs(pdf_files, output_format="chunked_text_by_topic")
            
            # Save processed content
            with open(processed_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            st.success(f"✅ Successfully processed {len(results['processed_files'])} books!")
            st.success(f"📊 Found {len(results.get('chunks_by_topic', {}))} topics with content")
            return results
            
        except Exception as e:
            st.error(f"Error processing PDFs: {str(e)}")
            return None
    else:
        st.error("PDF processor not available. Please install required dependencies.")
        return None

def display_content_status():
    """Display content source and processing status"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("📚 Content Source")
    
    pdf_files = get_pdf_files()
    st.sidebar.write(f"**Financial Books Folder:** {len(pdf_files)} PDFs found")
    
    if pdf_files:
        with st.sidebar.expander("📖 Your CFA Books"):
            for pdf_file in pdf_files:
                filename = os.path.basename(pdf_file)
                file_size = os.path.getsize(pdf_file) / (1024 * 1024)  # MB
                st.write(f"• {filename} ({file_size:.1f} MB)")
    
    if st.session_state.processed_content:
        st.sidebar.success("✅ Content Processed")
        content = st.session_state.processed_content
        st.sidebar.write(f"Total chunks: {len(content.get('all_chunks', []))}")
        st.sidebar.write(f"Topics: {len(content.get('topic_distribution', {}))}")
    else:
        st.sidebar.info("📤 Ready to process")

def display_session_status():
    """Display session and persistence status"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 Session Status")
    
    session_id = get_session_id()
    st.sidebar.success(f"Session: {session_id[-8:]}")
    
    # Show persistence status
    if st.session_state.exam_started and not st.session_state.exam_submitted:
        st.sidebar.info("🔄 Exam in progress")
        st.sidebar.write("✅ Auto-saving answers")
        st.sidebar.write("✅ Timer persistent")
        st.sidebar.write("🔄 Safe to refresh!")
    else:
        st.sidebar.write("💾 Progress auto-saved")

def display_exam_interface():
    """Display exam interface with live timer and answers"""
    exam = st.session_state.current_exam
    session = exam["session"]
    
    # Live timer implementation
    if st.session_state.start_time:
        elapsed = datetime.now() - st.session_state.start_time
        remaining = timedelta(minutes=exam["total_time_minutes"]) - elapsed
        
        if remaining.total_seconds() <= 0:
            st.error("⏰ Time's up! Exam automatically submitted.")
            st.session_state.exam_submitted = True
            save_session_data()
            st.rerun()
        
        # Calculate time components
        total_seconds = int(remaining.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        # JavaScript-based live timer
        start_time_js = int(st.session_state.start_time.timestamp() * 1000)
        total_time_ms = exam["total_time_minutes"] * 60 * 1000
        
        timer_html = f"""
        <div style="text-align: center; padding: 20px; background: #f0f2f6; border-radius: 10px; margin: 20px 0;">
            <h2 id="timer-display" style="font-size: 2.5em; margin: 0; font-family: monospace;">⏰ Loading...</h2>
            <div id="progress-container" style="width: 100%; background: #ddd; border-radius: 10px; margin-top: 15px;">
                <div id="progress-bar" style="height: 20px; background: linear-gradient(90deg, #4CAF50, #FFC107, #FF5722); border-radius: 10px; width: 0%; transition: width 1s;"></div>
            </div>
            <p style="margin: 10px 0 0 0; color: #666;">💾 Your answers are being saved automatically - safe to refresh!</p>
        </div>
        
        <script>
        function updateTimer() {{
            const startTime = {start_time_js};
            const totalTime = {total_time_ms};
            const now = Date.now();
            const elapsed = now - startTime;
            const remaining = Math.max(0, totalTime - elapsed);
            
            if (remaining <= 0) {{
                document.getElementById('timer-display').innerHTML = '🔴 TIME UP!';
                document.getElementById('progress-bar').style.width = '100%';
                return;
            }}
            
            const totalSeconds = Math.floor(remaining / 1000);
            const hours = Math.floor(totalSeconds / 3600);
            const minutes = Math.floor((totalSeconds % 3600) / 60);
            const seconds = totalSeconds % 60;
            
            let timeStr;
            let icon;
            if (hours > 0) {{
                timeStr = String(hours).padStart(2, '0') + ':' + 
                         String(minutes).padStart(2, '0') + ':' + 
                         String(seconds).padStart(2, '0');
            }} else {{
                timeStr = String(minutes).padStart(2, '0') + ':' + 
                         String(seconds).padStart(2, '0');
            }}
            
            if (totalSeconds < 300) {{
                icon = '🔴';
            }} else if (totalSeconds < 900) {{
                icon = '🟡';
            }} else {{
                icon = '⏰';
            }}
            
            document.getElementById('timer-display').innerHTML = icon + ' Time Remaining: ' + timeStr;
            
            const progress = (elapsed / totalTime) * 100;
            document.getElementById('progress-bar').style.width = Math.min(progress, 100) + '%';
        }}
        
        // Update immediately and then every second
        updateTimer();
        setInterval(updateTimer, 1000);
        </script>
        """
        
        st.components.v1.html(timer_html, height=150)
    
    st.markdown("---")
    
    if session == "AM":
        display_am_exam()
    else:
        display_pm_exam()
    
    # Submit button
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("📤 Submit Exam", type="primary"):
            st.session_state.exam_submitted = True
            save_session_data()
            st.success("✅ Exam submitted!")
            st.balloons()
            st.rerun()

def display_am_exam():
    """Display AM questions with persistent answers"""
    exam = st.session_state.current_exam
    
    for question in exam["questions"]:
        st.subheader(f"Question {question['question_number']} - {question['topic']} ({question['total_points']} points)")
        
        # Scenario
        st.markdown("**Scenario:**")
        st.write(question["scenario"])
        st.markdown("---")
        
        # Sub-questions with persistent answers
        for sub_q in question["sub_questions"]:
            st.markdown(f"**{sub_q['part']}.** {sub_q['question']} *({sub_q['points']} points)*")
            
            answer_key = f"q{question['question_number']}_{sub_q['part']}"
            current_answer = st.session_state.user_answers.get(answer_key, "")
            
            # Text area with persistent value and auto-save
            answer = st.text_area(
                f"Your answer for {sub_q['part']}:",
                value=current_answer,
                key=f"input_{answer_key}",
                height=150,
                placeholder="Provide your detailed answer here..."
            )
            
            # Save answer and auto-save session
            if answer != current_answer:
                st.session_state.user_answers[answer_key] = answer
                save_session_data()
            
            st.markdown("---")

def display_pm_exam():
    """Display PM questions with persistent answers"""
    exam = st.session_state.current_exam
    
    for item_set in exam["questions"]:
        st.subheader(f"Item Set {item_set['set_number']} - {item_set['topic']}")
        
        # Vignette
        st.markdown("**Case Study:**")
        st.write(item_set["vignette"])
        st.markdown("---")
        
        # Questions with persistent selection
        for mcq in item_set["questions"]:
            st.markdown(f"**{mcq['question_number']}.** {mcq['question_text']}")
            
            answer_key = f"mcq_{mcq['question_number']}"
            current_answer = st.session_state.user_answers.get(answer_key)
            
            options = list(mcq['options'].keys())
            default_index = 0
            if current_answer in options:
                default_index = options.index(current_answer)
            
            # Radio button with persistent selection
            selected = st.radio(
                f"Select answer for question {mcq['question_number']}:",
                options=options,
                index=default_index,
                key=f"radio_{answer_key}",
                format_func=lambda x: f"{x}. {mcq['options'][x]}"
            )
            
            # Save answer and auto-save session
            if selected != current_answer:
                st.session_state.user_answers[answer_key] = selected
                save_session_data()
            
        st.markdown("---")

# Real AI-powered question generation using OpenAI
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

def generate_questions_from_content(session_type, content):
    """Generate real CFA questions using OpenAI from processed content"""
    if not content or 'chunks_by_topic' not in content:
        st.error("No processed content available for question generation!")
        return []
    
    chunks_by_topic = content['chunks_by_topic']
    if not chunks_by_topic:
        st.error("No topic-classified content found!")
        return []
    
    questions = []
    
    try:
        if session_type == "AM":
            # Generate 4 AM constructed response questions
            available_topics = list(chunks_by_topic.keys())
            selected_topics = random.sample(available_topics, min(4, len(available_topics)))
            
            for i, topic in enumerate(selected_topics, 1):
                chunks = chunks_by_topic[topic]
                if not chunks:
                    continue
                    
                # Select relevant content chunks for this topic
                selected_chunks = random.sample(chunks, min(3, len(chunks)))
                content_text = "\n\n".join([chunk['content'] for chunk in selected_chunks])
                
                # Generate AM question using OpenAI
                prompt = f"""
You are creating a CFA Level III Morning Session constructed response question.

Topic: {topic}
Content from CFA books:
{content_text[:2000]}

Create a realistic CFA Level III AM question with:
1. A detailed scenario (200-300 words)
2. Two sub-questions (A and B) worth 10 points each
3. Professional, exam-level difficulty
4. Based on the provided content

Return ONLY a JSON object with this structure:
{{
    "scenario": "detailed scenario text",
    "sub_questions": [
        {{"part": "A", "question": "question text", "points": 10}},
        {{"part": "B", "question": "question text", "points": 10}}
    ]
}}"""
                
                response = openai.chat.completions.create(
                    model=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1000
                )
                
                try:
                    import json
                    # Clean the response - remove markdown code blocks if present
                    raw_response = response.choices[0].message.content.strip()
                    if raw_response.startswith('```json'):
                        raw_response = raw_response[7:]  # Remove ```json
                    if raw_response.endswith('```'):
                        raw_response = raw_response[:-3]  # Remove ```
                    raw_response = raw_response.strip()
                    
                    question_data = json.loads(raw_response)
                    
                    question = {
                        "question_id": f"AM_Q{i}_{topic.replace(' ', '_')}",
                        "question_number": i,
                        "topic": topic,
                        "scenario": question_data["scenario"],
                        "sub_questions": question_data["sub_questions"],
                        "total_points": 20,
                        "estimated_time_minutes": 45
                    }
                    questions.append(question)
                    
                except (json.JSONDecodeError, KeyError) as e:
                    st.warning(f"Error parsing question {i} for {topic}: {e}")
                    continue
        
        else:  # PM Session
            # Generate 5 PM item sets
            available_topics = list(chunks_by_topic.keys())
            selected_topics = random.sample(available_topics, min(5, len(available_topics)))
            
            for i, topic in enumerate(selected_topics, 1):
                chunks = chunks_by_topic[topic]
                if not chunks:
                    continue
                    
                # Select relevant content chunks for this topic
                selected_chunks = random.sample(chunks, min(3, len(chunks)))
                content_text = "\n\n".join([chunk['content'] for chunk in selected_chunks])
                
                # Generate PM item set using OpenAI
                prompt = f"""
You are creating a CFA Level III Afternoon Session item set.

Topic: {topic}
Content from CFA books:
{content_text[:2000]}

Create a realistic CFA Level III PM item set with:
1. A case study vignette (150-200 words)
2. Three multiple choice questions (A, B, C, D options)
3. Professional, exam-level difficulty
4. Based on the provided content

Return ONLY a JSON object with this structure:
{{
    "vignette": "case study text",
    "questions": [
        {{
            "question_text": "question 1 text",
            "options": {{"A": "option A", "B": "option B", "C": "option C", "D": "option D"}},
            "correct_answer": "A",
            "explanation": "why this answer is correct"
        }},
        {{
            "question_text": "question 2 text",
            "options": {{"A": "option A", "B": "option B", "C": "option C", "D": "option D"}},
            "correct_answer": "B",
            "explanation": "why this answer is correct"
        }},
        {{
            "question_text": "question 3 text",
            "options": {{"A": "option A", "B": "option B", "C": "option C", "D": "option D"}},
            "correct_answer": "C",
            "explanation": "why this answer is correct"
        }}
    ]
}}"""
                
                response = openai.chat.completions.create(
                    model=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=1500
                )
                
                try:
                    import json
                    # Clean the response - remove markdown code blocks if present
                    raw_response = response.choices[0].message.content.strip()
                    if raw_response.startswith('```json'):
                        raw_response = raw_response[7:]  # Remove ```json
                    if raw_response.endswith('```'):
                        raw_response = raw_response[:-3]  # Remove ```
                    raw_response = raw_response.strip()
                    
                    item_data = json.loads(raw_response)
                    
                    # Add question numbers
                    for j, q in enumerate(item_data["questions"]):
                        q["question_number"] = (i-1) * 3 + j + 1
                        q["points"] = 6
                    
                    item_set = {
                        "item_set_id": f"PM_Set{i}_{topic.replace(' ', '_')}",
                        "set_number": i,
                        "topic": topic,
                        "vignette": item_data["vignette"],
                        "questions": item_data["questions"],
                        "total_points": 18,
                        "estimated_time_minutes": 36
                    }
                    questions.append(item_set)
                    
                except (json.JSONDecodeError, KeyError) as e:
                    st.warning(f"Error parsing item set {i} for {topic}: {e}")
                    continue
        
        return questions
        
    except Exception as e:
        st.error(f"Error generating questions: {str(e)}")
        return []

def build_exam_from_books(session_type):
    """Build exam from processed financial books"""
    if not st.session_state.processed_content:
        st.error("No processed content available!")
        return None
    
    with st.spinner(f"Building {session_type} exam from your CFA books..."):
        questions = generate_questions_from_content(session_type, st.session_state.processed_content)
        
        exam = {
            "exam_id": f"CFA_L3_{session_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "session": session_type,
            "created_at": datetime.now().isoformat(),
            "total_questions": len(questions),
            "total_time_minutes": 180,
            "total_points": sum([q.get('total_points', 18) for q in questions]),
            "questions": questions,
            "instructions": [
                f"CFA Level III {session_type} Session",
                "Based on content from your financial books",
                "Time: 180 minutes (3 hours)",
                "Read all instructions carefully",
                "Your progress is automatically saved"
            ]
        }
        
        st.session_state.current_exam = exam
        save_session_data()
        return exam

def grade_exam():
    """Grade the exam (simplified for demo)"""
    exam = st.session_state.current_exam
    session = exam["session"]
    
    if session == "PM":
        # Count answered questions
        total_questions = sum([len(item_set["questions"]) for item_set in exam["questions"]])
        answered = len([k for k, v in st.session_state.user_answers.items() if k.startswith("mcq_") and v])
        
        # Simple scoring
        percentage = (answered / total_questions * 100) if total_questions > 0 else 0
        
        return {
            "session": "PM",
            "total_questions": total_questions,
            "answered_questions": answered,
            "percentage": percentage,
            "passing": percentage >= 70
        }
    else:
        # AM session - count answered parts
        total_parts = sum([len(q["sub_questions"]) for q in exam["questions"]])
        answered = len([k for k, v in st.session_state.user_answers.items() if k.startswith("q") and v.strip()])
        
        percentage = (answered / total_parts * 100) if total_parts > 0 else 0
        
        return {
            "session": "AM",
            "total_parts": total_parts,
            "answered_parts": answered,
            "percentage": percentage,
            "passing": percentage >= 70
        }

def main():
    initialize_session_state()
    
    st.title("🎓 CFA Level III Mock Exam Generator")
    st.markdown("**Robust System** - Based on YOUR CFA books with persistent sessions!")
    
    # Display status sidebars
    display_content_status()
    display_session_status()
    
    # Main workflow
    if not st.session_state.processed_content:
        st.subheader("📚 Step 1: Process Your CFA Books")
        st.info("The system will automatically process PDFs from your 'financial books' folder")
        
        pdf_files = get_pdf_files()
        if pdf_files:
            st.success(f"✅ Found {len(pdf_files)} CFA books in your folder")
            
            if st.button("🔄 Process My CFA Books", type="primary"):
                content = process_financial_books()
                if content:
                    st.session_state.processed_content = content
                    save_session_data()
                    st.success("✅ Your books have been processed!")
                    st.rerun()
        else:
            st.error(f"❌ No PDF files found in '{FINANCIAL_BOOKS_DIR}' folder")
            st.info("Please add your CFA Level III books to the financial books folder")
    
    elif not st.session_state.current_exam:
        st.subheader("📝 Step 2: Build Exam from Your Books")
        
        # Show content summary
        content = st.session_state.processed_content
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Books Processed", len(content.get('processed_files', [])))
        with col2:
            st.metric("Content Chunks", len(content.get('all_chunks', [])))
        with col3:
            st.metric("Topics Covered", len(content.get('topic_distribution', {})))
        
        session_type = st.selectbox("Select session:", ["AM", "PM"])
        
        if st.button(f"Build {session_type} Exam from My Books", type="primary"):
            exam = build_exam_from_books(session_type)
            if exam:
                st.success(f"✅ {session_type} exam built from your CFA books!")
                st.rerun()
    
    elif not st.session_state.exam_started:
        st.subheader("🎯 Step 3: Take Your Personalized Exam")
        exam = st.session_state.current_exam
        
        st.info("📖 This exam is based on content from YOUR CFA books!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Questions", exam["total_questions"])
        with col2:
            st.metric("Time", f"{exam['total_time_minutes']} min")
        with col3:
            st.metric("Points", exam["total_points"])
        
        if st.button("🚀 Start My Personalized Exam", type="primary"):
            st.session_state.exam_started = True
            st.session_state.start_time = datetime.now()
            save_session_data()
            st.rerun()
    
    elif not st.session_state.exam_submitted:
        st.subheader(f"📝 {st.session_state.current_exam['session']} Session - In Progress")
        display_exam_interface()
    
    elif not st.session_state.grading_results:
        with st.spinner("Grading your exam..."):
            st.session_state.grading_results = grade_exam()
            save_session_data()
        st.rerun()
    
    else:
        # Display results
        results = st.session_state.grading_results
        st.header(f"📊 {results['session']} Session Results")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if results['session'] == 'PM':
                st.metric("Answered", f"{results['answered_questions']}/{results['total_questions']}")
            else:
                st.metric("Answered", f"{results['answered_parts']}/{results['total_parts']}")
        with col2:
            st.metric("Completion", f"{results['percentage']:.1f}%")
        with col3:
            result_color = "green" if results['passing'] else "red"
            st.markdown(f"**Result:** :{result_color}[{'PASS' if results['passing'] else 'FAIL'}]")
        
        st.success("🎉 Exam completed! This was based on YOUR CFA books.")
        
        # Reset for new exam
        if st.button("🔄 Take Another Exam"):
            # Keep processed content, reset exam state
            st.session_state.current_exam = None
            st.session_state.exam_started = False
            st.session_state.start_time = None
            st.session_state.user_answers = {}
            st.session_state.exam_submitted = False
            st.session_state.grading_results = None
            save_session_data()
            st.rerun()

if __name__ == "__main__":
    main()
