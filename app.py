"""
CFA Level III Mock Exam Generator - Main Streamlit Application
"""
import streamlit as st
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Import our custom modules
from src.pdf_processor import CFAPDFProcessor, ingest_pdfs
from src.question_generator import CFAQuestionGenerator
from src.exam_builder import CFAExamBuilder
from src.grading_engine import CFAGradingEngine
from src.export_utils import CFAExportUtils, export_exam
from config.topics import TOPIC_WEIGHTS, QUESTION_TYPES

# Page configuration
st.set_page_config(
    page_title="CFA Level III Mock Exam Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    if 'processed_pdfs' not in st.session_state:
        st.session_state.processed_pdfs = None
    if 'current_exam' not in st.session_state:
        st.session_state.current_exam = None
    if 'exam_start_time' not in st.session_state:
        st.session_state.exam_start_time = None
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'exam_submitted' not in st.session_state:
        st.session_state.exam_submitted = False
    if 'grading_results' not in st.session_state:
        st.session_state.grading_results = None

def main():
    initialize_session_state()
    
    st.title("🎓 CFA Level III Mock Exam Generator")
    st.markdown("Generate high-quality CFA Level III mock exams based on your PDF content")
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "📚 PDF Upload & Processing",
        "🔧 Question Generation", 
        "📝 Exam Builder",
        "⏱️ Take Exam",
        "📊 Results & Analysis",
        "📄 Export Options"
    ])
    
    # API Key setup
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔑 API Configuration")
    
    if not os.path.exists('.env'):
        api_key = st.sidebar.text_input("OpenAI API Key", type="password")
        if api_key:
            with open('.env', 'w') as f:
                f.write(f"OPENAI_API_KEY={api_key}\n")
                f.write("OPENAI_MODEL=gpt-4-turbo-preview\n")
            st.sidebar.success("API key saved!")
            st.rerun()
    else:
        st.sidebar.success("✅ API key configured")
    
    # Route to pages
    if page == "📚 PDF Upload & Processing":
        pdf_upload_page()
    elif page == "🔧 Question Generation":
        question_generation_page()
    elif page == "📝 Exam Builder":
        exam_builder_page()
    elif page == "⏱️ Take Exam":
        take_exam_page()
    elif page == "📊 Results & Analysis":
        results_analysis_page()
    elif page == "📄 Export Options":
        export_options_page()

def pdf_upload_page():
    st.header("📚 PDF Upload & Processing")
    
    uploaded_files = st.file_uploader(
        "Upload CFA PDF Books", 
        type=['pdf'], 
        accept_multiple_files=True
    )
    
    if uploaded_files:
        pdf_paths = []
        os.makedirs("data/uploaded_pdfs", exist_ok=True)
        
        for uploaded_file in uploaded_files:
            file_path = f"data/uploaded_pdfs/{uploaded_file.name}"
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            pdf_paths.append(file_path)
        
        if st.button("🔄 Process PDFs", type="primary"):
            with st.spinner("Processing PDFs..."):
                processor = CFAPDFProcessor()
                results = processor.process_multiple_pdfs(pdf_paths)
                
                os.makedirs("data/processed", exist_ok=True)
                with open("data/processed/pdf_content.json", 'w') as f:
                    json.dump(results, f, indent=2)
                
                st.session_state.processed_pdfs = results
                st.success("✅ PDFs processed successfully!")

def question_generation_page():
    st.header("🔧 Question Generation")
    
    if not st.session_state.processed_pdfs:
        st.warning("⚠️ Please process PDFs first.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        am_count = st.number_input("AM questions", min_value=1, max_value=10, value=5)
        if st.button("Generate AM Questions"):
            generate_questions("AM", am_count)
    
    with col2:
        pm_count = st.number_input("PM item sets", min_value=1, max_value=10, value=6)
        if st.button("Generate PM Questions"):
            generate_questions("PM", pm_count)

def generate_questions(session: str, count: int):
    with st.spinner(f"Generating {session} questions..."):
        generator = CFAQuestionGenerator()
        processed_data = st.session_state.processed_pdfs
        
        chunks_by_topic = {}
        for chunk in processed_data['all_chunks']:
            topic = chunk['topic']
            if topic not in chunks_by_topic:
                chunks_by_topic[topic] = []
            chunks_by_topic[topic].append(chunk)
        
        all_questions = []
        questions_per_topic = max(1, count // len(chunks_by_topic))
        
        for topic, chunks in chunks_by_topic.items():
            if chunks:
                topic_questions = generator.generate_questions_for_topic(
                    chunks, 
                    "constructed" if session == "AM" else "item_set",
                    min(questions_per_topic, len(chunks))
                )
                all_questions.extend(topic_questions)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{session}_questions_{timestamp}.json"
        generator.save_questions_to_json(all_questions, filename)
        
        st.success(f"✅ Generated {len(all_questions)} {session} questions!")

def exam_builder_page():
    st.header("📝 Exam Builder")
    
    exam_mode = st.selectbox("Select exam session", ["AM", "PM", "Both"])
    
    if st.button("🏗️ Build Exam", type="primary"):
        builder = CFAExamBuilder()
        builder.load_questions_pool()
        
        if exam_mode == "Both":
            am_exam = builder.build_exam(mode="AM")
            pm_exam = builder.build_exam(mode="PM")
            st.session_state.current_exam = {"AM": am_exam, "PM": pm_exam}
        else:
            exam = builder.build_exam(mode=exam_mode)
            st.session_state.current_exam = {exam_mode: exam}
        
        st.success(f"✅ Built {exam_mode} exam!")

def take_exam_page():
    st.header("⏱️ Take Exam")
    
    if not st.session_state.current_exam:
        st.warning("⚠️ Please build an exam first.")
        return
    
    sessions = list(st.session_state.current_exam.keys())
    selected_session = st.selectbox("Select session", sessions) if len(sessions) > 1 else sessions[0]
    exam_data = st.session_state.current_exam[selected_session]
    
    if not st.session_state.exam_start_time:
        st.subheader(f"Ready to start {selected_session} session")
        if st.button("🚀 Start Exam"):
            st.session_state.exam_start_time = datetime.now()
            st.rerun()
    else:
        # Display exam questions and timer
        elapsed = datetime.now() - st.session_state.exam_start_time
        remaining = timedelta(minutes=exam_data['total_time_minutes']) - elapsed
        
        if remaining.total_seconds() > 0:
            st.markdown(f"### ⏰ Time Remaining: {str(remaining).split('.')[0]}")
            st.write("Exam interface would be displayed here...")
            
            if st.button("📤 Submit Exam"):
                st.session_state.exam_submitted = True
                st.success("Exam submitted!")
        else:
            st.error("Time's up!")

def results_analysis_page():
    st.header("📊 Results & Analysis")
    
    if not st.session_state.exam_submitted:
        st.warning("⚠️ Please take an exam first.")
        return
    
    st.success("Results would be displayed here after grading implementation.")

def export_options_page():
    st.header("📄 Export Options")
    
    if not st.session_state.current_exam:
        st.warning("⚠️ Please build an exam first.")
        return
    
    if st.button("📄 Export as PDF"):
        st.success("PDF export functionality ready!")
    
    if st.button("💾 Export as JSON"):
        st.success("JSON export functionality ready!")

if __name__ == "__main__":
    main()
