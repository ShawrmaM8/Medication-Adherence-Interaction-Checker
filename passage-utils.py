# Purpose: Handle file reading (with optional translation, PDF reading)

import fitz # PyMuPDF
from docx import Document
import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize

def extract_text(file):
    """Detect file type  and extract text"""
    if file.type == 'application/pdf':
        return extract_text_from_pdf(file)
    elif file.type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        return extract_text_from_docx(file)
    elif file.type == 'text/plain':
        return file.read().decode('utf-8')
    else:
        return ""
    
def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype='pdf')
    text = ''
    for page in doc:
        text += page.get_text()
    return text 

def extract_text_from_docx(file):
    doc = Document(file)
    return "\n".join([para.text for para in doc.paragraphs])

def split_sentences(text):
    return sent_tokenize(text)
                    