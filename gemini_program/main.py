import google.generativeai as genai
from flask import Flask, request, render_template
from dotenv import load_dotenv
import os
from flask import session

app = Flask(__name__)

load_dotenv()
# Replace with your actual Gemini API key
GOOGLE_API_KEY = "AIzaSyCvFJIH-5t0Uj9QKiXMjzUf4_H6Y3cIZqQ"

genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel('gemini-pro')

def generate_text(prompt):
    """
    Generates text using the Gemini API based on the given prompt.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"An error occurred: {e}"

# @app.route('/', methods=['GET', 'POST'])
# def index():
#     if request.method == 'POST':
#         prompt = request.form['prompt']
#         generated_text = generate_text(prompt)
#         return render_template('index.html', generated_text=generated_text)
#     return render_template('index.html')

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        prompt = request.form['prompt']
        generated_text = generate_text(prompt)
        return render_template('index.html', generated_text=generated_text, session=session.get('user'))
    return render_template('index.html', session=session.get('user'))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5001)
