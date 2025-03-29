import os
import streamlit as st

from dotenv import load_dotenv
from streamlit_pdf_viewer import pdf_viewer
from phi.utils.log import logger

from agents import create_resume_analyzer, create_email_agent
from utils import extract_text_from_pdf
from recruitment_utils import analyze_resume, send_selection_email, send_rejection_email, schedule_interview

load_dotenv()

ENV_VARS = {
    "openai_api_key": "OPENAI_API_KEY",
    "email_sender": "EMAIL_ADDRESS",
    "email_passkey": "EMAIL_APP_PASSWORD",
    "zoom_client_id": "ZOOM_CLIENT_ID",
    "zoom_client_secret": "ZOOM_CLIENT_SECRET",
    "zoom_account_id": "ZOOM_ACCOUNT_ID",
    "zoom_link": "ZOOM_LINK",
    "zoom_passcode": "ZOOM_PASSCODE",
    "company_name": "COMPANY_NAME"
}

def init_session_state():
    """Initialize session state variables."""
    default_values = {
        "candidate_email": "",
        "resume_text": "",
        "analysis_complete": False
    }
    
    for key, value in default_values.items():
        st.session_state.setdefault(key, value)
    
    for key, env_var in ENV_VARS.items():
        st.session_state.setdefault(key, os.getenv(env_var, ""))


def main():
    st.title("AI Recruitment System")
    init_session_state()

    with st.sidebar:
        st.header("Configuration")

        st.subheader("OpenAI Settings")
        api_key = st.text_input("OpenAI API Key", type="password", value=st.session_state.openai_api_key)
        if api_key:
            st.session_state.openai_api_key = api_key

        st.subheader("Zoom Settings")
        zoom_link = st.text_input("Zoom Meeting Link", value=st.session_state.zoom_link)
        zoom_passcode = st.text_input("Zoom Passcode", type="password", value=st.session_state.zoom_passcode)

        st.subheader("Email Settings")
        email_sender = st.text_input("Sender Email", value=st.session_state.email_sender)
        email_passkey = st.text_input("Email App Password", type="password", value=st.session_state.email_passkey)
        company_name = st.text_input("Company Name", value=st.session_state.company_name)

        if zoom_link:
            st.session_state.zoom_link = zoom_link
        if zoom_passcode:
            st.session_state.zoom_passcode = zoom_passcode
        if email_sender:
            st.session_state.email_sender = email_sender
        if email_passkey:
            st.session_state.email_passkey = email_passkey
        if company_name:
            st.session_state.company_name = company_name

        required_configs = {
            "OpenAI API Key": st.session_state.openai_api_key,
            "Zoom Account ID": st.session_state.zoom_account_id,
            "Zoom Client ID": st.session_state.zoom_client_id,
            "Zoom Client Secret": st.session_state.zoom_client_secret,
            "Zoom Link": st.session_state.zoom_link,
            "Zoom Passcode": st.session_state.zoom_passcode,
            "Email Sender": st.session_state.email_sender,
            "Email Password": st.session_state.email_passkey,
            "Company Name": st.session_state.company_name,
        }

    missing_configs = [k for k, v in required_configs.items() if not v]
    if missing_configs:
        st.warning(f"Please configure the following in the sidebar: {', '.join(missing_configs)}")
        return

    if not st.session_state.openai_api_key:
        st.warning("Please enter your OpenAI API key in the sidebar to continue.")
        return

    role = st.text_input("Enter Role", "")
    role_requirements = st.text_area("Enter role requirements", "")

    if st.button("📝 New Application"):
        keys_to_clear = ['resume_text', 'analysis_complete', 'is_selected', 'candidate_email', 'current_pdf']
        for key in keys_to_clear:
            if key in st.session_state:
                st.session_state[key] = None if key == 'current_pdf' else ""
        st.rerun()

    resume_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"], key="resume_uploader")
    if resume_file is not None and resume_file != st.session_state.get('current_pdf'):
        st.session_state.current_pdf = resume_file
        st.session_state.resume_text = ""
        st.session_state.analysis_complete = False
        st.session_state.is_selected = False
        st.rerun()

    if resume_file:
        st.subheader("Uploaded Resume")
        col1, col2 = st.columns([4, 1])
        
        with col1:
            import tempfile, os
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
                tmp_file.write(resume_file.read())
                tmp_file_path = tmp_file.name
            resume_file.seek(0)
            try: pdf_viewer(tmp_file_path)
            finally: os.unlink(tmp_file_path)
        
        with col2:
            st.download_button(label="📥 Download", data=resume_file, file_name=resume_file.name, mime="application/pdf")

        if not st.session_state.resume_text:
            with st.spinner("Processing your resume..."):
                resume_text = extract_text_from_pdf(resume_file)
                if resume_text:
                    st.session_state.resume_text = resume_text
                    st.success("Resume processed successfully!")
                else:
                    st.error("Could not process the PDF. Please try again.")

    email = st.text_input(
        "Candidate's email address",
        value=st.session_state.candidate_email,
        key="email_input"
    )
    st.session_state.candidate_email = email

    if st.session_state.resume_text and email and not st.session_state.analysis_complete:
        if st.button("Analyze Resume"):
            with st.spinner("Analyzing your resume..."):
                resume_analyzer = create_resume_analyzer()
                email_agent = create_email_agent()
                
                if resume_analyzer and email_agent:
                    is_selected, feedback = analyze_resume(
                        st.session_state.resume_text,
                        role,
                        role_requirements,
                        resume_analyzer
                    )

                    if is_selected:
                        st.success("Congratulations! Your skills match our requirements!")
                        st.session_state.analysis_complete = True
                        st.session_state.is_selected = True
                        st.rerun()
                    else:
                        st.warning("Unfortunately, your skills don't match our requirements.")

                        with st.spinner("Sending feedback email..."):
                            try:
                                send_rejection_email(
                                    email_agent=email_agent,
                                    to_email=email,
                                    role=role,
                                    feedback=feedback
                                )
                                st.info("We've sent you an email with detailed feedback!")
                            except Exception as e:
                                logger.error(f"Error sending rejection email: {e}")
                                st.error("Could not send feedback email. Please try again!")

    st.subheader("Resume Analysis Result")

    if st.session_state.get("resume_feedback"):
        if st.session_state.get("resume_selected"):
            st.success("✅ **Selected**")
        else:
            st.error("❌ **Not Selected**")

        st.markdown(f"""
        - **Matching Skills (Score: {st.session_state.resume_feedback['matching_skills_score']}):**  
        {", ".join(st.session_state.resume_feedback.get('matching_skills', []))}  

        - **Missing Skills:**  
        {", ".join(st.session_state.resume_feedback.get('missing_skills', []))}  

        - **Project Evaluation:**  
        {st.session_state.resume_feedback['project_evaluation']}  

        - **Overall Fit (Score: {st.session_state.resume_feedback['overall_fit_score']}):**  
        {st.session_state.resume_feedback['overall_fit']}  

        🏆 **Experience Level:** {st.session_state.resume_feedback['experience_level'].capitalize()}  
        """)

        st.markdown(f"**Feedback:** {st.session_state.resume_feedback.get('overall_fit', 'No detailed feedback available.')}")

    if st.session_state.get('analysis_complete') and st.session_state.get('is_selected', False):
        st.success("Congratulations! Your skills match our requirements.")
        st.info("Click 'Proceed with Application' to continue with the interview process.")
        
        if st.button("Proceed with Application", key="proceed_button"):
            with st.spinner("🔄 Processing your application..."):
                try:
                    email_agent = create_email_agent()

                    with st.status("📧 Sending confirmation email...", expanded=True) as status:
                        send_selection_email(
                            email_agent,
                            st.session_state.candidate_email,
                            role
                        )
                        status.update(label="✅ Confirmation email sent!")

                    with st.status("📅 Scheduling interview...", expanded=True) as status:
                        schedule_interview(
                            email_agent,
                            role
                        )
                        status.update(label="✅ Interview scheduled!")

                    st.success("🎉 Application Successfully Processed!")

                except Exception as e:
                    print(f"DEBUG: Error occurred: {str(e)}")
                    print(f"DEBUG: Error type: {type(e)}")
                    import traceback
                    print(f"DEBUG: Full traceback: {traceback.format_exc()}")
                    st.error(f"An error occurred: {str(e)}")
                    st.error("Please try again or contact support.")

    if st.sidebar.button("Reset Application"):
        for key in st.session_state.keys():
            if key != 'openai_api_key':
                del st.session_state[key]
        st.rerun()


if __name__ == "__main__":
    main()