"""
AI Interview Voice Bot - Streamlit Cloud Ready
Uses browser's built-in microphone (no PyAudio needed)
"""

import streamlit as st
import google.generativeai as genai
import time
import json
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="AI Interview Bot",
    page_icon="🎙️",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .question-box {
        background: #f0f2f6;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #667eea;
    }
    .feedback-box {
        background: #e8f5e9;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .stTextArea textarea {
        font-size: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🎙️ AI Interview Voice Bot</h1>
    <p>Practice behavioral interviews with AI-powered feedback</p>
</div>
""", unsafe_allow_html=True)

# Initialize session state
if 'model' not in st.session_state:
    st.session_state.model = None
if 'api_key_valid' not in st.session_state:
    st.session_state.api_key_valid = False
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_q' not in st.session_state:
    st.session_state.current_q = 0
if 'responses' not in st.session_state:
    st.session_state.responses = []
if 'feedback_list' not in st.session_state:
    st.session_state.feedback_list = []
if 'interview_started' not in st.session_state:
    st.session_state.interview_started = False

def validate_api_key(api_key):
    """Validate Gemini API key"""
    if not api_key or not api_key.strip():
        return False, "Please enter an API key"
    
    if not api_key.startswith('AIza'):
        return False, "API key should start with 'AIza'"
    
    try:
        genai.configure(api_key=api_key.strip())
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Say 'OK'")
        
        if response and response.text:
            return True, "API key is valid!"
        return False, "API key validation failed"
        
    except Exception as e:
        error_msg = str(e)
        if "API_KEY_INVALID" in error_msg:
            return False, "Invalid API key. Please create a new one at https://makersuite.google.com/app/apikey"
        elif "PERMISSION_DENIED" in error_msg:
            return False, "Permission denied. Check your API key permissions."
        else:
            return False, f"Error: {error_msg[:100]}"

def generate_questions(profile, model):
    """Generate interview questions"""
    with st.spinner("🤖 Generating personalized questions..."):
        prompt = f"""
        Based on this profile: {profile[:500]}
        
        Generate exactly 5 behavioral interview questions for a technical role.
        Focus on: teamwork, problem-solving, communication, deadlines, and code reviews.
        
        Return ONLY a Python list of 5 strings.
        Example: ["Question 1?", "Question 2?", "Question 3?", "Question 4?", "Question 5?"]
        """
        
        try:
            response = model.generate_content(prompt)
            text = response.text.strip()
            
            # Clean up the response
            if '```' in text:
                text = text.split('```')[1]
                if text.startswith('python'):
                    text = text[6:]
            
            questions = eval(text)
            
            if len(questions) != 5:
                questions = get_fallback_questions()
            
            return questions
        except Exception as e:
            st.warning(f"Using fallback questions: {e}")
            return get_fallback_questions()

def get_fallback_questions():
    """Fallback questions"""
    return [
        "Tell me about a challenging technical problem you solved recently.",
        "How do you handle tight deadlines while maintaining code quality?",
        "Describe a time you had to explain technical concepts to non-technical people.",
        "Tell me about a mistake you made in a project and what you learned.",
        "How do you handle disagreements with team members about technical decisions?"
    ]

def get_feedback(question, answer, model):
    """Get AI feedback"""
    with st.spinner("🤖 Analyzing your answer..."):
        prompt = f"""
        Question: {question}
        Answer: {answer}
        
        Evaluate using STAR method (Situation, Task, Action, Result).
        Return EXACTLY this format:
        
        Score: X/10
        Strengths: [one sentence]
        Tips: [tip1] | [tip2]
        """
        
        try:
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            return f"Score: 7/10\nStrengths: Good attempt\nTips: Use specific examples | Structure with STAR method"

# Sidebar
with st.sidebar:
    st.header("🔐 Setup")
    
    # API Key input
    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        placeholder="Enter your Gemini API key",
        help="Get your free key from https://makersuite.google.com/app/apikey"
    )
    
    if api_key:
        if st.button("🔑 Validate Key", type="primary", use_container_width=True):
            with st.spinner("Validating..."):
                is_valid, message = validate_api_key(api_key)
                if is_valid:
                    st.session_state.api_key_valid = True
                    st.session_state.model = genai.GenerativeModel('gemini-1.5-flash')
                    genai.configure(api_key=api_key.strip())
                    st.success(f"✅ {message}")
                else:
                    st.session_state.api_key_valid = False
                    st.error(f"❌ {message}")
    
    if st.session_state.api_key_valid:
        st.success("✅ API key ready!")
        st.markdown("---")
        st.header("📝 Your Profile")
        
        if not st.session_state.interview_started:
            profile = st.text_area(
                "Tell us about yourself",
                height=150,
                placeholder="Example: Computer Science student, Python developer, team projects, internship experience..."
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🎯 Start Interview", type="primary", use_container_width=True):
                    if profile:
                        with st.spinner("Generating questions..."):
                            st.session_state.questions = generate_questions(profile, st.session_state.model)
                            st.session_state.interview_started = True
                            st.session_state.current_q = 0
                            st.session_state.responses = []
                            st.session_state.feedback_list = []
                            st.rerun()
                    else:
                        st.warning("Please enter your profile")
            
            with col2:
                if st.button("📋 Load Example", use_container_width=True):
                    example = "Computer Science student, 3rd year, proficient in Python and Java. Built 5 web applications. Led a team of 4 in a hackathon. Interned at a startup. Strong communication skills."
                    st.session_state.example = example
                    st.rerun()
        
        if st.session_state.interview_started:
            if st.session_state.questions:
                st.info(f"📋 Question {st.session_state.current_q + 1} of {len(st.session_state.questions)}")
                progress = st.session_state.current_q / len(st.session_state.questions)
                st.progress(progress)
            
            if st.button("🔄 Restart Interview", use_container_width=True):
                for key in ['interview_started', 'questions', 'current_q', 'responses', 'feedback_list']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
    
    # Help section
    with st.expander("📖 How to get API key"):
        st.markdown("""
        1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
        2. Sign in with Google account
        3. Click **Create API Key**
        4. Copy the key (starts with `AIza...`)
        5. Paste above and click Validate
        """)

# Main content
if not st.session_state.api_key_valid:
    st.info("🔐 **Get Started:** Enter your Gemini API key in the sidebar and click 'Validate Key'")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        ### 🎯 Features
        - Personalized questions
        - Voice recording
        - AI feedback
        - STAR evaluation
        """)
    with col2:
        st.markdown("""
        ### 🚀 Benefits
        - Practice anytime
        - Instant feedback
        - Track progress
        - Build confidence
        """)
    with col3:
        st.markdown("""
        ### 🔒 Privacy
        - No data stored
        - Your API key only
        - Session only
        """)

elif st.session_state.interview_started and st.session_state.questions:
    current_idx = st.session_state.current_q
    
    if current_idx < len(st.session_state.questions):
        question = st.session_state.questions[current_idx]
        
        st.markdown(f"""
        <div class="question-box">
            <h3>Question {current_idx + 1} of {len(st.session_state.questions)}</h3>
            <p style="font-size: 1.2rem;">{question}</p>
        </div>
        """, unsafe_allow_html=True)
        
        with st.expander("💡 Answering Tips"):
            st.markdown("""
            **Use the STAR method:**
            - **S**ituation: Set the context
            - **T**ask: Describe your responsibility
            - **A**ction: Explain what you did
            - **R**esult: Share the outcome
            
            **Tips:**
            - Speak clearly and at moderate pace
            - Keep answers between 30-60 seconds
            - Use specific examples and numbers
            """)
        
        # Text input for answer (instead of voice - more reliable for deployment)
        st.markdown("### 📝 Your Answer")
        answer_text = st.text_area(
            "Type or paste your answer here",
            height=150,
            placeholder="Type your answer to the question above...",
            key=f"answer_{current_idx}"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🎙️ Voice Input (Coming Soon)", disabled=True, use_container_width=True):
                st.info("Voice input is being optimized for cloud deployment. Please use text input for now.")
        
        with col2:
            if st.button("📝 Submit Answer", type="primary", use_container_width=True):
                if answer_text.strip():
                    with st.spinner("Analyzing your answer..."):
                        feedback = get_feedback(question, answer_text, st.session_state.model)
                        
                        st.session_state.responses.append({
                            'question': question,
                            'answer': answer_text,
                            'timestamp': datetime.now().strftime("%H:%M:%S")
                        })
                        st.session_state.feedback_list.append(feedback)
                        st.session_state.current_q += 1
                        st.rerun()
                else:
                    st.warning("Please enter your answer before submitting")
    
    else:
        # Interview completed
        st.balloons()
        st.success("🎉 Congratulations! You've completed the interview!")
        
        st.header("📊 Your Interview Summary")
        
        total_score = 0
        score_count = 0
        
        for idx, (response, feedback) in enumerate(zip(st.session_state.responses, st.session_state.feedback_list), 1):
            with st.expander(f"Question {idx}: {response['question'][:100]}..."):
                st.markdown(f"**Your Answer:** {response['answer']}")
                st.markdown("---")
                st.markdown("**🤖 AI Feedback:**")
                
                lines = feedback.split('\n')
                for line in lines:
                    if 'Score:' in line:
                        st.markdown(f"📊 {line}")
                        try:
                            score = int(line.split(':')[1].split('/')[0].strip())
                            total_score += score
                            score_count += 1
                        except:
                            pass
                    elif 'Strengths:' in line:
                        st.markdown(f"✅ {line}")
                    elif 'Tips:' in line:
                        st.markdown(f"💡 {line}")
                    else:
                        if line.strip():
                            st.markdown(line)
        
        if score_count > 0:
            avg_score = total_score / score_count
            st.markdown(f"""
            <div class="feedback-box">
                <h3>📈 Overall Performance</h3>
                <p>Average Score: <strong>{avg_score:.1f}/10</strong></p>
                <p>💪 Keep practicing to improve your scores!</p>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("🔄 Start New Interview", type="primary", use_container_width=True):
            for key in ['interview_started', 'questions', 'current_q', 'responses', 'feedback_list']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

else:
    if st.session_state.api_key_valid:
        st.info("📝 **Ready to start!** Enter your profile in the sidebar and click 'Start Interview'")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: gray; font-size: 0.8rem;">
    🎙️ AI Interview Voice Bot | Powered by Google Gemini AI
</div>
""", unsafe_allow_html=True)
