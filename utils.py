import PyPDF2
import streamlit as st

def extract_text_from_pdf(pdf_file) -> str:
    """Extracts text from a given PDF file."""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"Error extracting PDF text: {str(e)}")
        return ""