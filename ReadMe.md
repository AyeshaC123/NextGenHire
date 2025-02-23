# NextGenHire

NextGenHire is a web application that helps users with their job search. It includes features such as an AI cover letter generator and a resume enhancer.

## How to Run the Project

1.  **Clone the repository:**

    ```bash
    git clone <repository_url>
    cd NextGenHire
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r gemini_program/requirements.txt
    ```

    Additionally, install missing dependencies:

    ```bash
    pip install Flask-PyMongo chardet
    ```

3.  **Set up environment variables: (already done)**

    *   Create a `.env` file in the `NextGenHire/` directory.
    *   Add the following environment variables to the `.env` file:

        ```
        AUTH0_DOMAIN=<your_auth0_domain>
        AUTH0_CLIENT_ID=<your_auth0_client_id>
        AUTH0_CLIENT_SECRET=<your_auth0_client_secret>
        APP_SECRET_KEY=<your_app_secret_key>
        MONGO_URI=<your_mongodb_uri>
        GOOGLE_API_KEY=<your_google_api_key>
        ```

    *   Replace the placeholders with your actual values.

4.  **Run the Flask application:**

    ```bash
    FLASK_APP=gemini_program/server.py flask run --port=5001 --debug
    ```

    *   This will start the Flask application on port 5001.
    *   Open your web browser and go to `http://127.0.0.1:5001` to access the application.
