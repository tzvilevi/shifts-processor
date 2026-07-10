from flask import Flask, request, Response, send_file
from ortools.sat.python import cp_model
import csv
import io
from flask_swagger_ui import get_swaggerui_blueprint

from pdf_password_remover import (
    remove_password,
    NotEncryptedError,
    WrongPasswordError,
)

app = Flask(__name__)

def schedule_shifts(employees, days):
    """
    Solves the shift scheduling problem using OR-Tools.

    Args:
        employees (list): List of employee names.
        days (list): List of days to schedule shifts for.

    Returns:
        dict: A dictionary with the schedule for each day and shift.
    """
    # Create the model
    model = cp_model.CpModel()

    # Define shifts and variables
    shifts = ["morning", "afternoon", "evening"]
    shift_vars = {}
    for day in days:
        for shift in shifts:
            for employee in employees:
                shift_vars[(day, shift, employee)] = model.NewBoolVar(f"{day}_{shift}_{employee}")

    # Each shift is assigned to exactly one employee
    for day in days:
        for shift in shifts:
            model.Add(sum(shift_vars[(day, shift, employee)] for employee in employees) == 1)

    # Each employee works at most one shift per day
    for day in days:
        for employee in employees:
            model.Add(sum(shift_vars[(day, shift, employee)] for shift in shifts) <= 1)

    # Solve the model
    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    # Format the solution
    if status == cp_model.FEASIBLE or status == cp_model.OPTIMAL:
        schedule = {day: {} for day in days}
        for day in days:
            for shift in shifts:
                for employee in employees:
                    if solver.Value(shift_vars[(day, shift, employee)]) == 1:
                        schedule[day][shift] = employee
        return schedule
    else:
        return None

@app.route('/')
def root_endpoint():
    return """
    <html>
        <head><title>Welcome</title></head>
        <body>
            <h1>Welcome to the Shift Scheduler Service!</h1>
            <img src="https://placedog.net/500/280" alt="Shih Tzu Dog">
            <p>Use the /schedule endpoint to generate shift schedules.</p>
            <p>Or remove a password from a PDF at <a href="/pdf">/pdf</a>.</p>
        </body>
    </html>
    """

@app.route('/schedule', methods=['POST'])
def schedule_endpoint():
    data = request.get_json()
    employees = data.get('employees', [])
    days = data.get('days', [])

    if not employees or not days:
        return {"error": "Both 'employees' and 'days' must be provided."}, 400

    schedule = schedule_shifts(employees, days)
    if not schedule:
        return {"error": "No valid schedule found."}, 400

    # Convert schedule to CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Day", "Shift", "Employee"])
    for day, shifts in schedule.items():
        for shift, employee in shifts.items():
            writer.writerow([day, shift, employee])

    output.seek(0)
    return Response(output, mimetype='text/csv', headers={"Content-Disposition": "attachment;filename=schedule.csv"})

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


@app.route('/pdf', methods=['GET'])
def pdf_unlock_page():
    return _render_pdf_page()


@app.route('/pdf/remove-password', methods=['POST'])
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


# Swagger setup
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

if __name__ == '__main__':
    app.run(debug=True)