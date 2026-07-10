from flask import Flask, request, Response
from ortools.sat.python import cp_model
import csv
import io
from flask_swagger_ui import get_swaggerui_blueprint

from pdf_web import pdf_bp

app = Flask(__name__)
app.register_blueprint(pdf_bp)

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

# Swagger setup
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'
swaggerui_blueprint = get_swaggerui_blueprint(SWAGGER_URL, API_URL)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

if __name__ == '__main__':
    app.run(debug=True)