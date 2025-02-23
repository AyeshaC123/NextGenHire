import google.generativeai as genai
from flask import Flask, request, render_template, redirect, url_for
import os
import io
import PyPDF2
import re

app = Flask(__name__)

# Replace with your actual Gemini API key
GOOGLE_API_KEY = "AIzaSyCvFJIH-5t0Uj9QKiXMjzUf4_H6Y3cIZqQ"
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def extract_text_from_pdf(file):
    """
    Extracts text from a PDF file.
    """
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        return f"An error occurred while reading the PDF: {e}"

def find_matching_skills(resume_text, job_description):
    """
    Finds matching skills between the resume and job description.
    """
    resume_skills = set(re.findall(r'\b\w+\b', resume_text.lower()))
    job_skills = set(re.findall(r'\b\w+\b', job_description.lower()))
    matching_skills = resume_skills.intersection(job_skills)
    return matching_skills

def generate_text(prompt, matching_skills=None):
    """
    Generates text using the Gemini API based on the given prompt,
    emphasizing the matching skills.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if the resume file was uploaded
        if 'resume' not in request.files:
            return render_template('index.html', error='No resume file uploaded')

        resume_file = request.files['resume']

        # Check if a file was selected
        if resume_file.filename == '':
            return render_template('index.html', error='No resume file selected')

        # Check if the job description was provided
        job_description = request.form.get('prompt')
        if not job_description:
            return render_template('index.html', error='No job description provided')

        try:
            # Extract text from the resume
            resume_text = extract_text_from_pdf(resume_file)

            # Find matching skills
            matching_skills = find_matching_skills(resume_text, job_description)

            # Create a prompt for the AI model
            prompt = f"Write a cover letter using the following resume:\n{resume_text}\n\nAnd the following job description:\n{job_description}\nonly writing about the skills: {', '.join(matching_skills)}."

            # Generate the cover letter
            generated_text = generate_text(prompt)

            return render_template('index.html', generated_text=generated_text)

        except Exception as e:
            return render_template('index.html', error=str(e))

    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5004)
