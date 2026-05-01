import os
import tempfile
from flask import Flask, request, jsonify, render_template
from salary_calculator import calculate_salary, SHIFT_TYPES, DEFAULT_PARAMS
from schedule_parser import parse_schedule
from payslip_analyzer import analyze_payslip, compare_with_calculation

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32 MB

ALLOWED_SCHEDULE_EXT = {'docx'}
ALLOWED_PAYSLIP_EXT = {'jpg', 'jpeg', 'png', 'pdf'}


def _ext(filename: str) -> str:
    return filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''


@app.route('/')
def index():
    return render_template('index.html', shift_types=SHIFT_TYPES, default_params=DEFAULT_PARAMS)


@app.route('/api/parse-schedule', methods=['POST'])
def api_parse_schedule():
    if 'file' not in request.files:
        return jsonify({'error': 'לא נשלח קובץ'}), 400
    file = request.files['file']
    if _ext(file.filename) not in ALLOWED_SCHEDULE_EXT:
        return jsonify({'error': 'נא לשלוח קובץ Word בפורמט .docx'}), 400

    employee_name = request.form.get('employee_name', '').strip()

    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        result = parse_schedule(tmp_path, employee_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        os.unlink(tmp_path)


@app.route('/api/calculate', methods=['POST'])
def api_calculate():
    data = request.get_json(silent=True) or {}
    shift_counts = data.get('shift_counts', {})
    params = data.get('params', {})
    result = calculate_salary(shift_counts, params)
    return jsonify(result)


@app.route('/api/analyze-payslip', methods=['POST'])
def api_analyze_payslip():
    if 'file' not in request.files:
        return jsonify({'error': 'לא נשלח קובץ'}), 400
    file = request.files['file']
    ext = _ext(file.filename)
    if ext not in ALLOWED_PAYSLIP_EXT:
        return jsonify({'error': 'נא לשלוח תמונה (JPG/PNG) או PDF'}), 400

    with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    try:
        result = analyze_payslip(tmp_path)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        os.unlink(tmp_path)


@app.route('/api/compare', methods=['POST'])
def api_compare():
    data = request.get_json(silent=True) or {}
    payslip_data = data.get('payslip_data', {})
    calc_result = data.get('calc_result', {})
    if not payslip_data or not calc_result:
        return jsonify({'error': 'חסרים נתוני תלוש או חישוב'}), 400
    analysis = compare_with_calculation(payslip_data, calc_result)
    return jsonify({'analysis': analysis})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
