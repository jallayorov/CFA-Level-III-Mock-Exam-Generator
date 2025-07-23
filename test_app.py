import streamlit as st
import os

st.set_page_config(
    page_title="CFA Level III Mock Exam Generator",
    page_icon="📊",
    layout="wide"
)

st.title("🎓 CFA Level III Mock Exam Generator")
st.markdown("Generate high-quality CFA Level III mock exams based on your PDF content")

# Check if .env file exists
if os.path.exists('.env'):
    st.success("✅ Environment configured")
else:
    st.warning("⚠️ Please configure your OpenAI API key")

st.markdown("## 📚 How It Works")

st.markdown("""
### **Phase 1: One-Time Content Processing**
1. **Upload Your CFA Books** - Upload your 7 CFA Level III PDF books
2. **Automatic Processing** - System extracts, cleans, and classifies content by topic
3. **Knowledge Base Creation** - Creates reusable chunks organized by CFA topics

### **Phase 2: Question Generation** 
1. **AI-Powered Questions** - Uses GPT-4 to create original CFA-style questions
2. **Two Session Types**:
   - **AM Session**: Constructed response (essay) questions
   - **PM Session**: Item sets with multiple choice questions
3. **Topic Weighting** - Follows official CFA Level III weights

### **Phase 3: Exam Taking & Grading**
1. **Timed Exams** - 3-hour sessions with countdown timer
2. **Automatic Grading** - PM sessions auto-graded, AM uses AI rubrics
3. **Performance Analysis** - Detailed breakdown by topic
""")

st.markdown("## 📊 CFA Level III Topic Weights")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    - **Asset Allocation**: 15–20%
    - **Portfolio Construction**: 15–20%  
    - **Performance Management**: 5–10%
    """)

with col2:
    st.markdown("""
    - **Derivatives & Risk Management**: 10–15%
    - **Ethics & Professional Standards**: 10–15%
    - **Portfolio Management Pathway**: 30–35%
    """)

st.markdown("---")

st.markdown("## 🚀 Getting Started")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🚀 Quick Start (Pre-loaded Content)")
    if st.button("⚡ Use Sample CFA Content", type="primary"):
        # Load pre-loaded content
        import json
        try:
            with open('data/sample_cfa_content.json', 'r') as f:
                sample_content = json.load(f)
            st.session_state['processed_content'] = sample_content
            st.success("✅ Loaded sample CFA Level III content!")
            st.json({
                "Total Chunks": len(sample_content['all_chunks']),
                "Topics Covered": list(sample_content['topic_distribution'].keys()),
                "Ready for": "Question Generation"
            })
        except FileNotFoundError:
            st.error("Sample content file not found")
    
    if st.button("🔧 Generate Sample Questions"):
        if 'processed_content' in st.session_state:
            st.success("🎯 Ready to generate questions from your content!")
            st.info("This would use OpenAI GPT-4 to create CFA-style questions from the loaded content.")
        else:
            st.warning("Please load sample content first")
    
    if st.button("📝 Build Mock Exam"):
        if 'processed_content' in st.session_state:
            st.success("📊 Ready to build a complete CFA Level III mock exam!")
            st.info("This would assemble an exam with proper topic weights and timing.")
        else:
            st.warning("Please load content and generate questions first")

with col2:
    st.subheader("📚 Custom Content (Upload Your Books)")
    if st.button("📁 Upload Your CFA Books"):
        st.info("📤 Upload functionality: Process your own 7 CFA books for personalized content.")
    
    st.markdown("**Benefits of Custom Upload:**")
    st.markdown("- Uses YOUR specific study materials")
    st.markdown("- Tailored to your curriculum version")
    st.markdown("- More comprehensive content coverage")
    st.markdown("- Takes 15-30 minutes initial processing")

st.markdown("---")
st.markdown("**Status**: Test interface loaded successfully! 🎉")
