import json
import pytz
import streamlit as st
from database import get_db_connection
from datetime import datetime, timedelta
from agno.agent import Agent
from phi.utils.log import logger

def analyze_resume(
    resume_text: str,
    role: str,
    role_requirements: str,
    analyzer: Agent
) -> tuple[bool, str]:
    """Analyze a resume based on the role requirements."""
    try:
        response = analyzer.run(
            f"""Please analyze this resume against the following requirements and provide your response in valid JSON format:
            Role: {role}
            Role-Specific Evaluation Criteria: {role_requirements}
            
            Resume Text: {resume_text}

            Your response must be a valid JSON object like this:
            {{
                "selected": true/false,
                "feedback": {{
                    "matching_skills": ["skill1", "skill2"],
                    "matching_skills_score": 0-100,
                    "missing_skills": ["skill3", "skill4"],
                    "project_evaluation": "Evaluation of relevant projects",
                    "overall_fit": "Summary of the candidate’s suitability",
                    "overall_fit_score": 0-100,
                    "experience_level": "intern/fresher/junior/mid/senior/leader/manager"
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
        """
    )


def send_rejection_email(email_agent: Agent, to_email: str, role: str, feedback: str) -> None:
    """Send a rejection email with constructive feedback."""
    email_agent.run(
        f"""
        Send an email to {to_email} regarding their application for the {role} position.
        Use this specific style:
        1. be empathetic and human
        2. mention specific feedback from: {feedback}
        3. encourage them to upskill and try again
        4. suggest some learning resources based on missing skills
        5. end the email with exactly:
           Best,
           The AI Recruiting Team.
        
        Do not include any names in the signature.
        The tone should be like a human writing a quick but thoughtful email.
        """
    )


def schedule_interview(email_agent: Agent, role: str) -> None:
    """Schedule an interview, save it to the database, and send confirmation email."""
    try:
        interview_time = get_next_available_time()
        
        if not interview_time:
            st.error("⚠ No available interview slots. Please try again later.")
            return

        candidate_email = st.session_state.get("candidate_email")
        if not candidate_email:
            st.error("⚠ Missing candidate email.")
            return

        conn, cursor = get_db_connection()
        cursor.execute("""
            INSERT INTO interview_schedule (candidate_email, interview_time, created_at)
            VALUES (%s, %s, NOW())
        """, (candidate_email, interview_time))
        conn.commit()
        cursor.close()
        conn.close()

        zoom_link = st.session_state.get("zoom_link", "N/A")
        zoom_passcode = st.session_state.get("zoom_passcode", "N/A")

        email_agent.run(
            f"""Send an interview confirmation email with these details:

            Role: {role} position  
            Date & Time: {interview_time} Vietnam Time (UTC+7)  
            Meeting Link: {zoom_link}  
            Passcode: {zoom_passcode}  

            Please ensure that you are available for the meeting during business hours (9 AM - 5 PM Vietnam Time).  

            If you have any questions or need further assistance, feel free to reach out.  

            Best,  
            The AI Recruiting Team.
            """
        )

        st.success(f"✅ Interview scheduled successfully! Time: {interview_time} Vietnam Time.")

    except Exception as e:
        logger.error(f"❌ Error scheduling interview: {str(e)}")
        st.error("❌ Unable to schedule interview. Please try again.")


def get_next_available_time() -> str:
    """Find available interview slots within the 9 AM - 5 PM (UTC+7) timeframe, automatically moving to the next day if no slots are left."""
    vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
    current_time_vn = datetime.now(vn_tz)
    search_date = current_time_vn + timedelta(days=1)

    conn, cursor = get_db_connection()

    while True:
        for hour in range(9, 17):
            interview_time = search_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            formatted_time = interview_time.strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute("SELECT COUNT(*) FROM interview_schedule WHERE interview_time = %s", (formatted_time,))
            if cursor.fetchone()[0] == 0:
                conn.close()
                return formatted_time
        
        search_date += timedelta(days=1)
