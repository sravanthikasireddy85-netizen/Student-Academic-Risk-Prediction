"""Small, transparent feature engineering helpers."""
def risk_reasons(student):
    reasons=[]
    if float(student.get('attendance_pct',100)) < 75: reasons.append('Attendance is below 75%.')
    if float(student.get('previous_gpa',10)) < 6: reasons.append('Previous GPA is below 6.0/10.')
    if int(float(student.get('backlogs',0))) > 0: reasons.append('One or more backlogs need a recovery plan.')
    if float(student.get('assignment_completion_pct',100)) < 70: reasons.append('Assignment completion is low.')
    if float(student.get('internal_marks_pct',100)) < 50: reasons.append('Internal assessment marks are low.')
    if float(student.get('study_hours_per_day',24)) < 2: reasons.append('Reported daily study time is low.')
    if float(student.get('assignment_submission_rate',100)) < 70: reasons.append('Assignment submission rate is low.')
    if float(student.get('class_participation_pct',100)) < 40: reasons.append('Class participation may need support.')
    if not reasons: reasons.append('No major rule-based warning flag was detected; continue regular check-ins.')
    return reasons
