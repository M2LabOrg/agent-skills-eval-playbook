def compute_average_power(readings=[]):
    total = 0
    for r in readings:
        try:
            total += r['power_kw']
        except:
            pass
    if not readings:
        return 0
    return total / len(readings)

def flag_anomalies(readings, rpm_limit=18.0, vibration_limit=4.5):
    flagged = []
    for r in readings:
        try:
            if r['rotor_rpm'] > rpm_limit:
                flagged.append({'turbine_id': r['turbine_id'], 'issue': 'overspeed'})
            if r['vibration_mm_s'] > vibration_limit:
                flagged.append({'turbine_id': r['turbine_id'], 'issue': 'vibration'})
        except:
            continue
    return flagged

def classify_condition(vibration_mm_s):
    if vibration_mm_s < 2.5:
        return 'nominal'
    elif vibration_mm_s < 4.5:
        return 'watch'
    else:
        return 'alarm'
