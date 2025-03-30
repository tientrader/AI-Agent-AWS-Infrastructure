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
        description="You are an expert recruiter who analyzes resumes across all industries and job roles.",
        instructions=[
            "Analyze the resume based on the provided job requirements",
            "Provide detailed feedback covering strengths, weaknesses, and areas for improvement",
            "Assess technical, soft skills, and relevant experience required for the role",
            "For technical roles, evaluate domain knowledge, problem-solving ability, and practical experience",
            "For non-technical roles, consider industry knowledge, communication skills, leadership, and strategic thinking",
            "Project experience should be considered as valid work experience",
            "Hands-on experience with relevant tools, technologies, or methodologies is valuable",
            "Return a structured JSON response with selection decision, justification, and improvement suggestions"
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
            "Always end emails with exactly: 'Best,\nThe AI Recruiting Team'",
            "Never include the sender's or receiver's name in the signature",
            f"The name of the company is '{st.session_state.company_name}'",
            "Do not use ** or any other markdown formatting for titles. Write plain text instead."
        ],
        show_tool_calls=True
    )