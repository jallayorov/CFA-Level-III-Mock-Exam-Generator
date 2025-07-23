#!/bin/bash

# CFA Level III Mock Exam Generator - Startup Script

echo "🎓 Starting CFA Level III Mock Exam Generator..."

# Activate virtual environment
source venv/bin/activate

# Install dependencies if not already installed
if [ ! -f "venv/installed" ]; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    touch venv/installed
    echo "✅ Dependencies installed!"
fi

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚠️  Please create a .env file with your OpenAI API key"
    echo "   Copy .env.example to .env and add your API key"
fi

# Create necessary directories
mkdir -p data/uploaded_pdfs
mkdir -p data/processed
mkdir -p data/generated_questions
mkdir -p exams
mkdir -p exams/results
mkdir -p exams/submissions

echo "🚀 Starting Streamlit application..."
streamlit run app.py
