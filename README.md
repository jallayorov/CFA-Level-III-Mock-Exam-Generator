# CFA Level III Mock Exam Generator

An AI-assisted application that generates CFA Level III mock exams (AM/PM format) based on PDF content from CFA books.

## Features

- **PDF Ingestion**: Process 7 CFA books with topic classification and chunking
- **Question Generation**: Create CFA-style questions using GPT-4
  - AM Session: Constructed response questions (3-5 questions)
  - PM Session: Item sets with multiple choice questions (4-6 sets, 3 MCQs each)
- **Exam Builder**: Enforce topic weights and generate timed exams
- **Grading Engine**: Automatic grading for PM, rubric-based for AM
- **Export Options**: PDF and JSON formats

## Topic Weights (CFA Level III)

- Asset Allocation: 15–20%
- Portfolio Construction: 15–20%
- Performance Management: 5–10%
- Derivatives & Risk Management: 10–15%
- Ethics & Professional Standards: 10–15%
- Portfolio Management Pathway: 30–35%

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your OpenAI API key
   ```

3. Run the application:
   ```bash
   streamlit run app.py
   ```

## Project Structure

- `app.py` - Main Streamlit application
- `src/` - Core application modules
- `data/` - PDF storage and processed content
- `exams/` - Generated exams and solutions
- `config/` - Configuration files

## Usage

1. Upload your CFA PDF books
2. Select exam type (AM/PM or both)
3. Generate mock exam
4. Take the exam with timer
5. Review results and solutions
