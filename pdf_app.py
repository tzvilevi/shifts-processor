"""Lightweight standalone web app for removing a PDF password.

Only depends on Flask and pypdf, so it deploys easily on free hosts
(PythonAnywhere, Hugging Face Spaces, etc.) without the scheduler's heavier
dependencies. The upload form is served at the site root.

Run locally:
    python pdf_app.py
Then open http://localhost:5000/ in a browser.
"""

from flask import Flask, redirect

from pdf_web import pdf_bp

app = Flask(__name__)
app.register_blueprint(pdf_bp)


@app.route('/')
def index():
    return redirect('/pdf')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
