import streamlit as st
import json
import os
from datetime import datetime, timedelta
import random

st.set_page_config(
    page_title="CFA Level III Mock Exam Generator",
    page_icon="📊",
    layout="wide"
)

# CFA Level III Exam Standards
CFA_STANDARDS = {
    "AM": {
        "questions": {"min": 3, "max": 5, "standard": 4},
        "time_minutes": 180,
        "question_type": "constructed_response",
        "time_per_question": 45
    },
    "PM": {
        "item_sets": {"min": 4, "max": 6, "standard": 5},
        "questions_per_set": 3,
        "time_minutes": 180,
        "question_type": "multiple_choice",
        "time_per_set": 36
    }
}

def initialize_session_state():
    if 'processed_content' not in st.session_state:
        st.session_state.processed_content = None
    if 'current_exam' not in st.session_state:
        st.session_state.current_exam = None
    if 'exam_started' not in st.session_state:
        st.session_state.exam_started = False
    if 'start_time' not in st.session_state:
        st.session_state.start_time = None
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'exam_submitted' not in st.session_state:
        st.session_state.exam_submitted = False
    if 'grading_results' not in st.session_state:
        st.session_state.grading_results = None

def load_sample_content():
    """Load pre-loaded CFA content"""
    try:
        with open('data/sample_cfa_content.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def generate_standard_am_questions():
    """Generate standard 4 AM questions following CFA format"""
    if not st.session_state.processed_content:
        return []
    
    chunks_by_topic = st.session_state.processed_content['chunks_by_topic']
    questions = []
    
    # Select 4 different topics for variety
    available_topics = list(chunks_by_topic.keys())
    selected_topics = random.sample(available_topics, min(4, len(available_topics)))
    
    am_scenarios = {
        "Asset Allocation": {
            "scenario": "You are the chief investment officer for the ABC Pension Fund, which has $5 billion in assets under management. The fund's current strategic asset allocation is 60% equities, 30% fixed income, and 10% alternatives. The board is concerned about the fund's risk exposure and is considering a review of the asset allocation policy.",
            "sub_questions": [
                {"part": "A", "question": "Explain the key principles of strategic asset allocation and how they differ from tactical asset allocation approaches.", "points": 8},
                {"part": "B", "question": "Describe three methods for determining optimal asset allocation weights and discuss their relative advantages and limitations.", "points": 12},
                {"part": "C", "question": "Calculate the expected portfolio return and standard deviation given the following assumptions: Equities (E[R]=8%, σ=18%), Bonds (E[R]=4%, σ=6%), Alternatives (E[R]=10%, σ=22%), with correlations ρ(E,B)=0.2, ρ(E,A)=0.6, ρ(B,A)=0.1.", "points": 10}
            ]
        },
        "Portfolio Construction": {
            "scenario": "XYZ Asset Management is launching a new multi-factor equity strategy for institutional clients. The strategy will target exposure to value, momentum, quality, and low volatility factors across developed markets.",
            "sub_questions": [
                {"part": "A", "question": "Describe the theoretical foundation for each of the four factors and explain why they are expected to generate risk premiums.", "points": 12},
                {"part": "B", "question": "Discuss the implementation challenges in factor investing and propose solutions for factor timing and portfolio construction.", "points": 10},
                {"part": "C", "question": "Design a factor allocation framework that balances factor exposures while managing turnover and transaction costs.", "points": 8}
            ]
        },
        "Performance Management": {
            "scenario": "The DEF Endowment Fund has hired you to evaluate the performance of their equity portfolio over the past three years. The portfolio returned 12.5% annually while the benchmark returned 11.2%. The portfolio's tracking error was 4.2%.",
            "sub_questions": [
                {"part": "A", "question": "Calculate and interpret the information ratio, Sharpe ratio (assuming risk-free rate of 2%), and Treynor ratio (portfolio beta = 1.1) for the portfolio.", "points": 10},
                {"part": "B", "question": "Conduct a Brinson-Fachler performance attribution analysis to decompose returns into asset allocation, security selection, and interaction effects.", "points": 12},
                {"part": "C", "question": "Evaluate whether the portfolio's active risk budget is being used efficiently and recommend improvements.", "points": 8}
            ]
        },
        "Portfolio Management Pathway": {
            "scenario": "You are advising a high-net-worth family with $50 million in investable assets. The family consists of a 55-year-old entrepreneur, his 52-year-old spouse, and two children aged 16 and 18. They have significant tax considerations and estate planning needs.",
            "sub_questions": [
                {"part": "A", "question": "Identify and analyze the key constraints and objectives for this family's investment policy statement.", "points": 8},
                {"part": "B", "question": "Design an appropriate asset allocation strategy considering their tax situation, liquidity needs, and multi-generational wealth transfer goals.", "points": 12},
                {"part": "C", "question": "Recommend specific investment structures and vehicles to optimize after-tax returns and facilitate wealth transfer.", "points": 10}
            ]
        }
    }
    
    for i, topic in enumerate(selected_topics, 1):
        if topic in am_scenarios:
            scenario_data = am_scenarios[topic]
        else:
            # Default scenario for other topics
            chunk = random.choice(chunks_by_topic[topic])
            scenario_data = {
                "scenario": f"Consider the following scenario related to {topic}: {chunk['content'][:300]}...",
                "sub_questions": [
                    {"part": "A", "question": f"Analyze the key considerations for {topic.lower()} in this context.", "points": 10},
                    {"part": "B", "question": f"Recommend an appropriate strategy and justify your approach.", "points": 10}
                ]
            }
        
        question = {
            "question_id": f"AM_Q{i}_{topic.replace(' ', '_')}",
            "question_number": i,
            "topic": topic,
            "scenario": scenario_data["scenario"],
            "sub_questions": scenario_data["sub_questions"],
            "total_points": sum([sq["points"] for sq in scenario_data["sub_questions"]]),
            "estimated_time_minutes": 45,
            "answer_key": [
                {
                    "part": sq["part"],
                    "answer": f"[Model answer for part {sq['part']} would be provided here with detailed explanation and calculations]",
                    "rubric": f"Award {sq['points']} points for comprehensive answer addressing all key concepts with proper justification."
                } for sq in scenario_data["sub_questions"]
            ]
        }
        questions.append(question)
    
    return questions

def generate_standard_pm_questions():
    """Generate standard 5 item sets (15 MCQs) following CFA format"""
    if not st.session_state.processed_content:
        return []
    
    chunks_by_topic = st.session_state.processed_content['chunks_by_topic']
    item_sets = []
    
    # Select 5 different topics
    available_topics = list(chunks_by_topic.keys())
    selected_topics = random.sample(available_topics, min(5, len(available_topics)))
    
    pm_vignettes = {
        "Asset Allocation": {
            "vignette": "Global Pension Advisors (GPA) manages a $10 billion pension fund for a large corporation. The fund's current allocation is 55% equities, 35% bonds, and 10% alternatives. The fund has a 15-year investment horizon and moderate risk tolerance. GPA is considering implementing a liability-driven investment (LDI) approach.",
            "questions": [
                {
                    "question_text": "Which asset allocation approach would be most appropriate for implementing an LDI strategy?",
                    "options": {
                        "A": "Increase equity allocation to 70% for higher expected returns",
                        "B": "Match asset duration to liability duration and hedge interest rate risk",
                        "C": "Implement tactical asset allocation based on market timing",
                        "D": "Focus solely on maximizing absolute returns"
                    },
                    "correct_answer": "B",
                    "explanation": "LDI focuses on matching assets to liabilities, particularly duration matching and interest rate hedging."
                },
                {
                    "question_text": "The primary benefit of strategic asset allocation is:",
                    "options": {
                        "A": "Maximizing short-term returns",
                        "B": "Providing a long-term framework for achieving investment objectives",
                        "C": "Eliminating all portfolio risk",
                        "D": "Guaranteeing outperformance of benchmarks"
                    },
                    "correct_answer": "B",
                    "explanation": "Strategic asset allocation provides the long-term framework aligned with investment objectives and constraints."
                },
                {
                    "question_text": "When rebalancing a strategic asset allocation, the most important consideration is:",
                    "options": {
                        "A": "Market timing opportunities",
                        "B": "Transaction costs and tax implications",
                        "C": "Short-term performance relative to peers",
                        "D": "Manager selection decisions"
                    },
                    "correct_answer": "B",
                    "explanation": "Rebalancing decisions must consider transaction costs and tax implications to ensure net benefits."
                }
            ]
        },
        "Portfolio Construction": {
            "vignette": "Systematic Investment Management (SIM) is developing a multi-factor equity strategy targeting value, momentum, and quality factors. The strategy will use a quantitative approach to construct portfolios with controlled risk exposures.",
            "questions": [
                {
                    "question_text": "The value factor is most likely to outperform when:",
                    "options": {
                        "A": "Interest rates are declining rapidly",
                        "B": "Economic growth is accelerating from recession",
                        "C": "Market volatility is at historic lows",
                        "D": "Technology stocks are leading market gains"
                    },
                    "correct_answer": "B",
                    "explanation": "Value stocks typically outperform during economic recoveries when their fundamentals improve."
                },
                {
                    "question_text": "A key challenge in factor investing is:",
                    "options": {
                        "A": "Factors always provide positive returns",
                        "B": "Factor premiums can experience long periods of underperformance",
                        "C": "Factors are perfectly correlated with each other",
                        "D": "Factor strategies have no implementation costs"
                    },
                    "correct_answer": "B",
                    "explanation": "Factor premiums can underperform for extended periods, testing investor patience."
                },
                {
                    "question_text": "When constructing a multi-factor portfolio, the most important consideration is:",
                    "options": {
                        "A": "Maximizing exposure to the highest returning factor",
                        "B": "Balancing factor exposures while managing correlations",
                        "C": "Minimizing the number of holdings",
                        "D": "Focusing only on momentum factors"
                    },
                    "correct_answer": "B",
                    "explanation": "Multi-factor portfolios require balancing exposures and managing correlations between factors."
                }
            ]
        }
    }
    
    for i, topic in enumerate(selected_topics, 1):
        if topic in pm_vignettes:
            vignette_data = pm_vignettes[topic]
        else:
            # Default vignette for other topics
            chunk = random.choice(chunks_by_topic[topic])
            vignette_data = {
                "vignette": f"Case Study: {chunk['content'][:400]}...",
                "questions": [
                    {
                        "question_text": f"Which statement about {topic.lower()} is most accurate?",
                        "options": {
                            "A": "It requires extensive use of derivatives",
                            "B": "It is only applicable to institutional investors", 
                            "C": "It involves systematic risk management processes",
                            "D": "It focuses primarily on short-term performance"
                        },
                        "correct_answer": "C",
                        "explanation": f"Systematic risk management is a key component of {topic.lower()}."
                    },
                    {
                        "question_text": f"The primary objective of {topic.lower()} is to:",
                        "options": {
                            "A": "Maximize absolute returns",
                            "B": "Minimize all forms of risk",
                            "C": "Achieve risk-adjusted returns aligned with objectives",
                            "D": "Outperform all market benchmarks"
                        },
                        "correct_answer": "C", 
                        "explanation": f"{topic} aims to achieve risk-adjusted returns consistent with investment objectives."
                    },
                    {
                        "question_text": f"A key challenge in {topic.lower()} is:",
                        "options": {
                            "A": "Lack of available investment options",
                            "B": "Balancing competing objectives and constraints",
                            "C": "Absence of performance measurement tools",
                            "D": "Regulatory restrictions on all strategies"
                        },
                        "correct_answer": "B",
                        "explanation": f"Balancing competing objectives and constraints is a fundamental challenge in {topic.lower()}."
                    }
                ]
            }
        
        # Add question numbers to each MCQ
        for j, q in enumerate(vignette_data["questions"], 1):
            q["question_number"] = (i-1) * 3 + j
            q["points"] = 6
        
        item_set = {
            "item_set_id": f"PM_Set{i}_{topic.replace(' ', '_')}",
            "set_number": i,
            "topic": topic,
            "vignette": vignette_data["vignette"],
            "questions": vignette_data["questions"],
            "total_points": 18,
            "estimated_time_minutes": 36
        }
        item_sets.append(item_set)
    
    return item_sets

def build_standard_exam(session_type):
    """Build exam following CFA standards"""
    with st.spinner(f"Building CFA Level III {session_type} Session..."):
        if session_type == "AM":
            questions = generate_standard_am_questions()
            total_time = CFA_STANDARDS["AM"]["time_minutes"]
        else:
            questions = generate_standard_pm_questions()
            total_time = CFA_STANDARDS["PM"]["time_minutes"]
        
        exam = {
            "exam_id": f"CFA_L3_{session_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "session": session_type,
            "created_at": datetime.now().isoformat(),
            "total_questions": len(questions),
            "total_time_minutes": total_time,
            "total_points": sum([q.get('total_points', 18) for q in questions]),
            "questions": questions,
            "instructions": [
                f"CFA Level III {session_type} Session",
                f"Time: {total_time} minutes ({total_time//60} hours)",
                "Read all instructions carefully",
                "Show all work for calculations",
                "Manage your time effectively"
            ]
        }
        
        st.session_state.current_exam = exam
        return exam

def display_exam_interface():
    """Display the actual exam taking interface"""
    exam = st.session_state.current_exam
    session = exam["session"]
    
    # Timer
    if st.session_state.start_time:
        elapsed = datetime.now() - st.session_state.start_time
        remaining = timedelta(minutes=exam["total_time_minutes"]) - elapsed
        
        if remaining.total_seconds() <= 0:
            st.error("⏰ Time's up! Exam automatically submitted.")
            st.session_state.exam_submitted = True
            return
        
        # Display timer
        st.markdown(f"### ⏰ Time Remaining: {str(remaining).split('.')[0]}")
        progress = elapsed.total_seconds() / (exam["total_time_minutes"] * 60)
        st.progress(min(progress, 1.0))
    
    st.markdown("---")
    
    if session == "AM":
        display_am_exam()
    else:
        display_pm_exam()
    
    # Submit button
    if st.button("📤 Submit Exam", type="primary"):
        st.session_state.exam_submitted = True
        st.success("✅ Exam submitted!")
        st.balloons()

def display_am_exam():
    """Display AM constructed response questions"""
    exam = st.session_state.current_exam
    
    for question in exam["questions"]:
        st.subheader(f"Question {question['question_number']} - {question['topic']} ({question['total_points']} points)")
        
        # Scenario
        st.markdown("**Scenario:**")
        st.write(question["scenario"])
        st.markdown("---")
        
        # Sub-questions
        for sub_q in question["sub_questions"]:
            st.markdown(f"**{sub_q['part']}.** {sub_q['question']} *({sub_q['points']} points)*")
            
            # Answer input
            answer_key = f"q{question['question_number']}_{sub_q['part']}"
            answer = st.text_area(
                f"Your answer for {sub_q['part']}:",
                key=answer_key,
                height=150,
                placeholder="Provide your detailed answer here..."
            )
            
            # Store answer
            if answer_key not in st.session_state.user_answers:
                st.session_state.user_answers[answer_key] = ""
            st.session_state.user_answers[answer_key] = answer
            
            st.markdown("---")

def display_pm_exam():
    """Display PM multiple choice questions"""
    exam = st.session_state.current_exam
    
    for item_set in exam["questions"]:
        st.subheader(f"Item Set {item_set['set_number']} - {item_set['topic']}")
        
        # Vignette
        st.markdown("**Case Study:**")
        st.write(item_set["vignette"])
        st.markdown("---")
        
        # Questions
        for mcq in item_set["questions"]:
            st.markdown(f"**{mcq['question_number']}.** {mcq['question_text']}")
            
            # Options
            answer_key = f"mcq_{mcq['question_number']}"
            selected = st.radio(
                f"Select answer for question {mcq['question_number']}:",
                options=list(mcq['options'].keys()),
                key=answer_key,
                format_func=lambda x: f"{x}. {mcq['options'][x]}"
            )
            
            # Store answer
            st.session_state.user_answers[answer_key] = selected
            
        st.markdown("---")

def grade_exam():
    """Grade the submitted exam"""
    exam = st.session_state.current_exam
    session = exam["session"]
    
    if session == "PM":
        return grade_pm_exam()
    else:
        return grade_am_exam()

def grade_pm_exam():
    """Grade PM multiple choice exam"""
    exam = st.session_state.current_exam
    total_questions = 0
    correct_answers = 0
    total_points = 0
    earned_points = 0
    detailed_results = []
    
    for item_set in exam["questions"]:
        for mcq in item_set["questions"]:
            total_questions += 1
            total_points += mcq["points"]
            
            answer_key = f"mcq_{mcq['question_number']}"
            user_answer = st.session_state.user_answers.get(answer_key, "")
            correct_answer = mcq["correct_answer"]
            
            is_correct = user_answer == correct_answer
            points_earned = mcq["points"] if is_correct else 0
            
            if is_correct:
                correct_answers += 1
                earned_points += points_earned
            
            detailed_results.append({
                "question_number": mcq["question_number"],
                "topic": item_set["topic"],
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "points_earned": points_earned,
                "explanation": mcq["explanation"]
            })
    
    percentage = (earned_points / total_points * 100) if total_points > 0 else 0
    
    return {
        "session": "PM",
        "total_questions": total_questions,
        "correct_answers": correct_answers,
        "total_points": total_points,
        "earned_points": earned_points,
        "percentage": percentage,
        "passing": percentage >= 70,
        "detailed_results": detailed_results
    }

def grade_am_exam():
    """Grade AM constructed response exam (simplified)"""
    exam = st.session_state.current_exam
    total_points = sum([q["total_points"] for q in exam["questions"]])
    
    # Simplified grading - in real implementation would use AI
    estimated_score = random.randint(60, 85)  # Placeholder
    earned_points = int(total_points * estimated_score / 100)
    
    return {
        "session": "AM", 
        "total_points": total_points,
        "earned_points": earned_points,
        "percentage": estimated_score,
        "passing": estimated_score >= 70,
        "note": "AM grading is simplified. Full version would use AI-assisted grading with rubrics."
    }

def display_results():
    """Display exam results"""
    results = st.session_state.grading_results
    
    st.header(f"📊 {results['session']} Session Results")
    
    # Overall performance
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Score", f"{results['earned_points']}/{results['total_points']}")
    with col2:
        st.metric("Percentage", f"{results['percentage']:.1f}%")
    with col3:
        result_color = "green" if results['passing'] else "red"
        st.markdown(f"**Result:** :{result_color}[{'PASS' if results['passing'] else 'FAIL'}]")
    
    # Detailed results for PM
    if results['session'] == 'PM' and 'detailed_results' in results:
        st.subheader("📝 Detailed Results")
        
        for result in results['detailed_results']:
            with st.expander(f"Question {result['question_number']} - {result['topic']} ({'✅' if result['is_correct'] else '❌'})"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Your Answer:** {result['user_answer']}")
                    st.write(f"**Correct Answer:** {result['correct_answer']}")
                with col2:
                    st.write(f"**Points:** {result['points_earned']}/6")
                    st.write(f"**Explanation:** {result['explanation']}")

def main():
    initialize_session_state()
    
    st.title("🎓 CFA Level III Mock Exam Generator")
    st.markdown("**Complete Exam System** - Following CFA Standards")
    
    # Show content source clearly
    st.sidebar.markdown("---")
    st.sidebar.subheader("📚 Content Source")
    if st.session_state.processed_content:
        st.sidebar.warning("📄 Using Sample Content")
        st.sidebar.write("Questions from pre-loaded CFA material")
        st.sidebar.write("(Not from your uploaded books)")
    else:
        st.sidebar.info("📤 No content loaded")
    
    # Persistence warning
    if st.session_state.exam_started and not st.session_state.exam_submitted:
        st.warning("⚠️ **IMPORTANT:** Refreshing the page will lose your answers and reset the timer. This is a Streamlit limitation.")
    
    # Show CFA standards
    with st.expander("📋 CFA Level III Exam Format"):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**AM Session (Morning)**")
            st.write("• 4 constructed response questions")
            st.write("• 180 minutes (3 hours)")
            st.write("• 45 minutes per question")
            st.write("• Essay format with calculations")
        
        with col2:
            st.markdown("**PM Session (Afternoon)**")
            st.write("• 5 item sets (case studies)")
            st.write("• 3 MCQs per item set (15 total)")
            st.write("• 180 minutes (3 hours)")
            st.write("• 36 minutes per item set")
    
    st.markdown("---")
    
    # Main workflow
    if not st.session_state.processed_content:
        st.subheader("🚀 Step 1: Load Content")
        if st.button("⚡ Load Sample CFA Content", type="primary"):
            content = load_sample_content()
            if content:
                st.session_state.processed_content = content
                st.success("✅ Content loaded!")
                st.rerun()
    
    elif not st.session_state.current_exam:
        st.subheader("📝 Step 2: Build Exam")
        session_type = st.selectbox("Select session:", ["AM", "PM"])
        
        if st.button(f"Build CFA Standard {session_type} Exam", type="primary"):
            build_standard_exam(session_type)
            st.success(f"✅ {session_type} exam built following CFA standards!")
            st.rerun()
    
    elif not st.session_state.exam_started:
        st.subheader("🎯 Step 3: Take Exam")
        exam = st.session_state.current_exam
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Questions", exam["total_questions"])
        with col2:
            st.metric("Time", f"{exam['total_time_minutes']} min")
        with col3:
            st.metric("Points", exam["total_points"])
        
        if st.button("🚀 Start Exam", type="primary"):
            st.session_state.exam_started = True
            st.session_state.start_time = datetime.now()
            st.rerun()
    
    elif not st.session_state.exam_submitted:
        st.subheader(f"📝 {st.session_state.current_exam['session']} Session - In Progress")
        display_exam_interface()
    
    elif not st.session_state.grading_results:
        with st.spinner("Grading exam..."):
            st.session_state.grading_results = grade_exam()
        st.rerun()
    
    else:
        display_results()
        
        # Reset for new exam
        if st.button("🔄 Take Another Exam"):
            st.session_state.current_exam = None
            st.session_state.exam_started = False
            st.session_state.start_time = None
            st.session_state.user_answers = {}
            st.session_state.exam_submitted = False
            st.session_state.grading_results = None
            st.rerun()

if __name__ == "__main__":
    main()
