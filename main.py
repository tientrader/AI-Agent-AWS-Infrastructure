import os
import time
import json
import requests
from datetime import datetime, timedelta
from typing import Literal, Dict, Optional

import PyPDF2
import pytz
import streamlit as st
from dotenv import load_dotenv
from streamlit_pdf_viewer import pdf_viewer

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.email import EmailTools
from phi.tools.zoom import ZoomTool
from phi.utils.log import logger

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
email_address = os.getenv("EMAIL_ADDRESS")
email_app_password = os.getenv("EMAIL_APP_PASSWORD")
zoom_client_id = os.getenv("ZOOM_CLIENT_ID")
zoom_client_secret = os.getenv("ZOOM_CLIENT_SECRET")
zoom_account_id = os.getenv("ZOOM_ACCOUNT_ID")
ZOOM_LINK = os.getenv("ZOOM_LINK")
ZOOM_PASSCODE = os.getenv("ZOOM_PASSCODE")

class CustomZoomTool(ZoomTool):
    def __init__(self, *, account_id: Optional[str] = None, client_id: Optional[str] = None, client_secret: Optional[str] = None, name: str = "zoom_tool"):
        super().__init__(account_id=account_id, client_id=client_id, client_secret=client_secret, name=name)
        self.token_url = "https://zoom.us/oauth/token"
        self.access_token = None
        self.token_expires_at = 0

    def get_access_token(self) -> str:
        if self.access_token and time.time() < self.token_expires_at:
            return str(self.access_token)
            
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"grant_type": "account_credentials", "account_id": self.account_id}

        try:
            response = requests.post(self.token_url, headers=headers, data=data, auth=(self.client_id, self.client_secret))
            response.raise_for_status()

            token_info = response.json()
            self.access_token = token_info["access_token"]
            expires_in = token_info["expires_in"]
            self.token_expires_at = time.time() + expires_in - 60

            self._set_parent_token(str(self.access_token))
            return str(self.access_token)

        except requests.RequestException as e:
            logger.error(f"Error fetching access token: {e}")
            return ""

    def _set_parent_token(self, token: str) -> None:
        """Helper method to set the token in the parent ZoomTool class"""
        if token:
            self._ZoomTool__access_token = token


# Role requirements as a constant dictionary
ROLE_REQUIREMENTS: Dict[str, str] = {
    "ai_ml_engineer": """
        **Core Skills:**
        - Python, PyTorch, TensorFlow, JAX
        - Understanding of mathematical foundations (Linear Algebra, Probability, Statistics)
        - Machine Learning algorithms (Supervised, Unsupervised, Reinforcement Learning)
        - Deep Learning architectures (CNN, RNN, Transformer, GANs)
        - Data preprocessing and feature engineering
        - Model evaluation and hyperparameter tuning
        
        **MLOps & Deployment:**
        - Model training and evaluation pipelines
        - Model versioning and reproducibility (MLflow, DVC)
        - API deployment (FastAPI, Flask, gRPC)
        - Scalable model deployment (Docker, Kubernetes, AWS/GCP/Azure)
        - Monitoring and debugging ML models in production

        **Specialized Skills:**
        - RAG (Retrieval-Augmented Generation), LLM fine-tuning, and inference optimization
        - Vector databases (Pinecone, FAISS, Weaviate)
        - Prompt Engineering and tuning for large-scale AI models
        - Distributed computing for ML (Ray, Spark, Dask)
        - Edge AI and model quantization (ONNX, TensorRT, TFLite)

        **Tools & Tech Stack:**
        - Python, Jupyter, NumPy, Pandas, SciPy
        - PyTorch, TensorFlow, Hugging Face Transformers
        - SQL, NoSQL, Redis, Apache Kafka
        - AWS Sagemaker, GCP Vertex AI, Azure ML
        - Kubernetes, Docker, Terraform, Airflow
    """,

    "frontend_engineer": """
        **Core Skills:**
        - Strong understanding of JavaScript and TypeScript
        - Experience with modern frontend frameworks (React.js, Next.js, Vue.js, Angular)
        - Proficiency in HTML5, CSS3, TailwindCSS, SCSS
        - State management (Redux, Zustand, Vuex, Pinia, NgRx)
        - UI component libraries (Material UI, Ant Design, Chakra UI)
        - SSR (Server-Side Rendering) and CSR (Client-Side Rendering)

        **Performance & Optimization:**
        - Web performance optimization (Lighthouse, Core Web Vitals)
        - Code splitting, lazy loading, tree shaking
        - Caching strategies (Service Workers, IndexedDB, LocalStorage)
        - Accessibility (ARIA, WCAG compliance)
        - Progressive Web Apps (PWA)

        **Testing & CI/CD:**
        - Unit testing, integration testing (Jest, Testing Library, Cypress, Playwright)
        - Linting, formatting (ESLint, Prettier)
        - CI/CD pipelines for frontend deployment (GitHub Actions, Vercel, Netlify)

        **Tools & Tech Stack:**
        - JavaScript, TypeScript, HTML5, CSS3
        - React.js, Next.js, Vue.js, Angular
        - Redux, Zustand, React Query, Apollo Client
        - TailwindCSS, Material UI, Ant Design
        - Jest, Cypress, Playwright
        - Webpack, Vite, Rollup
    """,

    "backend_engineer": """
        **Core Skills:**
        - Strong proficiency in Java, JavaScript, Python or C++
        - Understanding of RESTful API
        - Software design patterns (Factory, Singleton, Observer, Strategy, etc.)
        - ACID, SOLID principles, Clean Architecture, Hexagonal Architecture
        - Algorithms, data structures, and system design

        **Scalability & Distributed Systems:**
        - Microservices architecture, CQRS, Event Sourcing
        - Message brokers (Kafka, RabbitMQ)
        - Caching strategies (Redis, Memcached)
        - Database scaling (Sharding, Replication, Partitioning)
        - High-throughput and low-latency services
        - API Gateway and service mesh (Spring Cloud Gateway, Istio)

        **Databases & Storage:**
        - Relational databases (PostgreSQL, MySQL, SQL Server)
        - NoSQL databases (MongoDB, Cassandra, DynamoDB)
        - Full-text search engines (Elasticsearch, OpenSearch)

        **Cloud & DevOps:**
        - Cloud platforms: AWS, GCP, Azure
        - Infrastructure as Code (Terraform, AWS CDK)
        - Containerization & orchestration (Docker, Kubernetes)
        - Observability (Prometheus, Grafana, OpenTelemetry, CloudWatch, ELK Stack)
        - Security best practices (OAuth2, JWT, mTLS)

        **Tools & Tech Stack:**
        - Java (Spring Boot), Python (FastAPI, Django)
        - Redis, Kafka, PostgreSQL, Elasticsearch
        - AWS Lambda, ECS, EKS, S3, CloudFront
        - Kubernetes, Terraform, Helm, CI/CD pipelines
    """
}


def init_session_state() -> None:
    """Initialize only necessary session state variables."""
    defaults = {
        'candidate_email': "", 'openai_api_key': "", 'resume_text': "", 'analysis_complete': False,
        'is_selected': False, 'zoom_account_id': "", 'zoom_client_id': "", 'zoom_client_secret': "",
        'email_sender': "", 'email_passkey': "", 'company_name': "", 'current_pdf': None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


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
        ],
        markdown=True
    )

def create_email_agent() -> Agent:
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
            "Act like a human writing an email and use all lowercase letters",
            "Maintain a friendly yet professional tone",
            "Always end emails with exactly: 'best,\nthe ai recruiting team'",
            "Never include the sender's or receiver's name in the signature",
            f"The name of the company is '{st.session_state.company_name}'"
        ],
        markdown=True,
        show_tool_calls=True
    )


def create_scheduler_agent() -> Agent:
    zoom_tools = CustomZoomTool(
        account_id=st.session_state.zoom_account_id,
        client_id=st.session_state.zoom_client_id,
        client_secret=st.session_state.zoom_client_secret
    )

    return Agent(
        name="Interview Scheduler",
        model=OpenAIChat(
            id="gpt-4o",
            api_key=st.session_state.openai_api_key
        ),
        tools=[zoom_tools],
        description="You are an interview scheduling coordinator.",
        instructions=[
            "You are an expert at scheduling technical interviews using Zoom.",
            "Schedule interviews during business hours (9 AM - 5 PM EST)",
            "Create meetings with proper titles and descriptions",
            "Ensure all meeting details are included in responses",
            "Use ISO 8601 format for dates",
            "Handle scheduling errors gracefully"
        ],
        markdown=True,
        show_tool_calls=True
    )


def extract_text_from_pdf(pdf_file) -> str:
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error extracting PDF text: {str(e)}")
        return ""


def analyze_resume(
    resume_text: str,
    role: Literal["ai_ml_engineer", "frontend_engineer", "backend_engineer"],
    analyzer: Agent
) -> tuple[bool, str]:
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

        # Lưu phản hồi vào session state
        st.session_state.resume_selected = result["selected"]
        st.session_state.resume_feedback = result["feedback"]

        return result["selected"], result["feedback"]  

    except (json.JSONDecodeError, ValueError) as e:
        error_message = f"Error analyzing resume: {str(e)}"
        st.session_state.resume_feedback = error_message
        st.session_state.resume_selected = False
        return False, error_message  


def send_selection_email(email_agent: Agent, to_email: str, role: str) -> None:
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
    """
    Send a rejection email with constructive feedback.
    """
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
    """
    Schedule interviews during business hours (9 AM - 5 PM Vietnam Time).
    """
    try:
        # Get current time in Vietnam Time
        vn_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        current_time_vn = datetime.now(vn_tz)

        # Set interview time to tomorrow at 11:00 AM Vietnam Time
        tomorrow_vn = current_time_vn + timedelta(days=1)
        interview_time = tomorrow_vn.replace(hour=11, minute=0, second=0, microsecond=0)
        formatted_time = interview_time.strftime('%Y-%m-%dT%H:%M:%S')

        # Send confirmation email
        email_agent.run(
            f"""Send an interview confirmation email with these details:
            - Role: {role} position
            - Meeting Time: {formatted_time} Vietnam Time (UTC+7)
            - Meeting Link: {ZOOM_LINK}
            - Passcode: {ZOOM_PASSCODE}

            Important Notes:
            - The meeting must be between 9 AM - 5 PM Vietnam Time
            - Use Vietnam Time (UTC+7) timezone for all communications
            - Include timezone information in the meeting details.
            """
        )

        st.success(f"Interview scheduled successfully! Zoom link: {ZOOM_LINK}")

    except Exception as e:
        logger.error(f"Error scheduling interview: {str(e)}")
        st.error("Unable to schedule interview. Please try again.")


def init_session_state():
    """Initialize session state variables."""
    if "candidate_email" not in st.session_state:
        st.session_state.candidate_email = ""

    if "resume_text" not in st.session_state:
        st.session_state.resume_text = ""

    if "analysis_complete" not in st.session_state:
        st.session_state.analysis_complete = False

    if "openai_api_key" not in st.session_state:
        st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")

    if "zoom_account_id" not in st.session_state:
        st.session_state.zoom_account_id = os.getenv("ZOOM_ACCOUNT_ID", "")

    if "zoom_client_id" not in st.session_state:
        st.session_state.zoom_client_id = os.getenv("ZOOM_CLIENT_ID", "")

    if "zoom_client_secret" not in st.session_state:
        st.session_state.zoom_client_secret = os.getenv("ZOOM_CLIENT_SECRET", "")

    if "email_sender" not in st.session_state:
        st.session_state.email_sender = os.getenv("EMAIL_ADDRESS", "")

    if "email_passkey" not in st.session_state:
        st.session_state.email_passkey = os.getenv("EMAIL_APP_PASSWORD", "")

    if "company_name" not in st.session_state:
        st.session_state.company_name = os.getenv("COMPANY_NAME", "")

def main():
    st.title("AI Recruitment System")
    init_session_state()

    with st.sidebar:
        st.header("Configuration")

        # OpenAI Configuration
        st.subheader("OpenAI Settings")
        api_key = st.text_input("OpenAI API Key", type="password", value=st.session_state.openai_api_key)
        if api_key:
            st.session_state.openai_api_key = api_key

        # Zoom Configuration
        st.subheader("Zoom Settings")
        zoom_account_id = st.text_input("Zoom Account ID", type="password", value=st.session_state.zoom_account_id)
        zoom_client_id = st.text_input("Zoom Client ID", type="password", value=st.session_state.zoom_client_id)
        zoom_client_secret = st.text_input("Zoom Client Secret", type="password", value=st.session_state.zoom_client_secret)

        # Email Configuration
        st.subheader("Email Settings")
        email_sender = st.text_input("Sender Email", value=st.session_state.email_sender)
        email_passkey = st.text_input("Email App Password", type="password", value=st.session_state.email_passkey)
        company_name = st.text_input("Company Name", value=st.session_state.company_name)

        # Cập nhật session state nếu người dùng thay đổi giá trị
        if zoom_account_id:
            st.session_state.zoom_account_id = zoom_account_id
        if zoom_client_id:
            st.session_state.zoom_client_id = zoom_client_id
        if zoom_client_secret:
            st.session_state.zoom_client_secret = zoom_client_secret
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

    role = st.selectbox("Select the role you're applying for:", ["ai_ml_engineer", "frontend_engineer", "backend_engineer"])
    with st.expander("View Required Skills", expanded=True): st.markdown(ROLE_REQUIREMENTS[role])

    # Add a "New Application" button before the resume upload
    if st.button("📝 New Application"):
        # Clear only the application-related states
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
        # Process the resume text
        if not st.session_state.resume_text:
            with st.spinner("Processing your resume..."):
                resume_text = extract_text_from_pdf(resume_file)
                if resume_text:
                    st.session_state.resume_text = resume_text
                    st.success("Resume processed successfully!")
                else:
                    st.error("Could not process the PDF. Please try again.")

    # Email input with session state
    email = st.text_input(
        "Candidate's email address",
        value=st.session_state.candidate_email,
        key="email_input"
    )
    st.session_state.candidate_email = email

    # Analysis and next steps
    if st.session_state.resume_text and email and not st.session_state.analysis_complete:
        if st.button("Analyze Resume"):
            with st.spinner("Analyzing your resume..."):
                resume_analyzer = create_resume_analyzer()
                email_agent = create_email_agent()  # Create email agent here
                
                if resume_analyzer and email_agent:
                    print("DEBUG: Starting resume analysis")
                    is_selected, feedback = analyze_resume(
                        st.session_state.resume_text,
                        role,
                        resume_analyzer
                    )
                    print(f"DEBUG: Analysis complete - Selected: {is_selected}, Feedback: {feedback}")

                    if is_selected:
                        st.success("Congratulations! Your skills match our requirements.")
                        st.session_state.analysis_complete = True
                        st.session_state.is_selected = True
                        st.rerun()
                    else:
                        st.warning("Unfortunately, your skills don't match our requirements.")

                        # Send rejection email
                        with st.spinner("Sending feedback email..."):
                            try:
                                send_rejection_email(
                                    email_agent=email_agent,
                                    to_email=email,
                                    role=role,
                                    feedback=feedback
                                )
                                st.info("We've sent you an email with detailed feedback.")
                            except Exception as e:
                                logger.error(f"Error sending rejection email: {e}")
                                st.error("Could not send feedback email. Please try again.")

    st.subheader("Resume Analysis Result")

    if st.session_state.get("resume_feedback"):
        # Kiểm tra xem ứng viên có được chọn hay không
        if st.session_state.get("resume_selected"):
            st.success("✅ **Selected**")
        else:
            st.error("❌ **Not Selected**")

        # Hiển thị format giống nhau dù có được chọn hay không
        st.markdown(f"""
        - **Matching Skills (Score: {st.session_state.resume_feedback['matching_skills_score']}):**  
        {", ".join(st.session_state.resume_feedback['matching_skills'])}

        - **Missing Skills (Score: {st.session_state.resume_feedback['missing_skills_score']}):**  
        {", ".join(st.session_state.resume_feedback['missing_skills'])}

        - **Project Evaluation (Score: {st.session_state.resume_feedback['project_experience_score']}):**  
        {st.session_state.resume_feedback['project_evaluation']}

        - **Overall Fit (Score: {st.session_state.resume_feedback['overall_fit_score']}):**  
        {st.session_state.resume_feedback['overall_fit']}

        🏆 **Experience Level: {st.session_state.resume_feedback['experience_level'].capitalize()}**
        """)

        # Phần feedback chung
        st.markdown(f"**Feedback:** {st.session_state.resume_feedback.get('overall_fit', 'No detailed feedback available.')}")

    if st.session_state.get('analysis_complete') and st.session_state.get('is_selected', False):
        st.success("Congratulations! Your skills match our requirements.")
        st.info("Click 'Proceed with Application' to continue with the interview process.")
        
        if st.button("Proceed with Application", key="proceed_button"):
            print("DEBUG: Proceed button clicked")  # Debug
            with st.spinner("🔄 Processing your application..."):
                try:
                    print("DEBUG: Creating email agent")  # Debug
                    email_agent = create_email_agent()
                    print(f"DEBUG: Email agent created: {email_agent}")  # Debug
                    
                    print("DEBUG: Creating scheduler agent")  # Debug
                    scheduler_agent = create_scheduler_agent()
                    print(f"DEBUG: Scheduler agent created: {scheduler_agent}")  # Debug

                    # 3. Send selection email
                    with st.status("📧 Sending confirmation email...", expanded=True) as status:
                        print(f"DEBUG: Attempting to send email to {st.session_state.candidate_email}")  # Debug
                        send_selection_email(
                            email_agent,
                            st.session_state.candidate_email,
                            role
                        )
                        print("DEBUG: Email sent successfully")  # Debug
                        status.update(label="✅ Confirmation email sent!")

                    # 4. Schedule interview
                    with st.status("📅 Scheduling interview...", expanded=True) as status:
                        print("DEBUG: Attempting to schedule interview")  # Debug
                        schedule_interview(
                            scheduler_agent,
                            st.session_state.candidate_email,
                            email_agent,
                            role
                        )
                        print("DEBUG: Interview scheduled successfully")  # Debug
                        status.update(label="✅ Interview scheduled!")

                    print("DEBUG: All processes completed successfully")  # Debug
                    st.success("""
                        🎉 Application Successfully Processed!
                        
                        Please check your email for:
                        1. Selection confirmation ✅
                        2. Interview details with Zoom link 🔗
                        
                        Next steps:
                        1. Review the role requirements
                        2. Prepare for your technical interview
                        3. Join the interview 5 minutes early
                    """)

                except Exception as e:
                    print(f"DEBUG: Error occurred: {str(e)}")  # Debug
                    print(f"DEBUG: Error type: {type(e)}")  # Debug
                    import traceback
                    print(f"DEBUG: Full traceback: {traceback.format_exc()}")  # Debug
                    st.error(f"An error occurred: {str(e)}")
                    st.error("Please try again or contact support.")

    # Reset button
    if st.sidebar.button("Reset Application"):
        for key in st.session_state.keys():
            if key != 'openai_api_key':
                del st.session_state[key]
        st.rerun()

if __name__ == "__main__":
    main()