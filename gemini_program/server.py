import json
import os
import time
import hashlib
from os import environ as env
from urllib.parse import quote_plus, urlencode, quote
from flask import Flask, redirect, render_template, session, url_for, request, send_file
from authlib.integrations.flask_client import OAuth
import google.generativeai as genai
import io
import PyPDF2
import chardet

# Load environment variables
from dotenv import find_dotenv, load_dotenv

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

app = Flask(__name__)
app.secret_key = env.get("APP_SECRET_KEY")

# Auth0 OAuth setup
oauth = OAuth(app)
oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={"scope": "openid profile email"},
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration'
)

# Google Gemini API setup
GOOGLE_API_KEY = env.get("GOOGLE_API_KEY")  # Use .env instead of hardcoding API keys!
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-pro')

# File upload directory
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Cache for reducing API calls
cache = {}

# ========================
#  PDF Text Extraction
# ========================
def extract_text_from_pdf(file):
    """
    Extracts text from an uploaded PDF file.
    """
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text
        return text
    except Exception as e:
        return f"An error occurred while reading the PDF: {e}"

# ========================
#  Resume Improvement Suggestions
# ========================
def suggest_stronger_verbs(resume_text):
    """
    Sends a prompt to Gemini with the resume and returns places in the resume that can be improved.
    """
    prompt = (
        f"Please review the following resume and provide specific suggestions for improvement. "
        f"Identify areas where the language is weak, vague, or could be more impactful. "
        f"Suggest specific rewrites or alternative phrasing to strengthen the resume only for the descriptions, not trivial things like name, email, gpa, etc. "
        f"Focus on improving the clarity, conciseness, and impact of the language. only give suggestions for up to 5 of the most needed things a time not more "
        f"Return the suggestions in a list format, with each item including the original text and the suggested improvement.\n\n"
        f"Resume:\n{resume_text}"
    )

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"

def extract_technical_skills(text):
    """
    Extracts technical skills using Gemini API.
    """
    prompt = f"Extract the technical skills from the following text:\n{text}\n\nList the skills as comma-separated values."

    # Cache lookup
    key = hashlib.sha256(text.encode()).hexdigest()
    if key in cache:
        return cache[key]

    try:
        response = model.generate_content(prompt)
        skills = {skill.strip() for skill in response.text.split(',')}
        cache[key] = skills  # Store in cache
        print(f"Cached Skills: {skills}")
        return skills
    except Exception as e:
        print(f"An error occurred: {e}")
        return set()  # Return an empty set in case of an error

# ========================
#  Generate Text (AI Cover Letter)
# ========================
def generate_text(prompt):
    """
    Generates text using the Gemini API based on the given prompt.
    Implements rate limiting to prevent 429 errors.
    """
    key = hashlib.sha256(prompt.encode()).hexdigest()
    if key in cache:
        return cache[key]  # Return cached result

    retries = 3
    for attempt in range(retries):
        try:
            response = model.generate_content(prompt)
            cache[key] = response.text  # Store response in cache
            return response.text
        except Exception as e:
            if "429" in str(e):
                wait_time = (attempt + 1) * 10  # Wait 10s, 20s, 30s
                print(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                return f"An error occurred: {e}"

    return "Failed after multiple attempts due to API rate limits."


# ========================
#  Auth Routes
# ========================
@app.route("/login")
def login():
    return oauth.auth0.authorize_redirect(redirect_uri=url_for("callback", _external=True))

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = oauth.auth0.authorize_access_token()
    session["user"] = token
    return redirect("/")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(
        "https://" + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {"returnTo": url_for("home", _external=True), "client_id": env.get("AUTH0_CLIENT_ID")},
            quote_via=quote_plus,
        )
    )

# ========================
#  Main Page
# ========================
@app.route("/")
def home():
    if "user" not in session:
        return render_template("login.html")
    return render_template("index.html", session=session.get("user"))

# ========================
#  Cover Letter Generator
# ========================
@app.route("/cover_letter_generator", methods=['GET', 'POST'])
def cover_letter_generator():
    if request.method == 'POST':
        if 'resume' not in request.files:
            return render_template('cover_letter_generator.html', error='No resume file uploaded')

        resume_file = request.files['resume']
        if resume_file.filename == '':
            return render_template('cover_letter_generator.html', error='No resume file selected')

        job_description = request.form.get('prompt')
        if not job_description:
            return render_template('cover_letter_generator.html', error='No job description provided')

        try:
            # Extract text from resume
            resume_text = extract_text_from_pdf(resume_file)

            # Extract technical skills from resume
            resume_skills = extract_technical_skills(resume_text)
            print(f"Resume Skills: {resume_skills}")

            # Extract technical skills from job description
            job_description_skills = extract_technical_skills(job_description)
            print(f"Job Description Skills: {job_description_skills}")

            # Find missing skills (skills in job description but not in resume)
            missing_skills = job_description_skills.difference(resume_skills)

            # Create AI prompt
            prompt = (
                f"Write a professional cover letter using the following resume:\n{resume_text}\n\n"
                f"For this job description:\n{job_description}\n\n"
                f"Highlight my existing skills and experience. "
                f"Do not include any contact information, addresses, or dates in the cover letter."
            )

            if missing_skills:
                prompt += (
                    f"Also, address the fact that I may not have experience with the following skills: {', '.join(missing_skills)}. "
                    f"Express my strong interest and eagerness to learn these skills quickly and contribute to the company's success."
                )

            # Generate cover letter
            generated_text = generate_text(prompt)

            return render_template("cover_letter_generator.html", generated_text=generated_text)

        except Exception as e:
            return render_template("cover_letter_generator.html", error=str(e))

    return render_template("cover_letter_generator.html")

# ========================
#  Resume Enhancer Page
# ========================
@app.route("/resume_enhancer", methods=['GET', 'POST'])
def resume_enhancer():
    if request.method == 'POST':
        if 'resume' not in request.files:
            return render_template('resume_enhancer.html', error='No resume file uploaded')

        resume_file = request.files['resume']
        if resume_file.filename == '':
            return render_template('resume_enhancer.html', error='No resume file selected')

        job_description = request.form.get('job_description')
        if not job_description:
            return render_template('resume_enhancer.html', error='No job description provided')

        try:
            resume_text = extract_text_from_pdf(resume_file)

            if not resume_text:
                return render_template('resume_enhancer.html', error='Could not extract text from resume. Please ensure it is a valid PDF.')

            suggested_verbs = suggest_stronger_verbs(resume_text)

            job_description_skills = extract_technical_skills(job_description)
            resume_skills = extract_technical_skills(resume_text)
            missing_skills = job_description_skills.difference(resume_skills)
            suggested_keywords = list(missing_skills)

            return render_template(
                "resume_enhancer.html",
                suggested_verbs=suggested_verbs,
                suggested_keywords=suggested_keywords,
            )

        except Exception as e:
            return render_template("resume_enhancer.html", error=str(e))

    return render_template("resume_enhancer.html")

# ========================
#  Run Flask App
# ========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 5001), debug=True)
