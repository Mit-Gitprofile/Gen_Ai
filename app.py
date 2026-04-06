"""
AI Interview Voice Bot - Streamlit Version
No PyAudio required - uses browser microphone
Optimized for 32-bit Windows
"""

import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv
import os
import time
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    st.error("❌ GEMINI_API_KEY not found in .env file")
    st.info("""
    **How to get your API Key:**
    1. Go to: https://makersuite.google.com/app/apikey
    2. Sign in with your Google account
    3. Click 'Create API Key'
    4. Copy the key and paste it in the `.env` file
    """)
    st.stop()

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Failed to configure Gemini API: {e}")
    st.stop()

# Initialize session state
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_q' not in st.session_state:
    st.session_state.current_q = 0
if 'responses' not in st.session_state:
    st.session_state.responses = []
if 'feedback' not in st.session_state:
    st.session_state.feedback = []
if 'interview_started' not in st.session_state:
    st.session_state.interview_started = False
if 'recording_text' not in st.session_state:
    st.session_state.recording_text = ""

# Page config
st.set_page_config(
    page_title="AI Interview Voice Bot",
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
    .score-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-weight: bold;
        margin: 0.5rem 0;
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

def generate_questions(profile):
    """Generate interview questions based on profile"""
    with st.spinner("🤖 Generating personalized questions..."):
        prompt = f"""
        Candidate Profile: {profile}
        
        Generate exactly 5 behavioral interview questions for a technical role.
        Focus on: teamwork, problem-solving, communication, deadlines, and code reviews.
        
        Return ONLY a Python list of 5 strings. Example: ["Q1?", "Q2?", "Q3?", "Q4?", "Q5?"]
        """
        
        try:
            response = model.generate_content(prompt)
            questions_text = response.text.strip()
            
            # Parse the response
            if '```' in questions_text:
                questions_text = questions_text.split('```')[1]
                if questions_text.startswith('python'):
                    questions_text = questions_text[6:]
            
            questions = eval(questions_text)
            
            if len(questions) != 5:
                questions = get_fallback_questions()
            
            return questions
        except:
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

def get_feedback(question, answer):
    """Get AI feedback on answer"""
    with st.spinner("🤖 Analyzing your answer..."):
        prompt = f"""
        Question: {question}
        Candidate's Answer: {answer}
        
        Evaluate using STAR method (Situation, Task, Action, Result).
        Return EXACTLY this format:
        
        Score: X/10
        Strengths: [one sentence]
        Tips: [tip 1] | [tip 2]
        """
        
        try:
            response = model.generate_content(prompt)
            feedback = response.text.strip()
            return feedback
        except:
            return "Score: 7/10\nStrengths: Good attempt\nTips: Use specific examples | Structure with STAR method"

# Sidebar for profile setup
with st.sidebar:
    st.header("📝 Setup")
    
    if not st.session_state.interview_started:
        profile = st.text_area(
            "Your Profile",
            placeholder="Example: Computer Science student, Python developer, worked on team projects, experienced with Agile methodology...",
            height=150
        )
        
        if st.button("🎯 Start Interview", type="primary"):
            if profile:
                st.session_state.questions = generate_questions(profile)
                st.session_state.interview_started = True
                st.session_state.current_q = 0
                st.session_state.responses = []
                st.session_state.feedback = []
                st.rerun()
            else:
                st.warning("Please enter your profile first")
    
    if st.session_state.interview_started:
        st.info(f"📋 Question {st.session_state.current_q + 1} of {len(st.session_state.questions)}")
        progress = (st.session_state.current_q) / len(st.session_state.questions) if st.session_state.questions else 0
        st.progress(progress)
        
        if st.button("🔄 Restart Interview"):
            for key in ['interview_started', 'questions', 'current_q', 'responses', 'feedback']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

# Main interview flow
if st.session_state.interview_started and st.session_state.questions:
    current_idx = st.session_state.current_q
    
    if current_idx < len(st.session_state.questions):
        # Display current question
        current_question = st.session_state.questions[current_idx]
        
        st.markdown(f"""
        <div class="question-box">
            <h3>Question {current_idx + 1} of {len(st.session_state.questions)}</h3>
            <p style="font-size: 1.2rem;">{current_question}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Audio recording using browser's microphone (no PyAudio needed)
        st.markdown("### 🎤 Record Your Answer")
        
        # Use Streamlit's audio input
        audio_value = st.audio_input("Click to record your answer", key=f"audio_{current_idx}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("⏺️ Record Answer", type="primary", use_container_width=True):
                st.info("🎙️ Please speak clearly into your microphone for 15-20 seconds")
                st.info("After recording, click 'Submit Answer'")
        
        with col2:
            if st.button("📝 Submit Answer", type="secondary", use_container_width=True):
                if audio_value:
                    # Save audio temporarily
                    temp_audio = f"temp_audio_{current_idx}.wav"
                    with open(temp_audio, "wb") as f:
                        f.write(audio_value.getbuffer())
                    
                    # Transcribe using speech recognition
                    import speech_recognition as sr
                    recognizer = sr.Recognizer()
                    
                    with st.spinner("📝 Transcribing your answer..."):
                        try:
                            with sr.AudioFile(temp_audio) as source:
                                audio = recognizer.record(source)
                                transcript = recognizer.recognize_google(audio)
                            
                            st.success(f"✅ Transcribed: {transcript}")
                            
                            # Get feedback
                            feedback = get_feedback(current_question, transcript)
                            
                            # Store response
                            st.session_state.responses.append({
                                'question': current_question,
                                'answer': transcript
                            })
                            st.session_state.feedback.append(feedback)
                            
                            # Move to next question
                            st.session_state.current_q += 1
                            
                            # Clean up
                            os.remove(temp_audio)
                            
                            st.rerun()
                            
                        except sr.UnknownValueError:
                            st.error("❌ Could not understand audio. Please speak clearly and try again.")
                        except Exception as e:
                            st.error(f"❌ Error processing audio: {e}")
                else:
                    st.warning("Please record your answer first")
        
        # Display recording tips
        with st.expander("💡 Tips for a good answer"):
            st.markdown("""
            **Use the STAR method:**
            - **S**ituation: Set the context
            - **T**ask: Describe your responsibility
            - **A**ction: Explain what you did
            - **R**esult: Share the outcome
            
            **Speak clearly** and at a moderate pace
            **Keep answers** between 30-60 seconds
            **Be specific** with examples
            """)
    
    else:
        # Interview completed - show summary
        st.success("🎉 Congratulations! You've completed the interview!")
        
        st.header("📊 Interview Summary")
        
        total_score = 0
        score_count = 0
        
        for idx, (response, feedback) in enumerate(zip(st.session_state.responses, st.session_state.feedback), 1):
            with st.expander(f"Question {idx}: {response['question'][:100]}..."):
                st.markdown(f"**Your Answer:** {response['answer']}")
                st.markdown("---")
                st.markdown("**Feedback:**")
                
                # Parse feedback
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
                        st.markdown(line)
        
        if score_count > 0:
            avg_score = total_score / score_count
            st.markdown(f"""
            <div class="feedback-box">
                <h3>📈 Overall Performance</h3>
                <p>Average Score: <strong>{avg_score:.1f}/10</strong></p>
                <p>Keep practicing to improve your scores!</p>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("🔄 Start New Interview", type="primary"):
            for key in ['interview_started', 'questions', 'current_q', 'responses', 'feedback']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()

else:
    # Welcome screen
    st.markdown("""
    ### 🎯 Welcome to AI Interview Voice Bot!
    
    **How it works:**
    1. 📝 Enter your profile in the sidebar
    2. 🎯 AI generates 5 personalized questions
    3. 🎤 Record your answers using your microphone
    4. 🤖 Get instant feedback with scores and tips
    5. 📊 Review your performance summary
    
    **Perfect for:**
    - Job interview preparation
    - Practicing behavioral questions
    - Improving communication skills
    - Building interview confidence
    
    ### 🚀 Get Started
    Enter your profile in the left sidebar and click "Start Interview"!
    """)
    
    st.info("💡 **Tip:** The more detailed your profile, the better the questions will be!")

# Footer
st.markdown("---")
st.markdown("🎙️ AI Interview Voice Bot | Powered by Google Gemini AI")