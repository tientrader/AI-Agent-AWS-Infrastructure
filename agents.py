import streamlit as st
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.email import EmailTools

def create_resume_analyzer() -> Agent:
    """Creates and returns a resume analysis agent."""
    if not st.session_state.openai_api_key:
        st.error("Please enter your OpenAI API key first.")
        return None

    return Agent(
        model=OpenAIChat(
            id="gpt-4o",
            api_key=st.session_state.openai_api_key
        ),
        description="You are an expert technical recruiter who analyzes resumes.",
        instructions=[
            "Analyze the resume against the provided job requirements",
            "Be detailed in feedback, covering strengths and weaknesses",
            "For AI/ML roles, consider research, implementation, and deployment",
            "For Backend roles, evaluate system design, scalability, and database skills",
            "For Frontend roles, assess UI/UX skills, performance, and JavaScript frameworks",
            "Consider project experience as valid experience",
            "Value hands-on experience with key technologies",
            "Return a JSON response with selection decision and detailed feedback"
        ]
    )

def create_email_agent() -> Agent:
    """Creates and returns an email handling agent."""
    return Agent(
        model=OpenAIChat(
            id="gpt-4o",
            api_key=st.session_state.openai_api_key
        ),
        tools=[EmailTools(
            receiver_email=st.session_state.candidate_email,
            sender_email=st.session_state.email_sender,
            sender_name=st.session_state.company_name,
            sender_passkey=st.session_state.email_passkey
        )],
        description="You are a professional recruitment coordinator handling email communications.",
        instructions=[
            "Draft and send professional recruitment emails",
            "Act like a human writing an email",
            "Maintain a friendly yet professional tone",
            "Always end emails with exactly: 'best,\nthe ai recruiting team'",
            "Never include the sender's or receiver's name in the signature",
            f"The name of the company is '{st.session_state.company_name}'",
            "Do not use ** or any other markdown formatting for titles. Write plain text instead."
        ],
        show_tool_calls=True
    )