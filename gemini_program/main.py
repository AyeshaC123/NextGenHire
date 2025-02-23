import google.generativeai as genai

from flask import Flask, request, render_template, redirect, url_for
import os
import io
import PyPDF2
import re
from dotenv import load_dotenv
import os
from flask import session

app = Flask(__name__)

load_dotenv()
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

def extract_technical_skills(job_description):
    """
    Extracts technical skills from the job description using Gemini.
    """
    prompt = f"Extract the technical skills from the following job description:\n{job_description}\n\nList the skills as comma separated values. Only extract skills explicitly mentioned in the job description."
    response = model.generate_content(prompt)
    # Split the skills by comma and remove leading/trailing whitespace
    technical_skills = {skill.strip() for skill in response.text.split(',')}
    return technical_skills

def find_matching_skills(resume_text, job_description):
    """
    Finds matching technical skills between the resume and job description.
    """
    # Extract technical skills from the resume
    resume_skills = extract_technical_skills(resume_text)
    # Extract technical skills from the job description
    job_skills = extract_technical_skills(job_description)
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
        prompt = request.form['prompt']
        generated_text = generate_text(prompt)
        return render_template('index.html', generated_text=generated_text, session=session.get('user'))
    return render_template('index.html', session=session.get('user'))

# @app.route('/', methods=['GET'])
# def index():
#     return render_template('index.html')


@app.route('/cover_letter_generator', methods=['GET', 'POST'])
def cover_letter_generator():
    if request.method == 'POST':
        # Check if the resume file was uploaded
        if 'resume' not in request.files:
            return render_template('cover_letter_generator.html', error='No resume file uploaded')

        resume_file = request.files['resume']

        # Check if a file was selected
        if resume_file.filename == '':
            return render_template('cover_letter_generator.html', error='No resume file selected')

        # Check if the job description was provided
        job_description = request.form.get('prompt')
        if not job_description:
            return render_template('cover_letter_generator.html', error='No job description provided')

        try:
            # Extract text from the resume
            resume_text = extract_text_from_pdf(resume_file)

            # Find matching skills
            matching_skills = find_matching_skills(resume_text, job_description)

            # Create a prompt for the AI model
            prompt = f"Write a cover letter using the following resume:\n{resume_text}\n\nAnd the following job description:\n{job_description}\nonly writing about the skills: {', '.join(matching_skills)}."

            # Generate the cover letter
            generated_text = generate_text(prompt)

            return render_template('cover_letter_generator.html', generated_text=generated_text)

        except Exception as e:
            return render_template('cover_letter_generator.html', error=str(e))

    return render_template('cover_letter_generator.html')

@app.route('/resume_enhancer')
def resume_enhancer():
    return render_template('resume_enhancer.html')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5004)
