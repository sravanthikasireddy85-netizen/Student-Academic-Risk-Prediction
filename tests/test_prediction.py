import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.data_preprocessing import validate_student
from src.recommendations import generate_recommendations
from src.database import init_db, save_student, get_students, save_prediction, get_predictions, delete_student

def sample():
 return {'student_id':'TEST001','student_name':'Test Student','age':20,'gender':'Prefer not to say','attendance_pct':60,'previous_gpa':5.0,'internal_marks_pct':40,'assignment_completion_pct':50,'backlogs':2,'study_hours_per_day':1,'previous_failures':1,'class_participation_pct':30,'assignment_submission_rate':50,'number_of_subjects':6,'previous_semester_pct':50}
def test_valid_and_invalid_inputs():
 s=sample(); assert validate_student(s)==[]
 s['attendance_pct']=-10; assert any('Attendance' in e for e in validate_student(s))
 s=sample(); s['attendance_pct']=150; assert validate_student(s)
 s=sample(); s['study_hours_per_day']=30; assert validate_student(s)
 s=sample(); s['backlogs']=-1; assert validate_student(s)
 s=sample(); s['student_name']=''; assert validate_student(s)
def test_recommendations():
 actions=generate_recommendations(sample()); assert any('attendance' in a.lower() for a in actions); assert any('backlog' in a.lower() for a in actions)
def test_database_roundtrip():
 init_db(); s=sample(); save_student(s); assert any(x['student_id']=='TEST001' for x in get_students())
 save_prediction('TEST001',{'risk_level':'HIGH RISK','risk_probability':.8,'probabilities':{'LOW RISK':.1,'MEDIUM RISK':.1,'HIGH RISK':.8},'reasons':['Low attendance'],'recommendations':['Attend class'],'model_name':'test'})
 assert get_predictions('TEST001'); delete_student('TEST001'); assert not any(x['student_id']=='TEST001' for x in get_students())
