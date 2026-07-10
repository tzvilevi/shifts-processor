"""Flask blueprint for the PDF password-removal web interface.

This module only depends on Flask and pypdf (via pdf_password_remover), so it
can be deployed as a lightweight standalone app without the heavier scheduler
dependencies (e.g. ortools).
"""

import io

from flask import Blueprint, request, Response, send_file

from pdf_password_remover import (
    remove_password,
    NotEncryptedError,
    WrongPasswordError,
)

pdf_bp = Blueprint('pdf', __name__)

PDF_UNLOCK_PAGE = """
<!doctype html>
<html lang="he" dir="rtl">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>הסרת סיסמה מקובץ PDF</title>
    <style>
        body { font-family: Arial, "Segoe UI", sans-serif; background: #f4f6fb;
               margin: 0; padding: 2rem; color: #1f2937; }
        .card { max-width: 460px; margin: 3rem auto; background: #fff;
                border-radius: 12px; padding: 2rem;
                box-shadow: 0 8px 24px rgba(0,0,0,.08); }
        h1 { font-size: 1.4rem; margin-top: 0; }
        p.desc { color: #6b7280; font-size: .95rem; }
        label { display: block; margin: 1rem 0 .4rem; font-weight: 600; }
        input[type=file], input[type=password] {
            width: 100%; padding: .6rem; border: 1px solid #d1d5db;
            border-radius: 8px; box-sizing: border-box; font-size: 1rem; }
        button { margin-top: 1.5rem; width: 100%; padding: .8rem;
                 background: #2563eb; color: #fff; border: none;
                 border-radius: 8px; font-size: 1rem; cursor: pointer; }
        button:hover { background: #1d4ed8; }
        .error { background: #fef2f2; color: #b91c1c; padding: .75rem 1rem;
                 border-radius: 8px; margin-bottom: 1rem; font-size: .9rem; }
    </style>
</head>
<body>
    <div class="card">
        <h1>הסרת סיסמה מקובץ PDF</h1>
        <p class="desc">העלו קובץ PDF מוגן והזינו את הסיסמה שלו.
        נחזיר לכם עותק זהה ללא סיסמה. הסיסמה חייבת להיות ידועה לכם —
        השירות אינו מנחש סיסמאות.</p>
        <!--ERROR-->
        <form method="post" enctype="multipart/form-data" action="/pdf/remove-password">
            <label for="file">קובץ PDF</label>
            <input id="file" type="file" name="file" accept="application/pdf" required>
            <label for="password">סיסמה</label>
            <input id="password" type="password" name="password" required>
            <button type="submit">הסר סיסמה והורד</button>
        </form>
    </div>
</body>
</html>
"""


def _render_pdf_page(error_html=""):
    return PDF_UNLOCK_PAGE.replace("<!--ERROR-->", error_html)


@pdf_bp.route('/pdf', methods=['GET'])
def pdf_unlock_page():
    return _render_pdf_page()


@pdf_bp.route('/pdf/remove-password', methods=['POST'])
def pdf_remove_password_endpoint():
    """Remove the password from an uploaded PDF using a known password.

    Accepts a multipart form (fields ``file`` and ``password``) from the
    browser, or the same fields from an API client. Returns the unlocked PDF
    as a download.
    """
    uploaded = request.files.get('file')
    password = request.form.get('password', '')

    def _respond_error(message, status):
        # Browsers get the HTML form back with the message; API clients get JSON.
        if request.accept_mimetypes.accept_html and uploaded is not None:
            error_html = f'<div class="error">{message}</div>'
            return Response(_render_pdf_page(error_html), status=status,
                            mimetype='text/html')
        return {"error": message}, status

    if uploaded is None or uploaded.filename == '':
        return _respond_error("יש לצרף קובץ PDF.", 400)
    if not password:
        return _respond_error("יש להזין סיסמה.", 400)

    pdf_bytes = uploaded.read()

    try:
        unlocked = remove_password(pdf_bytes, password)
    except NotEncryptedError:
        return _respond_error("הקובץ אינו מוגן בסיסמה - אין מה להסיר.", 400)
    except WrongPasswordError:
        return _respond_error("הסיסמה שגויה.", 400)
    except ValueError as exc:
        return _respond_error(str(exc), 400)

    original_name = uploaded.filename
    if original_name.lower().endswith('.pdf'):
        download_name = original_name[:-4] + '-unlocked.pdf'
    else:
        download_name = original_name + '-unlocked.pdf'

    return send_file(
        io.BytesIO(unlocked),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=download_name,
    )
