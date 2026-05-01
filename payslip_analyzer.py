import base64
import json
import anthropic


PAYSLIP_SCHEMA = {
    "employee_name": "",
    "month": "",
    "gross_salary": 0,
    "net_salary": 0,
    "components": {
        "payment_100": 0,
        "payment_200": 0,
        "shabbat_payment": 0,
        "konenut_payment": 0,
        "total_shift_extras": 0,
    },
    "deductions": {
        "income_tax": 0,
        "national_insurance": 0,
        "health_insurance": 0,
        "pension": 0,
        "other": 0,
    },
    "raw_items": [{"name": "", "amount": 0}],
}

EXTRACT_PROMPT = f"""נתח את תלוש השכר הישראלי הזה וחלץ את כל רכיבי השכר.

חפש:
- שם העובד וחודש התלוש
- שכר ברוטו ונטו
- תוספות משמרות (ש"ג 100%, ש"ג 200%, שבת בקרים, כוננות)
- ניכויים (מס הכנסה, ביטוח לאומי, ביטוח בריאות, פנסיה)

חשוב: "ש"ג" = שעות גמול (תוספת שכר). "כוננות" = תוספת כוננות חודשית.

החזר JSON בלבד, ללא הסברים, בפורמט זה:
{json.dumps(PAYSLIP_SCHEMA, ensure_ascii=False, indent=2)}

אם שדה לא נמצא בתלוש, השתמש ב-0 לסכומים ומחרוזת ריקה לטקסט.
חלץ את כל השורות מהתלוש ב-raw_items."""

COMPARE_PROMPT = """השווה בין חישוב השכר שנעשה מסידור העבודה לבין נתוני התלוש.

חישוב מסידור העבודה:
{calc_summary}

נתוני תלוש השכר:
{payslip_summary}

נתח את ההשוואה בעברית, כלול:
1. סיכום קצר — האם השכר שולם בהתאם לסידור?
2. טבלת השוואה לכל רכיב (חישוב מול תלוש, הפרש)
3. ניתוח הפרשים משמעותיים עם הסברים אפשריים
4. המלצה — האם יש צורך לפנות למעסיק בגין אי-התאמה?

היה מקצועי, ברור ופשוט להבנה."""


def _get_media_type(filename: str) -> str:
    ext = filename.lower().rsplit('.', 1)[-1]
    return {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'pdf': 'application/pdf'}.get(ext, 'image/jpeg')


def analyze_payslip(file_path: str) -> dict:
    client = anthropic.Anthropic()
    media_type = _get_media_type(file_path)

    with open(file_path, 'rb') as f:
        image_data = base64.standard_b64encode(f.read()).decode('utf-8')

    message = client.messages.create(
        model='claude-opus-4-7',
        max_tokens=2048,
        messages=[{
            'role': 'user',
            'content': [
                {
                    'type': 'image',
                    'source': {'type': 'base64', 'media_type': media_type, 'data': image_data},
                },
                {'type': 'text', 'text': EXTRACT_PROMPT},
            ],
        }],
    )

    text = message.content[0].text.strip()
    if text.startswith('```'):
        lines = text.split('\n')
        text = '\n'.join(lines[1:-1])

    return json.loads(text)


def compare_with_calculation(payslip_data: dict, calc_result: dict) -> str:
    client = anthropic.Anthropic()
    payments = calc_result.get('payments', {})

    calc_summary = f"""תשלום ש"ג 100%: {payments.get('payment_100', 0):.2f} ₪
תשלום ש"ג 200%: {payments.get('payment_200', 0):.2f} ₪
שבת בקרים: {payments.get('shabbat_payment', 0):.2f} ₪
כוננות: {payments.get('konenut_payment', 0):.2f} ₪
סה"כ תוספות: {payments.get('total', 0):.2f} ₪"""

    comp = payslip_data.get('components', {})
    payslip_summary = f"""תשלום ש"ג 100%: {comp.get('payment_100', 0):.2f} ₪
תשלום ש"ג 200%: {comp.get('payment_200', 0):.2f} ₪
שבת בקרים: {comp.get('shabbat_payment', 0):.2f} ₪
כוננות: {comp.get('konenut_payment', 0):.2f} ₪
סה"כ תוספות (לפי תלוש): {comp.get('total_shift_extras', 0):.2f} ₪
שכר ברוטו: {payslip_data.get('gross_salary', 0):.2f} ₪
שכר נטו: {payslip_data.get('net_salary', 0):.2f} ₪"""

    message = client.messages.create(
        model='claude-opus-4-7',
        max_tokens=2048,
        messages=[{
            'role': 'user',
            'content': COMPARE_PROMPT.format(
                calc_summary=calc_summary,
                payslip_summary=payslip_summary,
            ),
        }],
    )
    return message.content[0].text
