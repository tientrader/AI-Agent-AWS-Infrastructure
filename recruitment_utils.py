import json
import pytz
import streamlit as st
from datetime import datetime, timedelta
from agno.agent import Agent
from phi.utils.log import logger
from role_requirements import ROLE_REQUIREMENTS

def analyze_resume(
    resume_text: str,
    role: str,
    analyzer: Agent
) -> tuple[bool, str]:
    """Analyze a resume based on the role requirements."""
    try:
        response = analyzer.run(
            f"""Please analyze this resume against the following requirements and provide your response in valid JSON format:
            Role: {role}
            Role-Specific Evaluation Criteria:
            {ROLE_REQUIREMENTS[role]}
            
            Resume Text:
            {resume_text}

            Your response must be a valid JSON object like this:
            {{
                "selected": true/false,
                "feedback": {{
                    "matching_skills": ["skill1", "skill2"],
                    "matching_skills_score": 8,  
                    "missing_skills": ["skill3", "skill4"],
                    "missing_skills_score": 4,  
                    "project_evaluation": "Evaluation of relevant projects",
                    "project_experience_score": 7,  
                    "overall_fit": "Summary of the candidate’s suitability",
                    "overall_fit_score": 8,  
                    "experience_level": "junior/mid/senior"
                }}
            }}
            Important: Return ONLY the JSON object without any markdown formatting or backticks.
            """
        )

        assistant_message = next((msg.content for msg in response.messages if msg.role == 'assistant'), None)
        if not assistant_message:
            raise ValueError("No assistant message found in response.")

        result = json.loads(assistant_message.strip())
        if not isinstance(result, dict) or "selected" not in result or "feedback" not in result:
            raise ValueError("Invalid response format")

        st.session_state.resume_selected = result["selected"]
        st.session_state.resume_feedback = result["feedback"]

        return result["selected"], result["feedback"]  

    except (json.JSONDecodeError, ValueError) as e:
        error_message = f"Error analyzing resume: {str(e)}"
        st.session_state.resume_feedback = error_message
        st.session_state.resume_selected = False
        return False, error_message


def send_selection_email(email_agent: Agent, to_email: str, role: str) -> None:
    """Send a selection email to the candidate."""
    email_agent.run(
        f"""
        Send an email to {to_email} regarding their selection for the {role} position.
        The email should:
        1. Congratulate them on being selected
        2. Explain the next steps in the process
        3. Mention that they will receive interview details shortly
        4. The name of the company is 'AI Recruiting Team'
        """
    )


def send_rejection_email(email_agent: Agent, to_email: str, role: str, feedback: str) -> None:
    """Send a rejection email with constructive feedback."""
    email_agent.run(
        f"""
        Send an email to {to_email} regarding their application for the {role} position.
        Use this specific style:
        1. use all lowercase letters
        2. be empathetic and human
        3. mention specific feedback from: {feedback}
        4. encourage them to upskill and try again
        5. suggest some learning resources based on missing skills
        6. end the email with exactly:
           best,
           the ai recruiting team
        
        Do not include any names in the signature.
        The tone should be like a human writing a quick but thoughtful email.
        """
    )


def schedule_interview(scheduler: Agent, candidate_email: str, email_agent: Agent, role: str) -> None:
    """Schedule interviews during business hours (9 AM - 5 PM Vietnam Time)."""
    try:
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        current_time_vn = datetime.now(vn_tz)
        tomorrow_vn = current_time_vn + timedelta(days=1)
        interview_time = tomorrow_vn.replace(hour=11, minute=0, second=0, microsecond=0)
        formatted_time = interview_time.strftime('%Y-%m-%dT%H:%M:%S')

        zoom_link = st.session_state.get("zoom_link", "N/A")
        zoom_passcode = st.session_state.get("zoom_passcode", "N/A")

        email_agent.run(
            f"""Send an interview confirmation email with these details:
            - Role: {role} position
            - Meeting Time: {formatted_time} Vietnam Time (UTC+7)
            - Meeting Link: {zoom_link}
            - Passcode: {zoom_passcode}

            Important Notes:
            - The meeting must be between 9 AM - 5 PM Vietnam Time
            - Use Vietnam Time (UTC+7) timezone for all communications
            - Include timezone information in the meeting details.
            """
        )

        st.success(f"Interview scheduled successfully! Zoom link: {zoom_link}")

    except Exception as e:
        logger.error(f"Error scheduling interview: {str(e)}")
        st.error("Unable to schedule interview. Please try again.")