SHIFT_TYPES = {
    'morning_weekday': {
        'name_he': 'בוקר חול',
        'hours_100': 0.5,
        'hours_200': 0.0,
        'shabbat_visit': False,
    },
    'morning_shabbat': {
        'name_he': 'בוקר שבת',
        'hours_100': 0.0,
        'hours_200': 8.5,
        'shabbat_visit': True,
    },
    'afternoon_weekday': {
        'name_he': 'צהריים חול',
        'hours_100': 0.5,
        'hours_200': 0.0,
        'shabbat_visit': False,
    },
    'afternoon_friday': {
        'name_he': 'צהריים שישי',
        'hours_100': 0.0,
        'hours_200': 4.5,
        'shabbat_visit': False,
    },
    'afternoon_shabbat': {
        'name_he': 'צהריים שבת',
        'hours_100': 0.0,
        'hours_200': 8.5,
        'shabbat_visit': True,
    },
    'night_weekday': {
        'name_he': 'לילה חול',
        'hours_100': 0.0,
        'hours_200': 8.5,
        'shabbat_visit': False,
    },
    'night_friday_shabbat': {
        'name_he': 'לילה שישי/שבת',
        'hours_100': 0.0,
        'hours_200': 8.5,
        'shabbat_visit': True,
    },
    'double_morning_afternoon_weekday': {
        'name_he': 'כפולה בוקר+צהריים חול',
        'hours_100': 4.33,
        'hours_200': 0.0,
        'shabbat_visit': False,
    },
    'double_morning_afternoon_shabbat': {
        'name_he': 'כפולה בוקר+צהריים שבת',
        'hours_100': 0.0,
        'hours_200': 12.83,
        'shabbat_visit': True,
    },
    'double_afternoon_night_weekday': {
        'name_he': 'כפולה צהריים+לילה חול',
        'hours_100': 4.33,
        'hours_200': 0.0,
        'shabbat_visit': False,
    },
    'double_afternoon_night_friday_shabbat': {
        'name_he': 'כפולה צהריים+לילה שישי/שבת',
        'hours_100': 0.0,
        'hours_200': 13.0,
        'shabbat_visit': True,
    },
}

DEFAULT_PARAMS = {
    'hourly_rate': 94.19,
    'shabbat_rate': 278.30,
    'seniority_hours': 15.0,
    'vacation_days': 0.0,
    'sick_days': 0.0,
}


def calculate_salary(shift_counts: dict, params: dict) -> dict:
    hourly_rate = float(params.get('hourly_rate', DEFAULT_PARAMS['hourly_rate']))
    shabbat_rate = float(params.get('shabbat_rate', DEFAULT_PARAMS['shabbat_rate']))
    seniority_hours = float(params.get('seniority_hours', DEFAULT_PARAMS['seniority_hours']))
    vacation_days = float(params.get('vacation_days', 0))
    sick_days = float(params.get('sick_days', 0))

    shift_hours_100 = 0.0
    shift_hours_200 = 0.0
    shabbat_visits = 0
    breakdown = []

    for key, count in shift_counts.items():
        count = int(count or 0)
        if count <= 0 or key not in SHIFT_TYPES:
            continue
        info = SHIFT_TYPES[key]
        h100 = info['hours_100'] * count
        h200 = info['hours_200'] * count
        visits = count if info['shabbat_visit'] else 0
        shift_hours_100 += h100
        shift_hours_200 += h200
        shabbat_visits += visits
        breakdown.append({
            'type': info['name_he'],
            'count': count,
            'hours_100': round(h100, 2),
            'hours_200': round(h200, 2),
            'shabbat_visits': visits,
        })

    vacation_hours = vacation_days * 2.25
    # Seniority hours count as 100% premium hours (ש"ג 100% - כוננות)
    total_hours_100 = shift_hours_100 + seniority_hours + vacation_hours
    total_hours_200 = shift_hours_200

    payment_100 = total_hours_100 * hourly_rate
    # 200% hours are paid at double the hourly rate (ש"ג 200% = 200% of base rate)
    payment_200 = total_hours_200 * hourly_rate * 2
    shabbat_payment = shabbat_visits * shabbat_rate
    # כוננות: separate monthly on-call stipend = seniority_hours × rate
    konenut_payment = seniority_hours * hourly_rate

    total = payment_100 + payment_200 + shabbat_payment + konenut_payment

    return {
        'breakdown': breakdown,
        'hours_summary': {
            'shift_hours_100': round(shift_hours_100, 2),
            'seniority_hours': round(seniority_hours, 2),
            'vacation_hours': round(vacation_hours, 2),
            'total_hours_100': round(total_hours_100, 2),
            'shift_hours_200': round(shift_hours_200, 2),
            'total_hours_200': round(total_hours_200, 2),
            'shabbat_visits': shabbat_visits,
        },
        'payments': {
            'payment_100': round(payment_100, 2),
            'payment_200': round(payment_200, 2),
            'shabbat_payment': round(shabbat_payment, 2),
            'konenut_payment': round(konenut_payment, 2),
            'total': round(total, 2),
        },
        'params_used': {
            'hourly_rate': hourly_rate,
            'shabbat_rate': shabbat_rate,
            'seniority_hours': seniority_hours,
            'vacation_days': vacation_days,
            'sick_days': sick_days,
        },
    }
