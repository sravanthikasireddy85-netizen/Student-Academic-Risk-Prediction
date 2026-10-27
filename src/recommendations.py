def generate_recommendations(student):
    actions=[]
    if float(student.get('attendance_pct',100)) < 75: actions.append('Agree on an attendance improvement plan and check in weekly.')
    if float(student.get('assignment_completion_pct',100)) < 70 or float(student.get('assignment_submission_rate',100)) < 70: actions.append('List pending assignments, set small deadlines, and review progress weekly.')
    if int(float(student.get('backlogs',0))) > 0: actions.append('Create a subject-wise backlog recovery plan with faculty support.')
    if float(student.get('internal_marks_pct',100)) < 50: actions.append('Practice previous questions and attend internal-assessment support sessions.')
    if float(student.get('study_hours_per_day',24)) < 2: actions.append('Build a realistic daily study schedule with short, consistent sessions.')
    if float(student.get('previous_gpa',10)) < 6: actions.append('Identify difficult subjects and arrange tutoring or peer study.')
    if float(student.get('class_participation_pct',100)) < 40: actions.append('Invite the student to participate through low-pressure questions or group work.')
    if not actions: actions.append('Maintain current study habits and review progress at the next checkpoint.')
    return actions
